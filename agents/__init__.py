"""
XHS Loop Engineer - Agent modules.

Agents:
    - topic_finder: Discovers candidate topics from Obsidian vault
    - content_writer: Generates Xiaohongshu posts via LLM
    - quality_checker: Validates content quality and style compliance
    - archiver: Saves content to Obsidian and sends notifications
"""

# Shared utilities for all agents

DEEP_TECH_KEYWORDS = (
    "源码",
    "架构",
    "深度",
    "拆解",
    "技术",
    "分析",
    "评测",
    "对比",
    "原理",
    "源码",
    "code",
    "arch",
    "deep",
    "tech",
)


def detect_article_type(topic: str) -> str:
    """Classify a topic as 'xiaobai' or 'deep_tech' based on keyword heuristics."""
    topic_lower = topic.lower()
    if any(kw in topic_lower for kw in DEEP_TECH_KEYWORDS):
        return "deep_tech"
    return "xiaobai"
