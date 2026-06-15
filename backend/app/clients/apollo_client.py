from __future__ import annotations

import json
from pathlib import Path

import httpx

from app.config import REPO_ROOT, get_settings

DEFAULT_CACHE_DIR = REPO_ROOT / "cache" / "apollo"


class ApolloClient:
    """Apollo enrichment with cache-first lookup.

    Responses are cached to local JSON keyed by email (people) or domain (org);
    a cache hit skips the API call entirely to protect the free-tier credit limit.
    """

    BASE = "https://api.apollo.io/api/v1"

    def __init__(
        self,
        http: httpx.Client | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        self._key = get_settings().apollo_api_key
        self._http = http or httpx.Client(timeout=30)
        self._cache = cache_dir or DEFAULT_CACHE_DIR
        self._cache.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, kind: str, key: str) -> Path:
        safe = key.lower().replace("/", "_").replace("@", "_at_")
        return self._cache / f"{kind}_{safe}.json"

    def _read_cache(self, path: Path) -> dict | None:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return None

    def _write_cache(self, path: Path, data: dict) -> None:
        path.write_text(json.dumps(data), encoding="utf-8")

    def enrich_person(self, email: str, **fields: str) -> dict:
        path = self._cache_path("person", email)
        cached = self._read_cache(path)
        if cached is not None:
            return cached
        resp = self._http.post(
            f"{self.BASE}/people/match",
            headers={"X-Api-Key": self._key, "Content-Type": "application/json"},
            json={"email": email, **fields},
        )
        resp.raise_for_status()
        data = resp.json()
        self._write_cache(path, data)
        return data

    def enrich_organization(self, domain: str) -> dict:
        path = self._cache_path("org", domain)
        cached = self._read_cache(path)
        if cached is not None:
            return cached
        resp = self._http.get(
            f"{self.BASE}/organizations/enrich",
            params={"domain": domain},
            headers={"X-Api-Key": self._key, "Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        self._write_cache(path, data)
        return data
