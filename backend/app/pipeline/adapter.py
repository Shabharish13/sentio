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
    return {
        "contact": {
            "name": full_name,
            "title": form.get("job_title") or p.get("title"),
            "seniority": p.get("seniority"),
        },
        "company": {
            "name": form.get("company_name"),
            "domain": email_domain(form.get("work_email", "")),
            "industry": o.get("industry"),
            "headcount": o.get("estimated_num_employees"),
            "technologies": list(o.get("technology_names") or o.get("current_technologies") or []),
            "funding": o.get("funding") or o.get("latest_funding_stage"),
            "keywords": o.get("keywords") or [],
        },
    }


def contact_props(form: dict) -> dict:
    return {
        "firstname": form.get("first_name", ""),
        "lastname": form.get("last_name", ""),
        "jobtitle": form.get("job_title", ""),
    }


def deal_name(form: dict) -> str:
    return f"{form.get('company_name', 'Unknown')} — inbound"
