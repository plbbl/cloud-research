"""Launch one prompt-directed ADK run as a durable Cloud Run Job execution."""

from __future__ import annotations

import os
import uuid

import google.auth
from google.auth.transport.requests import AuthorizedSession

from .labs import LabSpec
from .research_ledger import ledger


def background_research_available() -> bool:
    return bool(os.getenv("CLOUD_RESEARCH_JOB", "").strip())


def launch_research_job(
    brief: str,
    lab: LabSpec,
    *,
    source: str = "web",
) -> dict[str, str]:
    """Launch the configured Cloud Run Job and return Google's operation name."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
    location = os.getenv("CLOUD_RESEARCH_JOB_LOCATION", "us-central1").strip()
    job = os.getenv("CLOUD_RESEARCH_JOB", "").strip()
    if not project or not job:
        raise RuntimeError("Background research is not configured on this service.")

    run_id = str(uuid.uuid4())
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    client = AuthorizedSession(credentials)
    response = client.post(
        f"https://run.googleapis.com/v2/projects/{project}/locations/{location}/jobs/{job}:run",
        json={
            "overrides": {
                "containerOverrides": [
                    {
                        "env": [
                            {"name": "RESEARCH_BRIEF", "value": brief},
                            {"name": "RESEARCH_RUN_ID", "value": run_id},
                            {
                                "name": "RESEARCH_LAB_SPEC",
                                "value": lab.model_dump_json(),
                            },
                            {"name": "RESEARCH_SOURCE", "value": source},
                        ]
                    }
                ]
            }
        },
        timeout=30,
    )
    response.raise_for_status()
    operation = response.json()
    ledger.begin_run(
        run_id,
        brief=brief,
        lab=lab.model_dump(mode="json"),
        source=source,
    )
    return {
        "operation": operation["name"],
        "run_id": run_id,
        "lab_id": lab.id,
        "message": (
            "The expert panel is working in Cloud Run. You can leave now. This page will keep "
            "showing who is moving the research forward."
        ),
    }
