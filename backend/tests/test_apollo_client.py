import httpx
import respx
from httpx import Response

from app.clients.apollo_client import ApolloClient

PEOPLE_URL = "https://api.apollo.io/api/v1/people/match"
ORG_URL = "https://api.apollo.io/api/v1/organizations/enrich"


@respx.mock
def test_enrich_person_caches(tmp_path):
    route = respx.post(PEOPLE_URL).mock(
        return_value=Response(200, json={"person": {"name": "Jane"}})
    )
    client = ApolloClient(http=httpx.Client(), cache_dir=tmp_path)

    first = client.enrich_person("jane@meridian.io", first_name="Jane")
    second = client.enrich_person("jane@meridian.io", first_name="Jane")

    assert first == second == {"person": {"name": "Jane"}}
    assert route.call_count == 1  # second call served from cache
    assert (tmp_path / "person_jane_at_meridian.io.json").exists()


@respx.mock
def test_enrich_person_sends_api_key_header(tmp_path):
    route = respx.post(PEOPLE_URL).mock(return_value=Response(200, json={}))
    client = ApolloClient(http=httpx.Client(), cache_dir=tmp_path)
    client.enrich_person("a@b.com")
    assert route.calls.last.request.headers["X-Api-Key"] == "test-apollo"


@respx.mock
def test_enrich_organization_caches(tmp_path):
    route = respx.get(ORG_URL).mock(
        return_value=Response(200, json={"organization": {"name": "Meridian"}})
    )
    client = ApolloClient(http=httpx.Client(), cache_dir=tmp_path)
    client.enrich_organization("meridian.io")
    client.enrich_organization("meridian.io")
    assert route.call_count == 1
