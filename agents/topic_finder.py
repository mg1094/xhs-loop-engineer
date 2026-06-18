"""
Agent 1: Topic Finder
Reads the Obsidian topic pool and dashboard, surfaces candidate topics.
"""

import yaml
from pathlib import Path


class TopicFinder:
    def __init__(self, config_path: str = "config/schedule.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.vault = Path(
            self.config["obsidian"]["vault_path"].replace("~", str(Path.home()))
        ).expanduser()

    def get_existing_articles(self) -> list[str]:
        """List names of published articles."""
        published = self.vault / self.config["obsidian"]["published_dir"]
        if published.exists():
            return [f.stem for f in published.glob("*.md")]
        return []

    def get_topic_pool(self) -> list[str]:
        """Extract unchecked topics from the topic pool markdown file."""
        topics_file = self.vault / self.config["obsidian"]["topics_file"]
        if topics_file.exists():
            content = topics_file.read_text(encoding="utf-8")
            return [
                line.strip()[6:]
                for line in content.split("\n")
                if line.strip().startswith("- [ ]")
            ]
        return []

    def get_data_summary(self) -> dict:
        """Read a slice of the dashboard file as data summary context."""
        dashboard = self.vault / self.config["obsidian"]["dashboard_file"]
        if dashboard.exists():
            return {"raw": dashboard.read_text(encoding="utf-8")[:2000]}
        return {"raw": "no data yet"}

    def run(self) -> dict:
        """Surface the topic pool and recent article context."""
        existing = self.get_existing_articles()
        pool = self.get_topic_pool()
        data = self.get_data_summary()

        return {
            "existing_articles": existing,
            "topic_pool": pool,
            "data_summary": data,
            "status": "ready_for_selection",
            "message": (
                f"Loaded {len(existing)} published articles, "
                f"{len(pool)} pending topics"
            ),
        }
