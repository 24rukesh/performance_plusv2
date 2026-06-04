"""st_db.py — Postgres persistence module for the Streamlit app.

Provides CRUD operations for analysis_runs (save/load/list/delete) and
observability logging via analysis_logs. Follows the same psycopg2
double-context-manager pattern as api/db.py.

No FastAPI dependency — plain Python module importable by app.py and llm.py.
"""

import os

import psycopg2
import psycopg2.errors
import psycopg2.extras  # required: Json adapter + JSONB auto-deserialization
from psycopg2.extras import Json


def get_conn():
    """Open a new connection. Caller is responsible for close()."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg2.connect(url)


def init_db() -> None:
    """Create analysis_runs and analysis_logs tables if they don't exist.

    Idempotent — safe to call on every Streamlit rerun. Uses CREATE TABLE IF
    NOT EXISTS so running alongside api/db.init_db() is safe.
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_runs (
                        id        SERIAL PRIMARY KEY,
                        label     TEXT NOT NULL,
                        saved_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        payload   JSONB NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_logs (
                        id                  SERIAL PRIMARY KEY,
                        logged_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        run_mode            TEXT NOT NULL,
                        error_type          TEXT,
                        campaign_count      INT,
                        latency_ms          INT,
                        api_fallback_active BOOLEAN NOT NULL DEFAULT FALSE
                    )
                """)
    finally:
        conn.close()


def save_analysis(label: str, payload: dict) -> int:
    """Insert an analysis run and return the new row id.

    Args:
        label: Human-readable label for this analysis (e.g. "Q2 2026 Review").
        payload: Dict containing serialized analysis_result, campaign_agg, merged_df.

    Returns:
        Integer id of the newly inserted row.
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO analysis_runs (label, payload) VALUES (%s, %s) RETURNING id",
                    (label, Json(payload)),
                )
                row = cur.fetchone()
                return row[0]
    finally:
        conn.close()


def list_analyses() -> list[dict]:
    """Return all saved analyses ordered by saved_at DESC.

    Returns:
        List of dicts with keys: id (int), label (str), saved_at (datetime).
        The saved_at value is a Python datetime object — callers can call
        .strftime() on it directly (e.g. row['saved_at'].strftime('%b %d, %H:%M')).
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, label, saved_at FROM analysis_runs ORDER BY saved_at DESC"
                )
                rows = cur.fetchall()
                return [{"id": r[0], "label": r[1], "saved_at": r[2]} for r in rows]
    finally:
        conn.close()


def load_analysis(run_id: int) -> dict:
    """Return the payload JSONB dict for the given analysis run id.

    psycopg2 auto-deserializes JSONB to a Python dict when psycopg2.extras
    is imported. Callers receive a plain dict — no json.loads() needed.

    Args:
        run_id: Integer id from analysis_runs.id.

    Returns:
        The payload dict (contains analysis_result, campaign_agg, merged_df).

    Raises:
        RuntimeError: If no row exists for the given run_id.
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT payload FROM analysis_runs WHERE id = %s",
                    (run_id,),
                )
                row = cur.fetchone()
                if row is None:
                    raise RuntimeError(f"Analysis run {run_id} not found")
                return row[0]
    finally:
        conn.close()


def delete_analysis(run_id: int) -> None:
    """Delete an analysis run by id.

    Args:
        run_id: Integer id from analysis_runs.id.
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM analysis_runs WHERE id = %s",
                    (run_id,),
                )
    finally:
        conn.close()


def _log_analysis_run(
    run_mode: str,
    error_type: str | None,
    campaign_count: int | None,
    latency_ms: int | None,
    api_fallback_active: bool,
) -> None:
    """Insert an observability row into analysis_logs.

    Silently swallows psycopg2.Error so DB connectivity issues during logging
    never crash the app. This function is fire-and-forget.

    Args:
        run_mode: 'live' | 'fixture' | 'demo_mode' | 'reload'
        error_type: OpenAI exception class name, or None if live succeeded.
        campaign_count: Number of campaigns in the analysis.
        latency_ms: Wall-clock milliseconds for the full run_analysis() call.
        api_fallback_active: True when the OpenAI API was unavailable.
    """
    try:
        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO analysis_logs
                            (run_mode, error_type, campaign_count, latency_ms, api_fallback_active)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (run_mode, error_type, campaign_count, latency_ms, api_fallback_active),
                    )
        finally:
            conn.close()
    except psycopg2.Error:
        pass  # observability must not crash the app
