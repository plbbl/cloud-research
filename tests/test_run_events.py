import json

import pytest

from app.run_events import ResearchEventEmitter, agent_presence, list_research_events


def test_agent_presence_maps_real_adk_names() -> None:
    assert agent_presence("experimentalist") == (
        "experimentalist",
        "testing",
        "Experimentalist is running a decisive probe",
    )
    assert agent_presence("cloud_research")[0] == "director"


def test_emitter_prints_structured_json(capsys) -> None:
    emitter = ResearchEventEmitter("ee0ca1f9-3fb6-4cd8-ab31-8ca8ca3f3a04")

    emitter.presence("finder")

    payload = json.loads(capsys.readouterr().out)
    assert payload["cloud_research_event"] is True
    assert payload["sequence"] == 1
    assert payload["state"] == "searching"


def test_list_events_uses_a_safe_filter(monkeypatch) -> None:
    run_id = "ee0ca1f9-3fb6-4cd8-ab31-8ca8ca3f3a04"
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "research-project")
    monkeypatch.setenv("CLOUD_RESEARCH_JOB", "research-shift")
    calls = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "entries": [
                    {
                        "timestamp": "2026-08-25T12:00:00Z",
                        "jsonPayload": {
                            "run_id": run_id,
                            "sequence": 2,
                            "agent": "writer",
                            "state": "writing",
                            "detail": "Writer is assembling the research handoff",
                        },
                    },
                    {
                        "timestamp": "2026-08-25T11:59:59Z",
                        "jsonPayload": {
                            "run_id": run_id,
                            "sequence": 1,
                            "agent": "finder",
                            "state": "searching",
                            "detail": "Finder is mapping prior work",
                        },
                    },
                ]
            }

    class Session:
        def __init__(self, credentials) -> None:
            calls["credentials"] = credentials

        def post(self, url, *, json, timeout):
            calls.update(url=url, body=json, timeout=timeout)
            return Response()

    monkeypatch.setattr("app.run_events.google.auth.default", lambda scopes: (object(), None))
    monkeypatch.setattr("app.run_events.AuthorizedSession", Session)

    events = list_research_events(run_id)

    assert [event["sequence"] for event in events] == [1, 2]
    assert f'jsonPayload.run_id="{run_id}"' in calls["body"]["filter"]
    assert calls["url"].endswith("/entries:list")


def test_list_events_rejects_filter_injection() -> None:
    with pytest.raises(ValueError):
        list_research_events('not-a-uuid" OR true')
