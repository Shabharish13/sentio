---
description: Score a lead's ICP fit + intent + routing (deterministic, no LLM)
---

The user described a lead: **$ARGUMENTS**

Translate that description into flags for the scoring CLI and run it. Available flags
(omit any unknown field):

```
--headcount N  --industry "..."  --title "..."  --country "..."
--tech Name1 Name2  --b2b  --problem "..."  --how-heard "..."
```

Run:

```
cd backend && .venv/Scripts/python.exe -m scripts.cli score <flags>
```

Then show the fit **grade/score**, the per-dimension **breakdown**, the **intent** score/band,
the **route** (qualified / disqualified), and any **disqualification reason**. This is
fully deterministic — no LLM, no network.
