# Sentio — FAQ & Objection Handling

---

## "We already use Gainsight."

**Short answer:** Gainsight is built for enterprise CS orgs with 20+ CSMs and a dedicated CS Ops team to configure and maintain it. If you're under 500 employees, there's a good chance Gainsight is either underused or took 6+ months and a consultant to implement.

**Longer answer:** Gainsight is a powerful platform — for large teams. The implementation alone for a mid-market company typically takes 3–6 months and requires a professional services engagement. Many mid-market companies that buy Gainsight end up using 20–30% of its features because the rest require configuration work they don't have the CS Ops bandwidth for.

Sentio is designed for companies with 5–30 CSMs that need health scoring and playbook automation without the enterprise overhead. If your team is already on Gainsight and getting value from it, Sentio probably isn't the right fit. If you're on Gainsight and it feels like you're maintaining a platform instead of using one, that's a conversation worth having.

---

## "We already use ChurnZero."

**Short answer:** ChurnZero is a solid tool for SMB CS teams. Sentio is designed for mid-market companies where the account complexity and ARR concentration require AI-driven scoring rather than rule-based thresholds.

**Longer answer:** ChurnZero uses rule-based health scoring — you define the rules (e.g., "if no login in 30 days, score = red"), and the platform executes them. That works well at scale when accounts are relatively simple and consistent. For mid-market accounts with complex stakeholder maps, multi-product footprints, and higher ACV, rule-based scoring tends to generate false positives and miss signals that don't fit the rules.

Sentio's scoring model learns from the shape of how accounts behave before they churn — not from rules you predefine. That's the difference between a threshold and a prediction.

---

## "We're too small for a tool like this."

**The honest answer:** If you have fewer than 5 CSMs or fewer than 100 accounts, the ROI math probably doesn't work for Sentio yet. A spreadsheet and a weekly standup can cover that ground.

Sentio's sweet spot is companies where:
- Each CSM manages 40+ accounts
- The CS team can't manually monitor every account every week
- Churn is starting to compound as the customer base scales

If you're at 3 CSMs managing 30 accounts each, revisit this conversation when you're at 6 CSMs and 80 accounts. We'd rather tell you the timing isn't right than have you buy something you won't get full value from.

---

## "How long does implementation take?"

**Short answer:** Most Growth-tier customers are live with health scores within 24 hours of starting setup. Full team adoption (CSMs working from the task queue daily) typically happens within 2 weeks.

**Longer answer:** Sentio's implementation timeline depends on how many integrations you're connecting and how much playbook customization your team wants to do before going live. The integrations themselves are fast — OAuth or API key, configured through the Sentio UI, no engineering required. Health scores appear within hours of your first data sync.

The slower part is usually playbook configuration and team onboarding — getting 10 CSMs comfortable with a new workflow takes a few days of practice. We structure onboarding to minimize that friction with a 90-minute team walkthrough session.

Compare this to Gainsight or Totango, where implementation is typically a 3–6 month project.

---

## "What makes this different from building a dashboard in Tableau/Looker?"

**Short answer:** A dashboard shows you what happened. Sentio tells you what's likely to happen next and what to do about it.

**Longer answer:** A BI dashboard can visualize product usage, support tickets, and NPS scores — if someone configures and maintains it. The problems are: (1) someone has to build and maintain the data model, (2) CSMs still have to interpret the data and decide who to call, and (3) there's no playbook — the dashboard tells you an account is unhealthy but doesn't trigger an action.

Sentio handles all three: the signal aggregation is automatic, the scoring is predictive (not descriptive), and the playbook fires automatically when a threshold is crossed. A CSM's job is to execute the recommended action — not to decide which accounts need attention today.

---

## "Do we need an engineer to set this up?"

No. All native integrations are configured through the Sentio UI using OAuth or API key. A CS Ops lead or technical admin can complete the setup without engineering involvement.

The only scenario that requires engineering time is pushing custom events to Sentio via the REST API — for internal data not covered by a native integration. That's typically a few hours of engineering work, not a project.

---

## "What if our health scoring data is wrong?"

**Short answer:** Sentio shows you exactly which signals contributed to each account's health score and how much weight each signal carries. If a score looks wrong, you can trace it and adjust.

**Longer answer:** Health scoring is only as good as the signals you feed it. Common reasons a score looks wrong:

1. **Missing integration:** If you haven't connected your billing system, Sentio can't factor in payment failures. Connecting more integrations gives the model more signal.
2. **Threshold mismatch:** Sentio's default thresholds are calibrated for typical mid-market SaaS patterns. Your company may have a different baseline. You can adjust thresholds in the configuration UI.
3. **Lagging data:** If an integration is syncing once per day and an event happened this morning, the score won't reflect it until the next sync.

Sentio makes the scoring logic transparent — you can see the score breakdown per account and understand why a score is what it is. It's not a black box.

---

## "We don't have budget for this right now."

**Short answer:** Understood — timing matters. Worth doing the retention math before the conversation ends.

**Longer answer:** The question is what the cost of not having it is. If your current churn rate is 8% on $15M ARR, you're losing $1.2M/year to churn. If Sentio helps you retain 15% of what would have churned — a conservative estimate for teams that execute the playbooks consistently — that's $180,000 in retained ARR against a $36,000/year investment. The payback is roughly 2 months.

If the budget timing genuinely doesn't work right now, we can talk about a pilot program or a delayed start date. We'd rather get the timing right than push you into a contract that doesn't fit.

---

## "How does Sentio handle security and data privacy?"

Sentio is SOC 2 Type II certified and GDPR compliant. Data in transit is encrypted via TLS 1.2+, data at rest via AES-256. EU data residency is available on the Enterprise tier. A full Data Processing Agreement is included in all contracts.

See `security-compliance.md` for the complete security overview.

---

## "What integrations do you support?"

Sentio connects natively to Salesforce, HubSpot, Amplitude, Mixpanel, Segment, Heap, Intercom, Zendesk, Freshdesk, Delighted, Medallia, Typeform, Stripe, Chargebee, Recurly, Slack, and Gmail/Outlook.

See `integrations.md` for the full list with setup details.

---

## "Can I see a demo?"

Yes — the best way to evaluate Sentio is to see it working with your actual data in a 30-minute tailored demo. Your AE will connect the demo environment to a sample of your integration data (with your permission) so you see health scores for your real accounts, not a fictional dataset.

Request a demo at sentio.io/demo or ask to schedule one through the chat on this page.
