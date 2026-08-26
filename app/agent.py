"""Default Google ADK app used by the standard ADK and Cloud Run surfaces."""

from google.adk.apps import App

from .lab_agents import MODEL_NAME as MODEL_NAME
from .lab_agents import build_lab_agent
from .labs import DEFAULT_LAB

root_agent = build_lab_agent(DEFAULT_LAB)

app = App(name="cloud_research", root_agent=root_agent)

__all__ = ["MODEL_NAME", "app", "root_agent"]
