import json

import pytest

from app.clients.cli_backend import ClaudeCliBackend, LLMError


def test_complete_parses_result_and_builds_argv():
    captured = {}

    def runner(args):
        captured["args"] = args
        return json.dumps({"type": "result", "is_error": False, "result": "ok"})

    backend = ClaudeCliBackend(runner=runner, model="claude-sonnet-4-6")
    out = backend.complete(system="You are a test.", user="ping", max_tokens=16)

    assert out == "ok"
    args = captured["args"]
    assert args[0] == "claude"
    assert "-p" in args and "ping" in args
    assert "--system-prompt" in args and "You are a test." in args
    assert "--model" in args and "claude-sonnet-4-6" in args
    assert "--output-format" in args and "json" in args
    assert "--max-turns" in args and "1" in args
    # Tools are disabled so the model answers directly (no tool-use turn).
    assert "--tools" in args and args[args.index("--tools") + 1] == ""


def test_complete_raises_on_is_error():
    def runner(args):
        return json.dumps(
            {"is_error": True, "api_error_status": 500, "subtype": "error"}
        )

    with pytest.raises(LLMError):
        ClaudeCliBackend(runner=runner).complete("s", "u")


def test_complete_raises_on_non_json():
    def runner(args):
        return "not json at all"

    with pytest.raises(LLMError):
        ClaudeCliBackend(runner=runner).complete("s", "u")


def test_complete_raises_when_result_missing():
    def runner(args):
        return json.dumps({"is_error": False})

    with pytest.raises(LLMError):
        ClaudeCliBackend(runner=runner).complete("s", "u")
