"""
Loop Controller — XHS Loop Engineer
Xiaohongshu content automation workflow.

Loop Engineering core principle:
  Don't prompt the agent manually. Design a system that does it for you.

Modes:
  - interactive: Human-in-the-loop (pick topics, review content)
  - auto: Fully automated (LLM generates → self-verify → retry → archive)
"""

import yaml
import json
from pathlib import Path
from datetime import datetime

from agents import detect_article_type
from agents.topic_finder import TopicFinder
from agents.content_writer import ContentWriter
from agents.quality_checker import QualityChecker
from agents.archiver import Archiver


class XHSLoopEngineer:
    def __init__(
        self,
        config_path: str = "config/schedule.yaml",
        mode: str = "interactive",
        backend: str = "manual",
        model: str = None,
    ):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.mode = mode
        self.backend = backend
        self.model = model

        self.topic_finder = TopicFinder(config_path)
        self.content_writer = ContentWriter(config_path)
        self.quality_checker = QualityChecker()
        self.archiver = Archiver(config_path)

        self.state_file = Path("state/loop_state.json")
        self.state = self._load_state()
        self.max_retries = 3

    # ── state management ──────────────────────────────────────────

    def _load_state(self) -> dict:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {"iterations": 0, "articles_generated": 0}

    def _save_state(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state["iterations"] = self.state.get("iterations", 0) + 1
        self.state_file.write_text(
            json.dumps(self.state, indent=2, ensure_ascii=False)
        )

    # ── step 1: topic discovery ───────────────────────────────────

    def step_1_find_topics(self) -> dict:
        """Run Agent 1: Topic Finder."""
        print("\n🔍 Agent 1: Topic Discovery...")
        result = self.topic_finder.run()
        print(f"   {result['message']}")
        return result

    # ── step 2: topic selection (interactive) ─────────────────────

    def step_2_user_select(self, topic_result: dict) -> str:
        """Human picks a topic (interactive mode only)."""
        print("\n⚡ Pick a topic:")
        all_topics = topic_result["topic_pool"][:5]
        if not all_topics:
            print("   No pending topics. Enter a new one.")
            return input("\n👉 New topic: ").strip()

        for i, t in enumerate(all_topics, 1):
            print(f"   {i}. {t}")

        choice = input("\n👉 Number (or type a new topic): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(all_topics):
                return all_topics[idx]
        except ValueError:
            pass
        return choice

    def step_2_auto_select(self, topic_result: dict) -> str:
        """Auto-pick the first topic (auto mode)."""
        if topic_result["topic_pool"]:
            return topic_result["topic_pool"][0]
        return "AI 工具推荐 — 最新实用工具合集"

    # ── step 3: content generation ────────────────────────────────

    def step_3_generate(
        self, topic: str, article_type: str = None
    ) -> dict:
        """Run Agent 2: Content Writer (with LLM backend)."""
        if article_type is None:
            article_type = detect_article_type(topic)

        print(f"\n✍️  Agent 2: Content Generation ({self.backend})...")
        print(f"   Topic: {topic}")
        print(f"   Type:  {article_type}")

        result = self.content_writer.generate(
            topic=topic,
            article_type=article_type,
            backend=self.backend,
            model=self.model,
        )

        if result["status"] == "error":
            print(f"   ❌ {result['message']}")
        elif result["status"] == "generated":
            print(f"   ✅ Generated ({result['backend']}/{result.get('model', '?')})")
        else:
            print(f"   📋 {result['message']}")

        return result

    # ── step 3b: manual content input ─────────────────────────────

    def step_3_manual_input(self) -> str:
        """Read content from stdin (interactive fallback)."""
        print("\n📋 Paste content below (type END on its own line to finish):")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        return "\n".join(lines)

    # ── step 4: quality verification ──────────────────────────────

    def step_4_verify(self, content: str, article_type: str) -> dict:
        """Run Agent 3: Quality Checker."""
        print(f"\n🔍 Agent 3: Quality Verification...")
        result = self.quality_checker.run(content, article_type)

        if result["pass"]:
            print(f"   ✅ Passed (score: {result['score']}/10)")
        else:
            print(f"   ❌ Failed (score: {result['score']}/10)")
            for issue in result["issues"]:
                print(f"      - {issue}")

        return result

    # ── step 5: archive + notify ──────────────────────────────────

    def step_5_archive(
        self, content: str, topic: str, article_type: str
    ) -> dict:
        """Run Agent 4: Archiver + Notifier."""
        print(f"\n📦 Agent 4: Archive + Notify...")
        result = self.archiver.run(content, topic, article_type)
        print(f"   {result['message']}")
        return result

    # ── main loop ─────────────────────────────────────────────────

    def run_interactive(self):
        """Interactive mode: human-in-the-loop for every decision."""
        print("=" * 50)
        print("🔄 XHS Loop Engineer — Interactive Mode")
        print(f"   Iterations: {self.state.get('iterations', 0)}")
        print(f"   Articles:   {self.state.get('articles_generated', 0)}")
        print("=" * 50)

        # Step 1: Find topics
        topics = self.step_1_find_topics()

        # Step 2: Select topic
        selected_topic = self.step_2_user_select(topics)

        # Step 3-5: Generate → Verify → Archive (with retries)
        for attempt in range(self.max_retries):
            print(f"\n--- Round {attempt + 1}/{self.max_retries} ---")

            # Step 3: Generate
            gen_result = self.step_3_generate(selected_topic)

            # Get content
            if gen_result.get("content"):
                content = gen_result["content"]
            else:
                content = self.step_3_manual_input()

            if not content.strip():
                print("   ⚠️  Empty content, skipping")
                continue

            # Step 4: Verify
            verify = self.step_4_verify(content, gen_result.get("type", "xiaobai"))

            if verify["pass"]:
                # Step 5: Archive
                archive = self.step_5_archive(
                    content, selected_topic, gen_result.get("type", "xiaobai")
                )
                self.state["articles_generated"] = (
                    self.state.get("articles_generated", 0) + 1
                )
                self.state["last_run_date"] = datetime.now().strftime("%Y-%m-%d")
                self._save_state()

                print(f"\n✅ Loop complete!")
                print(f"   File: {archive['filepath']}")
                return archive

            # Failed verification — collect feedback and retry
            if attempt < self.max_retries - 1:
                feedback = input("\n💬 Revision feedback (Enter to skip): ").strip()
                if feedback:
                    selected_topic = f"{selected_topic} (revise: {feedback})"

        print(f"\n⚠️  Max retries ({self.max_retries}) reached. Manual review needed.")
        return {"status": "max_retries_reached"}

    def run_auto(self):
        """Auto mode: fully automated with self-verification and retry."""
        print("=" * 50)
        print("🤖 XHS Loop Engineer — Auto Mode")
        print(f"   Backend: {self.backend}/{self.model or 'default'}")
        print(f"   Iterations: {self.state.get('iterations', 0)}")
        print(f"   Articles:   {self.state.get('articles_generated', 0)}")
        print("=" * 50)

        # Step 1: Find topics
        topics = self.step_1_find_topics()

        # Step 2: Auto-select
        selected_topic = self.step_2_auto_select(topics)

        # Step 3-5: Generate → Verify → Retry (automatic)
        for attempt in range(self.max_retries):
            print(f"\n--- Round {attempt + 1}/{self.max_retries} ---")

            # Step 3: Generate via LLM
            gen_result = self.step_3_generate(selected_topic)

            if gen_result["status"] == "error":
                print(f"   ⚠️  Generation failed, retrying...")
                continue

            if not gen_result.get("content"):
                print(f"   ⚠️  No content returned, retrying...")
                continue

            content = gen_result["content"]

            # Step 4: Verify
            verify = self.step_4_verify(content, gen_result.get("type", "xiaobai"))

            if verify["pass"]:
                # Step 5: Archive
                archive = self.step_5_archive(
                    content, selected_topic, gen_result.get("type", "xiaobai")
                )
                self.state["articles_generated"] = (
                    self.state.get("articles_generated", 0) + 1
                )
                self.state["last_run_date"] = datetime.now().strftime("%Y-%m-%d")
                self._save_state()

                print(f"\n✅ Auto loop complete!")
                print(f"   File: {archive['filepath']}")
                return archive

            # Auto-retry with feedback injected
            if attempt < self.max_retries - 1:
                feedback = "; ".join(verify["issues"])
                print(f"   🔄 Auto-retry with feedback: {feedback[:80]}...")
                selected_topic = f"{selected_topic} (fix: {feedback[:100]})"

        print(f"\n⚠️  Auto mode: max retries ({self.max_retries}) reached.")
        return {"status": "max_retries_reached"}

    def run(self):
        """Entry point — dispatches to interactive or auto mode."""
        if self.mode == "auto":
            return self.run_auto()
        return self.run_interactive()
