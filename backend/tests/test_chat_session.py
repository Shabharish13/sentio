from app.chat.models import QualificationState
from app.chat.session import SessionStore


def test_get_or_create_makes_a_session_with_an_id():
    store = SessionStore()
    state = store.get_or_create(None, page="/pricing")
    assert isinstance(state, QualificationState)
    assert state.session_id
    assert state.page == "/pricing"


def test_get_or_create_returns_same_object_for_same_id():
    store = SessionStore()
    first = store.get_or_create(None, page="/demo")
    again = store.get_or_create(first.session_id, page="/demo")
    assert again is first


def test_sessions_are_isolated_by_id():
    store = SessionStore()
    a = store.get_or_create(None, page="/")
    b = store.get_or_create(None, page="/")
    assert a.session_id != b.session_id
    a.add("user", "hi")
    assert b.history == []


def test_transcript_renders_roles():
    state = QualificationState(session_id="s1", page="/")
    state.add("user", "what is sentio")
    state.add("assistant", "a churn platform")
    assert state.transcript() == "user: what is sentio\nassistant: a churn platform"
