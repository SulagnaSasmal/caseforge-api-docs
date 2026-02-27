# CaseForge API Documentation

> A Stripe-quality API documentation portal for a fictional enterprise compliance & case management platform. Built from a real-world OpenAPI 3.0 specification, restructured with documentation best practices.

![License](https://img.shields.io/badge/license-MIT-blue)
![Version](https://img.shields.io/badge/API_version-v10.1-brightgreen)
![Endpoints](https://img.shields.io/badge/endpoints-25+-orange)

## Live Demo

Open `index.html` in any browser — no build step, no dependencies, no server required.

## What This Demonstrates

This project takes a **real enterprise REST API specification** (12,000+ line OpenAPI YAML from a compliance platform) and transforms it into a polished, Stripe-style developer documentation portal — showcasing the full spectrum of API documentation skills:

### Documentation Gaps Fixed (from source spec)

| Gap in Original Spec | Fix Applied |
|----------------------|-------------|
| Missing error response schema | Added structured error response format with `type`, `code`, `message`, `param`, `request_id` |
| Empty tag descriptions (`' '`) | Wrote complete descriptions for all API categories |
| No rate limiting documentation | Added tiered rate limit structure with headers and retry guidance |
| No pagination guidance | Documented offset-based pagination pattern with `startIndex`, `maxNumOfRows`, `rowLimitExceeded` |
| No authentication flow explanation | Created visual auth flow diagram + session/CSRF token lifecycle |
| Inconsistent error descriptions | Standardized all error responses with specific, actionable messages |
| Missing permission documentation | Added permission tags on every endpoint with license requirements |
| No changelog | Created versioned changelog from `From ActOne x.x` annotations scattered through descriptions |
| No code samples | Added cURL examples with proper auth headers for key endpoints |
| Generic `*/*` content types | Specified `application/json` with structured response schemas |
| Internal IP addresses as server URLs | Replaced with generic `{your-instance}.caseforge.io` pattern |

### API Categories Covered

- **Authentication** — Session login/logout, CSRF tokens, password management
- **Work Items** — CRUD operations for alerts, cases, SARs with workflow lifecycle
- **Data Ingestion** — External system integration with field mapping definitions
- **Groups & Users** — Batch membership management with partial success handling
- **Policy Engine** — Rule CRUD, simulation, versioning, import/export
- **System Configuration** — Data source connections, custom fields, multi-tenancy
- **Graph Analytics** — Graph DB query management and execution (Beta)

## Design Decisions

- **Dark theme** with warm amber accents — avoids generic AI aesthetics
- **Collapsible endpoint cards** — Stripe/Twilio interaction pattern
- **Color-coded HTTP methods** — GET (green), POST (blue), PUT (amber), DELETE (red)
- **Permission & license badges** — Inline on every endpoint
- **Scroll-tracking sidebar** — Intersection Observer-based active state
- **Responsive** — Works on mobile and tablet

## Tech Stack

- **Single HTML file** — Zero dependencies, zero build step
- **Fonts**: Source Serif 4 (headings), Outfit (body), JetBrains Mono (code)
- **Vanilla JS** — Collapsible cards, scroll tracking, copy buttons

## Quick Start

### GitHub Pages (recommended)

1. Fork this repository
2. Go to **Settings → Pages → Deploy from main branch**
3. Live at `your-username.github.io/caseforge-api-docs`

### Local

```bash
# Just open it
open index.html

# Or serve it
python3 -m http.server 8000
```

## Who This Is For

- **Technical Writers** demonstrating API documentation expertise
- **Documentation Teams** evaluating enterprise API doc patterns
- **Hiring Managers** assessing real-world documentation engineering skills

## Source Material

Built from a 12,779-line OpenAPI 3.0.1 specification for an enterprise case management platform. All proprietary names, URLs, and identifying details have been replaced with fictional equivalents.

## License

MIT — Free for personal and commercial use.

---

*Part of the [DocCraft Tools](https://github.com/your-username/doccraft-tools) portfolio — open-source documentation engineering projects.*
