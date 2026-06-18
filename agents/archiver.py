"""
Agent 4: 归档 + 通知
将生成的内容写入 Obsidian，更新数据看板，发送桌面通知。
"""

import yaml
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime


class Archiver:
    def __init__(
        self,
        config_path: str = "config/schedule.yaml",
    ):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.vault = Path(
            self.config["obsidian"]["vault_path"].replace("~", str(Path.home()))
        ).expanduser()

    def save_to_obsidian(
        self, content: str, topic: str, article_type: str = "xiaobai"
    ) -> Path:
        """保存内容到 Obsidian"""
        # 生成文件名
        article_num = len(list((self.vault / self.config["obsidian"]["published_dir"]).glob("*.md"))) + 1
        slug = topic[:20].replace(" ", "-").replace("/", "-")
        filename = f"{article_num:03d}-{slug}.md"

        # 确定保存目录
        pending_dir = self.vault / "小红书" / "待发布"
        pending_dir.mkdir(parents=True, exist_ok=True)

        # 写入 frontmatter
        date_str = datetime.now().strftime("%Y-%m-%d")
        full_content = f"""---
title: {filename}
date: {date_str}
tags:
  - 待发布
  - {article_type}
---

{content}
"""

        filepath = pending_dir / filename
        filepath.write_text(full_content, encoding="utf-8")
        return filepath

    def update_dashboard(self, article_info: dict):
        """更新数据看板"""
        dashboard = self.vault / self.config["obsidian"]["dashboard_file"]
        if not dashboard.exists():
            return

        content = dashboard.read_text(encoding="utf-8")
        date_str = datetime.now().strftime("%Y-%m-%d")

        # 在对应编号处更新发布日期
        article_num = article_info.get("num", "???")
        update_line = f"| 发布日期 | {date_str} |"

        # 简单替换
        new_content = content.replace(
            f"### {article_num} ·",
            f"### {article_num} · {article_info.get('topic', '')}",
        )

        dashboard.write_text(new_content, encoding="utf-8")

    def send_notification(self, title: str, body: str):
        """发送桌面通知"""
        try:
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'display notification "{body}" with title "{title}"',
                ],
                timeout=5,
            )
        except Exception:
            # macOS 通知失败时，用 terminal-notifier 或 echo
            try:
                subprocess.run(
                    ["terminal-notifier", "-title", title, "-message", body],
                    timeout=5,
                )
            except Exception:
                print(f"\n📢 {title}\n{body}\n")

    def run(self, content: str, topic: str, article_type: str = "xiaobai") -> dict:
        """执行归档和通知"""
        # 保存到 Obsidian
        filepath = self.save_to_obsidian(content, topic, article_type)

        # 通知
        notif_config = self.config.get("notification", {})
        title = notif_config.get("title_template", "📝 新稿子已生成")
        body = notif_config.get("body_template", "").format(
            topic=topic,
            word_count=len(content),
        )
        self.send_notification(title, body)

        # 更新状态文件
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
            "message": f"已保存到 {filepath}，请前往 Obsidian 查看",
        }
