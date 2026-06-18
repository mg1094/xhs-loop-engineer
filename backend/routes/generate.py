"""Content generation endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from agents import detect_article_type
from agents.content_writer import ContentWriter
from agents.quality_checker import QualityChecker
from agents.style_scorer import StyleScorer

router = APIRouter()


class GenerateRequest(BaseModel):
    topic: str
    article_type: str | None = None  # auto-detect if None
    backend: str = "openai"
    model: str | None = None
    api_key: str | None = None
    api_base: str | None = None


class GenerateResponse(BaseModel):
    topic: str
    article_type: str
    title: str
    content: str
    rule_check: dict
    style_score: dict
    backend: str
    model: str
    passed: bool


@router.post("", response_model=GenerateResponse)
def generate_article(req: GenerateRequest):
    """Generate an article, verify it, and return results."""
    article_type = req.article_type or detect_article_type(req.topic)

    # Step 1: Generate content via LLM
    writer = ContentWriter()
    gen_result = writer.generate(
        topic=req.topic,
        article_type=article_type,
        backend=req.backend,
        model=req.model,
        api_key=req.api_key,
        api_base=req.api_base,
    )

    if gen_result.get("status") != "generated" or not gen_result.get("content"):
        # Fall back to prompt-only response for manual mode
        if req.backend == "manual":
            return {
                "topic": req.topic,
                "article_type": article_type,
                "title": req.topic,
                "content": "",
                "rule_check": {"pass": False, "issues": ["Manual mode: please paste content"], "score": 0},
                "style_score": {"score": 0, "passed": False, "reason": "no_content"},
                "backend": "manual",
                "model": req.model or "n/a",
                "passed": False,
            }
        # Real backend but failed
        return {
            "topic": req.topic,
            "article_type": article_type,
            "title": req.topic,
            "content": "",
            "rule_check": {"pass": False, "issues": [gen_result.get("message", "generation failed")], "score": 0},
            "style_score": {"score": 0, "passed": False},
            "backend": req.backend,
            "model": req.model or "n/a",
            "passed": False,
        }

    content = gen_result["content"]

    # Extract title (first line)
    title = content.strip().split("\n")[0]

    # Step 2: Rule check
    rule_check = QualityChecker().run(content, article_type)

    # Step 3: Style score
    style_score = StyleScorer().score(content, article_type)

    passed = rule_check.get("pass", False) and style_score.get("passed", False)

    return GenerateResponse(
        topic=req.topic,
        article_type=article_type,
        title=title,
        content=content,
        rule_check=rule_check,
        style_score=style_score,
        backend=req.backend,
        model=req.model or "default",
        passed=passed,
    )


@router.post("/save")
def save_article(topic: str, content: str, article_type: str = "xiaobai"):
    """Save a verified article to the Obsidian vault's pending folder."""
    from agents.archiver import Archiver

    result = Archiver().run(content, topic, article_type)
    return result
