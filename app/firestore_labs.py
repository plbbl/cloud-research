"""Firestore persistence for user-defined labs, selected only when configured."""

from __future__ import annotations

import uuid
from pathlib import Path

from .labs import DEFAULT_LAB, LabDraft, LabSpec, LabStore, _slug
from .research_ledger import ResearchLedger


class FirestoreLabStore:
    def __init__(self, ledger: ResearchLedger) -> None:
        if not ledger.client:
            raise ValueError("Firestore is not configured.")
        self.collection = ledger.client.collection("labs")

    def list(self) -> list[LabSpec]:
        labs = [LabSpec.model_validate(item.to_dict()) for item in self.collection.stream()]
        if labs:
            return sorted(labs, key=lambda lab: lab.name.casefold())
        lab = DEFAULT_LAB.model_copy(deep=True)
        self.collection.document(lab.id).set(lab.model_dump(mode="json"))
        return [lab]

    def get(self, lab_id: str) -> LabSpec | None:
        snapshot = self.collection.document(lab_id).get()
        return LabSpec.model_validate(snapshot.to_dict()) if snapshot.exists else None

    def create(self, draft: LabDraft) -> LabSpec:
        base = _slug(draft.name)
        lab_id = base
        while self.collection.document(lab_id).get().exists:
            lab_id = f"{base[:27]}_{uuid.uuid4().hex[:8]}"
        lab = LabSpec(id=lab_id, version=1, **draft.model_dump())
        self.collection.document(lab.id).set(lab.model_dump(mode="json"))
        return lab

    def update(self, lab_id: str, draft: LabDraft) -> LabSpec | None:
        current = self.get(lab_id)
        if current is None:
            return None
        updated = LabSpec(id=lab_id, version=current.version + 1, **draft.model_dump())
        self.collection.document(lab_id).set(updated.model_dump(mode="json"))
        return updated

    def delete(self, lab_id: str) -> bool:
        labs = self.list()
        if len(labs) == 1 or not any(lab.id == lab_id for lab in labs):
            return False
        self.collection.document(lab_id).delete()
        return True


def build_lab_store(path: Path, ledger: ResearchLedger) -> LabStore | FirestoreLabStore:
    return FirestoreLabStore(ledger) if ledger.enabled else LabStore(path)
