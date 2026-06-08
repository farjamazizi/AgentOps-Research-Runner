import json
from dataclasses import replace

import pytest

from agentops_research_agent.agent import (
    ResearchAgent,
    extract_structured_summary,
    parse_tool_arguments,
)
from agentops_research_agent.config import Settings


class FakeItem:
    def __init__(self, item_type, name=None, arguments=None, call_id=None, payload=None):
        self.type = item_type
        self.name = name
        self.arguments = arguments
        self.call_id = call_id
        self._payload = payload or {
            "type": item_type,
            "name": name,
            "arguments": arguments,
            "call_id": call_id,
        }

    def model_dump(self, exclude_none=True):
        if not exclude_none:
            return dict(self._payload)
        return {key: value for key, value in self._payload.items() if value is not None}


class FakeResponse:
    def __init__(self, output, output_text=""):
        self.output = output
        self.output_text = output_text


class FakeResponsesClient:
    def __init__(self, responses):
        self.responses = list(responses)

    def create(self, **kwargs):
        if not self.responses:
            raise AssertionError("No fake responses left.")
        return self.responses.pop(0)


@pytest.fixture
def settings():
    return Settings(
        agentops_api_key="agentops-test-key",
        openai_api_key="openai-test-key",
        max_iterations=4,
    )


def test_parse_tool_arguments_accepts_json_object():
    assert parse_tool_arguments('{"topic": "AgentOps"}') == {"topic": "AgentOps"}


def test_parse_tool_arguments_rejects_invalid_json():
    with pytest.raises(ValueError):
        parse_tool_arguments("{not-json")


def test_extract_structured_summary_from_tool_output():
    payload = {
        "format": "structured_summary",
        "title": "AgentOps",
        "key_points": ["Tracing matters"],
        "conclusion": "Use session traces.",
    }
    assert extract_structured_summary(
        [{"type": "function_call_output", "output": json.dumps(payload)}]
    ) == payload


def test_repeated_tool_call_guard(settings, monkeypatch):
    monkeypatch.setattr("agentops_research_agent.agent.agentops.end_trace", lambda **kwargs: None)
    repeated_call = FakeItem(
        "function_call",
        name="search_topic",
        arguments='{"topic": "AgentOps"}',
        call_id="call_1",
    )
    client = FakeResponsesClient(
        [
            FakeResponse([repeated_call]),
            FakeResponse([repeated_call]),
            FakeResponse([repeated_call]),
        ]
    )
    agent = ResearchAgent(
        replace(settings, max_repeated_tool_calls=2),
        responses_client=client,
    )

    result = agent.run("AgentOps")

    assert "Repeated tool-call guard" in result["error"]
