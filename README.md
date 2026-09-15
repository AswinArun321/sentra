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

---

## Project Structure

```text
SENTRA/
├── config/              # Django project settings & URLs
├── accounts/            # User authentication & profile management
├── projects/            # Repository project workspaces
├── scans/               # Scan lifecycle & tracking
├── dependencies/        # Dependency models & catalog
├── vulnerabilities/     # Vulnerability & RiskFinding models
├── github_integration/  # GitHub OAuth, repository sync & auto-analysis
├── reports/             # Report generation (JSON + CycloneDX SBOM)
├── scanner/             # Core scanning engine & parsers
│   ├── parsers/         # Manifest parsers (package.json, requirements.txt)
│   ├── vulnerability.py # OSV API integration
│   ├── license_analyzer.py # License detection & categorization
│   ├── maintenance.py   # Maintenance health & metrics
│   ├── risk_engine.py   # Multi-factor risk engine
│   └── orchestrator.py  # Pipeline orchestrator
└── frontend/            # Adaptive UI templates & static assets
```

---

## Disclaimer

> SENTRA provides automated software dependency risk, repository health, and open-source compliance analysis. Its findings are informational and should not be treated as legal or security guarantees. Final compliance decisions should be reviewed by qualified security or legal professionals.

---

## License

MIT
