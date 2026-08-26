"""Structured Cloud Run Job events for the live lab presence UI."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from typing import Any

import google.auth
from google.auth.transport.requests import AuthorizedSession
from requests import HTTPError

from .labs import LabSpec
from .research_ledger import ledger

AGENT_STATES = {
    "cloud_research": ("director", "directing", "Director is assembling the expert panel"),
    "director": ("director", "directing", "Director is assembling the expert panel"),
    "finder": ("finder", "searching", "Finder is mapping prior work"),
    "theorist": ("theorist", "theorizing", "Theorist is sharpening the mechanism"),
    "experimentalist": (
        "experimentalist",
        "testing",
        "Experimentalist is running a decisive probe",
    ),
    "critic": ("critic", "critiquing", "Critic is attacking the strongest claim"),
    "writer": ("writer", "writing", "Writer is assembling the research handoff"),
    "explainer": ("explainer", "explaining", "Explainer is rebuilding the logic for you"),
}


def agent_presence(name: str, lab: LabSpec | None = None) -> tuple[str, str, str]:
    """Return the presentation identity for one real ADK author or tool name."""
    normalized = name.strip().lower().replace("-", "_")
    if normalized in AGENT_STATES:
        return AGENT_STATES[normalized]
    if lab:
        spec = next((agent for agent in lab.agents if agent.id == normalized), None)
        if spec:
            copy = f"{spec.id} {spec.name} {spec.role}".lower()
            state, action = _presence_from_role(copy)
            return spec.id, state, f"{spec.name} is {action}"
    return "director", "directing", "Director is coordinating the next move"


def _presence_from_role(copy: str) -> tuple[str, str]:
    if any(word in copy for word in ("search", "paper", "prior", "find", "scout")):
        return "searching", "mapping live evidence"
    if any(word in copy for word in ("experiment", "test", "code", "run", "probe")):
        return "testing", "running a decisive probe"
    if any(word in copy for word in ("critic", "challenge", "attack", "fals", "skeptic")):
        return "critiquing", "attacking the strongest claim"
    if any(word in copy for word in ("write", "report", "publish", "handoff")):
        return "writing", "assembling the research handoff"
    if any(word in copy for word in ("explain", "teach", "clar")):
        return "explaining", "making the mechanism clear"
    return "theorizing", "sharpening the mechanism"


@dataclass
class ResearchEventEmitter:
    """Print JSON events that Cloud Run captures as structured log entries."""

    run_id: str
    lab: LabSpec | None = None
    sequence: int = field(default=0, init=False)

    def emit(
        self,
        agent: str,
        state: str,
        detail: str,
        *,
        output: str = "",
    ) -> dict[str, Any]:
        self.sequence += 1
        payload: dict[str, Any] = {
            "cloud_research_event": True,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "agent": agent,
            "state": state,
            "detail": detail,
        }
        if output:
            payload["output"] = output
        print(json.dumps(payload, ensure_ascii=False), flush=True)
        try:
            ledger.append_event(self.run_id, payload)
        except Exception as exc:  # Cloud Logging remains the durable fallback.
            print(
                json.dumps(
                    {
                        "cloud_research_ledger_warning": True,
                        "run_id": self.run_id,
                        "detail": str(exc),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
        return payload

    def presence(self, name: str, detail: str = "") -> dict[str, Any]:
        agent, state, default_detail = agent_presence(name, self.lab)
        return self.emit(agent, state, detail or default_detail)


def validate_run_id(run_id: str) -> str:
    """Canonicalize a UUID before including it in a Logging filter."""
    return str(uuid.UUID(run_id))


def list_research_events(run_id: str) -> list[dict[str, Any]]:
    """Read one job's structured events from Cloud Logging."""
    canonical_run_id = validate_run_id(run_id)
    if ledger.enabled:
        try:
            events = ledger.list_events(canonical_run_id)
            if events:
                return events
        except Exception:
            pass
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
    job = os.getenv("CLOUD_RESEARCH_JOB", "").strip()
    if not project or not job:
        raise RuntimeError("Background research is not configured on this service.")

    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform.read-only"]
    )
    client = AuthorizedSession(credentials)
    response = client.post(
        "https://logging.googleapis.com/v2/entries:list",
        json={
            "resourceNames": [f"projects/{project}"],
            "filter": " AND ".join(
                [
                    'resource.type="cloud_run_job"',
                    f'resource.labels.job_name="{job}"',
                    "jsonPayload.cloud_research_event=true",
                    f'jsonPayload.run_id="{canonical_run_id}"',
                ]
            ),
            "orderBy": "timestamp asc",
            "pageSize": 100,
        },
        timeout=15,
    )
    try:
        response.raise_for_status()
    except HTTPError as exc:
        raise RuntimeError("Research activity is not readable yet.") from exc

    events = []
    for entry in response.json().get("entries", []):
        payload = entry.get("jsonPayload", {})
        if payload.get("run_id") != canonical_run_id:
            continue
        events.append(
            {
                "sequence": int(payload.get("sequence", 0)),
                "agent": str(payload.get("agent", "director")),
                "state": str(payload.get("state", "directing")),
                "detail": str(payload.get("detail", "Research is moving")),
                "output": str(payload.get("output", "")),
                "timestamp": str(entry.get("timestamp", "")),
            }
        )
    return sorted(events, key=lambda event: event["sequence"])
