# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

Take-home interview assignment for Docket AI (Customer Success Program Manager role), due **17 June 2026, 10:00 PM IST**. Deliverables: working agentic marketing tool, Loom walkthrough video, written design document.

## Canonical Docs

- **`Solution-Design-Document.md`** — primary build spec. All architecture, agent logic, workflow, tools, and KB definitions live here. This is the source of truth.
- **`sentio-company-profile.md`** — fictional company profile. ICP scoring weights, buyer personas, research triggers, pricing, integrations, competitive positioning. Referenced throughout the build.
- **`Agentic_Marketing_Assessment.md`** — original brief. Read-only reference.
- **`archive/`** — superseded research docs. Do not reference at any cost.

## Fictional Company: Sentio

AI-powered customer health scoring and churn prediction platform for B2B SaaS companies. "See churn before your customers do." All product, ICP, pricing, and persona details are in `sentio-company-profile.md`.

## What We're Building

Three problems addressed, four named agents (Research, Copywriter, CRM, Sage):

1. **Inbound queue** (demo form → inbound pipeline) — enriches lead via Apollo, scores ICP fit + intent deterministically, runs the Research Agent for trigger signals, generates a stakeholder-specific personalized email draft via the Copywriter Agent, routes to HubSpot via the CRM Agent
2. **Dumb chatbot** (website widget → Sage) — RAG-grounded qualifying chatbot, creates HubSpot deal on qualification (pipeline default, stage 3832955632), escalates to human with full context
3. **Generic outbound** — folded into the Copywriter Agent's email generation step (email engine is part of the same pipeline, not a separate agent)
4. **Lead graveyard** — explicitly out of scope for this build

## Architecture at a Glance

```
/demo form submit → inbound pipeline: exit check → enrich → fit score → intent score → route → Research Agent → classify → Copywriter Agent → CRM Agent
/pricing or /demo page load → Sage (RAG chatbot → book / nurture / escalate / disqualify)
Both paths → HubSpot CRM (deduped by email)
```

## Stack

| Layer | Tool |
|---|---|
| Website | Next.js (Vercel) |
| Backend / agent runtime | Python (FastAPI) |
| LLM | OpenAI `gpt-5` (primary) → Anthropic `claude-sonnet-4-6` → logged-in `claude` CLI (fallback chain via `app/clients/llm.py`) |
| Embeddings | sentence-transformers (local, free) |
| Vector store | ChromaDB (local) |
| Lead enrichment | Apollo.io free tier |
| Supplemental research | Tavily Search API (free tier) |
| CRM | HubSpot free tier |
| Meeting booking | HubSpot Deals API (pipeline `default`; demo-requested `3832955632`, disqualified `3840698071`) |

## Hard Constraints

- No hardcoded/faked outputs — everything generated at runtime
- No hallucinated facts at runtime — emails use only sourced data from enrichment + research
- Scores calculated by code, not LLM
- LLM only invoked after all deterministic steps are complete (the Research and Copywriter agents run after enrich → score → route)
- Loom: camera-on, under 5 minutes, narrative for a non-technical CMO

## As Co-Pilot

- Prioritize demonstrable agentic behavior (tool use, branching logic, handoffs) over polished UI
- Keep prompts visible and editable — evaluation includes "clean prompts"
- Every agent output must be traceable to real inputs
- Apollo responses cached to local JSON — protect the 50 credit/month free tier limit
- ICP scoring reads from CSV (built from sentio-company-profile.md), not hardcoded values
