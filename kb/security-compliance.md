# Sentio — Security & Compliance

---

## SOC 2 Type II

Sentio is SOC 2 Type II certified. The audit covers the Security, Availability, and Confidentiality trust service criteria.

- **Report availability:** Customers on Growth and Enterprise tiers can request the full SOC 2 report under NDA during the security review process. Contact your AE or the Sentio security team at security@sentio.io.
- **Audit cadence:** Annual. Most recent audit completed Q1 2026.

---

## GDPR Compliance

Sentio is GDPR compliant. Key details:

- Sentio acts as a **data processor** on behalf of its customers (who are data controllers).
- A Data Processing Agreement (DPA) is available and included in all Growth and Enterprise contracts by default. Starter customers can request a DPA.
- **Data subject requests:** Sentio provides tooling for customers to fulfill data subject access and deletion requests within 30 days as required by GDPR Article 17.
- **Data retention:** Customer data is retained for the duration of the contract plus 90 days. Customers can request deletion at contract end.

---

## Data Residency

- **Default:** Data is stored and processed in the United States (AWS us-east-1).
- **EU data residency:** Available on Enterprise tier for customers requiring data to remain in the EU (AWS eu-central-1, Frankfurt). This must be selected at contract signing — migration between regions post-deployment is possible but involves a planned maintenance window.
- **Data in transit:** All data in transit is encrypted using TLS 1.2 or higher.
- **Data at rest:** All customer data encrypted at rest using AES-256.

---

## Authentication & Access Control

### SSO / SAML
- SAML 2.0 single sign-on is available on **Enterprise tier**.
- Supports Okta, Azure AD, and Google Workspace as identity providers.
- Available on Growth tier as an add-on (pricing available on request).

### Multi-Factor Authentication (MFA)
- MFA is enforced for all Sentio user accounts by default.
- Admins can enforce MFA via SSO provider on Enterprise tier.

### Role-Based Access Control (RBAC)
- **Admin:** Full platform access including integration configuration, playbook editing, and user management
- **CS Manager:** Full account view, playbook assignment, team performance reporting — cannot edit integrations
- **CSM:** Task queue, account health view, playbook execution — no admin or team reporting access
- **Read-only / Executive:** Dashboard and reporting access only — no task or playbook actions

---

## Subprocessors

Sentio uses a limited set of third-party subprocessors to deliver the service. Customers on Growth and Enterprise tiers can request the current subprocessor list. Sentio provides 30 days' notice of any new subprocessors added, allowing customers to object if they have a legitimate privacy concern.

Key subprocessors include:
- **AWS** — cloud infrastructure and data storage
- **Snowflake** — data warehouse for analytics processing
- **Anthropic** — AI model inference (health scoring narrative, anomaly explanation features)

---

## Penetration Testing

Sentio conducts an annual third-party penetration test. Summary reports are available to Enterprise customers upon request under NDA.

---

## Vulnerability Disclosure

Sentio maintains a responsible disclosure program. Security researchers can report vulnerabilities to security@sentio.io. We commit to acknowledging reports within 72 hours and providing a remediation timeline within 14 days for validated findings.

---

## Security Review Process

For customers with formal security review requirements (procurement, InfoSec, or legal), Sentio provides:

- SOC 2 Type II report (NDA required)
- DPA (included in contract)
- Subprocessor list
- Standard InfoSec questionnaire responses (CAIQ / SIG Lite — available within 5 business days)
- Penetration test summary (Enterprise only, NDA required)

Dedicated security review support is available for Enterprise prospects. Contact your AE to schedule a security review call.

---

## Incident Response

- Sentio maintains a documented incident response plan reviewed annually.
- **Breach notification:** Sentio will notify affected customers within 72 hours of discovering a confirmed data breach, consistent with GDPR Article 33 requirements.
- **Status page:** Sentio maintains a public status page at status.sentio.io for service availability incidents.
