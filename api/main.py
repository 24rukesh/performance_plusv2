import logging
import os
import uuid
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from api.db import get_latest_result, init_db, insert_analysis_result, insert_pending_session, insert_waitlist_email
from api.email_utils import send_waitlist_notification
from api.models import AnalyzeRequest, CrmWebhookRecord, WaitlistRequest
from data import compute_campaign_agg
from llm import AnalysisResult, run_analysis

logger = logging.getLogger(__name__)
_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Security(_API_KEY_HEADER)) -> None:
    expected = os.environ.get("API_KEY")
    if not expected or api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan, title="Performance Plus API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0", "service": "performance-plus-api"}


@app.post("/api/analyze", response_model=AnalysisResult)
def analyze(body: AnalyzeRequest, _: None = Depends(verify_api_key)) -> AnalysisResult:
    if not body.web_sessions or not body.crm_records:
        raise HTTPException(status_code=422, detail="web_sessions and crm_records must be non-empty")
    web_df = pd.DataFrame([s.model_dump() for s in body.web_sessions])
    crm_df = pd.DataFrame([r.model_dump() for r in body.crm_records])
    try:
        merged_df = pd.merge(web_df, crm_df, on=["session_id", "campaign_id"], how="inner", validate="m:1")
    except pd.errors.MergeError as e:
        raise HTTPException(status_code=422, detail=f"Duplicate session_id in crm_records: {e}")
    if merged_df.empty:
        raise HTTPException(status_code=422, detail="No session_id overlap between web_sessions and crm_records")
    campaign_agg = compute_campaign_agg(merged_df)
    result = run_analysis(campaign_agg)
    run_id = str(uuid.uuid4())
    for campaign in result.campaigns:
        insert_analysis_result(campaign.campaign_id, run_id, result)
    return result


@app.post("/api/webhook/crm", status_code=202)
def webhook_crm(record: CrmWebhookRecord, _: None = Depends(verify_api_key)):
    insert_pending_session(record)
    return {"status": "accepted"}


@app.get("/api/campaigns/{campaign_id}/actions")
def get_campaign_actions(campaign_id: str, _: None = Depends(verify_api_key)):
    row = get_latest_result(campaign_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No analysis results found for campaign_id={campaign_id}")
    return row


@app.post("/api/waitlist", status_code=200)
def waitlist_signup(body: WaitlistRequest):
    signed_up_at = insert_waitlist_email(body.email)
    try:
        send_waitlist_notification(body.email, signed_up_at)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"SMTP error: {exc}")
    return {"message": "You're on the waitlist! We'll be in touch."}
