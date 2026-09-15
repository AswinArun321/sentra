# SENTRA — Premium Public Home Page UI/UX Redesign Plan

## Reference

**Visual/UX reference:**  
https://www.eloqwnt.com/

The reference is being used for **design inspiration only**. The SENTRA implementation must be an original design for a repository-security product.

Do not copy:

- Eloqwnt branding
- Logos
- Text/content
- Images
- Illustrations
- Client logos
- Testimonials
- Proprietary assets
- Exact page copy
- Exact layouts where they would amount to a clone

Use the reference to learn from its design principles: strong typography, large whitespace, visual storytelling, clear hierarchy, section transitions, bold calls to action, metrics, project-style showcases, service/feature presentation, FAQ structure, and polished responsive behavior.

---

# 1. Project Identity

## Product

**SENTRA**

## Full product name

**SENTRA — Repository Security & Intelligence Platform**

## Tagline

**Know your code. Secure what you ship.**

## Product purpose

SENTRA analyzes GitHub repositories and provides repository security and intelligence across:

- Dependency analysis
- Vulnerability detection
- Open-source license analysis
- README/documentation health
- Repository health
- Overall repository risk

---

# 2. Current Problem

The current application opens directly on the Login page.

Current flow:

```text
Browser
   |
   v
Login
   |
   v
Dashboard
```

This makes the project feel like an internal application rather than a complete product.

The new experience should be:

```text
Browser
   |
   v
SENTRA Public Home
   |
   +---- Features
   +---- How It Works
   +---- About
   +---- Documentation
   +---- Contact
   |
   +---- Login
   +---- Get Started
              |
              v
          Authentication
              |
              v
           Dashboard
```

---

# 3. Primary Goal

Create a premium, modern, technology-focused public landing page for SENTRA inspired by the visual quality and UX principles of the reference website.

The result should feel like:

- A real cybersecurity/developer product
- A modern startup website
- A premium SaaS/security platform
- A polished production application

It must **not** feel like:

- A generic Bootstrap template
- A basic college-project landing page
- A dashboard copied onto a marketing page
- A clone of the reference website

---

# 4. Technology Constraints

The existing project uses:

- Django
- Django templates
- HTML
- CSS
- Vanilla JavaScript
- Chart.js where already used

The redesign must continue using:

```text
Django
HTML
CSS
Vanilla JavaScript
```

Do **not** migrate the frontend to:

- React
- Next.js
- Vue
- Angular
- Tailwind-based replacement architecture
- A separate frontend application

unless there is an explicit later requirement.

The existing backend must remain intact.

---

# 5. Critical Existing Functionality to Preserve

The redesign is a public UI change.

Do not break:

### Authentication

- Login
- Signup
- Logout
- Password handling
- Existing authentication/session/JWT behavior

### GitHub

- GitHub OAuth
- GitHub connection
- Per-user GitHub account isolation
- Repository listing
- Repository import

### Repository analysis

- Automatic repository inspection
- Manifest detection
- Dependency extraction
- Vulnerability analysis
- License analysis
- README detection
- Repository health
- Risk scoring

### Authenticated application

- Dashboard
- Projects
- Scans
- Dependencies
- Vulnerabilities
- Reports

---

# 6. Reference Design Analysis

The reference site demonstrates several useful design patterns.

Its homepage uses a strong hero statement followed by credibility/metric content, a company/identity section, selected work, services, FAQ, testimonials, and a strong contact CTA.

For SENTRA, these concepts should be translated into product-specific sections:

```text
Reference concept          SENTRA equivalent

Hero                       Product Hero
Metrics                    Repository Security Signals
Who we are                 What SENTRA Does
Selected Work              Example Repository Analysis
Services                   Security Intelligence
FAQ                        SENTRA FAQ
Testimonials               Product/Developer Value
Contact CTA                Analyze Your Repository CTA
```

This keeps the UX inspiration while creating original SENTRA content.

---

# 7. Overall Design Direction

The design should use:

- Large typography
- Strong visual hierarchy
- Generous whitespace
- Minimal navigation
- Large section headings
- High-quality cards only where useful
- Strong contrast
- Subtle motion
- Smooth transitions
- Technical visualizations
- Clean security-oriented UI
- Responsive layouts

Avoid:

- Excessive glassmorphism
- Excessive gradients
- Excessive shadows
- Too many small cards
- Random illustrations
- Stock photography
- Generic shield graphics everywhere
- Overloaded navigation
- Fake SaaS metrics
- Fake customer logos
- Fake testimonials

---

# 8. Recommended Visual Identity

## Primary visual character

SENTRA should feel:

```text
Precise
Secure
Technical
Confident
Minimal
Intelligent
Premium
```

## Suggested visual system

Use:

- Dark navy/near-black hero sections
- Light sections for content
- White or near-white surfaces
- Blue/cyan accent associated with the existing SENTRA login page
- One additional accent only if necessary
- High-contrast typography

Do not hard-code dozens of colors.

Create CSS variables.

Example:

```css
:root {
    --sentra-bg: ...;
    --sentra-surface: ...;
    --sentra-text: ...;
    --sentra-muted: ...;
    --sentra-primary: ...;
    --sentra-border: ...;
}
```

Exact colors should be selected during implementation to harmonize with the existing login page.

---

# 9. Typography

Typography is one of the most important parts of the redesign.

Use a modern sans-serif font stack.

Recommended characteristics:

- Large hero heading
- Tight heading line-height
- Strong weight
- Medium-width paragraphs
- Smaller uppercase labels for section identifiers

Example:

```text
01 / REPOSITORY INTELLIGENCE

YOUR CODEBASE
HAS A STORY.

SENTRA HELPS YOU
UNDERSTAND IT.
```

Avoid making every heading huge. Create a hierarchy.

---

# 10. Public Navigation

Create a reusable public navbar.

Recommended:

```text
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  SENTRA      Home  Features  How It Works  About  Docs     │
│                                      Login   Get Started →  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Left

```text
SENTRA
```

### Center

```text
Home
Features
How It Works
About
Documentation
```

### Right

```text
Login
Get Started →
```

Do not add:

- Mail icon
- Notification icon
- Unimplemented search
- Fake profile menu

These were previously identified as confusing in the application header.

---

# 11. Navbar Behavior

Desktop:

```text
Logo | Navigation | Authentication actions
```

Mobile:

```text
SENTRA                         ☰
```

Opening the menu should show:

```text
Home
Features
How It Works
About
Documentation
Contact
Login
Get Started
```

The navbar should:

- Remain readable over hero content
- Have appropriate contrast
- Transition smoothly if sticky
- Avoid excessive animation
- Work with keyboard navigation

---

# 12. Home Page Structure

The recommended final Home page is:

```text
01  Navigation
02  Hero
03  Security Signal / Metrics
04  Problem
05  SENTRA Intelligence
06  Repository Analysis Visualization
07  How SENTRA Works
08  Example Security Report
09  Why SENTRA
10  FAQ
11  Final CTA
12  Footer
```

---

# 13. Section 01 — Hero

## Purpose

Immediately communicate what SENTRA does.

The hero should occupy most of the initial viewport.

Recommended structure:

```text
01 / REPOSITORY SECURITY & INTELLIGENCE

KNOW YOUR CODE.
SECURE WHAT
YOU SHIP.

SENTRA automatically analyzes your GitHub repositories
to uncover dependency risks, vulnerabilities, license
issues, documentation gaps, and repository-health signals.

[ Get Started → ]     [ Explore SENTRA ]
```

---

# 14. Hero Visual

Instead of using generic artwork, create an original SENTRA repository-analysis visual.

Example:

```text
                         ┌───────────────────────┐
                         │ SENTRA ANALYSIS       │
                         │                       │
                         │ repository: api-core  │
                         │                       │
                         │ Security Score  87    │
                         │                       │
                         │ Dependencies      ✓   │
                         │ Vulnerabilities   2   │
                         │ Licenses          ✓   │
                         │ README            ⚠   │
                         │ Repository Health ✓   │
                         │                       │
                         │ Risk: LOW             │
                         └───────────────────────┘
```

This should feel like part of the SENTRA product, not a random dashboard screenshot.

---

# 15. Hero Animation

Use subtle motion.

Possible animation:

```text
Repository
     |
     v
Scanning
     |
     v
Dependencies ──────┐
Vulnerabilities ───┤
Licenses ──────────┤
README ────────────┤
Repository Health ─┘
     |
     v
87 / 100
```

Animation requirements:

- Fast enough to not annoy users
- No infinite excessive motion
- Pause/reduce motion for accessibility
- No dependency on backend data
- Use CSS/vanilla JS
- No React animation library

---

# 16. Section 02 — Security Signals / Metrics

The reference site uses repeated business metrics to create a visual rhythm.

SENTRA should use meaningful product signals instead of fake company statistics.

Example:

```text
/ DEPENDENCY INTELLIGENCE

/ VULNERABILITY ANALYSIS

/ LICENSE VISIBILITY

/ REPOSITORY HEALTH
```

Alternative:

```text
DEPENDENCIES
DISCOVERED

VULNERABILITIES
IDENTIFIED

LICENSES
ANALYZED

REPOSITORIES
UNDERSTOOD
```

If real project-wide statistics are not available, do not invent numbers.

Use capabilities rather than fake metrics.

---

# 17. Section 03 — Problem

Heading:

```text
YOUR REPOSITORY
IS MORE THAN CODE.
```

Supporting text:

```text
Modern applications depend on packages, open-source
components, configuration, documentation, and external
software ecosystems.

Hidden risks can exist across all of them.
```

Then:

```text
Dependencies
Vulnerabilities
Licenses
Documentation
Repository Health
```

Transition into:

```text
SENTRA brings these signals together.
```

---

# 18. Section 04 — SENTRA Intelligence

This replaces the reference site's agency "services" section.

Heading:

```text
ONE REPOSITORY.
MULTIPLE SECURITY SIGNALS.
ONE CLEAR VIEW.
```

Use a large numbered list rather than six tiny generic cards.

---

# 19. Intelligence Item 01

```text
01
DEPENDENCY INTELLIGENCE

Discover the dependencies that power your project
and understand what your repository is built on.
```

---

# 20. Intelligence Item 02

```text
02
VULNERABILITY DETECTION

Identify known vulnerabilities affecting supported
project dependencies.
```

---

# 21. Intelligence Item 03

```text
03
LICENSE INTELLIGENCE

Understand the licenses associated with open-source
dependencies and identify potential compliance concerns.
```

---

# 22. Intelligence Item 04

```text
04
README HEALTH

Detect missing README documentation and improve the
clarity and usability of your repository.
```

---

# 23. Intelligence Item 05

```text
05
REPOSITORY HEALTH

Inspect supported repository-level signals to understand
the overall health of a project.
```

---

# 24. Intelligence Item 06

```text
06
RISK INTELLIGENCE

Turn multiple findings into a clear repository-level
risk assessment.
```

---

# 25. Section 05 — Repository Analysis Visualization

This should be one of the visual highlights of the page.

Create an original diagram/animation:

```text
                    GITHUB
                  REPOSITORY
                      |
                      v
              ┌──────────────┐
              │    SENTRA    │
              │   INSPECTS   │
              └──────┬───────┘
                     |
       ┌─────────────┼─────────────┐
       |             |             |
       v             v             v
 Dependencies   Vulnerabilities  Licenses
       |             |             |
       └─────────────┼─────────────┘
                     |
              README / HEALTH
                     |
                     v
                RISK ENGINE
                     |
                     v
                 87 / 100
```

Use animated lines, dots, or subtle pulses.

Do not make this a literal copy of any reference graphic.

---

# 26. Section 06 — How SENTRA Works

Heading:

```text
FROM GITHUB REPOSITORY
TO SECURITY INTELLIGENCE.
```

Four or five large steps:

### 01 — Connect

```text
Connect your GitHub account securely.
```

### 02 — Select

```text
Choose the repository you want to analyze.
```

### 03 — Inspect

```text
SENTRA discovers supported repository and dependency files.
```

### 04 — Analyze

```text
SENTRA analyzes dependencies, vulnerabilities, licenses,
README health, and supported repository signals.
```

### 05 — Understand

```text
Review findings, recommendations, and overall repository risk.
```

---

# 27. Section 07 — Example Security Report

Create a visual example of what a user will see after analysis.

Example:

```text
┌───────────────────────────────────────────────────┐
│ SENTRA REPOSITORY ANALYSIS                        │
│                                                   │
│ repository: example-api                           │
│                                                   │
│                  87 / 100                         │
│                  LOW RISK                         │
│                                                   │
│ Dependencies          Healthy                     │
│ Vulnerabilities       2 Findings                  │
│ Licenses              Compliant                   │
│ README                Missing                     │
│ Repository Health     Healthy                     │
│                                                   │
│ Recommendations:                                  │
│ • Review 2 vulnerable dependencies                │
│ • Add README documentation                        │
└───────────────────────────────────────────────────┘
```

Use clearly labeled fictional/demo information.

Do not imply that this is a real user's repository.

---

# 28. Section 08 — Why SENTRA

Heading:

```text
WHY SENTRA?
```

Possible principles:

```text
AUTOMATIC

No need to manually collect dependency files
from GitHub repositories.

CONNECTED

Work directly with repositories available to
your connected GitHub account.

MULTI-SIGNAL

Understand dependencies, vulnerabilities,
licenses, documentation, and repository health.

ACTIONABLE

Turn technical findings into understandable
security insights.

CENTRALIZED

Keep repository security information in one place.
```

---

# 29. Section 09 — Product Trust Section

Do not use fake client logos or fake customer statistics.

Instead use product principles:

```text
ACCOUNT-AWARE
GitHub access is tied to the authenticated SENTRA account.

AUTOMATED
Supported repository files can be discovered automatically.

TRANSPARENT
Findings are shown with clear explanations.

SECURITY-FOCUSED
Designed around repository and software-supply-chain signals.
```

---

# 30. Section 10 — FAQ

The reference site uses a large FAQ section.

SENTRA should have a concise FAQ.

Questions:

### What is SENTRA?

Answer:

```text
SENTRA is a repository security and intelligence platform
for analyzing GitHub repositories.
```

### What can SENTRA analyze?

```text
SENTRA analyzes supported dependencies, vulnerabilities,
licenses, README health, repository-health signals, and
overall repository risk.
```

### Does SENTRA require manual dependency-file uploads?

```text
For GitHub-imported repositories, SENTRA is designed to
automatically discover and retrieve supported dependency
files. Manual upload can remain as a fallback where needed.
```

### Does SENTRA store my GitHub password?

```text
No. SENTRA uses GitHub's authorization flow rather than
asking users for their GitHub password.
```

Only describe authentication behavior that is actually implemented.

### Can multiple users connect different GitHub accounts?

```text
Yes. GitHub connections are associated with individual
SENTRA accounts.
```

### What does the risk score mean?

```text
It is SENTRA's repository-level assessment based on the
analysis signals implemented by the platform. It is not
a formal security certification.
```

---

# 31. Section 11 — Final CTA

Use a visually strong final section.

Heading:

```text
READY TO UNDERSTAND
YOUR REPOSITORY?
```

Supporting text:

```text
Connect GitHub and let SENTRA turn repository complexity
into clear security intelligence.
```

Buttons:

```text
Get Started →
Explore How It Works
```

---

# 32. Footer

Recommended:

```text
SENTRA
Repository Security & Intelligence Platform

Know your code. Secure what you ship.

PRODUCT
Features
How It Works
Documentation

COMPANY
About
Contact

ACCOUNT
Login
Get Started

────────────────────────────────

© 2026 SENTRA
```

Do not add fake:

- Social media
- Newsletter
- Careers
- Blog
- Enterprise
- Customer portals

unless actually implemented.

---

# 33. Secondary Public Pages

The Home page is the primary redesign target.

Create/update:

```text
/features/
/how-it-works/
/about/
/docs/
/contact/
```

These pages should use the same:

- Navbar
- Footer
- Typography
- Spacing
- Colors
- Button styles
- Motion principles

---

# 34. Features Page

## Heading

```text
REPOSITORY SECURITY,
ALL IN ONE PLACE.
```

Sections:

```text
Dependency Intelligence
Vulnerability Detection
License Intelligence
README Health
Repository Health
Risk Intelligence
```

Use large sections and visual examples rather than six identical cards.

---

# 35. How It Works Page

## Heading

```text
FROM REPOSITORY
TO SECURITY INTELLIGENCE.
```

Visual flow:

```text
GitHub
  ↓
Connect
  ↓
Select Repository
  ↓
Inspect
  ↓
Retrieve Supported Files
  ↓
Analyze
  ↓
Risk Assessment
  ↓
SENTRA Dashboard
```

---

# 36. About Page

## Heading

```text
WHY WE BUILT SENTRA.
```

Explain the problem:

```text
Software repositories increasingly depend on open-source
components and external packages. Developers need visibility
into what their projects depend on and where risks exist.
```

Explain the mission:

```text
SENTRA aims to make repository security information easier
to discover, understand, and act on.
```

Add the actual team members if desired.

Do not invent achievements or company claims.

---

# 37. Documentation Page

Sections:

```text
Getting Started
Connect GitHub
Select Repository
Automatic Repository Analysis
Understanding Dependencies
Understanding Vulnerabilities
Understanding Licenses
README Health
Risk Assessment
Supported Dependency Files
```

Only document functionality that actually exists.

---

# 38. Contact Page

Keep it simple.

Heading:

```text
LET'S TALK ABOUT SENTRA.
```

Provide real team/project contact details.

If no real email backend exists, do not create a fake "Send Message" form.

A static contact section is acceptable.

---

# 39. Template Architecture

Use reusable Django templates.

Recommended:

```text
templates/
└── public/
    ├── base.html
    ├── home.html
    ├── features.html
    ├── how_it_works.html
    ├── about.html
    ├── documentation.html
    ├── contact.html
    └── components/
        ├── navbar.html
        ├── footer.html
        ├── section_label.html
        └── cta.html
```

Adapt to the existing project structure instead of duplicating templates.

---

# 40. Public Base Template

The base template should provide:

```text
DOCTYPE
HTML
head
metadata
title block
stylesheet links
navbar
main content block
footer
JavaScript
```

Example:

```django
{% extends "..." %}

{% block title %}
SENTRA
{% endblock %}

{% block content %}
...
{% endblock %}
```

---

# 41. CSS Architecture

Use a dedicated public stylesheet.

Recommended:

```text
static/
└── css/
    ├── public.css
    └── public-responsive.css
```

If the project already has a centralized stylesheet, integrate the public styles into it instead of creating unnecessary files.

Create reusable classes:

```text
container
section
section-label
display-heading
body-copy
primary-button
secondary-button
feature-item
analysis-card
metric-row
faq-item
cta-section
```

Avoid inline styles wherever possible.

---

# 42. JavaScript Architecture

Use vanilla JavaScript.

Possible functionality:

```text
Mobile navigation
Scroll reveal
FAQ accordion
Hero visualization
Metric animation
Navbar state
Smooth scrolling
Reduced-motion handling
```

Do not add JavaScript for simple static behavior.

---

# 43. Animation Principles

Animations should communicate product intelligence.

Good examples:

```text
Scanning indicator
Data flowing into analysis modules
Security score appearing
Cards entering viewport
FAQ expansion
Button hover
Navigation transition
```

Avoid:

```text
Constant bouncing
Heavy parallax
Excessive particles
Large distracting video backgrounds
Long loading animations
```

---

# 44. Scroll-Based Visual Storytelling

Use scroll sections to tell the product story.

Example:

```text
USER SCROLLS
     ↓
Problem
     ↓
Repository complexity
     ↓
SENTRA inspection
     ↓
Multiple signals
     ↓
Risk intelligence
     ↓
Actionable result
     ↓
Get Started
```

This is one of the key UX ideas to take from the reference site.

---

# 45. Responsive Design

Desktop:

```text
Large hero
2-column hero
large typography
wide analysis visual
```

Tablet:

```text
Reduced typography
2-column or stacked sections
```

Mobile:

```text
Single-column layout
Collapsed navbar
Readable typography
Horizontal overflow avoided
Full-width buttons where appropriate
```

Never allow:

- Horizontal page scrolling
- Text clipped by viewport
- Overlapping cards
- Unusable navigation

---

# 46. Accessibility

Implement:

- Semantic HTML
- Proper headings
- Accessible navigation
- Keyboard navigation
- Visible focus states
- Form labels
- Alt text
- ARIA only where necessary
- Reduced-motion support
- Sufficient contrast

Support:

```css
@media (prefers-reduced-motion: reduce) {
    ...
}
```

---

# 47. SEO / Metadata

Home title:

```text
SENTRA — Repository Security & Intelligence Platform
```

Description:

```text
SENTRA analyzes GitHub repositories for dependency,
vulnerability, license, documentation, and repository-health risks.
```

Other titles:

```text
SENTRA | Features
SENTRA | How It Works
SENTRA | About
SENTRA | Documentation
SENTRA | Contact
```

Add:

- viewport meta
- description
- Open Graph metadata if appropriate
- favicon
- semantic headings

---

# 48. Favicon / Brand Asset

Create a simple SENTRA favicon based on the product's existing visual identity.

Do not copy another company's logo.

The favicon should work at:

```text
16x16
32x32
180x180
```

where applicable.

---

# 49. Image and Asset Policy

Do not download or reuse the reference website's proprietary images.

Instead use:

- CSS-generated visuals
- Original SVG illustrations
- Original repository/security diagrams
- Original icons
- Existing project assets
- Properly licensed assets where needed

For SENTRA, CSS/SVG product visualizations are preferred over stock photos.

---

# 50. Demo Data Policy

Public pages may use fictional demo data.

Example:

```text
example-api
87 / 100
2 vulnerabilities
README missing
```

Clearly treat this as a demonstration.

Never expose:

- Actual user repositories
- Private GitHub repository information
- Real access tokens
- Real user email addresses
- Internal project data

---

# 51. Django URL Architecture

Public routes should conceptually be:

```text
/
 /features/
 /how-it-works/
 /about/
 /docs/
 /contact/
```

Authentication:

```text
/auth/login/
/auth/signup/
```

Authenticated:

```text
/dashboard/
/projects/
/repositories/
/scans/
/dependencies/
/vulnerabilities/
/reports/
```

Use the project's existing authentication URLs if they differ.

---

# 52. Public Views

If the existing `frontend` app is responsible for public pages, add public views there.

Possible structure:

```text
frontend/
    views.py
    public_views.py
```

or use a dedicated page app:

```text
pages/
    views.py
    urls.py
```

Do not create unnecessary Django apps if the current architecture does not require them.

---

# 53. Authentication Boundary

Public routes:

```text
/
features
how-it-works
about
docs
contact
login
signup
```

must not require authentication.

Application routes must remain protected.

Do not accidentally put `@login_required` on public views.

---

# 54. Existing Login Page

The current Login page already has the SENTRA identity:

```text
Welcome back to SENTRA
Repository Security & Intelligence Platform
```

Keep the existing login functionality.

The new Home page should link to it.

Do not redesign authentication at the same time unless necessary.

---

# 55. Existing Signup Page

Ensure:

```text
Get Started
```

and:

```text
Create Account
```

link to the existing signup page.

Preserve:

- Custom User model
- Email login
- Validation
- Password hashing
- CSRF
- Redirect logic

---

# 56. Do Not Change Backend Analysis Logic

The public redesign must not rewrite:

```text
scanner
dependencies
vulnerabilities
reports
risk engine
GitHub services
OAuth services
```

unless required to expose a small safe demo API.

Prefer static demo data on the public page.

---

# 57. Do Not Put Real Analysis on the Home Page

The landing page should not scan repositories automatically when a visitor loads `/`.

Avoid:

```text
GET /
    ↓
GitHub API
    ↓
Repository scan
```

The public page should be fast.

Actual repository analysis happens after:

```text
Signup/Login
    ↓
Connect GitHub
    ↓
Select Repository
```

---

# 58. Performance Requirements

The home page should be fast.

Avoid:

- Large unoptimized videos
- Huge image files
- Dozens of JavaScript libraries
- Blocking scripts
- Unnecessary API requests
- Heavy animations

Prefer:

- CSS
- SVG
- Optimized images
- Vanilla JS
- Lazy loading
- Minimal dependencies

---

# 59. Mobile Menu

Implement a functional menu.

Behavior:

```text
Desktop:
SENTRA | links | buttons

Mobile:
SENTRA | ☰

Click:
--------------------
Home
Features
How It Works
About
Docs
Contact
Login
Get Started
--------------------
```

Click outside or select a link to close where appropriate.

---

# 60. FAQ Accordion

Implement a simple vanilla-JS accordion.

Default:

```text
+ What is SENTRA?
+ What can SENTRA analyze?
+ How does GitHub integration work?
+ Does SENTRA automatically find dependency files?
+ How is the risk score calculated?
```

When opened:

```text
− What is SENTRA?

SENTRA is a repository security and intelligence platform...
```

Only one or multiple open items depending on the final UX decision.

---

# 61. Hero Repository Animation

Recommended implementation:

```text
HTML
  +
CSS animation
  +
small vanilla JS state changes
```

Possible states:

```text
Scanning repository...
Discovering dependencies...
Checking vulnerabilities...
Analyzing licenses...
Checking README...
Calculating risk...
Analysis complete
```

Then:

```text
87 / 100
LOW RISK
```

This creates a strong visual demonstration of the product.

---

# 62. Security Score Visualization

Use a circular or large numerical score.

Example:

```text
              87
             /100

          LOW RISK
```

Below:

```text
Dependencies       ✓
Vulnerabilities    ⚠ 2
Licenses            ✓
README              ⚠
Repository Health   ✓
```

This is demo content only.

---

# 63. Visual Section Transitions

Use sections that visually change rather than placing every section in a bordered card.

Example:

```text
DARK HERO
     ↓
LIGHT PROBLEM
     ↓
DARK INTELLIGENCE
     ↓
LIGHT ANALYSIS
     ↓
DARK CTA
```

This creates visual rhythm.

---

# 64. Component Reuse

Create reusable components for:

```text
Navbar
Footer
Button
Section Label
Feature/Intelligence Item
Analysis Card
FAQ Item
CTA
```

Do not copy/paste the same HTML into multiple templates.

---

# 65. Recommended Implementation Workflow

## Phase 1 — Inspect

Before coding:

```text
Inspect Django structure
Inspect current templates
Inspect current CSS
Inspect current JS
Inspect login URL
Inspect signup URL
Inspect static configuration
```

Do not overwrite existing files blindly.

---

## Phase 2 — Create Public Shell

Implement:

```text
base.html
navbar
footer
global CSS
```

Test them before building the Home page.

---

## Phase 3 — Build Hero

Implement:

```text
Navbar
Hero
Hero buttons
Repository visualization
```

Test desktop and mobile.

---

## Phase 4 — Build Content Sections

Implement:

```text
Problem
Security signals
SENTRA intelligence
How it works
Example report
Why SENTRA
FAQ
Final CTA
```

---

## Phase 5 — Add Motion

After static layout is correct, add:

```text
Scroll reveal
Hero animation
FAQ accordion
Navbar transition
Hover states
```

Do not add animations before the layout is stable.

---

## Phase 6 — Secondary Pages

Implement:

```text
Features
How It Works
About
Documentation
Contact
```

Reuse the public shell.

---

## Phase 7 — Connect Authentication

Test:

```text
Get Started → Signup
Login → Login
```

Do not alter authentication logic unnecessarily.

---

## Phase 8 — Responsive Review

Test:

```text
Desktop
Laptop
Tablet
Mobile
```

---

## Phase 9 — Security Review

Check:

```text
No tokens exposed
No private repository data
No API credentials
No debug data
No real user information
```

---

## Phase 10 — Final QA

Run all application tests and manually inspect the entire user journey.

---

# 66. Antigravity IDE Instructions

The implementation can be handed to an IDE agent such as Antigravity.

However, do **not** provide only:

```text
Make my site look like https://www.eloqwnt.com
```

Instead provide:

1. Reference URL
2. This complete design plan
3. Existing project directory
4. Existing technology constraints
5. Explicit "inspiration, not clone" instruction
6. Existing functionality that must not be changed

---

# 67. Recommended Antigravity Master Prompt

Use this as the implementation prompt:

```text
I am redesigning the public-facing website of my existing
Django project.

PRODUCT:
SENTRA — Repository Security & Intelligence Platform

TAGLINE:
Know your code. Secure what you ship.

REFERENCE:
https://www.eloqwnt.com/

IMPORTANT:
Use the reference website only as visual and UX inspiration.

Do NOT clone the reference website.

Do NOT copy:
- logos
- text
- images
- illustrations
- client logos
- testimonials
- proprietary assets
- exact branding

Create an original SENTRA design inspired by:
- strong typography
- large whitespace
- bold hero composition
- visual storytelling
- metrics/signals
- large numbered sections
- polished navigation
- smooth transitions
- FAQ structure
- strong final CTA
- premium responsive UX

TECH STACK:
- Django
- Django templates
- HTML
- CSS
- Vanilla JavaScript
- Existing Chart.js where already used

DO NOT migrate to React, Next.js, Vue, Angular,
or another frontend framework.

IMPORTANT:
Inspect the existing project before changing anything.

First identify:
1. Django project structure
2. Existing frontend templates
3. Existing static files
4. Existing login URL
5. Existing signup URL
6. Existing dashboard routes
7. Existing GitHub OAuth implementation
8. Existing repository analysis implementation

DO NOT BREAK:
- authentication
- login
- signup
- GitHub OAuth
- per-user GitHub account isolation
- repository import
- automatic repository analysis
- dependency analysis
- vulnerability analysis
- license analysis
- README analysis
- repository health
- risk engine
- dashboard
- projects
- scans
- reports

ONLY redesign/add the public website.

PUBLIC ROUTES:

/
 /features/
 /how-it-works/
 /about/
 /docs/
 /contact/

Authentication remains at the existing URLs.

HOME PAGE:

Hero:

"KNOW YOUR CODE.
SECURE WHAT YOU SHIP."

Description:

"SENTRA automatically analyzes your GitHub repositories
to uncover dependency risks, vulnerabilities, license
issues, documentation gaps, and repository-health signals."

Buttons:

"Get Started →"
"Explore SENTRA"

Create an original repository analysis visualization.

Show:

GitHub Repository
→ SENTRA Inspection
→ Dependencies
→ Vulnerabilities
→ Licenses
→ README
→ Repository Health
→ Risk Engine
→ Security Score

Use fictional demo data only.

HOME SECTIONS:

1. Hero
2. Security signals
3. Problem
4. SENTRA Intelligence
5. Repository analysis visualization
6. How SENTRA Works
7. Example security report
8. Why SENTRA
9. FAQ
10. Final CTA
11. Footer

DESIGN:

- Premium security/developer product
- Large typography
- Strong spacing
- Minimal layout
- Dark/light section contrast
- Blue/cyan SENTRA accent
- Subtle motion
- Responsive
- Accessible
- Fast

Avoid:
- generic SaaS cards everywhere
- excessive gradients
- excessive glassmorphism
- stock photos
- fake customer logos
- fake metrics
- fake testimonials
- unnecessary libraries

Create reusable Django components:

navbar
footer
buttons
section labels
intelligence items
analysis card
FAQ
CTA

Use a shared public base template.

Create public CSS and vanilla JS where appropriate.

Implement mobile navigation.

Implement FAQ accordion.

Implement subtle hero scanning animation.

Support prefers-reduced-motion.

Do not call GitHub APIs from the public landing page.

Do not expose private data.

Do not modify backend analysis logic.

After implementation run:

python manage.py check

and test:

- /
- /features/
- /how-it-works/
- /about/
- /docs/
- /contact/
- existing login
- existing signup
- existing dashboard

Also verify:
- no console errors
- no broken links
- no horizontal overflow
- responsive behavior
- no authentication regressions

Before finishing, provide a summary of:
- files created
- files modified
- routes added
- functionality preserved
- tests performed
```

---

# 68. Important Antigravity Safety Rule

Do not allow the IDE agent to perform a large rewrite before inspecting the repository.

Correct sequence:

```text
Inspect
   ↓
Plan
   ↓
Implement
   ↓
Test
   ↓
Review
```

Not:

```text
Prompt
   ↓
Rewrite entire frontend
```

---

# 69. Git Workflow Before Implementation

Create a dedicated branch:

```bash
git checkout -b feat/sentra-public-website
```

Then inspect the current state:

```bash
git status
git log --oneline -5
```

Make a backup/commit before major changes:

```bash
git add .
git commit -m "chore: checkpoint before public website redesign"
```

This makes it easy to revert if the IDE agent damages existing pages.

---

# 70. Git Workflow After Implementation

Review:

```bash
git status
git diff
```

Run:

```bash
python manage.py check
python manage.py test
```

Then manually test the browser.

If everything works:

```bash
git add .
git commit -m "feat: add SENTRA public website"
git push -u origin feat/sentra-public-website
```

Merge after review.

---

# 71. Definition of Done

## Visual

- [ ] Premium hero implemented
- [ ] Strong typography
- [ ] Large whitespace
- [ ] Dark/light section rhythm
- [ ] Original repository visualization
- [ ] Consistent SENTRA branding
- [ ] Professional CTA
- [ ] No copied Eloqwnt assets

## Public pages

- [ ] Home
- [ ] Features
- [ ] How It Works
- [ ] About
- [ ] Documentation
- [ ] Contact

## Navigation

- [ ] Desktop navbar
- [ ] Mobile menu
- [ ] Login link
- [ ] Get Started link
- [ ] Footer

## Interaction

- [ ] Hero animation
- [ ] Scroll effects
- [ ] FAQ accordion
- [ ] Hover states
- [ ] Reduced-motion support

## Backend

- [ ] Django routing works
- [ ] Public pages don't require authentication
- [ ] Login still works
- [ ] Signup still works
- [ ] Dashboard still works
- [ ] GitHub OAuth still works
- [ ] Repository import still works
- [ ] Automatic analysis still works

## Security

- [ ] No GitHub tokens exposed
- [ ] No private repository information exposed
- [ ] No credentials in frontend
- [ ] No real user data on public pages
- [ ] No debug information exposed

## Quality

- [ ] Desktop tested
- [ ] Tablet tested
- [ ] Mobile tested
- [ ] No horizontal overflow
- [ ] No broken links
- [ ] No console errors
- [ ] Django checks pass
- [ ] Tests pass

---

# 72. Final User Experience

The final experience should feel like this:

```text
                    VISITOR
                       |
                       v
                ┌──────────────┐
                │    SENTRA    │
                │              │
                │ KNOW YOUR    │
                │ CODE.        │
                │ SECURE WHAT  │
                │ YOU SHIP.    │
                └──────┬───────┘
                       |
                       v
              Understand the Problem
                       |
                       v
                Explore SENTRA
                       |
                       v
             See Repository Analysis
                       |
                       v
              Understand the Workflow
                       |
                       v
                GET STARTED
                       |
                       v
                    SIGN UP
                       |
                       v
                    LOGIN
                       |
                       v
                CONNECT GITHUB
                       |
                       v
              SELECT REPOSITORY
                       |
                       v
          AUTOMATIC REPOSITORY ANALYSIS
                       |
                       v
                SENTRA DASHBOARD
```

---

# 73. Final Design Principle

The most important principle for this redesign is:

> **Borrow the visual quality, not the identity.**

The reference website should inspire:

- composition
- typography
- spacing
- storytelling
- motion
- section rhythm
- visual hierarchy

But SENTRA should have its own:

- security language
- repository visualizations
- product concepts
- color identity
- copy
- information architecture
- interaction patterns

The finished page should make someone think:

> **"This looks like a serious repository-security product."**

not:

> **"This looks like a copy of another website."**
