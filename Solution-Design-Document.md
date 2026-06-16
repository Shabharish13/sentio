# Docket Assessment — Solution Design Document

## Introduction

This document records the solution design for **Sentio**, a fictional subscription SaaS that predicts churn and maintains a real-time customer health score for B2B SaaS companies (*"See churn before your customers do."*). The full company profile — ICP, personas, pricing, integrations — lives in `sentio-company-profile.md` and is the factual anchor for everything below.

The solution targets pipeline leaks in lead qualification. The assignment lists four gaps; this build addresses the two with the most leverage and scopes the rest out.

### Problems

**Statement:** Inbound demo requests sit in a queue — nobody knows which ones to call first.
**Observation:** There is no prioritisation process.
**Goal:** Identify and prioritise inbound leads by ICP fit and intent. *(In scope — Problem 1.)*

**Statement:** The website chatbot greets visitors but doesn't qualify them, doesn't book meetings, and never escalates to a human when a real prospect shows up.
**Observation:** The chatbot lacks reasoning and intelligence.
**Goal:** An AI chatbot grounded in knowledge articles and ICP profiles that qualifies, books, and escalates. *(In scope — Problem 2.)*

**Statement:** SDRs are blasting the same template to every outbound lead, and conversion is dropping.
**Observation:** SDRs lack insight on the lead and can't personalise outreach.
**Goal:** An insight + email-generation engine for SDRs. *(Out of scope for now — revisit if time allows. Note: the inbound flow already produces personalised, sourced hand-off notes via the Copywriter Agent, so the core engine for this exists and could be pointed at an outbound list later.)*

**Statement:** Past leads — months of demo requests that never converted — sit in a graveyard, untouched.
**Observation:** Stale leads with no re-engagement strategy.
**Goal:** A re-engagement strategy. *(Out of scope.)*

### Scope at a glance

| Problem | Status |
|---|---|
| 1 — Inbound prioritisation | **In scope** |
| 2 — Intelligent chatbot | **In scope** |
| 3 — SDR outbound personalisation | Out of scope (engine exists via Copywriter; revisit if time) |
| 4 — Lead graveyard re-engagement | Out of scope |

---

## Architecture at a Glance

Two entry paths, four agents, one deterministic scoring engine, one CRM. Every lead — whether it arrives through the form or the chatbot — converges on HubSpot, deduplicated by email.

```
/demo form submit
   └─ Inbound Pipeline:
        email in Apollo cache? ─ hit → SCORE | miss → enrich (Apollo) → SCORE
        → ROUTE ─ A/B → Research Agent (LLM: triggers) → Copywriter (LLM: email + notes)
                        → CRM Agent (upsert deal, demo-requested stage)
                 └ C   → CRM Agent (upsert deal, DISQUALIFIED stage + reason notes)

any page → "Talk to Sage" (page-aware)
   └─ Sage Chat Agent (RAG over KB):
        answer-first → qualify on self-reported signals → outcome:
          book      → capture email → enrich + SCORE + Research → CRM upsert (demo-requested + transcript)
          disqualify→ CRM upsert (DISQUALIFIED stage + disqualification notes), warm close
          escalate  → hand to human with context | nurture → offer KB resource

Both paths ──────────────────────────────► HubSpot CRM (deduped by email)
```

The design is **multi-agent**: each agent has one job, a defined input/output contract, and is independently testable. The numeric judgment that decides *who to call first* is removed from the LLM entirely and handed to a deterministic scoring engine — so prioritisation is reproducible and defensible, not a model's opinion.

---

## Deterministic Scoring Engine

> **The reconciling decision of this design.** Scores are calculated by **code**, not by an LLM. The LLM is only invoked *after* scoring is complete, and only for qualitative work (trigger research, copywriting). This makes prioritisation deterministic, auditable, and identical on every run.

**Input:** Apollo people + organisation enrichment data. The lead's email is checked against the Apollo cache first — on a hit, scoring runs directly off the cached record and the Apollo API call is skipped (protects the free-tier credit limit). Only a cache miss triggers a live Apollo call.
**Reads from:** an ICP scoring CSV built from `sentio-company-profile.md` (weights are data, not hardcoded constants).
**Output:** a numeric ICP fit score → grade, plus an intent score, attached to the lead record before any model runs.

### ICP fit score (max 90 pts)

Computed by summing weighted bands from the CSV:

- **Company size (headcount):** 100–300 → 25, 301–800 → 20, 51–99 → 10, 801–2000 → 5, else 0
- **Industry:** Computer Software 20, Internet 18, Financial Services (SaaS-confirmed) 15, IT & Services 15, HR 12, Martech 12, Financial Services (no SaaS signal) 5, other tech-adjacent 5, non-tech 0
- **Title / seniority (champion):** VP/Head of CS 20 … down to end-user 3, other 0
- **Geography:** USA 15, Canada/UK 12, ANZ 10, W. Europe 7, other 0
- **Business model:** B2B confirmed 10, SaaS confirmed +5

**Grade thresholds:** A = 60+ · B = 30–59 · C = below 30.

**Industry disambiguation (code, not LLM):** when Apollo returns the ambiguous `Financial Services`, the engine inspects the `technologies` field (Tavily fallback) for `SaaS / API / platform / fintech / payments / subscription`. One or more present → fintech-SaaS path (15 pts); none → traditional-finance path (5 pts).

### Intent score

Derived from available signal. A form lead arriving via the CTA carries thin intent data; a chatbot lead reveals intent through the conversation (questions asked, urgency, fit statements). The engine scores what's present and flags the rest as unknown — it never fabricates intent.

### Routing / exit gate

Scoring is followed by a deterministic **route** step. A **C-grade** (non-ICP) lead does **not** proceed to the Research and Copywriter agents — no LLM spend or SDR email is wasted on a poor fit, so the email generator only ever receives `fit_grade: A | B`. But a C-grade lead is **not discarded**: the CRM Agent upserts it into the **disqualified stage** with **disqualification notes** — the ICP breakdown showing *why* it scored C (e.g. headcount out of range, non-ICP industry, junior title) — so a human can review and override. Only **A** and **B** grades continue down the research/email pipeline.

---

## The Four Agents

Each agent stays strictly within its scope and is hardened against hallucination. No agent invents facts about a real lead's company.

> **Runtime mapping.** The Research, Copywriter, and CRM agents run as ordered stages of the inbound pipeline — chained after the deterministic enrich → score → route steps. Sage runs standalone as the chat agent. Each is a separately-prompted agent with its own contract and responsibility; the pipeline is the orchestration that chains the first three.

| Agent | Role in flow | Prompt file |
|---|---|---|
| Research Agent | Inbound pipeline — research step | `prompts/research_agent.md` |
| Copywriter Agent | Inbound pipeline — email step | `prompts/copywriter_agent.md` |
| CRM Agent | Inbound pipeline final step + Sage hand-off | `prompts/crm_agent.md` (HubSpot tool spec) |
| Sage | Standalone chat agent | `prompts/sage_agent.md` |

### 1. Research Agent

**Input:** the scored, enriched lead record (Apollo data + ICP grade + intent from the Scoring Engine).
**Process:** an LLM prompt surfaces the single strongest **"why now"** signal — it does *not* compute scores. It works **Apollo-first**: the enriched record is already sourced, so the agent mines it before searching, and only uses Tavily (LLM-oriented web research) to find fresher, person-level signals Apollo doesn't carry (capped at 3 searches).

| Source | Signal types it looks for |
|---|---|
| **Apollo record (mine first)** | `funding` (round in last ~12mo), `rapid_growth` (12-mo headcount ≥ ~20%), `competitor_displacement` (rival CS tool in stack), `tech_fit` (integration-ready stack), CS/support org scale |
| **Tavily (supplement)** | `exec_hire` (VP/Head CS hired ≤ 60 days), `job_posting` (CSM/CS Ops/Head of Retention), `retention_signal` (public churn/NPS post) |
| **None** | `none` — returned rather than a weak/unverifiable signal; handled gracefully downstream by the stage+vertical fallback opener |

Funding recency and rapid growth outrank tech-fit when both are present. Every fact in the signal must trace to the Apollo record or a cited URL.

**Output:** a clean JSON brief — lead + company info, ICP grade, intent, classified persona, and the `top_signal` / `signal_type` / `source_url` (traceable).

### 2. Copywriter Agent

**Input:** the Research Agent's JSON brief.
**Process:** a brand-tone-aware LLM prompt writes a **stakeholder-specific** outreach email + SDR hand-off notes. The persona classified from the Apollo title selects the frame (from `sentio-company-profile.md`):

- **Champion (VP/Dir CS):** efficiency, playbook consistency, CSM capacity.
- **Economic buyer (CFO/CRO):** ROI, NRR in dollar terms, payback.
- **Technical evaluator (CTO/IT):** integrations, SOC 2, no-code setup.
- **End user (CS Manager):** day-to-day workflow, time saved.
- **Combined buyer (Founder, <150 emp):** outcome + simplicity in one breath.

The email uses **only sourced data** — the ICP facts, the persona frame, and the research trigger. No invented stats, funding rounds, or tech-stack claims.

### 3. CRM Agent

**Input:** outputs from the Research and Copywriter agents (qualified path), or the score breakdown / disqualification reason (disqualified path).
**Process:** an LLM tool call to HubSpot APIs that **upserts** by email — contact and deal are matched on email, then created or updated. A lead can come back more than once; a repeat event refreshes the existing deal rather than creating a duplicate. The **stage is set by the routing outcome**:

| Outcome | Stage | Notes attached (always required) |
|---|---|---|
| A/B fit, or Sage **Book** | demo-requested (`3832955632`) | SDR hand-off notes — persona, "why now" signal, draft email |
| C fit, or Sage **Disqualify** | disqualified (`3840698071`) | **Disqualification notes** — the specific reason (failed ICP dimension, or the conversational signal that placed them out of market) + transcript/score breakdown |

**A deal is never written without notes.** A disqualified deal with no reason is useless for human review, so the disqualification note is mandatory on that path. *(HubSpot pipeline `default`.)*

### 4. Sage — Chat Agent

A conversational agent on **every page** of the site, strictly on brand tone, that answers **only** from the knowledge base.

**Page awareness:** Sage receives the current page (`/pricing`, `/product`, `/demo`, …) at widget init and uses it as an intent signal — a visitor on `/pricing` is read as later-funnel than one on the homepage — to weight qualification and tailor responses. It never has to ask which page they're on. *Build delta: the widget currently mounts on `/pricing` and `/demo` only; extending it to all pages is outstanding work, but the prompt already consumes the page so no prompt change is needed.*

**Qualification — conversational, not enrichment-based.** Sage has *no* Apollo data during the chat. It qualifies on **five self-reported signals** collected one at a time (answer-first, then one binary question per turn): use-case/pain, team context, authority, timeline, company scale. It never runs as a form.

**Process:** a RAG-grounded LLM over the product glossary + KB markdown. Each turn it retrieves the top chunks and answers *only* from them. A weak retrieval match (cosine < 0.75) is treated as "no answer" → escalate, not guess.

**Outcomes** (evaluated every turn, fired as soon as a threshold is met):
- **Book** — scale ≥ ~50, champion/decision-maker role, active timeline. Sage captures the work email, then the runtime kicks off the **enrich → score → research** pipeline so the deal carries a real ICP grade and "why now" signal for SDR hand-off, and the **CRM Agent upserts** the deal (transcript + collected signals attached as a note).
- **Escalate** — custom/enterprise pricing, security/procurement/legal, implementation scope, explicit ask for a human, or low retrieval confidence → hand to a human with full context.
- **Nurture** — genuine intent but exploratory timeline or below threshold → offer the single most relevant KB resource by name, capture email if offered.
- **Disqualify** — clearly outside the market (tiny/pre-revenue, non-commercial, no CS function) → close warmly, **and** the CRM Agent upserts a deal in the **disqualified stage** with **disqualification notes** (the reason + transcript) for human review. Sage captures the email if the visitor offers one but doesn't push for it; the record is created either way so a human can see who was turned away and why.

> **Decision recorded:** enrichment/scoring runs **after** Sage captures the email on a Book outcome — not during the chat. This keeps Apollo credits spent only on genuinely booked leads. *Build delta: the current `sage_agent.md` creates the deal from transcript + signals only; wiring the post-capture enrich→score→research step into the chat runtime is outstanding work.*

---

## Knowledge Grounding (RAG)

Sage's answers are grounded to prevent hallucination:

- **Embeddings:** `sentence-transformers` (local, free).
- **Vector store:** ChromaDB (local).
- **Corpus:** KB markdown + product glossary in the repo.

On each turn Sage retrieves the top relevant chunks and is prompted to answer *only* from them. No relevant chunk → escalate or push to sales. This is what separates Sage from the "dumb greeter" being replaced.

---

## Orchestration & Triggers

**Inbound prioritisation pipeline**
- **Trigger:** a visitor submits the `/demo` form.
- **Action:** Apollo cache lookup (hit → skip API) → **score (code)** → route (C-grade exits) → Research Agent (triggers) → Copywriter (email + notes) → CRM Agent (upsert deal).

**Chatbot (Sage)**
- **Trigger:** a visitor clicks **"Talk to Sage"** on any page (Sage receives that page as an intent signal).
- **Action:** Sage answers from the KB and qualifies on self-reported signals. On a **Book** outcome it captures the email, then runs the same cache/enrich → score → Research pipeline to enrich the deal, and the CRM Agent upserts it. Other outcomes: escalate to a human, nurture with a KB resource, or disqualify.

Once a chat lead books, both paths converge on the **same** enrich → score → research → CRM pipeline. The only difference is the entry point and how much intent data exists up front — the form starts from enrichment, Sage starts from conversation.

---

## Stack

| Layer | Tool |
|---|---|
| Website | Next.js (Vercel) |
| Backend / agent runtime | Python (FastAPI) |
| LLM | OpenAI `gpt-5` (primary) → Anthropic `claude-sonnet-4-6` → logged-in `claude` CLI — ordered fallback chain (`backend/app/clients/llm.py`). Agent prompts are provider-agnostic system prompts, so they port unchanged. |
| Embeddings | sentence-transformers (local, free) |
| Vector store | ChromaDB (local) |
| Lead enrichment | Apollo.io (free tier, responses cached to local JSON) |
| Supplemental research | Tavily Search API (free tier) |
| CRM | HubSpot (free tier) |
| Meeting booking | HubSpot Deals API (pipeline `default`; demo-requested `3832955632`, disqualified `3840698071`) |

---

## Hard Constraints & Guardrails

- **No hardcoded or faked outputs** — everything is generated at runtime from real inputs.
- **No runtime hallucination** — emails and chat answers use only sourced data (enrichment + research + KB). No fabricated stats, funding, pricing, or tech-stack claims about a real lead.
- **Scores are computed by code, not the LLM** — read deterministically from the ICP CSV.
- **The LLM is invoked only after all deterministic steps are complete** — enrich and score first, then research, copywrite, and converse.
- **Apollo responses are cached to local JSON** to protect the 50-credit/month free-tier limit.
- **ICP weights live in a CSV** (built from `sentio-company-profile.md`), never as hardcoded values in code.
- **Every agent output is traceable** to a real input — research triggers carry their source URL; emails cite only profile/research facts.
- **Each agent is scope-guarded** — it performs only its own job and refuses out-of-scope work.

---

## Pre-Requisites

1. A website with a demo-request form and Product / Use-cases / Pricing pages.
2. A product knowledge base (markdown in the repo).
3. A CRM (HubSpot).
4. A lead-enrichment API (Apollo).
