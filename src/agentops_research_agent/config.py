import os
from dataclasses import dataclass

from dotenv import load_dotenv


DEFAULT_TOPIC = "AgentOps and AI agent observability in 2026"


@dataclass(frozen=True)
class Settings:
    agentops_api_key: str
    openai_api_key: str
    openai_model: str = "gpt-5.4-mini"
    max_iterations: int = 10
    max_repeated_tool_calls: int = 3
    max_output_tokens: int = 4096
    request_timeout_seconds: float = 60.0
    research_topic: str = DEFAULT_TOPIC
    log_level: str = "INFO"
    agentops_trace_name: str = "research-agent-openai"
    agentops_tags: tuple[str, ...] = ("research-agent", "openai", "production")

    @classmethod
    def from_env(cls, env_file: str | None = ".env") -> "Settings":
        if env_file:
            load_dotenv(env_file)

        return cls(
            agentops_api_key=_required("AGENTOPS_API_KEY"),
            openai_api_key=_required("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", cls.openai_model),
            max_iterations=_int_env("MAX_ITERATIONS", cls.max_iterations),
            max_repeated_tool_calls=_int_env(
                "MAX_REPEATED_TOOL_CALLS",
                cls.max_repeated_tool_calls,
            ),
            max_output_tokens=_int_env("MAX_OUTPUT_TOKENS", cls.max_output_tokens),
            request_timeout_seconds=_float_env(
                "OPENAI_REQUEST_TIMEOUT_SECONDS",
                cls.request_timeout_seconds,
            ),
            research_topic=os.getenv("RESEARCH_TOPIC", cls.research_topic),
            log_level=os.getenv("LOG_LEVEL", cls.log_level).upper(),
            agentops_trace_name=os.getenv("AGENTOPS_TRACE_NAME", cls.agentops_trace_name),
            agentops_tags=_tags_env("AGENTOPS_TAGS", cls.agentops_tags),
        )

    def redacted(self) -> dict[str, object]:
        return {
            "agentops_api_key": _mask(self.agentops_api_key),
            "openai_api_key": _mask(self.openai_api_key),
            "openai_model": self.openai_model,
            "max_iterations": self.max_iterations,
            "max_repeated_tool_calls": self.max_repeated_tool_calls,
            "max_output_tokens": self.max_output_tokens,
            "request_timeout_seconds": self.request_timeout_seconds,
            "research_topic": self.research_topic,
            "log_level": self.log_level,
            "agentops_trace_name": self.agentops_trace_name,
            "agentops_tags": list(self.agentops_tags),
        }


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc
    if value < 1:
        raise RuntimeError(f"{name} must be greater than 0.")
    return value


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a number.") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than 0.")
    return value


def _tags_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(name)
    if raw is None:
        return default
    tags = tuple(tag.strip() for tag in raw.split(",") if tag.strip())
    return tags or default


def _mask(value: str) -> str:
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"
