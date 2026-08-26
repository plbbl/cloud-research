"""Small persistent model for user-defined research labs."""

from __future__ import annotations

import json
import re
import threading
import uuid
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

SAFE_ID = re.compile(r"^[a-z][a-z0-9_]{0,47}$")
SAFE_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


class LabAgentSpec(BaseModel):
    id: str
    name: str = Field(min_length=1, max_length=48)
    role: str = Field(min_length=1, max_length=320)
    color: str = "#2a92fe"

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not SAFE_ID.fullmatch(value):
            raise ValueError("Agent ids must be lowercase identifiers.")
        return value

    @field_validator("name", "role")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        if not SAFE_COLOR.fullmatch(value):
            raise ValueError("Agent colors must be six-digit hex values.")
        return value.lower()


class LabDraft(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    mission: str = Field(min_length=1, max_length=800)
    agents: list[LabAgentSpec] = Field(min_length=1, max_length=12)

    @field_validator("name", "mission")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("agents")
    @classmethod
    def unique_agents(cls, agents: list[LabAgentSpec]) -> list[LabAgentSpec]:
        ids = [agent.id for agent in agents]
        names = [agent.name.casefold() for agent in agents]
        if len(ids) != len(set(ids)) or len(names) != len(set(names)):
            raise ValueError("Every agent needs a unique id and name inside its lab.")
        return agents


class LabSpec(LabDraft):
    id: str
    version: int = 1


DEFAULT_LAB = LabSpec(
    id="cloud_research",
    name="Cloud Research Lab",
    mission="Find important, tractable research openings and turn them into evidence-backed work.",
    version=1,
    agents=[
        LabAgentSpec(
            id="finder",
            name="Finder",
            role="Map live literature, code, and overlooked research openings.",
            color="#ff5eb1",
        ),
        LabAgentSpec(
            id="theorist",
            name="Theorist",
            role="Turn openings into precise mechanisms, claims, proofs, or counterexamples.",
            color="#a97efe",
        ),
        LabAgentSpec(
            id="experimentalist",
            name="Experimentalist",
            role="Design and run the cheapest experiment that can change the decision.",
            color="#a27952",
        ),
        LabAgentSpec(
            id="critic",
            name="Critic",
            role="Attack the strongest claim, expose failure, and propose a stronger repair.",
            color="#000000",
        ),
        LabAgentSpec(
            id="writer",
            name="Writer",
            role="Synthesize evidence, failures, and next moves into a research handoff.",
            color="#00c972",
        ),
        LabAgentSpec(
            id="explainer",
            name="Explainer",
            role="Make a paper, task, result, or this lab's work genuinely understandable.",
            color="#2a92fe",
        ),
    ],
)


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    if not cleaned or not cleaned[0].isalpha():
        cleaned = f"lab_{cleaned}" if cleaned else "research_lab"
    return cleaned[:36]


class LabStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._labs = self._load()

    def _load(self) -> list[LabSpec]:
        if not self.path.exists():
            return [DEFAULT_LAB.model_copy(deep=True)]
        data = json.loads(self.path.read_text(encoding="utf-8"))
        labs = [LabSpec.model_validate(item) for item in data]
        return labs or [DEFAULT_LAB.model_copy(deep=True)]

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [lab.model_dump(mode="json") for lab in self._labs]
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def list(self) -> list[LabSpec]:
        with self._lock:
            return [lab.model_copy(deep=True) for lab in self._labs]

    def get(self, lab_id: str) -> LabSpec | None:
        with self._lock:
            lab = next((item for item in self._labs if item.id == lab_id), None)
            return lab.model_copy(deep=True) if lab else None

    def create(self, draft: LabDraft) -> LabSpec:
        with self._lock:
            base = _slug(draft.name)
            existing = {lab.id for lab in self._labs}
            lab_id = base
            while lab_id in existing:
                lab_id = f"{base[:27]}_{uuid.uuid4().hex[:8]}"
            lab = LabSpec(id=lab_id, version=1, **draft.model_dump())
            self._labs.append(lab)
            self._save()
            return lab.model_copy(deep=True)

    def update(self, lab_id: str, draft: LabDraft) -> LabSpec | None:
        with self._lock:
            for index, current in enumerate(self._labs):
                if current.id != lab_id:
                    continue
                updated = LabSpec(
                    id=current.id,
                    version=current.version + 1,
                    **draft.model_dump(),
                )
                self._labs[index] = updated
                self._save()
                return updated.model_copy(deep=True)
        return None

    def delete(self, lab_id: str) -> bool:
        with self._lock:
            if len(self._labs) == 1:
                return False
            remaining = [lab for lab in self._labs if lab.id != lab_id]
            if len(remaining) == len(self._labs):
                return False
            self._labs = remaining
            self._save()
            return True
