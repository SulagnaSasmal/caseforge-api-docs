/**
 * CaseForge API — Authentication Sample (JavaScript / Node.js)
 * =============================================================
 *
 * This sample covers the authentication flow for the CaseForge API using
 * the Node.js built-in `fetch` API (Node 18+). For earlier versions, install
 * `node-fetch` and import it instead.
 *
 * Why session cookies instead of bearer tokens?
 * -----------------------------------------------
 * CaseForge's session model predates widespread JWT adoption. The platform
 * uses JSESSIONID (server-managed session) + X-XSRF-TOKEN (CSRF guard).
 * In Node.js, you must track and forward the Set-Cookie header manually
 * because the built-in `fetch` does not persist cookies across calls the
 * way a browser or Python's requests.Session does.
 *
 * What can go wrong?
 * -------------------
 * - Forgetting X-XSRF-TOKEN on a POST returns 403. This is the single
 *   most common error in JavaScript integrations.
 * - Node.js fetch does not follow redirects for POST requests by default.
 *   If your instance has a login redirect, set redirect: 'follow'.
 * - The session cookie is HttpOnly on production instances. You cannot
 *   read it from document.cookie in a browser context — only from the
 *   Set-Cookie response header in server-side code.
 *
 * Prerequisites
 * --------------
 *   Node.js >= 18 (built-in fetch)
 *   -- or --
 *   npm install node-fetch  (for Node < 18)
 *
 * Environment variables
 * ----------------------
 *   CASEFORGE_HOST   Base URL, e.g. https://your-instance.caseforge.io
 *   CASEFORGE_USER   Service account username
 *   CASEFORGE_PASS   Service account password
 */

const BASE_URL = process.env.CASEFORGE_HOST ?? 'https://your-instance.caseforge.io';
const USERNAME  = process.env.CASEFORGE_USER;
const PASSWORD  = process.env.CASEFORGE_PASS;

if (!USERNAME || !PASSWORD) {
  console.error('Set CASEFORGE_USER and CASEFORGE_PASS before running.');
  process.exit(1);
}

// ── Authentication ────────────────────────────────────────────────────────────

/**
 * Authenticates against CaseForge and returns the session state needed for
 * subsequent API calls.
 *
 * @returns {{ cookieHeader: string, csrfToken: string }} Session credentials.
 *
 * Unlike Python's requests.Session, Node.js fetch does not carry cookies
 * automatically. This function returns the raw cookie string and CSRF token
 * separately — pass them both into every subsequent request via the helper
 * functions below.
 */
async function authenticate() {
  const response = await fetch(`${BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: USERNAME, password: PASSWORD }),
  });

  if (!response.ok) {
    // 401 = wrong credentials; 403 = account locked; 429 = rate limited.
    // The response body usually contains a machine-readable error code.
    const error = await response.json().catch(() => ({}));
    throw new Error(
      `Login failed — HTTP ${response.status}: ${error.message ?? response.statusText}`
    );
  }

  // Extract the session cookie from the Set-Cookie header.
  // In a browser, the browser engine handles this automatically.
  // In Node.js server-side code, you forward it on each subsequent request.
  const setCookieHeader = response.headers.get('set-cookie');
  if (!setCookieHeader) {
    throw new Error('No Set-Cookie header in login response. Check BASE_URL.');
  }

  // Extract JSESSIONID specifically — discard other cookie attributes
  // (Path, SameSite, HttpOnly) because fetch will not accept them.
  const cookieHeader = setCookieHeader
    .split(';')
    .filter(part => part.trim().startsWith('JSESSIONID'))
    .join('; ')
    || setCookieHeader.split(';')[0];

  // CSRF token is returned as a response header — not in the body.
  const csrfToken = response.headers.get('X-XSRF-TOKEN');
  if (!csrfToken) {
    throw new Error('CSRF token missing from login response. Verify your CaseForge instance.');
  }

  console.log('Authenticated successfully.');
  console.log(`  Cookie present : ${cookieHeader.includes('JSESSIONID')}`);
  console.log(`  CSRF token     : ${csrfToken.slice(0, 8)}...`);

  return { cookieHeader, csrfToken };
}

// ── Request helper ────────────────────────────────────────────────────────────

/**
 * Wraps fetch with the correct authentication headers for CaseForge.
 *
 * All requests to CaseForge must carry:
 *   - Cookie: JSESSIONID=<token>   (proves you have an active session)
 *   - X-XSRF-TOKEN: <token>        (required on all non-GET requests)
 *
 * @param {string} url           Full endpoint URL.
 * @param {{ cookieHeader: string, csrfToken: string }} auth  Session state.
 * @param {RequestInit} [options]  Standard fetch options (method, body, etc.).
 * @returns {Promise<Response>}
 */
async function apiFetch(url, auth, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'Cookie': auth.cookieHeader,
    'X-XSRF-TOKEN': auth.csrfToken,
    ...options.headers,
  };

  return fetch(url, { ...options, headers });
}

// ── End-to-end validation ──────────────────────────────────────────────────────

/**
 * Validates the session by calling GET /api/auth/me.
 *
 * If this succeeds, your JSESSIONID and CSRF token are both correctly
 * attached and the session is active. If it returns 401, the session
 * expired — call authenticate() again and retry.
 *
 * @param {{ cookieHeader: string, csrfToken: string }} auth
 */
async function validateSession(auth) {
  const response = await apiFetch(`${BASE_URL}/api/auth/me`, auth);

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session is not valid. Re-authenticate and retry.');
    }
    throw new Error(`Session validation failed — HTTP ${response.status}`);
  }

  const profile = await response.json();
  console.log('\nSession validation passed.');
  console.log(`  Logged in as : ${profile.username}`);
  console.log(`  Display name : ${profile.displayName}`);
  console.log(`  Role(s)      : ${(profile.roles ?? []).join(', ')}`);
}

// ── Entry point ────────────────────────────────────────────────────────────────

(async () => {
  const auth = await authenticate();
  await validateSession(auth);

  // Pass `auth` into any function that calls the API.
  console.log('\nReady. Pass `auth` to any API function below.');
})().catch(err => {
  console.error(err.message);
  process.exit(1);
});
