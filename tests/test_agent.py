from google.adk.tools import AgentTool

from app.agent import MODEL_NAME, app, root_agent


def test_google_stack_and_expert_panel() -> None:
    assert MODEL_NAME == "gemini-3.7-flash"
    assert app.name == "cloud_research"
    assert root_agent.name == "cloud_research"
    assert all(isinstance(tool, AgentTool) for tool in root_agent.tools)
    assert {tool.name for tool in root_agent.tools} == {
        "finder",
        "theorist",
        "experimentalist",
        "critic",
        "writer",
        "explainer",
    }
