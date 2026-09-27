# SENTRA — Repository Security & Intelligence Platform

> **Know your code. Secure what you ship.**

SENTRA is a Django-based repository security and intelligence platform that helps developers understand the security, dependency, licensing, documentation, and maintenance health of their software repositories.

It connects with GitHub, discovers repository manifests, analyzes dependencies and vulnerabilities, evaluates open-source licenses and repository health, calculates an overall risk profile, and provides security reports and SBOM exports through a unified interface.

---

## Overview

Modern software projects depend heavily on third-party packages and open-source components. As repositories grow, it becomes difficult to manually track:

- What dependencies a project uses
- Whether dependencies contain known vulnerabilities
- Which open-source licenses are present
- Whether repository documentation is complete
- Which maintenance signals indicate potential risk
- How different risk areas affect the overall repository security posture

SENTRA brings these checks together into one repository-focused security workflow.

### Analysis Flow

```text
GitHub Repository
       │
       ▼
Repository Inspection
       │
       ▼
Manifest Detection
       │
       ├── package.json
       ├── requirements.txt
       └── Supported manifests
       │
       ▼
Dependency Analysis
       │
       ├── Vulnerability Analysis
       ├── License Analysis
       ├── Maintenance Analysis
       └── Documentation / README Health
       │
       ▼
Risk Engine
       │
       ▼
Security Intelligence
       │
       ├── Dashboard
       ├── Findings
       ├── Reports
       └── CycloneDX SBOM
```

---

## Key Features

### GitHub Integration

- Secure GitHub OAuth integration
- Per-user GitHub account association
- Repository discovery and import
- Repository ownership and access isolation
- Repository metadata and source inspection

### Repository Analysis

- Automatic repository tree inspection
- Manifest discovery
- Dependency extraction
- README/documentation health checks
- Repository maintenance signals
- Analysis status tracking

### Dependency Intelligence

- Dependency discovery from supported manifests
- Package metadata lookup
- Dependency-level security analysis
- Dependency health visibility

### Vulnerability Analysis

- Known vulnerability lookup using OSV.dev
- Vulnerability severity and affected-package information
- Security findings linked to repository dependencies
- Centralized vulnerability visibility

### License Intelligence

- Open-source license identification
- License categorization
- License risk visibility
- Project-level license reporting

### Repository Health

SENTRA evaluates repository signals such as:

- Documentation completeness
- Maintenance activity
- Dependency freshness
- Repository-level risk indicators

### Risk Scoring

SENTRA combines multiple analysis areas into an overall repository risk profile, including:

- Security
- Dependencies
- Licensing
- Maintenance

The goal is to turn individual findings into a clear, actionable view of repository risk.

### Reports & SBOM

- Security audit reports
- CycloneDX 1.4 SBOM generation
- Downloadable analysis results
- Repository-level security summaries

### Multi-User Security

- Django authentication
- JWT-protected API access
- User-specific project isolation
- GitHub connection isolation
- Staff-only administrative access
- Protected administrative operations

---

## Technology Stack

| Area | Technology |
|---|---|
| Backend | Django 5.1.4 |
| API | Django REST Framework 3.15.2 |
| Authentication | Django Sessions + SimpleJWT |
| Database (Dev) | SQLite |
| Database (Prod) | PostgreSQL |
| Production Server | Gunicorn |
| Static Files | WhiteNoise |
| Frontend | Django Templates, HTML, CSS, Vanilla JavaScript |
| Charts | Chart.js |
| Vulnerability Intelligence | OSV.dev API |
| Package Metadata | PyPI JSON API + npm Registry |
| SBOM Standard | CycloneDX 1.4 |
| Reports | JSON + PDF/report generation |
| External Integration | GitHub OAuth / GitHub API |
| Deployment | Render (Web Service + PostgreSQL) |

---

## Application Areas

SENTRA is organized around the following product areas:

### Public Website

- Home
- About
- Contact

The public interface introduces SENTRA and explains its repository security workflow.

### User Application

- Dashboard
- Projects / Repositories
- Scans
- Dependencies
- Vulnerabilities
- Licenses
- Reports
- Profile / GitHub connection
- Account management

### Admin Console

A dedicated administrative console provides controlled platform-level management for authorized staff.

---

## Admin Console

SENTRA includes a separate admin console for platform administration.

### Administrative Areas

```text
Admin Console
├── Dashboard
├── Users
├── Projects
├── GitHub Connections
├── Scans
├── Vulnerabilities
├── Dependencies
├── Licenses
├── Reports
├── Audit Logs
├── System Health
└── Platform Settings
```

### Administration Capabilities

- User management
- Account activation and suspension
- Project and repository monitoring
- GitHub connection monitoring
- Scan monitoring
- Vulnerability and dependency oversight
- License visibility
- Report management
- Administrative audit logging
- System health checks
- Safe runtime platform settings

Sensitive credentials such as Django secret keys, OAuth client secrets, API tokens, and database passwords are kept outside the administrative interface and should be supplied through the deployment environment.

---

## Security & Access Model

SENTRA follows a user-isolated application model.

```text
SENTRA User
    │
    ├── Projects
    │     └── Scans
    │           ├── Dependencies
    │           ├── Vulnerabilities
    │           └── Reports
    │
    └── GitHub Connection
          └── Accessible Repositories
```

A standard user should only be able to access resources associated with their account.

Administrative access is separated from normal user access through role-based authorization.

---

## Quick Start

### 1. Clone the repository

Clone the SENTRA repository and move into the project directory.

```bash
git clone <repository-url>
cd SENTRA
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

On macOS/Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file based on the project's environment configuration.

Typical deployment values include:

```env
SECRET_KEY=your-secret-key
DEBUG=True

GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

Do not commit `.env` or other files containing secrets to Git.

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Create an administrator

```bash
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

## Typical User Workflow

```text
Create Account
      │
      ▼
Sign In
      │
      ▼
Connect GitHub
      │
      ▼
Select Repository
      │
      ▼
Import Repository
      │
      ▼
Inspect Repository
      │
      ▼
Detect Manifests
      │
      ▼
Analyze Dependencies
      │
      ├── Vulnerabilities
      ├── Licenses
      ├── README Health
      └── Maintenance Signals
      │
      ▼
Calculate Risk
      │
      ▼
Review Findings
      │
      ▼
Generate Report / SBOM
```

Manual manifest-based scanning can also be used where repository import or automatic analysis is not available.

---

## Project Structure

```text
SENTRA/
│
├── config/                  # Django project configuration and URLs
├── accounts/                # Authentication, users and profiles
├── admin_panel/             # SENTRA Admin Console and administration APIs
├── projects/                # Repository projects and workspaces
├── scans/                   # Scan lifecycle and scan records
├── dependencies/            # Dependency models and analysis data
├── vulnerabilities/         # Vulnerability and risk finding models
├── github_integration/      # GitHub OAuth, repository import and analysis
├── reports/                 # Security reports and SBOM generation
├── scanner/                 # Scanning engine, parsers and risk analysis
├── frontend/                # User-facing templates and static assets
├── manage.py
├── requirements.txt
└── README.md
```

---

## API

SENTRA exposes REST APIs for authentication, projects, repository analysis, findings, reports, GitHub integration, and administration.

### Main API Groups

| Area | Purpose |
|---|---|
| Authentication | Registration, login and profile management |
| Projects | Repository/project management |
| GitHub | Connection, repository discovery and import |
| Scans | Scan execution and analysis status |
| Dependencies | Detected dependency information |
| Vulnerabilities | Security findings |
| Licenses | License intelligence |
| Reports | Security reports and SBOM-related outputs |
| Administration | Staff-only platform management |

API endpoints are protected according to their authentication and authorization requirements.

---

## Security Considerations

SENTRA is designed with security and account isolation as core requirements.

Key considerations include:

- Never expose GitHub OAuth access tokens through the UI or API responses.
- Keep secrets in environment variables or a secure deployment secret store.
- Enforce ownership checks on user resources.
- Restrict administrative APIs to authorized staff.
- Validate OAuth state during GitHub authentication.
- Avoid committing `.env` files or credentials to source control.
- Apply appropriate production security settings before deployment.
- Review automated findings before making security or compliance decisions.

---

## Development

### Run Django checks

```bash
python manage.py check
```

### Create migrations

```bash
python manage.py makemigrations
```

### Apply migrations

```bash
python manage.py migrate
```

### Run the development server

```bash
python manage.py runserver
```

### Run tests

```bash
python manage.py test
```

---

## Deployment

SENTRA is designed for deployment on **Render** using PostgreSQL, Gunicorn, and WhiteNoise.

### Architecture

```text
User → HTTPS → Render Web Service (Django + Gunicorn + WhiteNoise) → PostgreSQL
```

### Prerequisites

- A [Render](https://render.com) account
- A GitHub OAuth application (see GitHub OAuth section below)
- The repository pushed to GitHub

### Environment Variables

Set the following in Render's environment variable configuration. Do not commit real secrets to version control.

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Strong random Django secret key (Render can auto-generate this) |
| `DEBUG` | ✅ | Must be `False` in production |
| `ALLOWED_HOSTS` | ✅ | Your Render domain, e.g. `sentra.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | ✅ | Your HTTPS origin, e.g. `https://sentra.onrender.com` |
| `DATABASE_URL` | ✅ | PostgreSQL connection string (auto-set by Render Blueprint) |
| `GITHUB_CLIENT_ID` | ✅ | GitHub OAuth application client ID |
| `GITHUB_CLIENT_SECRET` | ✅ | GitHub OAuth application client secret |
| `GITHUB_REDIRECT_URI` | ✅ | `https://your-domain.onrender.com/github/callback/` |
| `OSV_API_URL` | — | Defaults to `https://api.osv.dev/v1/query` |
| `NVD_API_KEY` | — | Optional NVD API key for enhanced vulnerability data |

### Render Blueprint Deployment

1. Push this repository to GitHub.
2. In Render, select **New → Blueprint** and connect the repository.
3. Render reads `render.yaml` and creates the web service and PostgreSQL database automatically.
4. Set the secret environment variables (`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_REDIRECT_URI`) in the Render dashboard.
5. Deploy.

### Manual Deployment Steps

If not using the Blueprint:

1. Create a **PostgreSQL** instance in Render. Copy the external connection string.
2. Create a **Web Service** connected to the repository.
3. Set **Build Command** to `./build.sh`
4. Set **Start Command** to:
   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```
5. Set the environment variables listed above.
6. Deploy.

### Build Script

`build.sh` runs automatically on each deploy:

```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

### Static Files

WhiteNoise serves static files directly from Gunicorn — no separate CDN or Nginx required.

### After First Deployment

```bash
# Create the superuser (run via Render's Shell)
python manage.py createsuperuser
```

Then configure the SENTRA Admin Console at `/admin-console/`.

### GitHub OAuth Configuration

1. Go to [GitHub Developer Settings](https://github.com/settings/developers).
2. Create a new OAuth App (or update your existing development app).
3. Set the **Authorization callback URL** to:
   ```text
   https://your-domain.onrender.com/github/callback/
   ```
4. Set `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, and `GITHUB_REDIRECT_URI` in Render's environment variables.

> **Important:** Never use an HTTP callback URL in production. GitHub OAuth requires HTTPS for production applications.

### Health Check

SENTRA exposes a lightweight health endpoint at `/health/` that returns:

```json
{"status": "ok"}
```

Render uses this endpoint to verify the service is healthy after deployment.

---

## Limitations

SENTRA provides automated repository security and open-source intelligence based on the data and analysis sources available to it.

Automated analysis can produce incomplete or context-dependent findings. Results should therefore be reviewed before making security, licensing, or compliance decisions.

SENTRA is not a replacement for a complete enterprise security program, professional security assessment, or legal review.

---

## Roadmap

Potential future improvements include:

- Expanded manifest and ecosystem support
- Deeper dependency relationship analysis
- Improved repository health intelligence
- More detailed security trends
- CI/CD integration
- Pull-request security checks
- Expanded SBOM capabilities
- Additional reporting formats
- Advanced organization-level security policies
- Broader repository security integrations

---

## License

This project is licensed under the **MIT License**.

See the `LICENSE` file for the full license text.

---

## Project Identity

**SENTRA**  
Repository Security & Intelligence Platform

> **Know your code. Secure what you ship.**
