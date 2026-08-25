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
