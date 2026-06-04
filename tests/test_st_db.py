"""Unit tests for st_db.py — all tests use mocked psycopg2 (no live Postgres required)."""

import sys
import os
from datetime import datetime
from unittest.mock import MagicMock, patch, call

import psycopg2
import pytest

import st_db


# ---------------------------------------------------------------------------
# Helpers to build the mock connection chain
# ---------------------------------------------------------------------------

def _make_mock_conn(cursor_fetchone=None, cursor_fetchall=None):
    """Return a (mock_conn, mock_cursor) pair.

    The mock_conn implements the psycopg2 double-context-manager protocol:
      with conn:           → calls __enter__/__exit__ on conn
      with conn.cursor():  → calls __enter__/__exit__ on the cursor context manager
    """
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = cursor_fetchone
    mock_cursor.fetchall.return_value = cursor_fetchall if cursor_fetchall is not None else []

    # conn.cursor() returns a context manager whose __enter__ yields mock_cursor
    cursor_cm = MagicMock()
    cursor_cm.__enter__ = MagicMock(return_value=mock_cursor)
    cursor_cm.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cursor_cm

    # with conn: — conn itself is a context manager
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    return mock_conn, mock_cursor


# ---------------------------------------------------------------------------
# Test 1: get_conn raises RuntimeError when DATABASE_URL is absent
# ---------------------------------------------------------------------------

def test_get_conn_raises_when_no_env(monkeypatch):
    """get_conn() must raise RuntimeError when DATABASE_URL is not set."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL is not configured"):
        st_db.get_conn()


# ---------------------------------------------------------------------------
# Test 2: init_db executes both CREATE TABLE statements
# ---------------------------------------------------------------------------

def test_init_db_executes_create_tables(monkeypatch):
    """init_db() must call cursor.execute twice and close the connection."""
    mock_conn, mock_cursor = _make_mock_conn()

    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")
    with patch("st_db.psycopg2.connect", return_value=mock_conn) as mock_connect:
        st_db.init_db()

    mock_connect.assert_called_once_with("postgresql://fake/db")
    assert mock_cursor.execute.call_count == 2, (
        f"Expected 2 CREATE TABLE calls, got {mock_cursor.execute.call_count}"
    )
    # Both calls must include CREATE TABLE IF NOT EXISTS
    for c in mock_cursor.execute.call_args_list:
        sql = c.args[0]
        assert "CREATE TABLE IF NOT EXISTS" in sql
    mock_conn.close.assert_called_once()


# ---------------------------------------------------------------------------
# Test 3: save_analysis inserts with Json and returns the new id
# ---------------------------------------------------------------------------

def test_save_analysis_returns_id(monkeypatch):
    """save_analysis() must return the integer id from RETURNING id."""
    mock_conn, mock_cursor = _make_mock_conn(cursor_fetchone=(42,))

    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")
    with patch("st_db.psycopg2.connect", return_value=mock_conn):
        result = st_db.save_analysis("Q2 Review", {"key": "val"})

    assert result == 42

    # Verify execute was called once and the second param used Json wrapping
    mock_cursor.execute.assert_called_once()
    call_args = mock_cursor.execute.call_args
    sql = call_args.args[0]
    params = call_args.args[1]

    assert "INSERT INTO analysis_runs" in sql
    assert "RETURNING id" in sql
    assert params[0] == "Q2 Review"

    # The payload parameter must be a psycopg2 Json adapter instance
    from psycopg2.extras import Json
    assert isinstance(params[1], Json), (
        f"Expected Json adapter, got {type(params[1])}"
    )


# ---------------------------------------------------------------------------
# Test 4: list_analyses returns list of dicts with correct shape
# ---------------------------------------------------------------------------

def test_list_analyses_returns_list_of_dicts(monkeypatch):
    """list_analyses() must map fetchall rows to list[dict] with correct keys."""
    saved_at = datetime(2026, 6, 4, 12, 0, 0)
    mock_conn, mock_cursor = _make_mock_conn(
        cursor_fetchall=[(1, "Q2 Review", saved_at)]
    )

    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")
    with patch("st_db.psycopg2.connect", return_value=mock_conn):
        result = st_db.list_analyses()

    assert result == [{"id": 1, "label": "Q2 Review", "saved_at": saved_at}]

    mock_cursor.execute.assert_called_once()
    sql = mock_cursor.execute.call_args.args[0]
    assert "ORDER BY saved_at DESC" in sql


# ---------------------------------------------------------------------------
# Test 5: load_analysis returns the payload dict from fetchone
# ---------------------------------------------------------------------------

def test_load_analysis_returns_payload(monkeypatch):
    """load_analysis() must return row[0] (the JSONB payload dict)."""
    payload = {"analysis_result": {}, "campaign_agg": [], "merged_df": []}
    mock_conn, mock_cursor = _make_mock_conn(cursor_fetchone=(payload,))

    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")
    with patch("st_db.psycopg2.connect", return_value=mock_conn):
        result = st_db.load_analysis(1)

    assert result == payload

    mock_cursor.execute.assert_called_once()
    call_args = mock_cursor.execute.call_args
    sql = call_args.args[0]
    params = call_args.args[1]
    assert "SELECT payload FROM analysis_runs WHERE id = %s" in sql
    assert params == (1,)


# ---------------------------------------------------------------------------
# Test 6: load_analysis raises RuntimeError when row not found
# ---------------------------------------------------------------------------

def test_load_analysis_raises_when_not_found(monkeypatch):
    """load_analysis() must raise RuntimeError when fetchone returns None."""
    mock_conn, mock_cursor = _make_mock_conn(cursor_fetchone=None)

    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")
    with patch("st_db.psycopg2.connect", return_value=mock_conn):
        with pytest.raises(RuntimeError, match="Analysis run 999 not found"):
            st_db.load_analysis(999)


# ---------------------------------------------------------------------------
# Test 7: delete_analysis executes DELETE with correct id param
# ---------------------------------------------------------------------------

def test_delete_analysis_executes_delete(monkeypatch):
    """delete_analysis() must execute DELETE with the correct id parameter."""
    mock_conn, mock_cursor = _make_mock_conn()

    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")
    with patch("st_db.psycopg2.connect", return_value=mock_conn):
        st_db.delete_analysis(5)

    mock_cursor.execute.assert_called_once()
    call_args = mock_cursor.execute.call_args
    sql = call_args.args[0]
    params = call_args.args[1]
    assert "DELETE FROM analysis_runs WHERE id = %s" in sql
    assert params == (5,)
    mock_conn.close.assert_called_once()


# ---------------------------------------------------------------------------
# Test 8: _log_analysis_run swallows psycopg2.Error silently
# ---------------------------------------------------------------------------

def test_log_analysis_run_swallows_psycopg2_error(monkeypatch):
    """_log_analysis_run() must not raise even when psycopg2.connect raises."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")
    with patch(
        "st_db.psycopg2.connect",
        side_effect=psycopg2.OperationalError("connection refused"),
    ):
        # Must complete without raising any exception
        st_db._log_analysis_run(
            run_mode="live",
            error_type=None,
            campaign_count=3,
            latency_ms=1500,
            api_fallback_active=False,
        )


# ---------------------------------------------------------------------------
# Test 9: Full CRUD round-trip — save -> list -> load -> delete
# ---------------------------------------------------------------------------

def _make_staged_conn(fetchone_val=None, fetchall_val=None):
    """Build a mock (conn, cursor) pair with pre-configured return values.

    Follows the same double-context-manager protocol as _make_mock_conn().
    Returns (mock_conn, mock_cursor) so callers can assert on mock_cursor.
    """
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = fetchone_val
    mock_cursor.fetchall.return_value = fetchall_val if fetchall_val is not None else []

    cursor_cm = MagicMock()
    cursor_cm.__enter__ = MagicMock(return_value=mock_cursor)
    cursor_cm.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cursor_cm
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    return mock_conn, mock_cursor


def test_crud_round_trip(monkeypatch):
    """Full CRUD round-trip: save -> list -> load -> delete with mocked psycopg2.

    Verifies:
      Stage 1 (save):   Returns the id from RETURNING clause (99).
      Stage 2 (list):   Returns list with correct id, label, saved_at.
      Stage 3 (load):   Returns payload dict equal to what was saved.
      Stage 4 (delete): Executes DELETE with correct id parameter.
    """
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")

    sample_payload = {
        "analysis_result": {
            "executive_summary": "Test summary — round-trip integrity check",
            "campaigns": [],
        },
        "campaign_agg": [{"campaign_id": "cmp_1", "spend": 100.0}],
        "merged_df": [{"session_id": "s1"}],
    }

    saved_at = datetime(2026, 6, 4, 12, 0, 0)

    # Build four independent connection mocks — one per CRUD call
    conn_save, cur_save = _make_staged_conn(fetchone_val=(99,))
    conn_list, cur_list = _make_staged_conn(fetchall_val=[(99, "Round-trip test", saved_at)])
    conn_load, cur_load = _make_staged_conn(fetchone_val=(sample_payload,))
    conn_delete, cur_delete = _make_staged_conn()

    with patch(
        "st_db.psycopg2.connect",
        side_effect=[conn_save, conn_list, conn_load, conn_delete],
    ):
        # Stage 1: save_analysis — must return id=99
        run_id = st_db.save_analysis("Round-trip test", sample_payload)
        assert run_id == 99, f"Expected run_id=99, got {run_id}"

        # Stage 2: list_analyses — must return 1 entry with correct fields
        rows = st_db.list_analyses()
        assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
        assert rows[0]["id"] == 99
        assert rows[0]["label"] == "Round-trip test"
        assert rows[0]["saved_at"] == saved_at

        # Stage 3: load_analysis — payload dict must match what was saved (round-trip integrity)
        loaded_payload = st_db.load_analysis(99)
        assert loaded_payload == sample_payload, (
            "Round-trip integrity failed: loaded payload does not equal saved payload"
        )

        # Stage 4: delete_analysis — must call DELETE with correct id parameter
        st_db.delete_analysis(99)
        cur_delete.execute.assert_called_once()
        delete_call = cur_delete.execute.call_args
        delete_sql = delete_call.args[0]
        delete_params = delete_call.args[1]
        assert "analysis_runs" in delete_sql, "DELETE SQL must reference analysis_runs table"
        assert delete_params == (99,), f"Expected params=(99,), got {delete_params}"
