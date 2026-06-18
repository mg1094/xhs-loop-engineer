"""
FastAPI backend for XHS Loop Engineer.

Run with:
    uv run python backend/main.py
or:
    uv run uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import articles, generate, style, settings

app = FastAPI(
    title="XHS Loop Engineer API",
    description="Xiaohongshu content automation backend",
    version="0.1.0",
)

# CORS — allow Vue dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "xhs-loop-engineer"}


app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(generate.router, prefix="/api/generate", tags=["generate"])
app.include_router(style.router, prefix="/api/style", tags=["style"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
