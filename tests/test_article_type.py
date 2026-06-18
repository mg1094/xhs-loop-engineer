"""Tests for shared utility functions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import detect_article_type


def test_detect_xiaobai_chinese():
    assert detect_article_type("AI 写周报") == "xiaobai"
    assert detect_article_type("打工人必备 5 个 AI 工具") == "xiaobai"


def test_detect_deep_tech_chinese():
    assert detect_article_type("MinerU 源码深度拆解") == "deep_tech"
    assert detect_article_type("AI Agent 架构分析") == "deep_tech"
    assert detect_article_type("PaddleOCR 技术对比") == "deep_tech"


def test_detect_deep_tech_english():
    assert detect_article_type("Open source AI architecture deep dive") == "deep_tech"
    assert detect_article_type("Build a tech blog with React") == "deep_tech"


def test_detect_xiaobai_english():
    assert detect_article_type("How I use AI to write weekly reports") == "xiaobai"
    assert detect_article_type("Top 5 AI tools for office workers") == "xiaobai"
