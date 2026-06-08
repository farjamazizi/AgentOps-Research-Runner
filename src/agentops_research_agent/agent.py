import json
import logging
from typing import Any, Protocol

import agentops
from agentops.sdk.decorators import agent as agent_span
from agentops.sdk.decorators import operation, trace, workflow
from openai import OpenAI

from agentops_research_agent.config import Settings
from agentops_research_agent.prompts import SYSTEM_PROMPT
from agentops_research_agent.tools import TOOLS, execute_tool

logger = logging.getLogger(__name__)


class ResponsesClient(Protocol):
    def create(self, **kwargs: Any) -> Any:
        pass


def parse_tool_arguments(raw_arguments: str | None) -> dict[str, Any]:
    if not raw_arguments:
        return {}

    try:
        data = json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        raise ValueError("Tool arguments were not valid JSON.") from exc

    if not isinstance(data, dict):
        raise ValueError("Tool arguments must be a JSON object.")

    return data


def response_items_as_input(response: Any) -> list[dict[str, Any]]:
    return [item.model_dump(exclude_none=True) for item in response.output]


def extract_structured_summary(input_items: list[Any]) -> dict[str, Any] | None:
    for item in reversed(input_items):
        if not isinstance(item, dict):
            continue
        if item.get("type") != "function_call_output":
            continue

        try:
            payload = json.loads(item.get("output", "{}"))
        except json.JSONDecodeError:
            continue

        if payload.get("format") == "structured_summary":
            return payload

    return None


def initialize_agentops(settings: Settings) -> None:
    agentops.init(
        api_key=settings.agentops_api_key,
        default_tags=settings.agentops_tags,
        trace_name=settings.agentops_trace_name,
        auto_start_session=False,
        instrument_llm_calls=True,
        log_level=settings.log_level,
    )


def build_openai_client(settings: Settings) -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key, timeout=settings.request_timeout_seconds)


def run_research(settings: Settings, topic: str) -> dict[str, Any]:
    initialize_agentops(settings)
    return _run_research_trace(settings, topic)


@trace(name="research-agent-session", tags=["research-agent", "openai"])
def _run_research_trace(settings: Settings, topic: str) -> dict[str, Any]:
    return _run_research_agent_span(settings, topic)


@agent_span(name="ResearchAgent")
def _run_research_agent_span(settings: Settings, topic: str) -> dict[str, Any]:
    return ResearchAgent(settings).run(topic)


class ResearchAgent:
    def __init__(self, settings: Settings, responses_client: ResponsesClient | None = None):
        self.settings = settings
        if responses_client is None:
            responses_client = build_openai_client(settings).responses
        self.responses_client = responses_client

    @workflow(name="research-workflow")
    def run(self, topic: str) -> dict[str, Any]:
        input_items: list[Any] = [
            {
                "role": "user",
                "content": f"Research this topic and produce a structured summary: {topic}",
            }
        ]
        last_tool_signature: tuple[str, str] | None = None
        repeated_tool_calls = 0

        for iteration in range(1, self.settings.max_iterations + 1):
            response = self._call_model(input_items, iteration)

            input_items.extend(response_items_as_input(response))
            tool_calls = [
                item for item in response.output if getattr(item, "type", None) == "function_call"
            ]

            if not tool_calls:
                final_summary = extract_structured_summary(input_items)
                return final_summary or {
                    "message": getattr(response, "output_text", "") or "Research complete.",
                }

            for tool_call in tool_calls:
                arguments = parse_tool_arguments(tool_call.arguments)
                signature = (tool_call.name, json.dumps(arguments, sort_keys=True))
                if signature == last_tool_signature:
                    repeated_tool_calls += 1
                else:
                    repeated_tool_calls = 1
                last_tool_signature = signature

                if repeated_tool_calls > self.settings.max_repeated_tool_calls:
                    return {
                        "error": (
                            "Repeated tool-call guard triggered for "
                            f"{tool_call.name}."
                        )
                    }

                result = self._execute_tool_call(tool_call.name, arguments, iteration)
                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": result,
                    }
                )

        return {
            "error": (
                f"Max iterations reached ({self.settings.max_iterations}); "
                "possible loop detected."
            )
        }

    @operation(name="openai-responses-create")
    def _call_model(self, input_items: list[Any], iteration: int) -> Any:
        logger.info(
            "calling OpenAI Responses API",
            extra={"iteration": iteration, "model": self.settings.openai_model},
        )
        return self.responses_client.create(
            model=self.settings.openai_model,
            instructions=SYSTEM_PROMPT,
            tools=TOOLS,
            input=input_items,
            max_output_tokens=self.settings.max_output_tokens,
        )

    @operation(name="execute-tool-call")
    def _execute_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        iteration: int,
    ) -> str:
        logger.info(
            "executing tool",
            extra={"tool": tool_name, "iteration": iteration},
        )
        return execute_tool(tool_name, arguments)
