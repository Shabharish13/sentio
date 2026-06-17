from __future__ import annotations

import re

# Deterministic email detection. Whether the visitor has shared an email is a
# string check, not a judgment — so the chat handoff gate ("do we still need to
# ask for it?") runs in code, not via the LLM classifier. The classifier's job is
# the semantic routing decision; presence of an email is decided here.
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def extract_email(text: str) -> str | None:
    """Return the first email address in `text`, or None. Trailing sentence
    punctuation (the `.` in '...@acme.com.') is excluded by the TLD letter class."""
    match = _EMAIL_RE.search(text or "")
    return match.group(0) if match else None
