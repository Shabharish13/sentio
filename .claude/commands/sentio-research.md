---
description: Run the Research agent — enriched record → "why now" signal (LLM + Tavily)
---

The user described a company to research: **$ARGUMENTS**

Translate it into flags and run the Research agent (it mines the record first, then may
run up to 3 Tavily searches):

```
--company "..." (required)  --contact "..."  --title "..."
--industry "..."  --headcount N  --tech Name1 Name2  --funding "Series B 2026"
```

Run:

```
cd backend && .venv/Scripts/python.exe -m scripts.cli research <flags>
```

Then show the `signal_type`, the `top_signal` sentence, and the `source_url`. Uses the
real LLM chain + Tavily, so it may take a few seconds and consume a Tavily credit if it searches.
