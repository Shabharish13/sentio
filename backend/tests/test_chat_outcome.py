import json

from app.chat.outcome import classify


class StubLLM:
    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    def complete(self, system, user, max_tokens=1024):
        self.calls.append((system, user))
        return self._payload


def test_classify_parses_book_with_email_and_signals():
    payload = json.dumps({
        "signals": {"timeline": "this quarter", "authority": "VP CS"},
        "outcome": "book",
        "email": "jane@acme.com",
        "reason": None,
    })
    d = classify([{"role": "user", "content": "we want this now"}], {}, StubLLM(payload))
    assert d.outcome == "book"
    assert d.email == "jane@acme.com"
    assert d.signals["timeline"] == "this quarter"


def test_classify_disqualify_carries_reason():
    payload = json.dumps({"signals": {}, "outcome": "disqualify",
                          "email": None, "reason": "pre-revenue solo founder, no CS function"})
    d = classify([], {}, StubLLM(payload))
    assert d.outcome == "disqualify"
    assert "solo founder" in d.reason
    assert d.email is None


def test_classify_unknown_outcome_falls_back_to_continue():
    d = classify([], {}, StubLLM(json.dumps({"outcome": "purchase"})))
    assert d.outcome == "continue"


def test_classify_tolerates_prose_wrapped_json():
    payload = "Sure! Here is the decision:\n{\"outcome\": \"nurture\"}\nThanks"
    d = classify([], {}, StubLLM(payload))
    assert d.outcome == "nurture"


def test_classify_rejects_non_email_strings():
    payload = json.dumps({"outcome": "continue", "email": "not-an-email"})
    d = classify([], {}, StubLLM(payload))
    assert d.email is None
