"""Tests for the style learner and scorer."""

import json
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.style_learner import (
    StyleLearner,
    _strip_frontmatter,
    _split_sentences,
    _extract_emoji_sections,
)
from agents.style_scorer import StyleScorer, _gaussian_similarity


# ── feature extraction helpers ────────────────────────────────────


def test_strip_frontmatter():
    text = """---
title: Test
tags: [a, b]
---

This is the body."""
    result = _strip_frontmatter(text)
    assert not result.startswith("---")
    assert "This is the body" in result


def test_strip_frontmatter_no_frontmatter():
    text = "Just plain text"
    assert _strip_frontmatter(text) == text


def test_split_sentences_chinese():
    sentences = _split_sentences("第一句。第二句？第三句！")
    assert len(sentences) >= 3
    assert any("第一句" in s for s in sentences)


def test_extract_emoji_sections_basic():
    text = """标题

🔧 第一段
内容1
内容2

🎯 第二段
内容3

普通段落
"""
    sections = _extract_emoji_sections(text)
    assert len(sections) == 2
    assert "🔧" in sections[0]
    assert "🎯" in sections[1]


# ── StyleLearner.extract_features ────────────────────────────────


def test_extract_features_basic():
    learner = StyleLearner.__new__(StyleLearner)
    learner.style_config = {"content_rules": {"forbidden_words": []}}
    text = """标题 🤯

🔧 方法很简单。第一步：打开 AI 工具，把你这周干的零碎事都丢进去。
第二步：发一句话指令，让它帮你整理成结构化内容。
第三步：复制粘贴到周报模板里，完事儿。

🎯 实测效果。以前写周报要半小时，现在 5 分钟搞定。
领导反馈最近周报写得越来越规范了，AI 帮我全过滤了废话。

你用哪个 AI 工具？评论区聊聊

#tag1 #tag2 #tag3 #tag4 #tag5
"""
    features = learner.extract_features(text)
    assert features["emoji_count"] >= 3
    assert features["emoji_section_count"] >= 2
    assert features["paragraph_count"] >= 3
    assert features["char_count"] > 50
    assert features["sentence_count"] >= 3


def test_extract_features_strips_hashtags():
    learner = StyleLearner.__new__(StyleLearner)
    learner.style_config = {"content_rules": {"forbidden_words": []}}
    text = """标题 🤯

🔧 方法

第一步
第二步

评论区聊聊

#tag1 #tag2 #tag3 #tag4 #tag5 #tag6
"""
    features = learner.extract_features(text)
    # Hashtags should not be counted as content characters
    assert "tag1" not in str(features["first_words"])


def test_extract_features_finds_first_words():
    learner = StyleLearner.__new__(StyleLearner)
    learner.style_config = {"content_rules": {"forbidden_words": []}}
    text = """我在国企用AI写周报 🤯

🔧 方法

第一步
第二步

评论区聊聊

#tag1 #tag2 #tag3 #tag4 #tag5
"""
    features = learner.extract_features(text)
    # First sentence should be captured
    assert len(features["first_words"]) > 0


# ── StyleLearner._classify ─────────────────────────────────────────


def test_classify_deep_tech_by_filename():
    learner = StyleLearner.__new__(StyleLearner)
    learner.style_config = {"content_rules": {"forbidden_words": []}}
    result = learner._classify("005-MinerU深度解析.md", "some text")
    assert result == "deep_tech"


def test_classify_xiaobai_by_filename():
    learner = StyleLearner.__new__(StyleLearner)
    learner.style_config = {"content_rules": {"forbidden_words": []}}
    result = learner._classify("001-国企AI写周报.md", "some text")
    assert result == "xiaobai"


# ── StyleScorer._gaussian_similarity ──────────────────────────────


def test_gaussian_similarity_exact_match():
    assert _gaussian_similarity(5.0, 5.0, 1.0) == 1.0


def test_gaussian_similarity_close_match():
    score = _gaussian_similarity(5.5, 5.0, 1.0)
    assert 0.6 < score < 1.0


def test_gaussian_similarity_far_match():
    score = _gaussian_similarity(10.0, 5.0, 1.0)
    assert score < 0.01


def test_gaussian_similarity_zero_tolerance():
    assert _gaussian_similarity(5.0, 5.0, 0) == 1.0
    assert _gaussian_similarity(5.0, 5.1, 0) == 0.0


# ── StyleScorer.score (integration) ────────────────────────────────


def test_score_with_no_profile_passes():
    """If no profile exists, score should be 1.0 (no penalty)."""
    scorer = StyleScorer.__new__(StyleScorer)
    scorer.style_path = Path("/tmp/nonexistent_style.json")
    result = scorer.score("any text here", "xiaobai")
    assert result["score"] == 1.0
    assert result["passed"] is True
    assert result["reason"] == "no_style_profile_yet"


def test_score_with_matching_profile_passes(tmp_path=None):
    """If candidate matches profile, score should be high."""
    scorer = StyleScorer.__new__(StyleScorer)
    # Build a candidate that matches the profile
    candidate_text = """标题 🤯

🔧 方法很简单。第一步：打开 AI 工具，把你这周干的零碎事都丢进去。
第二步：发一句话指令，让它帮你整理成结构化内容。
第三步：复制粘贴到周报模板里，完事儿。

🎯 实测效果。以前写周报要半小时，现在 5 分钟搞定。
领导反馈最近周报写得越来越规范了，AI 帮我全过滤了废话。

💡 不只是周报。月报、述职、会议纪要都能用。

你用哪个 AI 工具？评论区聊聊？

#打工人效率工具 #AI工具推荐 #职场干货 #零基础也能用 #周报
"""
    profile = {
        "sample_size": 3,
        "emoji_density": 1.5,
        "sent_length_mean": 20,
        "para_lines_mean": 1.5,
        "emoji_section_count": 4,
        "punct_ratio": {"？": 0.3, "。": 0.5, "其他": 0.2, "！": 0, "...": 0},
        "first_words": ["标题"],  # matches candidate's first sentence "标题 🤯..."
        "closing_phrases": ["评论区聊"],  # matches candidate's last sentence
    }
    import json as _json
    fake_path = Path(tempfile.mktemp(suffix=".json"))
    fake_path.write_text(_json.dumps({"xiaobai": profile, "deep_tech": {}}))
    scorer.style_path = fake_path

    result = scorer.score(candidate_text, "xiaobai")
    assert result["passed"], f"Score: {result['score']}, dimensions: {result.get('dimension_scores')}"
    assert result["score"] >= 0.65


def test_score_with_unrelated_text_fails():
    """An English technical writeup should fail a xiaobai style check."""
    scorer = StyleScorer.__new__(StyleScorer)
    candidate_text = """Implementation Details

The system architecture consists of several microservices communicating via gRPC.
Performance benchmarks show significant improvements over the legacy implementation.
We have validated the approach through extensive testing in production environments.
"""
    profile = {
        "sample_size": 3,
        "emoji_density": 2.0,
        "sent_length_mean": 20,
        "para_lines_mean": 1.0,
        "emoji_section_count": 6,
        "punct_ratio": {"？": 0.5, "。": 0.3, "其他": 0.2, "！": 0, "...": 0},
    }
    import json as _json
    fake_path = Path(tempfile.mktemp(suffix=".json"))
    fake_path.write_text(_json.dumps({"xiaobai": profile, "deep_tech": {}}))
    scorer.style_path = fake_path

    result = scorer.score(candidate_text, "xiaobai")
    # No emoji, no question marks, no Chinese → should fail
    assert not result["passed"]
    assert result["score"] < 0.65
