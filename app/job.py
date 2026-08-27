"""One durable, model-directed research shift for Cloud Run Jobs."""

from __future__ import annotations

import asyncio
import os
import uuid

from google.adk.agents.run_config import RunConfig
from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import app as default_app
from .lab_agents import build_lab_agent
from .labs import DEFAULT_LAB, LabSpec
from .research_ledger import ledger
from .run_events import ResearchEventEmitter, agent_presence

DEFAULT_RESEARCH_BRIEF = """Run a bounded Cloud Research smoke shift.
Use only the Explainer and Writer experts. Explain why a four-line counterexample can invalidate
a universal claim, preserve the explanation as a short handoff, and stop. Do not search the web,
publish to GitHub, or run a real benchmark."""


def research_job_brief() -> str:
    """Return the submitted brief or a safe, bounded console-execution brief."""
    return os.getenv("RESEARCH_BRIEF", DEFAULT_RESEARCH_BRIEF).strip() or DEFAULT_RESEARCH_BRIEF


def research_job_prompt(brief: str) -> str:
    return f"""Continue this research program while the human is away:

{brief}

Treat the brief as the execution contract. If it says smoke, bounded, or stop, use only the named
experts once each and return immediately; do not search, publish, benchmark, or recruit extra
experts when the brief forbids it. Otherwise make only the smallest number of useful moves. Carry
evidence between calls, then end with one understandable, evidence-backed Handoff. Publish an
Artifact only when the brief explicitly allows publishing."""


def research_job_app(raw_lab: str | None = None) -> App:
    """Rebuild the selected prompt-directed lab in this isolated execution."""
    raw_lab = raw_lab if raw_lab is not None else os.getenv("RESEARCH_LAB_SPEC", "")
    if not raw_lab.strip():
        return default_app
    lab = LabSpec.model_validate_json(raw_lab)
    return App(name=lab.id, root_agent=build_lab_agent(lab))


async def run() -> str:
    brief = research_job_brief()
    run_id = os.getenv("RESEARCH_RUN_ID", str(uuid.uuid4()))
    raw_lab = os.getenv("RESEARCH_LAB_SPEC", "")
    lab = LabSpec.model_validate_json(raw_lab) if raw_lab.strip() else DEFAULT_LAB
    ledger.begin_run(
        run_id,
        brief=brief,
        lab=lab.model_dump(mode="json"),
        source=os.getenv("RESEARCH_SOURCE", "cloud-run-job"),
    )
    events = ResearchEventEmitter(run_id, lab=lab)
    events.presence("director")
    session_id = str(uuid.uuid4())
    user_id = "human-pi"
    app = research_job_app(raw_lab)
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
            run_config=RunConfig(
                max_llm_calls=int(os.getenv("CLOUD_RESEARCH_MAX_LLM_CALLS", "12")),
            ),
        ):
            parts = event.content.parts if event.content else []
            text = "\n".join(part.text for part in parts if part.text)
            for part in parts:
                function_call = getattr(part, "function_call", None)
                if function_call and function_call.name:
                    events.presence(function_call.name)
            if text and not event.is_final_response():
                author, state, default_detail = agent_presence(event.author, lab)
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
