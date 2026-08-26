from pathlib import Path

from app.lab_agents import build_expert, build_lab_agent, expert_capability
from app.labs import DEFAULT_LAB, LabAgentSpec, LabDraft, LabSpec, LabStore
from app.live_voice import LIVE_MODEL_NAME, live_config, live_instruction


def draft(name: str = "Vision Lab") -> LabDraft:
    return LabDraft(
        name=name,
        mission="Find a decisive vision research opening.",
        agents=[
            LabAgentSpec(
                id="scout",
                name="Scout",
                role="Search current papers and implementations.",
                color="#ff5eb1",
            ),
            LabAgentSpec(
                id="breaker",
                name="Breaker",
                role="Try to falsify every important claim.",
                color="#000000",
            ),
        ],
    )


def test_lab_store_creates_updates_and_reloads(tmp_path: Path) -> None:
    path = tmp_path / "labs.json"
    store = LabStore(path)

    created = store.create(draft())
    updated = store.update(created.id, draft("Vision Systems Lab"))

    assert updated is not None
    assert updated.version == 2
    assert updated.agents[0].name == "Scout"
    assert LabStore(path).get(created.id).name == "Vision Systems Lab"


def test_dynamic_lab_builds_search_grounded_agent_tools() -> None:
    spec = draft()
    root = build_lab_agent(LabSpec(id="vision_lab", version=1, **spec.model_dump()))

    assert root.tools[0].name == "google_search"
    expert_tools = root.tools[1:]
    assert {tool.name for tool in expert_tools} == {"scout", "breaker"}
    assert all(tool.agent.tools[0].name == "google_search" for tool in expert_tools)


def test_custom_roles_receive_google_native_capabilities() -> None:
    scientist = LabAgentSpec(
        id="scientist",
        name="Scientist",
        role="Design and run the cheapest decisive experiment.",
        color="#222222",
    )
    publisher = LabAgentSpec(
        id="reporter",
        name="Reporter",
        role="Write and publish the evidence-backed handoff.",
        color="#333333",
    )

    assert expert_capability(scientist) == "experimentalist"
    assert build_expert(scientist, "Test one opening.").code_executor is not None
    assert expert_capability(publisher) == "writer"
    assert {
        getattr(tool, "name", getattr(tool, "__name__", ""))
        for tool in build_expert(publisher, "Test one opening.").tools
    } == {
        "google_search",
        "write_research_artifact",
        "publish_research_packet",
    }


def test_live_voice_is_native_audio_with_search_and_lab_context() -> None:
    config = live_config(DEFAULT_LAB)

    assert LIVE_MODEL_NAME == "gemini-3.1-flash-live-preview"
    assert [modality.value for modality in config.response_modalities] == ["AUDIO"]
    assert config.tools[0].google_search is not None
    assert config.input_audio_transcription is not None
    assert config.output_audio_transcription is not None
    assert DEFAULT_LAB.name in live_instruction(DEFAULT_LAB)
