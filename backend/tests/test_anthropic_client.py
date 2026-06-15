import anthropic
import respx
from httpx import Response

from app.clients.anthropic_client import AnthropicClient, load_prompt

MESSAGES_URL = "https://api.anthropic.com/v1/messages"


def _message_json(text: str) -> dict:
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": "claude-sonnet-4-6",
        "content": [{"type": "text", "text": text}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 5, "output_tokens": 2},
    }


@respx.mock
def test_complete_returns_text():
    route = respx.post(MESSAGES_URL).mock(
        return_value=Response(200, json=_message_json("ok"))
    )
    sdk = anthropic.Anthropic(api_key="test")
    client = AnthropicClient(client=sdk, model="claude-sonnet-4-6")
    out = client.complete(system="You are a test.", user="ping", max_tokens=16)
    assert out == "ok"
    assert route.called
    sent = route.calls.last.request
    assert b'"model":"claude-sonnet-4-6"' in sent.content.replace(b" ", b"")


def test_load_prompt_reads_repo_prompt():
    text = load_prompt("research_agent.md")
    assert "Research Agent" in text
