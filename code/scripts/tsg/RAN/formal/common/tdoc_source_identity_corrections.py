#!/usr/bin/env python3
"""tdoc_source_identity_corrections.py — overlay independently checked CR identities.

Spec: Phase-1 Tdoc identity and revision contract; original spreadsheet remains an input.
Ontology: source-owned CR number/revision, Spec/Release and immediate document revisions.
Cycle: retained ledger → own cover plus complete report entry → selected-meeting overlay.
배경: report and CR cover can identify an error in a spreadsheet snapshot.
사용: validated_corrections(root, wg); overlay_identity_corrections(...).
LLM 호출: none. Local original bytes only; no network or database writes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from tdoc_source_supplements import SupplementError, canonical_meeting, checked_path, normalized


def ledger_path(root: Path, wg: str) -> Path:
    from tdoc_source_supplements import ledger_path as supplement_path
    return supplement_path(root, wg).with_name('tdoc_source_identity_corrections.json')


def validate_correction(root, row):
    from decision_disposition import source_blocks
    evidence = row['review']['actualDocumentEvidence']
    if not evidence:
        raise SupplementError('Identity correction requires its own unambiguous CR source')
    groups = {}
    for item in evidence:
        groups.setdefault((item['path'], item['sha256']), []).append(item)
    if len(groups) > 1:
        for group in groups.values():
            validate_correction(root, {**row, 'review': {**row['review'], 'actualDocumentEvidence': group}})
        return row
    first = evidence[0]
    path = checked_path(root, first['path'], first['sha256'])
    texts, sha, _ = source_blocks(str(path.resolve()))
    if sha != first['sha256']:
        raise SupplementError('Cached correction source does not match actual bytes')
    for item in evidence:
        loc = re.fullmatch(r'word/document.xml accepted body blocks \[(\d+),(\d+)\)', item['locator'])
        if not loc or int(loc[2]) != int(loc[1]) + 1 or texts[int(loc[1])] != item['quote']:
            raise SupplementError('Correction cover locator/quote changed: ' + row['target'])
    if not re.search(r'(?<![\w-])' + re.escape(row['target']) + r'(?![\w-])', texts[0]):
        raise SupplementError('Correction source does not identify its own document')
    # Meeting selection is the checked report's identity. CR cover templates can
    # retain a previous meeting header; only the enumerated CR fields are overlaid.
    target_wg = re.fullmatch(r'R([1-5])-\d{6,8}', row['target'])
    cover_wg = re.search(r'TSG[ -]RAN\s*(?:WG)?\s*([1-5])\b', texts[0], re.I)
    if not target_wg or not cover_wg or target_wg[1] != cover_wg[1]:
        raise SupplementError('Correction cover is outside its document working group')
    cover = '\n'.join(item['quote'] for item in evidence)
    # The same accepted Word view binds both the quote and the CR identity.
    # A tracked insertion can replace a CR# placeholder; python-docx's ordinary
    # cell text still exposes the placeholder in such a source.
    headers = list(re.finditer(r'\|\s*(\d{2}\.\d{3}(?:-\d+)?)\s*\|\s*CR\s*\|\s*(\d+)\s*\|\s*rev\s*\|\s*([^|]*)\|\s*Current version:', cover, re.I))
    if len(headers) != 1:
        raise SupplementError('Correction requires exactly one accepted CR-form identity')
    spec, cr_number, revision = headers[0].groups()
    revision = revision.strip()
    if revision not in ('', '-', '0') and not revision.isdigit():
        raise SupplementError('Correction CR revision is not an assigned number')
    revision = revision if revision not in ('', '-') else '0'
    release = re.search(r'Release:\s*\|\s*<?\s*(Rel-\d+)\b', cover, re.I)
    actual = {'modifies': 'tdoc:spec/' + spec.replace('.', '_'),
              'tdoc:crNumber': cr_number, 'tdoc:crRevision': revision,
              'targetRelease': 'tdoc:release/' + release[1].replace('-', '_') if release else None}
    report = row['reportEntry']
    if canonical_meeting(report['meeting']) != canonical_meeting(row['meetingId']):
        raise SupplementError('Correction report is outside the selected meeting')
    report_path = checked_path(root, report['path'], report['sourceSHA256'])
    rt, report_sha, _ = source_blocks(str(report_path.resolve()))
    if report_sha != report['sourceSHA256']:
        raise SupplementError('Cached correction report does not match its bytes')
    source_event = report.get('sourceEvent')
    if source_event is not None:
        # A header-indexed Annex row has its own locator. Adjacent CR rows and
        # free text in the table cannot supply this target's identity fields.
        from document_decision_source import annex_source_evidence
        checked = annex_source_evidence(source_event, root)
        if (checked['path'] != report['path'] or checked['sha256'] != report['sourceSHA256']
                or checked['locator'] != report['locator'] or checked['quote'] != report['quote']
                or source_event['subject_tdoc'] != row['target']
                or canonical_meeting(source_event['meeting_id']) != canonical_meeting(row['meetingId'])):
            raise SupplementError('Correction Annex source identity changed')
        fields = source_event['document_entry']['sourceFields']
        if (fields.get('spec') != spec or not str(fields.get('crNumber') or '').isdigit()
                or int(fields['crNumber']) != int(cr_number)
                or not str(fields.get('crRevision') or '').isdigit()
                or int(fields['crRevision']) != int(revision)
                or not release or fields.get('release') != release[1]):
            raise SupplementError('Own cover and Annex row disagree on corrected CR identity: ' + row['target'])
        entry = checked['quote']
    else:
        start, end = report['startBlock'], report['endBlockExclusive']
        if ([e['block'] for e in report['entry']] != list(range(start, end))
            or any(rt[e['block']] != e['text'] for e in report['entry'])
            or not re.match(r'^' + re.escape(row['target']) + r'\s', rt[start])):
            raise SupplementError('Correction report entry span/identity changed')
        entry = '\n'.join(rt[start:end])
        descriptor = re.search(r'(\d{2}\.\d{3}(?:-\d+)?)(?:\s+v\d+\.\d+\.\d+)?\s+CR-?(\d+)(?:\s+rev\s+(\d+))?\s+Cat:\s*[A-F]\s*\((Rel-\d+)\)', entry)
        if (not descriptor or descriptor[1] != spec or int(descriptor[2]) != int(cr_number)
            or (descriptor[3] or '0') != revision
            or not release or descriptor[4] != release[1]):
            raise SupplementError('Own cover and final report disagree on corrected CR identity: ' + row['target'])
    prior = re.findall(r'\(Replaces\s+(R[1-5]-\d{6,8})\)', entry)
    outputs = re.findall(r'Decision:\s*The document was revised to (R[1-5]-\d{6,8})\.', entry)
    if len(prior) == 1:
        actual['isRevisionOf'] = 'tdoc:' + prior[0]
    if len(outputs) == 1:
        actual['revisedTo'] = 'tdoc:' + outputs[0]
    allowed = {'modifies', 'targetRelease', 'tdoc:crNumber', 'tdoc:crRevision', 'isRevisionOf', 'revisedTo'}
    for delta in row['deltas']:
        if delta['field'] not in allowed or actual.get(delta['field']) != delta['sourceBackedValue']:
            raise SupplementError('Correction delta lacks direct cover/report support: ' + row['target'])
    return row


def validated_corrections(root: Path, wg: str, selected_meetings: set[str] | None = None) -> list[dict]:
    path = ledger_path(root, wg)
    if not path.exists():
        return []
    ledger = json.loads(path.read_text())
    rows = ledger.get('records')
    if ledger.get('schema') != 1 or ledger.get('wg') != wg or not isinstance(rows, list):
        raise SupplementError('Invalid CR source correction ledger')
    if len({row['target'] for row in rows}) != len(rows):
        raise SupplementError('Duplicate correction identity')
    selected = None if selected_meetings is None else {canonical_meeting(m) for m in selected_meetings}
    return [validate_correction(root, row) for row in rows
            if selected is None or canonical_meeting(row['meetingId']) in selected]


def source_inputs(root, wg, selected_meetings):
    path = ledger_path(root, wg)
    if not path.exists():
        return {}
    result = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()}
    for row in validated_corrections(root, wg, selected_meetings):
        for item in row['review']['actualDocumentEvidence']:
            result[item['path']] = item['sha256']
        result[row['reportEntry']['path']] = row['reportEntry']['sourceSHA256']
    return result


def overlay_identity_corrections(root, wg, instances, references, selected_meetings):
    """Apply only enumerated source-backed fields; accept the reviewed or corrected value."""
    rows = validated_corrections(root, wg, selected_meetings)
    nodes = {n['@id']: n for n in instances}
    endpoints = set(nodes) | {n['@id'] for graph in references.values() for n in graph}
    changed = []
    for row in rows:
        node = nodes.get('tdoc:' + row['target'])
        if node is None:
            raise SupplementError('Selected source correction target is absent: ' + row['target'])
        for delta in row['deltas']:
            field, before, after = delta['field'], delta['before'], delta['sourceBackedValue']
            if field in ('modifies', 'targetRelease', 'isRevisionOf', 'revisedTo') and after not in endpoints:
                raise SupplementError('Correction endpoint is absent: ' + after)
            current = node.get(field)
            if current not in (before, after):
                raise SupplementError('Unreviewed canonical correction preimage: ' + row['target'] + ' ' + field)
            if current != after:
                changed.append({'target': row['target'], 'scope': row['scope'], **delta})
                node[field] = after
    return changed
