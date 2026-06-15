import httpx
import respx
from httpx import Response

from app.clients.hubspot_client import HubSpotClient

BASE = "https://api.hubapi.com"


def _client() -> HubSpotClient:
    return HubSpotClient(http=httpx.Client())


@respx.mock
def test_upsert_contact_returns_id_and_sends_bearer():
    route = respx.post(f"{BASE}/crm/v3/objects/contacts/batch/upsert").mock(
        return_value=Response(200, json={"results": [{"id": "501"}]})
    )
    cid = _client().upsert_contact("jane@meridian.io", {"firstname": "Jane"})
    assert cid == "501"
    req = route.calls.last.request
    assert req.headers["Authorization"] == "Bearer test-hubspot"
    assert b'"idProperty":"email"' in req.content.replace(b" ", b"")


@respx.mock
def test_upsert_deal_creates_when_none_found():
    respx.post(f"{BASE}/crm/v3/objects/deals/search").mock(
        return_value=Response(200, json={"results": []})
    )
    create = respx.post(f"{BASE}/crm/v3/objects/deals").mock(
        return_value=Response(201, json={"id": "900"})
    )
    did = _client().upsert_deal(
        name="Meridian — inbound", stage="3832955632", contact_id="501"
    )
    assert did == "900"
    body = create.calls.last.request.content.replace(b" ", b"")
    assert b'"dealstage":"3832955632"' in body
    assert b'"pipeline":"default"' in body
    assert b'"associationTypeId":3' in body


@respx.mock
def test_upsert_deal_updates_when_found():
    respx.post(f"{BASE}/crm/v3/objects/deals/search").mock(
        return_value=Response(200, json={"results": [{"id": "777"}]})
    )
    patch = respx.patch(f"{BASE}/crm/v3/objects/deals/777").mock(
        return_value=Response(200, json={"id": "777"})
    )
    did = _client().upsert_deal(
        name="Meridian — inbound", stage="3840698071", contact_id="501"
    )
    assert did == "777"
    assert b'"dealstage":"3840698071"' in patch.calls.last.request.content.replace(b" ", b"")


@respx.mock
def test_create_note_associates_to_deal():
    note = respx.post(f"{BASE}/crm/v3/objects/notes").mock(
        return_value=Response(201, json={"id": "n1"})
    )
    nid = _client().create_note("hand-off notes", deal_id="900")
    assert nid == "n1"
    body = note.calls.last.request.content.replace(b" ", b"")
    assert b'"associationTypeId":214' in body
    assert b'"hs_note_body"' in body
