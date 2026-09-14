import os
import secrets
import logging
import base64
import requests
from urllib.parse import urlencode
from django.conf import settings
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class GitHubAuthError(GitHubAPIError):
    """Authentication or token exchange failure."""
    pass


class GitHubRateLimitError(GitHubAPIError):
    """GitHub API rate limit exceeded."""
    pass


class GitHubNotFoundError(GitHubAPIError):
    """Resource not found on GitHub."""
    pass


class GitHubService:
    """
    Service layer encapsulating communication with GitHub OAuth and REST API.
    """
    OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
    DEFAULT_API_URL = "https://api.github.com"
    OAUTH_SCOPES = "read:user,repo"

    def __init__(self, client_id=None, client_secret=None, redirect_uri=None, api_url=None):
        try:
            load_dotenv(override=True)
        except Exception:
            pass
        self.client_id = client_id or os.environ.get('GITHUB_CLIENT_ID') or getattr(settings, 'GITHUB_CLIENT_ID', '')
        self.client_secret = client_secret or os.environ.get('GITHUB_CLIENT_SECRET') or getattr(settings, 'GITHUB_CLIENT_SECRET', '')
        self.redirect_uri = redirect_uri or os.environ.get('GITHUB_REDIRECT_URI') or getattr(settings, 'GITHUB_REDIRECT_URI', '')
        self.api_url = (api_url or os.environ.get('GITHUB_API_URL') or getattr(settings, 'GITHUB_API_URL', self.DEFAULT_API_URL)).rstrip('/')

    def get_authorization_url(self, state=None):
        """
        Generate the GitHub OAuth authorization URL and CSRF state token.
        Returns: tuple of (authorization_url, state)
        """
        if not state:
            state = secrets.token_urlsafe(32)

        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.OAUTH_SCOPES,
            'state': state,
        }
        auth_url = f"{self.OAUTH_AUTHORIZE_URL}?{urlencode(params)}"
        return auth_url, state

    def exchange_code_for_token(self, code):
        """
        Exchange OAuth temporary authorization code for an access token.
        """
        if not self.client_id or not self.client_secret:
            raise GitHubAuthError("GitHub OAuth client credentials are not configured in settings.")

        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri,
        }
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'LicenseLens-Dependency-Auditor',
        }

        try:
            response = requests.post(self.OAUTH_TOKEN_URL, data=payload, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Failed to connect to GitHub OAuth token endpoint: %s", str(e))
            raise GitHubAuthError(f"Unable to reach GitHub authentication service: {str(e)}")

        if 'error' in data:
            error_desc = data.get('error_description', data.get('error', 'OAuth token exchange failed'))
            logger.warning("GitHub OAuth token exchange error: %s", error_desc)
            raise GitHubAuthError(error_desc)

        access_token = data.get('access_token')
        if not access_token:
            raise GitHubAuthError("No access token returned by GitHub.")

        return access_token

    def _get_headers(self, access_token):
        return {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
            'User-Agent': 'LicenseLens-Dependency-Auditor',
        }

    def _handle_response(self, response):
        """Handle common GitHub API response errors."""
        if response.status_code == 401:
            raise GitHubAuthError("GitHub access token is invalid or has expired.", status_code=401)
        elif response.status_code == 403:
            if 'rate limit' in response.text.lower():
                raise GitHubRateLimitError("GitHub API rate limit reached. Please try again later.", status_code=403)
            raise GitHubAPIError("Permission denied by GitHub API.", status_code=403)
        elif response.status_code == 404:
            raise GitHubNotFoundError("Repository or resource could not be found or is not accessible.", status_code=404)
        elif response.status_code >= 400:
            raise GitHubAPIError(f"GitHub API returned error {response.status_code}: {response.text}", status_code=response.status_code)

    def get_user(self, access_token):
        """
        Fetch authenticated user profile details from GitHub.
        """
        url = f"{self.api_url}/user"
        headers = self._get_headers(access_token)

        try:
            response = requests.get(url, headers=headers, timeout=15)
            self._handle_response(response)
            data = response.json()
            return {
                'id': data.get('id'),
                'login': data.get('login'),
                'name': data.get('name') or data.get('login'),
                'avatar_url': data.get('avatar_url', ''),
                'html_url': data.get('html_url', ''),
                'public_repos': data.get('public_repos', 0),
                'total_private_repos': data.get('total_private_repos', 0),
            }
        except requests.exceptions.RequestException as e:
            logger.error("GitHub API network error in get_user: %s", str(e))
            raise GitHubAPIError(f"Unable to connect to GitHub: {str(e)}")

    def get_repositories(self, access_token, page=1, per_page=30, sort='updated', direction='desc'):
        """
        Fetch repositories owned by or accessible to the authenticated user.
        """
        url = f"{self.api_url}/user/repos"
        headers = self._get_headers(access_token)
        params = {
            'affiliation': 'owner,collaborator',
            'sort': sort,
            'direction': direction,
            'page': page,
            'per_page': min(per_page, 100),
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            self._handle_response(response)
            raw_repos = response.json()
            if not isinstance(raw_repos, list):
                raw_repos = []
            return [self.normalize_repository(r) for r in raw_repos]
        except requests.exceptions.RequestException as e:
            logger.error("GitHub API network error in get_repositories: %s", str(e))
            raise GitHubAPIError(f"Unable to connect to GitHub: {str(e)}")

    def get_repository(self, access_token, repo_id):
        """
        Fetch details for a specific repository by its GitHub numeric ID.
        Verifies that the user's token has access to this repository.
        """
        url = f"{self.api_url}/repositories/{repo_id}"
        headers = self._get_headers(access_token)

        try:
            response = requests.get(url, headers=headers, timeout=15)
            self._handle_response(response)
            return self.normalize_repository(response.json())
        except requests.exceptions.RequestException as e:
            logger.error("GitHub API network error in get_repository: %s", str(e))
            raise GitHubAPIError(f"Unable to connect to GitHub: {str(e)}")

    @staticmethod
    def normalize_repository(repo):
        """
        Normalize repository data dictionary into standard LicenseLens schema.
        """
        return {
            'id': repo.get('id'),
            'name': repo.get('name', ''),
            'full_name': repo.get('full_name', ''),
            'description': repo.get('description') or '',
            'private': bool(repo.get('private', False)),
            'html_url': repo.get('html_url', ''),
            'default_branch': repo.get('default_branch', 'main'),
            'language': repo.get('language') or 'Unknown',
            'updated_at': repo.get('updated_at', ''),
            'stargazers_count': repo.get('stargazers_count', 0),
            'forks_count': repo.get('forks_count', 0),
            'owner': {
                'login': repo.get('owner', {}).get('login', ''),
                'avatar_url': repo.get('owner', {}).get('avatar_url', ''),
            } if isinstance(repo.get('owner'), dict) else {},
        }

    def get_contents(self, access_token, repo_identifier, path=""):
        """
        Fetch directory listing or file content from GitHub repository contents API.
        repo_identifier can be a repo full_name ('owner/repo') or integer repo_id.
        """
        clean_path = path.strip('/')
        if isinstance(repo_identifier, int) or str(repo_identifier).isdigit():
            url = f"{self.api_url}/repositories/{repo_identifier}/contents/{clean_path}" if clean_path else f"{self.api_url}/repositories/{repo_identifier}/contents"
        else:
            url = f"{self.api_url}/repos/{repo_identifier}/contents/{clean_path}" if clean_path else f"{self.api_url}/repos/{repo_identifier}/contents"

        headers = self._get_headers(access_token)
        try:
            response = requests.get(url, headers=headers, timeout=15)
            self._handle_response(response)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("GitHub API network error in get_contents (%s): %s", url, str(e))
            raise GitHubAPIError(f"Unable to connect to GitHub: {str(e)}")

    def commit_file(self, access_token, repo_identifier, path, content_str, commit_message, sha=None):
        """
        Create or update a file in the repository using the GitHub Contents API.
        Encodes content to Base64.
        """
        clean_path = path.strip('/')
        if isinstance(repo_identifier, int) or str(repo_identifier).isdigit():
            url = f"{self.api_url}/repositories/{repo_identifier}/contents/{clean_path}"
        else:
            url = f"{self.api_url}/repos/{repo_identifier}/contents/{clean_path}"

        headers = self._get_headers(access_token)
        encoded_content = base64.b64encode(content_str.encode('utf-8')).decode('utf-8')
        payload = {
            'message': commit_message,
            'content': encoded_content,
        }
        if sha:
            payload['sha'] = sha

        try:
            response = requests.put(url, headers=headers, json=payload, timeout=20)
            self._handle_response(response)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("GitHub API network error in commit_file (%s): %s", url, str(e))
            raise GitHubAPIError(f"Unable to commit file to GitHub: {str(e)}")

    def get_connection_for_user(self, user):
        """
        Retrieve the active GitHubConnection for the given LicenseLens user.
        """
        from .models import GitHubConnection
        return GitHubConnection.objects.filter(user=user).first()

    def get_repositories_for_user(self, user, page=1, per_page=30, sort='updated', direction='desc'):
        """
        Retrieve repositories strictly using the given user's GitHub connection token.
        Raises GitHubAuthError if the user is not connected.
        """
        connection = self.get_connection_for_user(user)
        if not connection:
            raise GitHubAuthError("User has no connected GitHub account.", status_code=400)
        return self.get_repositories(connection.access_token, page=page, per_page=per_page, sort=sort, direction=direction)

    def get_repository_for_user(self, user, repo_id):
        """
        Retrieve specific repository details strictly using the given user's GitHub connection token.
        """
        connection = self.get_connection_for_user(user)
        if not connection:
            raise GitHubAuthError("User has no connected GitHub account.", status_code=400)
        return self.get_repository(connection.access_token, repo_id)

    def validate_repository_access(self, user, repo_id):
        """
        Validates that the given user has verified access to the specified repository.
        Returns repository data dict on success, raises exception on failure.
        """
        return self.get_repository_for_user(user, repo_id)

    def get_repository_tree(self, access_token, repo_identifier, branch_or_sha='main', recursive=True, max_entries=5000):
        """
        Fetch repository file tree recursively via GitHub Git Trees API.
        repo_identifier can be a repo full_name ('owner/repo') or integer repo_id.
        Applies max_entries limit to prevent memory/performance issues on very large repos.
        """
        if isinstance(repo_identifier, int) or str(repo_identifier).isdigit():
            url = f"{self.api_url}/repositories/{repo_identifier}/git/trees/{branch_or_sha}"
        else:
            url = f"{self.api_url}/repos/{repo_identifier}/git/trees/{branch_or_sha}"

        headers = self._get_headers(access_token)
        params = {'recursive': 1} if recursive else {}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=20)
            self._handle_response(response)
            data = response.json()
            tree_entries = data.get('tree', [])
            if len(tree_entries) > max_entries:
                logger.warning("Repository tree exceeded max entries limit: %d > %d", len(tree_entries), max_entries)
                data['tree'] = tree_entries[:max_entries]
                data['truncated'] = True
            return data
        except requests.exceptions.RequestException as e:
            logger.error("GitHub API network error in get_repository_tree (%s): %s", url, str(e))
            raise GitHubAPIError(f"Unable to fetch repository file tree: {str(e)}")

    def get_file_content(self, access_token, repo_identifier, path, ref=None, max_size_bytes=5242880):
        """
        Retrieve raw file content from GitHub repository and decode Base64 into UTF-8.
        Enforces maximum file size limit (5MB by default).
        """
        clean_path = path.strip('/')
        if isinstance(repo_identifier, int) or str(repo_identifier).isdigit():
            url = f"{self.api_url}/repositories/{repo_identifier}/contents/{clean_path}"
        else:
            url = f"{self.api_url}/repos/{repo_identifier}/contents/{clean_path}"

        headers = self._get_headers(access_token)
        params = {}
        if ref:
            params['ref'] = ref

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            self._handle_response(response)
            data = response.json()
            if isinstance(data, list):
                raise GitHubAPIError(f"Path '{path}' is a directory, not a file.")
            if data.get('size', 0) > max_size_bytes:
                raise GitHubAPIError(f"File '{path}' exceeds max allowed size of {max_size_bytes} bytes.")

            content_b64 = data.get('content', '')
            encoding = data.get('encoding', 'base64')
            if encoding == 'base64':
                clean_b64 = content_b64.replace('\n', '').replace('\r', '')
                decoded = base64.b64decode(clean_b64).decode('utf-8', errors='replace')
                return decoded, data.get('sha')
            return content_b64, data.get('sha')
        except requests.exceptions.RequestException as e:
            logger.error("GitHub API network error in get_file_content (%s): %s", url, str(e))
            raise GitHubAPIError(f"Unable to retrieve file '{path}': {str(e)}")

    def get_latest_commit_sha(self, access_token, repo_identifier, branch='main'):
        """
        Fetch the latest commit SHA for a specific branch.
        """
        if isinstance(repo_identifier, int) or str(repo_identifier).isdigit():
            url = f"{self.api_url}/repositories/{repo_identifier}/commits/{branch}"
        else:
            url = f"{self.api_url}/repos/{repo_identifier}/commits/{branch}"

        headers = self._get_headers(access_token)
        try:
            response = requests.get(url, headers=headers, timeout=15)
            self._handle_response(response)
            data = response.json()
            return data.get('sha', '')
        except Exception as e:
            logger.warning("Could not fetch commit SHA for %s (branch %s): %s", repo_identifier, branch, str(e))
            return ''


