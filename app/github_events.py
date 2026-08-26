"""Small, authenticated GitHub event adapter for the Taskmaster entry point."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GitHubResearchBrief:
    brief: str
    lab_id: str
    source: str


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
