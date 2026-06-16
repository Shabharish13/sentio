"""Interactive CLI to exercise the Sentio agents one by one.

Run from backend/:  .venv/Scripts/python.exe -m scripts.cli <command> [options]

LLM-backed commands (research, email, sage, pipeline) use get_llm() — the
OpenAI -> Anthropic -> claude CLI fallback chain. Scoring is deterministic (no LLM).
HubSpot writes are DRY-RUN by default; pass --write to create real records.
Apollo enrichment is opt-in (--enrich) to protect the free-tier credit limit.
"""
from __future__ import annotations

import argparse
import json
import sys


def _llm():
    from app.clients.llm import get_llm
    return get_llm()


# ---------------------------------------------------------------- score
def cmd_score(args: argparse.Namespace) -> None:
    from app.scoring.engine import score_lead
    from app.scoring.models import Lead

    lead = Lead(
        headcount=args.headcount, industry=args.industry, title=args.title,
        country=args.country, technologies=args.tech, is_b2b=args.b2b,
        problem_stated=args.problem or "", how_heard=args.how_heard,
    )
    r = score_lead(lead)
    print(f"Fit grade : {r.fit.grade}  (score {r.fit.score})  stakeholder={r.fit.stakeholder}")
    print(f"Breakdown : {r.fit.breakdown}")
    print(f"Intent    : {r.intent.score} ({r.intent.band})  known={r.intent.known}")
    print(f"Route     : {r.route}")
    if r.disqualification_reason:
        print(f"Reason    : {r.disqualification_reason}")


# ---------------------------------------------------------------- research
def cmd_research(args: argparse.Namespace) -> None:
    from app.agents.research import run_research
    from app.clients.tavily_client import TavilyClient

    record = {
        "contact": {"name": args.contact, "title": args.title},
        "company": {
            "name": args.company, "industry": args.industry,
            "headcount": args.headcount, "technologies": args.tech,
            "funding": args.funding, "keywords": [],
        },
    }
    brief = run_research(record, llm=_llm(), tavily=TavilyClient(max_calls=3))
    print(f"signal_type : {brief.signal_type}")
    print(f"top_signal  : {brief.top_signal}")
    print(f"source_url  : {brief.source_url}")


# ---------------------------------------------------------------- email
def cmd_email(args: argparse.Namespace) -> None:
    from app.agents.copywriter import build_brief, write_email
    from app.agents.models import ResearchBrief
    from app.scoring.models import FitResult, IntentResult

    fit = FitResult(score=args.fit_score, grade=args.grade,
                    stakeholder=args.stakeholder, breakdown={})
    intent = IntentResult(score=args.intent, band="high" if args.intent >= 20 else "low", known=True)
    research = ResearchBrief(args.signal, args.signal_type, args.source)
    brief = build_brief(
        contact={"first_name": args.first_name, "name": args.contact, "title": args.title},
        company={"name": args.company, "industry": args.industry, "headcount": args.headcount},
        fit=fit, intent=intent, research=research, problem_stated=args.problem or "",
    )
    print(write_email(brief, llm=_llm()))


# ---------------------------------------------------------------- sage
def cmd_sage(args: argparse.Namespace) -> None:
    from app.agents.sage import answer
    from app.rag.store import get_retriever

    try:
        retriever = get_retriever()
    except Exception:
        print("KB index not found. Build it first:\n"
              "  .venv/Scripts/python.exe -m scripts.build_kb_index", file=sys.stderr)
        raise SystemExit(2)
    resp = answer(args.question, page=args.page, llm=_llm(), retriever=retriever)
    print(f"[redirected={resp.redirected}]  sources={resp.sources}")
    print(resp.answer)
    if resp.question:
        print(resp.question)


# ---------------------------------------------------------------- pipeline
class _DryRunHubSpot:
    def upsert_contact(self, email, properties):
        print(f"[dry-run] upsert_contact  {email}  {properties}")
        return "dry-contact"

    def upsert_deal(self, name, stage, contact_id):
        print(f"[dry-run] upsert_deal      name={name!r}  stage={stage}  contact={contact_id}")
        return "dry-deal"

    def create_note(self, body, deal_id):
        print(f"[dry-run] create_note (deal={deal_id}):\n----\n{body}\n----")
        return "dry-note"


class _SyntheticApollo:
    """No real Apollo calls — synthesizes an org from flags so the pipeline runs free."""

    def __init__(self, industry, headcount, country, tech):
        self._org = {"organization": {
            "industry": industry, "estimated_num_employees": headcount,
            "country": country, "technology_names": tech,
        }}

    def enrich_organization(self, domain):
        return self._org

    def enrich_person(self, email, **fields):
        return {"person": {}}


def cmd_pipeline(args: argparse.Namespace) -> None:
    from app.clients.tavily_client import TavilyClient
    from app.pipeline.inbound import run_inbound_pipeline

    form = {
        "first_name": args.first_name, "last_name": args.last_name, "work_email": args.email,
        "company_name": args.company, "job_title": args.title, "company_size": args.size,
        "problem_stated": args.problem or "", "how_heard": args.how_heard,
    }
    if args.enrich:
        from app.clients.apollo_client import ApolloClient
        apollo = ApolloClient()
    else:
        apollo = _SyntheticApollo(args.industry, args.headcount, args.country, args.tech)

    if args.write:
        from app.clients.hubspot_client import HubSpotClient
        hubspot = HubSpotClient()
    else:
        hubspot = _DryRunHubSpot()

    result = run_inbound_pipeline(form, apollo=apollo, llm=_llm(),
                                  tavily=TavilyClient(max_calls=3), hubspot=hubspot)
    print(json.dumps({
        "route": result.route, "fit_grade": result.fit_grade, "fit_score": result.fit_score,
        "stakeholder": result.stakeholder, "intent_score": result.intent_score,
        "signal_type": result.signal_type, "top_signal": result.top_signal,
        "disqualification_reason": result.disqualification_reason,
        "crm_stage": result.crm.stage,
    }, indent=2))
    if result.email_draft:
        print("\n--- Draft email ---\n" + result.email_draft)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scripts.cli", description="Test the Sentio agents one by one.")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("score", help="Deterministic ICP fit + intent + routing (no LLM)")
    s.add_argument("--headcount", type=int)
    s.add_argument("--industry")
    s.add_argument("--title")
    s.add_argument("--country")
    s.add_argument("--tech", nargs="*", default=[])
    s.add_argument("--b2b", action="store_true")
    s.add_argument("--problem")
    s.add_argument("--how-heard", dest="how_heard")
    s.set_defaults(func=cmd_score)

    r = sub.add_parser("research", help="Research agent: enriched record -> why-now signal (LLM + Tavily)")
    r.add_argument("--company", required=True)
    r.add_argument("--contact", default="")
    r.add_argument("--title", default="")
    r.add_argument("--industry")
    r.add_argument("--headcount", type=int)
    r.add_argument("--tech", nargs="*", default=[])
    r.add_argument("--funding")
    r.set_defaults(func=cmd_research)

    e = sub.add_parser("email", help="Copywriter agent: brief -> email body (LLM)")
    e.add_argument("--stakeholder", default="champion")
    e.add_argument("--grade", default="A")
    e.add_argument("--fit-score", dest="fit_score", type=int, default=80)
    e.add_argument("--intent", type=int, default=20)
    e.add_argument("--first-name", dest="first_name", default="there")
    e.add_argument("--contact", default="")
    e.add_argument("--title", default="")
    e.add_argument("--company", default="your company")
    e.add_argument("--industry")
    e.add_argument("--headcount", type=int)
    e.add_argument("--signal", help="research top_signal text")
    e.add_argument("--signal-type", dest="signal_type", default="none")
    e.add_argument("--source")
    e.add_argument("--problem")
    e.set_defaults(func=cmd_email)

    g = sub.add_parser("sage", help="Sage chatbot: question -> grounded answer / escalation (RAG + LLM)")
    g.add_argument("question")
    g.add_argument("--page", default="/pricing")
    g.set_defaults(func=cmd_sage)

    pl = sub.add_parser("pipeline", help="Full inbound pipeline (HubSpot dry-run unless --write)")
    pl.add_argument("--email", required=True)
    pl.add_argument("--first-name", dest="first_name", default="")
    pl.add_argument("--last-name", dest="last_name", default="")
    pl.add_argument("--company", required=True)
    pl.add_argument("--title", default="")
    pl.add_argument("--size", default="201-500", help="form company-size band, e.g. 201-500")
    pl.add_argument("--problem")
    pl.add_argument("--how-heard", dest="how_heard", default="Other")
    pl.add_argument("--enrich", action="store_true", help="use real Apollo (spends a credit)")
    pl.add_argument("--industry", help="synthetic org industry when --enrich is off")
    pl.add_argument("--headcount", type=int, help="synthetic org headcount when --enrich is off")
    pl.add_argument("--country", help="synthetic org country when --enrich is off")
    pl.add_argument("--tech", nargs="*", default=[])
    pl.add_argument("--write", action="store_true", help="actually create the HubSpot deal")
    pl.set_defaults(func=cmd_pipeline)

    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
