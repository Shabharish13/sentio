from __future__ import annotations

from app.scoring.models import Lead

# Demo-form company-size bands -> a representative headcount (midpoint-ish).
_SIZE_BAND_HEADCOUNT = {
    "1-10": 5, "11-50": 30, "51-200": 125, "201-500": 350, "500+": 800,
}


def email_domain(email: str) -> str:
    if "@" not in email:
        return ""
    return email.split("@", 1)[1].strip().lower()


def _org(org: dict) -> dict:
    return org.get("organization") or {}


def _person(person: dict) -> dict:
    return person.get("person") or {}


def build_lead(form: dict, org: dict, person: dict) -> Lead:
    o, p = _org(org), _person(person)
    headcount = o.get("estimated_num_employees")
    if not headcount:
        headcount = _SIZE_BAND_HEADCOUNT.get((form.get("company_size") or "").strip())
    technologies = list(o.get("technology_names") or o.get("current_technologies") or [])
    return Lead(
        headcount=headcount,
        industry=o.get("industry"),
        title=form.get("job_title") or p.get("title"),
        country=o.get("country") or p.get("country"),
        technologies=technologies,
        is_b2b=bool(o),
        problem_stated=form.get("problem_stated") or "",
        how_heard=form.get("how_heard"),
    )


def build_record(form: dict, org: dict, person: dict) -> dict:
    o, p = _org(org), _person(person)
    full_name = f"{form.get('first_name', '')} {form.get('last_name', '')}".strip()

    # Build structured funding object matching the research agent's expected schema.
    # Without this, the agent only receives a stage string and cannot assess recency.
    funding = None
    if o.get("latest_funding_stage"):
        events = [
            {
                "type": e.get("type"),
                "date": (e.get("date") or "")[:10],
                "amount": e.get("amount"),
                "news_url": e.get("news_url"),
            }
            for e in (o.get("funding_events") or [])
        ]
        funding = {
            "latest_stage": o.get("latest_funding_stage"),
            "latest_round_date": (o.get("latest_funding_round_date") or "")[:10],
            "total_funding_printed": o.get("total_funding_printed"),
            "events": events,
        }

    # Map Apollo's decimal growth fractions to rounded percentage points.
    headcount_growth = None
    if o.get("organization_headcount_twelve_month_growth") is not None:
        headcount_growth = {
            "six_month_pct": round((o.get("organization_headcount_six_month_growth") or 0) * 100, 1),
            "twelve_month_pct": round((o.get("organization_headcount_twelve_month_growth") or 0) * 100, 1),
            "twenty_four_month_pct": round((o.get("organization_headcount_twenty_four_month_growth") or 0) * 100, 1),
        }

    return {
        "contact": {
            "name": full_name,
            "title": form.get("job_title") or p.get("title"),
            "seniority": p.get("seniority"),
            "departments": p.get("departments") or [],
            "headline": p.get("headline"),
        },
        "company": {
            "name": form.get("company_name"),
            "domain": email_domain(form.get("work_email", "")),
            "industry": o.get("industry"),
            "headcount": o.get("estimated_num_employees"),
            "revenue_range": o.get("annual_revenue_printed") or o.get("organization_revenue_printed"),
            "founded_year": o.get("founded_year"),
            "technologies": list(o.get("technology_names") or o.get("current_technologies") or []),
            "keywords": o.get("keywords") or [],
            "departmental_head_count": o.get("departmental_head_count"),
            "funding": funding,
            "headcount_growth": headcount_growth,
        },
    }


def contact_props(form: dict, org: dict | None = None) -> dict:
    o = _org(org or {})
    props: dict = {
        "firstname": form.get("first_name", ""),
        "lastname": form.get("last_name", ""),
        "jobtitle": form.get("job_title", ""),
        "company": form.get("company_name", ""),
    }
    revenue = o.get("annual_revenue") or o.get("organization_revenue")
    if revenue:
        props["annualrevenue"] = str(int(float(revenue)))
    employees = o.get("estimated_num_employees")
    if employees:
        props["numemployees"] = str(employees)
    industry = o.get("industry")
    if industry:
        props["industry"] = industry
    return props


def deal_name(form: dict) -> str:
    return f"{form.get('company_name', 'Unknown')} — inbound"
