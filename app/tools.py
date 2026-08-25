"""A few sharp tools for the agent lab. No workflow policy lives here."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .research_logic import compare_claim_text, safe_artifact_name


def compare_research_claims(left_claim: str, right_claim: str) -> dict[str, object]:
    """Compare two research claims for cheap lexical overlap.

    Args:
        left_claim: The first complete claim.
        right_claim: The second complete claim.

    Returns:
        Overlap evidence that must be followed by mechanism-level reading.
    """
    return compare_claim_text(left_claim, right_claim)


def write_research_artifact(title: str, markdown: str) -> dict[str, str]:
    """Write one research note that a human or another agent can continue.

    Args:
        title: Human-readable note title.
        markdown: Complete Markdown research note with evidence and next move.

    Returns:
        The saved artifact path.
    """
    root = Path(os.getenv("CLOUD_RESEARCH_LAB_DIR", "/tmp/cloud-research/lab"))
    root.mkdir(parents=True, exist_ok=True)
    path = root / safe_artifact_name(title)
    path.write_text(markdown.rstrip() + "\n", encoding="utf-8")
    return {"title": title, "path": str(path), "message": "Research artifact preserved."}


def publish_research_packet(
    title: str,
    markdown: str,
    repository_path: str = "research/cloud-research-handoff.md",
) -> dict[str, str]:
    """Publish a research packet to a new GitHub branch when GitHub is configured.

    The tool uses GITHUB_TOKEN and GITHUB_REPOSITORY from the service environment.
    With no token it safely leaves the packet as a local artifact for later pickup.

    Args:
        title: Short research title used for the branch and commit.
        markdown: Complete research packet.
        repository_path: Markdown path inside the configured repository.

    Returns:
        The branch and URL, or the local artifact path when GitHub is not configured.
    """
    token = os.getenv("GITHUB_TOKEN", "").strip()
    repository = os.getenv("GITHUB_REPOSITORY", "").strip()
    if not token or not repository:
        local = write_research_artifact(title, markdown)
        return {
            **local,
            "message": "GitHub is not configured; the complete packet remains available locally.",
        }

    target = PurePosixPath(repository_path)
    if target.is_absolute() or ".." in target.parts or target.suffix.lower() != ".md":
        raise ValueError("repository_path must be a relative Markdown path")

    repo = _github_json(f"/repos/{repository}", token)
    default_branch = repo["default_branch"]
    base_ref = _github_json(f"/repos/{repository}/git/ref/heads/{quote(default_branch)}", token)
    branch = "cloud-research/" + safe_artifact_name(title).removesuffix(".md")

    try:
        _github_json(
            f"/repos/{repository}/git/refs",
            token,
            method="POST",
            payload={"ref": f"refs/heads/{branch}", "sha": base_ref["object"]["sha"]},
        )
    except HTTPError as exc:
        if exc.code != 422:
            raise

    encoded_path = "/".join(quote(part) for part in target.parts)
    content_url = f"/repos/{repository}/contents/{encoded_path}?ref={quote(branch, safe='')}"
    sha = None
    try:
        sha = _github_json(content_url, token)["sha"]
    except HTTPError as exc:
        if exc.code != 404:
            raise

    payload = {
        "message": f"research: {title}",
        "content": base64.b64encode(markdown.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    result = _github_json(
        f"/repos/{repository}/contents/{encoded_path}", token, method="PUT", payload=payload
    )
    return {
        "title": title,
        "branch": branch,
        "url": result["content"]["html_url"],
        "message": "Research packet published for the human and local experiment agents.",
    }


def _github_json(
    endpoint: str,
    token: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        "https://api.github.com" + endpoint,
        data=body,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "cloud-research-hackathon",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(request, timeout=30) as response:  # noqa: S310 - fixed GitHub host
        return json.load(response)
