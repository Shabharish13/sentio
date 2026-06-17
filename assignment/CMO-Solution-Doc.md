# Agentic Marketing Solution for Sentio

## Executive Summary

This agentic marketing solution fixes two high-value pipeline leaks for Sentio, a churn prediction company: inbound demo requests are prioritized immediately, and the website chatbot becomes a qualified booking motion instead of a passive greeter.

The solution turns every hand-raise into a scored lead brief in HubSpot. High-fit leads get routed to sales with a research-backed "why now" signal and a draft email. Poor-fit leads are not ignored; they are moved to a disqualified stage with the reason recorded, so Marketing and Sales can audit the funnel instead of losing context.

## Why This Matters to the CMO

The system is designed around pipeline outcomes, not automation for its own sake.

| CMO problem | What the solution does for Sentio | Business value |
|---|---|---|
| Demo requests sit in a queue | Scores and routes every inbound lead at submission time | SDRs call the best leads first |
| Chatbot does not qualify | Sage answers product questions, qualifies visitors, captures email, and triggers handoff | Website traffic converts into qualified conversations |
| SDR outreach is generic | Qualified leads receive a sourced research signal and persona-specific draft email | Faster follow-up with stronger relevance |
| Disqualified leads disappear | Leads classified as low intent and chat-disqualified leads with email are captured, are written to HubSpot with reasons | So quality becomes auditable |

## Assumptions

Sentio is the B2B SaaS company in this assignment context. It helps SaaS teams predict churn and maintain real-time customer health scores.

Target ICP:

- B2B SaaS companies.
- Roughly 100 to 800 employees, with best fit around mid-market CS teams.
- Buyers include VP/Head of Customer Success, RevOps, CFO/CRO, and technical evaluators.
- Pain points include surprise churn, inconsistent playbooks, poor customer health visibility, and CSM capacity pressure.

## What Was Built

### 1. Inbound Demo Prioritization

When a visitor submits the demo form, the backend:

1. Validates that a work email exists.
2. Enriches the person and company through Apollo.
3. Scores ICP fit and intent with deterministic code.
4. Routes the lead:
   - Grade A/B fit: continue to research, email generation, and HubSpot demo-requested stage.
   - C fit: skip AI research/email spend and create a disqualified HubSpot deal with the reason.
   - B fit above the headcount sweet spot: route as edge fit for SDR review.
5. Generates a lead brief for the website and a HubSpot note for Sales.

### 2. Sage Website Chatbot

Sage is the website assistant. It is page-aware, grounded in Sentio's knowledge base, and designed to move from answer to qualification without feeling like a form.

Sage:

1. Answers product, pricing, implementation, integration, and security questions from the knowledge base.
2. Asks one qualifying question at a time.
3. Classifies the conversation into continue, book, escalate, nurture, or disqualify.
4. Captures prospect email before any sales handoff.
5. On a booked chat lead, runs the same enrich -> score -> research -> CRM pipeline as the demo form.
6. On escalation, or disqualification where an email is available, creates the right HubSpot handoff note with transcript context.

## Decision Logic

### Lead Scoring

The ICP fit score is deterministic and calculated from scoring tables in `backend/app/scoring/data/`. The maximum fit score is 95 points.

| Dimension | Parameter | Points |
|---|---|---:|
| Headcount | 51-99 employees | 10 |
| Headcount | 100-300 employees | 25 |
| Headcount | 301-800 employees | 20 |
| Headcount | 801-2,000 employees | 5 |
| Headcount | 2,001+ employees | 0 |
| Industry | Computer Software | 20 |
| Industry | Internet | 18 |
| Industry | Information Technology and Services | 15 |
| Industry | Financial Services with SaaS/API/platform signal | 15 |
| Industry | Human Resources | 12 |
| Industry | Marketing and Advertising | 12 |
| Industry | Telecommunications or E-learning | 5 |
| Industry | Financial Services without SaaS signal | 5 |
| Title | VP/Head of Customer Success | 20 |
| Title | Director of Customer Success | 18 |
| Title | CS Ops / Customer Success Operations | 17 |
| Title | CRO / Chief Revenue Officer | 15 |
| Title | CFO / VP Finance | 12 |
| Title | RevOps leadership | 12 |
| Title | Customer Success Manager / CS lead | 8 |
| Title | Senior CSM, AE, SDR, or similar end-user title | 3 |
| Title | CTO / VP Engineering / Head of IT | 0 |
| Title | CEO / Founder | 0 |
| Geography | United States | 15 |
| Geography | Canada or United Kingdom | 12 |
| Geography | Australia or New Zealand | 10 |
| Geography | Germany, France, Netherlands, Ireland, Spain, Italy, Sweden, Belgium, Austria, Switzerland, Denmark, Finland, Norway, or Portugal | 7 |
| Business model | B2B signal present | 10 |
| Business model | SaaS signal present | 5 |

Grades:

- A: 60+ points. Strong fit, prioritized for Sales.
- B: 30-59 points. Workable fit, routed to Sales or marked edge-fit if above the 800-employee sweet spot.
- C: below 30 points. Disqualified, but still recorded with reason.

### Chat Outcomes

Sage, the chatbot, evaluates self-reported signals during the conversation:

| Signal | Why it matters |
|---|---|
| Use case or pain | Determines whether the visitor has a real churn/CS problem |
| Team context | Confirms relevance to CS, retention, or revenue operations |
| Authority | Identifies champion or decision-maker strength |
| Timeline | Separates active evaluation from casual browsing |
| Company scale | Prevents booking poor-fit companies |

Outcomes:

- Book: strong fit, active pain, right authority, reasonable scale, and email captured.
- Escalate: custom enterprise pricing, security/procurement/legal review, implementation complexity, explicit human request, or weak knowledge-base confidence.
- Nurture: relevant but early-stage or not ready to buy.
- Disqualify: clearly outside market, such as pre-revenue, no CS function, or very small company. A CRM record is created when an email is available.
- Continue: answer the question and ask the next qualifier.

## Deterministic vs Probabilistic

| System part | Type | Reason |
|---|---|---|
| Email validation | Deterministic | Code checks for required email format before pipeline starts |
| Apollo cache lookup | Deterministic | Same domain/email returns same cached enrichment |
| ICP scoring | Deterministic | CSV-weighted rules calculate the score |
| Grade thresholds | Deterministic | Fixed A/B/C thresholds decide route |
| C-grade exit gate | Deterministic | C leads never reach research or copywriting |
| HubSpot stage mapping | Deterministic | Route maps to a fixed CRM stage |
| Deal/contact dedupe | Deterministic | CRM upsert is keyed by email/deal identity |
| Knowledge retrieval | Probabilistic support step | Vector search ranks likely relevant KB chunks |
| Sage answer generation | Probabilistic | LLM writes natural-language answers, constrained to retrieved KB |
| Chat outcome classification | Probabilistic with deterministic guardrails | LLM interprets conversation signals; code controls email capture and final CRM action |
| Research signal selection | Probabilistic with source constraints | LLM summarizes the strongest "why now" signal from Apollo/Tavily inputs |
| Email draft | Probabilistic with source constraints | LLM writes copy from sourced facts and persona framing |

The most important business decision, who gets prioritized, is deterministic. The probabilistic parts improve explanation, personalization, and conversation quality, but they do not own the scoring math.

## Agent Architecture

| Agent | Job | Guardrail |
|---|---|---|
| Research Agent | Finds the strongest sourced "why now" signal | Must use Apollo/Tavily inputs and return a source or no signal |
| Copywriter Agent | Writes persona-specific SDR email and handoff notes | Cannot invent facts, stats, funding, pricing, or tech stack |
| CRM Agent | Upserts contact/deal and attaches notes | Every deal must have a note; disqualified deals require a reason |
| Sage | Answers and qualifies website visitors | Answers only from the KB; redirects/escalates when confidence is low |

## Funnel Flow

```text
Demo form
  -> validate email
  -> Apollo cache/enrichment
  -> deterministic ICP + intent score
  -> route
      -> A/B or edge fit: research -> email -> HubSpot demo-requested
      -> C fit: HubSpot disqualified with reason

Website chat
  -> answer from knowledge base
  -> ask one qualifier at a time
  -> classify outcome
      -> book: capture email -> inbound pipeline -> HubSpot demo-requested
      -> escalate: capture email -> HubSpot handoff note
      -> nurture: offer relevant resource
      -> disqualify: warm close, record reason when email is available
```

## Trade-Offs

Built now:

- Inbound scoring and routing.
- Research-backed sales handoff.
- Persona-specific email draft.
- Sage chatbot with qualification and booking flow.
- HubSpot upsert and dedupe.

Deferred:

- Full outbound list personalization workflow.
- Real meeting-calendar slot booking. Current implementation creates a sales handoff/demo-requested deal rather than selecting a calendar time in-chat.

## Success Metrics

The CMO should evaluate the solution on:

- Speed-to-lead for grades A/B inbound requests.
- Percentage of website chats that become qualified handoffs.
- SDR acceptance rate of agent-generated lead briefs.
- Demo-requested to meeting-booked conversion.
- Disqualified lead audit accuracy.
- Reduction in low-fit SDR follow-up.
