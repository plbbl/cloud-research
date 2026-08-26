"""Launch repeatable Cloud Research cases and record only observable evidence."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

URL = re.compile(r"https?://[^\s<>]+")


def request_json(url: str, payload: dict[str, str] | None = None) -> dict[str, Any]:
    body = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        method="POST" if body else "GET",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"{exc.code} from {url}: {detail}") from exc


def evaluate_case(base_url: str, case: dict[str, str], timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    launch = request_json(
        f"{base_url}/api/dispatch",
        {"brief": case["brief"], "lab_id": case["lab_id"]},
    )
    run_id = launch["run_id"]
    result: dict[str, Any] = {"events": [], "done": False}
    while time.monotonic() - started < timeout:
        try:
            result = request_json(f"{base_url}/api/runs/{run_id}")
        except RuntimeError as exc:
            if str(exc).startswith("503 from"):
                time.sleep(10)
                continue
            raise
        if result.get("done"):
            break
        time.sleep(10)

    return summarize(case, run_id, result, time.monotonic() - started)


def summarize(
    case: dict[str, str],
    run_id: str,
    result: dict[str, Any],
    duration_seconds: float,
) -> dict[str, Any]:
    handoff = next(
        (
            event.get("output", "")
            for event in reversed(result.get("events", []))
            if event.get("output")
        ),
        "",
    )
    copy = handoff.casefold()
    urls = sorted(set(URL.findall(handoff)))
    section_checks = {
        "killed_paths": "killed" in copy,
        "unknowns": "unknown" in copy,
        "next_task": "next" in copy and ("experiment" in copy or "task" in copy),
        "artifact": "artifact" in copy,
    }
    return {
        "id": case["id"],
        "run_id": run_id,
        "completed": bool(result.get("done")),
        "duration_seconds": round(duration_seconds, 1),
        "event_count": len(result.get("events", [])),
        "handoff_characters": len(handoff),
        "source_url_count": len(urls),
        "section_checks": section_checks,
        "observable_pass": (
            bool(result.get("done")) and len(urls) >= 2 and all(section_checks.values())
        ),
        "source_urls": urls,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8092")
    parser.add_argument("--cases", type=Path, default=Path("evals/research_cases.json"))
    parser.add_argument("--output", type=Path, default=Path("evals/latest-results.json"))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--resume-manifest", type=Path)
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if args.limit:
        cases = cases[: args.limit]
    base_url = args.base_url.rstrip("/")
    if args.resume_manifest:
        manifest = {
            item["id"]: item
            for item in json.loads(args.resume_manifest.read_text(encoding="utf-8"))
        }
        results = [
            summarize(
                case,
                manifest[case["id"]]["run_id"],
                request_json(f"{base_url}/api/runs/{manifest[case['id']]['run_id']}"),
                float(manifest[case["id"]]["duration_seconds"]),
            )
            for case in cases
            if case["id"] in manifest
        ]
    else:
        with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 3))) as pool:
            results = list(
                pool.map(lambda case: evaluate_case(base_url, case, args.timeout), cases)
            )
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_url": base_url,
        "summary": {
            "cases": len(results),
            "completed": sum(item["completed"] for item in results),
            "observable_passes": sum(item["observable_pass"] for item in results),
        },
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"]))


if __name__ == "__main__":
    main()
