"""Small, authenticated GitHub event adapter for the Taskmaster entry point."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from .cloud_run import background_research_available, launch_research_job
from .labs import LabSpec
from .research_ledger import claim_github_delivery


@dataclass(frozen=True)
class GitHubResearchBrief:
    brief: str
    lab_id: str
    source: str


class LabRepository(Protocol):
    def list(self) -> list[LabSpec]: ...

    def get(self, lab_id: str) -> LabSpec | None: ...


class GitHubEventError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def valid_signature(body: bytes, signature: str, secret: str) -> bool:
    if not signature.startswith("sha256=") or not secret:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature.removeprefix("sha256="), expected)


def research_brief(
    event_name: str,
    payload: dict[str, Any],
    *,
    trigger_label: str = "cloud-research",
) -> GitHubResearchBrief | None:
    if event_name == "issues":
        if payload.get("action") != "labeled":
            return None
        label = str((payload.get("label") or {}).get("name", ""))
        if label.casefold() != trigger_label.casefold():
            return None
        issue = payload.get("issue") or {}
        labels = [str(item.get("name", "")) for item in issue.get("labels", [])]
        lab_id = next(
            (name.split(":", 1)[1] for name in labels if name.casefold().startswith("lab:")),
            "",
        )
        title = str(issue.get("title", "Untitled research brief"))
        body = str(issue.get("body", "")).strip()
        url = str(issue.get("html_url", ""))
        return GitHubResearchBrief(
            brief=f"Research program from GitHub\n\nTitle: {title}\n\n{body}\n\nSource: {url}",
            lab_id=lab_id,
            source=f"github:issue:{issue.get('number', '')}",
        )

    if event_name == "repository_dispatch" and payload.get("action") == "cloud-research":
        client_payload = payload.get("client_payload") or {}
        brief = str(client_payload.get("brief", "")).strip()
        if not brief:
            return None
        return GitHubResearchBrief(
            brief=brief,
            lab_id=str(client_payload.get("lab_id", "")),
            source="github:repository_dispatch",
        )
    return None


def dispatch_research_event(
    body: bytes,
    headers: Mapping[str, str],
    lab_store: LabRepository,
) -> dict[str, object]:
    if not background_research_available():
        raise GitHubEventError(503, "Background research is not configured.")
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "").strip()
    if not valid_signature(body, headers.get("x-hub-signature-256", ""), secret):
        raise GitHubEventError(401, "The GitHub signature is invalid.")

    event_name = headers.get("x-github-event", "")
    if event_name == "ping":
        return {"accepted": True, "message": "Cloud Research is listening."}
    delivery_id = headers.get("x-github-delivery", "").strip()
    if not delivery_id:
        raise GitHubEventError(400, "The GitHub delivery id is missing.")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise GitHubEventError(400, "The GitHub payload is invalid.") from exc
    trigger = research_brief(event_name, payload)
    if trigger is None:
        return {"accepted": False, "message": "This event does not request research."}

    lab = lab_store.get(trigger.lab_id) if trigger.lab_id else lab_store.list()[0]
    if lab is None:
        raise GitHubEventError(404, "The requested lab does not exist.")
    if not claim_github_delivery(delivery_id):
        return {"accepted": True, "duplicate": True, "delivery_id": delivery_id}
    result = launch_research_job(trigger.brief, lab, source=trigger.source)
    return {"accepted": True, "delivery_id": delivery_id, **result}
