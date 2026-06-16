from __future__ import annotations

import re

from app.scoring.models import FitResult, Lead
from app.scoring.weights import (
    load_business_model,
    load_geography,
    load_headcount_bands,
    load_industry,
    load_titles,
)

# Keywords that confirm a fintech-SaaS reading of an ambiguous "Financial Services" industry.
FINANCIAL_SAAS_KEYWORDS = {"saas", "api", "platform", "fintech", "payments", "subscription"}
# Tech-stack signals or industries that confirm the company is itself a SaaS business.
SAAS_TECH_SIGNALS = {"saas", "api", "platform", "subscription"}
SAAS_CONFIRM_INDUSTRIES = {"computer software", "internet", "information technology and services"}


def score_headcount(headcount: int | None) -> int:
    if headcount is None:
        return 0
    for lo, hi, pts in load_headcount_bands():
        if lo <= headcount <= hi:
            return pts
    return 0


def score_industry(industry: str | None, technologies: list[str]) -> int:
    if not industry:
        return 0
    key = industry.strip().lower()
    table = load_industry()
    if key == "financial services":
        techs = {t.strip().lower() for t in technologies}
        condition = "saas" if techs & FINANCIAL_SAAS_KEYWORDS else "nonsaas"
        return table.get((key, condition), 0)
    return table.get((key, ""), 0)


def score_geography(country: str | None) -> int:
    if not country:
        return 0
    return load_geography().get(country.strip().lower(), 0)


def score_business_model(lead: Lead) -> int:
    weights = load_business_model()
    points = 0
    if lead.is_b2b:
        points += weights.get("b2b", 0)
    techs = {t.strip().lower() for t in lead.technologies}
    industry = (lead.industry or "").strip().lower()
    if techs & SAAS_TECH_SIGNALS or industry in SAAS_CONFIRM_INDUSTRIES:
        points += weights.get("saas", 0)
    return points


def score_title(title: str | None) -> tuple[int, str]:
    if not title:
        return 0, "other"
    text = title.strip().lower()
    for _priority, keywords, points, stakeholder in load_titles():
        if any(re.search(rf"\b{re.escape(kw)}\b", text) for kw in keywords):
            return points, stakeholder
    return 0, "other"


def grade_for(score: int) -> str:
    if score >= 60:
        return "A"
    if score >= 30:
        return "B"
    return "C"


def score_fit(lead: Lead) -> FitResult:
    title_points, stakeholder = score_title(lead.title)
    breakdown = {
        "headcount": score_headcount(lead.headcount),
        "industry": score_industry(lead.industry, lead.technologies),
        "title": title_points,
        "geography": score_geography(lead.country),
        "business_model": score_business_model(lead),
    }
    score = sum(breakdown.values())
    return FitResult(
        score=score,
        grade=grade_for(score),
        stakeholder=stakeholder,
        breakdown=breakdown,
    )
