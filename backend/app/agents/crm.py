from __future__ import annotations

from app.agents.models import CrmResult
from app.config import get_settings


def sync_to_crm(*, email: str, contact_props: dict, deal_name: str, route: str,
                note_body: str, hubspot) -> CrmResult:
    """Upsert the contact + deal and attach a (mandatory) note.

    Stage is set by the routing outcome: qualified -> demo-requested, otherwise
    -> disqualified. A deal is never written without a note (design constraint).
    """
    if not note_body or not note_body.strip():
        raise ValueError("note_body is mandatory — a deal must never be written without a note")
    settings = get_settings()
    stage = (
        settings.hubspot_stage_demo_requested
        if route == "qualified"
        else settings.hubspot_stage_disqualified
    )
    contact_id = hubspot.upsert_contact(email, contact_props)
    deal_id = hubspot.upsert_deal(name=deal_name, stage=stage, contact_id=contact_id)
    note_id = hubspot.create_note(note_body, deal_id=deal_id)
    return CrmResult(contact_id=contact_id, deal_id=deal_id, stage=stage, note_id=note_id)
