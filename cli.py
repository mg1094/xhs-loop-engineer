"""CLI entry point — argument parsing and dispatch."""

import argparse
import sys

from agents import detect_article_type
from loop import XHSLoopEngineer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xhs-loop",
        description="XHS Loop Engineer — Xiaohongshu content automation",
    )
    parser.add_argument(
        "--mode",
        choices=["interactive", "auto"],
        default="interactive",
        help="Run mode (default: interactive)",
    )
    parser.add_argument(
        "--backend",
        choices=["manual", "anthropic", "openai"],
        default="manual",
        help="LLM backend (default: manual)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name (e.g., claude-sonnet-4-6, gpt-4o, qwen-max)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/schedule.yaml",
        help="Path to schedule config",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Skip topic discovery and use this topic directly",
    )
    parser.add_argument(
        "--type",
        dest="article_type",
        choices=["xiaobai", "deep_tech"],
        default=None,
        help="Article type (auto-detected if not specified)",
    )
    return parser


def run_fast_path(loop: XHSLoopEngineer, topic: str, article_type: str) -> int:
    """Generate, verify, and archive a single article by topic."""
    print(f"⚡ Fast path: generating for '{topic}'")

    gen_result = loop.step_3_generate(topic, article_type)
    content = gen_result.get("content") or loop.step_3_manual_input()

    if not content.strip():
        print("⚠️  Empty content, aborting")
        return 1

    verify = loop.step_4_verify(content, article_type)
    if verify["pass"]:
        loop.step_5_archive(content, topic, article_type)
        return 0

    print("\n⚠️  Content did not pass verification:")
    for issue in verify["issues"]:
        print(f"   - {issue}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    loop = XHSLoopEngineer(
        config_path=args.config,
        mode=args.mode,
        backend=args.backend,
        model=args.model,
    )

    # Fast path: --topic provided
    if args.topic:
        article_type = args.article_type or detect_article_type(args.topic)
        return run_fast_path(loop, args.topic, article_type)

    # Default: full loop
    loop.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
