"""Style learning and scoring endpoints."""

import json
from pathlib import Path

import yaml
from fastapi import APIRouter
from pydantic import BaseModel

from agents.style_learner import StyleLearner
from agents.style_scorer import StyleScorer

router = APIRouter()


def _vault():
    with open("config/schedule.yaml") as f:
        cfg = yaml.safe_load(f)
    return Path(cfg["obsidian"]["vault_path"].replace("~", str(Path.home()))).expanduser()


@router.post("/learn")
def learn_style():
    """Re-learn style from all published articles."""
    learner = StyleLearner()
    profile = learner.run()
    return {"status": "ok", "profile": profile}


@router.get("/profile")
def get_profile():
    """Return the current style profile."""
    style_path = _vault() / "小红书" / "style_profile.json"
    if not style_path.exists():
        return {"xiaobai": {}, "deep_tech": {}}
    return json.loads(style_path.read_text(encoding="utf-8"))


class ScoreRequest(BaseModel):
    content: str
    article_type: str = "xiaobai"


@router.post("/score")
def score_content(req: ScoreRequest):
    """Score a draft against the learned style profile."""
    return StyleScorer().score(req.content, req.article_type)
