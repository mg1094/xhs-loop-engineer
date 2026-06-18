"""Tests for the quality checker agent."""

import sys
from pathlib import Path

# Add project root to path so tests can run from anywhere
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.quality_checker import QualityChecker


VALID_BODY = (
    "🔧 方法很简单。第一步：打开一个 AI 工具，把你这周干的零碎事都丢进去。"
    "第二步：发一句话指令，让它帮你整理成结构化内容。"
    "第三步：复制粘贴到周报模板里，完事儿。"
    "🎯 实测效果。以前写周报要半小时，现在 5 分钟搞定。"
    "领导反馈最近周报写得越来越规范了，AI 帮我全过滤了废话。"
    "💡 不只是周报。同一个方法，换个说法就能搞定月度总结、"
    "述职报告、会议纪要、汇报 PPT 大纲。一套方法吃遍所有文书工作。"
    "⚠️ 小提醒。重要信息别往里放，AI 写完自己读一遍，"
    "同事问你就说平时多积累，别说是 AI 写的 😂"
    "你用哪个 AI 工具？评论区聊聊"
)

VALID_TAGS = (
    "#打工人效率工具 #AI工具推荐 #AI提效 #职场干货 #零基础也能用 #周报"
)


# ── forbidden words ────────────────────────────────────────────


def test_forbidden_words_detects_known_violation():
    checker = QualityChecker()
    text = "我在国企写了一份周报"
    found = checker.check_forbidden_words(text)
    assert "国企" in found


def test_forbidden_words_passes_clean_text():
    checker = QualityChecker()
    text = "打工人用 AI 提效实战"
    found = checker.check_forbidden_words(text)
    assert found == []


# ── title ──────────────────────────────────────────────────────


def test_title_too_short():
    checker = QualityChecker()
    result = checker.check_title("短标题")
    assert not result["pass"]
    assert any("too short" in i.lower() for i in result["issues"])


def test_title_too_long():
    checker = QualityChecker()
    long = "这是一个" * 10
    result = checker.check_title(long)
    assert not result["pass"]
    assert any("too long" in i.lower() for i in result["issues"])


def test_title_missing_emoji():
    checker = QualityChecker()
    result = checker.check_title("我用AI写周报领导以为我天天加班")
    assert not result["pass"]
    assert any("emoji" in i.lower() for i in result["issues"])


def test_title_valid():
    checker = QualityChecker()
    result = checker.check_title("我用AI写周报 🤯 领导以为我天天加班")
    assert result["pass"], result["issues"]


# ── structure ──────────────────────────────────────────────────


def test_structure_emoji_count():
    checker = QualityChecker()
    text = "短文本没有 emoji 段落标记，但写得很长很长写得很长很长写得很长很长写得很长很长写得很长很长写得很长很长写得很长很长"
    result = checker.check_structure(text)
    assert any("emoji" in i.lower() for i in result["issues"])


def test_structure_character_count():
    checker = QualityChecker()
    text = "🔧 短"
    result = checker.check_structure(text)
    assert any("too short" in i.lower() for i in result["issues"])


def test_structure_valid():
    checker = QualityChecker()
    result = checker.check_structure(VALID_BODY)
    assert result["pass"], result["issues"]


# ── tags ───────────────────────────────────────────────────────


def test_tags_too_few():
    checker = QualityChecker()
    text = "标题\n#tag1 #tag2"
    result = checker.check_tags(text)
    assert not result["pass"]


def test_tags_valid():
    checker = QualityChecker()
    text = f"标题\n{VALID_TAGS}"
    result = checker.check_tags(text)
    assert result["pass"], result["issues"]


def test_tags_missing_default():
    checker = QualityChecker()
    text = "#tag1 #tag2 #tag3 #tag4 #tag5 #tag6"
    result = checker.check_tags(text)
    assert not result["pass"]


# ── interaction ────────────────────────────────────────────────


def test_interaction_missing():
    checker = QualityChecker()
    text = "标题\n内容没有任何互动引导"
    result = checker.check_interaction(text)
    assert not result["pass"]


def test_interaction_present():
    checker = QualityChecker()
    text = "你用哪个工具？评论区聊聊"
    result = checker.check_interaction(text)
    assert result["pass"]


# ── full pipeline ──────────────────────────────────────────────


def test_full_run_valid_post():
    checker = QualityChecker()
    text = f"我用AI写周报 🤯 领导以为我天天加班\n\n{VALID_BODY}\n\n{VALID_TAGS}"
    result = checker.run(text)
    assert result["pass"], result["issues"]
    assert result["score"] >= 8


def test_full_run_violates_forbidden_word():
    checker = QualityChecker()
    text = (
        f"我在国企用AI写周报 🤯\n\n{VALID_BODY}\n\n{VALID_TAGS}"
    )
    result = checker.run(text)
    assert not result["pass"]
    assert any("forbidden" in i.lower() or "国企" in i for i in result["issues"])
