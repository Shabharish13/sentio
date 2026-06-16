// All user-facing copy for the Sentio marketing site, lifted verbatim from
// website-copy.md. Kept in one module so pages stay presentational.

export const brand = {
  name: "Sentio",
  tagline: "See churn before your customers do.",
  category: "Customer Health Intelligence for B2B SaaS",
  valueProp:
    "Sentio gives CS teams a 60–90 day warning before an account is likely to churn — with a recommended action attached, not just a red flag.",
  disclaimer:
    "Sentio is a fictional company created for a take-home demo. All outcomes shown are illustrative.",
};

export const nav = {
  links: [
    { label: "Home", href: "/" },
    { label: "Product", href: "/product" },
    { label: "Pricing", href: "/pricing" },
    { label: "Case Studies", href: "/case-studies" },
  ],
  cta: { label: "Request a demo", href: "/demo" },
};

export const home = {
  hero: {
    eyebrow: "Customer Health Intelligence for B2B SaaS",
    headline: "See churn before your customers do.",
    subhead: brand.valueProp,
    primary: { label: "Request a demo", href: "/demo" },
    secondary: { label: "See pricing", href: "/pricing" },
  },
  problems: {
    heading: "Churn doesn't happen overnight. You just find out too late.",
    subhead: "Three failures quietly erode retention. Sentio fixes all three.",
    cards: [
      {
        title: "Blind spots",
        body: "CS teams manage 50–150 accounts each and can't monitor every signal manually. Sentio aggregates signals no human can track at scale.",
      },
      {
        title: "Reactive CS",
        body: "Most teams learn about churn risk from the customer, not before. Sentio inverts that — the CSM reaches out before the customer complains.",
      },
      {
        title: "Inconsistent playbooks",
        body: "Different CSMs handle risk differently. Sentio standardizes escalation logic so the best-performing response becomes the default.",
      },
    ],
  },
  features: {
    heading: "One health score. Every signal. A recommended next move.",
    cards: [
      {
        title: "Unified health score",
        body: "One real-time score per account, synthesized from product usage, support tickets, NPS/CSAT, billing events, and stakeholder engagement.",
      },
      {
        title: "60–90 day churn warning",
        body: "Risk thresholds surface accounts well before renewal — enough runway to actually change the outcome.",
      },
      {
        title: "Recommended playbooks",
        body: "When health crosses a threshold, Sentio surfaces a recommended action (exec outreach, discount, onboarding re-engagement) and assigns it to the right CSM.",
      },
      {
        title: "Connects in under a day",
        body: "No custom ETL. Sentio reads from the tools you already run and starts scoring immediately.",
      },
    ],
  },
  socialProof: {
    heading: "Results teams see with Sentio",
    stats: [
      {
        metric: "9 of 12",
        label: "at-risk accounts retained",
        headline: "Caught 12 at-risk accounts 60 days before renewal",
        attribution: "200-person B2B SaaS · VP of Customer Success",
      },
      {
        metric: "4 hrs/wk",
        label: "saved per CSM",
        headline: "Cut manual health-check time by 4 hours/week per rep",
        attribution: "350-person SaaS · CS Ops Director",
      },
    ],
  },
  integrations: {
    heading: "Connects to the stack you already run",
    subhead:
      "No custom ETL. Sentio reads from your existing tools and starts scoring in under a day.",
    tools: [
      "Salesforce", "HubSpot", "Amplitude", "Mixpanel", "Segment", "Heap",
      "Intercom", "Zendesk", "Freshdesk", "Delighted", "Medallia", "Typeform",
      "Slack", "Gmail", "Outlook", "Stripe", "Chargebee", "Recurly",
    ],
  },
  ctaBand: {
    heading: "See which accounts are at risk — before they churn.",
    subhead: "A 15-minute walkthrough on your own CS stack.",
    cta: { label: "Request a demo", href: "/demo" },
  },
};

export const product = {
  hero: {
    headline: "The intelligence layer for customer retention",
    subhead:
      "Sentio turns the signals scattered across your tools into a single health score — and a recommended action — for every account.",
  },
  howItWorks: [
    {
      step: "1",
      title: "Connect your stack",
      body: "Point Sentio at the tools you already use — CRM, product analytics, support, NPS, billing. No custom ETL, live in under a day.",
    },
    {
      step: "2",
      title: "Score every account",
      body: "Sentio synthesizes usage, tickets, sentiment, billing, and engagement into a single real-time health score per account.",
    },
    {
      step: "3",
      title: "Act before churn",
      body: "When a score crosses a risk threshold, Sentio surfaces a recommended playbook and assigns it to the right CSM automatically.",
    },
  ],
  integrationsHeading: "Integrations",
  integrationsSubhead:
    "Every integration feeds Sentio's health scoring engine. Connect what you have today; add more anytime.",
  integrationCategories: [
    { category: "CRM", tools: ["Salesforce", "HubSpot"] },
    { category: "Product analytics", tools: ["Amplitude", "Mixpanel", "Segment", "Heap"] },
    { category: "Support", tools: ["Intercom", "Zendesk", "Freshdesk"] },
    { category: "NPS / CSAT", tools: ["Delighted", "Medallia", "Typeform"] },
    { category: "Communication", tools: ["Slack", "Gmail", "Outlook"] },
    { category: "Billing", tools: ["Stripe", "Chargebee", "Recurly"] },
  ],
  ctaBand: {
    heading: "Ready to see it on your own accounts?",
    cta: { label: "Request a demo", href: "/demo" },
  },
};

export const pricing = {
  hero: {
    headline: "Pricing that scales with your CS team",
    subhead:
      "Every plan includes the full health-scoring engine. You only pay for seats and integration depth.",
  },
  plans: [
    {
      name: "Starter",
      price: "$1,500 /mo",
      annual: "$18K/yr",
      blurb: "For early CS teams putting structure around retention for the first time.",
      seats: "Up to 3 CSMs",
      integrations: "HubSpot or Salesforce (1) + Intercom",
      support: "Email support",
      cta: "Start with Starter",
      popular: false,
    },
    {
      name: "Growth",
      price: "$3,000 /mo",
      annual: "$36K/yr",
      blurb: "The sweet spot for 100–300 person SaaS teams scaling NRR.",
      seats: "Up to 10 CSMs",
      integrations: "HubSpot + Salesforce + Segment + Amplitude",
      support: "Slack + email, shared CSM",
      cta: "Request a demo",
      popular: true,
    },
    {
      name: "Enterprise",
      price: "Custom",
      annual: "$60K+/yr",
      blurb: "For complex orgs needing custom connectors, SSO, and a dedicated CSM.",
      seats: "Unlimited CSMs",
      integrations: "Full stack + custom connectors + SSO/SAML",
      support: "Dedicated CSM, SLA",
      cta: "Talk to sales",
      popular: false,
    },
  ],
  belowPlans: "Not sure which plan fits? The assistant in the corner can help — or just book a demo.",
  faq: [
    {
      q: "What triggers an upgrade?",
      a: "Most teams move from Starter to Growth when they add a fourth CSM or need more than one CRM/analytics integration. Growth to Enterprise is usually driven by SSO/SAML, custom connectors, or an SLA requirement.",
    },
    {
      q: "Is there an annual discount?",
      a: "Yes — annual pricing is shown above (roughly two months free versus monthly). Talk to us for multi-year terms.",
    },
    {
      q: "How long does onboarding take?",
      a: "Sentio connects to your existing stack in under a day. There's no custom ETL to build.",
    },
  ],
};

export const caseStudies = {
  hero: {
    headline: "Customer stories",
    subhead:
      "How mid-market SaaS teams turned scattered signals into retention they could act on.",
    note: brand.disclaimer,
  },
  stories: [
    {
      headline: "Caught 12 at-risk accounts 60 days before renewal",
      metric: "9 of 12",
      metricLabel: "at-risk accounts retained",
      attribution: "200-person B2B SaaS · VP of Customer Success",
      body: "Using Sentio's health scoring, the CS team flagged 12 accounts trending toward churn two months ahead of their renewal dates — and ran the recommended save playbook on each. They retained 9 of the 12.",
      tag: "Fictional illustrative results",
    },
    {
      headline: "Cut manual health-check time by 4 hours/week per rep",
      metric: "4 hrs/wk",
      metricLabel: "saved per CSM",
      attribution: "350-person SaaS · CS Ops Director",
      body: "Sentio replaced the patchwork of dashboards CSMs checked every morning with a single prioritized view, and standardized escalation playbooks across the whole team.",
      tag: "Fictional illustrative results",
    },
  ],
  ctaBand: {
    heading: "Want results like these on your accounts?",
    cta: { label: "Request a demo", href: "/demo" },
  },
};

export const demoPage = {
  pitch: {
    headline: "See Sentio on your accounts",
    subhead:
      "Tell us a little about your team and we'll tailor a 15-minute walkthrough to your CS stack — and show you exactly which accounts would surface as at-risk today.",
    bullets: [
      "A live look at health scoring on real account patterns",
      "How recommended playbooks route to the right CSM",
      "Connects to your existing tools in under a day",
    ],
  },
  companySizes: ["1–10", "11–50", "51–200", "201–500", "500+"],
  howHeard: [
    "Google search",
    "LinkedIn",
    "Referral / word of mouth",
    "Industry event",
    "Blog / content",
    "Other",
  ],
  submit: "Request my demo",
  submitting: "Processing…",
  submitCaption:
    "On submit, our inbound pipeline enriches, scores, and routes your request automatically.",
  errorFallback: "Something went wrong. Please try again.",
};

export const widget = {
  greeting:
    "Hi! I'm Sentio's assistant. I can answer questions about how we predict churn, what's included in each plan, and whether we're a fit for your team. What brought you in today?",
  headerTitle: "Sentio assistant",
  headerStatus: "Typically replies instantly",
  inputPlaceholder: "Ask about pricing, fit, security…",
  send: "Send",
  launcherOpen: "Chat with us",
  launcherClose: "Close",
  typing: "typing…",
  connectionError:
    "Sorry — I'm having trouble connecting right now. Please try the demo form and our team will follow up.",
};

export const footer = {
  tagline: `${brand.name} — ${brand.tagline}`,
  links: [
    { label: "Home", href: "/" },
    { label: "Product", href: "/product" },
    { label: "Pricing", href: "/pricing" },
    { label: "Case Studies", href: "/case-studies" },
    { label: "Request a demo", href: "/demo" },
  ],
  disclaimer: brand.disclaimer,
};

// Demo-form size labels use en-dashes for display; the backend scoring bands use
// hyphens (see app/pipeline/adapter.py _SIZE_BAND_HEADCOUNT). Map before posting.
export const SIZE_TO_BAND: Record<string, string> = {
  "1–10": "1-10",
  "11–50": "11-50",
  "51–200": "51-200",
  "201–500": "201-500",
  "500+": "500+",
};
