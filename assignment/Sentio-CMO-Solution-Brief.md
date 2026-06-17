# Sentio — Agentic Marketing System
### What It Does and Why It Works

---

## The Problem We Solved

Pipeline was leaking at three points:

1. **Inbound queue** — demo requests sat unranked. SDRs called whoever was on top, not whoever was best.
2. **Website chatbot** — greeted visitors, answered nothing, booked no one.
3. **SDR outreach** — same template to every lead. Conversion dropping because no one felt spoken to.

This system fixes all three.

---

## What Was Built

Two entry points into one pipeline. Every qualified lead lands in HubSpot with a score, a "why now" signal, and a ready-to-send email draft — before an SDR touches the record.

### Entry 1 — Inbound Demo Form

A prospect fills the demo request form. Here is what happens next, entirely automated:

```
Form submit
  └─ Enrich (Apollo)         ← who is this person and company?
  └─ Score (code, not AI)    ← how good a fit are they?
  └─ Route                   ← A/B grade → pipeline  |  C grade → disqualified
  └─ Research (AI)           ← what's the "why now" signal?
  └─ Copywriter (AI)         ← write the stakeholder-specific outreach email
  └─ CRM (HubSpot)           ← create deal, attach score + email draft
```

An SDR opens HubSpot. The deal is already there, graded, with a draft email ready to review and send.

### Entry 2 — Sage (Website Chat Agent)

A visitor opens the chat widget on any page. Sage — an AI agent grounded in Sentio's product knowledge base — answers questions, qualifies the visitor through conversation, and routes them:

| Sage outcome | What happens |
|---|---|
| **Book** | Captures email → runs full enrich + score + research pipeline → HubSpot deal created (same stage as form leads) |
| **Escalate** | Hands off to a human with full transcript and context |
| **Nurture** | Offers the most relevant resource; captures email if offered |
| **Disqualify** | Closes warmly; logs the lead in HubSpot with reason — for human review and override |

Both entry points converge on the same HubSpot pipeline, deduplicated by email.

---

## What Is Deterministic and What Is AI

This distinction matters. It prevents hallucination and makes scoring defensible.

### Deterministic (code, not AI)

| Step | What it does | Why it's deterministic |
|---|---|---|
| **Apollo enrichment** | Pulls company headcount, industry, geography, tech stack | API lookup; results cached |
| **ICP fit score** | Sums weighted points across 5 dimensions (size, industry, title, geo, business model) | Reads weights from a CSV; identical inputs → identical score every time |
| **Routing decision** | A/B grade → qualified pipeline; C grade → disqualified | Pure conditional on numeric score; no model involved |
| **Intent scoring** | Scores available signals (page, form fields, chat statements) | Rule-based; no inference |

**Grade thresholds:** A = 60+ pts | B = 30–59 pts | C = below 30 pts (max possible: 90 pts)

The score is computed entirely in code. The AI never decides who is qualified.

### Probabilistic (AI)

| Step | What the AI does | Guardrail |
|---|---|---|
| **Research Agent** | Finds the strongest "why now" signal — funding round, exec hire, job posting, retention signal | Uses only sourced data (Apollo record + cited Tavily URLs); returns `none` rather than a weak signal |
| **Copywriter Agent** | Writes a stakeholder-specific outreach email and SDR hand-off notes | Uses only facts from enrichment and research; no invented stats, pricing, or company claims |
| **Sage** | Qualifies visitors in conversation; answers product questions | Answers only from the knowledge base; cosine similarity < 0.75 triggers escalation, not guessing |

**The rule:** AI only runs after all deterministic steps are complete. The model never sees a lead it hasn't already scored.

---

## How Leads Are Scored

Five dimensions, each capped. Total possible: 90 points.

| Dimension | Top score | Example |
|---|---|---|
| Company size (headcount) | 25 pts | 100–300 employees = 25; >2000 = 0 |
| Industry | 20 pts | Computer Software = 20; non-tech = 0 |
| Title / seniority | 20 pts | VP/Head of CS = 20; CS Manager = 8 |
| Geography | 15 pts | USA = 15; Western Europe = 7 |
| Business model | 10 pts | B2B confirmed + SaaS confirmed = 10 |

**A 300-person US SaaS company, VP of CS:** ~80 pts → Grade A → full pipeline, research, email draft.

**A 30-person services firm, Marketing Coordinator:** ~15 pts → Grade C → disqualified, logged with reason.

---

## How Sage Qualifies Without a Form

Sage collects five signals through conversation — one per turn, not as a questionnaire:

1. **Use case / pain** — what problem are they describing?
2. **Team context** — how many CSMs, how many accounts?
3. **Authority** — are they a decision-maker or an influencer?
4. **Timeline** — active evaluation or exploratory?
5. **Company scale** — employees or ARR, self-reported

As soon as enough signals cross the threshold — qualified on scale, role, and active timeline — Sage asks for the work email and books them. It doesn't wait to collect all five if three are enough.

A visitor who is clearly outside the market (pre-revenue, no CS function, B2C) is disqualified warmly within two turns.

---

## What the SDR Receives

For every A/B qualified lead — whether from the form or Sage — the HubSpot deal note contains:

- **ICP score and grade** with the dimension breakdown
- **Stakeholder classification** (Champion / Economic Buyer / Technical Evaluator / End User / Combined)
- **"Why now" signal** with source citation (funding announcement, exec hire, job posting, etc.)
- **Draft outreach email** written to the classified stakeholder, using only sourced facts
- **Chat transcript** (Sage leads only)

The SDR reviews, edits if needed, and sends. Sentio does not send email automatically.

---

## What Was Left Out (and Why)

**Lead graveyard re-engagement** — out of scope. The inbound and chat pipelines were the highest-leverage problems. The Copywriter Agent's email engine already exists and could be pointed at a re-engagement list with moderate effort.

**SDR outbound personalisation as a separate flow** — folded into the inbound pipeline. The same Research + Copywriter agents that serve the form pipeline produce personalised outreach; extending them to an outbound list is additive, not a rebuild.

---

## Stack

| Component | Tool |
|---|---|
| Website | Next.js |
| Backend / agent runtime | Python (FastAPI) |
| AI models | OpenAI GPT-5 → Anthropic Claude Sonnet (fallback chain) |
| Lead enrichment | Apollo.io |
| Web research | Tavily Search API |
| Knowledge base / chat grounding | ChromaDB (local vector store) |
| CRM | HubSpot |

All outputs are generated at runtime from real inputs. Nothing is hardcoded or pre-generated.
