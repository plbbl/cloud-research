"""One durable, model-directed research shift for Cloud Run Jobs."""

from __future__ import annotations

import asyncio
import os
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import app
from .run_events import ResearchEventEmitter, agent_presence


def research_job_prompt(brief: str) -> str:
    return f"""Take over this research program while the human is away:

{brief}

Use any experts, in any order, until no honest progress remains. Before ending, ask Explainer to
make the result genuinely understandable and Writer to publish one complete research packet."""


async def run() -> str:
    brief = os.environ["RESEARCH_BRIEF"].strip()
    run_id = os.getenv("RESEARCH_RUN_ID", str(uuid.uuid4()))
    events = ResearchEventEmitter(run_id)
    events.presence("director")
    session_id = str(uuid.uuid4())
    user_id = "human-pi"
    sessions = InMemorySessionService()
    await sessions.create_session(
        app_name=app.name,
        user_id=user_id,
        session_id=session_id,
    )
    runner = Runner(app=app, session_service=sessions)
    final_text = ""
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=research_job_prompt(brief))],
            ),
        ):
            parts = event.content.parts if event.content else []
            text = "\n".join(part.text for part in parts if part.text)
            for part in parts:
                function_call = getattr(part, "function_call", None)
                if function_call and function_call.name:
                    events.presence(function_call.name)
            if text and not event.is_final_response():
                author, state, default_detail = agent_presence(event.author)
                events.emit(author, state, default_detail)
            if event.is_final_response() and text:
                final_text = text
    except Exception as exc:
        events.emit("director", "error", "The research shift hit an error", output=str(exc))
        raise
    events.emit(
        "director",
        "complete",
        "The research handoff is ready",
        output=final_text,
    )
    return final_text


if __name__ == "__main__":
    asyncio.run(run())
