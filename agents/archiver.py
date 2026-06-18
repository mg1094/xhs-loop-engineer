"""
Agent 4: Archiver + Notifier
Saves generated content to Obsidian and sends desktop notifications.
"""

import yaml
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime


# Unicode emoji ranges — same conservative set as quality_checker
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000027BF"
    "]+",
    flags=re.UNICODE,
)


class Archiver:
    def __init__(self, config_path: str = "config/schedule.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.vault = Path(
            self.config["obsidian"]["vault_path"].replace("~", str(Path.home()))
        ).expanduser()

    def save_to_obsidian(
        self, content: str, topic: str, article_type: str = "xiaobai"
    ) -> Path:
        """Save content to a pending folder in the Obsidian vault."""
        published_dir = self.vault / self.config["obsidian"]["published_dir"]
        article_num = (
            len(list(published_dir.glob("*.md"))) + 1 if published_dir.exists() else 1
        )
        slug = re.sub(r"[^\w\-]", "-", topic[:20]).strip("-")
        filename = f"{article_num:03d}-{slug}.md"

        pending_dir = self.vault / "小红书" / "待发布"
        pending_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        frontmatter = (
            "---\n"
            f"title: {filename}\n"
            f"date: {date_str}\n"
            "tags:\n"
            f"  - 待发布\n"
            f"  - {article_type}\n"
            "---\n\n"
        )

        filepath = pending_dir / filename
        filepath.write_text(frontmatter + content, encoding="utf-8")
        return filepath

    def update_dashboard(self, article_info: dict):
        """Patch the dashboard markdown with the latest run metadata."""
        dashboard = self.vault / self.config["obsidian"]["dashboard_file"]
        if not dashboard.exists():
            return

        content = dashboard.read_text(encoding="utf-8")
        date_str = datetime.now().strftime("%Y-%m-%d")
        article_num = article_info.get("num", "???")

        new_content = content.replace(
            f"### {article_num} ·",
            f"### {article_num} · {article_info.get('topic', '')} ({date_str})",
        )
        dashboard.write_text(new_content, encoding="utf-8")

    def send_notification(self, title: str, body: str):
        """Send a desktop notification (macOS-first, with Linux fallback)."""
        try:
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'display notification "{body}" with title "{title}"',
                ],
                check=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            try:
                subprocess.run(
                    ["terminal-notifier", "-title", title, "-message", body],
                    check=True,
                    timeout=5,
                )
            except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
                # Final fallback: stdout
                print(f"\n📢 {title}\n{body}\n")

    def run(
        self, content: str, topic: str, article_type: str = "xiaobai"
    ) -> dict:
        """Save content, notify user, persist loop state."""
        filepath = self.save_to_obsidian(content, topic, article_type)

        notif_config = self.config.get("notification", {})
        title = notif_config.get("title_template", "📝 New draft ready")
        body = notif_config.get("body_template", "").format(
            topic=topic, word_count=len(content)
        )
        self.send_notification(title, body)

        state = {
            "last_run": datetime.now().isoformat(),
            "last_topic": topic,
            "last_file": str(filepath),
            "status": "published",
        }
        state_file = Path("state/loop_state.json")
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False))

        return {
            "filepath": str(filepath),
            "notification_sent": True,
            "status": "archived",
            "message": f"Saved to {filepath} — open Obsidian to review",
        }
