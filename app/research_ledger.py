"""Append-only research facts in Firestore; never a scientific workflow engine."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from typing import Any

from google.api_core.exceptions import AlreadyExists
from google.cloud import firestore


@dataclass
class ResearchLedger:
    """Persist labs, external deliveries, run facts, and handoffs when configured."""

    client: firestore.Client | None = None

    @classmethod
    def from_env(cls) -> ResearchLedger:
        database = os.getenv("CLOUD_RESEARCH_FIRESTORE_DATABASE", "").strip()
        if not database:
            return cls()
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip() or None
        return cls(firestore.Client(project=project, database=database))

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def begin_run(
        self,
        run_id: str,
        *,
        brief: str,
        lab: dict[str, Any],
        source: str,
    ) -> None:
        if not self.client:
            return
        self.client.collection("runs").document(run_id).set(
            {
                "run_id": run_id,
                "brief": brief,
                "lab": lab,
                "source": source,
                "created_at": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )

    def append_event(self, run_id: str, event: dict[str, Any]) -> None:
        if not self.client:
            return
        sequence = int(event["sequence"])
        self.client.collection("runs").document(run_id).collection("events").document(
            f"{sequence:06d}"
        ).set({**event, "recorded_at": firestore.SERVER_TIMESTAMP})
        if event.get("output") and event.get("state") == "complete":
            self.client.collection("runs").document(run_id).set(
                {
                    "handoff": str(event["output"]),
                    "completed_at": firestore.SERVER_TIMESTAMP,
                },
                merge=True,
            )
        elif event.get("state") == "error":
            self.client.collection("runs").document(run_id).set(
                {
                    "error": str(event.get("output", "")),
                    "failed_at": firestore.SERVER_TIMESTAMP,
                },
                merge=True,
            )

    def list_events(self, run_id: str) -> list[dict[str, Any]]:
        if not self.client:
            return []
        query = (
            self.client.collection("runs")
            .document(run_id)
            .collection("events")
            .order_by("sequence")
        )
        events = []
        for snapshot in query.stream():
            payload = snapshot.to_dict()
            events.append(
                {
                    "sequence": int(payload.get("sequence", 0)),
                    "agent": str(payload.get("agent", "director")),
                    "state": str(payload.get("state", "directing")),
                    "detail": str(payload.get("detail", "Research is moving")),
                    "output": str(payload.get("output", "")),
                    "timestamp": _iso(payload.get("recorded_at")),
                }
            )
        return events

    def handoff(self, run_id: str) -> str:
        if not self.client:
            return ""
        snapshot = self.client.collection("runs").document(run_id).get()
        return str((snapshot.to_dict() or {}).get("handoff", "")) if snapshot.exists else ""

    def claim_delivery(self, delivery_id: str) -> bool:
        if not self.client:
            return False
        try:
            self.client.collection("github_deliveries").document(delivery_id).create(
                {"received_at": firestore.SERVER_TIMESTAMP}
            )
        except AlreadyExists:
            return False
        return True


@dataclass
class LocalDeliveryClaims:
    """Best-effort webhook deduplication for local development without Firestore."""

    _claims: set[str] = field(default_factory=set)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def claim(self, delivery_id: str) -> bool:
        with self._lock:
            if delivery_id in self._claims:
                return False
            self._claims.add(delivery_id)
            return True


def _iso(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value or "")


ledger = ResearchLedger.from_env()
local_delivery_claims = LocalDeliveryClaims()


def claim_github_delivery(delivery_id: str) -> bool:
    return ledger.claim_delivery(delivery_id) if ledger.enabled else local_delivery_claims.claim(
        delivery_id
    )
