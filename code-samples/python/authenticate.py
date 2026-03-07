"""
CaseForge API — Authentication Sample (Python)
===============================================

This sample covers the authentication flow for the CaseForge API. CaseForge
uses a session-based mechanism, not bearer tokens, because the platform is
designed for interactive web sessions rather than machine-to-machine calls.
If you are building an automated integration, use a dedicated service account
and manage the session cookie across all requests in your pipeline.

Why session cookies instead of API keys?
-----------------------------------------
CaseForge was built on a JSF-based web platform that predates JWT prevalence.
The session cookie (JSESSIONID) carries your authenticated state, and the
CSRF token (X-XSRF-TOKEN) prevents cross-site forgery for state-mutating
requests. Both must be present on every POST, PUT, PATCH, and DELETE call.

What can go wrong?
-------------------
- Missing CSRF token on a write request returns 403, not 401. This is the
  most common error in new integrations.
- The session expires after a period of inactivity. Build in re-authentication
  logic for long-running pipelines.
- Account lockout after repeated failed logins is enforced by the platform.
  Use environment variables — never embed credentials in code.

Prerequisites
--------------
    pip install requests

Environment variables
----------------------
    CASEFORGE_HOST      Base URL, e.g. https://your-instance.caseforge.io
    CASEFORGE_USER      Service account username
    CASEFORGE_PASS      Service account password
"""

import os
import requests

# ── Configuration ─────────────────────────────────────────────────────────────

BASE_URL = os.environ.get("CASEFORGE_HOST", "https://your-instance.caseforge.io")
USERNAME = os.environ.get("CASEFORGE_USER")
PASSWORD = os.environ.get("CASEFORGE_PASS")

if not USERNAME or not PASSWORD:
    raise EnvironmentError(
        "Set CASEFORGE_USER and CASEFORGE_PASS environment variables before running."
    )

# ── Authentication ─────────────────────────────────────────────────────────────


def authenticate() -> requests.Session:
    """Authenticate against CaseForge and return a live session.

    Uses requests.Session so cookies persist automatically across all
    subsequent calls in this session. The CSRF token is extracted from the
    response header and stored for later use on write operations.

    Returns:
        requests.Session: A session with JSESSIONID and X-XSRF-TOKEN set.

    Raises:
        requests.HTTPError: If the server returns 401 (bad credentials),
            403 (account locked), or 5xx (server-side fault).
        ValueError: If the CSRF token is absent from the response headers,
            which indicates a misconfigured server or wrong endpoint.
    """
    session = requests.Session()

    payload = {
        "username": USERNAME,
        "password": PASSWORD,
    }

    response = session.post(
        f"{BASE_URL}/api/auth/login",
        json=payload,
        timeout=15,
    )

    # Surface the HTTP status as an exception rather than silently continuing.
    # A 401 here means wrong credentials; a 403 means the account is locked.
    response.raise_for_status()

    # The CSRF token is returned in a response header, not the body. Extract
    # it and attach it to the session so every subsequent write request
    # carries it automatically.
    csrf_token = response.headers.get("X-XSRF-TOKEN")
    if not csrf_token:
        raise ValueError(
            "CSRF token missing from login response. "
            "Verify that BASE_URL points to the correct CaseForge instance."
        )

    session.headers.update({"X-XSRF-TOKEN": csrf_token})

    print("Authenticated successfully.")
    print(f"  Session cookie present: {bool(session.cookies.get('JSESSIONID'))}")
    print(f"  CSRF token: {csrf_token[:8]}...  (truncated for display)")

    return session


# ── End-to-end validation ──────────────────────────────────────────────────────


def validate_session(session: requests.Session) -> None:
    """Confirm the session is active by calling a low-cost read endpoint.

    Calls GET /api/auth/me, which returns the profile of the authenticated
    user. This serves as a health check: if it returns 200, your session
    cookie and CSRF token are both valid and correctly attached.

    Args:
        session: An authenticated requests.Session.

    Raises:
        requests.HTTPError: 401 means the session expired; re-authenticate.
    """
    response = session.get(f"{BASE_URL}/api/auth/me", timeout=10)
    response.raise_for_status()

    profile = response.json()
    print("\nSession validation passed.")
    print(f"  Logged in as : {profile.get('username')}")
    print(f"  Display name : {profile.get('displayName')}")
    print(f"  Role(s)      : {', '.join(profile.get('roles', []))}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    session = authenticate()
    validate_session(session)

    # From here, pass `session` into any other function that calls the API.
    # The session persists cookies and attaches the CSRF header on every
    # request, so you do not need to manage authentication state manually.
    print("\nReady. Pass `session` to any API function below.")
