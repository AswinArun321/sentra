# SENTRA — Simplified Public Website UI/UX Plan

## 1. Objective

Simplify the public-facing SENTRA website so it is clean, standardized, professional, and easy to navigate.

Visual inspiration:
- https://sentira.framer.website/
- https://www.framer.com/marketplace/templates/sentira/

Use these only as visual inspiration. Do not clone Sentira branding, text, assets, images, or identity.

### Core principle

> Keep the public website simple. Move Features, How It Works, and Documentation into one concise About page.

The About page must remain short and must not become a full documentation page.

---

# 2. New Public Navigation

### Current

```text
SENTRA.
Home | Features | How It Works | About | Documentation | Contact
Sign In | Get Started
```

### New

```text
SENTRA.
Home | About | Contact
Sign In | Get Started
```

Remove Features, How It Works, and Documentation from the primary navbar.

Keep the existing theme/light-dark toggle if it already works.

---

# 3. Final Public Structure

```text
/
├── Home
├── About
├── Contact
├── Login
└── Signup
```

The existing Documentation route, such as `/docs/`, may remain available directly. Do not delete existing routes or files blindly.

---

# 4. About Page Goal

The About page should be:

- Short
- Simple
- Standardized
- Professional
- Easy to scan
- Visually consistent with SENTRA
- Sentira-inspired in visual language
- Focused on the actual product

Avoid:

- Long company history
- Long paragraphs
- Full technical documentation
- Repeated marketing content
- Excessive cards
- Unnecessary sections

Target approximately one to two desktop screen lengths depending on typography and spacing.

---

# 5. About Page Structure

```text
ABOUT SENTRA
      ↓
WHAT SENTRA DOES
      ↓
HOW IT WORKS
      ↓
DOCUMENTATION CTA
      ↓
FINAL CTA
```

Only these major sections are required.

---

# 6. About Hero

Label:

```text
ABOUT SENTRA
```

Heading:

```text
Repository security,
made understandable.
```

Description:

```text
SENTRA is a repository security and intelligence
platform that helps developers understand their
dependencies, vulnerabilities, licenses and
repository health.
```

Keep it spacious and concise. Do not add a long company story.

---

# 7. What SENTRA Does

Heading:

```text
WHAT SENTRA DOES
```

Use four concise numbered items.

### 01 — Repository Analysis

```text
Connect and analyze GitHub repositories.
```

### 02 — Security Intelligence

```text
Identify dependency and vulnerability risks.
```

### 03 — Repository Health

```text
Understand documentation and repository health.
```

### 04 — Reports

```text
Generate structured security reports.
```

Each item may contain a number, title, one-sentence description, small icon, and arrow/hover indicator.

Do not turn these into large dashboard-style cards.

---

# 8. How It Works

Heading:

```text
HOW IT WORKS
```

Use four concise steps.

### 01 — Connect
Connect your GitHub account.

### 02 — Analyze
SENTRA inspects your repository and dependencies.

### 03 — Understand
Review vulnerabilities, licenses and risk insights.

### 04 — Secure
Use the findings to improve your repository.

Desktop can use a horizontal or 2x2 layout. Mobile should stack the steps vertically.

Keep this section concise; the About page is not a technical manual.

---

# 9. Documentation Section

Do not place the entire documentation page inside About.

Heading:

```text
DOCUMENTATION
```

Text:

```text
Everything you need to understand how SENTRA
works and how to use its main features.
```

Button:

```text
View Documentation →
```

The button must point to the existing documentation route, such as `/docs/`.

---

# 10. Final CTA

Heading:

```text
READY TO UNDERSTAND
YOUR REPOSITORIES?
```

Button:

```text
Get Started
```

Optional supporting line:

```text
Know your code. Secure what you ship.
```

Do not add more sections after the CTA.

---

# 11. About Page Wireframe

```text
┌─────────────────────────────────────────────────────┐
│                                                     │
│                  ABOUT SENTRA                       │
│                                                     │
│          Repository security,                       │
│          made understandable.                       │
│                                                     │
│          SENTRA is a repository security and        │
│          intelligence platform...                   │
│                                                     │
└─────────────────────────────────────────────────────┘

WHAT SENTRA DOES

01                         02
Repository Analysis        Security Intelligence
Connect and analyze        Identify dependency and
GitHub repositories.       vulnerability risks.

03                         04
Repository Health          Reports
Understand documentation   Generate structured
and repository health.     security reports.

─────────────────────────────────────────────────────

HOW IT WORKS

01              02              03              04
CONNECT         ANALYZE         UNDERSTAND      SECURE

Connect         Inspect         Review          Improve
GitHub.         repository.     findings.       repository.

─────────────────────────────────────────────────────

DOCUMENTATION

Everything you need to understand how SENTRA works.

              [ View Documentation → ]

─────────────────────────────────────────────────────

READY TO UNDERSTAND
YOUR REPOSITORIES?

                  [ Get Started ]
```

---

# 12. Homepage Relationship

Home remains the main marketing/landing page.

Do not duplicate the entire Features and How It Works content on both Home and About.

Home can provide short previews. About contains the concise consolidated explanation.

Avoid repeating identical paragraphs across pages.

---

# 13. Navigation Behavior

- Home → existing home route
- About → `/about/`
- Contact → existing contact route
- Sign In → existing login route
- Get Started → existing signup/get-started flow
- Documentation → accessible through About → View Documentation → existing `/docs/` route

Documentation should not be a primary navbar item.

---

# 14. Existing Documentation Page

If `/docs/` already exists, preserve it unless there is an independent reason to change it.

The About page only provides a short entry point to it.

This keeps About short while preserving existing documentation functionality.

---

# 15. Header Design

Target:

```text
┌─────────────────────────────────────────────────────────────┐
│ SENTRA.   Home   About   Contact       Sign In  Get Started │
└─────────────────────────────────────────────────────────────┘
```

Retain the strengths visible in the current design:

- Rounded navigation container
- SENTRA branding
- Blue accent
- Neutral/off-white background
- Large editorial heading
- Pill labels
- Rounded buttons
- Generous whitespace
- Clean typography

Do not add unnecessary navigation items.

---

# 16. Mobile Header

```text
SENTRA.                                  ☰
```

Menu:

```text
Home
About
Contact

Sign In
Get Started
```

Keep it simple.

---

# 17. Visual Design Direction

Preserve and refine the current SENTRA visual language:

- Large editorial typography
- Neutral light background
- Near-black text
- SENTRA blue accent
- Rounded navbar
- Rounded buttons
- Pill labels
- Large whitespace
- Thin borders
- Clean grids
- Minimal visual noise

Do not add visual complexity just for decoration.

---

# 18. Typography

Suggested public hierarchy:

```text
Hero: 72–120px
H1: 64–88px
H2: 48–64px
H3: 28–36px
Body: 16–20px
Small labels: 13–14px
```

Use responsive typography.

---

# 19. Spacing

Use a consistent rhythm:

```text
8px  12px  16px  24px  32px
48px 64px 96px 128px
```

Use generous whitespace on public pages.

---

# 20. Cards and Components

Avoid excessive floating cards.

Prefer:

- Numbered content
- Thin separators
- Open layouts
- Large headings
- Simple icons
- Spacious grids
- Minimal borders

The About page should feel editorial rather than like an admin dashboard.

---

# 21. Animation

Use subtle animation only:

- Hero fade-in
- Section reveal
- Number reveal
- Small hover translation
- CTA hover
- Smooth transitions

Avoid excessive parallax, constant movement, distracting backgrounds, and heavy animation libraries.

Respect `prefers-reduced-motion`.

---

# 22. Responsive Design

Desktop:
- Spacious centered layout
- 2x2 What SENTRA Does grid
- Horizontal How It Works where appropriate

Tablet:
- Two columns where comfortable

Mobile:
- One column
- Stacked numbered sections
- Stacked How It Works steps
- No horizontal scrolling

---

# 23. Accessibility

Maintain:

- Semantic HTML
- One H1
- Logical H2 hierarchy
- Keyboard navigation
- Visible focus states
- Accessible buttons and links
- Good contrast
- Reduced-motion support

---

# 24. SEO

Suggested title:

```text
About SENTRA — Repository Security & Intelligence
```

Suggested description:

```text
Learn how SENTRA helps developers understand repository
security, dependencies, vulnerabilities, licenses and
repository health.
```

---

# 25. Backend Protection

This is a UI/UX and information-architecture change.

Do not change:

- Django models
- Migrations
- Database schema
- Authentication logic
- GitHub OAuth
- GitHub repository isolation
- Repository import
- Automatic analysis
- Dependency parser
- Vulnerability analyzer
- License analyzer
- Risk engine
- Scan logic
- Report generation
- PDF generation
- API contracts
- Security controls

Use existing routes and functionality wherever possible.

---

# 26. Route Safety

If these currently exist:

```text
/features/
/how-it-works/
/docs/
/about/
```

do not delete them blindly.

First search the project for references to them.

Only remove them from the main navbar unless there is a separate requirement to retire the routes.

---

# 27. Content Consolidation

Conceptually consolidate:

```text
FEATURES
   ↓
WHAT SENTRA DOES
   ↓
ABOUT

HOW IT WORKS
   ↓
HOW IT WORKS SECTION
   ↓
ABOUT

DOCUMENTATION
   ↓
DOCUMENTATION CTA
   ↓
ABOUT → /docs/
```

Do not duplicate full page content.

---

# 28. Implementation Steps

## Step 1 — Inspect

Inspect the existing public templates, routes, CSS and JavaScript.

## Step 2 — Navbar

Change the primary navigation to:

```text
Home
About
Contact
```

Keep:

```text
Sign In
Get Started
```

## Step 3 — About

Create:

```text
About Hero
↓
What SENTRA Does
↓
How It Works
↓
Documentation CTA
↓
Final CTA
```

## Step 4 — Content

Reuse useful content from Features and How It Works, but keep only concise content.

## Step 5 — Documentation

Keep the existing documentation page/route and link to it from About.

## Step 6 — Mobile

Update mobile navigation.

## Step 7 — Visual polish

Apply the existing SENTRA/Sentira-inspired design language.

## Step 8 — Testing

Verify all links and existing functionality.

---

# 29. Antigravity Implementation Prompt

Copy this into Antigravity:

```text
Update the public SENTRA website information architecture and About page.

PRIMARY VISUAL REFERENCE:
https://sentira.framer.website/

SECONDARY REFERENCE:
https://www.framer.com/marketplace/templates/sentira/

Use these only as visual inspiration.

DO NOT clone Sentira.
Do not copy its branding, logo, text, images, assets or identity.

The goal is to make SENTRA simpler, cleaner and more premium.

IMPORTANT:
This is a UI/UX and public information-architecture change.

DO NOT change:
- Django models
- migrations
- database
- authentication logic
- GitHub OAuth
- GitHub repository isolation
- repository import
- automatic repository analysis
- dependency analysis
- vulnerability analysis
- license analysis
- risk engine
- scans
- reports
- PDF generation
- API contracts
- security controls

Keep all existing backend functionality.

PUBLIC NAVIGATION:

Replace:
Home
Features
How It Works
About
Documentation
Contact

with:
Home
About
Contact

Keep:
Sign In
Get Started

Remove Features, How It Works and Documentation from the primary navbar.
Do not blindly delete their existing routes or files. Inspect references first.

ABOUT PAGE:

Make the About page short and standardized.
Do NOT make it a long About page.

Structure:
1. About Hero
2. What SENTRA Does
3. How It Works
4. Documentation CTA
5. Final CTA

ABOUT HERO:

ABOUT SENTRA

Repository security,
made understandable.

Supporting text:
SENTRA is a repository security and intelligence platform that helps developers understand their dependencies, vulnerabilities, licenses and repository health.

WHAT SENTRA DOES:

01 Repository Analysis
Connect and analyze GitHub repositories.

02 Security Intelligence
Identify dependency and vulnerability risks.

03 Repository Health
Understand documentation and repository health.

04 Reports
Generate structured security reports.

HOW IT WORKS:

01 Connect
Connect your GitHub account.

02 Analyze
SENTRA inspects your repository and dependencies.

03 Understand
Review vulnerabilities, licenses and risk insights.

04 Secure
Use the findings to improve your repository.

DOCUMENTATION:

Keep this section very short.

Heading:
DOCUMENTATION

Text:
Everything you need to understand how SENTRA works and how to use its main features.

Button:
View Documentation →

Use the existing documentation route, such as /docs/, if that is the current route.
Do NOT place the entire documentation content inside About.

FINAL CTA:

READY TO UNDERSTAND
YOUR REPOSITORIES?

[ Get Started ]

Optional:
Know your code. Secure what you ship.

DESIGN:

Maintain the current SENTRA direction:
- rounded navbar
- neutral/off-white background
- near-black text
- SENTRA blue accent
- large editorial typography
- pill labels
- rounded buttons
- generous whitespace
- thin borders
- clean grids
- minimal visual noise

Avoid:
- excessive cards
- excessive text
- unnecessary animations
- duplicate sections
- fake statistics
- fake customer stories

RESPONSIVE:
Desktop:
- 2x2 grid for What SENTRA Does
- horizontal How It Works where appropriate

Mobile:
- single-column layout
- stacked numbered sections
- compact navigation drawer

ACCESSIBILITY:
Maintain semantic HTML, keyboard navigation, visible focus states, proper heading hierarchy, good contrast and reduced-motion support.

IMPORTANT:
Do not break Home, About, Contact, Documentation, Login, Signup, Get Started or theme switching.
Do not change backend logic.

After implementation run:

python manage.py check
python manage.py test

Then manually verify:
Home
About
Contact
Documentation link
Login
Signup
Get Started
Theme toggle
Mobile navigation

FINAL GOAL:

The public navbar should be:

SENTRA.

Home
About
Contact

Sign In
Get Started

The About page should explain:
- What SENTRA is
- What SENTRA does
- How SENTRA works
- Where to find documentation

It should remain concise, standardized and visually premium.

Do not turn About into a long page.
```

---

# 30. Final Information Architecture

```text
                         SENTRA.
                           │
             ┌─────────────┼─────────────┐
             │             │             │
            HOME          ABOUT        CONTACT
                           │
                ┌──────────┼───────────┐
                │          │           │
             WHAT IT    HOW IT      DOCUMENTATION
              DOES      WORKS          CTA
                           │
                           ↓
                    GET STARTED
```

---

# 31. Final Navbar

```text
┌─────────────────────────────────────────────────────────────┐
│ SENTRA.   Home   About   Contact       Sign In  Get Started │
└─────────────────────────────────────────────────────────────┘
```

---

# 32. Final User Journey

```text
Home
 ↓
What is SENTRA?
 ↓
About
 ↓
What does it do?
 ↓
How does it work?
 ↓
Documentation if needed
 ↓
Get Started
 ↓
Signup/Login
 ↓
Dashboard
```

No unnecessary navigation. No unnecessary marketing pages. No unnecessarily long About page.

---

# 33. Final Principle

The public website should communicate the product quickly:

```text
WHAT IS SENTRA?
Repository security platform.

WHAT DOES IT DO?
Analyzes repositories and security signals.

HOW DOES IT WORK?
Connect → Analyze → Understand → Secure

WHERE CAN I LEARN MORE?
Documentation.

WHAT SHOULD I DO NEXT?
Get Started.
```

> **Simple structure. Strong typography. Clear product story. Premium SENTRA experience.**

### SENTRA

> **Know your code. Secure what you ship.**
