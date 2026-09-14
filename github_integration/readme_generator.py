import logging
from .services import GitHubService, GitHubNotFoundError, GitHubAPIError

logger = logging.getLogger(__name__)

IGNORED_DIRS = {
    '.git', '.github', 'node_modules', 'venv', '.venv', 'env', '__pycache__',
    '.idea', '.vscode', 'dist', 'build', 'staticfiles', '.pytest_cache'
}


class ReadmeGenerator:
    """
    Synthesizes a clean, standard, and tailored README.md document
    using actual repository metadata, detected frameworks, dependencies, and file structure.
    """

    def __init__(self, service=None):
        self.service = service or GitHubService()

    def generate_readme(self, access_token, repo_id):
        """
        Main generator method: gathers repository metadata and contents,
        detects frameworks, and builds a complete Markdown README.
        """
        # 1. Fetch Repository Metadata
        repo = self.service.get_repository(access_token, repo_id)
        name = repo.get('name') or f"repository-{repo_id}"
        full_name = repo.get('full_name', name)
        description = repo.get('description') or f"Open-source software project {name}."
        language = repo.get('language') or 'General'
        html_url = repo.get('html_url') or f"https://github.com/{full_name}"
        default_branch = repo.get('default_branch', 'main')

        # 2. Fetch Root Directory Structure & File Listing
        root_items = []
        try:
            root_items = self.service.get_contents(access_token, repo_id, "")
            if not isinstance(root_items, list):
                root_items = []
        except Exception as e:
            logger.warning("Could not fetch repository contents for README generation: %s", str(e))

        file_names = {item.get('name', '') for item in root_items}

        # 3. Detect Frameworks & Stacks
        frameworks, tech_stack = self._detect_technologies(language, file_names, access_token, repo_id)

        # 4. Generate Project Structure Tree
        structure_tree = self._build_structure_tree(name, root_items)

        # 5. Assemble Structured Markdown
        readme_md = self._render_markdown(
            name=name,
            full_name=full_name,
            description=description,
            language=language,
            html_url=html_url,
            default_branch=default_branch,
            frameworks=frameworks,
            tech_stack=tech_stack,
            file_names=file_names,
            structure_tree=structure_tree,
        )

        return {
            'repository': name,
            'full_name': full_name,
            'filename': 'README.md',
            'content': readme_md,
            'frameworks': frameworks,
            'language': language,
        }

    def _detect_technologies(self, language, file_names, access_token, repo_id):
        frameworks = []
        tech_stack = []

        lang_lower = (language or '').lower()

        if language and language != 'Unknown':
            tech_stack.append(language)

        # Python checks
        if 'manage.py' in file_names or 'wsgi.py' in file_names:
            frameworks.append('Django')
            tech_stack.extend(['Django', 'Python', 'SQLite / PostgreSQL'])
        elif 'requirements.txt' in file_names or 'Pipfile' in file_names or 'pyproject.toml' in file_names or lang_lower == 'python':
            if 'app.py' in file_names:
                frameworks.append('Flask')
                tech_stack.extend(['Flask', 'Python'])
            elif 'main.py' in file_names:
                frameworks.append('FastAPI / Python')
                tech_stack.extend(['FastAPI', 'Python'])
            else:
                tech_stack.append('Python')

        # JavaScript / TypeScript checks
        if 'package.json' in file_names or lang_lower in ('javascript', 'typescript'):
            tech_stack.append('Node.js')
            if 'next.config.js' in file_names or 'next.config.mjs' in file_names:
                frameworks.append('Next.js')
                tech_stack.extend(['Next.js', 'React'])
            elif 'vite.config.js' in file_names or 'vite.config.ts' in file_names:
                frameworks.append('Vite')
                tech_stack.append('Vite')
            elif 'angular.json' in file_names:
                frameworks.append('Angular')
                tech_stack.append('Angular')
            elif 'vue.config.js' in file_names or 'nuxt.config.js' in file_names:
                frameworks.append('Vue.js')
                tech_stack.append('Vue.js')
            else:
                frameworks.append('Node.js / Express')

        # Java / JVM
        if 'pom.xml' in file_names:
            frameworks.append('Maven / Spring Boot')
            tech_stack.extend(['Java', 'Maven', 'Spring Boot'])
        elif 'build.gradle' in file_names:
            frameworks.append('Gradle / Java')
            tech_stack.extend(['Java', 'Gradle'])

        # Rust / Go / PHP
        if 'Cargo.toml' in file_names or lang_lower == 'rust':
            tech_stack.extend(['Rust', 'Cargo'])
        if 'go.mod' in file_names or lang_lower == 'go':
            tech_stack.extend(['Go', 'Go Modules'])
        if 'composer.json' in file_names or lang_lower == 'php':
            tech_stack.extend(['PHP', 'Composer'])

        # Deduplicate while preserving order
        seen = set()
        dedup_stack = []
        for t in tech_stack:
            if t not in seen:
                seen.add(t)
                dedup_stack.append(t)

        return frameworks, dedup_stack

    def _build_structure_tree(self, repo_name, root_items):
        lines = [f"{repo_name}/"]
        dirs = []
        files = []

        for item in root_items:
            name = item.get('name', '')
            if name in IGNORED_DIRS or name.startswith('.'):
                continue
            if item.get('type') == 'dir':
                dirs.append(f"{name}/")
            else:
                files.append(name)

        # Show max 15 items in sample tree
        all_items = sorted(dirs) + sorted(files)
        sample = all_items[:14]

        for i, item in enumerate(sample):
            is_last = (i == len(sample) - 1)
            prefix = "└── " if is_last else "├── "
            lines.append(f"{prefix}{item}")

        if len(all_items) > 14:
            lines.append("└── ...")

        return "\n".join(lines)

    def _render_markdown(self, name, full_name, description, language, html_url,
                         default_branch, frameworks, tech_stack, file_names, structure_tree):
        fw_label = frameworks[0] if frameworks else language

        # Requirements snippet
        req_items = []
        if 'Python' in tech_stack:
            req_items.append("- Python 3.10+ & `pip`")
        if 'Node.js' in tech_stack or 'React' in tech_stack:
            req_items.append("- Node.js 18+ & `npm` or `yarn`")
        if 'Java' in tech_stack:
            req_items.append("- JDK 17+ & Maven/Gradle")
        if 'Docker' in file_names or 'docker-compose.yml' in file_names:
            req_items.append("- Docker & Docker Compose")
        if not req_items:
            req_items.append(f"- {language} runtime environment")
            req_items.append("- Git version control")

        # Installation snippet
        install_steps = [
            "1. **Clone the repository:**",
            "   ```bash",
            f"   git clone {html_url}.git",
            f"   cd {name}",
            "   ```",
        ]

        if 'requirements.txt' in file_names:
            install_steps.extend([
                "2. **Set up virtual environment & install dependencies:**",
                "   ```bash",
                "   python -m venv venv",
                "   source venv/bin/activate  # On Windows: venv\\Scripts\\activate",
                "   pip install -r requirements.txt",
                "   ```",
            ])
        elif 'package.json' in file_names:
            install_steps.extend([
                "2. **Install package dependencies:**",
                "   ```bash",
                "   npm install",
                "   ```",
            ])
        elif 'pom.xml' in file_names:
            install_steps.extend([
                "2. **Build with Maven:**",
                "   ```bash",
                "   mvn clean install",
                "   ```",
            ])
        elif 'Cargo.toml' in file_names:
            install_steps.extend([
                "2. **Build with Cargo:**",
                "   ```bash",
                "   cargo build",
                "   ```",
            ])

        # Usage snippet
        usage_steps = []
        if 'manage.py' in file_names:
            usage_steps.extend([
                "Run database migrations and start the local development server:",
                "```bash",
                "python manage.py migrate",
                "python manage.py runserver",
                "```",
                "Open your browser and navigate to `http://127.0.0.1:8000/`.",
            ])
        elif 'package.json' in file_names:
            usage_steps.extend([
                "Start the local development application:",
                "```bash",
                "npm run dev  # or npm start",
                "```",
                "Open `http://localhost:3000/` in your browser.",
            ])
        elif 'main.py' in file_names or 'app.py' in file_names:
            target = 'main.py' if 'main.py' in file_names else 'app.py'
            usage_steps.extend([
                f"Run the application entry point:",
                "```bash",
                f"python {target}",
                "```",
            ])
        else:
            usage_steps.extend([
                "Refer to the build commands above to launch the application.",
            ])

        tech_bullets = "\n".join(f"- {t}" for t in tech_stack) if tech_stack else f"- {language}"
        req_bullets = "\n".join(req_items)
        install_text = "\n".join(install_steps)
        usage_text = "\n".join(usage_steps)

        # Synthesize Markdown document
        doc = f"""# {name}

{description}

---

## Overview

**{name}** is a software repository built with {fw_label}. It provides a modular codebase designed for high maintainability, efficiency, and extensibility.

---

## Key Features

- **Robust Architecture:** Clean separation of concerns and modular component structure.
- **Dependency Tracking:** Compatible with standard dependency manifests for vulnerability auditing.
- **Cross-Platform:** Can be developed, tested, and deployed across Windows, macOS, and Linux.

---

## Technologies Used

{tech_bullets}

---

## Requirements

Before setting up the project, ensure you have the following installed:

{req_bullets}

---

## Installation & Setup

{install_text}

---

## Configuration

Create a local `.env` configuration file if your project relies on environment secrets:

```env
DEBUG=True
SECRET_KEY=your_development_secret_key
DATABASE_URL=sqlite:///db.sqlite3
```

---

## Usage

{usage_text}

---

## Project Structure

```text
{structure_tree}
```

---

## Contributing

Contributions, issues, and feature requests are welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

Distributed under the open-source software terms. See `LICENSE` for details.
"""
        return doc.strip() + "\n"
