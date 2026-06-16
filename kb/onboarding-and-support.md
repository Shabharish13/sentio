# Sentio — Onboarding & Support

---

## Time to Value

Sentio is designed to connect to your existing stack and surface meaningful signals within 24 hours of setup — not in 6 weeks after a professional services engagement.

**Typical onboarding timeline:**
- **Day 1:** Connect your first integration (CRM + product analytics). Sentio begins ingesting data and computing initial health scores.
- **Day 2–3:** Review initial health scores with your CS Ops lead or VP CS. Confirm thresholds match your team's expectations. Adjust weighting if needed.
- **Day 5–7:** Configure playbooks. Sentio ships with 5 pre-built playbook templates; most teams customize 2–3 to match their own escalation logic.
- **Day 10–14:** CSM team onboarding — a 90-minute team walkthrough (live or recorded). Task queue is live. CSMs start working from Sentio daily.
- **Week 3–4:** First review with your Sentio shared CSM (Growth tier). Discuss what signals surfaced, what playbooks fired, what's working.

For most Growth-tier customers, the "I'm getting value from this" moment happens in the first week — typically when Sentio surfaces an at-risk account the team wasn't watching.

---

## What "No Custom ETL" Actually Means

Every native integration in Sentio connects via OAuth or API key through the Sentio UI. You are not writing SQL, configuring data pipelines, or asking your engineering team to build a connector. Setup is done by a CS Ops lead or technical admin — not by engineers.

Exceptions:
- **Custom events via REST API:** If you have internal data that isn't covered by a native integration, your team can push events to Sentio's API. This requires basic engineering work (a few hours, not weeks).
- **Custom connectors (Enterprise):** For non-standard data sources with no native Sentio integration, Enterprise customers can request a custom connector build. Scoped case by case.

---

## Onboarding by Tier

### Starter
- **Onboarding format:** Self-serve with documentation + 2 onboarding video calls (45 minutes each — integration setup, team walkthrough)
- **Documentation:** Full help center access
- **Kickoff SLA:** Within 5 business days of contract signing

### Growth
- **Onboarding format:** Guided onboarding with a dedicated onboarding specialist for the first 30 days
  - Session 1: Integration setup and data validation (60 min)
  - Session 2: Health score threshold review and customization (45 min)
  - Session 3: Playbook configuration (60 min)
  - Session 4: CSM team walkthrough (90 min)
- **Shared CSM:** Assigned after onboarding; quarterly check-ins, office hours bi-weekly
- **Kickoff SLA:** Within 3 business days of contract signing

### Enterprise
- **Onboarding format:** Dedicated implementation lead for 60 days. Custom onboarding plan scoped to team size, integration complexity, and timeline.
- **Dedicated CSM:** Named CSM assigned for the contract duration. Monthly business reviews. Executive sponsor alignment.
- **Kickoff SLA:** Within 1 business day of contract signing

---

## Support

### Starter — Email Only
- Email support at support@sentio.io
- Response time: within 2 business days for standard issues
- Help center: full access (articles, video walkthroughs, integration guides)

### Growth — Slack + Email
- Shared Slack channel with Sentio support team
- Response time: within 4 business hours during business hours (9am–6pm ET, Monday–Friday)
- Priority handling for playbook and integration issues
- Help center: full access

### Enterprise — Dedicated CSM + SLA
- Named CSM as primary point of contact for all support and strategic questions
- Critical issue SLA: 4-hour response, 24-hour resolution target
- 24/7 emergency support for production-down scenarios
- Quarterly business reviews with Sentio leadership

---

## Help Center

All tiers have access to Sentio's full help center, which includes:
- Step-by-step integration setup guides (with screenshots)
- Playbook configuration walkthroughs
- Health score interpretation guide
- CSM onboarding guide (shareable with your team)
- API documentation (Growth and Enterprise)
- Video walkthroughs for all major features

---

## Frequently Asked Questions on Onboarding

**Do we need to involve our engineering team?**
Not for standard onboarding. CRM, product analytics, support, and billing integrations are all configured through the Sentio UI without engineering involvement. If you want to push custom events via the API, that requires engineering time — typically a few hours for a simple event push.

**How long until we see our first health scores?**
Health scores appear within a few hours of your first integration connecting, assuming the integration has historical data to pull. If you're connecting Amplitude or Mixpanel, Sentio will backfill up to 90 days of historical event data on first sync.

**What if we don't have a CS Ops person to manage the setup?**
Most VP CS or CS Manager roles can own the setup without a dedicated CS Ops function. The average setup time for a Growth-tier customer connecting 3 integrations is about 4–6 hours of admin time spread across 2 days.

**Can we migrate from Gainsight or Totango?**
Yes. Sentio can import your historical account data and health score history from Gainsight or Totango to give the model a baseline. This is handled during the dedicated onboarding sessions.

**What if we need to pause or cancel?**
Starter (monthly billing): cancel anytime with 30 days' notice. Annual plans: cancellation at contract end with 60 days' notice. No mid-term cancellation for annual contracts except in circumstances covered by the contract's termination clause.
