#!/usr/bin/env python3
"""tdoc_source_supplements.py — recover source-identified documents absent from XLSX.

Spec: Phase-1 Tdoc ontology Step 7 §6.9–6.11; source identity/count contract.
Ontology: primary CR class inherits Tdoc; source-backed Company/Meeting/Spec/Release/WI references.
Cycle: retained source ledger → exact source verification → selected-meeting supplement.
배경: a final CR may be distributed after the spreadsheet snapshot used by Phase-1.
사용: validated_records(root, wg, selected_meetings); supplement_instances(...).
LLM 호출: none. Reads retained local source bytes; no network or database writes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'common'))
from common import axis, review_artifacts


class SupplementError(ValueError):
    pass


def normalized(value):
    return ' '.join(str(value).split())


def canonical_meeting(value):
    return re.sub(r'-e$', '', value)


def ledger_path(root: Path, wg: str) -> Path:
    sys.path.insert(0, str(root / 'scripts/common/common'))
    import axis
    return axis.tree_path('ontology_input', wg=wg, doc_type='meetings', root=root) / 'tdoc_source_supplements.json'


def checked_path(root, relative, sha):
    if (not isinstance(relative, str) or not relative or '\\' in relative or '\x00' in relative
            or any(part in {'', '.', '..'} for part in relative.split('/'))):
        raise SupplementError('Supplement source must have a canonical repository-relative path')
    path = root / relative
    if Path(relative).is_absolute() or not path.resolve().is_relative_to(root.resolve()):
        raise SupplementError('Supplement source escapes the repository: ' + relative)
    review_roots = (review_artifacts.LEGACY_REVIEW_ROOT, review_artifacts.REVIEW_ROOT, *(
        axis.tree_path('logs_common', wg=wg, root=Path('.')) / 'verification/ontology-system-review'
        for wg in axis.WG_REGISTRY))
    if any(Path(relative).is_relative_to(base) for base in review_roots):
        try:
            return review_artifacts.resolve_recorded_path(root, relative, sha)
        except (OSError, ValueError, TypeError) as exc:
            raise SupplementError('Supplement retained review source is not bound: ' + relative) from exc
    if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
        raise SupplementError('Supplement source SHA changed: ' + relative)
    return path


def read_ledger(root, wg):
    path = ledger_path(root, wg)
    if not path.exists():
        return None
    ledger = json.loads(path.read_text())
    rows = ledger.get('records')
    if ledger.get('schema') != 1 or ledger.get('wg') != wg or not isinstance(rows, list):
        raise SupplementError('Invalid source supplement ledger: ' + str(path))
    ids = [r.get('target') for r in rows]
    own_number = 'R' + wg.removeprefix('RAN') + r'-\d{6,8}'
    if len(ids) != len(set(ids)) or any(not re.fullmatch(own_number, x or '') for x in ids):
        raise SupplementError('Invalid or duplicate supplement document identities')
    return ledger


def validate_record(root, row):
    if row.get('kind') == 'document':
        from tdoc_document_supplements import validate_document
        return validate_document(root, row)
    # Use the same accepted Word view as the maintained disposition producer.
    import cr_form
    from docx import Document
    from decision_disposition import source_blocks
    path = checked_path(root, row['path'], row['sha256'])
    for source in row['meetingSourceFiles']:
        checked_path(root, source['path'], source['sha256'])
    texts, sha, _ = source_blocks(str(path.resolve()))
    if sha != row['sha256']:
        raise SupplementError('Cached source view does not match its bytes')
    for block in row['coverBlocks']:
        if texts[block['block']] != block['text']:
            raise SupplementError('Accepted CR cover evidence changed: ' + row['target'])
    identity = row['sourceIdentity']
    header = re.fullmatch(r'\s*3GPP\s+TSG-RAN([1-5])\s+Meeting\s+#(\d+(?:-e)?)\s+(R[1-5]-\d{6,8})\s*', texts[0], re.I)
    if not header:
        raise SupplementError('Unsupported CR source cover header: ' + row['target'])
    actual = {'tdocNumber': header[3], 'meetingNumber': f'RAN{header[1]}#{header[2]}'}
    document = Document(path)
    fields = cr_form.form_fields(document)
    actual['specNumber'] = cr_form.header_spec(document)
    for source, target in {'cr_number': 'crNumber', 'rev': 'crRevision', 'title': 'title',
                           'source': 'sourceToWG', 'work_item': 'workItem', 'category': 'category'}.items():
        actual[target] = fields.get(source)
    cover = '\n'.join(texts[b['block']] for b in row['coverBlocks'])
    for key, pattern in {'currentVersion': r'Current version:\s*\|\s*(\d+\.\d+\.\d+)',
                         'release': r'Release:\s*\|\s*(Rel-\d+)\b'}.items():
        match = re.search(pattern, cover, re.I)
        actual[key] = match[1] if match else None
    if any(normalized(actual.get(key)) != normalized(identity.get(key)) for key in actual):
        raise SupplementError('CR cover metadata differs from the source ledger: ' + row['target'])
    if actual['tdocNumber'] != row['target'] or canonical_meeting(actual['meetingNumber']) != identity['canonicalMeetingNumber']:
        raise SupplementError('CR cover identity differs from its document/meeting key')
    report = row['report']
    report_path = checked_path(root, report['path'], report['sourceSHA256'])
    report_texts, report_sha, _ = source_blocks(str(report_path.resolve()))
    if report_sha != report['sourceSHA256']:
        raise SupplementError('Cached report view does not match its bytes')
    start, end = report['startBlock'], report['endBlockExclusive']
    if [e['block'] for e in report['entry']] != list(range(start, end)):
        raise SupplementError('Report evidence is not its complete declared entry span')
    if any(report_texts[e['block']] != e['text'] for e in report['entry']):
        raise SupplementError('Accepted report entry evidence changed')
    header_match = re.match(r'^\s*(R[1-5]-\d{6,8})\s+(.+)$', report_texts[start], re.S)
    entry = '\n'.join(report_texts[start:end])
    descriptor = re.search(r'(?P<spec>\d{2}\.\d{3}(?:-\d+)?)\s+v(?P<version>\d+\.\d+\.\d+)\s+CR-?(?P<cr>\d+)\s+rev\s+(?P<rev>\d+)\s+Cat:\s*(?P<cat>[A-F])\s*\((?P<release>Rel-\d+)\)', entry)
    expected_descriptor = [identity[k] for k in ('specNumber', 'currentVersion', 'crNumber', 'crRevision', 'category', 'release')]
    if (not header_match or header_match[1] != row['target']
            or normalized(header_match[2]) != normalized(report['title'])
            or report['target'] != row['target'] or report['documentType'] != 'CR'
            or canonical_meeting(report['meeting']) != identity['canonicalMeetingNumber']
            or not re.search(r'\bType:\s*CR\b', entry) or not re.search(r'\bFor:\s*Agreement\b', entry)
            or not descriptor or list(descriptor.groups()) != expected_descriptor):
        raise SupplementError('Report entry and own CR cover do not identify the same CR revision')
    prior = re.findall(r'\(Replaces\s+(R[1-5]-\d{6,8})\)', entry)
    if prior != identity['isRevisionOf']:
        raise SupplementError('Revision link lacks direct report source support')
    decision_blocks = [i for i in range(start, end) if re.match(r'^\s*Decision:', report_texts[i])]
    if decision_blocks != [e['block'] for e in report['documentDecisions']]:
        raise SupplementError('Report disposition evidence omits a Decision within its entry')
    decisions = [normalized(report_texts[i]) for i in decision_blocks]
    match = re.fullmatch(r'Decision: The document was (agreed|revised to (R[1-5]-\d{6,8}))\.', decisions[0]) if len(decisions) == 1 else None
    status = ('revised' if match[2] else 'agreed') if match else None
    if status != report['sourceDocumentDisposition']:
        raise SupplementError('Unsupported or ambiguous source disposition; review the source entry')
    return row


def validated_records(root: Path, wg: str, selected_meetings: set[str] | None = None) -> list[dict]:
    ledger = read_ledger(root, wg)
    if ledger is None:
        return []
    selected = None if selected_meetings is None else {canonical_meeting(m) for m in selected_meetings}
    rows = [r for r in ledger['records'] if selected is None or r['sourceIdentity']['canonicalMeetingNumber'] in selected]
    return [validate_record(root, row) for row in rows]


def source_inputs(root, wg, selected_meetings):
    """Source count contracts bind the ledger and each selected original source SHA."""
    path = ledger_path(root, wg)
    if not path.exists():
        return {}
    result = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()}
    for row in validated_records(root, wg, selected_meetings):
        sources = [(row['path'], row['sha256']), (row['report']['path'], row['report']['sourceSHA256'])] + [
                (r['path'], r['sha256']) for r in row['meetingSourceFiles']]
        if row.get('nativeView'):
            sources.append((row['nativeView']['path'], row['nativeView']['sha256']))
        for relative, sha in sources:
            if relative in result and result[relative] != sha:
                raise SupplementError('Conflicting supplement source SHAs')
            result[relative] = sha
    return result


def reference_graphs(directory):
    return {name: json.loads((directory / (name + '.jsonld')).read_text())['@graph']
            for name in ('companies', 'meetings', 'specs', 'releases', 'work_items')}


def supplement_instances(root, wg, instances, references, selected_meetings):
    """Materialize exact supported fields; keep every existing node and unrelated field."""
    rows = validated_records(root, wg, selected_meetings)
    existing = {node['@id']: node for node in instances}
    def resolve(group, predicate, value, aliases=False):
        targets = [r['@id'] for r in references[group]
                   if normalized(value).casefold() in {normalized(v).casefold() for v in
                      [r.get(predicate, '')] + (r.get('tdoc:aliases', []) if aliases else [])}]
        if len(set(targets)) != 1:
            raise SupplementError(f'Source endpoint is missing/ambiguous: {group} {value}')
        return targets[0]
    result = []
    for row in rows:
        if row.get('kind') == 'document':
            from tdoc_document_supplements import document_instance
            node = document_instance(row, references, resolve)
            if node['@id'] in existing:
                if any(existing[node['@id']].get(k) != v for k, v in node.items()):
                    raise SupplementError('Existing canonical document conflicts with native source: ' + row['target'])
            else:
                result.append(node)
            continue
        i = row['sourceIdentity']
        node = {'@id': 'tdoc:' + row['target'], '@type': 'tdoc:CR',
                'tdoc:tdocNumber': row['target'], 'tdoc:title': i['title'], 'tdoc:type': 'CR',
                'tdoc:status': row['report']['sourceDocumentDisposition'], 'tdoc:for': 'Agreement', 'tdoc:crNumber': i['crNumber'],
                'tdoc:crRevision': i['crRevision'], 'tdoc:crCategory': i['category'],
                'submittedBy': [resolve('companies', 'tdoc:companyName', i['sourceToWG'], True)],
                'presentedAt': resolve('meetings', 'tdoc:meetingNumber', i['meetingNumber']),
                'modifies': resolve('specs', 'tdoc:specNumber', i['specNumber']),
                'targetRelease': resolve('releases', 'tdoc:releaseName', i['release']),
                'relatedTo': [resolve('work_items', 'tdoc:workItemCode', i['workItem'])]}
        if len(i['isRevisionOf']) != 1 or 'tdoc:' + i['isRevisionOf'][0] not in existing:
            raise SupplementError('Directly identified previous revision is outside the selected source population')
        node['isRevisionOf'] = 'tdoc:' + i['isRevisionOf'][0]
        if node['tdoc:status'] == 'revised':
            decision = row['report']['documentDecisions'][0]['text']
            target = 'tdoc:' + re.search(r'revised to (R[1-5]-\d{6,8})', decision)[1]
            if target not in existing:
                raise SupplementError('Explicit revision output is outside the selected source population')
            node['revisedTo'] = target
        if node['@id'] in existing:
            if any(existing[node['@id']].get(k) != v for k, v in node.items()):
                raise SupplementError('Existing canonical document conflicts with source supplement: ' + row['target'])
        else:
            result.append(node)
    return result


def legacy_expected_counts(root, wg, legacy):
    """Keep the spreadsheet snapshot and explicitly add selected source-ledger identities."""
    if not ledger_path(root, wg).exists():
        return legacy
    # Source meeting selection comes from the maintained filename parser, not output JSON-LD.
    import importlib.util
    path = root / f'scripts/tsg/RAN/formal/{wg}/phase-1/jsonld/meeting_id.py'
    spec = importlib.util.spec_from_file_location('_supplement_meeting_id', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    directory = ledger_path(root, wg).parent / 'TDoc_List'
    meetings = {module.extract_meeting_from_filename(p.name) for p in directory.iterdir()
                if p.suffix.lower() in ('.xlsx', '.xlsm')}
    from collections import Counter
    counts = Counter(r.get('canonicalClass', 'CR') for r in validated_records(root, wg, meetings - {None}))
    return {**legacy, **{kind: legacy.get(kind, 0) + count for kind, count in counts.items()}}
