"""Tests for the feedback-driven style learning system."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.style_learner import StyleLearner


def _temp_learner() -> StyleLearner:
    """Create a StyleLearner that points at a temp directory."""
    learner = StyleLearner.__new__(StyleLearner)
    learner.style_config = {"content_rules": {"forbidden_words": []}}
    # Point at a temp directory so we don't pollute the real vault
    tmpdir = tempfile.mkdtemp()
    learner.vault = Path(tmpdir)
    learner.published_dir = learner.vault / "01-已发文章"
    learner.published_dir.mkdir(parents=True, exist_ok=True)
    learner.style_path = learner.vault / "小红书" / "style_profile.json"
    return learner


SAMPLE_XIAOBAI = """我用AI写周报 🤯 领导以为我天天加班

🔧 方法很简单。第一步：打开 AI 工具，把你这周干的零碎事都丢进去。
第二步：发一句话指令，让它帮你整理成结构化内容。
第三步：复制粘贴到周报模板里，完事儿。

🎯 实测效果。以前写周报要半小时，现在 5 分钟搞定。
领导反馈最近周报写得越来越规范了，AI 帮我全过滤了废话。

💡 不只是周报。同一个方法，换个说法就能搞定月度总结。

你用哪个 AI 工具？评论区聊聊

#打工人效率工具 #AI工具推荐 #职场干货 #零基础也能用 #周报
"""


def _write_article(learner: StyleLearner, filename: str, content: str):
    path = learner.published_dir / filename
    path.write_text(content, encoding="utf-8")


def test_first_learn_uses_all_articles():
    """When no feedback exists, all articles are used."""
    learner = _temp_learner()
    _write_article(learner, "001-test.md", SAMPLE_XIAOBAI)
    _write_article(learner, "002-test2.md", SAMPLE_XIAOBAI)

    profile = learner.learn()
    assert profile["xiaobai"]["sample_size"] == 2


def test_feedback_evolves_profile():
    """Approve an article → profile grows; reject → profile shrinks."""
    learner = _temp_learner()
    _write_article(learner, "001-test.md", SAMPLE_XIAOBAI)
    _write_article(learner, "002-test2.md", SAMPLE_XIAOBAI)

    # Initially: 2 articles
    profile = learner.learn()
    assert profile["xiaobai"].get("sample_size", 0) == 2

    # Reject one — should drop to 1
    learner.record_feedback("002-test2.md", "xiaobai", approved=False)
    profile = learner.learn()
    assert profile["xiaobai"].get("sample_size", 0) == 1

    # Approve it again — back to 2
    learner.record_feedback("002-test2.md", "xiaobai", approved=True)
    profile = learner.learn()
    assert profile["xiaobai"].get("sample_size", 0) == 2


def test_feedback_persists_across_loads():
    """Approved list survives save/load cycle."""
    learner = _temp_learner()
    _write_article(learner, "001-test.md", SAMPLE_XIAOBAI)

    # First call: approves
    learner.record_feedback("001-test.md", "xiaobai", approved=True)
    # Second call: should still see it as approved
    profile = learner.learn()
    assert profile["xiaobai"]["sample_size"] == 1
    # Verify _approved is in the saved file
    saved = json.loads(learner.style_path.read_text(encoding="utf-8"))
    assert "001-test.md" in saved["_approved"]["xiaobai"]


def test_feedback_history_truncated():
    """History is capped at 50 entries."""
    learner = _temp_learner()
    _write_article(learner, "001-test.md", SAMPLE_XIAOBAI)

    # Record 60 feedbacks (alternating approve/reject)
    for i in range(60):
        learner.record_feedback(
            f"{i:03d}-test.md", "xiaobai", approved=(i % 2 == 0)
        )

    saved = json.loads(learner.style_path.read_text(encoding="utf-8"))
    assert len(saved["_history"]) == 50


def test_moving_between_approved_and_rejected():
    """Re-classifying an article moves it between buckets."""
    learner = _temp_learner()
    _write_article(learner, "001-test.md", SAMPLE_XIAOBAI)

    learner.record_feedback("001-test.md", "xiaobai", approved=True)
    profile = learner.learn()
    assert profile["xiaobai"].get("sample_size", 0) == 1

    # Flip to rejected
    learner.record_feedback("001-test.md", "xiaobai", approved=False)
    profile = learner.learn()
    assert profile["xiaobai"].get("sample_size", 0) == 0

    saved = json.loads(learner.style_path.read_text(encoding="utf-8"))
    assert "001-test.md" not in saved["_approved"]["xiaobai"]
    assert "001-test.md" in saved["_rejected"]["xiaobai"]
