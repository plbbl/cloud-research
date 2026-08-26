"""Production HTTP surface for Cloud Run and the hackathon demo."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import HTTPException, Request, WebSocket
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from google.adk.cli.fast_api import get_fast_api_app
from pydantic import BaseModel, Field

from .cloud_run import background_research_available, launch_research_job
from .firestore_labs import build_lab_store
from .github_events import GitHubEventError, dispatch_research_event
from .lab_runtime import LabRunnerRegistry, stream_lab_events
from .labs import LabDraft, LabSpec
from .live_voice import LIVE_MODEL_NAME, bridge_live_voice
from .research_ledger import ledger
from .run_events import list_research_events

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_ROOT / "app" / "static"
LABS_FILE = Path(
    os.getenv("CLOUD_RESEARCH_LABS_FILE", PROJECT_ROOT / ".cloud-research" / "labs.json")
)
lab_store = build_lab_store(LABS_FILE, ledger)
lab_runners = LabRunnerRegistry()


class LabRunRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=100_000)
    session_id: str = Field(min_length=1, max_length=96)
    user_id: str = Field(default="human-pi", min_length=1, max_length=96)


class DispatchRequest(BaseModel):
    brief: str = Field(min_length=1, max_length=100_000)
    lab_id: str = Field(min_length=1, max_length=48)

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
    vertex_enabled = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in {"1", "true"}
    return {
        "service": "cloud-research",
        "model": os.getenv("CLOUD_RESEARCH_MODEL", "gemini-3.7-flash"),
        "model_backend": "Vertex AI" if vertex_enabled else "Gemini Developer API",
        "agent_framework": "Google ADK",
        "infrastructure": "Google Cloud Run",
    }


@app.get("/api/about")
async def about() -> dict[str, object]:
    return {
        "thesis": "Every researcher becomes the PI of a persistent team of AI experts.",
        "stack": [
            "Gemini 3.7 Flash",
            LIVE_MODEL_NAME,
            "Google ADK",
            "Google Cloud Run",
        ],
        "experts": ["Finder", "Theorist", "Experimentalist", "Critic", "Writer", "Explainer"],
        "philosophy": ["Concise", "Excited by truth", "Certain a valuable opening exists"],
        "background_research": background_research_available(),
        "networking": "Google Search grounding",
        "model": os.getenv("CLOUD_RESEARCH_MODEL", "gemini-3.7-flash"),
        "live_model": LIVE_MODEL_NAME,
        "voice": f"Native audio with {LIVE_MODEL_NAME}",
        "research_ledger": "Firestore" if ledger.enabled else "Local development storage",
    }


@app.get("/api/labs")
async def list_labs() -> list[LabSpec]:
    return lab_store.list()


@app.post("/api/labs", status_code=201)
async def create_lab(draft: LabDraft) -> LabSpec:
    return lab_store.create(draft)


@app.put("/api/labs/{lab_id}")
async def update_lab(lab_id: str, draft: LabDraft) -> LabSpec:
    lab = lab_store.update(lab_id, draft)
    if lab is None:
        raise HTTPException(status_code=404, detail="That lab does not exist.")
    lab_runners.discard(lab_id)
    return lab


@app.delete("/api/labs/{lab_id}", status_code=204)
async def delete_lab(lab_id: str) -> None:
    if not lab_store.delete(lab_id):
        raise HTTPException(status_code=409, detail="Keep at least one lab.")
    lab_runners.discard(lab_id)


@app.post("/api/labs/{lab_id}/run_sse")
async def run_lab(lab_id: str, request: LabRunRequest) -> StreamingResponse:
    lab = lab_store.get(lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail="That lab does not exist.")
    runner = lab_runners.runner_for(lab)
    return StreamingResponse(
        stream_lab_events(
            runner,
            lab_id=lab.id,
            user_id=request.user_id,
            session_id=request.session_id,
            prompt=request.prompt,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.websocket("/api/labs/{lab_id}/live")
async def live_lab_voice(websocket: WebSocket, lab_id: str) -> None:
    lab = lab_store.get(lab_id)
    if lab is None:
        await websocket.close(code=4404, reason="That lab does not exist.")
        return
    await bridge_live_voice(websocket, lab)


@app.post("/api/dispatch")
async def dispatch(request: DispatchRequest) -> dict[str, str]:
    if not background_research_available():
        raise HTTPException(status_code=503, detail="Background research is not configured.")
    lab = lab_store.get(request.lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail="That lab does not exist.")
    return launch_research_job(request.brief.strip(), lab, source="web")


@app.post("/api/github/events")
async def github_event(request: Request) -> dict[str, object]:
    body = await request.body()
    try:
        return dispatch_research_event(body, request.headers, lab_store)
    except GitHubEventError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.get("/api/runs/{run_id}")
async def research_run(run_id: str) -> dict[str, object]:
    try:
        events = list_research_events(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="The research run id is invalid.") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    done = bool(events and events[-1]["state"] in {"complete", "error"})
    return {"run_id": run_id, "events": events, "done": done}
