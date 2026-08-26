"""In-memory ADK runners for editable labs."""

from __future__ import annotations

import json
import threading
from collections.abc import AsyncIterator

from google.adk.agents._streaming_mode import StreamingMode
from google.adk.agents.run_config import RunConfig
from google.adk.runners import InMemoryRunner
from google.genai import types

from .lab_agents import build_lab_agent
from .labs import LabSpec


class LabRunnerRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._runners: dict[str, tuple[int, InMemoryRunner]] = {}

    def runner_for(self, lab: LabSpec) -> InMemoryRunner:
        with self._lock:
            cached = self._runners.get(lab.id)
            if cached and cached[0] == lab.version:
                return cached[1]
            runner = InMemoryRunner(agent=build_lab_agent(lab), app_name=lab.id)
            self._runners[lab.id] = (lab.version, runner)
            return runner

    def discard(self, lab_id: str) -> None:
        with self._lock:
            self._runners.pop(lab_id, None)


async def stream_lab_events(
    runner: InMemoryRunner,
    *,
    lab_id: str,
    user_id: str,
    session_id: str,
    prompt: str,
) -> AsyncIterator[str]:
    session = await runner.session_service.get_session(
        app_name=lab_id,
        user_id=user_id,
        session_id=session_id,
    )
    if session is None:
        await runner.session_service.create_session(
            app_name=lab_id,
            user_id=user_id,
            session_id=session_id,
        )

    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    config = RunConfig(streaming_mode=StreamingMode.SSE, max_llm_calls=60)
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
            run_config=config,
        ):
            yield f"data: {event.model_dump_json(by_alias=True, exclude_none=True)}\n\n"
    except Exception as exc:
        payload = json.dumps({"error": str(exc)}, ensure_ascii=False)
        yield f"data: {payload}\n\n"
