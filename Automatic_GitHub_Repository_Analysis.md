# LicenseLens — Automatic GitHub Repository Analysis

## 1. Feature Name

**Automatic Repository File Detection and Analysis After GitHub Import**

---

## 2. Objective

When a user imports a project from the **GitHub Repositories** page, LicenseLens must automatically inspect the repository, detect the files required for analysis, retrieve those files directly from GitHub, and run the existing LicenseLens analysis system.

The user must **not manually upload** files such as:

- `requirements.txt`
- `package.json`
- `package-lock.json`
- `pyproject.toml`
- `pom.xml`
- `go.mod`
- `Cargo.toml`
- Other supported dependency files

The manual upload feature should remain available only as a fallback for repositories where automatic analysis cannot find a supported manifest.

---

# 3. Current Workflow

Currently:

```text
GitHub Repositories
        ↓
Import Project
        ↓
Project Page
        ↓
User sees Upload Dependency Manifest
        ↓
User manually uploads requirements.txt/package.json
        ↓
Scan
        ↓
Results
```

This requires the user to manually find the dependency file inside the GitHub repository.

---

# 4. New Workflow

Change the workflow to:

```text
GitHub Repositories
        ↓
Import Project
        ↓
Create LicenseLens Project
        ↓
Automatically access GitHub repository
        ↓
Read repository structure
        ↓
Detect required files
        ↓
Retrieve required files from GitHub
        ↓
Analyze dependencies
        ↓
Analyze vulnerabilities
        ↓
Analyze licenses
        ↓
Analyze README
        ↓
Analyze repository health
        ↓
Calculate overall risk
        ↓
Display results
```

The goal is:

> **Import Repository → Automatically Detect → Automatically Retrieve → Automatically Analyze → Display Results**

---

# 5. Core Requirement

After clicking **Import Project**, LicenseLens should automatically determine what the repository contains and what can be analyzed.

Example:

```text
Repository
│
├── README.md
├── LICENSE
├── requirements.txt
├── src/
└── main.py
```

LicenseLens should automatically detect:

```text
✓ README.md
✓ LICENSE
✓ requirements.txt
```

Then retrieve `requirements.txt` and pass it to the existing dependency analysis system.

The user should not have to upload it manually.

---

# 6. GitHub Integration

Use the GitHub OAuth connection belonging to the currently logged-in LicenseLens user.

Flow:

```text
Current LicenseLens User
        ↓
User's GitHubConnection
        ↓
User's GitHub Access Token
        ↓
GitHub Repository
```

Do not use a global GitHub token.

The previously implemented multi-user GitHub isolation must remain unchanged.

---

# 7. User Isolation

Example:

```text
LicenseLens User A
        ↓
GitHub Account A
        ↓
Repository A
        ↓
Project A
        ↓
Analysis A
```

and:

```text
LicenseLens User B
        ↓
GitHub Account B
        ↓
Repository B
        ↓
Project B
        ↓
Analysis B
```

User B must never be able to analyze or view User A's repository.

---

# 8. Import Project Flow

When the user clicks:

```text
Import Project
```

perform:

```text
1. Authenticate current LicenseLens user
2. Get current user's GitHub connection
3. Validate repository access
4. Get repository metadata
5. Create project
6. Start automatic analysis
7. Redirect to project page
8. Display analysis progress
9. Display results after completion
```

Recommended endpoint:

```text
POST /api/github/repositories/{id}/import/
```

The created project must belong to:

```python
request.user
```

---

# 9. Repository Metadata

Automatically retrieve useful metadata:

```text
Repository ID
Repository name
Owner
Description
Repository URL
Default branch
Primary language
Visibility
Latest commit SHA
Updated date
```

Do not unnecessarily download the complete repository.

---

# 10. Repository Tree Detection

After importing, retrieve the repository file structure.

Preferred GitHub API approach:

```text
GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1
```

The existing GitHub service should be reused if it already provides repository tree functionality.

Example returned files:

```text
README.md
LICENSE
requirements.txt
src/main.py
src/utils.py
package.json
```

---

# 11. Automatic Manifest Detection

Create or extend a dedicated manifest detector.

Recommended file:

```text
github_integration/manifest_detector.py
```

Possible implementation:

```python
class ManifestDetector:
    def detect(self, file_paths):
        ...
```

Example result:

```json
{
    "manifests": [
        {
            "path": "requirements.txt",
            "type": "python"
        }
    ]
}
```

---

# 12. Supported Manifest Files

The initial implementation can detect:

| File | Project Type |
|---|---|
| `requirements.txt` | Python |
| `pyproject.toml` | Python |
| `Pipfile` | Python |
| `package.json` | Node.js |
| `package-lock.json` | Node.js |
| `yarn.lock` | Node.js |
| `pnpm-lock.yaml` | Node.js |
| `pom.xml` | Java |
| `build.gradle` | Java |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `composer.json` | PHP |
| `*.csproj` | .NET |

Only analyze file formats supported by the existing LicenseLens parser.

Detection support and analysis support should not be confused.

---

# 13. Nested Manifest Detection

Do not search only the repository root.

Example:

```text
repository/
├── frontend/
│   └── package.json
├── backend/
│   └── requirements.txt
└── README.md
```

LicenseLens should detect:

```text
✓ frontend/package.json
✓ backend/requirements.txt
✓ README.md
```

---

# 14. Multiple Manifest Support

A repository can contain multiple projects.

Example:

```text
repository/
├── frontend/package.json
├── backend/requirements.txt
└── services/api/go.mod
```

The system should identify all supported manifests.

Initial implementation may analyze each supported manifest independently and combine the results.

---

# 15. Manifest Priority

When multiple dependency files describe the same ecosystem, define a consistent priority based on the existing scanner.

Example:

```text
Python:
1. poetry.lock + pyproject.toml
2. pyproject.toml
3. requirements.txt
4. Pipfile

Node.js:
1. package-lock.json
2. pnpm-lock.yaml
3. yarn.lock
4. package.json
```

The exact order must match the existing parser's capabilities.

Do not arbitrarily select a manifest that the scanner cannot process.

---

# 16. Retrieve Manifest Content

After detecting manifests:

```text
Repository Tree
        ↓
Detected Manifest Paths
        ↓
GitHub Contents API
        ↓
Manifest Content
```

Example:

```text
GET /repos/{owner}/{repo}/contents/requirements.txt
```

Use the current user's GitHub token.

Do not retrieve every source file unless required.

---

# 17. Optimization

Prefer:

```text
Repository Metadata
        ↓
Repository Tree
        ↓
Detect Required Files
        ↓
Download Only Required Files
        ↓
Analyze
```

Avoid:

```text
Download Entire Repository ZIP
        ↓
Extract Everything
        ↓
Search
```

unless the existing architecture requires a repository archive.

---

# 18. Automatic Analysis Pipeline

The complete pipeline should be:

```text
Import Repository
        ↓
Fetch Repository Metadata
        ↓
Fetch Repository Tree
        ↓
Detect README
        ↓
Detect License
        ↓
Detect Dependency Manifests
        ↓
Retrieve Manifest Contents
        ↓
Parse Dependencies
        ↓
Check Vulnerabilities
        ↓
Check License Compliance
        ↓
Calculate Risk
        ↓
Generate Repository Health
        ↓
Store Results
        ↓
Mark Analysis Complete
```

---

# 19. Reuse Existing Analysis Engine

This is critical.

Do not create separate GitHub-specific versions of:

```text
Dependency Parser
Vulnerability Scanner
License Analyzer
Risk Calculator
```

Instead:

```text
GitHub Manifest
      ↓
Existing Parser
      ↓
Existing Vulnerability Scanner
      ↓
Existing License Analyzer
      ↓
Existing Risk Engine
```

The GitHub workflow and manual workflow should eventually produce the same result format.

---

# 20. README Detection

Automatically detect:

```text
README.md
README
README.txt
README.rst
```

At minimum, support:

```text
README.md
```

If missing:

```text
⚠ README Missing
```

The existing README recommendation feature should be reused.

---

# 21. License Detection

Automatically detect common license files:

```text
LICENSE
LICENSE.md
LICENSE.txt
COPYING
```

Also use GitHub's recognized license metadata where appropriate.

Example:

```text
✓ MIT License
```

or:

```text
⚠ License Not Detected
```

---

# 22. Dependency Analysis

After retrieving the manifest:

```text
Manifest Content
        ↓
Existing Dependency Parser
        ↓
Dependency List
```

Example:

```text
requirements.txt
        ↓
Django
Requests
NumPy
        ↓
Existing LicenseLens Dependency Analyzer
```

---

# 23. Vulnerability Analysis

Use the existing vulnerability scanner.

```text
Dependencies
        ↓
Vulnerability Scanner
        ↓
CVE / Security Results
```

Example:

```text
24 Dependencies
2 Vulnerabilities
0 Critical
1 High
1 Medium
```

Do not create a separate vulnerability system for GitHub projects.

---

# 24. License Compliance Analysis

Automatically analyze dependency licenses.

```text
Dependency
        ↓
Package Metadata
        ↓
License
        ↓
License Policy
        ↓
Compliance Result
```

Example:

```text
MIT       ✓ Permissive
Apache-2  ✓ Permissive
GPL-3.0   ⚠ Review Required
```

Use the existing LicenseLens license rules.

---

# 25. Risk Calculation

Reuse the existing risk engine.

Possible results:

```text
Overall Risk
Security Score
Dependency Count
Vulnerability Count
License Risk Count
README Status
```

The scoring logic should remain consistent with existing manual scans.

---

# 26. Automatic Analysis Status

Add or reuse scan status.

Recommended states:

```text
IMPORTING
ANALYZING
COMPLETED
NO_MANIFEST
PARTIAL
FAILED
```

Recommended analysis stages:

```text
fetching_repository
detecting_files
detecting_manifests
retrieving_manifests
parsing_dependencies
checking_vulnerabilities
checking_licenses
checking_readme
generating_results
completed
failed
```

---

# 27. Analysis Progress UI

Immediately after import, the project page should show:

```text
Repository Analysis

✓ Repository connected
✓ Repository structure retrieved
✓ Manifest detected
● Analyzing dependencies
○ Checking vulnerabilities
○ Checking licenses
○ Checking README
○ Generating results
```

Do not show the manual upload form as the primary action.

---

# 28. Project Page After Import

Current experience:

```text
Overall Risk
Dependency Overview

No scans yet. Upload a manifest below.

Upload Dependency Manifest
```

New experience for GitHub projects:

```text
SmartCampusSystem
github.com/owner/SmartCampusSystem

✓ GitHub Repository Connected

Repository Analysis

✓ requirements.txt detected
✓ README.md detected
✓ LICENSE detected

Commit Analyzed:
a84f3c91

Status:
✓ Analysis Complete
```

---

# 29. Final Analysis Dashboard

After analysis:

```text
SmartCampusSystem
github.com/owner/SmartCampusSystem

✓ Analysis Complete

┌─────────────────┐
│ Overall Risk    │
│                 │
│ LOW             │
└─────────────────┘

┌─────────────────┐
│ Dependencies    │
│                 │
│ 24              │
└─────────────────┘

┌─────────────────┐
│ Vulnerabilities │
│                 │
│ 2               │
└─────────────────┘

Repository Health
────────────────────────────

✓ README.md
✓ LICENSE
✓ requirements.txt

Dependency Analysis
────────────────────────────

24 Dependencies
2 Vulnerabilities
1 License Risk

Commit:
a84f3c91

[ Refresh Analysis ] [ Open GitHub ]
```

---

# 30. No Manifest Handling

If the repository has no supported dependency manifest:

```text
⚠ No Supported Dependency Manifest Found

LicenseLens could not find a dependency file
supported by the current analysis engine.

✓ README detected
✓ License detected
⚠ Dependencies not analyzed

[ Upload Manifest Manually ]
```

Use:

```text
NO_MANIFEST
```

instead of marking the scan as a generic failure.

---

# 31. Unsupported Manifest Handling

If a file looks like a dependency file but is unsupported:

```text
⚠ Unsupported Dependency File

Detected:
custom.lock

This file type is not currently supported
by LicenseLens.
```

Do not silently ignore it.

---

# 32. Partial Analysis

For example:

```text
frontend/package.json        ✓ Analyzed
backend/requirements.txt    ✓ Analyzed
services/custom.lock        ⚠ Unsupported
```

Display:

```text
PARTIAL ANALYSIS
```

and provide results for supported files.

---

# 33. Failed Analysis

If an unexpected error occurs:

```text
Analysis Failed

LicenseLens could not complete the repository analysis.

[ Retry Analysis ]
```

Technical errors should be logged server-side.

Never expose:

```text
Access Token
OAuth credentials
Private repository secrets
```

---

# 34. Manual Upload as Fallback

Do not remove the current manual upload system.

For GitHub projects:

```text
Automatic analysis
        ↓
No supported manifest?
        ↓
Show manual upload fallback
```

For manually created projects:

```text
Create Project
        ↓
Upload Manifest
        ↓
Existing Analysis
```

This keeps backward compatibility.

---

# 35. Re-Scan / Refresh Analysis

Add:

```text
[ Refresh Analysis ]
```

For a GitHub project:

```text
Refresh
   ↓
Fetch latest GitHub repository
   ↓
Get latest tree
   ↓
Detect manifests
   ↓
Retrieve latest manifests
   ↓
Analyze
   ↓
Create new scan
   ↓
Display updated results
```

No manual file upload should be required.

---

# 36. Commit SHA Tracking

Store the commit SHA used during analysis.

Example:

```text
Commit Analyzed:
a84f3c91...
```

When refreshing:

```text
Current GitHub HEAD
        ↓
Compare with stored SHA
        ↓
Changed?
 ├── YES → Run new analysis
 └── NO  → Previous results may be reused
```

A manual refresh may still force a new scan.

---

# 37. Default Branch

Do not assume that every repository uses `main`.

Retrieve:

```text
default_branch
```

from GitHub repository metadata.

Support:

```text
main
master
develop
other default branches
```

---

# 38. Private Repository Support

If the connected GitHub account has permission to access private repositories:

```text
Private Repository
        ↓
Current user's GitHub token
        ↓
Automatic analysis
```

Private repository information must remain private to that LicenseLens user.

---

# 39. API Endpoints

Recommended:

```text
POST /api/github/repositories/{id}/import/
GET  /api/projects/{id}/analysis-status/
POST /api/projects/{id}/refresh-analysis/
```

All endpoints must:

```text
Require authentication
Verify project ownership
Use current user's GitHub connection
```

---

# 40. Analysis Status Response

Example:

```json
{
  "status": "analyzing",
  "stage": "checking_vulnerabilities",
  "progress": 70
}
```

Completed:

```json
{
  "status": "completed",
  "stage": "completed",
  "progress": 100
}
```

---

# 41. Project Model Changes

Inspect the existing `Project` model first.

If GitHub fields do not already exist, consider:

```text
source
github_repository_id
github_owner
github_repo_name
github_default_branch
github_commit_sha
```

Use:

```text
source = github
```

for imported GitHub projects.

Use:

```text
source = manual
```

for manually created projects.

Do not duplicate existing fields.

---

# 42. Scan Model Changes

Reuse the existing Scan model if possible.

A GitHub scan should be able to identify:

```text
Project
Repository
Detected manifests
Commit SHA
Started time
Completed time
Status
Results
```

---

# 43. Repository Analysis Service

Create or extend a central service:

```python
class RepositoryAnalysisService:

    def analyze_github_repository(self, user, project):
        ...

    def detect_manifests(self, repository_tree):
        ...

    def retrieve_manifests(self, user, repository, manifests):
        ...

    def analyze_manifests(self, project, manifests):
        ...

    def analyze_repository_health(self, user, repository):
        ...
```

This service should orchestrate the existing analyzers.

---

# 44. GitHub Service

Reuse the existing GitHub integration.

Possible methods:

```python
class GitHubService:

    def get_repository(self, user, owner, repo):
        ...

    def get_repository_tree(self, user, owner, repo, branch):
        ...

    def get_file_content(self, user, owner, repo, path, ref):
        ...

    def get_default_branch(self, user, owner, repo):
        ...
```

Every method must use the current user's GitHub connection.

---

# 45. Do Not Download the Entire Repository

The preferred process is:

```text
Repository Metadata
       ↓
Repository Tree
       ↓
Detect Required Files
       ↓
Retrieve Required Files
       ↓
Analyze
```

Only download the entire repository when a specific analyzer genuinely requires it.

---

# 46. Large Repository Protection

Add reasonable limits for:

```text
Maximum repository tree entries
Maximum manifest size
Maximum number of manifests
Maximum analysis duration
```

If limits are exceeded:

```text
Repository is too large for automatic analysis.

Please select or upload a supported manifest manually.
```

Use limits appropriate for the existing college-project environment.

---

# 47. GitHub API Error Handling

Handle:

```text
401 Unauthorized
403 Forbidden
404 Not Found
429 Rate Limit
Network Error
```

### 401

```text
GitHub connection is no longer valid.

[ Reconnect GitHub ]
```

### 403

```text
LicenseLens cannot access this repository.
Please check GitHub permissions.
```

### 404

```text
Repository could not be found or is no longer accessible.
```

---

# 48. Development Phase 1 — Inspect Existing System

Before coding:

```text
[ ] Inspect Project model
[ ] Inspect Scan model
[ ] Inspect dependency parser
[ ] Inspect vulnerability analyzer
[ ] Inspect license analyzer
[ ] Inspect README analyzer
[ ] Inspect current manifest upload workflow
[ ] Inspect GitHub OAuth service
[ ] Inspect GitHub repository API
[ ] Inspect Import Project endpoint
```

Do not create duplicate services before understanding the existing implementation.

---

# 49. Development Phase 2 — GitHub Repository Retrieval

```text
[ ] Retrieve repository metadata
[ ] Retrieve default branch
[ ] Retrieve repository tree
[ ] Detect required files
[ ] Retrieve manifest contents
[ ] Retrieve README information
[ ] Retrieve license information
[ ] Add GitHub error handling
```

---

# 50. Development Phase 3 — Manifest Detector

```text
[ ] Create ManifestDetector
[ ] Add supported manifest mappings
[ ] Support nested manifests
[ ] Support multiple manifests
[ ] Define manifest priority
[ ] Add unit tests
```

---

# 51. Development Phase 4 — Automatic Analysis

```text
[ ] Connect manifest detector to existing parser
[ ] Connect parser to vulnerability scanner
[ ] Connect parser to license analyzer
[ ] Connect README analyzer
[ ] Connect repository health checks
[ ] Calculate risk
[ ] Store scan results
[ ] Store commit SHA
```

---

# 52. Development Phase 5 — Project UI

```text
[ ] Detect whether project source is GitHub
[ ] Show GitHub repository information
[ ] Show analysis progress
[ ] Show detected files
[ ] Show commit SHA
[ ] Show automatic results
[ ] Add Refresh Analysis
[ ] Add Open GitHub
[ ] Keep manual upload as fallback
```

---

# 53. Development Phase 6 — API

```text
[ ] Update Import Project endpoint
[ ] Add analysis status endpoint
[ ] Add Refresh Analysis endpoint
[ ] Require authentication
[ ] Verify project ownership
[ ] Return safe API responses
```

---

# 54. Development Phase 7 — Testing

## Manifest tests

```text
[ ] requirements.txt
[ ] package.json
[ ] pyproject.toml
[ ] package-lock.json
[ ] pom.xml
[ ] go.mod
[ ] Cargo.toml
[ ] Nested manifest
[ ] Multiple manifests
[ ] No manifest
[ ] Unsupported manifest
```

## Import tests

```text
[ ] Import repository
[ ] Project created automatically
[ ] Analysis starts automatically
[ ] No manual upload required
[ ] Manifest detected
[ ] Manifest retrieved
[ ] Dependencies parsed
[ ] Vulnerabilities checked
[ ] Licenses checked
[ ] README checked
[ ] Results displayed
```

---

# 55. Multi-User Testing

### User A

```text
Login A
Connect GitHub A
Import Repository A
Run automatic analysis
```

Expected:

```text
Project A
Scan A
Repository A
```

### User B

```text
Logout A
Login B
Connect GitHub B
Import Repository B
Run automatic analysis
```

Expected:

```text
Project B
Scan B
Repository B
```

Verify:

```text
[ ] B cannot view A's project
[ ] B cannot view A's scan
[ ] B cannot analyze A's repository
[ ] A cannot view B's project
[ ] A cannot view B's scan
```

---

# 56. Re-Scan Testing

```text
[ ] Import repository
[ ] Complete analysis
[ ] Change dependency on GitHub
[ ] Push new commit
[ ] Click Refresh Analysis
[ ] Detect new commit
[ ] Retrieve latest manifest
[ ] Run new analysis
[ ] Store new scan
[ ] Display updated results
```

---

# 57. No Manifest Testing

```text
[ ] Import repository with no supported dependency file
[ ] Analysis does not crash
[ ] NO_MANIFEST status shown
[ ] README check still runs
[ ] License check still runs
[ ] Manual upload fallback is available
```

---

# 58. Multiple Manifest Testing

Example:

```text
repo/
├── frontend/package.json
└── backend/requirements.txt
```

Expected:

```text
Detected Manifests

✓ frontend/package.json
✓ backend/requirements.txt
```

Both should be analyzed if supported.

---

# 59. Private Repository Testing

```text
[ ] Connect GitHub with required permissions
[ ] Import private repository
[ ] Retrieve manifest
[ ] Analyze successfully
[ ] Verify private repository data is not exposed
```

---

# 60. Final User Experience

### Before

```text
Import GitHub Project
        ↓
Project Page
        ↓
No scans yet
        ↓
Find requirements.txt/package.json
        ↓
Upload manually
        ↓
Run scan
```

### After

```text
Import GitHub Project
        ↓
Project Created
        ↓
Analyzing Repository...
        ↓
Detecting Files
        ↓
Detecting Manifest
        ↓
Retrieving Manifest
        ↓
Analyzing Dependencies
        ↓
Checking Vulnerabilities
        ↓
Checking Licenses
        ↓
Checking README
        ↓
Analysis Complete
        ↓
Results Displayed
```

---

# 61. Final Project Page Example

```text
SmartCampusSystem
github.com/owner/SmartCampusSystem

✓ GitHub Connected

┌────────────────────┐
│ Overall Risk       │
│                    │
│ Medium             │
└────────────────────┘

┌───────────────────────────────────┐
│ Dependency Overview               │
│                                   │
│ 24 Dependencies                   │
│ 2 Vulnerabilities                 │
│ 1 License Risk                    │
└───────────────────────────────────┘

Repository Analysis
────────────────────────────────────

Detected Files

✓ requirements.txt
✓ README.md
✓ LICENSE

Commit Analyzed
a84f3c91

Analysis Status
✓ Complete

[ Refresh Analysis ] [ Open GitHub ]
```

The manual upload area should no longer be the primary workflow for GitHub-imported projects.

---

# 62. Final Architecture

```text
                         GitHub OAuth
                              │
                              ▼
                    Current LicenseLens User
                              │
                              ▼
                   User's GitHub Connection
                              │
                              ▼
                    Import GitHub Repository
                              │
                              ▼
                 Repository Analysis Service
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
          Repository Tree   README        License
                │           Detection     Detection
                ▼
          Manifest Detector
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
     Python    Node     Other
        │       │        │
        └───────┼────────┘
                ▼
       Existing Dependency Parser
                │
                ▼
       Existing Vulnerability Scanner
                │
                ▼
        Existing License Analyzer
                │
                ▼
            Risk Engine
                │
                ▼
          Scan Results
                │
                ▼
           Project Page
```

---

# 63. Final Acceptance Criteria

```text
[ ] Importing a GitHub repository automatically starts analysis
[ ] User does not manually upload requirements.txt
[ ] User does not manually upload package.json
[ ] Repository structure is inspected automatically
[ ] Supported manifest files are detected
[ ] Nested manifests are detected
[ ] Multiple manifests are supported
[ ] Manifest contents are retrieved directly from GitHub
[ ] Existing dependency parser is reused
[ ] Existing vulnerability scanner is reused
[ ] Existing license analyzer is reused
[ ] README detection is automatic
[ ] License detection is automatic
[ ] Risk calculation is automatic
[ ] Scan results are stored
[ ] Commit SHA is stored
[ ] Analysis progress is visible
[ ] Refresh Analysis works
[ ] No-manifest repositories are handled gracefully
[ ] Unsupported manifests are handled gracefully
[ ] Partial analysis is handled
[ ] GitHub API errors are handled
[ ] Private repositories work when permissions allow
[ ] User-specific GitHub isolation is preserved
[ ] Imported projects belong to the current LicenseLens user
[ ] Manual upload remains available as a fallback
[ ] Existing manual projects continue working
[ ] Existing LicenseLens analysis functionality is not broken
```

---

# 64. Final Goal

LicenseLens should provide a **one-click GitHub security audit**.

The final experience should be:

```text
User selects GitHub repository
              ↓
        Click Import
              ↓
    LicenseLens reads repository
              ↓
    Automatically finds required files
              ↓
    Automatically retrieves files
              ↓
    Automatically analyzes everything
              ↓
      Complete results shown
```

The user should never need to manually search GitHub for `requirements.txt`, `package.json`, or another dependency file just to start the analysis.
