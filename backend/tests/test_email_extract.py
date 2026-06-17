from app.chat.email_extract import extract_email


def test_extracts_plain_email():
    assert extract_email("sure, it's jane.doe@meridian.io") == "jane.doe@meridian.io"


def test_returns_none_when_absent():
    assert extract_email("we're a 200-person CS team evaluating tools") is None


def test_strips_trailing_punctuation():
    assert extract_email("reach me at sam@acme.com.") == "sam@acme.com"


def test_picks_first_email_when_multiple():
    assert extract_email("me@a.com or my colleague at you@b.io") == "me@a.com"


def test_handles_plus_and_subdomain():
    assert extract_email("ciso+security@corp.bigco.co.uk please") == "ciso+security@corp.bigco.co.uk"


def test_none_for_empty():
    assert extract_email("") is None
