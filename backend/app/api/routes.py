from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api import deps
from app.api.schemas import ChatRequest, ChatResponse, DemoRequest, LeadBrief
from app.chat.orchestrator import handle_turn
from app.pipeline.inbound import run_inbound_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/demo", response_model=LeadBrief)
def demo(
    req: DemoRequest,
    llm=Depends(deps.provide_llm),
    apollo=Depends(deps.provide_apollo),
    tavily=Depends(deps.provide_tavily),
    hubspot=Depends(deps.provide_hubspot),
) -> LeadBrief:
    """Run the inbound pipeline for a demo request and return the Lead Brief."""
    try:
        result = run_inbound_pipeline(req.to_form(), apollo=apollo, llm=llm,
                                      tavily=tavily, hubspot=hubspot)
    except ValueError as exc:  # exit check (e.g. missing/invalid work email)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — enrichment/search/CRM failure
        logger.exception("inbound pipeline failed")
        raise HTTPException(status_code=502, detail="Something went wrong. Please try again.") from exc

    return LeadBrief(
        route=result.route,
        fit_grade=result.fit_grade,
        fit_score=result.fit_score,
        intent_score=result.intent_score,
        stakeholder=result.stakeholder,
        signal_type=result.signal_type,
        top_signal=result.top_signal,
        source_url=result.source_url,
        email_draft=result.email_draft,
        disqualification_reason=result.disqualification_reason,
        contact_name=result.contact_name,
        contact_title=result.contact_title,
        contact_email=result.contact_email,
        company_name=result.company_name,
        headcount=result.headcount,
        industry=result.industry,
        revenue=result.revenue,
        enriched=result.enriched,
        crm_stage=result.crm.stage,
        crm_ref=result.crm.deal_id,
    )


@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    store=Depends(deps.provide_store),
    llm=Depends(deps.provide_llm),
    retriever=Depends(deps.provide_retriever),
    apollo=Depends(deps.provide_apollo),
    tavily=Depends(deps.provide_tavily),
    hubspot=Depends(deps.provide_hubspot),
) -> ChatResponse:
    """Drive one Sage turn with server-side qualification state."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")
    state = store.get_or_create(req.session_id, page=req.page)
    try:
        turn = handle_turn(state, req.message, llm=llm, retriever=retriever,
                           apollo=apollo, tavily=tavily, hubspot=hubspot)
    except Exception as exc:  # noqa: BLE001 — retrieval/LLM failure
        logger.exception("chat turn failed")
        raise HTTPException(status_code=502, detail="Sorry — I'm having trouble connecting right now.") from exc

    return ChatResponse(
        session_id=turn.session_id,
        reply=turn.reply,
        outcome=turn.outcome,
        escalated=turn.escalated,
        booked=turn.booked,
        sources=turn.sources,
    )
