# SENTRA — Complete Project Rename Plan

## 1. Project Identity

Replace the existing product name **LicenseLens** with:

> **SENTRA — Repository Security & Intelligence Platform**

**Recommended tagline:** `Know your code. Secure what you ship.`

The rename must cover the entire project: source code, Django configuration, templates, JavaScript, CSS, documentation, reports, environment configuration, deployment files, GitHub integration, and product branding.

---

## 2. Rename Objective

The final application should be presented entirely as **SENTRA**, while preserving all existing functionality and user data.

### Goals

1. Replace all user-facing LicenseLens branding with SENTRA.
2. Rename the Django project package to `sentra` if the current root package is named `licenselens`.
3. Update imports, settings, ASGI, WSGI, and `manage.py`.
4. Update environment/configuration names where they are project-specific.
5. Update GitHub OAuth and repository-import messaging.
6. Preserve per-user GitHub account isolation.
7. Preserve automatic GitHub repository analysis.
8. Update README, documentation, reports, and generated output.
9. Update frontend branding, browser titles, headers, and authentication pages.
10. Verify that no unintended old branding remains.

---

# 3. Important Rename Rule

Do **not** blindly replace every occurrence of `LicenseLens`.

Classify occurrences first.

### A. User-facing branding — MUST change

Examples:

```text
LicenseLens
LicenseLens Dashboard
LicenseLens Report
Welcome to LicenseLens
```

Change to SENTRA equivalents.

### B. Technical identifiers — change when safe

Examples:

```text
licenselens
LICENSELENS_*
licenselens_project
```

### C. Historical migrations — normally DO NOT change

Existing Django migration files represent historical state. Do not rewrite old migrations simply to remove the old name.

If database schema changes are actually required, create proper new migrations.

### D. External identifiers — do not blindly change

Do not rename third-party API names, GitHub API fields, dependency names, or external service identifiers.

---

# 4. Current Architecture to Preserve

The project uses:

- Django 5.1.4
- Django REST Framework
- SimpleJWT
- django-cors-headers
- SQLite for development
- Python
- Django templates
- HTML/CSS/vanilla JavaScript
- Chart.js
- GitHub API/OAuth
- OSV vulnerability API
- PyPI/npm metadata
- CycloneDX SBOM

Existing Django apps:

```text
accounts
projects
scans
dependencies
vulnerabilities
reports
scanner
frontend
```

These app names should remain unless there is a separate requirement to restructure them.

---

# 5. Phase 1 — Repository-Wide Audit

Search the complete repository for:

```text
LicenseLens
LICENSELENS
licenselens
license_lens
license-lens
License Lens
```

Inspect at minimum:

```text
*.py
*.html
*.js
*.css
*.json
*.md
*.txt
*.env
*.ini
*.cfg
*.toml
*.yml
*.yaml
*.xml
*.sql
```

Also inspect:

```text
manage.py
Django settings
URL configuration
templates
static files
scanner code
report generation
README
documentation
Docker files
GitHub workflows
```

Create a list of all matches before changing files.

---

# 6. Phase 2 — Product Branding

Use:

```text
SENTRA
```

as the primary product name.

Use the full identity where appropriate:

```text
SENTRA — Repository Security & Intelligence Platform
```

Recommended tagline:

```text
Know your code. Secure what you ship.
```

Update:

- Login
- Registration
- Dashboard
- Header/sidebar
- Projects
- GitHub repository pages
- Scan pages
- Dependency pages
- Vulnerability pages
- Reports
- Empty states
- Error messages
- Browser titles
- Documentation

---

# 7. Phase 3 — Django Project Package

If the root Django package is currently:

```text
licenselens/
```

rename it to:

```text
sentra/
```

Target structure:

```text
project-root/
├── manage.py
├── sentra/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── accounts/
├── projects/
├── scans/
├── dependencies/
├── vulnerabilities/
├── reports/
├── scanner/
└── frontend/
```

Update imports such as:

```python
from licenselens.settings import ...
```

to:

```python
from sentra.settings import ...
```

Update:

```text
DJANGO_SETTINGS_MODULE=licenselens.settings
```

to:

```text
DJANGO_SETTINGS_MODULE=sentra.settings
```

---

# 8. Phase 4 — manage.py

Update:

```python
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "licenselens.settings"
)
```

to:

```python
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "sentra.settings"
)
```

Then run:

```bash
python manage.py check
```

---

# 9. Phase 5 — Django Settings

Update project-level references:

```python
ROOT_URLCONF = "sentra.urls"

WSGI_APPLICATION = "sentra.wsgi.application"

ASGI_APPLICATION = "sentra.asgi.application"
```

Search the settings file for all remaining old project-package references.

---

# 10. Phase 6 — Environment Variables

Inspect:

```text
.env
.env.example
deployment configuration
CI/CD variables
settings.py
```

If project-specific variables use the old name, migrate them to SENTRA naming.

For example:

```text
LICENSELENS_GITHUB_CLIENT_ID
LICENSELENS_GITHUB_CLIENT_SECRET
```

can become:

```text
SENTRA_GITHUB_CLIENT_ID
SENTRA_GITHUB_CLIENT_SECRET
```

Do not rename variables required by third-party libraries.

Never commit real secrets.

---

# 11. Phase 7 — GitHub Integration

Update product branding in:

- GitHub OAuth screens
- OAuth callback messages
- repository import pages
- repository selection pages
- import success/failure messages
- API responses
- documentation

Examples:

```text
Connect LicenseLens to GitHub
```

becomes:

```text
Connect SENTRA to GitHub
```

and:

```text
Import repository into LicenseLens
```

becomes:

```text
Import repository into SENTRA
```

Do not rename GitHub's external API terminology.

---

# 12. Phase 8 — Preserve Multi-User GitHub Isolation

The rename must not change the security model.

Maintain:

```text
SENTRA Account
      |
      v
User's GitHubConnection
      |
      v
User's GitHub Access Token
      |
      v
GitHub API
      |
      v
User's Repositories
```

Verify that:

- Account A sees only Account A's GitHub repositories.
- Account B sees only Account B's GitHub repositories.
- Disconnecting A does not affect B.
- GitHub tokens are not exposed to frontend code.
- Tokens are not stored in localStorage.
- Tokens are not placed in URLs.
- OAuth `state` validation remains enabled.

---

# 13. Phase 9 — Preserve Automatic Repository Analysis

The SENTRA rename must preserve the automatic GitHub analysis workflow:

```text
GitHub Repository
        |
        v
SENTRA Import
        |
        v
Repository Inspection
        |
        +-- README detection
        +-- License detection
        +-- Manifest detection
        +-- Dependency extraction
        +-- Vulnerability analysis
        +-- License analysis
        +-- Repository health
        +-- Security signals
        |
        v
Risk Engine
        |
        v
SENTRA Repository Risk Score
```

All user-facing messages should refer to SENTRA.

---

# 14. Phase 10 — README Health

Keep the README analysis feature.

Display:

```text
README Health
```

If missing:

```text
README Missing

Your repository does not contain a README file.

Recommendation:
Add a README to explain the project's purpose, setup,
usage, and contribution guidelines.
```

Remove old product branding from recommendations.

---

# 15. Phase 11 — Frontend Branding

Search all templates, including:

```text
templates/
frontend/templates/
accounts/templates/
projects/templates/
scans/templates/
reports/templates/
```

Update:

- `<title>`
- Logo
- Navbar
- Sidebar
- Footer
- Headings
- Buttons
- Empty states
- Loading screens
- Alerts
- Authentication pages

Recommended titles:

```text
SENTRA | Dashboard
SENTRA | Projects
SENTRA | Repositories
SENTRA | Repository Analysis
SENTRA | Vulnerabilities
SENTRA | Reports
```

Main title:

```text
SENTRA — Repository Security & Intelligence Platform
```

---

# 16. Phase 12 — Logo and Brand Mark

Replace any text-based LicenseLens logo with:

```text
SENTRA
```

Optional subtitle:

```text
Repository Security & Intelligence
```

Keep the initial brand mark simple and professional.

---

# 17. Phase 13 — Dashboard

The dashboard should reflect SENTRA's broader scope rather than being license-focused.

Recommended essential sections:

```text
SENTRA
Repository Security & Intelligence

Repositories
Dependencies
Vulnerabilities
Security Score

Recent Repository Analyses
Security Findings
Repository Health
```

Avoid unnecessary decorative cards.

---

# 18. Phase 14 — Header

Recommended structure:

```text
SENTRA
------------------------------------------------
Dashboard | Projects | Repositories

                              Refresh
                              + New Project

                              User Profile
```

Keep working actions such as:

- Refresh
- New Project

Remove non-functional mail/notification buttons if those features do not exist.

Separate SENTRA account information from GitHub identity:

```text
SENTRA Account
username/email

GitHub
@github_username
```

---

# 19. Phase 15 — API Responses

Search views, serializers, and response dictionaries.

Example:

```python
return Response({
    "message": "Repository imported successfully into SENTRA."
})
```

Do not rename domain fields merely because they contain `license`.

These should remain when they describe actual functionality:

```text
license
licenses
license_risk
license_analyzer
```

---

# 20. Phase 16 — Scanner and Analysis Code

Inspect:

```text
scanner/
dependencies/
vulnerabilities/
reports/
projects/
scans/
```

Change only product-brand references.

Example:

```text
Scanned by LicenseLens
```

becomes:

```text
Scanned by SENTRA
```

Do not unnecessarily rename internal security concepts.

---

# 21. Phase 17 — Generated Reports

Update ReportLab/report-generation code.

Recommended report header:

```text
SENTRA
Repository Security & Intelligence Report

Repository: example-project
Analysis Date: ...
Security Score: ...
Overall Risk: ...
```

Footer:

```text
Generated by SENTRA
```

Search all report templates and Python generators.

---

# 22. Phase 18 — Static Files

Inspect:

```text
static/
frontend/static/
css/
js/
images/
```

Check:

- JavaScript messages
- CSS classes
- SVG text
- logo assets
- HTML fragments
- chart labels
- alerts

Rename product-specific identifiers only when safe.

---

# 23. Phase 19 — Documentation

Update:

```text
README.md
PLAN.md
plan.md
docs/
API documentation
architecture documentation
assignment documentation
project reports
```

Recommended README opening:

```markdown
# SENTRA — Repository Security & Intelligence Platform

Know your code. Secure what you ship.

SENTRA automatically analyzes software repositories to identify
dependency, vulnerability, license, documentation, and repository
health risks.
```

Core capabilities:

```text
GitHub repository integration
Automatic repository inspection
Dependency detection
Vulnerability analysis
Open-source license analysis
README health checks
Repository health analysis
Risk scoring
Security reports
Multi-user GitHub account isolation
```

---

# 24. Phase 20 — Package Metadata

Inspect:

```text
pyproject.toml
setup.py
setup.cfg
package.json
Dockerfile
docker-compose.yml
```

Update project-specific metadata such as:

```toml
name = "sentra"
description = "Repository Security & Intelligence Platform"
```

Do not change third-party dependency names.

---

# 25. Phase 21 — Docker and Deployment

Inspect:

```text
Dockerfile
docker-compose.yml
docker/
Procfile
gunicorn configuration
deployment scripts
```

Change project-specific names such as:

```text
licenselens-web
```

to:

```text
sentra-web
```

Do not change external Docker image names.

---

# 26. Phase 22 — GitHub Actions

Inspect:

```text
.github/workflows/
```

Update:

- workflow names
- project-specific variables
- Docker image names
- deployment names
- comments
- badges
- documentation

Do not change third-party GitHub Action identifiers.

---

# 27. Phase 23 — Database Safety

Do not rename database tables or rewrite migrations simply for branding.

First determine whether an old name is:

- a Django app/table identifier
- historical migration state
- a genuinely product-specific database identifier

Preserve existing user/project/scan data.

If a schema rename is actually required:

1. Back up the database.
2. Create a proper Django migration.
3. Use Django rename operations.
4. Test on a fresh database.
5. Test against an existing database.
6. Verify all existing records remain accessible.

Never delete migration history.

---

# 28. Phase 24 — URL and Route Names

If product-specific URLs exist:

```text
/licenselens/
/licenselens-dashboard/
```

prefer clean routes:

```text
/
/dashboard/
/projects/
/repositories/
```

Where practical, preserve old routes temporarily through redirects instead of immediately breaking existing bookmarks.

---

# 29. Phase 25 — Authentication Pages

### Login

```text
Welcome back to SENTRA
```

### Registration

```text
Create your SENTRA account
```

### Password reset

```text
Reset your SENTRA password
```

### GitHub

```text
Connect GitHub to SENTRA
```

---

# 30. Phase 26 — Error Messages

Search:

```text
404
500
authentication errors
permission errors
GitHub errors
scan errors
API errors
```

Example:

```text
LicenseLens could not analyze this repository.
```

becomes:

```text
SENTRA could not analyze this repository.
```

---

# 31. Phase 27 — Git Repository Metadata

Review:

```text
.gitignore
README badges
GitHub repository description
issue templates
pull request templates
CI/CD configuration
```

If desired, the remote repository can separately be renamed to:

```text
sentra
```

or:

```text
sentra-repository-security
```

The code rename should not depend on changing the remote repository name.

---

# 32. Phase 28 — Final Search

Run a repository-wide search for:

```text
LicenseLens
LICENSELENS
licenselens
license_lens
license-lens
License Lens
```

Example with Git:

```bash
git grep -inE "licenselens|license[_ -]?lens"
```

Example PowerShell:

```powershell
Get-ChildItem -Recurse -File |
  Select-String -Pattern "LicenseLens|LICENSELENS|licenselens|license_lens|license-lens|License Lens"
```

Every remaining result must be classified as:

1. historical migration data,
2. compatibility code,
3. external identifier,
4. legitimate software-license terminology.

All unintended branding references must be removed.

---

# 33. Phase 29 — Testing

Run:

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
python manage.py test
```

If pytest is configured:

```bash
pytest
```

Also verify that the server starts:

```bash
python manage.py runserver
```

---

# 34. Phase 30 — Manual Smoke Test

Verify:

### Authentication

- Login
- Registration
- Logout
- Password functionality

### Dashboard

- SENTRA branding
- Dashboard loads
- Refresh works
- New Project works
- Header is functional

### GitHub

- OAuth works
- Correct GitHub account is connected
- Repository list loads
- Repository import works
- User isolation works

### Repository Analysis

- Repository inspection works
- Manifest detection works
- Dependencies are extracted
- Vulnerabilities are analyzed
- License analysis works
- README detection works
- Risk score is calculated

### Reports

- Report generation works
- Report says SENTRA
- No accidental LicenseLens branding remains

---

# 35. Final Recommended Project Structure

If the Django root package is currently named `licenselens`, the target structure is:

```text
SENTRA/
│
├── manage.py
│
├── sentra/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── accounts/
├── projects/
├── scans/
├── dependencies/
├── vulnerabilities/
├── reports/
├── scanner/
├── frontend/
│
├── static/
├── templates/
│
├── .env.example
├── requirements.txt
└── README.md
```

---

# 36. Definition of Done

The rename is complete when:

- [ ] Product name is SENTRA
- [ ] Full product identity is updated
- [ ] Tagline is updated
- [ ] Django root package renamed to `sentra` where applicable
- [ ] `manage.py` updated
- [ ] Django settings updated
- [ ] ASGI/WSGI updated
- [ ] Imports updated
- [ ] Environment variables reviewed
- [ ] GitHub OAuth branding updated
- [ ] Multi-user GitHub isolation preserved
- [ ] Automatic GitHub repository analysis preserved
- [ ] README detection preserved
- [ ] Dependency analysis preserved
- [ ] Vulnerability analysis preserved
- [ ] License analysis preserved
- [ ] Risk scoring preserved
- [ ] Dashboard updated
- [ ] Header updated
- [ ] Authentication pages updated
- [ ] API messages updated
- [ ] Reports updated
- [ ] Static files reviewed
- [ ] Documentation updated
- [ ] README rewritten
- [ ] Docker/deployment reviewed
- [ ] GitHub Actions reviewed
- [ ] Database preserved
- [ ] Historical migrations preserved
- [ ] `python manage.py check` passes
- [ ] `python manage.py makemigrations --check` passes
- [ ] Tests pass
- [ ] Manual smoke test passes
- [ ] Final repository-wide search completed
- [ ] No unintended LicenseLens references remain

---

# 37. Final Product Positioning

The project should no longer be presented as a license-focused application.

### Old

```text
LicenseLens
Open-source license auditing platform
```

### New

```text
SENTRA
Repository Security & Intelligence Platform
```

### Product description

```text
SENTRA automatically inspects software repositories,
analyzes dependencies and vulnerabilities, evaluates
open-source license compliance, checks repository health,
and produces an overall repository risk assessment.
```

### Final identity

# SENTRA

## Repository Security & Intelligence Platform

**Know your code. Secure what you ship.**
