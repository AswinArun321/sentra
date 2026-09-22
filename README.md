# SENTRA — Repository Security & Intelligence Platform

> **Know your code. Secure what you ship.**

SENTRA automatically analyzes software repositories to identify dependency, vulnerability, license, documentation, and repository health risks — delivering comprehensive security visibility in one unified platform.

![SENTRA Dashboard](docs/screenshot.png)

---

## Core Capabilities

- 🔗 **GitHub Repository Integration** — Seamlessly connect GitHub accounts with strict per-user account isolation
- ⚡ **Automatic Repository Inspection** — Automatic tree inspection, manifest discovery, and background analysis
- 🔍 **Dependency Detection** — Automatically detects and parses `package.json`, `requirements.txt`, and more
- 🛡️ **Vulnerability Analysis** — Real-time vulnerability lookup against OSV.dev and national databases
- 📜 **Open-Source License Analysis** — Identifies, verifies, and categorizes licenses to flag compliance risks
- 📖 **README Documentation Health** — Evaluates repository documentation completeness and generates recommendations
- 🏥 **Repository Health Metrics** — Tracks maintenance health, commit activity, stale packages, and risk signals
- 📊 **Intelligent Risk Scoring** — Multi-factor weighted risk engine (Security, License, Maintenance, Dependency)
- 📋 **CycloneDX SBOM & Reports** — Export CycloneDX 1.4 standard SBOMs and downloadable JSON security audits
- 🔐 **Secure Multi-User Platform** — Django session and JWT authentication with protected credential management

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.1 + Django REST Framework |
| Database | SQLite (development) / PostgreSQL (production) |
| Authentication | Django Sessions + SimpleJWT |
| Frontend | Django Templates + Vanilla JavaScript + Chart.js |
| Styling | Custom CSS (Responsive Dark / Light Adaptive Theme) |
| Vulnerability Data | OSV.dev API (open, no key required) + optional NVD |
| Package Metadata | PyPI JSON API + npm Registry |
| Standards | CycloneDX 1.4 JSON SBOM |

---

## Quick Start

### 1. Clone and install dependencies

```bash
git clone https://github.com/yourname/SENTRA.git
cd SENTRA
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings (GitHub OAuth credentials, Secret Key, etc.)
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Create admin user

```bash
python manage.py createsuperuser
```

### 5. Start the development server

```bash
python manage.py runserver
```

Visit [http://localhost:8000](http://localhost:8000)

---

## Default Test Credentials

After running migrations and fixtures, you can log in with:

```text
Email:    admin@sentra.dev
Password: SentraPassword2026!
```

---

## Usage Workflow

1. **Sign In** — Log into your SENTRA account or register a new workspace profile.
2. **Connect GitHub (Optional)** — Link your GitHub account securely to import repositories with a single click.
3. **Register / Import Repository** — Import directly from GitHub or create a workspace project and upload `package.json` / `requirements.txt`.
4. **Automatic Analysis** — SENTRA analyzes repository tree, manifests, README documentation, licenses, and CVEs.
5. **Review Risk & Compliance** — Inspect vulnerability severities, license categorization, README audit scores, and overall risk rating.
6. **Export Security Assets** — Download standard JSON security audit reports and CycloneDX 1.4 SBOMs.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` | Register a new user |
| POST | `/api/auth/login/` | Login and get JWT tokens |
| GET | `/api/auth/profile/` | Get user profile |
| GET | `/api/dashboard/overview/` | Dashboard metrics & summary |
| GET | `/api/projects/` | List user projects |
| POST | `/api/projects/` | Create project |
| POST | `/api/projects/{id}/scan/` | Upload manifest and execute scan |
| GET | `/api/projects/{id}/analysis-status/` | Check automatic analysis progress |
| GET | `/api/github/status/` | Check GitHub connection status |
| GET | `/api/github/repositories/` | List user's GitHub repositories |
| POST | `/api/github/import/` | Import GitHub repository as project |
| GET | `/api/scans/{id}/` | Get scan details |
| GET | `/api/scans/{id}/dependencies/` | List detected dependencies |
| GET | `/api/scans/{id}/vulnerabilities/` | List detected vulnerabilities |
| GET | `/api/scans/{id}/report/` | Get JSON report |
| GET | `/api/admin/dashboard/` | Platform-wide admin telemetry & KPIs (Staff only) |
| GET | `/api/admin/users/` | List and search all platform users (Staff only) |
| POST | `/api/admin/users/{id}/suspend/` | Suspend user account with reason (Staff only) |
| POST | `/api/admin/users/{id}/activate/` | Activate user account (Staff only) |
| GET | `/api/admin/audit-logs/` | Query administrative audit logs (Staff only) |
| GET | `/api/admin/system/` | System diagnostic & health checks (Staff only) |

---

## SENTRA Admin Console

SENTRA includes a dedicated, secure **Admin Console** accessible at:

```text
Web Console:  /admin-console/
REST API:     /api/admin/
```

Django's built-in administrative interface remains available at `/admin/`.

### Administrative Capabilities

1. **Platform Overview & Telemetry** — Real-time KPI cards and Chart.js graphs tracking user growth, scan execution velocity, vulnerability severity distribution, and open-source license usage.
2. **User Account Governance** — Search, filter, and paginate users; inspect individual profiles, scan history, and project risk; safely activate, deactivate, suspend, or reactivate accounts with audit records.
3. **Repository & Project Monitoring** — Inspect all software projects across user workspaces with risk scoring, analysis statuses, and GitHub sources.
4. **Scan Execution Monitoring** — Live monitoring of running, completed, pending, and failed scans with duration metrics and error diagnostics.
5. **Vulnerability & Supply-Chain Intelligence** — Global aggregation of CVEs, GHSAs, CVSS severity ratings, and affected packages across all repositories.
6. **Dependency & License Governance** — Cross-project package frequency tracking and open-source license compliance categorization (Permissive, Copyleft, Unknown).
7. **Reports & SBOM Management** — Controlled inspection and audited downloads of CycloneDX 1.4 SBOMs and JSON security assessments.
8. **GitHub Connection Monitoring** — Connection status telemetry without ever exposing OAuth access tokens, client secrets, or refresh tokens.
9. **Administrative Audit Trail** — Immutable `AdminAuditLog` logging every status adjustment, privilege modification, report download, and configuration change with actor, IP address, and timestamp.
10. **System Health Diagnostics** — Live health probes verifying database latency, Django runtime, media storage, OSV.dev API connectivity, and GitHub API status.
11. **Safe Runtime Platform Settings** — Administrative UI controls for platform name, maintenance mode, upload limits, scan timeouts, and report retention windows without exposing environment secrets.

### Role-Based Access Control

- **Standard User (`USER`)**: Strict isolation limited solely to their personal workspaces, repositories, and scan findings. Non-staff attempts to access the admin console are rejected with `403 Forbidden`.
- **Administrator (`STAFF`)**: Authorized platform operators with access to the SENTRA Admin Console and administrative APIs.
- **Superuser (`SUPERADMIN`)**: Full platform control and administrative delegation.

### Creating Administrators

To grant administrative access, create or promote a user with Django's management commands:

```bash
python manage.py createsuperuser
```

---

## Project Structure

```text
SENTRA/
├── config/              # Django project settings & URLs
├── accounts/            # User authentication & profile management
├── admin_panel/         # Dedicated SENTRA Admin Console & API
│   ├── models.py        # AdminAuditLog, PlatformSetting, UserAccountStatus
│   ├── permissions.py   # IsSENTRAAdminUser & @admin_required
│   ├── services.py      # Telemetry, User governance, Audit, and Health services
│   ├── serializers.py   # Safe REST API serializers (zero secret leakage)
│   ├── views.py         # Admin console template views (/admin-console/)
│   ├── api_views.py     # Admin REST API views (/api/admin/)
│   ├── templates/       # Dark-first admin operational templates
│   └── static/          # Dedicated admin CSS & JavaScript
├── projects/            # Repository project workspaces
├── scans/               # Scan lifecycle & tracking
├── dependencies/        # Dependency models & catalog
├── vulnerabilities/     # Vulnerability & RiskFinding models
├── github_integration/  # GitHub OAuth, repository sync & auto-analysis
├── reports/             # Report generation (JSON + CycloneDX SBOM)
├── scanner/             # Core scanning engine & parsers
└── frontend/            # Adaptive UI templates & static assets
```

---

## Disclaimer

> SENTRA provides automated software dependency risk, repository health, and open-source compliance analysis. Its findings are informational and should not be treated as legal or security guarantees. Final compliance decisions should be reviewed by qualified security or legal professionals.

---

## License

MIT
