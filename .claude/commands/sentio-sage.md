---
description: Ask Sentio's Sage chatbot a question (RAG-grounded; escalates if off-topic)
---

The visitor's question is: **$ARGUMENTS**

Run the Sage agent against the KB and show its answer:

```
cd backend && .venv/Scripts/python.exe -m scripts.cli sage "$ARGUMENTS" --page /pricing
```

Then present, clearly:
- whether it **escalated** (off-topic / low confidence) or answered,
- which **KB sources** it cited,
- the reply itself.

If the output says the KB index is missing, first run
`.venv/Scripts/python.exe -m scripts.build_kb_index` (from `backend/`), then retry.
The answer uses the real LLM chain (OpenAI → Anthropic → logged-in `claude` CLI), so it may take a few seconds.
