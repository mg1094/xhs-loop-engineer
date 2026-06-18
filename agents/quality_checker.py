"""
Agent 3: 质量验证
检查生成内容是否符合发布标准：敏感词、风格一致性、内容质量。
"""

import yaml
import re
from pathlib import Path


class QualityChecker:
    def __init__(
        self,
        style_path: str = "config/style.yaml",
    ):
        with open(style_path) as f:
            self.style = yaml.safe_load(f)
        self.forbidden_words = self.style["content_rules"]["forbidden_words"]

    def check_forbidden_words(self, text: str) -> list[str]:
        """检查敏感词"""
        found = []
        for word in self.forbidden_words:
            if word in text:
                found.append(word)
        return found

    def check_title(self, text: str) -> dict:
        """检查标题"""
        lines = text.strip().split("\n")
        title = lines[0] if lines else ""

        issues = []
        # 长度检查
        if len(title) < 10:
            issues.append("标题太短（<10字）")
        if len(title) > 30:
            issues.append("标题太长（>30字）")

        # emoji 检查
        if not any("☀" <= c <= "➿" or "\U0001F000" <= c <= "\U0001FFFF" or c in "😀😁😂🤣😃😄😅😆😉😊😋😎😍😘😗😙😚☺🙂🤗🤩🤔🤨😐😑😶🙄😏😣😥😮🤐😯😪😫😴😌😛😜😝🤤😒😓😔😕🙃🤑😲☹🙁😖😞😟😤😢😭😦😧😨😩🤯😬😰😱😳🤪😵😡😠🤬😷🤒🤕🤢🤮🤧😇🤠🤡🤥🤫🤭🧐🤓😈👿👹👺💀👻👽🤖💩😺😸😹😻😼😽🙀😿😾" for c in title):
            issues.append("标题缺少 emoji")

        return {"pass": len(issues) == 0, "issues": issues, "title": title}

    def check_structure(self, text: str) -> dict:
        """检查正文结构"""
        issues = []
        lines = text.strip().split("\n")

        # 检查段落长度
        current_para_len = 0
        for line in lines:
            if line.strip():
                current_para_len += 1
            else:
                if current_para_len > 5:
                    issues.append(f"存在过长段落（{current_para_len}行）")
                current_para_len = 0

        # 检查 emoji 分段标记
        emoji_separator = re.findall(r"[🔧🎯💡⚠️📖🔌🔄🏗️🏢🧠📊🔍📝🤯😎🔥📄]", text)
        if len(emoji_separator) < 3:
            issues.append("emoji 分段标记不足（建议 ≥3 个）")

        # 检查字数
        content_only = text.split("---")[-1] if "---" in text else text
        # 去掉标签
        content_only = re.sub(r"#[\w一-鿿]+", "", content_only)
        char_count = len(content_only.replace("\n", "").replace(" ", ""))
        if char_count < 200:
            issues.append(f"内容太短（{char_count}字，建议 >200）")

        return {"pass": len(issues) == 0, "issues": issues, "char_count": char_count}

    def check_tags(self, text: str) -> dict:
        """检查标签"""
        tags = re.findall(r"#[\w一-鿿]+", text)
        issues = []

        if len(tags) < 5:
            issues.append(f"标签太少（{len(tags)}个，建议 5-10 个）")
        if len(tags) > 12:
            issues.append(f"标签太多（{len(tags)}个，建议 5-10 个）")

        # 检查是否有默认标签
        default_tags = self.style.get("tags", {}).get("default", [])
        missing_defaults = [t for t in default_tags if t not in tags]
        if missing_defaults:
            issues.append(f"缺少常用标签：{missing_defaults}")

        return {"pass": len(issues) == 0, "issues": issues, "tags": tags}

    def check_interaction(self, text: str) -> dict:
        """检查互动引导"""
        interaction_patterns = [
            "评论区",
            "留言",
            "点赞",
            "收藏",
            "关注",
            "你怎么",
            "你用什么",
            "点菜",
            "想看什么",
        ]
        found = [p for p in interaction_patterns if p in text]

        if not found:
            return {
                "pass": False,
                "issues": ["缺少评论区互动引导"],
                "suggestion": "在结尾加上「你用什么工具？评论区聊聊」之类的引导",
            }

        return {"pass": True, "issues": [], "found_interactions": found}

    def run(self, content: str, article_type: str = "xiaobai") -> dict:
        """运行所有检查"""
        results = {
            "forbidden_words": self.check_forbidden_words(content),
            "title": self.check_title(content),
            "structure": self.check_structure(content),
            "tags": self.check_tags(content),
            "interaction": self.check_interaction(content),
        }

        # 汇总
        all_issues = []
        for check_name, result in results.items():
            if isinstance(result, dict) and "issues" in result:
                all_issues.extend(result["issues"])
            elif isinstance(result, list):
                if result:
                    all_issues.append(f"发现敏感词：{result}")

        passed = len(all_issues) == 0
        score = max(1, 10 - len(all_issues))

        return {
            "pass": passed,
            "score": score,
            "issues": all_issues,
            "details": results,
            "status": "verified" if passed else "needs_revision",
        }
