"""
CaseForge API — Work Items Sample (Python)
==========================================

This sample demonstrates creating, retrieving, and updating a SAR (Suspicious
Activity Report) case via the CaseForge Work Items API.

Why does the Work Items API exist?
------------------------------------
CaseForge is a case management platform for financial crime compliance teams.
The Work Items API is the primary integration path for systems that need to:

  - Push alerts from a detection engine into CaseForge for analyst review
  - Read case decisions back into an analytics pipeline
  - Automate status transitions as evidence is gathered

This is not a "nice to have" API bolt-on. For AML/KYC operations, the audit
trail of case creation, assignment, and disposition is a regulatory requirement
under FINCEN SAR filing rules and internal model governance frameworks.

What can go wrong?
-------------------
- Creating a case without required custom fields returns 422, not 400. Check
  the configuration for your tenant's mandatory field schema before posting.
- The `workItemType` enum is tenant-configured. Do not hardcode "SAR" or
  "Alert" without confirming the exact string from GET /api/config/workItemTypes.
- Transitioning a case to CLOSED without all mandatory fields populated
  will return 409 (Conflict). The error body will list the blocking fields.

Prerequisites
--------------
    pip install requests
    Authenticated session from authenticate.py

Environment variables
----------------------
    CASEFORGE_HOST      Base URL
    CASEFORGE_USER      Service account username
    CASEFORGE_PASS      Service account password
"""

import os
import json
import requests

from authenticate import authenticate  # See authenticate.py

BASE_URL = os.environ.get("CASEFORGE_HOST", "https://your-instance.caseforge.io")


# ── Create a work item ─────────────────────────────────────────────────────────


def create_sar_case(session: requests.Session, alert_ref: str) -> dict:
    """Create a new SAR case from an upstream alert reference.

    A SAR case is the container record that analysts populate as they
    investigate suspicious activity. Creating it from code is the normal
    integration path when your detection engine lives outside CaseForge.

    Args:
        session:   An authenticated requests.Session (from authenticate.py).
        alert_ref: The upstream alert ID from your detection system. Stored
                   as an external reference so the case can be correlated back.

    Returns:
        dict: The new case record, including `id`, `caseNumber`, and `status`.

    Raises:
        requests.HTTPError: 422 if required tenant fields are missing;
            409 if a case for this alert_ref already exists (duplicate check).
    """
    payload = {
        "workItemType": "SAR",           # Confirm this value from GET /api/config/workItemTypes
        "title": f"Suspicious activity — ref {alert_ref}",
        "priority": "HIGH",
        "externalReference": alert_ref,
        "customFields": {
            # customFields are tenant-specific. Replace these keys with the
            # field IDs from your CaseForge instance configuration.
            "cf_detection_source": "transaction-monitoring",
            "cf_risk_score": "87",
        },
    }

    response = session.post(
        f"{BASE_URL}/api/workItems",
        json=payload,
        timeout=15,
    )
    response.raise_for_status()

    case = response.json()
    print(f"Case created: {case['caseNumber']}  (id={case['id']})")
    return case


# ── Read a work item ───────────────────────────────────────────────────────────


def get_case(session: requests.Session, case_id: str) -> dict:
    """Retrieve a full case record by ID.

    Use this after creation to confirm the record is persisted correctly, or
    to read the current state before submitting a status transition.

    Args:
        session:  An authenticated requests.Session.
        case_id:  The numeric case ID returned by the create call.

    Returns:
        dict: Full case record including status, assignee, and customFields.

    Raises:
        requests.HTTPError: 404 if the case does not exist or your account
            does not have read permission for this case type.
    """
    response = session.get(f"{BASE_URL}/api/workItems/{case_id}", timeout=10)
    response.raise_for_status()
    return response.json()


# ── Transition a work item ─────────────────────────────────────────────────────


def assign_case(session: requests.Session, case_id: str, analyst_username: str) -> dict:
    """Assign a case to an analyst.

    Assignment changes the case status from UNASSIGNED to IN_REVIEW, which
    starts the SLA clock for your compliance team. If the analyst account is
    inactive or lacks the required license, the server returns 403 with a
    detailed permission error in the body.

    Args:
        session:          An authenticated requests.Session.
        case_id:          The case to assign.
        analyst_username: The CaseForge username of the analyst to assign to.

    Returns:
        dict: Updated case record confirming new status and assignee.

    Raises:
        requests.HTTPError: 403 if the analyst lacks the required license tier.
            409 if the case is already closed and cannot be reassigned.
    """
    payload = {
        "assignee": analyst_username,
    }

    response = session.patch(
        f"{BASE_URL}/api/workItems/{case_id}/assign",
        json=payload,
        timeout=10,
    )
    response.raise_for_status()

    updated = response.json()
    print(f"Case {updated['caseNumber']} assigned to {updated['assignee']}  "
          f"(status={updated['status']})")
    return updated


# ── End-to-end validation ──────────────────────────────────────────────────────


def validate_case_lifecycle(session: requests.Session) -> None:
    """Run a create → read → assign lifecycle to confirm integration health.

    Useful as a smoke test after deploying a new environment or rotating
    service account credentials.
    """
    print("\n── End-to-end case lifecycle validation ──────────────────────────────")

    # Step 1: Create
    case = create_sar_case(session, alert_ref="DEMO-ALERT-001")
    case_id = case["id"]

    # Step 2: Read back and confirm fields
    fetched = get_case(session, case_id)
    assert fetched["externalReference"] == "DEMO-ALERT-001", (
        "externalReference mismatch — check payload mapping."
    )
    assert fetched["status"] == "UNASSIGNED", (
        f"Expected UNASSIGNED on creation, got {fetched['status']}."
    )
    print("Read-back confirmed: externalReference and status are correct.")

    # Step 3: Assign — replace 'demo.analyst' with a real username
    assigned = assign_case(session, case_id, analyst_username="demo.analyst")
    assert assigned["status"] == "IN_REVIEW", (
        f"Expected IN_REVIEW after assignment, got {assigned['status']}."
    )
    print("Assignment confirmed: status transitioned to IN_REVIEW.")

    print("\nValidation complete. Case lifecycle is functioning correctly.")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    session = authenticate()
    validate_case_lifecycle(session)
