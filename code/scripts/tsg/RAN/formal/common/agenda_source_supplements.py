#!/usr/bin/env python3
"""agenda_source_supplements.py — Source-bound closure for report headings absent from Tdoc-list rows.

Spec: docs/tsg/RAN/formal/RAN1/phase-2/step1_parsing.md.
Ontology: AgendaItem identity (meetingNumber, agendaNumber).
Cycle: immutable accepted report TOC/heading evidence -> Phase-1 reference closure.
배경: an agenda can occur in the meeting report without a Tdoc registered on its parent.
사용: supplement_agenda_items(root, wg, existing, selected_meetings).
LLM 호출: none. Input XLSX, report bytes, and existing records remain unchanged.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from openpyxl import load_workbook
import docx_text
import agenda_number


def ledger_path(root, wg):
    return Path(root) / f'ontology/input/tsg/RAN/formal/meetings/{wg}/agenda_source_supplements.json'


@lru_cache(maxsize=1024)
def _meeting(value):
    label = re.sub(r'^(?:RAN\d[#_]|TSGR\d_)', '', value, flags=re.I)
    # This pure helper shares the maintained canonical/bis identity grammar.
    path = Path(__file__).resolve().parents[1] / 'RAN1/phase-1/jsonld/meeting_id.py'
    spec = importlib.util.spec_from_file_location('_agenda_meeting_identity', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    label = module.canonical_meeting_id(label).lower()
    if not re.fullmatch(r'\d+(?:bis|[a-z])?', label):
        raise ValueError('Invalid source agenda meeting identity')
    return label


def _source_path(root, name, wg, slot, *, promoted=True):
    relative = Path(name)
    prefix = Path(f'ontology/input/tsg/RAN/formal/meetings/{wg}/{slot}')
    if relative.is_absolute() or '..' in relative.parts or (promoted and relative.parent != prefix):
        raise ValueError('Agenda source is outside the promoted meeting inputs')
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root)):
        raise ValueError('Agenda source symlinks are unsupported')
    return path


def _source_meeting(path, wg, slot):
    marker = f'TDoc_List_TSGR{wg[-1]}_' if slot == 'TDoc_List' else f'Final_Report_{wg}-'
    if not path.stem.startswith(marker):
        raise ValueError('Agenda source filename is not a promoted meeting identity')
    return _meeting(path.stem[len(marker):])


def _placement_tools():
    """Load the source readers with the parser's bare module names isolated."""
    directory = Path(__file__).resolve().parents[1] / 'RAN1/phase-2/report-parser'
    names = ('models', 'agenda_matcher', 'toc_parser')
    previous = {name: sys.modules.pop(name) for name in names if name in sys.modules}
    old_path = sys.path[:]
    try:
        sys.path.insert(0, str(directory))
        spec = importlib.util.spec_from_file_location('_source_agenda_receipts', directory / 'reconcile_agendas.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = old_path
        for name in names:
            sys.modules.pop(name, None)
        sys.modules.update(previous)


def _registered_agendas(path, sheet=None):
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = sheet or book.sheetnames[0]
        rows = book[sheet].iter_rows(values_only=True)
        header = next(rows, ())
        columns = [i for i, value in enumerate(header) if str(value).strip() == 'Agenda item']
        if len(columns) != 1:
            raise ValueError('Registered agenda source needs one Agenda item column')
        column = columns[0]
        return sheet, {str(row[column]).strip() for row in rows
                       if len(row) > column and row[column] is not None}
    finally:
        book.close()


def _report_receipts(path, tools):
    sections, paragraphs, toc = tools.source_sections(path, include_toc=True)
    receipts = tools.placement_receipts(sections, paragraphs, toc)
    return [(section, receipts[section['start_index']]) for section in sections]


def _verified(receipt):
    return (receipt['evidenceStatus'] == 'source_verified' and receipt['method'] in
            {'explicit_heading_number', 'exact_toc_title_level_parent_context',
             'exact_child_toc_common_parent_within_source_heading_boundary'})


def _evidence_matches(section, receipt, evidence):
    """Legacy ledgers may omit ancestors; the actual source still fixes the parent."""
    heading = {'paragraphIndex': section['start_index'], 'quote': section['title'], 'role': 'source_heading'}
    if not isinstance(evidence, list) or heading not in evidence:
        return False
    if any(item not in receipt['evidence'] for item in evidence):
        return False
    if receipt['method'] == 'exact_toc_title_level_parent_context':
        return any(item['role'] == 'numbered_table_of_contents_entry' for item in evidence)
    if receipt['method'] == 'exact_child_toc_common_parent_within_source_heading_boundary':
        roles = {'direct_child_heading_binding_parent', 'numbered_child_table_of_contents_entry'}
        children = [item for item in receipt['evidence'] if item['role'] in roles]
        return {item['role'] for item in children} == roles and all(item in evidence for item in children)
    return True


def _rule_paths():
    formal = Path(__file__).resolve().parents[1]
    return {Path(__file__), Path(docx_text.__file__), Path(agenda_number.__file__),
            Path(docx_text.symbol_fonts.__file__),
            formal / 'RAN1/phase-1/jsonld/meeting_id.py',
            *(formal / 'RAN1/phase-2/report-parser' / name for name in
              ('reconcile_agendas.py', 'agenda_matcher.py', 'toc_parser.py', 'models.py'))}


def validated_records(root, wg, selected_meetings=None, *, document=None):
    root = Path(root)
    path = ledger_path(root, wg)
    if document is None and not path.exists():
        return []
    if document is None:
        document = json.loads(path.read_text())
    if document.get('schemaVersion') != '1.0.0' or document.get('wg') != wg:
        raise ValueError('Invalid source agenda supplement ledger contract')
    selected = {_meeting(m) for m in selected_meetings} if selected_meetings is not None else None
    promoted = 'sourceInputs' in document or 'selectedMeetings' in document
    selected_sources = None
    if 'sourceInputs' in document:
        scope = {_meeting(value) for value in document.get('selectedMeetings',
                    [row['meetingId'] for row in document['records']])}
        selected_sources, current_inputs = _selected_sources(root, wg, scope)
        expected_inputs = document['sourceInputs']
        if set(current_inputs) != set(expected_inputs):
            raise ValueError('Agenda source inputs changed during closure validation')
        if current_inputs != expected_inputs:
            raise ValueError('Agenda source input SHA drift')
    result, seen = [], set()
    tools, reports, masters, registered_unions = None, {}, {}, {}
    for record in document['records']:
        if not record['meetingId'].startswith(wg + '#'):
            raise ValueError('Report agenda record belongs to another working group')
        if selected is not None and _meeting(record['meetingId']) not in selected:
            continue
        number = record['agendaNumber']
        expected = f'tdoc:agenda/{_meeting(record["meetingId"])}-{number}'
        if record['id'] != expected or expected in seen:
            raise ValueError('Duplicate or inconsistent report agenda identity')
        seen.add(expected)
        source = record['source']
        source_path = _source_path(root, source['path'], wg, 'Final_Report', promoted=promoted)
        if promoted and _source_meeting(source_path, wg, 'Final_Report') != _meeting(record['meetingId']):
            raise ValueError('Report agenda source meeting identity mismatch')
        raw = source_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise ValueError('Report agenda source SHA drift')
        if source_path not in reports:
            tools = tools or _placement_tools()
            reports[source_path] = _report_receipts(source_path, tools)
        if not any(section['agenda_number'] == number
                   and section['title'] == record['agendaDescription']
                   and _verified(receipt) and _evidence_matches(section, receipt, record['evidence'])
                   for section, receipt in reports[source_path]):
            raise ValueError('Report agenda TOC, heading, level and parent evidence are not bound')
        master = record['tdocList']
        master_path = _source_path(root, master['path'], wg, 'TDoc_List', promoted=promoted)
        if promoted and _source_meeting(master_path, wg, 'TDoc_List') != _meeting(record['meetingId']):
            raise ValueError('Registered agenda source meeting identity mismatch')
        if hashlib.sha256(master_path.read_bytes()).hexdigest() != master['sha256']:
            raise ValueError('Registered agenda source XLSX SHA drift')
        key = (master_path, master['sheet'])
        if key not in masters:
            masters[key] = _registered_agendas(*key)[1]
        if number in masters[key]:
            raise ValueError('Report agenda supplement is already registered in the source XLSX')
        if selected_sources is not None:
            meeting = _meeting(record['meetingId'])
            if meeting not in registered_unions:
                registered_unions[meeting] = set().union(*(
                    _registered_agendas(path)[1]
                    for path, _ in selected_sources['TDoc_List'][meeting]))
            if number in registered_unions[meeting]:
                raise ValueError('Report agenda supplement is already registered in a selected source XLSX edition')
        result.append(record)
    return result


def _selected_sources(root, wg, selected):
    grouped = {'TDoc_List': {}, 'Final_Report': {}}
    inputs = {}
    for slot, suffixes in [('TDoc_List', {'.xlsx', '.xlsm'}), ('Final_Report', {'.docx'})]:
        directory = root / f'ontology/input/tsg/RAN/formal/meetings/{wg}/{slot}'
        if any(p.is_symlink() for p in (directory, *directory.parents) if p.is_relative_to(root)):
            raise ValueError('Agenda source directory symlinks are unsupported')
        for path in sorted(directory.iterdir() if directory.exists() else []):
            if path.suffix.lower() not in suffixes:
                continue
            meeting = _source_meeting(path, wg, slot)
            if meeting not in selected:
                continue
            relative = path.relative_to(root).as_posix()
            _source_path(root, relative, wg, slot)
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            inputs[relative] = sha
            if slot == 'TDoc_List':
                # A regular and electronic workbook can register documents for
                # the same canonical meeting. Both physical inputs contribute.
                grouped[slot].setdefault(meeting, []).append((path, sha))
            else:
                previous = grouped[slot].get(meeting)
                if previous and previous[1] != sha:
                    raise ValueError('Conflicting promoted agenda sources for one meeting')
                grouped[slot].setdefault(meeting, (path, sha))
    if set(grouped['TDoc_List']) != selected:
        raise ValueError('Selected meeting has no promoted Tdoc-list source')
    return grouped, dict(sorted(inputs.items()))


def _build_source_document(root, wg, selected, grouped, inputs):
    tools = _placement_tools()
    records = {}
    for meeting, (path, sha) in sorted(grouped['Final_Report'].items()):
        masters = grouped['TDoc_List'][meeting]
        master, master_sha = masters[0]
        sheet, _ = _registered_agendas(master)
        registered = set().union(*(_registered_agendas(path)[1] for path, _ in masters))
        for section, receipt in _report_receipts(path, tools):
            number = section['agenda_number']
            if number in registered or not _verified(receipt):
                continue
            identity = f'tdoc:agenda/{meeting}-{number}'
            record = {'id': identity, 'meetingId': f'{wg}#{meeting}', 'agendaNumber': number,
                      'agendaDescription': section['title'],
                      'source': {'path': path.relative_to(root).as_posix(), 'sha256': sha},
                      'evidence': receipt['evidence'],
                      'tdocList': {'path': master.relative_to(root).as_posix(),
                                   'sha256': master_sha, 'sheet': sheet}}
            if identity in records and records[identity]['agendaDescription'] != record['agendaDescription']:
                raise ValueError('Conflicting verified report headings for one agenda identity')
            records.setdefault(identity, record)
    return {'schemaVersion': '1.0.0', 'wg': wg, 'selectedMeetings': sorted(selected),
            'sourceInputs': inputs, 'records': [records[key] for key in sorted(records)]}


def prepare_source_ledger(root, wg, selected_meetings, *, expected_inputs=None, allow_create=True):
    """Create/reuse source-only closure before count sealing without replacing a ledger.

    ``inputs`` contains promoted XLSX/DOCX hashes for comparison with the existing
    promotion receipt. Other WGs retain their existing source contract.
    """
    if wg != 'RAN1':
        return {'ledger': None, 'created': False, 'inputs': {}}
    root = Path(root)
    selected_meetings = tuple(selected_meetings)
    if any(re.match(r'^(?:RAN[2-5][#_]|TSGR[2-5]_)', value, re.I) for value in selected_meetings):
        raise ValueError('Source agenda selection belongs to another working group')
    selected = {_meeting(value) for value in selected_meetings}
    if not selected:
        raise ValueError('Source agenda closure requires an explicit selected meeting scope')
    grouped, inputs = _selected_sources(root, wg, selected)
    if expected_inputs is not None and any(expected_inputs.get(name) != sha for name, sha in inputs.items()):
        raise ValueError('Agenda source is absent or changed in the promotion receipt')
    rules = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in _rule_paths()}
    document = _build_source_document(root, wg, selected, grouped, inputs)
    validated_records(root, wg, document=document)
    path = ledger_path(root, wg)
    if any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root)):
        raise ValueError('Agenda ledger symlinks are unsupported')

    def fence():
        if _selected_sources(root, wg, selected)[1] != inputs:
            raise ValueError('Agenda source inputs changed during closure preparation')
        if any(hashlib.sha256(path.read_bytes()).hexdigest() != sha for path, sha in rules.items()):
            raise ValueError('Agenda source rules changed during closure preparation')

    def reuse():
        raw = path.read_bytes()
        existing = json.loads(raw)
        validated_records(root, wg, document=existing)
        def identities(records):
            return {row['id']: {**{key: row[key] for key in
                    ('id', 'agendaNumber', 'agendaDescription', 'source', 'tdocList')},
                    'meetingId': _meeting(row['meetingId'])} for row in records}
        if (identities(existing['records']) != identities(document['records'])
                or existing.get('selectedMeetings', sorted(selected)) != sorted(selected)
                or existing.get('sourceInputs', inputs) != inputs):
            raise ValueError('Existing agenda source ledger differs; refusing replacement')
        fence()
        if path.read_bytes() != raw:
            raise ValueError('Existing agenda source ledger changed during reuse')
        return {'ledger': path.relative_to(root).as_posix(),
                'sha256': hashlib.sha256(raw).hexdigest(), 'created': False, 'inputs': inputs}

    fence()
    if path.exists():
        return reuse()
    if not allow_create:
        raise ValueError('Source agenda ledger is required before sealing counts')
    fd, temporary = tempfile.mkstemp(prefix='.agenda-source-', dir=path.parent)
    temporary = Path(temporary)
    published = False
    try:
        raw = (json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        fence()
        try:
            os.link(temporary, path)
            published = True
        except FileExistsError:
            return reuse()
        fence()
        if path.is_symlink() or path.read_bytes() != raw:
            raise ValueError('Agenda ledger changed during publication')
        return {'ledger': path.relative_to(root).as_posix(),
                'sha256': hashlib.sha256(raw).hexdigest(), 'created': True, 'inputs': inputs}
    except BaseException:
        try:
            if (published and path.exists()
                    and os.path.samestat(path.lstat(), temporary.lstat())
                    and path.read_bytes() == raw
                    and os.path.samestat(path.lstat(), temporary.lstat())):
                path.unlink()
        except OSError:
            # Preserve the original failure and any unreadable or removed concurrent ledger.
            pass
        raise
    finally:
        temporary.unlink(missing_ok=True)


def supplement_agenda_items(root, wg, existing, selected_meetings=None):
    result = deepcopy(existing)
    existing_ids = {row['@id'] for row in result.values()}
    for record in validated_records(root, wg, selected_meetings):
        if record['id'] in existing_ids:
            continue
        key = (_meeting(record['meetingId']), record['agendaNumber'])
        if key in result:
            raise ValueError('Source agenda composite key collision')
        result[key] = {'@id': record['id'], '@type': 'tdoc:AgendaItem',
                       'tdoc:agendaNumber': record['agendaNumber'],
                       'tdoc:meetingNumber': _meeting(record['meetingId']),
                       'tdoc:agendaDescription': record['agendaDescription']}
        existing_ids.add(record['id'])
    return result


def source_inputs(root, wg, selected_meetings=None):
    root = Path(root)
    path = ledger_path(root, wg)
    if not path.exists():
        return {}
    document = json.loads(path.read_text())
    records = validated_records(root, wg, selected_meetings, document=document)
    paths = {path, *_rule_paths()}
    paths.update(Path(root) / r['source']['path'] for r in records)
    paths.update(Path(root) / r['tdocList']['path'] for r in records)
    selected = {_meeting(m) for m in selected_meetings} if selected_meetings is not None else None
    for name, expected in document.get('sourceInputs', {}).items():
        slot = Path(name).parent.name
        if slot not in {'TDoc_List', 'Final_Report'}:
            raise ValueError('Agenda ledger source input is outside promoted inputs')
        source = _source_path(root, name, wg, slot)
        if selected is None or _source_meeting(source, wg, slot) in selected:
            if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
                raise ValueError('Agenda ledger promoted source SHA drift')
            paths.add(source)
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def legacy_expected_counts(root, wg, legacy):
    """Keep the historical source snapshot and add only validated absent parent IDs."""
    records = validated_records(root, wg)
    if not records:
        return legacy
    result = dict(legacy)
    result['AgendaItem'] += len(records)
    return result
