from fastapi.testclient import TestClient

from app.fast_api_app import app

client = TestClient(app)


def test_health_names_all_three_google_pieces() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "cloud-research",
        "model": "gemini-3.7-flash",
        "agent_framework": "Google ADK",
        "infrastructure": "Google Cloud Run",
    }


def test_adk_discovers_the_app() -> None:
    assert client.get("/list-apps").json() == ["app"]


def test_demo_surface_is_served() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "What should the lab pursue?" in response.text
    assert "Your research team" in response.text
    assert "/static/cloud-research-icon.png" in response.text


def test_background_dispatch_is_off_until_cloud_job_is_configured(monkeypatch) -> None:
    monkeypatch.delenv("CLOUD_RESEARCH_JOB", raising=False)

    response = client.post("/api/dispatch", json={"brief": "Find the crack."})

    assert response.status_code == 503


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
