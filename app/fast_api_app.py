"""Production HTTP surface for Cloud Run and the hackathon demo."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.adk.cli.fast_api import get_fast_api_app

from .cloud_run import background_research_available, launch_research_job

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_ROOT / "app" / "static"

app = get_fast_api_app(
    agents_dir=str(PROJECT_ROOT / "app"),
    web=False,
    a2a=False,
    use_local_storage=False,
    allow_origins=[os.getenv("CLOUD_RESEARCH_ORIGIN", "*")],
    auto_create_session=True,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/healthz")
@app.get("/api/health")
async def healthz() -> dict[str, str]:
    return {
        "service": "cloud-research",
        "model": os.getenv("CLOUD_RESEARCH_MODEL", "gemini-3.7-flash"),
        "agent_framework": "Google ADK",
        "infrastructure": "Google Cloud Run",
    }


@app.get("/api/about")
async def about() -> dict[str, object]:
    return {
        "thesis": "Every researcher becomes the PI of a persistent team of AI experts.",
        "stack": ["Gemini 3.7 Flash", "Google ADK", "Google Cloud Run"],
        "experts": ["Finder", "Theorist", "Experimentalist", "Critic", "Writer", "Explainer"],
        "philosophy": ["Concise", "Excited by truth", "Certain a valuable opening exists"],
        "background_research": background_research_available(),
    }


@app.post("/api/dispatch")
async def dispatch(request: Request) -> dict[str, str]:
    body = await request.json()
    brief = str(body.get("brief", "")).strip()
    if not brief:
        raise HTTPException(status_code=400, detail="A research brief is required.")
    if not background_research_available():
        raise HTTPException(status_code=503, detail="Background research is not configured.")
    return launch_research_job(brief)
