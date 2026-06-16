import openai
import pytest
import respx
from httpx import Response

from app.clients.cli_backend import LLMError
from app.clients.openai_backend import OpenAIBackend

CHAT_URL = "https://api.openai.com/v1/chat/completions"


def _sdk() -> openai.OpenAI:
    # max_retries=0 so 429s fail fast in tests instead of retrying with backoff.
    return openai.OpenAI(api_key="test", max_retries=0)


def _completion_json(content):
    return {
        "id": "chatcmpl-x",
        "object": "chat.completion",
        "created": 0,
        "model": "gpt-5",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


@respx.mock
def test_complete_parses_choice_and_builds_request():
    route = respx.post(CHAT_URL).mock(
        return_value=Response(200, json=_completion_json("ok"))
    )
    backend = OpenAIBackend(client=_sdk(), model="gpt-5")
    out = backend.complete(system="You are a test.", user="ping", max_tokens=16)
    assert out == "ok"
    body = route.calls.last.request.content.replace(b" ", b"")
    assert b'"model":"gpt-5"' in body
    assert b'"max_completion_tokens":16' in body
    assert b'"role":"system"' in body and b'"role":"user"' in body


@respx.mock
def test_quota_error_propagates_as_openai_error():
    respx.post(CHAT_URL).mock(
        return_value=Response(
            429,
            json={"error": {"message": "quota", "type": "insufficient_quota",
                            "code": "insufficient_quota"}},
        )
    )
    backend = OpenAIBackend(client=_sdk(), model="gpt-5")
    with pytest.raises(openai.OpenAIError):
        backend.complete("s", "u")


@respx.mock
def test_empty_content_raises_llmerror():
    respx.post(CHAT_URL).mock(return_value=Response(200, json=_completion_json(None)))
    backend = OpenAIBackend(client=_sdk(), model="gpt-5")
    with pytest.raises(LLMError):
        backend.complete("s", "u")
