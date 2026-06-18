"""CLI entry point — argument parsing and dispatch."""

import argparse
import sys

from agents import detect_article_type
from agents.style_learner import StyleLearner
from agents.style_scorer import StyleScorer
from loop import XHSLoopEngineer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xhs-loop",
        description="XHS Loop Engineer — Xiaohongshu content automation",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Default: run the loop
    run_parser = subparsers.add_parser("run", help="Run the content generation loop (default)")
    run_parser.add_argument(
        "--mode",
        choices=["interactive", "auto"],
        default="interactive",
        help="Run mode (default: interactive)",
    )
    run_parser.add_argument(
        "--backend",
        choices=["manual", "anthropic", "openai"],
        default="manual",
        help="LLM backend (default: manual)",
    )
    run_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name (e.g., claude-sonnet-4-6, gpt-4o, qwen-max)",
    )
    run_parser.add_argument(
        "--config",
        type=str,
        default="config/schedule.yaml",
        help="Path to schedule config",
    )
    run_parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Skip topic discovery and use this topic directly",
    )
    run_parser.add_argument(
        "--type",
        dest="article_type",
        choices=["xiaobai", "deep_tech"],
        default=None,
        help="Article type (auto-detected if not specified)",
    )

    # learn-style: extract style profile from published articles
    learn_parser = subparsers.add_parser(
        "learn-style", help="Learn your writing style from published articles"
    )
    learn_parser.add_argument(
        "--config",
        type=str,
        default="config/schedule.yaml",
    )

    # score-style: score a draft against the learned profile
    score_parser = subparsers.add_parser(
        "score-style", help="Score a draft against your style profile"
    )
    score_parser.add_argument(
        "file", help="Path to the markdown file to score"
    )
    score_parser.add_argument(
        "--type",
        dest="article_type",
        choices=["xiaobai", "deep_tech"],
        default="xiaobai",
    )
    score_parser.add_argument(
        "--config",
        type=str,
        default="config/schedule.yaml",
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


def cmd_learn_style(args) -> int:
    learner = StyleLearner(config_path=args.config)
    profile = learner.run()
    xiaobai_n = profile.get("xiaobai", {}).get("sample_size", 0)
    deep_tech_n = profile.get("deep_tech", {}).get("sample_size", 0)
    if xiaobai_n == 0 and deep_tech_n == 0:
        print("⚠️  No published articles found in your Obsidian vault.")
        print(
            f"   Looked in: {learner.published_dir}"
        )
        print("   Publish some posts first, then run this command.")
        return 1
    return 0


def cmd_score_style(args) -> int:
    scorer = StyleScorer(config_path=args.config)
    text = open(args.file, encoding="utf-8").read()
    result = scorer.score(text, args.article_type)

    print(f"\n🎨 Style score for {args.file}")
    print(f"   Type: {args.article_type}")
    print(f"   Overall: {result['score']:.3f} (threshold: {result.get('threshold', 0.70)})")
    print(f"   Result: {'✅ PASS' if result['passed'] else '❌ FAIL'}")
    if result.get("reason") == "no_style_profile_yet":
        print(f"   Note: {result['message']}")
        return 0
    print(f"   Sample size: {result.get('sample_size', 0)} articles")
    print(f"   Dimensions:")
    for dim, dim_score in result.get("dimension_scores", {}).items():
        print(f"     - {dim}: {dim_score:.3f}")
    return 0 if result["passed"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    # If no subcommand, default to "run" for backward compatibility
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] not in ("run", "learn-style", "score-style"):
        argv = ["run"] + argv
    elif not argv:
        argv = ["run"]

    args = parser.parse_args(argv)

    if args.command == "learn-style":
        return cmd_learn_style(args)
    if args.command == "score-style":
        return cmd_score_style(args)

    # Default: run the loop
    loop = XHSLoopEngineer(
        config_path=args.config,
        mode=args.mode,
        backend=args.backend,
        model=args.model,
    )

    if args.topic:
        article_type = args.article_type or detect_article_type(args.topic)
        return run_fast_path(loop, args.topic, article_type)

    loop.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

