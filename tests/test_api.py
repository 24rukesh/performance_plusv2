"""Contract tests for the Performance Plus FastAPI service.

All 5 endpoints are covered:
  - GET  /api/health
  - POST /api/analyze
  - POST /api/webhook/crm
  - GET  /api/campaigns/{campaign_id}/actions

Tests use:
  - FastAPI TestClient (httpx-backed, no network required)
  - monkeypatch to zero-out DB calls (no live Postgres)
  - DEMO_MODE=1 + llm.client=None to use the fixture branch (no live gpt-4o)
"""
import os
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

VALID_PAYLOAD = {
    "web_sessions": [
        {
            "session_id": "s1",
            "campaign_id": "c1",
            "clicks": 100,
            "impressions": 1000,
            "cost_usd": 50.0,
            "conversion_rate": 0.1,
        }
    ],
    "crm_records": [
        {
            "session_id": "s1",
            "campaign_id": "c1",
            "lead_status": "Qualified",
            "projected_value": 5000.0,
            "sales_notes": "Strong interest, great fit",
        }
    ],
}

WEBHOOK_PAYLOAD = {
    "session_id": "s1",
    "campaign_id": "c1",
    "lead_status": "Qualified",
    "projected_value": 1000.0,
    "sales_notes": "good fit",
}


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------


def _make_client(monkeypatch, db_overrides=None):
    """Build a TestClient with all external dependencies patched out.

    Patches applied (in order):
      1. API_KEY env var (auth gate uses os.environ["API_KEY"])
      2. DEMO_MODE=1 so llm.run_analysis returns fixture, not gpt-4o
      3. llm.client = None forces the DEMO_MODE fixture branch in llm.py
      4. api.main.init_db = no-op (prevents real DB connection at lifespan startup)
      5. Any db_overrides are applied to the api.main namespace AFTER the import
         binding is in place (api/main.py does `from api.db import ...` creating
         local names, so patching the original api.db.* would have no effect).

    The app import is done INSIDE this helper (after patching) to ensure the
    patched environment is active when the module-level code executes.
    """
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setattr("llm.client", None)
    monkeypatch.setattr("api.main.init_db", lambda: None)
    if db_overrides:
        for name, mock in db_overrides.items():
            monkeypatch.setattr(f"api.main.{name}", mock)
    from api.main import app  # noqa: PLC0415 — intentional deferred import

    return TestClient(app)


# ---------------------------------------------------------------------------
# Health endpoint (API-05)
# ---------------------------------------------------------------------------


def test_health_returns_status_version_service(monkeypatch):
    """GET /api/health → 200 with exact response dict."""
    with _make_client(monkeypatch) as client:
        resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {
        "status": "ok",
        "version": "2.0.0",
        "service": "performance-plus-api",
    }


def test_health_no_auth_required(monkeypatch):
    """GET /api/health must succeed without X-API-Key header (D-12)."""
    with _make_client(monkeypatch) as client:
        resp = client.get("/api/health")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /api/analyze — auth gates (API-01)
# ---------------------------------------------------------------------------


def test_analyze_missing_api_key_returns_401(monkeypatch):
    """POST /api/analyze without X-API-Key → 401 with correct error detail."""
    with _make_client(monkeypatch) as client:
        resp = client.post("/api/analyze", json=VALID_PAYLOAD)
    assert resp.status_code == 401
    assert "Invalid or missing API key" in resp.json()["detail"]


def test_analyze_wrong_api_key_returns_401(monkeypatch):
    """POST /api/analyze with wrong key → 401."""
    with _make_client(monkeypatch) as client:
        resp = client.post(
            "/api/analyze",
            json=VALID_PAYLOAD,
            headers={"X-API-Key": "wrong-key"},
        )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /api/analyze — input validation (API-01)
# ---------------------------------------------------------------------------


def test_analyze_empty_arrays_returns_422(monkeypatch):
    """POST /api/analyze with empty lists → 422 mentioning 'non-empty'."""
    with _make_client(monkeypatch) as client:
        resp = client.post(
            "/api/analyze",
            json={"web_sessions": [], "crm_records": []},
            headers={"X-API-Key": "test-key"},
        )
    assert resp.status_code == 422
    assert "non-empty" in resp.json()["detail"]


def test_analyze_duplicate_crm_session_id_returns_422(monkeypatch):
    """POST /api/analyze with duplicate session_id in crm_records → 422."""
    payload = {
        "web_sessions": [
            {
                "session_id": "s1",
                "campaign_id": "c1",
                "clicks": 10,
                "impressions": 100,
                "cost_usd": 5.0,
                "conversion_rate": 0.1,
            },
            {
                "session_id": "s2",
                "campaign_id": "c1",
                "clicks": 20,
                "impressions": 200,
                "cost_usd": 10.0,
                "conversion_rate": 0.05,
            },
        ],
        "crm_records": [
            # Two rows sharing the same session_id triggers m:1 MergeError
            {
                "session_id": "s1",
                "campaign_id": "c1",
                "lead_status": "Qualified",
                "projected_value": 1000.0,
                "sales_notes": "first entry",
            },
            {
                "session_id": "s1",
                "campaign_id": "c1",
                "lead_status": "Contacted",
                "projected_value": 2000.0,
                "sales_notes": "duplicate entry",
            },
        ],
    }
    with _make_client(monkeypatch) as client:
        resp = client.post(
            "/api/analyze",
            json=payload,
            headers={"X-API-Key": "test-key"},
        )
    assert resp.status_code == 422
    assert "Duplicate session_id" in resp.json()["detail"]


def test_analyze_no_session_overlap_returns_422(monkeypatch):
    """POST /api/analyze with no common session_id → 422 mentioning 'No session_id overlap'."""
    payload = {
        "web_sessions": [
            {
                "session_id": "web_only",
                "campaign_id": "c1",
                "clicks": 10,
                "impressions": 100,
                "cost_usd": 5.0,
                "conversion_rate": 0.1,
            }
        ],
        "crm_records": [
            {
                "session_id": "crm_only",
                "campaign_id": "c1",
                "lead_status": "Qualified",
                "projected_value": 1000.0,
                "sales_notes": "disjoint session",
            }
        ],
    }
    with _make_client(monkeypatch) as client:
        resp = client.post(
            "/api/analyze",
            json=payload,
            headers={"X-API-Key": "test-key"},
        )
    assert resp.status_code == 422
    assert "No session_id overlap" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# /api/analyze — happy path (API-01)
# ---------------------------------------------------------------------------


def test_analyze_happy_path_returns_200_with_analysis_result(monkeypatch):
    """POST /api/analyze with valid matching sessions → 200 + AnalysisResult shape.

    DEMO_MODE=1 + llm.client=None forces fixture branch; no gpt-4o call is made.
    insert_analysis_result is mocked so no live Postgres is required.
    """
    mock_insert = MagicMock()
    with _make_client(monkeypatch, db_overrides={"insert_analysis_result": mock_insert}) as client:
        resp = client.post(
            "/api/analyze",
            json=VALID_PAYLOAD,
            headers={"X-API-Key": "test-key"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["executive_summary"], str)
    assert len(body["executive_summary"]) > 0
    assert isinstance(body["campaigns"], list)
    assert len(body["campaigns"]) > 0

    # Verify each campaign has the expected fields
    for campaign in body["campaigns"]:
        assert "campaign_id" in campaign
        assert "budget_action" in campaign
        assert "percentage_change" in campaign
        assert "semantic_reasoning" in campaign
        assert "confidence" in campaign
        assert "evidence_count" in campaign


# ---------------------------------------------------------------------------
# /api/analyze — DB persistence side-effects (API-02)
# ---------------------------------------------------------------------------


def test_analyze_persists_one_row_per_campaign_with_shared_run_id(monkeypatch):
    """insert_analysis_result is called once per campaign; all calls share a UUID run_id."""
    mock_insert = MagicMock()
    with _make_client(monkeypatch, db_overrides={"insert_analysis_result": mock_insert}) as client:
        resp = client.post(
            "/api/analyze",
            json=VALID_PAYLOAD,
            headers={"X-API-Key": "test-key"},
        )
    assert resp.status_code == 200
    campaigns = resp.json()["campaigns"]

    # One insert call per campaign
    assert mock_insert.call_count == len(campaigns)

    # All calls share the same run_id (2nd positional arg)
    run_ids = {call.args[1] for call in mock_insert.call_args_list}
    assert len(run_ids) == 1, "All inserts must share the same run_id"

    # run_id is a valid UUID string
    shared_run_id = run_ids.pop()
    uuid.UUID(shared_run_id)  # raises ValueError if not a valid UUID

    # The set of campaign_ids inserted matches the response
    inserted_campaign_ids = {call.args[0] for call in mock_insert.call_args_list}
    response_campaign_ids = {c["campaign_id"] for c in campaigns}
    assert inserted_campaign_ids == response_campaign_ids


# ---------------------------------------------------------------------------
# /api/webhook/crm — auth gate (API-03)
# ---------------------------------------------------------------------------


def test_webhook_missing_api_key_returns_401(monkeypatch):
    """POST /api/webhook/crm without X-API-Key → 401."""
    with _make_client(monkeypatch) as client:
        resp = client.post("/api/webhook/crm", json=WEBHOOK_PAYLOAD)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /api/webhook/crm — happy path (API-03)
# ---------------------------------------------------------------------------


def test_webhook_happy_path_returns_202_and_calls_insert_pending(monkeypatch):
    """POST /api/webhook/crm with valid body → 202 + {"status": "accepted"} + insert_pending_session called."""
    mock_insert_pending = MagicMock()
    with _make_client(
        monkeypatch, db_overrides={"insert_pending_session": mock_insert_pending}
    ) as client:
        resp = client.post(
            "/api/webhook/crm",
            json=WEBHOOK_PAYLOAD,
            headers={"X-API-Key": "test-key"},
        )
    assert resp.status_code == 202
    assert resp.json() == {"status": "accepted"}

    # insert_pending_session called exactly once with correct field values
    mock_insert_pending.assert_called_once()
    record = mock_insert_pending.call_args.args[0]
    assert record.session_id == WEBHOOK_PAYLOAD["session_id"]
    assert record.campaign_id == WEBHOOK_PAYLOAD["campaign_id"]
    assert record.lead_status == WEBHOOK_PAYLOAD["lead_status"]
    assert record.projected_value == WEBHOOK_PAYLOAD["projected_value"]
    assert record.sales_notes == WEBHOOK_PAYLOAD["sales_notes"]


# ---------------------------------------------------------------------------
# /api/campaigns/{campaign_id}/actions — auth gate (API-04)
# ---------------------------------------------------------------------------


def test_campaigns_actions_missing_api_key_returns_401(monkeypatch):
    """GET /api/campaigns/cmp_test/actions without X-API-Key → 401."""
    with _make_client(monkeypatch) as client:
        resp = client.get("/api/campaigns/cmp_test/actions")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /api/campaigns/{campaign_id}/actions — not-found path (API-04)
# ---------------------------------------------------------------------------


def test_campaigns_actions_returns_404_when_no_results(monkeypatch):
    """GET /api/campaigns/{id}/actions → 404 when get_latest_result returns None."""
    mock_get = MagicMock(return_value=None)
    with _make_client(monkeypatch, db_overrides={"get_latest_result": mock_get}) as client:
        resp = client.get(
            "/api/campaigns/cmp_test/actions",
            headers={"X-API-Key": "test-key"},
        )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /api/campaigns/{campaign_id}/actions — happy path (API-04)
# ---------------------------------------------------------------------------


def test_campaigns_actions_returns_latest_result_dict(monkeypatch):
    """GET /api/campaigns/{id}/actions → 200 + exact dict when get_latest_result returns data."""
    sample_result = {
        "executive_summary": "Scale winner campaigns.",
        "campaigns": [
            {
                "campaign_id": "cmp_test",
                "budget_action": "increase",
                "percentage_change": 25,
                "semantic_reasoning": "Strong positive signals from sales reps.",
                "confidence": 0.9,
                "evidence_count": 5,
            }
        ],
    }
    mock_get = MagicMock(return_value=sample_result)
    with _make_client(monkeypatch, db_overrides={"get_latest_result": mock_get}) as client:
        resp = client.get(
            "/api/campaigns/cmp_test/actions",
            headers={"X-API-Key": "test-key"},
        )
    assert resp.status_code == 200
    assert resp.json() == sample_result

    # Verify get_latest_result was called with the correct campaign_id
    mock_get.assert_called_once_with("cmp_test")


# ---------------------------------------------------------------------------
# POST /api/waitlist — four behavioral contracts (WAIT-01, WAIT-02, WAIT-03)
# ---------------------------------------------------------------------------


def test_waitlist_valid_email_returns_200(monkeypatch):
    """POST /api/waitlist with valid email → 200 + confirmation message (WAIT-01, WAIT-02)."""
    mock_insert = MagicMock(return_value="2026-06-01T10:00:00+00:00")
    mock_smtp = MagicMock()
    with _make_client(monkeypatch, db_overrides={
        "insert_waitlist_email": mock_insert,
        "send_waitlist_notification": mock_smtp,
    }) as client:
        resp = client.post("/api/waitlist", json={"email": "user@example.com"})
    assert resp.status_code == 200
    assert resp.json() == {"message": "You're on the waitlist! We'll be in touch."}
    mock_insert.assert_called_once_with("user@example.com")
    mock_smtp.assert_called_once_with("user@example.com", "2026-06-01T10:00:00+00:00")


def test_waitlist_invalid_email_returns_422(monkeypatch):
    """POST /api/waitlist with malformed email → 422 (Pydantic EmailStr validation)."""
    with _make_client(monkeypatch) as client:
        resp = client.post("/api/waitlist", json={"email": "not-an-email"})
    assert resp.status_code == 422


def test_waitlist_duplicate_email_returns_409(monkeypatch):
    """POST /api/waitlist with already-registered email → 409 with detail message (WAIT-02)."""
    from fastapi import HTTPException
    mock_insert = MagicMock(side_effect=HTTPException(status_code=409, detail="You're already on the waitlist."))
    with _make_client(monkeypatch, db_overrides={"insert_waitlist_email": mock_insert}) as client:
        resp = client.post("/api/waitlist", json={"email": "dup@example.com"})
    assert resp.status_code == 409
    assert resp.json() == {"detail": "You're already on the waitlist."}


def test_waitlist_smtp_failure_returns_500(monkeypatch):
    """POST /api/waitlist when SMTP raises → 500 with detail starting 'SMTP error:' (WAIT-03)."""
    mock_insert = MagicMock(return_value="2026-06-01T10:00:00+00:00")
    mock_smtp = MagicMock(side_effect=Exception("SMTP connection refused"))
    with _make_client(monkeypatch, db_overrides={
        "insert_waitlist_email": mock_insert,
        "send_waitlist_notification": mock_smtp,
    }) as client:
        resp = client.post("/api/waitlist", json={"email": "user@example.com"})
    assert resp.status_code == 500
    assert "SMTP error:" in resp.json()["detail"]
