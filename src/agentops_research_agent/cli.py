import argparse
import json
import logging
import sys
from typing import Sequence

from agentops_research_agent.agent import run_research
from agentops_research_agent.config import Settings


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentops-research-agent")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to dotenv file. Defaults to .env.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check-config", help="Validate configuration.")
    check.add_argument("--json", action="store_true", help="Print sanitized config as JSON.")

    run = subparsers.add_parser("run", help="Run the research agent.")
    run.add_argument(
        "--topic",
        default=None,
        help="Research topic. Defaults to RESEARCH_TOPIC or the built-in sample topic.",
    )
    run.add_argument("--json", action="store_true", help="Print only JSON output.")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        settings = Settings.from_env(args.env_file)
    except Exception as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    configure_logging(settings.log_level)

    if args.command == "check-config":
        payload = settings.redacted()
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("Configuration OK")
            print(f"Model: {payload['openai_model']}")
            print(f"AgentOps trace: {payload['agentops_trace_name']}")
        return 0

    if args.command == "run":
        topic = args.topic or settings.research_topic
        try:
            result = run_research(settings, topic)
        except Exception as exc:
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.exception("research agent run failed")
            else:
                logging.error("research agent run failed: %s", exc.__class__.__name__)
            result = {
                "error": exc.__class__.__name__,
                "message": "Research agent run failed. Check logs for details.",
            }
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print_result(result)
        return 1 if "error" in result else 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def print_result(result: dict[str, object]) -> None:
    print("\n" + "=" * 60)
    print("RESEARCH SUMMARY")
    print("=" * 60)

    if "error" in result:
        print(f"Error: {result['error']}")
    elif "message" in result:
        print(result["message"])
    else:
        print(f"Title: {result.get('title', 'N/A')}")
        print("\nKey Points:")
        for index, point in enumerate(result.get("key_points", []), 1):
            print(f"  {index}. {point}")
        print(f"\nConclusion: {result.get('conclusion', 'N/A')}")

    print("=" * 60)
    print("Session replay available at: https://app.agentops.ai")
