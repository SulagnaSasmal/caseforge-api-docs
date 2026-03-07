# CaseForge API Documentation

> Enterprise AML and SAR filing API reference — built from a production-grade OpenAPI 3.0 specification, normalized to Stripe quality documentation standards with multi-language code samples, CSRF authentication guides, and end-to-end validation walkthroughs.

![License](https://img.shields.io/badge/license-MIT-blue)
![API Version](https://img.shields.io/badge/API_version-v10.1-brightgreen)
![Endpoints](https://img.shields.io/badge/endpoints-25+-orange)
![Languages](https://img.shields.io/badge/code_samples-Python_%7C_JS_%7C_Java_%7C_C%23_%7C_cURL-blueviolet)

## Live documentation

[Open the live portal →](https://sulagnasasmal.github.io/caseforge-api-docs/)

Or run locally — no build step, no dependencies, no server required:

```bash
open index.html
# or
python3 -m http.server 8000
```

## What this project demonstrates

This project takes a real enterprise REST API specification (12,000+ line OpenAPI YAML from a compliance platform) and restructures it into a polished developer documentation portal. The goal is not just to describe what each endpoint does — it's to explain why it exists, what can break, and how to confirm it is working end to end.

### Documentation gaps addressed from the original spec

| Gap in original spec | Fix applied |
|---|---|
| Missing error response schema | Structured error format with `type`, `code`, `message`, `param`, `request_id` |
| Empty tag descriptions | Complete descriptions written for all API categories |
| No rate-limiting guidance | Tiered rate limit structure with response headers and retry logic |
| No pagination guidance | Documented offset-based pagination with `startIndex`, `maxNumOfRows`, `rowLimitExceeded` |
| No authentication flow explanation | Session + CSRF token lifecycle with visual flow and multi-language samples |
| Inconsistent error descriptions | Standardized to specific, actionable messages throughout |
| No permission documentation | Permission badges on every endpoint with license tier requirements |
| No changelog | Versioned changelog reconstructed from inline annotations in the spec |
| No code samples | Python, JavaScript, Java, C#, and cURL samples with error handling and validation |
| Generic `*/*` content types | Specified `application/json` with structured response schemas |

### API sections covered

- **Authentication** — Session login/logout, CSRF tokens, password management
- **Work Items** — CRUD operations for alerts, cases, and SARs with workflow lifecycle
- **Data Ingestion** — External system integration with field mapping definitions
- **Groups and Users** — Batch membership management with partial success handling
- **Policy Engine** — Rule CRUD, simulation, versioning, import/export
- **System Configuration** — Data source connections, custom fields, multi-tenancy
- **Graph Analytics** — Graph database query management and execution (Beta)

## Code samples

Ready-to-run samples in five languages covering authentication, case creation, and end-to-end validation:

```
code-samples/
├── python/
│   ├── authenticate.py       Session auth + CSRF token extraction
│   └── work_items.py         Create, read, and validate a SAR case
├── javascript/
│   ├── authenticate.js       Node.js fetch with cookie forwarding
│   └── work_items.js         Case lifecycle with end-to-end assertions
├── java/
│   └── AuthenticateExample.java  HttpClient + CookieManager pattern
├── csharp/
│   └── AuthenticateExample.cs    HttpClient + CookieContainer + default headers
└── curl/
    └── authenticate.sh       Full auth flow with CSRF extraction, bash-safe
```

Each sample includes:

- The **why** — why this authentication model exists, not just how to call it
- The **what can go wrong** — specific error codes, what triggers them, and how to fix them
- The **how to validate** — assertions you can run to confirm the integration is working

## Design decisions

- **Session-based auth explainer** — The authentication section explains why CaseForge uses JSESSIONID + CSRF rather than bearer tokens, which is the number-one question from developers integrating with the platform for the first time.
- **Error codes as first-class content** — Every error response includes the HTTP status, the internal error code, a plain-English cause, and the corrective step. Developers can find the fix without reading a separate troubleshooting page.
- **Dark theme with warm amber accents** — Avoids the generic light-mode documentation aesthetic.
- **Collapsible endpoint cards** — Stripe/Twilio interaction pattern. Developers scan the endpoint list, expand only what they need.
- **Permission and license badges** — Inline on every endpoint, so a developer knows immediately whether their account tier supports the call.
- **Scroll-tracking sidebar** — Intersection Observer-based active state.
- **Responsive** — Works on mobile and tablet.

## Tech stack

- Single HTML file — zero dependencies, zero build step
- Fonts: Source Serif 4 (headings), Outfit (body), JetBrains Mono (code)
- Vanilla JS — collapsible cards, scroll tracking, copy buttons

## Quick start

### GitHub Pages

1. Fork this repository.
2. Go to **Settings → Pages → Deploy from main branch**.
3. Your portal is live at `your-username.github.io/caseforge-api-docs`.

### Local

```bash
open index.html
# or
python3 -m http.server 8000
```

### Code samples

```bash
# Python
cd code-samples/python
pip install requests
export CASEFORGE_HOST="https://your-instance.caseforge.io"
export CASEFORGE_USER="your.username"
export CASEFORGE_PASS="your.password"
python authenticate.py

# JavaScript (Node 18+)
cd code-samples/javascript
export CASEFORGE_HOST="https://your-instance.caseforge.io"
export CASEFORGE_USER="your.username"
export CASEFORGE_PASS="your.password"
node authenticate.js

# cURL
cd code-samples/curl
chmod +x authenticate.sh
./authenticate.sh
```

## Who this is for

- **Technical writers** evaluating API documentation patterns and multi-language sample architecture
- **Documentation teams** assessing how to handle session-based authentication documentation
- **Hiring managers** reviewing real-world documentation engineering with source-to-output traceability

## Source material

Built from a 12,779-line OpenAPI 3.0.1 specification for an enterprise case management platform. All proprietary names, URLs, and identifying details have been replaced with fictional equivalents. No confidential information is present.

## License

MIT — free for personal and commercial use.
