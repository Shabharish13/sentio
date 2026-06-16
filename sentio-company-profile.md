# Sentio — Fictional Company Profile
### For use in the Docket AI take-home assignment demo

> All details below are invented for demo purposes.  
> Sentio does not exist. No real company, product, pricing, or outcome data is represented here.

---

## Company Overview

| Field | Value |
|---|---|
| **Name** | Sentio |
| **Tagline** | "See churn before your customers do." |
| **Product category** | Customer Health Intelligence — B2B SaaS |
| **Stage** | Series B |
| **Founded** | 2021 |
| **HQ** | Austin, TX |
| **Employees** | ~210 |
| **ARR** | ~$11M |
| **ACV** | ~$36,000 / year |
| **Sales motion** | Demo-led, 45–90 day cycle |
| **SDR team** | 5 SDRs, ~50 accounts/month each |

---

## What Sentio Does

Sentio is an AI-powered customer health scoring and churn prediction platform for B2B SaaS companies.

It connects to a company's existing data sources — product usage, support tickets, NPS/CSAT responses, billing events, and stakeholder engagement activity — and synthesizes them into a single, real-time health score per account. When an account's health score crosses a risk threshold, Sentio surfaces a recommended playbook (e.g., executive outreach, discount offer, onboarding re-engagement) and assigns it to the right CSM automatically.

**The core value proposition:** Sentio gives CS teams a 60–90 day warning before an account is likely to churn, with a recommended action — not just a red flag.

---

## Three Problems Sentio Solves

1. **Blind spots** — CS teams manage 50–150 accounts each and can't monitor every signal manually. Sentio aggregates signals no human can track at scale.
2. **Reactive CS** — Most teams learn about churn risk from the customer, not before. Sentio inverts that: the CSM reaches out before the customer complains.
3. **Inconsistent playbooks** — Different CSMs handle risk differently. Sentio standardizes escalation logic so the best-performing response becomes the default.

---

## Ideal Customer Profile (ICP)

These are the companies Sentio's SDR team targets. The ICP scoring logic is built from these parameters.

| Dimension | Target Range | Notes |
|---|---|---|
| **Company type** | B2B SaaS only | Not B2C, not services, not marketplace |
| **Employees** | 100 – 800 | Below 100: CS team too small to justify; above 800: enterprise procurement adds 6+ months |
| **ARR** | $5M – $50M | Below $5M: churn risk isn't yet existential; above $50M: enterprise competitors (Gainsight) dominate |
| **CS team size** | ≥ 5 CSMs (inferred) | Apollo does not return CS team headcount. Proxy: companies with 100–300 employees in a B2B SaaS vertical typically have 5–15 CSMs. Headcount band scoring serves as the proxy — no separate scoring dimension needed. |
| **Geography** | USA, Canada, UK, ANZ | GTM coverage only |
| **Business model** | Subscription / recurring revenue | One-time or project-based revenue doesn't produce churn signals |
| **Industry** | SaaS, cloud infrastructure, dev tools, fintech SaaS, HR tech, martech | Verticals where retention is a board-level metric |

**ICP score grade thresholds:**  
A = 60+ pts | B = 30–59 pts | C = below 30 pts

---

## ICP Scoring Weights

Used by the inbound pipeline's Scoring Engine to compute fit score deterministically from enrichment data.

### Company Size (Headcount)

| Headcount Band | Points |
|---|---|
| 100 – 300 | 25 |
| 301 – 800 | 20 |
| 51 – 99 | 10 |
| 801 – 2000 | 5 |
| < 50 or > 2000 | 0 |

### Industry

Apollo returns a single `industry` string per company. `Financial Services` is ambiguous — it covers both fintech SaaS companies and traditional banks/insurers. Agent 1 applies a secondary disambiguation check before assigning points: if Apollo's `industry` is `Financial Services`, the agent checks the company's tech stack keywords (via Apollo's `technologies` field or Tavily fallback) for signals like `"SaaS"`, `"API"`, `"platform"`, `"fintech"`, `"payments"`, `"subscription"`. If at least one is present → fintech SaaS path (15 pts). If none → traditional finance path (5 pts).

| Apollo Industry String | Condition | Points |
|---|---|---|
| Computer Software | — | 20 |
| Internet | — | 18 |
| Financial Services | Tech stack confirms SaaS/fintech keywords | 15 |
| Information Technology and Services | — | 15 |
| Human Resources | — | 12 |
| Marketing and Advertising | — | 12 |
| Financial Services | No SaaS/fintech keywords found | 5 |
| Other tech-adjacent (e.g. Telecommunications, E-Learning) | — | 5 |
| Non-tech / unmatched | — | 0 |

### Title / Seniority (Champion)

| Title Pattern | Points |
|---|---|
| VP / Head of Customer Success | 20 |
| Director of Customer Success | 18 |
| VP / Director of CS Ops | 17 |
| CRO / Chief Revenue Officer | 15 |
| CFO / VP Finance (economic buyer path) | 12 |
| CS Manager / CS Lead | 8 |
| AE / SDR / CSM (end user) | 3 |
| Other | 0 |

### Geography

| Region | Points |
|---|---|
| USA | 15 |
| Canada, UK | 12 |
| Australia, New Zealand | 10 |
| Western Europe | 7 |
| Other | 0 |

### Business Model

| Signal | Points |
|---|---|
| B2B confirmed (Apollo org type) | 10 |
| SaaS confirmed (tech stack / Apollo data) | 5 |
| Not confirmed | 0 |

**Total possible: 90 points**

---

## Buyer Personas

The Research Agent classifies the stakeholder type from Apollo title data, and the Copywriter Agent frames the outreach email accordingly.

### Champion — VP / Director of Customer Success

- **Pain:** Managing 80+ accounts per CSM. Can't see which ones are about to churn until it's too late. Renewal reviews are reactive, not predictive.
- **Goal:** Improve net revenue retention (NRR), reduce CSM firefighting, run consistent renewal playbooks.
- **Email frame:** Efficiency, time saved, playbook consistency, CSM capacity.
- **Key phrase:** "Your CSMs shouldn't learn about churn risk from the customer."

### Economic Buyer — CFO / VP Finance / CRO

- **Pain:** Churn is eroding ARR. Board wants NRR >110%. CS is a cost center that needs to justify headcount.
- **Goal:** Reduce gross churn by X%, improve net retention, see CS ROI clearly.
- **Email frame:** ROI, payback period, churn reduction in dollar terms, NRR impact.
- **Key phrase:** "Every point of NRR improvement at $10M ARR is worth six figures in retained revenue."

### Technical Evaluator — CTO / VP Engineering / Head of IT

- **Pain:** Another tool means another integration, another data pipeline, another security review.
- **Goal:** Verify that Sentio doesn't add engineering overhead. Confirm security posture, data residency, API access.
- **Email frame:** Integrations (Salesforce, HubSpot, Segment, Amplitude), SOC 2, no-code setup, REST API.
- **Key phrase:** "Connects to your existing stack in under a day — no custom ETL required."

### End User — CS Manager / Senior CSM

- **Pain:** Manually checking dashboards across five tools to figure out which accounts need attention today.
- **Goal:** A single view of account health, actionable next steps, less admin.
- **Email frame:** Day-to-day workflow, ease of use, time saved per week.
- **Key phrase:** "Know which accounts to call today without spending an hour figuring it out."

### Combined Buyer — Founder / CEO (company < 150 employees)

- **Pain:** No dedicated CS team yet. Founder is managing key accounts personally and can't scale that.
- **Goal:** Build a CS motion that doesn't require hiring a team of 10.
- **Email frame:** Business outcome + simplicity. ROI and ease of setup in the same sentence.
- **Key phrase:** "A CS intelligence layer you can stand up before you hire your second CSM."

---

## High-Intent Research Triggers

These are the signals the Research Agent (LLM + Tavily) looks for. Each trigger maps to a specific email opener.

| Signal | Why It Matters | Email Opener Frame |
|---|---|---|
| Hired a VP of Customer Success in the last 60 days | New VP CS = mandate to fix the CS motion; first 90 days, budget to spend | "Congrats on the VP CS hire — new CS leaders typically have 90 days to set direction..." |
| Raised a Series A or B in the last 6 months | Fresh capital, scaling ARR, churn becomes existential at this stage | "Series B companies typically see their first real churn pressure as the customer base scales..." |
| Job posting: CSM, CS Ops, VP CS, Head of Retention | Active CS team build-out; CS tooling budget likely | "Noticed you're hiring for CS — that usually means the spreadsheet-and-gut-feel era is ending..." |
| NPS program launched / Medallia / Delighted mentioned in news | Already investing in feedback loops; natural next step is closing the loop on risk | "You're collecting NPS — Sentio turns that signal into a health score that triggers action..." |
| Blog post / press release about customer retention focus | Explicit intent signal; leadership is talking about retention publicly | "Saw [company]'s post on reducing churn — sounds like retention is a top priority right now..." |
| No signal found | Fallback: company stage + vertical frame | Opens with company size + industry + why churn risk is acute at this stage |

---

## Pricing Tiers

*(Fictional — illustrative only)*

| Tier | Price | Seats | Integrations | Support |
|---|---|---|---|---|
| **Starter** | $1,500/mo ($18K/yr) | Up to 3 CSMs | HubSpot or Salesforce (1), Intercom | Email only |
| **Growth** | $3,000/mo ($36K/yr) | Up to 10 CSMs | HubSpot + Salesforce + Segment + Amplitude | Slack + email, shared CSM |
| **Enterprise** | Custom ($60K+/yr) | Unlimited | Full stack + custom connectors + SSO/SAML | Dedicated CSM, SLA |

**ACV for ICP sweet spot (Growth tier, 100–300 employee SaaS):** ~$36,000/year

---

## Integrations

Sentio connects to:
- **CRM:** Salesforce, HubSpot
- **Product analytics:** Amplitude, Mixpanel, Segment, Heap
- **Support:** Intercom, Zendesk, Freshdesk
- **NPS / CSAT:** Delighted, Medallia, Typeform
- **Communication:** Slack, Gmail, Outlook
- **Billing:** Stripe, Chargebee, Recurly
- **CS platforms:** Gainsight (import only), Totango (import only)

---

## Competitive Landscape

*(Sentio's positioning against alternatives — fictional framing only)*

| Competitor | How Sentio Positions |
|---|---|
| **Gainsight** | "Built for 500-person CS orgs. If you have fewer than 10 CSMs, Gainsight's implementation alone takes 6 months and a consultant." |
| **Totango** | "Solid product, but health scoring is still largely manual. Sentio's signal aggregation is automated from day one." |
| **ChurnZero** | "Great for SMB CS teams. Sentio targets mid-market companies where account complexity requires AI-driven scoring, not rule-based thresholds." |
| **Spreadsheets / manual** | "Not a competitor. That's the before state." |

---

## Sales Motion

- **Stage 1:** SDR outreach (personalized, trigger-based) → book discovery call (15 min)
- **Stage 2:** Discovery call with AE → qualify pain, confirm ICP, identify champion + economic buyer
- **Stage 3:** Demo (30 min, tailored to company's CS stack)
- **Stage 4:** Pilot (30 days, 1 CSM team, 10 accounts)
- **Stage 5:** Commercial proposal → champion → CFO → close
- **Cycle length:** 45–90 days for ICP accounts
- **Win rate:** ~22% on qualified opportunities *(illustrative)*

---

## Why This Company Works for the Demo

- **ICP is precise enough** to make fit scoring genuinely meaningful — a 300-person SaaS company gets an A, a 30-person services firm gets a C, a 1,500-person enterprise gets a B.
- **Two distinct buyers** (VP CS + CFO) make stakeholder classification interesting — the same lead brief generates different emails depending on title.
- **Research triggers are common** — Series B announcements and VP CS hires happen daily on LinkedIn, making Tavily results realistic and non-hardcoded.
- **The pain is universally understood** — every evaluator watching the Loom has experienced churn. No domain explanation needed.
- **Mirrors Docket's space** — Docket evaluators work in CS-adjacent product territory. An ICP story about VP CS and CFO will land with them directly.
