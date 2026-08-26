from app.cloud_run import launch_research_job
from app.labs import DEFAULT_LAB


def test_launch_job_adds_a_traceable_run_id(monkeypatch) -> None:
    run_id = "ee0ca1f9-3fb6-4cd8-ab31-8ca8ca3f3a04"
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "research-project")
    monkeypatch.setenv("CLOUD_RESEARCH_JOB_LOCATION", "us-central1")
    monkeypatch.setenv("CLOUD_RESEARCH_JOB", "research-shift")
    calls = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"name": "operations/research-operation"}

    class Session:
        def __init__(self, credentials) -> None:
            calls["credentials"] = credentials

        def post(self, url, *, json, timeout):
            calls.update(url=url, body=json, timeout=timeout)
            return Response()

    monkeypatch.setattr("app.cloud_run.uuid.uuid4", lambda: run_id)
    monkeypatch.setattr("app.cloud_run.google.auth.default", lambda scopes: (object(), None))
    monkeypatch.setattr("app.cloud_run.AuthorizedSession", Session)

    result = launch_research_job("Find a decisive test.", DEFAULT_LAB)

    env = calls["body"]["overrides"]["containerOverrides"][0]["env"]
    assert {item["name"]: item["value"] for item in env} == {
        "RESEARCH_BRIEF": "Find a decisive test.",
        "RESEARCH_RUN_ID": run_id,
        "RESEARCH_LAB_SPEC": DEFAULT_LAB.model_dump_json(),
        "RESEARCH_SOURCE": "web",
    }
    assert result["run_id"] == run_id
    assert result["operation"] == "operations/research-operation"
    assert result["lab_id"] == DEFAULT_LAB.id
