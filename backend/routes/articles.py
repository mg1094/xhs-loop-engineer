"""Article listing and dashboard endpoints."""

from pathlib import Path

import yaml
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


def _config():
    with open("config/schedule.yaml") as f:
        return yaml.safe_load(f)


def _vault():
    cfg = _config()
    return Path(cfg["obsidian"]["vault_path"].replace("~", str(Path.home()))).expanduser()


class ArticleSummary(BaseModel):
    filename: str
    title: str
    article_type: str
    date: str | None = None
    file_size: int = 0


class DashboardStats(BaseModel):
    total_articles: int
    xiaobai_count: int
    deep_tech_count: int
    style_profile_loaded: bool
    style_sample_size: int


@router.get("", response_model=list[ArticleSummary])
def list_articles():
    """List all published articles in the Obsidian vault."""
    cfg = _config()
    pub_dir = _vault() / cfg["obsidian"]["published_dir"]
    if not pub_dir.exists():
        return []

    items: list[ArticleSummary] = []
    from agents import detect_article_type

    for f in sorted(pub_dir.glob("*.md"), reverse=True):
        text = f.read_text(encoding="utf-8")
        # Extract title from frontmatter or filename
        title = f.stem
        date = None
        if text.startswith("---\n"):
            end = text.find("\n---\n", 4)
            if end != -1:
                fm = text[4:end]
                for line in fm.split("\n"):
                    if line.startswith("title:"):
                        title = line.split(":", 1)[1].strip()
                    if line.startswith("date:"):
                        date = line.split(":", 1)[1].strip()

        items.append(
            ArticleSummary(
                filename=f.name,
                title=title,
                article_type=detect_article_type(f.stem),
                date=date,
                file_size=f.stat().st_size,
            )
        )
    return items


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats():
    """Return aggregate stats for the dashboard."""
    cfg = _config()
    pub_dir = _vault() / cfg["obsidian"]["published_dir"]
    articles = list(pub_dir.glob("*.md")) if pub_dir.exists() else []

    from agents import detect_article_type

    xiaobai = sum(1 for a in articles if detect_article_type(a.stem) == "xiaobai")
    deep_tech = len(articles) - xiaobai

    style_path = _vault() / "小红书" / "style_profile.json"
    style_loaded = style_path.exists()
    sample_size = 0
    if style_loaded:
        import json

        profile = json.loads(style_path.read_text(encoding="utf-8"))
        sample_size = (
            profile.get("xiaobai", {}).get("sample_size", 0)
            + profile.get("deep_tech", {}).get("sample_size", 0)
        )

    return DashboardStats(
        total_articles=len(articles),
        xiaobai_count=xiaobai,
        deep_tech_count=deep_tech,
        style_profile_loaded=style_loaded,
        style_sample_size=sample_size,
    )
