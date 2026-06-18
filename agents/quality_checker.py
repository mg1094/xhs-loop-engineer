"""
Agent 3: Quality Verification
Validates content against publishing standards: forbidden words, style, structure, tags.
"""

import yaml
import re
from pathlib import Path


class QualityChecker:
    def __init__(self, style_path: str = "config/style.yaml"):
        with open(style_path) as f:
            self.style = yaml.safe_load(f)
        self.forbidden_words = self.style["content_rules"]["forbidden_words"]

        # Conservative emoji range — only well-known emoji blocks.
        # Avoid ranges that overlap with CJK (e.g. U+1F18E–U+1F251).
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # Emoticons
            "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
            "\U0001F680-\U0001F6FF"  # Transport and Map
            "\U0001F700-\U0001F77F"  # Alchemical
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "\U00002600-\U000027BF"  # Misc Symbols + Dingbats
            "]+",
            flags=re.UNICODE,
        )

    def check_forbidden_words(self, text: str) -> list[str]:
        """Check for forbidden words in content."""
        found = []
        for word in self.forbidden_words:
            if word in text:
                found.append(word)
        return found

    def check_title(self, text: str) -> dict:
        """Validate title format."""
        lines = text.strip().split("\n")
        title = lines[0] if lines else ""

        issues = []
        if len(title) < 10:
            issues.append(f"Title too short ({len(title)} chars, need >= 10)")
        if len(title) > 30:
            issues.append(f"Title too long ({len(title)} chars, need <= 30)")

        if not self.emoji_pattern.search(title):
            issues.append("Title missing emoji")

        return {"pass": len(issues) == 0, "issues": issues, "title": title}

    def check_structure(self, text: str) -> dict:
        """Validate body structure."""
        issues = []
        lines = text.strip().split("\n")

        # Check paragraph length
        current_para_len = 0
        for line in lines:
            if line.strip():
                current_para_len += 1
            else:
                if current_para_len > 5:
                    issues.append(f"Overlong paragraph ({current_para_len} lines)")
                current_para_len = 0

        # Check emoji section dividers
        emoji_sections = len(self.emoji_pattern.findall(text))
        if emoji_sections < 3:
            issues.append(f"Too few emoji dividers ({emoji_sections}, need >= 3)")

        # Check character count (excluding hashtags)
        content_only = re.sub(r"#[\w一-鿿]+", "", text)
        char_count = len(content_only.replace("\n", "").replace(" ", ""))
        if char_count < 200:
            issues.append(f"Content too short ({char_count} chars, need >= 200)")

        return {"pass": len(issues) == 0, "issues": issues, "char_count": char_count}

    def check_tags(self, text: str) -> dict:
        """Validate hashtags."""
        tags = re.findall(r"#[\w一-鿿]+", text)
        issues = []

        if len(tags) < 5:
            issues.append(f"Too few tags ({len(tags)}, need 5-10)")
        if len(tags) > 12:
            issues.append(f"Too many tags ({len(tags)}, need 5-10)")

        # Check default tags
        default_tags = self.style.get("tags", {}).get("default", [])
        # Normalize: strip leading '#' from defaults for comparison
        default_normalized = [t.lstrip("#") for t in default_tags]
        missing_defaults = [
            f"#{t}" for t in default_normalized if f"#{t}" not in tags
        ]
        if missing_defaults:
            issues.append(f"Missing recommended tags: {missing_defaults}")

        return {"pass": len(issues) == 0, "issues": issues, "tags": tags}

    def check_interaction(self, text: str) -> dict:
        """Verify interaction hook at the end."""
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
            "聊聊",
        ]
        found = [p for p in interaction_patterns if p in text]

        if not found:
            return {
                "pass": False,
                "issues": ["Missing comment-section interaction hook"],
                "suggestion": "Add a CTA like 'Which tool do you use? Comment below' at the end",
            }

        return {"pass": True, "issues": [], "found_interactions": found}

    def run(self, content: str, article_type: str = "xiaobai") -> dict:
        """Run all quality checks."""
        results = {
            "forbidden_words": self.check_forbidden_words(content),
            "title": self.check_title(content),
            "structure": self.check_structure(content),
            "tags": self.check_tags(content),
            "interaction": self.check_interaction(content),
        }

        all_issues = []
        for check_name, result in results.items():
            if isinstance(result, dict) and "issues" in result:
                all_issues.extend(result["issues"])
            elif isinstance(result, list):
                if result:
                    all_issues.append(f"Forbidden words found: {result}")

        passed = len(all_issues) == 0
        score = max(1, 10 - len(all_issues))

        return {
            "pass": passed,
            "score": score,
            "issues": all_issues,
            "details": results,
            "status": "verified" if passed else "needs_revision",
        }
