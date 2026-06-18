"""
Agent 2: 内容生成
根据选定选题和风格指南，调用 LLM 生成小红书正文。
"""

import yaml
from pathlib import Path


class ContentWriter:
    def __init__(
        self,
        config_path: str = "config/schedule.yaml",
        style_path: str = "config/style.yaml",
    ):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        with open(style_path) as f:
            self.style = yaml.safe_load(f)

    def build_prompt(self, topic: str, article_type: str = "xiaobai") -> str:
        """构建内容生成 prompt"""
        prompt_template = Path("prompts/content_writer.md").read_text(encoding="utf-8")

        style_summary = yaml.dump(self.style, allow_unicode=True, default_flow_style=False)

        return prompt_template.format(
            style_guide=style_summary,
            topic=topic,
            article_type=article_type,
        )

    def run(self, topic: str, article_type: str = "xiaobai") -> dict:
        """生成内容"""
        prompt = self.build_prompt(topic, article_type)

        return {
            "topic": topic,
            "type": article_type,
            "prompt": prompt,
            "status": "prompt_ready",
            "message": "请将此 prompt 发送给 Claude 生成内容，生成后调用 archiver 归档",
        }
