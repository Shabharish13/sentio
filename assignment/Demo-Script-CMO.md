# 5-Minute CMO Demo Script

## Setup Before Recording

Run both apps:

```bash
# Terminal 1
cd backend
.venv/bin/python -m uvicorn app.main:app --port 8000

# Terminal 2
cd frontend
npm run dev
```

Open:

```text
http://localhost:3000
```

Suggested tabs:

- Sentio homepage or pricing page.
- `/demo` form.
- HubSpot deal/contact view, if you want to show CRM output.

## Demo Intention

Use this as a natural talk track, not a word-for-word script. The tone should be: "I understand the funnel problem, I built something practical to recover pipeline, and here is how your marketing and sales teams would use it."

## Talk Track

### 0:00-0:30 - Open Like a CSM

"If I were walking you through this as Sentio's CMO, I would start with the business problem, not the tech.

You already have demand coming in through demo requests and website chat. The leak is that the team does not know which hand-raisers deserve immediate attention, the chatbot is not qualifying serious buyers, and SDRs are left to follow up without enough context.

So I built an agentic marketing solution for Sentio that focuses on one outcome: turn inbound interest into cleaner, faster pipeline."

### 0:30-1:10 - Explain What Changed

"There are two front doors into this workflow: the demo form and Sage, the website chat assistant.

The important thing is that both paths end in the same place: a prioritized HubSpot record with the score, the reason for the score, the buyer context, and the recommended next action.

I also made one very intentional design choice. Lead priority is not left to the AI's opinion. The score is deterministic. It uses a 95-point model across headcount, industry, title, geography, and B2B/SaaS fit. AI is used where it is strongest: answering questions, summarizing research, and drafting human-sounding follow-up."

### 1:10-2:10 - Show a Strong Demo Request

Go to `/demo`.

Submit a strong-fit lead:

- Name: Marcus Wong
- Email: `marcus.wong@nimbuscs.io`
- Company: NimbusCS
- Job title: VP of Customer Success
- Company size: 201-500
- Problem: "We are seeing surprise churn and our CSMs do not trust our health scores."

Say while submitting:

"Here I am acting as a buyer who looks very similar to Sentio's ICP: a VP of Customer Success at a mid-market B2B SaaS company, with a clear churn-related pain.

When this form submits, the buyer sees exactly what you'd want them to see: a clean confirmation. Everything else — enrichment, scoring, research, email drafting, CRM — runs in the background."

After the confirmation screen appears, switch to HubSpot:

"This is what the SDR sees. The lead is not just marked 'hot' in a vague way. The score is explainable.

NimbusCS is in the 100-300 employee sweet spot, it is Computer Software, it is US-based, it has B2B/SaaS signals, and Marcus is the right champion persona. That produces an A-grade lead.

The SDR gets the fit score, the reason this account matters, a research-backed 'why now' signal, and a draft email — before they've ever opened the record for the first time."

Point out in HubSpot:

- Fit grade and score breakdown in the deal note.
- Research signal with source.
- Draft email.
- Deal stage: demo-requested.

### 2:10-2:45 - Show Why Bad-Fit Leads Do Not Waste Sales Time

Submit a poor-fit lead on the form (or reference the HubSpot disqualified stage if time is tight):

- Company size: 1-10
- Title: Student or Office Manager
- Problem: unrelated to churn/customer success

Say:

"The second thing I wanted to protect is Sales capacity.

If a lead scores below 30 points, it is a C-grade lead. They get the same 'request received' confirmation — we are not rude about it — but they do not go through research or email generation, and they do not land in the SDR's queue.

They are still logged. In HubSpot you can see exactly why this lead was filtered: which ICP dimension failed, what the score was, what the routing decision was. Marketing gets the audit trail, Sales does not get the noise."

Switch to HubSpot disqualified stage to show the deal note.

### 2:45-4:10 - Show Sage Turning Chat Into Pipeline

Open Sage on the pricing or demo page.

Ask:

```text
What are your pricing tiers?
```

Say after Sage answers:

"This is the website chat experience. A normal chatbot would answer this and stop. Sage answers from Sentio's knowledge base, then asks one qualifying question at a time.

That matters because the visitor does not feel like they are filling out a form, but Marketing still gets the signals needed to decide whether this is a real buyer."

Continue with:

```text
I'm VP of Customer Success at a 200-person B2B SaaS company. We're fighting surprise churn and evaluating tools this quarter.
```

If Sage asks for email, reply:

```text
marcus.wong@nimbuscs.io
```

Say:

"Now Sage has the signals we care about: right role, right company size, relevant pain, and an active evaluation timeline.

Notice that Sage asks for an email before claiming a handoff. That is important operationally because the system should not pretend a sales rep is following up unless it has a way to route the lead.

Once the email is captured, this chat lead goes through the same path as the form: enrichment, deterministic scoring, research, and HubSpot sync. So chat leads do not become second-class records. Sales gets the transcript and the same quality of context."

Optional escalation example if time allows:

```text
I need custom enterprise pricing, security review, and procurement support.
```

Say:

"If the visitor raises enterprise pricing, security, procurement, or asks for a human, Sage escalates instead of trying to bluff through an answer. That protects trust and gets the right buyer to the right person."

### 4:10-4:40 - Make the Guardrail Clear

"The reason I separated deterministic and probabilistic work is control.

The deterministic parts are the business rules: validation, scoring, grade thresholds, routing, CRM stage, and dedupe. A is 60-plus points, B is 30 to 59, and C is below 30.

The probabilistic parts are the parts where language helps: Sage's answer, research summarization, and the draft email. Those are constrained by the knowledge base, enrichment data, and source-backed research, so the system is designed not to invent company facts."

### 4:40-5:00 - Close With the CMO Outcome

"So the value to Sentio is straightforward.

High-fit demo requests get surfaced faster. Poor-fit leads stop consuming SDR time but remain auditable. Website chat becomes a qualification and handoff channel. And SDRs get a better first touch because the system gives them the score, the context, and a starting email.

If this were going into production, the next layer I would add is measurement: speed-to-lead, chat-to-demo conversion, SDR acceptance rate, and disqualification accuracy."

## Sage Chat Prompts for Recording

Use this clean booking path:

```text
What are your pricing tiers?
```

```text
I'm VP of Customer Success at a 200-person B2B SaaS company. We're fighting surprise churn and evaluating tools this quarter.
```

```text
marcus.wong@nimbuscs.io
```

Use this escalation path only if you have time:

```text
I need custom enterprise pricing, security review, and procurement support.
```

```text
marcus.wong@nimbuscs.io
```

Use this off-topic guardrail path only if you want to show safety:

```text
What is the gold price in Chennai today?
```

Expected response:

- Sage should avoid answering outside its domain.
- It should steer back to Sentio or ask for email only if the conversation is a real handoff case.

## Recording Tips

- Speak as if the CMO cares about pipeline quality, speed-to-lead, and SDR focus.
- Keep the screen on the product and CRM outputs; avoid explaining code.
- Use technical terms only when they support a business decision.
- If an API call is slow, say what business work is happening: enrichment, scoring, research, and CRM sync.
