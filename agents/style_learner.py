"""
Style Learner — extracts your writing style from published articles.

Reads your published articles from Obsidian, computes a style profile,
saves it for the style scorer to use later.

Style dimensions:
    - sentence_length: mean and std of sentence character count
    - emoji_density: emojis per 100 chars
    - sentence_punct_ratio: distribution of ？/。/！/...
    - paragraph_lines: average lines per paragraph
    - section_count: number of emoji-marked sections
    - hook_phrases: recurring opening phrases
    - closing_phrases: recurring CTA patterns
"""

import re
import json
import yaml
from pathlib import Path
from datetime import datetime
from statistics import mean, pstdev

# Reuse the conservative emoji range from quality_checker
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

_SENT_SPLIT_RE = re.compile(
    r"(?<=[。！？])\s*|(?<=[.!?])\s+"  # Chinese full-width punct + English half-width
)
_PARA_SPLIT_RE = re.compile(r"\n[ \t]*\n")


def _extract_emoji_sections(text: str) -> list[str]:
    """Split text into sections marked by leading emoji."""
    sections = []
    current: list[str] = []
    for line in text.split("\n"):
        if _EMOJI_RE.match(line):
            if current:
                sections.append("\n".join(current))
            current = [line]
        elif current:
            current.append(line)
    if current:
        sections.append("\n".join(current))
    return sections


def _strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter from a markdown file."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5 :]
    return text


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences (Chinese + English)."""
    sentences = _SENT_SPLIT_RE.split(text)
    return [s.strip() for s in sentences if s.strip()]


class StyleLearner:
    def __init__(
        self,
        config_path: str = "config/schedule.yaml",
        style_path: str = "config/style.yaml",
    ):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        with open(style_path) as f:
            self.style_config = yaml.safe_load(f)

        self.vault = Path(
            self.config["obsidian"]["vault_path"].replace("~", str(Path.home()))
        ).expanduser()
        self.published_dir = (
            self.vault / self.config["obsidian"]["published_dir"]
        )
        self.style_path = self.vault / "小红书" / "style_profile.json"

    # ── feature extraction ────────────────────────────────────────

    def extract_features(self, text: str) -> dict:
        """Compute all style features for a single article."""
        text = _strip_frontmatter(text)
        text = re.sub(r"#[\w一-鿿]+", "", text)  # strip hashtags

        # IMPORTANT: do NOT collapse newlines — we need paragraph structure.
        # Only collapse runs of spaces/tabs within each line.
        text = re.sub(r"[ \t]+", " ", text)

        # Trim each line individually, but keep newlines.
        text = "\n".join(line.strip() for line in text.split("\n"))

        sentences = _split_sentences(text)
        paragraphs = [p.strip() for p in _PARA_SPLIT_RE.split(text) if p.strip()]
        emojis = _EMOJI_RE.findall(text)
        emoji_sections = _extract_emoji_sections(text)

        sent_lengths = [len(s) for s in sentences]
        para_lines = [len(p.split("\n")) for p in paragraphs]

        # Punctuation distribution
        punct_count = {"？": 0, "！": 0, "。": 0, "...": 0, "其他": 0}
        for s in sentences:
            if "？" in s:
                punct_count["？"] += 1
            elif "！" in s:
                punct_count["！"] += 1
            elif "。" in s:
                punct_count["。"] += 1
            elif "..." in s or "…" in s:
                punct_count["..."] += 1
            else:
                punct_count["其他"] += 1

        total_punct = sum(punct_count.values()) or 1
        punct_ratio = {k: v / total_punct for k, v in punct_count.items()}

        # Hook phrases: first 3 words of each article
        first_words = []
        for s in sentences[:3]:
            first_words.append(s[:8])

        # Closing patterns: last 2 sentences
        closing_phrases = [s[:15] for s in sentences[-2:]]

        return {
            "char_count": len(text.replace("\n", "")),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "emoji_section_count": len(emoji_sections),
            "emoji_count": len(emojis),
            "emoji_density": len(emojis) / max(len(text), 1) * 100,
            "sent_length_mean": mean(sent_lengths) if sent_lengths else 0,
            "sent_length_std": pstdev(sent_lengths) if len(sent_lengths) > 1 else 0,
            "para_lines_mean": mean(para_lines) if para_lines else 0,
            "punct_ratio": punct_ratio,
            "first_words": first_words,
            "closing_phrases": closing_phrases,
        }

    # ── profile aggregation ───────────────────────────────────────

    def _aggregate(self, feature_list: list[dict]) -> dict:
        """Aggregate per-article features into a single profile."""
        if not feature_list:
            return {}

        n = len(feature_list)

        def safe_mean(key):
            return mean(f[key] for f in feature_list)

        return {
            "sample_size": n,
            "char_count": safe_mean("char_count"),
            "sentence_count": safe_mean("sentence_count"),
            "paragraph_count": safe_mean("paragraph_count"),
            "emoji_section_count": safe_mean("emoji_section_count"),
            "emoji_count": safe_mean("emoji_count"),
            "emoji_density": safe_mean("emoji_density"),
            "sent_length_mean": safe_mean("sent_length_mean"),
            "sent_length_std": safe_mean("sent_length_std"),
            "para_lines_mean": safe_mean("para_lines_mean"),
            "punct_ratio": {
                k: mean(f["punct_ratio"][k] for f in feature_list)
                for k in ["？", "！", "。", "...", "其他"]
            },
            "first_words": [w for f in feature_list for w in f["first_words"]],
            "closing_phrases": [
                c for f in feature_list for c in f["closing_phrases"]
            ],
            "learned_at": datetime.now().isoformat(),
        }

    # ── main entry points ─────────────────────────────────────────

    def learn(self) -> dict:
        """Read all published articles and build style profiles per type."""
        if not self.published_dir.exists():
            return {"xiaobai": {}, "deep_tech": {}}

        xiaobai_features = []
        deep_tech_features = []

        for f in sorted(self.published_dir.glob("*.md")):
            text = f.read_text(encoding="utf-8")
            features = self.extract_features(text)
            article_type = self._classify(f.name, text)
            if article_type == "deep_tech":
                deep_tech_features.append(features)
            else:
                xiaobai_features.append(features)

        profile = {
            "xiaobai": self._aggregate(xiaobai_features),
            "deep_tech": self._aggregate(deep_tech_features),
        }

        return profile

    def _classify(self, filename: str, text: str) -> str:
        """Classify an article as xiaobai or deep_tech based on filename/content."""
        from agents import detect_article_type

        # Strip the article number prefix (e.g. "001-")
        title = re.sub(r"^\d+-", "", filename.replace(".md", ""))
        # Use the title (matches what topic_finder uses)
        if detect_article_type(title) == "deep_tech":
            return "deep_tech"
        return "xiaobai"

    def save(self, profile: dict):
        """Save the style profile to the Obsidian vault."""
        self.style_path.parent.mkdir(parents=True, exist_ok=True)
        self.style_path.write_text(
            json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def load(self) -> dict:
        """Load existing style profile from the Obsidian vault."""
        if self.style_path.exists():
            return json.loads(self.style_path.read_text(encoding="utf-8"))
        return {"xiaobai": {}, "deep_tech": {}}

    def run(self) -> dict:
        """Learn style from published articles and save the profile."""
        print("🔍 Learning style from published articles...")
        profile = self.learn()
        self.save(profile)

        xiaobai_n = profile.get("xiaobai", {}).get("sample_size", 0)
        deep_tech_n = profile.get("deep_tech", {}).get("sample_size", 0)
        print(
            f"   ✅ Learned from {xiaobai_n} xiaobai + {deep_tech_n} deep_tech articles"
        )
        print(f"   📁 Saved to: {self.style_path}")
        return profile
