# API cURL Reference

Verified against current provider docs (June 2026). All commands read keys from
`api-tests/.env` — `source` it first:

```bash
set -a; . api-tests/.env; set +a
```

Smoke test (one credit-safe call per provider): `bash api-tests/smoke-test.sh`

---

## 1. Anthropic — Claude Messages

- **Endpoint:** `POST https://api.anthropic.com/v1/messages`
- **Auth:** header `x-api-key: $ANTHROPIC_API_KEY`
- **Required:** header `anthropic-version: 2023-06-01`
- **Build model:** `claude-sonnet-4-6` (smoke test uses `claude-haiku-4-5` to save cost)

```bash
curl -sS https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "max_tokens": 1024,
    "system": "You are the Research Agent. Respond only with JSON.",
    "messages": [{"role": "user", "content": "..."}]
  }'
```

## 2. Apollo — enrichment

**People match** (consumes 1 credit). Auth header is `X-Api-Key`.

```bash
curl -sS -X POST "https://api.apollo.io/api/v1/people/match" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: $APOLLO_API_KEY" \
  -d '{
    "email": "jane@meridian.io",
    "first_name": "Jane",
    "last_name": "Doe",
    "domain": "meridian.io",
    "reveal_personal_emails": false
  }'
```

**Organization enrichment** (GET, by domain):

```bash
curl -sS -X GET "https://api.apollo.io/api/v1/organizations/enrich?domain=meridian.io" \
  -H "Accept: application/json" \
  -H "X-Api-Key: $APOLLO_API_KEY"
```

> Cache both responses to local JSON keyed by email/domain — the cache-first lookup
> skips these calls on a hit (protects the free tier).

## 3. Tavily — research search

- **Endpoint:** `POST https://api.tavily.com/search`
- **Auth:** `Authorization: Bearer $TAVILY_API_KEY`
- Use `search_depth: "advanced"` for the research loop; `time_range` to bias recency.

```bash
curl -sS -X POST "https://api.tavily.com/search" \
  -H "Authorization: Bearer $TAVILY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Meridian Analytics VP Customer Success hire 2026",
    "search_depth": "advanced",
    "max_results": 5,
    "include_answer": false,
    "topic": "general",
    "time_range": "year"
  }'
```

## 4. HubSpot — CRM (`Authorization: Bearer $HUBSPOT_TOKEN`)

`HUBSPOT_TOKEN` can be a **Service Key** (recommended for single-account, data-only
integrations — no app overhead) or a private app token. Both authenticate the same
way and hit the same v3 endpoints below. Service Keys: Settings → Integrations →
Service Keys; grant only the CRM scopes the agent needs. (Service Keys don't support
webhooks — not needed here.)

Base host `https://api.hubapi.com`. v3 paths are current and supported (date-versioned
`/crm/objects/2026-03/...` also exists; v3 is fine).

**Upsert contact by email** (idempotent — no duplicates on repeat bookings):

```bash
curl -sS -X POST "https://api.hubapi.com/crm/v3/objects/contacts/batch/upsert" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": [{
      "idProperty": "email",
      "id": "jane@meridian.io",
      "properties": {"email": "jane@meridian.io", "firstname": "Jane", "lastname": "Doe", "jobtitle": "VP Customer Success"}
    }]
  }'
```

**Search existing deal by a property** (for upsert / dedupe):

```bash
curl -sS -X POST "https://api.hubapi.com/crm/v3/objects/deals/search" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filterGroups":[{"filters":[{"propertyName":"dealname","operator":"EQ","value":"Meridian Analytics — inbound"}]}]}'
```

**Create deal, set pipeline + stage, associate to contact** (associationTypeId `3` =
deal→contact, HubSpot-defined default):

```bash
curl -sS -X POST "https://api.hubapi.com/crm/v3/objects/deals" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "properties": {
      "dealname": "Meridian Analytics — inbound",
      "pipeline": "'"$HUBSPOT_PIPELINE_ID"'",
      "dealstage": "'"$HUBSPOT_STAGE_DEMO_REQUESTED"'"
    },
    "associations": [{
      "to": {"id": "<CONTACT_ID>"},
      "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}]
    }]
  }'
```

For a **disqualified** deal, set `"dealstage": "'"$HUBSPOT_STAGE_DISQUALIFIED"'"`
(fill `HUBSPOT_STAGE_DISQUALIFIED` in `.env` once that stage exists).

**Create note (mandatory hand-off / disqualification reason) and associate to the deal**
(associationTypeId `214` = note→deal default):

```bash
curl -sS -X POST "https://api.hubapi.com/crm/v3/objects/notes" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "properties": {
      "hs_timestamp": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'",
      "hs_note_body": "SDR hand-off: persona=Champion; why-now=VP CS hired 30d ago; ICP=A/72."
    },
    "associations": [{
      "to": {"id": "<DEAL_ID>"},
      "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 214}]
    }]
  }'
```

> Association type IDs (`3`, `214`) are HubSpot-defined defaults; if a call rejects them,
> list valid ones via `GET /crm/v4/associations/deals/contacts/labels`.

**List pipelines + stages** (to grab the disqualified stage id once created):

```bash
curl -sS -X GET "https://api.hubapi.com/crm/v3/pipelines/deals" \
  -H "Authorization: Bearer $HUBSPOT_TOKEN"
```
