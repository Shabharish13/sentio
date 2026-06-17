import json

import pytest

from app.pipeline.inbound import run_inbound_pipeline
from app.pipeline.models import PipelineResult


class StubApollo:
    def __init__(self, org, person):
        self._org, self._person = org, person
        self.org_calls, self.person_calls = [], []

    def enrich_organization(self, domain):
        self.org_calls.append(domain)
        return self._org

    def enrich_person(self, email, **fields):
        self.person_calls.append(email)
        return self._person


class StubLLM:
    """First call -> research final JSON; second call -> email body."""

    def __init__(self):
        self.calls = []

    def complete(self, system, user, max_tokens=1024):
        self.calls.append((system, user))
        if "Research" in system or "why now" in system.lower():
            return json.dumps({"action": "final", "top_signal": "Raised a Series B",
                               "signal_type": "funding", "source_url": "https://x"})
        return "Hi Jane,\n\nNoticed your Series B...\n\nBest,\nAlex"


class StubTavily:
    def search(self, query, **kwargs):
        return {"results": []}


class StubHubSpot:
    def __init__(self):
        self.calls = []

    def upsert_contact(self, email, properties):
        self.calls.append(("contact", email)); return "c1"

    def upsert_deal(self, name, stage, contact_id):
        self.calls.append(("deal", name, stage)); return "d1"

    def create_note(self, body, deal_id):
        self.calls.append(("note", body)); return "n1"


A_FORM = {
    "first_name": "Jane", "last_name": "Doe", "work_email": "jane@meridian.io",
    "company_name": "Meridian Analytics", "job_title": "VP of Customer Success",
    "company_size": "201-500", "problem_stated": "surprise churn", "how_heard": "Referral",
}
A_ORG = {"organization": {"estimated_num_employees": 210, "industry": "Computer Software",
                          "country": "United States", "technology_names": ["HubSpot"]}}
A_PERSON = {"person": {"title": "VP of Customer Success", "country": "United States"}}


def test_qualified_lead_runs_research_email_and_demo_requested_deal():
    apollo = StubApollo(A_ORG, A_PERSON)
    llm = StubLLM()
    hubspot = StubHubSpot()
    result = run_inbound_pipeline(A_FORM, apollo=apollo, llm=llm, tavily=StubTavily(), hubspot=hubspot)

    assert isinstance(result, PipelineResult)
    assert result.fit_grade == "A"
    assert result.route == "qualified"
    assert result.signal_type == "funding"
    assert result.email_draft.startswith("Hi Jane")
    assert result.crm.stage == "3832955632"
    assert len(llm.calls) == 2
    note_call = [c for c in hubspot.calls if c[0] == "note"][0]
    assert "Series B" in note_call[1] and "Hi Jane" in note_call[1]
    assert apollo.org_calls == ["meridian.io"]


def test_disqualified_lead_skips_research_and_writes_disqualified_deal():
    c_form = {
        "first_name": "Bob", "last_name": "Lee", "work_email": "bob@tinyco.io",
        "company_name": "TinyCo", "job_title": "Office Manager",
        "company_size": "1-10", "problem_stated": "", "how_heard": "Other",
    }
    c_org = {"organization": {"estimated_num_employees": 6, "industry": "Construction",
                              "country": "India", "technology_names": []}}
    apollo = StubApollo(c_org, {"person": {}})
    llm = StubLLM()
    hubspot = StubHubSpot()
    result = run_inbound_pipeline(c_form, apollo=apollo, llm=llm, tavily=StubTavily(), hubspot=hubspot)

    assert result.fit_grade == "C"
    assert result.route == "disqualified"
    assert result.email_draft is None
    assert llm.calls == []
    assert result.crm.stage == "3840698071"
    note_call = [c for c in hubspot.calls if c[0] == "note"][0]
    assert "ICP fit C" in note_call[1]


def test_numeric_apollo_revenue_is_formatted_as_string():
    # Apollo returns annual_revenue as a number; the brief/schema expect a string.
    org = {"organization": {**A_ORG["organization"], "annual_revenue": 5_120_000_000.0}}
    result = run_inbound_pipeline(A_FORM, apollo=StubApollo(org, A_PERSON),
                                  llm=StubLLM(), tavily=StubTavily(), hubspot=StubHubSpot())
    assert result.revenue == "$5.1B"
    assert isinstance(result.revenue, str)


def test_exit_check_rejects_missing_email():
    with pytest.raises(ValueError):
        run_inbound_pipeline({"company_name": "X"}, apollo=StubApollo({}, {}),
                             llm=StubLLM(), tavily=StubTavily(), hubspot=StubHubSpot())
