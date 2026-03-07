package io.caseforge.samples;

import java.io.IOException;
import java.net.CookieManager;
import java.net.CookiePolicy;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * CaseForge API — Authentication Sample (Java)
 * ============================================
 *
 * <p>Demonstrates the CaseForge authentication flow using the Java {@link HttpClient}
 * introduced in JDK 11. The client is configured with a {@link CookieManager} so
 * that JSESSIONID is carried automatically on every subsequent request, matching
 * the behaviour of a browser or Python's {@code requests.Session}.
 *
 * <h2>Why session cookies?</h2>
 * <p>CaseForge uses a server-side session model, not bearer tokens. The session
 * cookie (JSESSIONID) carries your authenticated state, and the CSRF token
 * (X-XSRF-TOKEN) prevents cross-site request forgery on write operations.
 * Configuring the {@code HttpClient} with a {@code CookieManager} handles
 * JSESSIONID automatically; you must extract and forward the CSRF token manually.
 *
 * <h2>What can go wrong?</h2>
 * <ul>
 *   <li>HTTP 403 on a POST with no CSRF token — most common Java integration error.</li>
 *   <li>HTTP 401 on session expiry — the server issued a new session ID after
 *       the previous one timed out. Re-authenticate and retry.</li>
 *   <li>PKIX path building failure — your instance may use a private CA.
 *       Import the certificate into your JVM truststore before running.</li>
 * </ul>
 *
 * <h2>Prerequisites</h2>
 * <ul>
 *   <li>JDK 11 or later</li>
 *   <li>Optionally add {@code com.google.code.gson:gson} for JSON parsing</li>
 * </ul>
 *
 * <h2>Environment variables</h2>
 * <pre>
 *   CASEFORGE_HOST   Base URL, e.g. https://your-instance.caseforge.io
 *   CASEFORGE_USER   Service account username
 *   CASEFORGE_PASS   Service account password
 * </pre>
 */
public class AuthenticateExample {

    private static final String BASE_URL = System.getenv().getOrDefault(
            "CASEFORGE_HOST", "https://your-instance.caseforge.io");

    private static final String USERNAME = System.getenv("CASEFORGE_USER");
    private static final String PASSWORD = System.getenv("CASEFORGE_PASS");

    // ── Shared HTTP client ──────────────────────────────────────────────────────

    /**
     * A single {@link HttpClient} instance shared across all requests.
     *
     * <p>Configuring {@link CookiePolicy#ACCEPT_ALL} allows the client to store
     * and forward JSESSIONID automatically. Use {@code CookiePolicy.ACCEPT_ORIGINAL_SERVER}
     * in production to restrict cookie acceptance to the CaseForge domain only.
     */
    private static final HttpClient HTTP_CLIENT = HttpClient.newBuilder()
            .cookieHandler(new CookieManager(null, CookiePolicy.ACCEPT_ALL))
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    // ── Authentication ──────────────────────────────────────────────────────────

    /**
     * Authenticates against CaseForge and returns the CSRF token.
     *
     * <p>The {@link CookieManager} attached to {@link #HTTP_CLIENT} stores the
     * JSESSIONID from the Set-Cookie response header automatically. You only
     * need to capture and return the CSRF token — pass it in the
     * {@code X-XSRF-TOKEN} header on every subsequent write request.
     *
     * @return The CSRF token string.
     * @throws IOException          On I/O failure.
     * @throws InterruptedException If the thread is interrupted while waiting.
     * @throws RuntimeException     If credentials are missing, auth fails,
     *                              or the CSRF token is absent from headers.
     */
    public static String authenticate() throws IOException, InterruptedException {
        if (USERNAME == null || PASSWORD == null) {
            throw new RuntimeException(
                    "Set CASEFORGE_USER and CASEFORGE_PASS environment variables.");
        }

        // Build the login payload as a raw JSON string. In production, use a
        // JSON serialisation library (Gson, Jackson) to prevent injection from
        // user-supplied values.
        String loginPayload = String.format(
                "{\"username\":\"%s\",\"password\":\"%s\"}", USERNAME, PASSWORD);

        HttpRequest loginRequest = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/api/auth/login"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(loginPayload, StandardCharsets.UTF_8))
                .timeout(Duration.ofSeconds(15))
                .build();

        HttpResponse<String> response = HTTP_CLIENT.send(
                loginRequest, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            throw new RuntimeException(
                    "Login failed — HTTP " + response.statusCode() + ": " + response.body());
        }

        // Extract the CSRF token from the X-XSRF-TOKEN response header.
        Optional<String> csrfToken = response.headers().firstValue("X-XSRF-TOKEN");
        if (csrfToken.isEmpty()) {
            throw new RuntimeException(
                    "CSRF token missing from login response. Verify CASEFORGE_HOST.");
        }

        System.out.println("Authenticated successfully.");
        System.out.println("  CSRF token: " + csrfToken.get().substring(0, 8) + "...");

        return csrfToken.get();
    }

    // ── Session validation ──────────────────────────────────────────────────────

    /**
     * Validates the active session by calling {@code GET /api/auth/me}.
     *
     * <p>The JSESSIONID is sent automatically by the {@link CookieManager}.
     * A 200 response confirms the session is live and the cookie is valid.
     * A 401 means the session expired — call {@link #authenticate()} again.
     *
     * @param csrfToken The CSRF token returned by {@link #authenticate()}.
     * @throws IOException          On I/O failure.
     * @throws InterruptedException If the thread is interrupted.
     * @throws RuntimeException     If the session is invalid or the request fails.
     */
    public static void validateSession(String csrfToken)
            throws IOException, InterruptedException {

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/api/auth/me"))
                // GET requests do not require the CSRF token, but including it
                // is harmless and saves you from forgetting it on write requests.
                .header("X-XSRF-TOKEN", csrfToken)
                .GET()
                .timeout(Duration.ofSeconds(10))
                .build();

        HttpResponse<String> response = HTTP_CLIENT.send(
                request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 401) {
            throw new RuntimeException("Session expired. Re-authenticate and retry.");
        }
        if (response.statusCode() != 200) {
            throw new RuntimeException(
                    "Session validation failed — HTTP " + response.statusCode());
        }

        System.out.println("Session validation passed.");
        System.out.println("  Raw profile: " + response.body());
    }

    // ── Entry point ─────────────────────────────────────────────────────────────

    /**
     * Main method: authenticate, then validate the session.
     *
     * <p>After this runs, pass {@code csrfToken} and the shared
     * {@link #HTTP_CLIENT} (which carries JSESSIONID) into any method that
     * calls the CaseForge API.
     */
    public static void main(String[] args) throws IOException, InterruptedException {
        String csrfToken = authenticate();
        validateSession(csrfToken);
        System.out.println("\nReady. Use HTTP_CLIENT + csrfToken for further API calls.");
    }
}
