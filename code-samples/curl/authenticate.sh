#!/usr/bin/env bash
# CaseForge API — Authentication & Validation (cURL)
# ===================================================
#
# This script demonstrates the CaseForge authentication flow, CSRF token
# extraction, and session validation using nothing but cURL and standard
# shell utilities (grep, awk, sed).
#
# Why two separate steps instead of one call?
# --------------------------------------------
# CaseForge requires both a session cookie (JSESSIONID) and a CSRF token
# (X-XSRF-TOKEN) on every write request. The login call returns both, but
# they're in different places — the cookie in the Set-Cookie header and the
# CSRF token in a dedicated response header. You must capture both before
# making any POST, PUT, PATCH, or DELETE request.
#
# What can go wrong?
# -------------------
#   HTTP 403 on a subsequent POST  →  CSRF token is missing or stale.
#   HTTP 401 on a subsequent call  →  Session cookie is missing or expired.
#   "curl: (60) SSL..."            →  Private CA certificate not trusted.
#                                     Add: --cacert /path/to/ca-bundle.pem
#   Empty CSRF_TOKEN or COOKIE     →  Wrong BASE_URL, or server returned an
#                                     error body instead of headers.
#
# Usage
# ------
#   export CASEFORGE_HOST="https://your-instance.caseforge.io"
#   export CASEFORGE_USER="service.account"
#   export CASEFORGE_PASS="s3cr3tP@ssw0rd"
#   chmod +x authenticate.sh
#   ./authenticate.sh

set -euo pipefail

: "${CASEFORGE_HOST:?Set CASEFORGE_HOST before running this script}"
: "${CASEFORGE_USER:?Set CASEFORGE_USER before running this script}"
: "${CASEFORGE_PASS:?Set CASEFORGE_PASS before running this script}"

COOKIE_JAR="$(mktemp /tmp/caseforge-cookies-XXXXXX)"
RESPONSE_HEADERS="$(mktemp /tmp/caseforge-headers-XXXXXX)"

# Clean up temporary files on exit — even if the script fails partway through.
trap 'rm -f "$COOKIE_JAR" "$RESPONSE_HEADERS"' EXIT

echo "Authenticating against $CASEFORGE_HOST ..."

# ── Step 1: Login ────────────────────────────────────────────────────────────
#
# --cookie-jar    Writes JSESSIONID (and any other cookies) to a temp file.
# --dump-header   Writes all response headers to a temp file for parsing.
# --silent        Suppresses the progress meter — keeps output readable.
# --fail-with-body Returns a non-zero exit code on 4xx/5xx AND prints the body.
#
LOGIN_HTTP_CODE=$(curl \
  --silent \
  --fail-with-body \
  --cookie-jar "$COOKIE_JAR" \
  --dump-header "$RESPONSE_HEADERS" \
  --header "Content-Type: application/json" \
  --data "{\"username\":\"$CASEFORGE_USER\",\"password\":\"$CASEFORGE_PASS\"}" \
  --output /dev/null \
  --write-out "%{http_code}" \
  "$CASEFORGE_HOST/api/auth/login")

if [ "$LOGIN_HTTP_CODE" != "200" ]; then
  echo "ERROR: Login returned HTTP $LOGIN_HTTP_CODE."
  echo "  401 = wrong credentials"
  echo "  403 = account locked or insufficient permissions"
  echo "  429 = rate limited — wait and retry"
  exit 1
fi

# ── Step 2: Extract the CSRF token ───────────────────────────────────────────
#
# The CSRF token is returned in the X-XSRF-TOKEN response header (not the body).
# The header name may be sent with any casing; use case-insensitive grep.
#
CSRF_TOKEN=$(grep -i "^x-xsrf-token:" "$RESPONSE_HEADERS" \
  | awk '{print $2}' \
  | tr -d '\r\n')

if [ -z "$CSRF_TOKEN" ]; then
  echo "ERROR: CSRF token not found in response headers."
  echo "Check that CASEFORGE_HOST points to a valid CaseForge instance."
  exit 1
fi

echo "Authenticated successfully."
echo "  CSRF token : ${CSRF_TOKEN:0:8}...  (truncated)"

# ── Step 3: Validate session ──────────────────────────────────────────────────
#
# GET /api/auth/me confirms the session is active using only the cookie.
# The CSRF token is not required on GET requests, but including it is harmless
# and confirms the complete header configuration before making write requests.
#
echo ""
echo "Validating session against GET /api/auth/me ..."

VALIDATE_HTTP_CODE=$(curl \
  --silent \
  --fail-with-body \
  --cookie "$COOKIE_JAR" \
  --header "X-XSRF-TOKEN: $CSRF_TOKEN" \
  --write-out "%{http_code}" \
  --output /tmp/caseforge-profile.json \
  "$CASEFORGE_HOST/api/auth/me")

if [ "$VALIDATE_HTTP_CODE" = "401" ]; then
  echo "ERROR: Session is not valid. The login may have succeeded but the"
  echo "  session cookie was not returned. Check your CaseForge instance logs."
  exit 1
elif [ "$VALIDATE_HTTP_CODE" != "200" ]; then
  echo "ERROR: Session validation returned HTTP $VALIDATE_HTTP_CODE."
  exit 1
fi

echo "Session validation passed."
echo "  Profile: $(cat /tmp/caseforge-profile.json)"
rm -f /tmp/caseforge-profile.json

# ── Step 4: Example write request ─────────────────────────────────────────────
#
# Every POST, PUT, PATCH, or DELETE must include:
#   --cookie "$COOKIE_JAR"          — session identity
#   --header "X-XSRF-TOKEN: ..."    — CSRF guard
#
# Removing either one from a write request returns 403.
#
echo ""
echo "Ready. For write requests, always include:"
echo "  --cookie \"$COOKIE_JAR\""
echo "  --header \"X-XSRF-TOKEN: $CSRF_TOKEN\""
echo ""
echo "Example — create a SAR case:"
echo ""
echo "  curl \\"
echo "    --silent --fail-with-body \\"
echo "    --cookie \"$COOKIE_JAR\" \\"
echo "    --header \"Content-Type: application/json\" \\"
echo "    --header \"X-XSRF-TOKEN: $CSRF_TOKEN\" \\"
echo "    --data '{\"workItemType\":\"SAR\",\"title\":\"Suspicious activity — ref DEMO-001\",\"priority\":\"HIGH\"}' \\"
echo "    \"$CASEFORGE_HOST/api/workItems\""
