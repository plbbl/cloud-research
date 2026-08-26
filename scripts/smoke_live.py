"""Exercise the authenticated Gemini Live bridge with text and record real output."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

import websockets


async def smoke(url: str, lab_id: str, handoff: str) -> dict[str, object]:
    binary_frames = 0
    binary_bytes = 0
    transcripts: list[str] = []
    event_types: list[str] = []

    async with asyncio.timeout(90):
        async with websockets.connect(f"{url}/api/labs/{lab_id}/live") as socket:
            await socket.send(json.dumps({"type": "start", "handoff": handoff}))
            ready = json.loads(await socket.recv())
            if ready.get("type") != "ready":
                raise RuntimeError(f"Live bridge did not become ready: {ready}")
            await socket.send(
                json.dumps(
                    {
                        "type": "text",
                        "text": (
                            "In one sentence, separate what this lab observed from what it only "
                            "proposed."
                        ),
                    }
                )
            )
            while True:
                message = await socket.recv()
                if isinstance(message, bytes):
                    binary_frames += 1
                    binary_bytes += len(message)
                    continue
                event = json.loads(message)
                event_types.append(str(event.get("type")))
                if event.get("type") in {"output_text", "output_transcript"}:
                    transcripts.append(str(event.get("text", "")))
                if event.get("type") == "error":
                    raise RuntimeError(str(event.get("message")))
                if event.get("type") == "turn_complete":
                    break

    return {
        "model": ready.get("model"),
        "binary_frames": binary_frames,
        "binary_bytes": binary_bytes,
        "event_types": sorted(set(event_types)),
        "transcript": "".join(transcripts).strip(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="ws://127.0.0.1:8092")
    parser.add_argument("--lab-id", default="lab_24gb_research_lab")
    parser.add_argument("--output", type=Path, default=Path("evals/live-smoke.json"))
    args = parser.parse_args()
    handoff = (
        "Observed here: a toy synthetic probe completed; no mechanism was confirmed. "
        "Proposed: the same mechanism will improve CLIP on a real benchmark."
    )
    result = asyncio.run(smoke(args.url, args.lab_id, handoff))
    result["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    result["scope"] = "Private Cloud Run proxy to Vertex Gemini Live; text input, audio output."
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
