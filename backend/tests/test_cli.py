import argparse
import sys
from io import StringIO

import pytest

from scripts.cli import _DryRunHubSpot, cmd_pipeline


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


def test_cmd_pipeline_bad_email_exits_cleanly(capsys):
    """Invalid work email → clean one-line error to stderr, SystemExit(1), no traceback."""
    args = argparse.Namespace(
        email="not-an-email",
        first_name="", last_name="", company="Acme",
        title="VP CS", size="201-500", problem="", how_heard="Other",
        enrich=False, write=False,
        industry="Computer Software", headcount=200,
        country="United States", tech=[],
    )
    with pytest.raises(SystemExit) as exc_info:
        cmd_pipeline(args)
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "traceback" not in captured.err.lower()
    assert "exit check" in captured.err.lower() or "work_email" in captured.err.lower()
