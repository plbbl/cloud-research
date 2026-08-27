"""Small, deterministic helpers created for the Cloud Research lab.

There is intentionally no workflow engine here. The model decides what research
to do; these helpers only let it compare claims and preserve useful artifacts.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

_BORING_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "we",
    "with",
}


def research_terms(text: str) -> set[str]:
    """Return stable content terms for a research claim."""
    words = re.findall(r"[a-z0-9]+|[\u3400-\u9fff]+", text.lower())
    return {word for word in words if len(word) > 1 and word not in _BORING_WORDS}


def jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    """Measure overlap without pretending it is semantic understanding."""
    left_set, right_set = set(left), set(right)
    union = left_set | right_set
    return len(left_set & right_set) / len(union) if union else 1.0


def compare_claim_text(left: str, right: str) -> dict[str, object]:
    """Give Gemini a cheap lexical duplicate hint, never a novelty verdict."""
    left_terms, right_terms = research_terms(left), research_terms(right)
    shared = sorted(left_terms & right_terms)
    return {
        "overlap": round(jaccard(left_terms, right_terms), 3),
        "shared_terms": shared[:24],
        "interpretation": (
            "A lexical clue only. Read the mechanism and evidence before deciding whether "
            "the claims are actually the same."
        ),
    }


def safe_artifact_name(title: str) -> str:
    """Create a portable Markdown filename."""
    cleaned = re.sub(r"[^a-z0-9\u3400-\u9fff]+", "-", title.lower()).strip("-")
    return (cleaned or "research-note")[:80] + ".md"
