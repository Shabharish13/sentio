# Iteration Log — what broke and how it was fixed

Evidence of testing → finding real issues → fixing them, across the build. Each item
was caught by actually running things (live API calls, real embedder, code review), not
by first-draft guesswork.

- **HubSpot "pipeline ID" was actually the portal ID.** The docs recorded pipeline
  `246500414`. The live `GET /crm/v3/pipelines/deals` revealed that is the *portal* id —
  the real deal pipeline is `default`, and the disqualified stage is `3840698071`.
  Corrected across `.env`, CLAUDE.md, the design doc, and the prompts.

- **Research agent silently dropped prose-wrapped JSON.** The first-brace/last-brace
  extraction failed when the LLM added preamble containing a `{` (e.g. "Based on {record},
  here is: {...}"). Switched to a `json.JSONDecoder().raw_decode` scan for the first valid
  JSON object; added a regression test that failed before and passes after.

- **Sage escalated *everything*.** The `sage_agent.md` prompt's 0.75 cosine threshold
  assumed a different embedder. Measured against the real KB with all-MiniLM-L6-v2:
  on-topic queries score ~0.52–0.55, off-topic ~0.12–0.22. Recalibrated the runtime
  threshold to **0.35** (validated live: on-topic answers, off-topic escalates) and
  updated the prompt to match.

- **The OpenAI key has no quota.** The Docket-provided key authenticates (lists models)
  but returns `429 insufficient_quota` on completions. So the LLM layer was made an
  ordered fallback chain — **OpenAI → Anthropic → logged-in `claude` CLI** — that catches
  provider errors and falls through. Proven live: OpenAI 429 → the CLI answered `5`.

- **Apollo cache-first verified.** Confirmed the second enrichment of the same email
  serves from the local JSON cache with zero API calls, protecting the 50-credit/month
  free tier. The connectivity smoke test uses Apollo's credit-free `/v1/auth/health`.

- **Windows venv + Store-stub Python.** Git Bash's `python` hit the Windows Store stub
  (exit 49); the venv was created via the `py -3` launcher. Tests run through
  `.venv/Scripts/python.exe` throughout.
