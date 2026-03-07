/**
 * CaseForge API — Work Items Sample (JavaScript / Node.js)
 * =========================================================
 *
 * Demonstrates creating and retrieving a SAR case using the CaseForge
 * Work Items API. Requires an authenticated session from authenticate.js.
 *
 * @module work-items
 */

const { authenticate, apiFetch } = require('./authenticate');

const BASE_URL = process.env.CASEFORGE_HOST ?? 'https://your-instance.caseforge.io';

// ── Create a work item ─────────────────────────────────────────────────────────

/**
 * Creates a SAR case from an upstream detection alert.
 *
 * The Work Items API is the bridge between your detection or transaction
 * monitoring system and CaseForge's analyst workspace. An alert in your
 * system maps to a case in CaseForge — the externalReference field is
 * the join key that lets both systems stay in sync.
 *
 * @param {{ cookieHeader: string, csrfToken: string }} auth  Session state.
 * @param {string} alertRef  External alert ID from your detection system.
 * @returns {Promise<object>}  New case record with id, caseNumber, status.
 *
 * @throws {Error} 422 — required custom fields are missing for your tenant.
 * @throws {Error} 409 — a case with this externalReference already exists.
 */
async function createSarCase(auth, alertRef) {
  const payload = {
    workItemType: 'SAR',          // Verify via GET /api/config/workItemTypes
    title: `Suspicious activity — ref ${alertRef}`,
    priority: 'HIGH',
    externalReference: alertRef,
    customFields: {
      // Replace these keys with field IDs from your tenant configuration.
      cf_detection_source: 'transaction-monitoring',
      cf_risk_score: '87',
    },
  };

  const response = await apiFetch(`${BASE_URL}/api/workItems`, auth, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      `Failed to create case — HTTP ${response.status}: ${JSON.stringify(error)}`
    );
  }

  const caseRecord = await response.json();
  console.log(`Case created: ${caseRecord.caseNumber}  (id=${caseRecord.id})`);
  return caseRecord;
}

// ── Retrieve a work item ───────────────────────────────────────────────────────

/**
 * Retrieves a full case record by its internal ID.
 *
 * Call this after creation to confirm persistence, or before a status
 * transition to read the current state and validate required fields.
 *
 * @param {{ cookieHeader: string, csrfToken: string }} auth
 * @param {string} caseId  Internal case ID from the create response.
 * @returns {Promise<object>}  Full case record.
 *
 * @throws {Error} 404 — case not found or insufficient read permissions.
 */
async function getCase(auth, caseId) {
  const response = await apiFetch(`${BASE_URL}/api/workItems/${caseId}`, auth);

  if (!response.ok) {
    throw new Error(`Failed to retrieve case ${caseId} — HTTP ${response.status}`);
  }

  return response.json();
}

// ── End-to-end validation ──────────────────────────────────────────────────────

/**
 * Creates a case and immediately reads it back to confirm correct persistence.
 *
 * Run this as a smoke test after any configuration change or environment
 * migration to confirm the Work Items API is functioning end to end.
 *
 * @param {{ cookieHeader: string, csrfToken: string }} auth
 */
async function validateCaseLifecycle(auth) {
  console.log('\n── Case lifecycle validation ──────────────────────────────────────');

  // Step 1: Create
  const created = await createSarCase(auth, 'DEMO-ALERT-001');

  // Step 2: Read back and assert field integrity
  const fetched = await getCase(auth, created.id);

  if (fetched.externalReference !== 'DEMO-ALERT-001') {
    throw new Error(
      `externalReference mismatch — got "${fetched.externalReference}", expected "DEMO-ALERT-001".`
    );
  }
  if (fetched.status !== 'UNASSIGNED') {
    throw new Error(
      `Unexpected status "${fetched.status}" on new case — expected "UNASSIGNED".`
    );
  }

  console.log('Read-back confirmed: externalReference and status are correct.');
  console.log('\nValidation complete. Case lifecycle is functioning correctly.');
}

// ── Entry point ────────────────────────────────────────────────────────────────

(async () => {
  const auth = await authenticate();
  await validateCaseLifecycle(auth);
})().catch(err => {
  console.error(err.message);
  process.exit(1);
});
