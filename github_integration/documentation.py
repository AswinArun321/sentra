import re
import base64
import logging
from .services import GitHubService, GitHubNotFoundError, GitHubAPIError

logger = logging.getLogger(__name__)

# Common README file patterns (case-insensitive check)
README_VARIANTS = {
    'readme.md',
    'readme',
    'readme.txt',
    'readme.rst',
    'readme.markdown',
}

# Documentation sections specification with weights and regex patterns
SECTION_RULES = [
    {
        'key': 'title',
        'name': 'Project Title',
        'points': 10,
        'patterns': [
            r'^\s*#\s+[\w\s\-\.\(\)\:\@\/\,\']+',  # Top-level H1 Markdown header
            r'^[^\n\r]+\n\s*={3,}\s*$',             # Setext-style H1 header
        ],
        'recommendation': 'Add a clear project title at the top of the README (e.g. `# Project Name`).',
    },
    {
        'key': 'description',
        'name': 'Description / Overview',
        'points': 15,
        'patterns': [
            r'(?i)##?\s+(overview|about|description|summary|introduction|what is)',
            r'(?i)\*\*(overview|description|about)\*\*',
        ],
        'recommendation': 'Add a project description or overview explaining what the project does.',
    },
    {
        'key': 'features',
        'name': 'Features',
        'points': 10,
        'patterns': [
            r'(?i)##?\s+(features|key features|highlights|capabilities|what\'?s included)',
            r'(?i)\*\*(features|highlights)\*\*',
        ],
        'recommendation': 'Add a Features section listing key capabilities and functional highlights.',
    },
    {
        'key': 'installation',
        'name': 'Installation',
        'points': 15,
        'patterns': [
            r'(?i)##?\s+(installation|setup|getting started|how to install|build instructions)',
            r'(?i)(pip install|npm install|yarn install|git clone|docker run)',
        ],
        'recommendation': 'Add step-by-step installation instructions for developers or users.',
    },
    {
        'key': 'requirements',
        'name': 'Requirements',
        'points': 10,
        'patterns': [
            r'(?i)##?\s+(requirements|prerequisites|dependencies|system requirements)',
            r'(?i)(python\s*>=?|node\.?js\s*>=?|docker|postgresql|sqlite)',
        ],
        'recommendation': 'Document system prerequisites, runtime versions (e.g. Python, Node.js), and dependencies.',
    },
    {
        'key': 'usage',
        'name': 'Usage',
        'points': 15,
        'patterns': [
            r'(?i)##?\s+(usage|how to use|quick start|quickstart|examples|commands|running)',
            r'(?i)(python manage\.py runserver|npm start|npm run dev)',
        ],
        'recommendation': 'Add a Usage section showing how to execute, run, or call the application.',
    },
    {
        'key': 'configuration',
        'name': 'Configuration',
        'points': 5,
        'patterns': [
            r'(?i)##?\s+(configuration|environment variables|config|settings|\.env)',
            r'(?i)(\.env\.example|SECRET_KEY|DATABASE_URL)',
        ],
        'recommendation': 'Add configuration instructions and describe required environment variables.',
    },
    {
        'key': 'project_structure',
        'name': 'Project Structure',
        'points': 5,
        'patterns': [
            r'(?i)##?\s+(project structure|directory structure|folder structure|architecture)',
            r'├──|└──|──\s*\w+',
        ],
        'recommendation': 'Add a project structure diagram or outline showing key files and directories.',
    },
    {
        'key': 'license',
        'name': 'License',
        'points': 10,
        'patterns': [
            r'(?i)##?\s+(license|licence|copyright)',
            r'(?i)(MIT License|Apache License|GPL|BSD|ISC|Mozilla Public License)',
        ],
        'recommendation': 'Add licensing information stating how this project is licensed.',
    },
    {
        'key': 'contributing',
        'name': 'Contributing',
        'points': 5,
        'patterns': [
            r'(?i)##?\s+(contributing|how to contribute|contribution guidelines|development)',
            r'(?i)(pull request|submit a PR|code of conduct)',
        ],
        'recommendation': 'Add contribution guidelines for other developers to contribute.',
    },
]


class DocumentationAnalyzer:
    """
    Analyzes repository documentation quality, checks README presence,
    evaluates sections, calculates a 100-point documentation score, and provides recommendations.
    """

    def __init__(self, service=None):
        self.service = service or GitHubService()

    def check_readme(self, access_token, repo_id):
        """
        Check if a README file exists in the repository root (case-insensitive).
        Returns dict with exists: bool, filename, path, sha, size, download_url.
        """
        try:
            root_contents = self.service.get_contents(access_token, repo_id, "")
        except GitHubNotFoundError:
            return {
                'exists': False,
                'status': 'MISSING',
                'filename': None,
                'path': None,
                'sha': None,
                'size': 0,
                'download_url': None,
            }
        except GitHubAPIError as e:
            logger.error("API error during check_readme for repo %s: %s", repo_id, str(e))
            return {
                'exists': False,
                'status': 'ERROR',
                'error': str(e),
                'filename': None,
                'path': None,
                'sha': None,
                'size': 0,
                'download_url': None,
            }

        if not isinstance(root_contents, list):
            root_contents = [root_contents]

        for item in root_contents:
            name = item.get('name', '')
            if name.lower() in README_VARIANTS:
                return {
                    'exists': True,
                    'status': 'PRESENT',
                    'filename': name,
                    'path': item.get('path', name),
                    'sha': item.get('sha'),
                    'size': item.get('size', 0),
                    'download_url': item.get('download_url'),
                }

        return {
            'exists': False,
            'status': 'MISSING',
            'filename': None,
            'path': None,
            'sha': None,
            'size': 0,
            'download_url': None,
        }

    def get_readme_content(self, access_token, repo_id, path):
        """
        Retrieve raw content of a file from GitHub repository and decode Base64.
        """
        file_data = self.service.get_contents(access_token, repo_id, path)
        encoding = file_data.get('encoding', 'base64')
        raw_content = file_data.get('content', '')

        if encoding == 'base64':
            try:
                # Remove possible newlines in base64 string
                clean_b64 = raw_content.replace('\n', '').replace('\r', '')
                decoded = base64.b64decode(clean_b64).decode('utf-8', errors='replace')
                return decoded, file_data.get('sha')
            except Exception as e:
                logger.error("Failed to decode base64 README content: %s", str(e))
                return raw_content, file_data.get('sha')
        return raw_content, file_data.get('sha')

    def analyze_readme_text(self, content_text):
        """
        Analyze the text content of a README, evaluate presence of sections,
        calculate score out of 100, and generate recommendations.
        """
        if not content_text or not content_text.strip():
            return {
                'score': 0,
                'rating': 'Very Poor / Missing',
                'sections': {rule['key']: False for rule in SECTION_RULES},
                'sections_detail': [
                    {'key': rule['key'], 'name': rule['name'], 'present': False, 'points': rule['points']}
                    for rule in SECTION_RULES
                ],
                'recommendations': [rule['recommendation'] for rule in SECTION_RULES],
            }

        text = content_text.strip()
        score = 0
        sections_dict = {}
        sections_detail = []
        recommendations = []

        # If first line has a heading without an explicit H1 tag, grant title
        first_line = text.split('\n')[0].strip()
        has_title = False

        for rule in SECTION_RULES:
            present = False
            for pattern in rule['patterns']:
                if re.search(pattern, text, re.MULTILINE):
                    present = True
                    break

            if rule['key'] == 'title' and not present:
                # Heuristic: non-empty first line with length < 80 characters can count as title
                if 2 <= len(first_line) <= 80 and not first_line.startswith(('http', 'import ', '//')):
                    present = True

            if rule['key'] == 'description' and not present:
                # Heuristic: if text length > 120 characters and has paragraphs, grant description
                if len(text) >= 120:
                    present = True

            sections_dict[rule['key']] = present
            sections_detail.append({
                'key': rule['key'],
                'name': rule['name'],
                'present': present,
                'points': rule['points'],
            })

            if present:
                score += rule['points']
            else:
                recommendations.append(rule['recommendation'])

        score = min(100, max(0, score))

        # Rating categories:
        # 90–100: Excellent, 75–89: Good, 50–74: Needs Improvement, 25–49: Poor, 0–24: Very Poor / Missing
        if score >= 90:
            rating = 'Excellent'
        elif score >= 75:
            rating = 'Good'
        elif score >= 50:
            rating = 'Needs Improvement'
        elif score >= 25:
            rating = 'Poor'
        else:
            rating = 'Very Poor / Missing'

        return {
            'score': score,
            'rating': rating,
            'sections': sections_dict,
            'sections_detail': sections_detail,
            'recommendations': recommendations,
        }

    def analyze_repository(self, access_token, repo_id):
        """
        Main entry point for repository documentation analysis.
        Checks presence, fetches content if present, calculates score and recommendations.
        """
        readme_info = self.check_readme(access_token, repo_id)

        if not readme_info['exists']:
            # Missing README result
            return {
                'exists': False,
                'status': readme_info.get('status', 'MISSING'),
                'filename': None,
                'path': None,
                'sha': None,
                'score': 0,
                'rating': 'Very Poor / Missing',
                'sections': {rule['key']: False for rule in SECTION_RULES},
                'sections_detail': [
                    {'key': rule['key'], 'name': rule['name'], 'present': False, 'points': rule['points']}
                    for rule in SECTION_RULES
                ],
                'recommendations': [
                    'Add a README.md file to the repository root.',
                    'Add a project description and overview.',
                    'Add installation instructions.',
                    'Add usage instructions.',
                    'Document project requirements and dependencies.',
                    'Add license information.',
                ],
                'content': '',
            }

        # Fetch and analyze existing README
        try:
            content_text, sha = self.get_readme_content(access_token, repo_id, readme_info['path'])
            analysis = self.analyze_readme_text(content_text)
            return {
                'exists': True,
                'status': 'PRESENT',
                'filename': readme_info['filename'],
                'path': readme_info['path'],
                'sha': sha,
                'score': analysis['score'],
                'rating': analysis['rating'],
                'sections': analysis['sections'],
                'sections_detail': analysis['sections_detail'],
                'recommendations': analysis['recommendations'],
                'content': content_text,
            }
        except Exception as e:
            logger.error("Failed to analyze README for repo %s: %s", repo_id, str(e))
            return {
                'exists': True,
                'status': 'ERROR',
                'filename': readme_info['filename'],
                'path': readme_info['path'],
                'sha': readme_info.get('sha'),
                'score': 0,
                'rating': 'Error',
                'sections': {rule['key']: False for rule in SECTION_RULES},
                'sections_detail': [],
                'recommendations': [f"Unable to analyze README due to an error: {str(e)}"],
                'content': '',
            }
