#!/usr/bin/env python3
"""report_decision_identity.py — Preserve decision identity across agenda-only corrections.

Spec: docs/tsg/RAN/formal/RAN1/phase-2/step1_parsing.md.
Ontology: Resolution identity is separate from resolutionBelongsTo placement.
Cycle: accepted source event -> parsed report -> stable Resolution and disposition IDs.
배경: corrected heading context must not rename unchanged decision occurrences.
사용: preserve_decision_ids(current_report_dict, previous_report_dict) before save.
LLM 호출: none. This module performs no file or database writes.
"""
from __future__ import annotations

from copy import deepcopy
import json

CATEGORIES = ('agreements', 'conclusions', 'working_assumptions')


def _signature(row):
    """Bind to the same accepted occurrence, excluding mutable location metadata."""
    required = ('decision_type', 'paragraph_index', 'content', 'body_blocks')
    if any(key not in row for key in required):
        return None
    fields = {key: value for key, value in row.items()
              if key not in {'decision_id', 'agenda_item', 'sequence'}}
    return json.dumps(fields, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def preserve_decision_ids(current, previous):
    """Return a copy with old IDs for byte-equivalent parsed source occurrences.

    A changed body, source span, target list, or decision kind creates no match.
    Ambiguous occurrences and ID collisions require explicit review before save.
    """
    result = deepcopy(current)
    if previous is None:
        return result
    if any(current.get(key) != previous.get(key) for key in ('meeting_id', 'docx_path')):
        raise ValueError('Cannot reuse decision IDs across a different meeting or source path')
    prior = {}
    for category in CATEGORIES:
        for row in previous.get(category, []):
            signature = _signature(row)
            if signature is None:
                continue
            if signature in prior:
                raise ValueError('Ambiguous previous accepted decision occurrence')
            prior[signature] = row['decision_id']
    seen = set()
    for category in CATEGORIES:
        for row in result.get(category, []):
            signature = _signature(row)
            if signature is not None and signature in prior:
                row['decision_id'] = prior[signature]
            identity = row['decision_id']
            if identity in seen:
                raise ValueError(f'Decision ID collision after source-bound reuse: {identity}')
            seen.add(identity)
    return result
