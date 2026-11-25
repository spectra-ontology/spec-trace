#!/usr/bin/env python3
"""tdoc_source_classification.py — source-owned classification of assigned CR documents.

Spec: Phase-1 document identity and selected-source count contract.
Ontology: a numbered CR form is a CR document; its disposition is a separate assertion.
Cycle: own cover and complete report entry → selected source overlay → exact projections.
배경: spreadsheet reservation rows can retain a generic document class after upload.
사용: validated_classifications(...); apply_source_classifications(...).
LLM 호출: none. Retained source bytes only; no database or embedding calls.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import zipfile

from tdoc_source_supplements import SupplementError, canonical_meeting, checked_path, normalized

_VALIDATED = {}


def ledger_path(root: Path, wg: str) -> Path:
    from tdoc_source_supplements import ledger_path as supplement_path
    return supplement_path(root, wg).with_name('tdoc_source_classifications.json')


def validate_classification(root, row):
    from decision_disposition import source_blocks
    evidence = row['review']['actualDocumentEvidence']
    identity = row['coverIdentity']
    if not evidence or {(e['path'], e['sha256']) for e in evidence} != {(identity['path'], identity['sha256'])}:
        raise SupplementError('Classification requires one own-document cover')
    path = checked_path(root, identity['path'], identity['sha256'])
    if archive := row.get('selectedSourceArchive'):
        archive_path = checked_path(root, archive['path'], archive['sha256'])
        with zipfile.ZipFile(archive_path) as source:
            if not archive['matchingMembers'] or any(hashlib.sha256(source.read(name)).hexdigest() != identity['sha256']
                    for name in archive['matchingMembers']):
                raise SupplementError('Selected source differs from its retained archive member')
    texts, sha, _ = source_blocks(str(path.resolve()))
    if sha != identity['sha256']:
        raise SupplementError('Cached classification source differs from its bytes')
    for item in evidence:
        loc = re.fullmatch(r'word/document.xml accepted body blocks \[(\d+),(\d+)\)', item['locator'])
        if not loc or int(loc[2]) != int(loc[1]) + 1 or texts[int(loc[1])] != item['quote']:
            raise SupplementError('Classification cover locator/quote changed: ' + row['target'])
    header_end = min(int(re.search(r'\[(\d+),', e['locator'])[1]) for e in evidence
                     if '| CR |' in e['quote'])
    source_header = '\n'.join(texts[:header_end])
    own = re.search(r'(?<![\w-])' + re.escape(row['target']).replace(r'\-', r'\s*-\s*') + r'(?![\w-])', source_header)
    wg = re.fullmatch(r'R([1-5])-\d{6,8}', row['target'])
    source_wg = re.search(r'(?:RAN\s*(?:WG|Working Group)?|TSG[ -]WG)\s*([1-5])\b', source_header, re.I)
    if not own or not wg or (source_wg and wg[1] != source_wg[1]):
        raise SupplementError('Classification source does not identify its own WG document')
    cover = '\n'.join(e['quote'] for e in evidence)
    headers = list(re.finditer(r'\|\s*(?:TS\s*)?(\d{2}\.\d{3}(?:-\d+)?)\s*\|\s*CR\s*\|\s*(\d+)\s*\|\s*rev\s*\|\s*([^|]*)\|\s*Current version:', cover, re.I))
    if len(headers) != 1 or int(headers[0][2]) == 0:
        raise SupplementError('Classification needs one assigned numeric CR identity')
    spec, number, revision = headers[0].groups()
    revision = revision.strip()
    if revision not in ('', '-', '0') and not revision.isdigit():
        raise SupplementError('Classification CR revision is not numeric')
    revision = revision if revision not in ('', '-') else '0'
    title = re.search(r'\|\s*Title:\s*\|\s*([^|]+)\|', cover, re.I)
    release = re.search(r'Release:\s*\|\s*<?\s*(Rel-\d+)\b', cover, re.I)
    category = re.search(r'Category:\s*\|\s*([A-F])\b', cover, re.I)
    report = row['reportEntry']
    if canonical_meeting(report['meeting']) != canonical_meeting(row['meetingId']):
        raise SupplementError('Classification report is outside its selected meeting')
    rp = checked_path(root, report['path'], report['sourceSHA256'])
    rt, rsha, _ = source_blocks(str(rp.resolve()))
    start, end = report['startBlock'], report['endBlockExclusive']
    if (rsha != report['sourceSHA256'] or start < 0 or end > len(rt)
            or [e['block'] for e in report['entry']] != list(range(start, end))
            or any(rt[e['block']] != e['text'] for e in report['entry'])):
        raise SupplementError('Classification complete report entry changed')
    header = re.match(r'^' + re.escape(row['target']) + r'\s+([^\n]+)', rt[start])
    entry = '\n'.join(rt[start:end])
    descriptor = re.search(r'(\d{2}\.\d{3}(?:-\d+)?)(?:\s+v\d+\.\d+\.\d+)?\s+CR-?\s*(\d+)(?:\s+rev\s*(\d*))?(?:\s+Cat:\s*([A-F-]))?\s*\((Rel-\d+)\)', entry)
    def title_words(value):
        return re.sub(r'[^a-z0-9]', '', value.casefold())
    formal_types = re.findall(r'^\s*Type:\s*(\S+)', entry, re.M)
    title_agrees = bool(header and title and title_words(header[1]) == title_words(title[1]))
    adjudicated = False
    if assessment := row.get('identityAdjudication'):
        proof_path = checked_path(root, assessment['path'], assessment['sha256'])
        proof = json.loads(proof_path.read_text())
        if 'records' in proof:
            matches = [r for r in proof['records'] if r['target'] == row['target']]
            candidate = matches[0] if len(matches) == 1 else {}
            adjudicated = bool(candidate
                and candidate['review']['sourceDocumentType'] == 'assigned_CR_form'
                and candidate['sourceCover']['path'] == identity['path']
                and candidate['sourceCover']['sha256'] == identity['sha256']
                and candidate['reportEntry']['path'] == report['path']
                and candidate['reportEntry']['sourceSHA256'] == report['sourceSHA256'])
            if native := candidate.get('nativeConversionVerification'):
                adjudicated = bool(adjudicated and native['allAcceptedBodyBlocksEqual']
                    and native['retainedDocxPath'] == identity['path']
                    and native['retainedDocxSha256'] == identity['sha256']
                    and native['acceptedBlocks'] == len(texts)
                    and native['acceptedBodySha256'] == hashlib.sha256(json.dumps(list(texts),
                        ensure_ascii=False, separators=(',', ':')).encode()).hexdigest())
            title_agrees = bool(title_agrees or (adjudicated and header and title
                and row['classificationContract']['titleComparison'] == 'explicit_source_identity_adjudication'))
        else:
            title_agrees = bool(title_agrees or (header and title and row.get('selectedSourceArchive')
            and row['classificationContract']['titleComparison'] == 'explicit_source_identity_adjudication'
            and proof['target'] == row['target']
            and proof['report'] == dict(spec=spec, crNumber=number, revision=revision)
            and any(d['path'] == identity['path'] and d['sha256'] == identity['sha256']
                    and d['revision'] == revision for d in proof['documents'])
            and proof['decisionEvidence']['path'] == report['path']
            and proof['decisionEvidence']['sha256'] == report['sourceSHA256']))
    tuple_agrees = bool(descriptor and descriptor[1] == spec and int(descriptor[2]) == int(number))
    # A self-numbered assigned form remains a CR document when the report's
    # metadata describes a different CR tuple. Only an explicit, byte-bound
    # own-source assessment permits this policy; its literal report facts stay
    # in the ledger and never become the retained body's identity.
    metadata_discrepancy = bool(adjudicated and descriptor
        and row.get('classificationContract', {}).get('reportComparison') == 'retained_own_form_metadata'
        and candidate['review'].get('actualCoverTuple') == dict(spec=spec, crNumber=number, revision=revision)
        and candidate['review'].get('reportTuple') == dict(spec=descriptor[1], crNumber=descriptor[2], revision=descriptor[3] or '0'))
    if (not title_agrees
            or (formal_types and formal_types != ['CR'] and not (adjudicated and formal_types == ['other']))
            or not (tuple_agrees or metadata_discrepancy)):
        raise SupplementError('Classification cover/report CR identity or title differs: ' + row['target'])
    if assessment := row.get('sourceSpecificationAdjudication'):
        proof_path = checked_path(root, assessment['path'], assessment['sha256'])
        proof = json.loads(proof_path.read_text())
        decision = proof['sourceCoverDiscrepancy']
        if (proof['target'] != row['target'] or proof['reportEntry'] != report
                or decision['literalValue'] != spec
                or decision['adjudicatedTargetSpec'] != descriptor[1]
                or not proof['sourceSpecificationEvidence']
                or not any(e['path'] == identity['path'] and e['sha256'] == identity['sha256']
                           for e in proof['actualCRSourceEvidence'])):
            raise SupplementError('Specification adjudication is outside its exact document/report')
        for evidence_item in proof['actualCRSourceEvidence'] + proof['sourceSpecificationEvidence']:
            source_path = checked_path(root, evidence_item['path'], evidence_item['sha256'])
            source_texts, source_sha, _ = source_blocks(str(source_path.resolve()))
            loc = re.fullmatch(r'word/document.xml accepted body blocks \[(\d+),(\d+)\)', evidence_item['locator'])
            if (source_sha != evidence_item['sha256'] or not loc or int(loc[2]) != int(loc[1])+1
                    or source_texts[int(loc[1])] != evidence_item['quote']):
                raise SupplementError('Specification adjudication quote/locator changed')
        spec = decision['adjudicatedTargetSpec']
    actual = {'@type': 'tdoc:CR', 'tdoc:type': 'CR', 'modifies': 'tdoc:spec/' + spec.replace('.', '_'),
              'tdoc:crNumber': number, 'tdoc:crRevision': revision}
    if release and descriptor[5] == release[1]:
        actual['targetRelease'] = 'tdoc:release/' + release[1].replace('-', '_')
    if category and (descriptor[4] == category[1] or adjudicated):
        actual['tdoc:crCategory'] = category[1]
    fields = [d['field'] for d in row['deltas']]
    if len(fields) != len(set(fields)) or not set(actual) - {'targetRelease', 'tdoc:crCategory'} <= set(fields):
        raise SupplementError('Classification delta identity is incomplete/duplicate')
    for delta in row['deltas']:
        if delta['field'] not in actual or actual[delta['field']] != delta['sourceBackedValue']:
            raise SupplementError('Classification field lacks direct cover/report support: ' + row['target'])
    return row


def target_selection(root, wg, path):
    path = path.resolve()
    if not path.is_relative_to(root.resolve()):
        raise SupplementError('Retain the selected-target input inside the repository')
    raw = path.read_bytes(); targets = json.loads(raw)
    if (not isinstance(targets, list) or not targets or any(not isinstance(t, str)
            or not re.fullmatch('R' + wg.removeprefix('RAN') + r'-\d{6,8}', t) for t in targets)
            or len(set(targets)) != len(targets)):
        raise SupplementError('Selected targets require unique own-WG canonical document numbers')
    return tuple(sorted(targets)), {path.relative_to(root).as_posix(): hashlib.sha256(raw).hexdigest()}


def validated_classifications(root, wg, selected_meetings=None, *, selected_targets=None):
    path = ledger_path(root, wg)
    if not path.exists():
        return []
    raw = path.read_bytes()
    ledger = json.loads(raw)
    rows = ledger.get('records')
    if ledger.get('schema') != 1 or ledger.get('wg') != wg or not isinstance(rows, list):
        raise SupplementError('Invalid source classification ledger')
    if len({r['target'] for r in rows}) != len(rows):
        raise SupplementError('Duplicate source classification identity')
    selected = None if selected_meetings is None else {canonical_meeting(m) for m in selected_meetings}
    rows = [r for r in rows if (selected is None or canonical_meeting(r['meetingId']) in selected)
            and (selected_targets is None or r['target'] in selected_targets)]
    # A producer can consume several views of the same ledger. Reuse its parsed
    # accepted Word views only after checking every original byte SHA again.
    sources = {r['coverIdentity']['path']: r['coverIdentity']['sha256'] for r in rows}
    for row in rows:
        p, sha = row['reportEntry']['path'], row['reportEntry']['sourceSHA256']
        if p in sources and sources[p] != sha:
            raise SupplementError('Conflicting classification source SHA')
        sources[p] = sha
        if archive := row.get('selectedSourceArchive'):
            sources[archive['path']] = archive['sha256']
        if assessment := row.get('identityAdjudication'):
            sources[assessment['path']] = assessment['sha256']
        if assessment := row.get('sourceSpecificationAdjudication'):
            sources[assessment['path']] = assessment['sha256']
            proof = json.loads(checked_path(root, assessment['path'], assessment['sha256']).read_text())
            for evidence in proof['actualCRSourceEvidence'] + proof['sourceSpecificationEvidence']:
                sources[evidence['path']] = evidence['sha256']
        for archive in row.get('retainedSourceInventory', []):
            sources[archive['path']] = archive['sha256']
    for relative, sha in sources.items():
        checked_path(root, relative, sha)
    key = (str(root.resolve()), wg, hashlib.sha256(raw).hexdigest(),
           None if selected is None else tuple(sorted(selected)),
           None if selected_targets is None else tuple(sorted(selected_targets)))
    if key not in _VALIDATED:
        _VALIDATED[key] = [validate_classification(root, r) for r in rows]
    return _VALIDATED[key]


def source_inputs(root, wg, selected_meetings, *, selected_targets=None):
    path = ledger_path(root, wg)
    if not path.exists():
        return {}
    result = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()}
    for row in validated_classifications(root, wg, selected_meetings, selected_targets=selected_targets):
        result[row['coverIdentity']['path']] = row['coverIdentity']['sha256']
        result[row['reportEntry']['path']] = row['reportEntry']['sourceSHA256']
        if archive := row.get('selectedSourceArchive'):
            result[archive['path']] = archive['sha256']
        if assessment := row.get('identityAdjudication'):
            result[assessment['path']] = assessment['sha256']
        if assessment := row.get('sourceSpecificationAdjudication'):
            result[assessment['path']] = assessment['sha256']
            proof = json.loads(checked_path(root, assessment['path'], assessment['sha256']).read_text())
            for evidence in proof['actualCRSourceEvidence'] + proof['sourceSpecificationEvidence']:
                result[evidence['path']] = evidence['sha256']
        for archive in row.get('retainedSourceInventory', []):
            checked_path(root, archive['path'], archive['sha256'])
            result[archive['path']] = archive['sha256']
        for variant in row.get('retainedSourceVariants', []):
            old = variant['coverIdentity']
            checked_path(root, old['path'], old['sha256'])
            result[old['path']] = old['sha256']
    verified = {}
    for relative, sha in result.items():
        current = checked_path(root, relative, sha).relative_to(root).as_posix()
        if current in verified:
            raise SupplementError('Ambiguous classification source coordinates: ' + current)
        verified[current] = sha
    helper = root / 'scripts/common/common/review_artifacts.py'
    helper_name = helper.relative_to(root).as_posix()
    if helper_name in verified:
        raise SupplementError('Classification source overlaps its relocation dependency')
    verified[helper_name] = hashlib.sha256(helper.read_bytes()).hexdigest()
    return verified


def apply_source_classifications(root, wg, instances, references, selected_meetings, *, selected_targets=None):
    """Overlay enumerated facts, preserving every other field and document identity."""
    rows = validated_classifications(root, wg, selected_meetings, selected_targets=selected_targets)
    nodes = {n['@id']: n for n in instances}
    endpoints = set(nodes) | {n['@id'] for graph in references.values() for n in graph}
    changed = []
    for row in rows:
        node = nodes.get('tdoc:' + row['target'])
        if node is None:
            raise SupplementError('Selected source classification target is absent: ' + row['target'])
        for delta in row['deltas']:
            field, before, after = delta['field'], delta['before'], delta['sourceBackedValue']
            if field in ('modifies', 'targetRelease') and after not in endpoints:
                raise SupplementError('Classification endpoint is absent: ' + after)
            current = node.get(field)
            if current not in (before, after):
                raise SupplementError('Unreviewed classification preimage: ' + row['target'] + ' ' + field)
            if current != after:
                changed.append({'target': row['target'], 'scope': row['scope'], **delta})
                node[field] = after
    return changed


def legacy_expected_counts(root, wg, legacy):
    result = dict(legacy)
    for row in validated_classifications(root, wg):
        delta = next(d for d in row['deltas'] if d['field'] == '@type')
        before, after = (delta[k].removeprefix('tdoc:') for k in ('before', 'sourceBackedValue'))
        if before != after:
            result[before] -= 1
            result[after] += 1
    if any(v < 0 for v in result.values()):
        raise SupplementError('Source class ledger exceeds the legacy source population')
    return result
