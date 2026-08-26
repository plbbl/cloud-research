from fastapi.testclient import TestClient

from app.webhook_app import app

client = TestClient(app)


def test_public_event_gateway_exposes_no_research_or_lab_surface() -> None:
    assert client.get("/healthz").json() == {
        "service": "cloud-research-events",
        "entry": "signed-github-events",
    }
    assert client.get("/api/labs").status_code == 404
    assert client.post("/api/dispatch", json={}).status_code == 404
