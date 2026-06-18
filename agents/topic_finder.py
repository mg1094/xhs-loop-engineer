"""
Agent 1: 选题发现
读取 Obsidian 选题库和数据看板，生成 3 个候选选题。
"""

import yaml
import json
from pathlib import Path


class TopicFinder:
    def __init__(self, config_path: str = "config/schedule.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.vault = Path(
            self.config["obsidian"]["vault_path"].replace("~", str(Path.home()))
        ).expanduser()

    def get_existing_articles(self) -> list[str]:
        """获取已发布文章列表"""
        published = self.vault / self.config["obsidian"]["published_dir"]
        if published.exists():
            return [f.stem for f in published.glob("*.md")]
        return []

    def get_topic_pool(self) -> list[str]:
        """获取选题库待写"""
        topics_file = self.vault / self.config["obsidian"]["topics_file"]
        if topics_file.exists():
            content = topics_file.read_text(encoding="utf-8")
            # 提取所有 - [ ] 开头的行
            topics = []
            for line in content.split("\n"):
                if line.strip().startswith("- [ ]"):
                    topics.append(line.strip()[6:])
            return topics
        return []

    def get_data_summary(self) -> dict:
        """获取数据摘要"""
        dashboard = self.vault / self.config["obsidian"]["dashboard_file"]
        if dashboard.exists():
            content = dashboard.read_text(encoding="utf-8")
            return {"raw": content[:2000]}  # 截取前 2000 字符
        return {"raw": "暂无数据"}

    def run(self) -> dict:
        """运行选题发现，返回候选选题"""
        existing = self.get_existing_articles()
        pool = self.get_topic_pool()
        data = self.get_data_summary()

        return {
            "existing_articles": existing,
            "topic_pool": pool,
            "data_summary": data,
            "status": "ready_for_selection",
            "message": f"已读取 {len(existing)} 篇已发文章，{len(pool)} 个待写选题",
        }
