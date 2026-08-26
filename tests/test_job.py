from app.job import research_job_app, research_job_prompt
from app.labs import LabAgentSpec, LabSpec


def test_job_prompt_delegates_the_path_but_demands_a_handoff() -> None:
    prompt = research_job_prompt("Investigate small-model adaptation.")

    assert "any available experts, in any order" in prompt
    assert "evidence-backed Handoff" in prompt
    assert "publishing expert" in prompt
    assert "Investigate small-model adaptation." in prompt


def test_research_job_rebuilds_the_selected_lab() -> None:
    lab = LabSpec(
        id="mechanism_lab",
        name="Mechanism Lab",
        mission="Find one mechanism worth testing.",
        agents=[
            LabAgentSpec(
                id="scout",
                name="Scout",
                role="Search for the nearest mechanism.",
                color="#222222",
            )
        ],
    )

    app = research_job_app(lab.model_dump_json())

    assert app.name == "mechanism_lab"
    assert app.root_agent.name == "mechanism_lab"
    assert app.root_agent.tools[1].name == "scout"
