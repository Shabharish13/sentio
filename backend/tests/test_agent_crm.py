import pytest

from app.agents.crm import sync_to_crm
from app.agents.models import CrmResult


class StubHubSpot:
    def __init__(self):
        self.calls = []

    def upsert_contact(self, email, properties):
        self.calls.append(("contact", email, properties))
        return "c1"

    def upsert_deal(self, name, stage, contact_id):
        self.calls.append(("deal", name, stage, contact_id))
        return "d1"

    def create_note(self, body, deal_id):
        self.calls.append(("note", body, deal_id))
        return "n1"


def test_qualified_routes_to_demo_requested_stage(monkeypatch):
    monkeypatch.setenv("HUBSPOT_STAGE_DEMO_REQUESTED", "3832955632")
    monkeypatch.setenv("HUBSPOT_STAGE_DISQUALIFIED", "3840698071")
    from app.config import get_settings
    get_settings.cache_clear()
    hs = StubHubSpot()
    result = sync_to_crm(
        email="jane@meridian.io", contact_props={"firstname": "Jane"},
        deal_name="Meridian — inbound", route="qualified",
        note_body="SDR hand-off: persona=champion; why-now=Series B.", hubspot=hs,
    )
    assert isinstance(result, CrmResult)
    assert result.stage == "3832955632"
    assert result.contact_id == "c1" and result.deal_id == "d1" and result.note_id == "n1"
    assert ("deal", "Meridian — inbound", "3832955632", "c1") in hs.calls


def test_disqualified_routes_to_disqualified_stage(monkeypatch):
    monkeypatch.setenv("HUBSPOT_STAGE_DEMO_REQUESTED", "3832955632")
    monkeypatch.setenv("HUBSPOT_STAGE_DISQUALIFIED", "3840698071")
    from app.config import get_settings
    get_settings.cache_clear()
    hs = StubHubSpot()
    result = sync_to_crm(
        email="bob@tinyco.io", contact_props={}, deal_name="TinyCo — inbound",
        route="disqualified", note_body="Disqualified: headcount out of ICP range.", hubspot=hs,
    )
    assert result.stage == "3840698071"


def test_empty_note_body_rejected():
    with pytest.raises(ValueError):
        sync_to_crm(email="x@y.io", contact_props={}, deal_name="X", route="qualified",
                    note_body="   ", hubspot=StubHubSpot())
