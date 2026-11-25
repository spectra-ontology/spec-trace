#!/usr/bin/env python3
"""capability_members.py — validate literal membership in a native definition row.

Spec: capability physical-source-row retrieval contract.
Ontology: joint definition membership supplies provenance, not entity equivalence.
Cycle: payload receipt → exact native label/cells/body binding → member lookup.
배경: names shared by a source row need their own defining receipt.
사용: source_members(payload), defines_member(payload, name).
LLM 호출: 없음. No name is recovered from a body mention or a release suffix.
"""
from __future__ import annotations

import hashlib
import re


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _line(cells):
    return ' | '.join(' '.join(part for part in c.split('\n') if part).strip() for c in cells)


def source_members(payload):
    """Return exact literal names only when their whole source-row receipt binds."""
    cap = payload.get('capability')
    if not isinstance(cap, dict):
        return ()
    source, label, members = cap.get('source'), cap.get('feature'), cap.get('members')
    if not isinstance(source, dict) or not isinstance(label, str) or not isinstance(members, list):
        return ()
    expected = [part.strip() for part in re.split(r'[,/]', label)]
    if members != expected or not members or len(set(members)) != len(members):
        return ()
    if any(not isinstance(m, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]+', m) for m in members):
        return ()
    relation = 'literal_member_of_joint_source_definition' if len(members) > 1 else 'literal_source_label'
    if cap.get('memberRelation') != relation:
        return ()
    cells, header = source.get('rowCells'), source.get('headerCells')
    if not isinstance(cells, list) or not isinstance(header, list) or len(cells) != len(header) or not cells:
        return ()
    if any(not isinstance(c, str) for c in cells + header) or cells[0].split('\n')[0].strip() != label:
        return ()
    if not re.fullmatch(r'[a-f0-9]{64}', str(source.get('sourceSHA256') or '')) or not source.get('sourcePath'):
        return ()
    if type(source.get('table')) is not int or type(source.get('acceptedRow')) is not int or not source.get('locator'):
        return ()
    if source.get('sourceSectionId') != payload.get('parentSectionId'):
        return ()
    release, version = source.get('sourceRelease'), source.get('sourceVersion')
    if not isinstance(release, str) or not re.fullmatch(r'Rel-\d+', release):
        return ()
    if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+', version):
        return ()
    if release != 'Rel-' + version.split('.')[0] or payload.get('specReleases') != [release]:
        return ()
    body = payload.get('text')
    if not isinstance(body, str) or _sha(body) != source.get('searchTextSHA256'):
        return ()
    row = _line(cells)
    if _sha(row) != source.get('rowTextSHA256') or not body.startswith('Columns: ' + _line(header) + '\n' + row):
        return ()
    return tuple(members)


def defines_member(payload, name):
    return name in source_members(payload)
