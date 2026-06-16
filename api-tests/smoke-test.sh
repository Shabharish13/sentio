#!/usr/bin/env bash
# Connectivity smoke test for all four provider APIs.
# Loads keys from api-tests/.env (gitignored). Prints HTTP status + body per provider.
# Credit-safe: Apollo uses the free /auth/health endpoint; Anthropic uses cheap Haiku;
# Tavily uses 1 search credit; HubSpot read is free.
#
# Run:  bash api-tests/smoke-test.sh

set -u
DIR="$(cd "$(dirname "$0")" && pwd)"

# Load .env without echoing values
set -a
# shellcheck disable=SC1091
[ -f "$DIR/.env" ] && . "$DIR/.env"
set +a

pass=0; fail=0
hr() { printf '%s\n' "------------------------------------------------------------"; }

check() { # name  required_var_value  curl-args...
  local name="$1"; local key="$2"; shift 2
  hr; printf '▶ %s\n' "$name"
  if [ -z "${key}" ]; then
    printf '  SKIPPED — key not set in api-tests/.env\n'; fail=$((fail+1)); return
  fi
  local body status
  body="$(curl -sS -w $'\n%{http_code}' "$@" 2>&1)"
  status="${body##*$'\n'}"; body="${body%$'\n'*}"
  printf '  HTTP %s\n' "$status"
  printf '  %.400s\n' "$body"
  case "$status" in
    2*) printf '  ✓ OK\n'; pass=$((pass+1));;
    *)  printf '  ✗ FAILED\n'; fail=$((fail+1));;
  esac
}

# 1) Anthropic — cheap Haiku ping
check "Anthropic (Claude Messages)" "${ANTHROPIC_API_KEY:-}" \
  https://api.anthropic.com/v1/messages \
  -H "x-api-key: ${ANTHROPIC_API_KEY:-}" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-haiku-4-5","max_tokens":16,"messages":[{"role":"user","content":"Reply with the single word: ok"}]}'

# 1b) OpenAI — list models (auth only; 200 even with no spend quota)
check "OpenAI (list models, auth only)" "${OPENAI_API_KEY:-}" \
  -X GET "https://api.openai.com/v1/models" \
  -H "Authorization: Bearer ${OPENAI_API_KEY:-}"

# 2) Apollo — credit-free auth health
check "Apollo (auth/health, 0 credits)" "${APOLLO_API_KEY:-}" \
  -X GET "https://api.apollo.io/v1/auth/health" \
  -H "Content-Type: application/json" \
  -H "Cache-Control: no-cache" \
  -H "X-Api-Key: ${APOLLO_API_KEY:-}"

# 3) Tavily — minimal search (1 credit)
check "Tavily (search, 1 credit)" "${TAVILY_API_KEY:-}" \
  -X POST "https://api.tavily.com/search" \
  -H "Authorization: Bearer ${TAVILY_API_KEY:-}" \
  -H "Content-Type: application/json" \
  -d '{"query":"Sentio API connectivity test","max_results":1,"search_depth":"basic"}'

# 4) HubSpot — read one contact (free; needs crm.objects.contacts.read scope)
check "HubSpot (list contacts)" "${HUBSPOT_TOKEN:-}" \
  -X GET "https://api.hubapi.com/crm/v3/objects/contacts?limit=1" \
  -H "Authorization: Bearer ${HUBSPOT_TOKEN:-}"

hr
printf 'RESULT: %d passed, %d failed/skipped\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
