from __future__ import annotations

from pydantic import BaseModel, Field


class DemoRequest(BaseModel):
    first_name: str = ""
    last_name: str = ""
    work_email: str
    company_name: str = ""
    job_title: str = ""
    company_size: str = ""
    problem_stated: str = ""
    how_heard: str = ""

    def to_form(self) -> dict:
        return self.model_dump()


class LeadBrief(BaseModel):
    route: str
    fit_grade: str
    fit_score: int
    intent_score: int
    stakeholder: str
    signal_type: str
    top_signal: str | None = None
    source_url: str | None = None
    email_draft: str | None = None
    disqualification_reason: str | None = None
    # Contact panel
    contact_name: str = ""
    contact_title: str = ""
    contact_email: str = ""
    # Company panel
    company_name: str = ""
    headcount: int | None = None
    industry: str | None = None
    revenue: str | None = None
    enriched: bool = False
    # CRM
    crm_stage: str
    crm_ref: str


class ChatRequest(BaseModel):
    message: str
    page: str = "/"
    session_id: str | None = Field(default=None)


class ChatResponse(BaseModel):
    session_id: str
    # `answer` is the answer bubble; `question` (nullable) is the qualifying
    # question rendered as a separate bubble. `reply` is kept as an alias of
    # `answer` for backwards compatibility with existing callers.
    answer: str
    reply: str
    question: str | None = None
    outcome: str
    escalated: bool
    booked: bool
    sources: list[str] = []
