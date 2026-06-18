"""
Style Scorer — measures how closely a candidate draft matches your style profile.

Returns a 0-1 score; >= 0.7 means "matches your style".
"""

import re
import json
import yaml
from pathlib import Path
from statistics import mean
from math import exp

from agents.style_learner import (
    _EMOJI_RE,
    _strip_frontmatter,
    _split_sentences,
    _PARA_SPLIT_RE,
    _extract_emoji_sections,
)


def _gaussian_similarity(value: float, target: float, tolerance: float) -> float:
    """Score 0-1: how close `value` is to `target` within `tolerance`."""
    if tolerance == 0:
        return 1.0 if value == target else 0.0
    diff = abs(value - target) / tolerance
    return exp(-0.5 * diff ** 2)


class StyleScorer:
    # Weights for each style dimension
    WEIGHTS = {
        "emoji_density": 0.20,
        "sent_length": 0.20,
        "para_lines": 0.10,
        "section_count": 0.10,
        "punct_ratio": 0.15,
        "opening_match": 0.10,
        "closing_match": 0.15,
    }

    PASS_THRESHOLD = 0.65

    def __init__(
        self,
        config_path: str = "config/schedule.yaml",
    ):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.vault = Path(
            self.config["obsidian"]["vault_path"].replace("~", str(Path.home()))
        ).expanduser()
        self.style_path = self.vault / "小红书" / "style_profile.json"

    def load_profile(self, article_type: str = "xiaobai") -> dict:
        if not self.style_path.exists():
            return {}
        profile = json.loads(self.style_path.read_text(encoding="utf-8"))
        return profile.get(article_type, {})

    def extract_candidate_features(self, text: str) -> dict:
        text = _strip_frontmatter(text)
        text = re.sub(r"#[\w一-鿿]+", "", text)
        text = re.sub(r"\s+", " ", text).strip()

        sentences = _split_sentences(text)
        paragraphs = [p.strip() for p in _PARA_SPLIT_RE.split(text) if p.strip()]
        emojis = _EMOJI_RE.findall(text)
        emoji_sections = _extract_emoji_sections(text)

        sent_lengths = [len(s) for s in sentences]
        para_lines = [len(p.split("\n")) for p in paragraphs]

        punct_count = {"？": 0, "！": 0, "。": 0, "其他": 0}
        for s in sentences:
            if "？" in s:
                punct_count["？"] += 1
            elif "！" in s:
                punct_count["！"] += 1
            elif "。" in s:
                punct_count["。"] += 1
            else:
                punct_count["其他"] += 1

        total_punct = sum(punct_count.values()) or 1
        punct_ratio = {k: v / total_punct for k, v in punct_count.items()}

        return {
            "char_count": len(text),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "emoji_section_count": len(emoji_sections),
            "emoji_density": len(emojis) / max(len(text), 1) * 100,
            "sent_length_mean": mean(sent_lengths) if sent_lengths else 0,
            "para_lines_mean": mean(para_lines) if para_lines else 0,
            "punct_ratio": punct_ratio,
            "first_sentence": sentences[0][:8] if sentences else "",
            "last_sentence": sentences[-1][:15] if sentences else "",
        }

    def score(
        self, candidate_text: str, article_type: str = "xiaobai"
    ) -> dict:
        """Score 0-1 of how well candidate matches the learned profile."""
        profile = self.load_profile(article_type)

        # No profile = cold start; default to passing
        if not profile or profile.get("sample_size", 0) == 0:
            return {
                "score": 1.0,
                "passed": True,
                "reason": "no_style_profile_yet",
                "message": "No style profile found — skipping style check (run `learn-style` first)",
            }

        candidate = self.extract_candidate_features(candidate_text)

        # Per-dimension scores
        scores = {}

        # Emoji density (target within 1.5 percentage points)
        scores["emoji_density"] = _gaussian_similarity(
            candidate["emoji_density"],
            profile.get("emoji_density", 1.0),
            tolerance=1.5,
        )

        # Sentence length (target within 15 chars — more forgiving)
        scores["sent_length"] = _gaussian_similarity(
            candidate["sent_length_mean"],
            profile.get("sent_length_mean", 15),
            tolerance=15.0,
        )

        # Paragraph lines (target within 1 line)
        scores["para_lines"] = _gaussian_similarity(
            candidate["para_lines_mean"],
            profile.get("para_lines_mean", 2),
            tolerance=1.0,
        )

        # Section count (target within 3 sections — forgiving for variety)
        scores["section_count"] = _gaussian_similarity(
            candidate["emoji_section_count"],
            profile.get("emoji_section_count", 5),
            tolerance=3.0,
        )

        # Punctuation distribution: cosine similarity between ratios
        profile_punct = profile.get("punct_ratio", {})
        score_punct = 0.0
        all_keys = set(profile_punct.keys()) | set(candidate["punct_ratio"].keys())
        if all_keys:
            dot = sum(
                profile_punct.get(k, 0) * candidate["punct_ratio"].get(k, 0)
                for k in all_keys
            )
            mag_p = sum(v ** 2 for v in profile_punct.values()) ** 0.5
            mag_c = sum(v ** 2 for v in candidate["punct_ratio"].values()) ** 0.5
            if mag_p and mag_c:
                score_punct = dot / (mag_p * mag_c)
        scores["punct_ratio"] = score_punct

        # Opening phrase match
        first_words = profile.get("first_words", [])
        opening_match = 0.0
        if first_words and candidate["first_sentence"]:
            for w in first_words:
                if w and w in candidate["first_sentence"]:
                    opening_match = 1.0
                    break
        scores["opening_match"] = opening_match

        # Closing phrase match
        closing_phrases = profile.get("closing_phrases", [])
        closing_match = 0.0
        if closing_phrases and candidate["last_sentence"]:
            for c in closing_phrases:
                if c and c in candidate["last_sentence"]:
                    closing_match = 1.0
                    break
        scores["closing_match"] = closing_match

        # Weighted total
        total = sum(scores[k] * self.WEIGHTS.get(k, 0) for k in scores)
        total = max(0.0, min(1.0, total))

        return {
            "score": round(total, 3),
            "passed": total >= self.PASS_THRESHOLD,
            "threshold": self.PASS_THRESHOLD,
            "dimension_scores": {k: round(v, 3) for k, v in scores.items()},
            "article_type": article_type,
            "sample_size": profile.get("sample_size", 0),
        }
