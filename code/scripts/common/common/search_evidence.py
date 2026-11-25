"""Choose body evidence while preserving short definitions and source chunks.

Pure section-reference sentences remain in the corpus and can be requested
explicitly. Default answer retrieval selects body evidence from a bounded window;
it never rewrites source text, similarity scores, or source identifiers.
"""
from __future__ import annotations

import re
from collections.abc import Mapping

from .payload_text import first_text_field

_REFERENCE = r"[A-Z]?\d+(?:\.\d+)+(?:[A-Z])?"
_TARGETS = rf"{_REFERENCE}(?:\s*(?:,|and|or)\s*{_REFERENCE})*"
_REFERENCE_ONLY = re.compile(
    rf"(?:see|refer to)\s+(?:sub)?clauses?\s+{_TARGETS}[.;]?|"
    rf"[^.!?]{{1,180}}\b(?:is|are)\s+(?:described|specified|defined|given)\s+"
    rf"in\s+(?:sub)?clauses?\s+{_TARGETS}[.;]?",
    re.IGNORECASE,
)


def reference_only_targets(text: str) -> list[str]:
    """Return clause targets only when the entire body is a reference sentence."""
    normalized = " ".join(text.split())
    if not _REFERENCE_ONLY.fullmatch(normalized):
        return []
    return re.findall(_REFERENCE, normalized)


def candidate_limit(top: int) -> int:
    """Bound over-retrieval used to find body evidence behind reference stubs."""
    if not isinstance(top, int) or isinstance(top, bool) or not 1 <= top <= 512:
        raise ValueError("top must be an integer between 1 and 512")
    return min(512, max(32, top * 8))


def select_body_evidence(candidates: list[dict], *, include_references: bool = False,
                         text_keys: tuple[str, ...] = ("text", "content", "asn1")) -> list[dict]:
    """Filter only full reference sentences; valid short bodies stay searchable.

    Each result is a new dictionary with its selection reason and any explicit
    clause targets. Input records and ordering among retained records are intact.
    Empty windows remain empty instead of treating a reference as body evidence.
    """
    if not isinstance(include_references, bool):
        raise ValueError("include_references must be a boolean")
    out = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise ValueError("search candidate must be an object")
        targets = reference_only_targets(first_text_field(candidate, text_keys))
        if targets and not include_references:
            continue
        out.append({**candidate, "evidence_kind": "reference_only" if targets else "body",
                    "reference_targets": targets})
    return out
