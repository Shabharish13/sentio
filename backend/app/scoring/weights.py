from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


@lru_cache
def load_headcount_bands() -> list[tuple[int, int, int]]:
    with (DATA_DIR / "headcount.csv").open(encoding="utf-8") as f:
        return [(int(r["min"]), int(r["max"]), int(r["points"])) for r in csv.DictReader(f)]


@lru_cache
def load_industry() -> dict[tuple[str, str], int]:
    """Key: (industry_lower, condition). condition is "" normally, or
    "saas"/"nonsaas" for the Financial Services disambiguation rows."""
    out: dict[tuple[str, str], int] = {}
    with (DATA_DIR / "industry.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[(r["industry"].strip().lower(), r["condition"].strip().lower())] = int(r["points"])
    return out


@lru_cache
def load_titles() -> list[tuple[int, tuple[str, ...], int, str]]:
    rows: list[tuple[int, tuple[str, ...], int, str]] = []
    with (DATA_DIR / "title.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            kws = tuple(k.strip().lower() for k in r["keywords"].split("|") if k.strip())
            rows.append((int(r["priority"]), kws, int(r["points"]), r["stakeholder"].strip()))
    rows.sort(key=lambda x: x[0])
    return rows


@lru_cache
def load_geography() -> dict[str, int]:
    with (DATA_DIR / "geography.csv").open(encoding="utf-8") as f:
        return {r["country"].strip().lower(): int(r["points"]) for r in csv.DictReader(f)}


@lru_cache
def load_business_model() -> dict[str, int]:
    with (DATA_DIR / "business_model.csv").open(encoding="utf-8") as f:
        return {r["signal"].strip().lower(): int(r["points"]) for r in csv.DictReader(f)}


@lru_cache
def load_thresholds() -> list[tuple[str, int]]:
    """Grade thresholds as (grade, min_score), sorted highest-min-score first."""
    with (DATA_DIR / "thresholds.csv").open(encoding="utf-8") as f:
        rows = [(r["grade"].strip(), int(r["min_score"])) for r in csv.DictReader(f)]
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows
