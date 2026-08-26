"""Build a Google ADK team directly from a lab definition."""

from __future__ import annotations

import os

from google.adk.agents import Agent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import AgentTool, google_search
from google.genai import types

from .labs import LabAgentSpec, LabSpec
from .prompts import CRITIC, EXPERIMENTALIST, EXPLAINER, FINDER, THEORIST, WRITER
from .tools import compare_research_claims, publish_research_packet, write_research_artifact

MODEL_NAME = os.getenv("CLOUD_RESEARCH_MODEL", "gemini-3.7-flash")

ROLE_PROMPTS = {
    "finder": FINDER,
    "theorist": THEORIST,
    "experimentalist": EXPERIMENTALIST,
    "critic": CRITIC,
    "writer": WRITER,
    "explainer": EXPLAINER,
}


def expert_capability(spec: LabAgentSpec) -> str:
    """Infer useful Google-native tools from the role the human wrote."""
    copy = f"{spec.id} {spec.name} {spec.role}".lower()
    for capability, pattern in [
        ("writer", "write|writer|report|synthesi|publish|artifact|handoff"),
        ("experimentalist", "experiment|test|code|execute|run|prototype|build"),
        ("theorist", "theor|mechanism|proof|prove|counterexample|formal|predict"),
        ("critic", "critic|challenge|attack|falsif|risk|review|breaker"),
        ("explainer", "explain|teach|clarif|understand"),
        ("finder", "find|search|paper|prior|literature|scout|novel"),
    ]:
        if any(token in copy for token in pattern.split("|")):
            return capability
    return spec.id if spec.id in ROLE_PROMPTS else "finder"


def model() -> Gemini:
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


def expert_instruction(spec: LabAgentSpec, mission: str) -> str:
    specialist = ROLE_PROMPTS[expert_capability(spec)]
    return "\n".join(
        part
        for part in [
            specialist,
            f"You are {spec.name}. Your role: {spec.role}",
            f"Lab mission: {mission}",
            (
                "Search the live web whenever current evidence could matter. Be concise, find the "
                "interesting truth, and believe a valuable research opening exists."
            ),
        ]
        if part
    )


def build_expert(spec: LabAgentSpec, mission: str) -> Agent:
    tools: list = [google_search]
    code_executor = None
    capability = expert_capability(spec)
    if capability == "theorist":
        tools.append(compare_research_claims)
    elif capability == "writer":
        tools.extend([write_research_artifact, publish_research_packet])
    elif capability == "experimentalist":
        code_executor = BuiltInCodeExecutor(stateful=False, timeout_seconds=120)

    return Agent(
        name=spec.id,
        description=spec.role,
        model=model(),
        instruction=expert_instruction(spec, mission),
        tools=tools,
        code_executor=code_executor,
    )


def director_instruction(lab: LabSpec) -> str:
    roster = "; ".join(f"{agent.name}: {agent.role}" for agent in lab.agents)
    return (
        f"You direct {lab.name}. Mission: {lab.mission}\n"
        f"Experts: {roster}\n"
        "The human is the PI. Treat @Name as direct speech. Otherwise recruit only useful experts, "
        "in any order, as often as useful. Carry one expert's evidence into the next call so they "
        "challenge and extend each other. Search live sources. Return one Handoff: Claim; Evidence "
        "with bare source links; Killed paths; Unknowns; Next decisive task; Artifact. Valuable "
        "research fruit "
        "exists; this candidate may not be it. Keep moving."
    )


def build_lab_agent(lab: LabSpec) -> Agent:
    experts = [build_expert(spec, lab.mission) for spec in lab.agents]
    return Agent(
        name=lab.id,
        description=f"A configurable multi-agent research team for {lab.name}.",
        model=model(),
        instruction=director_instruction(lab),
        tools=[google_search, *[AgentTool(expert) for expert in experts]],
    )
