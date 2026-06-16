# Sentio — Integrations

Sentio connects to your existing stack with no custom ETL. All integrations are configured through the Sentio UI — no engineering required for supported connectors.

---

## CRM

### Salesforce
- **What flows in:** Account details, contact records, opportunity stage, contract value, renewal dates, last activity date
- **What flows out:** Health score written back to Account object (custom field), playbook tasks created as Salesforce Tasks, at-risk flags added to Opportunity records
- **Available on:** Growth, Enterprise

### HubSpot
- **What flows in:** Company records, contacts, deal stage, last contact date, lifecycle stage
- **What flows out:** Health score written back to Company property, playbook tasks created as HubSpot Tasks, deal risk flags surfaced in deal view
- **Available on:** Starter (1 CRM only), Growth, Enterprise

---

## Product Analytics

### Amplitude
- **What flows in:** Event counts, DAU/MAU ratio, feature adoption flags, session frequency, last active date
- **Data cadence:** Updated every 4 hours
- **Available on:** Growth, Enterprise

### Mixpanel
- **What flows in:** Event tracks, user engagement metrics, funnel completion rates, last seen
- **Data cadence:** Updated every 4 hours
- **Available on:** Growth, Enterprise

### Segment
- **What flows in:** User events forwarded via Segment's existing pipeline — Sentio appears as a Segment destination. No separate integration required if Segment is already in use.
- **Available on:** Growth, Enterprise

### Heap
- **What flows in:** Auto-captured user interactions, session data, feature usage
- **Data cadence:** Daily batch
- **Available on:** Enterprise

---

## Customer Support

### Intercom
- **What flows in:** Open ticket count, ticket resolution time, conversation sentiment (via Intercom's built-in classification), escalation flags, CSAT scores
- **What flows out:** Sentio can trigger an Intercom message to a CSM when an account crosses a risk threshold (optional, configurable)
- **Available on:** Starter, Growth, Enterprise

### Zendesk
- **What flows in:** Ticket volume, ticket priority, resolution time, satisfaction scores, agent notes (sentiment analysis applied)
- **Available on:** Growth, Enterprise

### Freshdesk
- **What flows in:** Ticket count, status, priority, CSAT
- **Available on:** Growth, Enterprise

---

## NPS / CSAT

### Delighted
- **What flows in:** NPS scores per account, promoter/passive/detractor classification, verbatim responses (used for sentiment signal)
- **Available on:** Growth, Enterprise

### Medallia
- **What flows in:** Survey response data, score trends, flagged verbatim feedback
- **Available on:** Enterprise

### Typeform
- **What flows in:** Survey response data mapped to account via email — NPS or CSAT surveys sent via Typeform can feed directly into Sentio's scoring engine
- **Available on:** Growth, Enterprise

---

## Billing

### Stripe
- **What flows in:** Payment status (successful / failed / disputed), subscription status (active / paused / cancelled), plan tier, MRR per account
- **Signal used:** Payment failures and subscription pauses are high-weight negative signals in health scoring
- **Available on:** Growth, Enterprise

### Chargebee
- **What flows in:** Subscription lifecycle events, invoice status, plan changes, downgrade events
- **Available on:** Growth, Enterprise

### Recurly
- **What flows in:** Subscription events, billing failures, dunning status
- **Available on:** Growth, Enterprise

---

## Communication

### Slack
- **What flows out:** Playbook assignments and at-risk alerts can be posted to a designated Slack channel or sent as direct messages to the assigned CSM
- **Available on:** Growth, Enterprise

### Gmail / Outlook
- **What flows in:** Email open rates, last email sent date, response lag — tracked at the account level to measure engagement cadence
- **Note:** Sentio reads metadata only (open events, send timestamps). Email body content is not read.
- **Available on:** Growth, Enterprise

---

## CS Platform Imports

### Gainsight (import only)
- If your team is migrating from Gainsight, Sentio can import your historical account data and health score history to bootstrap the model. Ongoing two-way sync is not supported.

### Totango (import only)
- Historical account data and segment definitions can be imported during onboarding. Ongoing sync not supported.

---

## Custom Integrations

Enterprise tier customers can request custom connectors for internal data sources not covered by the native integration list. Scoped during the sales process; typical turnaround is 4–8 weeks for a custom connector depending on the data source's API quality.

REST API access (Growth and Enterprise) can also be used to push custom events into Sentio's scoring engine directly.

---

## Integration Setup Time

All native integrations are configured through the Sentio UI using OAuth or API key. No custom ETL, no data engineering work required for supported connectors. Typical full-stack setup (CRM + product analytics + support + billing) takes under a day for a technical admin or CS Ops lead.
