# Case Study: CS Operations Efficiency

## How Capsule HR Standardized CS Playbooks and Saved 4 Hours Per CSM Per Week

> **Fictional illustrative results.** Capsule HR is an invented company. All outcomes described are illustrative examples of the kind of results Sentio is designed to produce — not guaranteed results.

---

## Company Profile

- **Company:** Capsule HR *(fictional)*
- **Industry:** B2B SaaS — HR technology / people analytics
- **Size:** ~350 employees
- **ARR at time of deployment:** ~$22M
- **CS team:** 14 CSMs, 1 CS Ops Director, 1 VP of Customer Success
- **Sentio tier:** Growth

---

## The Problem

Marcus, CS Ops Director at Capsule HR, had a team of 14 CSMs each managing 60–80 accounts. The CS team had grown from 4 to 14 in 18 months — fast enough that onboarding became inconsistent and playbook discipline eroded.

The operational symptoms:
- Each CSM had their own interpretation of when an account was "at risk." Some flagged accounts at the first support ticket. Others waited for an explicit churn signal.
- Health checks were done manually: each CSM pulled usage data from Amplitude, checked HubSpot for last contact date, reviewed Zendesk ticket history, and then made a judgment call. Average time: 30–45 minutes per account per month.
- With 70 accounts per CSM, doing manual health checks on the full book was impossible. Most CSMs only checked the accounts they were already worried about — which meant they were optimizing for accounts they knew were at risk, not finding the ones they didn't know about.
- NRR was 98% — technically positive, but below the board's 110% target. The VP of CS couldn't identify whether the gap was a retention problem, an expansion problem, or a CSM consistency problem.

Marcus was tasked with fixing the operational model without adding headcount.

---

## How Sentio Was Used

Capsule HR connected Sentio to HubSpot, Amplitude, and Zendesk over a half-day implementation session. The CS Ops team then spent two weeks configuring custom playbooks based on their internal escalation logic.

**Key configuration decisions:**
- Set custom health score thresholds based on Capsule HR's own historical churn patterns (accounts that churned had consistently dropped below 45 on product engagement, 90 days out)
- Built a "CSM variance" report: health score trends segmented by CSM to identify whether performance differences were skill-based or book-of-business-based
- Created a "silent at-risk" playbook: for accounts that hadn't had a support ticket in 90 days AND had declining product engagement — a pattern that manual checks almost always missed (no ticket = assumed healthy)

---

## What Changed

**For CSMs:**
Each CSM's daily task queue replaced the manual health check process. Instead of 30–45 minutes of pulling data per account, CSMs started the day with a prioritized list of 3–5 accounts to contact, with the reason pre-populated: "Product engagement down 40% vs. 30-day average. Last contact: 47 days ago. Suggested action: health check call."

Time saved: approximately 3–4 hours per CSM per week across the team. (Illustrative estimate based on time-tracking data before and after Sentio deployment.)

**For CS Ops:**
The CSM variance report revealed that 4 CSMs had significantly higher account health scores in their books than the other 10 — and those CSMs were doing something differently. Marcus ran a retrospective and discovered they were proactively scheduling QBRs at the 60-day-post-onboarding mark, regardless of health signal. That practice was formalized as a new standard playbook for the whole team.

**For the VP of CS:**
The renewal forecast dashboard let her see At-Risk ARR in aggregate for the first time. She could now go into a board meeting with a number: "$3.4M in at-risk ARR this quarter, $2.1M of which has an active recovery playbook running."

**Outcomes (illustrative):**

- CSM manual health check time: reduced from ~35 minutes/account/month to approximately 5–8 minutes (reviewing Sentio's pre-surfaced signals and confirming playbook action)
- "Silent at-risk" accounts detected in first 60 days of deployment: 18 accounts that manual review had categorized as healthy were flagged by Sentio — 12 were actioned, 9 retained at their next renewal
- NRR improvement: moved from 98% to 104% over the following two quarters (illustrative — multiple factors contributed, Sentio was one)
- Playbook consistency: variance between highest- and lowest-performing CSMs on account health scores narrowed by approximately 30%

**Marcus's reflection (illustrative quote):**
> "We didn't have a talent problem. We had a visibility problem. Once CSMs could see the same signals and act on the same playbook, the variance went away."

---

## Key Takeaway

The efficiency gain was real, but it wasn't the main benefit. The main benefit was consistency: when every CSM sees the same signals and follows the same playbook, the outcome is determined by account health — not by which CSM happened to own the account.

For CS Ops leaders, Sentio is an operational standardization tool as much as it is a churn prediction tool.
