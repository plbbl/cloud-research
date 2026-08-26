"""Check whether evaluation source URLs resolve; never judge scientific support."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


def check(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "CloudResearchEvidenceAudit/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
            return {
                "url": url,
                "ok": 200 <= response.status < 400,
                "status": response.status,
                "resolved_url": response.url,
            }
    except urllib.error.HTTPError as exc:
        return {"url": url, "ok": False, "status": exc.code, "error": str(exc)}
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"url": url, "ok": False, "status": None, "error": str(exc)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("evals/latest-results.json"))
    parser.add_argument("--output", type=Path, default=Path("evals/source-audit.json"))
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    evidence = json.loads(args.results.read_text(encoding="utf-8"))
    urls = sorted(
        {
            url
            for result in evidence["results"]
            for url in result.get("source_urls", [])
        }
    )
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 8))) as pool:
        checks = list(pool.map(check, urls))
    by_url = {item["url"]: item for item in checks}
    cases = [
        {
            "id": result["id"],
            "urls": len(result.get("source_urls", [])),
            "reachable": sum(
                by_url[url]["ok"] for url in result.get("source_urls", [])
            ),
            "transport_pass": all(
                by_url[url]["ok"] for url in result.get("source_urls", [])
            ),
        }
        for result in evidence["results"]
    ]

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": (
            "Transport audit only: a successful response does not prove that a source supports "
            "a research claim."
        ),
        "summary": {
            "unique_urls": len(checks),
            "reachable": sum(item["ok"] for item in checks),
            "unreachable": sum(not item["ok"] for item in checks),
            "cases_with_all_urls_reachable": sum(
                case["transport_pass"] for case in cases
            ),
        },
        "cases": cases,
        "checks": checks,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"]))


if __name__ == "__main__":
    main()
