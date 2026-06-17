import argparse
import sys
from io import StringIO

import pytest

from scripts.cli import _DryRunHubSpot


def test_dry_run_note_prints_unicode_without_error(monkeypatch):
    """_DryRunHubSpot.create_note must not raise on non-ASCII chars."""
    buf = StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    # U+2011 (non-breaking hyphen) and U+2014 (em-dash) are the chars that
    # crash the Windows cp1252 console.
    body = "SDR hand‑off — 60–90 day warning"
    _DryRunHubSpot().create_note(body, "dry-deal")
    assert "[dry-run] create_note" in buf.getvalue()
    assert "SDR hand" in buf.getvalue()


def test_dry_run_deal_name_prints_unicode_without_error(monkeypatch):
    buf = StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    _DryRunHubSpot().upsert_deal("Rocketlane — inbound", "3832955632", "c1")
    assert "Rocketlane" in buf.getvalue()
