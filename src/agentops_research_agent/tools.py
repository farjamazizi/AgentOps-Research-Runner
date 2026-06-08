import json
import time
from typing import Any

from agentops.sdk.decorators import tool


TOOLS = [
    {
        "type": "function",
        "name": "search_topic",
        "description": (
            "Search for comprehensive information about a topic. "
            "Use this as the first step for any research task."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to research. Be specific.",
                },
                "depth": {
                    "type": "string",
                    "enum": ["overview", "detailed"],
                    "description": "How deep to search. Use 'overview' first.",
                },
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_key_facts",
        "description": (
            "Extract the most important facts about a topic from search results. "
            "Use after search_topic to identify the 5-7 most significant points."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to extract facts about.",
                },
                "focus": {
                    "type": "string",
                    "description": (
                        "Optional angle to focus on, such as recent developments "
                        "or key players."
                    ),
                },
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "format_summary",
        "description": (
            "Format research findings into a clean structured summary. "
            "Always call this as the final step before returning to the user."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title for the summary.",
                },
                "key_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of key findings.",
                },
                "conclusion": {
                    "type": "string",
                    "description": "A 2-3 sentence synthesis of the research.",
                },
            },
            "required": ["title", "key_points", "conclusion"],
            "additionalProperties": False,
        },
    },
]


@tool
def search_topic(topic: str, depth: str = "overview") -> dict[str, Any]:
    """Stub search tool. Replace with a real search API in production."""
    time.sleep(0.3)
    return {
        "topic": topic,
        "depth": depth,
        "results": (
            f"Comprehensive overview of {topic}: this is a rapidly evolving "
            "field with active technical innovation, adoption patterns, and "
            "organizational impact."
        ),
        "source_count": 12,
        "timestamp": "2026-06-08",
    }


@tool
def get_key_facts(topic: str, focus: str | None = None) -> dict[str, Any]:
    """Stub fact extraction tool. Replace with retrieval over real sources."""
    time.sleep(0.2)
    focus_note = f" Focus: {focus}." if focus else ""
    return {
        "topic": topic,
        "focus": focus,
        "facts": [
            f"{topic} adoption is driven by reliability, cost, and governance needs.",
            "Session-level traces make multi-step agent failures diagnosable.",
            "Tool-call spans expose malformed arguments and repeated calls.",
            "Cost controls should be enforced at the full-session level.",
            "Production agent safety depends on input checks, scoped tools, and output validation.",
        ],
        "summary": f"Key production considerations for {topic}.{focus_note}",
        "confidence": "medium",
    }


@tool
def format_summary(title: str, key_points: list[str], conclusion: str) -> dict[str, Any]:
    """Final formatting tool for the research workflow."""
    return {
        "title": title,
        "key_points": key_points,
        "conclusion": conclusion,
        "format": "structured_summary",
        "generated_at": "2026-06-08",
    }


def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> str:
    if tool_name == "search_topic":
        result = search_topic(**tool_input)
    elif tool_name == "get_key_facts":
        result = get_key_facts(**tool_input)
    elif tool_name == "format_summary":
        result = format_summary(**tool_input)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result)
