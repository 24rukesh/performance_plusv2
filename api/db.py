import os

import psycopg2
import psycopg2.errors
import psycopg2.extras  # required: Json adapter + JSONB auto-deserialization
from fastapi import HTTPException
from psycopg2.extras import Json


def get_conn():
    """Open a new connection. Caller is responsible for close()."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg2.connect(url)


def init_db() -> None:
    """Create tables if they don't exist. Called at lifespan startup."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        id          SERIAL PRIMARY KEY,
                        campaign_id TEXT NOT NULL,
                        run_id      UUID NOT NULL,
                        analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        result_json JSONB NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pending_sessions (
                        id              SERIAL PRIMARY KEY,
                        campaign_id     TEXT NOT NULL,
                        session_id      TEXT NOT NULL,
                        lead_status     TEXT,
                        projected_value NUMERIC,
                        sales_notes     TEXT,
                        received_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS waitlist (
                        id           SERIAL PRIMARY KEY,
                        email        TEXT NOT NULL UNIQUE,
                        signed_up_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        source       TEXT NOT NULL DEFAULT 'landing_page'
                    )
                """)
    finally:
        conn.close()


def insert_analysis_result(campaign_id: str, run_id: str, result) -> None:
    """Insert a campaign analysis result row into analysis_results."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO analysis_results
                        (campaign_id, run_id, analyzed_at, result_json)
                    VALUES (%s, %s::uuid, NOW(), %s)
                    """,
                    (campaign_id, run_id, Json(result.model_dump())),
                )
    finally:
        conn.close()


def get_latest_result(campaign_id: str) -> dict | None:
    """Return the most recent result_json for campaign_id, or None."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT result_json FROM analysis_results
                    WHERE campaign_id = %s
                    ORDER BY analyzed_at DESC
                    LIMIT 1
                    """,
                    (campaign_id,),
                )
                row = cur.fetchone()
                return row[0] if row else None
    finally:
        conn.close()


def insert_pending_session(record) -> None:
    """Insert a CrmWebhookRecord into pending_sessions."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO pending_sessions
                        (campaign_id, session_id, lead_status, projected_value, sales_notes)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        record.campaign_id,
                        record.session_id,
                        record.lead_status,
                        record.projected_value,
                        record.sales_notes,
                    ),
                )
    finally:
        conn.close()


def insert_waitlist_email(email: str) -> str:
    """Insert email into waitlist. Returns signed_up_at as ISO string.

    Raises HTTPException(409) on duplicate email (D-07).
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO waitlist (email, source) VALUES (%s, %s) RETURNING signed_up_at",
                    (email, "landing_page"),
                )
                row = cur.fetchone()
                return row[0].isoformat()
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="You're already on the waitlist.")
    finally:
        conn.close()
