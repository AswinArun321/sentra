# LicenseLens

> **Software Dependency Risk & Open-Source Compliance Auditor**

LicenseLens analyzes your project's dependencies for security vulnerabilities, license compliance issues, and maintenance health — all in one place.

![LicenseLens Dashboard](docs/screenshot.png)

---

## Features

- 🔍 **Dependency Scanning** — Upload `package.json` or `requirements.txt`
- 🛡️ **Vulnerability Detection** — Queries OSV.dev for known CVEs
- 📜 **License Analysis** — Detects and categorizes open-source licenses
- 🔧 **Maintenance Health** — Flags stale or abandoned packages
- 📊 **Risk Scoring** — Weighted risk score (Security 50%, License 25%, Maintenance 15%, Dependency 10%)
- 🎯 **Risk Findings** — Human-readable explanations and remediation advice
- 📥 **JSON Reports** — Downloadable security report
- 📋 **CycloneDX SBOM** — Software Bill of Materials export
- 🔐 **Authentication** — Email/password login with session management

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.1 + Django REST Framework |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | Django sessions + JWT (djangorestframework-simplejwt) |
| Frontend | Django Templates + Vanilla JS + Chart.js |
| Styling | Custom CSS (dark security dashboard theme) |
| Vuln API | OSV.dev (open, no key required) |
| License API | PyPI JSON API + npm Registry |
| SBOM | CycloneDX 1.4 JSON |

---

## Quick Start

### 1. Clone and install dependencies

```bash
git clone https://github.com/yourname/LicenseLens_Django.git
cd LicenseLens_Django
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings
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

## Default Admin Account

After setup, use these credentials to test immediately:

```
Email:    admin@licenselens.dev
Password: LicenseLens2026!
```

---

## Usage

1. **Register** or log in
2. **Create a Project** (e.g., "My Backend App")
3. **Upload** a `package.json` or `requirements.txt`
4. **Wait** for the scan to complete (synchronous, ~10-30 seconds)
5. **View** the scan results:
   - Vulnerability severity breakdown
   - License categories and compliance warnings
   - Maintenance health of each package
   - Overall risk score
6. **Download** a JSON report or CycloneDX SBOM

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` | Register a new user |
| POST | `/api/auth/login/` | Login and get JWT tokens |
| GET | `/api/auth/profile/` | Get user profile |
| GET | `/api/projects/` | List projects |
| POST | `/api/projects/` | Create project |
| POST | `/api/projects/{id}/scan/` | Upload file and start scan |
| GET | `/api/scans/{id}/` | Get scan details |
| GET | `/api/scans/{id}/dependencies/` | List dependencies |
| GET | `/api/scans/{id}/vulnerabilities/` | List vulnerabilities |
| GET | `/api/scans/{id}/report/` | Get JSON report |

---

## Project Structure

```
LicenseLens_Django/
├── config/          # Django project settings & URLs
├── accounts/        # User authentication
├── projects/        # Project management
├── scans/           # Scan lifecycle
├── dependencies/    # Dependency model
├── vulnerabilities/ # Vulnerability & RiskFinding models
├── reports/         # Report generation (JSON + SBOM)
├── scanner/         # Core scanning engine
│   ├── parsers/     # package.json & requirements.txt parsers
│   ├── vulnerability.py    # OSV API client
│   ├── license_analyzer.py # License detection & categorization
│   ├── maintenance.py      # Package maintenance health
│   ├── risk_engine.py      # Risk scoring
│   └── orchestrator.py     # Scan pipeline orchestrator
└── frontend/        # Django templates + static assets
```

---

## Disclaimer

> LicenseLens provides automated software dependency risk and open-source compliance analysis. Its findings are informational and should not be treated as legal or security guarantees. Final compliance decisions should be reviewed by qualified security or legal professionals.

---

## License

MIT
