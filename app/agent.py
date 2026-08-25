"""Google ADK multi-agent lab: prompts choose the path, not a state machine."""

from __future__ import annotations

import os

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import AgentTool, google_search
from google.genai import types

from .prompts import CRITIC, DIRECTOR, EXPERIMENTALIST, EXPLAINER, FINDER, THEORIST, WRITER
from .tools import compare_research_claims, publish_research_packet, write_research_artifact

MODEL_NAME = os.getenv("CLOUD_RESEARCH_MODEL", "gemini-3.7-flash")


def _model() -> Gemini:
    return Gemini(
        model=MODEL_NAME,
        retry_options=types.HttpRetryOptions(
            attempts=4,
            initial_delay=1,
            max_delay=16,
            exp_base=2,
            jitter=0.2,
        ),
    )


finder = Agent(
    name="finder",
    description="Searches the live literature and web for an interesting research opening.",
    model=_model(),
    instruction=FINDER,
    tools=[google_search],
)

theorist = Agent(
    name="theorist",
    description="Turns an opening into a precise mechanism, claim, proof, or counterexample.",
    model=_model(),
    instruction=THEORIST,
    tools=[compare_research_claims],
)

experimentalist = Agent(
    name="experimentalist",
    description=(
        "Runs cheap decisive Python probes in Gemini's isolated code execution environment."
    ),
    model=_model(),
    instruction=EXPERIMENTALIST,
    code_executor=BuiltInCodeExecutor(stateful=False, timeout_seconds=120),
)

critic = Agent(
    name="critic",
    description="Tries to break the current claim and returns a stronger repair.",
    model=_model(),
    instruction=CRITIC,
)

writer = Agent(
    name="writer",
    description="Synthesizes evidence and failures into a research packet worth continuing.",
    model=_model(),
    instruction=WRITER,
    tools=[write_research_artifact, publish_research_packet],
)

explainer = Agent(
    name="explainer",
    description="Explains a team's research or a paper so a human truly understands it.",
    model=_model(),
    instruction=EXPLAINER,
)

root_agent = Agent(
    name="cloud_research",
    description="A persistent panel of expert AI researchers working with one human PI.",
    model=_model(),
    instruction=DIRECTOR,
    tools=[
        AgentTool(finder),
        AgentTool(theorist),
        AgentTool(experimentalist),
        AgentTool(critic),
        AgentTool(writer),
        AgentTool(explainer),
    ],
)

app = App(name="cloud_research", root_agent=root_agent)
