using System;
using System.Net;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace CaseForge.Samples
{
    /// <summary>
    /// CaseForge API — Authentication Sample (C# / .NET 6+)
    /// =======================================================
    ///
    /// <para>
    /// Authenticates against the CaseForge API using <see cref="HttpClient"/> and
    /// a <see cref="CookieContainer"/> so JSESSIONID is carried automatically on
    /// every subsequent request. The CSRF token is extracted from the response
    /// header and attached to a shared <see cref="HttpClient"/> default header,
    /// removing the need to pass it individually to each call.
    /// </para>
    ///
    /// <para><strong>Why session cookies?</strong><br/>
    /// CaseForge uses server-managed sessions — JSESSIONID holds your authenticated
    /// state, and X-XSRF-TOKEN guards against cross-site request forgery on
    /// write operations.  A <see cref="HttpClientHandler"/> with a
    /// <see cref="CookieContainer"/> replicates the browser cookie model in
    /// server-side .NET code.
    /// </para>
    ///
    /// <para><strong>What can go wrong?</strong></para>
    /// <list type="bullet">
    ///   <item>HTTP 403 on a POST — CSRF token is missing or stale. Re-authenticate.</item>
    ///   <item>HTTP 401 on a subsequent call — session expired. Re-authenticate.</item>
    ///   <item>SSL handshake failure — for self-signed certs in dev, use
    ///         <c>ServerCertificateCustomValidationCallback</c> only in development;
    ///         never disable certificate validation in production.</item>
    /// </list>
    ///
    /// <para><strong>Prerequisites:</strong> .NET 6 or later (no extra packages required)</para>
    ///
    /// <para><strong>Environment variables:</strong><br/>
    /// <c>CASEFORGE_HOST</c>: Base URL, e.g., https://your-instance.caseforge.io<br/>
    /// <c>CASEFORGE_USER</c>: Service account username<br/>
    /// <c>CASEFORGE_PASS</c>: Service account password
    /// </para>
    /// </summary>
    public class AuthenticateExample
    {
        private static readonly string BaseUrl =
            Environment.GetEnvironmentVariable("CASEFORGE_HOST")
            ?? "https://your-instance.caseforge.io";

        private static readonly string? Username =
            Environment.GetEnvironmentVariable("CASEFORGE_USER");

        private static readonly string? Password =
            Environment.GetEnvironmentVariable("CASEFORGE_PASS");

        // ── Shared HTTP client ────────────────────────────────────────────────────

        /// <summary>
        /// The <see cref="HttpClient"/> used for all API calls.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <see cref="HttpClient"/> is designed to be instantiated once and
        /// reused across the application lifetime. Creating a new instance per
        /// request exhausts socket connections under load (socket exhaustion).
        /// </para>
        /// <para>
        /// The <see cref="CookieContainer"/> stores JSESSIONID after login
        /// and attaches it automatically to every subsequent request — the same
        /// behaviour as a browser session.
        /// </para>
        /// </remarks>
        private static readonly CookieContainer CookieJar = new();

        private static readonly HttpClient Client = new(
            new HttpClientHandler { CookieContainer = CookieJar })
        {
            BaseAddress = new Uri(BaseUrl),
            Timeout = TimeSpan.FromSeconds(30),
        };

        // ── Authentication ────────────────────────────────────────────────────────

        /// <summary>
        /// Authenticates against CaseForge and sets the CSRF token on the
        /// shared <see cref="Client"/> default headers.
        /// </summary>
        /// <returns>
        /// The CSRF token extracted from the login response header.
        /// </returns>
        /// <exception cref="InvalidOperationException">
        /// Thrown when environment variables are missing or CSRF token is absent.
        /// </exception>
        /// <exception cref="HttpRequestException">
        /// Thrown when HTTP 401 (bad credentials), 403 (locked), or 5xx occurs.
        /// </exception>
        public static async Task<string> AuthenticateAsync()
        {
            if (string.IsNullOrEmpty(Username) || string.IsNullOrEmpty(Password))
            {
                throw new InvalidOperationException(
                    "Set CASEFORGE_USER and CASEFORGE_PASS environment variables.");
            }

            var payload = new { username = Username, password = Password };

            // Serialize with System.Text.Json rather than building raw JSON strings.
            // This prevents injection if credentials ever come from user input.
            var content = JsonContent.Create(payload);

            HttpResponseMessage response = await Client.PostAsync("/api/auth/login", content);

            // EnsureSuccessStatusCode throws HttpRequestException on 4xx/5xx.
            // The exception message includes the status code and reason phrase.
            response.EnsureSuccessStatusCode();

            // Extract the CSRF token from the response header.
            // The CookieContainer handles JSESSIONID automatically from Set-Cookie.
            if (!response.Headers.TryGetValues("X-XSRF-TOKEN", out var values))
            {
                throw new InvalidOperationException(
                    "CSRF token missing from login response. Verify CASEFORGE_HOST.");
            }

            string csrfToken = string.Join("", values);

            // Attach the CSRF token to every subsequent request via default headers.
            // This means you do not need to set it individually on each call.
            Client.DefaultRequestHeaders.Remove("X-XSRF-TOKEN");
            Client.DefaultRequestHeaders.Add("X-XSRF-TOKEN", csrfToken);

            Console.WriteLine("Authenticated successfully.");
            Console.WriteLine($"  CSRF token: {csrfToken[..Math.Min(8, csrfToken.Length)]}...");

            return csrfToken;
        }

        // ── Session validation ────────────────────────────────────────────────────

        /// <summary>
        /// Validates the active session by calling <c>GET /api/auth/me</c>.
        /// </summary>
        /// <remarks>
        /// <para>
        /// JSESSIONID is sent automatically by <see cref="CookieJar"/>.
        /// A 200 response confirms the session is active; 401 means it expired.
        /// </para>
        /// </remarks>
        /// <exception cref="HttpRequestException">
        /// Thrown on non-2xx responses.
        /// </exception>
        public static async Task ValidateSessionAsync()
        {
            HttpResponseMessage response = await Client.GetAsync("/api/auth/me");

            if (response.StatusCode == HttpStatusCode.Unauthorized)
            {
                throw new InvalidOperationException(
                    "Session expired. Call AuthenticateAsync() again to refresh.");
            }

            response.EnsureSuccessStatusCode();

            // Deserialize into a dynamic JSON document — avoids a concrete
            // model class for this sample. Use a typed DTO in production code.
            using JsonDocument profile = JsonDocument.Parse(
                await response.Content.ReadAsStringAsync());

            JsonElement root = profile.RootElement;

            Console.WriteLine("Session validation passed.");
            Console.WriteLine($"  Logged in as : {root.GetProperty("username").GetString()}");
            Console.WriteLine($"  Display name : {root.GetProperty("displayName").GetString()}");
        }

        // ── Entry point ───────────────────────────────────────────────────────────

        public static async Task Main(string[] args)
        {
            await AuthenticateAsync();
            await ValidateSessionAsync();

            Console.WriteLine("\nReady. Use the shared Client for further API calls.");
        }
    }
}
