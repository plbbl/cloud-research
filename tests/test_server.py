import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.fast_api_app import app
from app.labs import LabStore

client = TestClient(app)


def test_health_names_all_three_google_pieces() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "cloud-research",
        "model": "gemini-3.7-flash",
        "model_backend": "Gemini Developer API",
        "agent_framework": "Google ADK",
        "infrastructure": "Google Cloud Run",
    }


def test_adk_discovers_the_app() -> None:
    assert client.get("/list-apps").json() == ["app"]


def test_demo_surface_is_served() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "What should the lab pursue?" in response.text
    assert "Research team" in response.text
    assert 'id="new-lab"' in response.text
    assert 'id="lab-editor"' in response.text
    assert 'id="voice-toggle"' in response.text
    assert "Cloud Research Lab" in response.text
    assert "/static/cloud-research-icon.png" in response.text


def test_demo_restores_cloud_run_research_after_the_user_leaves() -> None:
    source = (client.get("/static/app.js")).text

    assert 'const ACTIVE_RUN_KEY = "cloud-research-active-run"' in source
    assert 'fetch("/api/dispatch"' in source
    assert "followBackgroundRun" in source
    assert "/api/runs/${encodeURIComponent(runId)}" in source
    assert "restoreBackgroundRun" in source


def test_background_dispatch_is_off_until_cloud_job_is_configured(monkeypatch) -> None:
    monkeypatch.delenv("CLOUD_RESEARCH_JOB", raising=False)

    response = client.post(
        "/api/dispatch",
        json={"brief": "Find the crack.", "lab_id": "cloud_research"},
    )

    assert response.status_code == 503


def test_background_dispatch_carries_the_selected_lab(monkeypatch) -> None:
    monkeypatch.setenv("CLOUD_RESEARCH_JOB", "research-shift")
    calls = {}

    def fake_launch(brief, lab, *, source):
        calls.update(brief=brief, lab=lab, source=source)
        return {"run_id": "run-1", "lab_id": lab.id, "operation": "op", "message": "ok"}

    monkeypatch.setattr("app.fast_api_app.launch_research_job", fake_launch)
    response = client.post(
        "/api/dispatch",
        json={"brief": "Find the crack.", "lab_id": "cloud_research"},
    )

    assert response.status_code == 200
    assert calls["brief"] == "Find the crack."
    assert calls["lab"].id == "cloud_research"
    assert calls["source"] == "web"


def test_background_dispatch_rejects_an_unknown_lab(monkeypatch) -> None:
    monkeypatch.setenv("CLOUD_RESEARCH_JOB", "research-shift")

    response = client.post(
        "/api/dispatch",
        json={"brief": "Find the crack.", "lab_id": "missing_lab"},
    )

    assert response.status_code == 404


def test_run_status_returns_structured_agent_events(monkeypatch) -> None:
    run_id = "ee0ca1f9-3fb6-4cd8-ab31-8ca8ca3f3a04"
    monkeypatch.setattr(
        "app.fast_api_app.list_research_events",
        lambda value: [
            {
                "sequence": 1,
                "agent": "explainer",
                "state": "complete",
                "detail": "The research handoff is ready",
                "output": "A clear explanation.",
                "timestamp": "2026-08-25T12:00:00Z",
            }
        ],
    )

    response = client.get(f"/api/runs/{run_id}")

    assert response.status_code == 200
    assert response.json()["done"] is True
    assert response.json()["events"][0]["output"] == "A clear explanation."


def test_run_status_rejects_an_invalid_id() -> None:
    response = client.get('/api/runs/not-a-uuid"-or-true')

    assert response.status_code == 400


def test_lab_crud_surface(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.fast_api_app.lab_store", LabStore(tmp_path / "labs.json"))
    body = {
        "name": "Mechanistic Vision Lab",
        "mission": "Find one decisive mechanistic vision task.",
        "agents": [
            {
                "id": "scout",
                "name": "Scout",
                "role": "Search current papers and code.",
                "color": "#ff5eb1",
            }
        ],
    }

    created = client.post("/api/labs", json=body)
    assert created.status_code == 201
    lab = created.json()
    assert lab["agents"][0]["name"] == "Scout"

    body["name"] = "Updated Vision Lab"
    updated = client.put(f"/api/labs/{lab['id']}", json=body)
    assert updated.status_code == 200
    assert updated.json()["version"] == 2

    listed = client.get("/api/labs")
    assert any(item["name"] == "Updated Vision Lab" for item in listed.json())


def test_live_voice_websocket_routes_to_the_selected_lab(monkeypatch) -> None:
    async def fake_bridge(websocket, lab) -> None:
        await websocket.accept()
        await websocket.send_json({"type": "ready", "lab": lab.name})
        await websocket.close()

    monkeypatch.setattr("app.fast_api_app.bridge_live_voice", fake_bridge)

    with client.websocket_connect("/api/labs/cloud_research/live") as websocket:
        assert websocket.receive_json() == {
            "type": "ready",
            "lab": "Cloud Research Lab",
        }


def test_github_issue_launches_the_selected_lab(monkeypatch) -> None:
    secret = "webhook-test-secret"
    monkeypatch.setenv("CLOUD_RESEARCH_JOB", "research-shift")
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", secret)
    calls = {}

    def fake_launch(brief, lab, *, source):
        calls.update(brief=brief, lab=lab, source=source)
        return {"run_id": "run-1", "lab_id": lab.id, "operation": "op", "message": "ok"}

    monkeypatch.setattr("app.fast_api_app.launch_research_job", fake_launch)
    payload = {
        "action": "labeled",
        "label": {"name": "cloud-research"},
        "issue": {
            "number": 7,
            "title": "Find a tractable crack",
            "body": "Use one 24 GB GPU.",
            "html_url": "https://github.com/plbbl/cloud-research/issues/7",
            "labels": [{"name": "cloud-research"}, {"name": "lab:cloud_research"}],
        },
    }
    body = json.dumps(payload).encode()
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    response = client.post(
        "/api/github/events",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "delivery-test-server-1",
            "X-Hub-Signature-256": signature,
        },
    )

    assert response.status_code == 200
    assert response.json()["accepted"] is True
    assert calls["lab"].id == "cloud_research"
    assert calls["source"] == "github:issue:7"
    assert "Use one 24 GB GPU." in calls["brief"]


def test_github_event_rejects_a_bad_signature(monkeypatch) -> None:
    monkeypatch.setenv("CLOUD_RESEARCH_JOB", "research-shift")
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "right-secret")

    response = client.post(
        "/api/github/events",
        content=b"{}",
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": "sha256=wrong",
        },
    )

    assert response.status_code == 401
