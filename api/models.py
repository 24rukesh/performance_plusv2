from pydantic import BaseModel, EmailStr


class WebSession(BaseModel):
    session_id: str
    campaign_id: str
    clicks: int
    impressions: int
    cost_usd: float
    conversion_rate: float


class CrmRecord(BaseModel):
    session_id: str
    campaign_id: str
    lead_status: str
    projected_value: float
    sales_notes: str


class AnalyzeRequest(BaseModel):
    web_sessions: list[WebSession]
    crm_records: list[CrmRecord]


class CrmWebhookRecord(BaseModel):
    session_id: str
    campaign_id: str
    lead_status: str
    projected_value: float
    sales_notes: str


class WaitlistRequest(BaseModel):
    email: EmailStr
