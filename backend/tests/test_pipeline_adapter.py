from app.pipeline.adapter import (
    build_lead,
    build_record,
    contact_props,
    deal_name,
    email_domain,
)
from app.scoring.models import Lead

FORM = {
    "first_name": "Jane", "last_name": "Doe", "work_email": "jane@meridian.io",
    "company_name": "Meridian Analytics", "job_title": "VP of Customer Success",
    "company_size": "201-500", "problem_stated": "surprise churn at renewal",
    "how_heard": "Referral / word of mouth",
}
ORG = {"organization": {"estimated_num_employees": 210, "industry": "Computer Software",
                        "country": "United States",
                        "technology_names": ["HubSpot", "Segment"]}}
PERSON = {"person": {"title": "VP of Customer Success", "country": "United States"}}


def test_email_domain():
    assert email_domain("jane@meridian.io") == "meridian.io"
    assert email_domain("bad-email") == ""


def test_build_lead_from_apollo_and_form():
    lead = build_lead(FORM, ORG, PERSON)
    assert isinstance(lead, Lead)
    assert lead.headcount == 210
    assert lead.industry == "Computer Software"
    assert lead.title == "VP of Customer Success"
    assert lead.country == "United States"
    assert "HubSpot" in lead.technologies
    assert lead.is_b2b is True
    assert lead.problem_stated == "surprise churn at renewal"
    assert lead.how_heard == "Referral / word of mouth"


def test_build_lead_falls_back_to_form_company_size_when_no_apollo():
    lead = build_lead(FORM, {"organization": {}}, {"person": {}})
    assert lead.headcount == 350
    assert lead.title == "VP of Customer Success"
    assert lead.is_b2b is False


def test_build_record_has_contact_and_company():
    rec = build_record(FORM, ORG, PERSON)
    assert rec["contact"]["name"] == "Jane Doe"
    assert rec["contact"]["title"] == "VP of Customer Success"
    assert rec["company"]["name"] == "Meridian Analytics"
    assert rec["company"]["headcount"] == 210
    assert rec["company"]["technologies"] == ["HubSpot", "Segment"]


def test_contact_props_and_deal_name():
    assert contact_props(FORM) == {"firstname": "Jane", "lastname": "Doe",
                                   "jobtitle": "VP of Customer Success"}
    assert deal_name(FORM) == "Meridian Analytics — inbound"
