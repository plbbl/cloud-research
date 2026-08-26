"""Public, HMAC-only GitHub event gateway; no model or lab UI is exposed."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request

from .firestore_labs import build_lab_store
from .github_events import GitHubEventError, dispatch_research_event
from .research_ledger import ledger

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LABS_FILE = Path(
    os.getenv("CLOUD_RESEARCH_LABS_FILE", PROJECT_ROOT / ".cloud-research" / "labs.json")
)
lab_store = build_lab_store(LABS_FILE, ledger)
app = FastAPI(title="Cloud Research Event Gateway", docs_url=None, redoc_url=None)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"service": "cloud-research-events", "entry": "signed-github-events"}


@app.post("/api/github/events")
async def github_event(request: Request) -> dict[str, object]:
    try:
        return dispatch_research_event(await request.body(), request.headers, lab_store)
    except GitHubEventError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
