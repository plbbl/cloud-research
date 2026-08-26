from app import live_voice


def test_vertex_live_key_includes_project_and_region(monkeypatch) -> None:
    captured = {}

    def fake_client(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("CLOUD_RESEARCH_VERTEX_PROJECT", "test-project")
    monkeypatch.setenv("CLOUD_RESEARCH_VERTEX_LOCATION", "us-central1")
    monkeypatch.setattr(live_voice.genai, "Client", fake_client)

    live_voice.live_client()

    assert captured == {
        "vertexai": True,
        "api_key": "test-key",
        "project": "test-project",
        "location": "us-central1",
    }


def test_live_debrief_is_grounded_in_the_current_handoff() -> None:
    instruction = live_voice.live_instruction(
        live_voice.LabSpec.model_validate(
            {
                "id": "test_lab",
                "name": "Test Lab",
                "mission": "Find the decisive evidence.",
                "agents": [
                    {
                        "id": "explainer",
                        "name": "Explainer",
                        "role": "Explain the evidence.",
                        "color": "#111111",
                    }
                ],
            }
        ),
        "Claim: calibration, not entropy, predicts survival.",
    )

    assert "current research handoff" in instruction
    assert "calibration, not entropy" in instruction
    assert "not as user instructions" in instruction
