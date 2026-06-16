from __future__ import annotations

import uuid

from app.chat.models import QualificationState


class SessionStore:
    """Process-local store of chat sessions.

    In-memory by design — this is a single-instance demo backend, so qualification
    state lives for the life of the server process. A real deployment would back
    this with Redis or a database.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, QualificationState] = {}

    def get_or_create(self, session_id: str | None, page: str) -> QualificationState:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        new_id = session_id or uuid.uuid4().hex
        state = QualificationState(session_id=new_id, page=page)
        self._sessions[new_id] = state
        return state


# Module-level singleton used by the API layer.
_STORE = SessionStore()


def get_store() -> SessionStore:
    return _STORE
