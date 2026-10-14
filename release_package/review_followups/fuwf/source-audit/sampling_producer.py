#!/usr/bin/env python3
"""Audit sampled original fields against a pinned RDF release without DB access.

The reader is independent of the production DOCX/CR parsers. Its lexical
findings are machine diagnostics, not expert judgments of process semantics.
All writes are confined to an explicitly supplied new audit directory.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import urllib.parse
import zipfile
import xml.etree.ElementTree as ET

import openpyxl

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
BASE = ROOT / 'logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/reviews/fUWF-follow-up/source-audit'
WGS = [f'RAN{i}' for i in range(1, 6)]
RELATIONS = ['MODIFIES_SECTION', 'REFERENCES', 'MADE_AT', 'RESOLUTION_BELONGS_TO', 'SENT_TO']
PREDICATES = dict(zip(RELATIONS, ['modifiesSection', 'references', 'madeAt', 'resolutionBelongsTo', 'sentTo']))
FROZEN = {
    'RAN1': '9540683df5407bb3f8978ad4d05ddc7f7880f10c94f21273f588d737f145e231',
    'RAN2': 'f0997bbfb5fd5844837514cd29cfe943b8cb2d0240f0ea5579c5e69b4e547d6c',
    'RAN3': 'd9791c08773a0e38b89869b3882d3098d879a37ddd7109630c346200d6776e95',
    'RAN4': '90c6bf7d4420949b7395e8a0b5700a07f8866ddd461699d4516fe4e4f5deec5d',
    'RAN5': '1ab414b785a155b58218a209be71ed9d1dacc1ea86ae13abbacfbaea27808f5e',
}
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
TDOC = re.compile(r'\bR[1-5]-\d{6,7}\b', re.I)
DECISION = re.compile(r'^\s*(?:agreements?|conclusions?|working[ -]?assumptions?|work[ -]?assumptions?)\s*[:\-]?\s*', re.I)
HEADING = re.compile(r'^\s*(\d+(?:\.\d+){0,6})\.?\s+\S')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def relpath(path):
    return str(Path(path).relative_to(ROOT))


def norm(text):
    return re.sub(r'\s+', ' ', str(text or '')).strip()


def content_norm(text):
    return norm(DECISION.sub('', norm(text)))


def rank(protocol, wg, relation, direction, identity):
    return hashlib.sha256('\n'.join([protocol['seed'], wg, relation, direction, identity]).encode()).hexdigest()


def choose(protocol, wg, relation, direction, records):
    n = protocol['requested_per_relation_direction_group']
    return sorted(records, key=lambda r: (rank(protocol, wg, relation, direction, r['identity']), r['identity']))[:n]


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def reader():
    path = ROOT / 'release_package/tests/reproduce_scenario_counts.py'
    spec = importlib.util.spec_from_file_location('fuwf_frozen_turtle_reader', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def paragraphs(data):
    """Return original OOXML text with reproducible paragraph/table locations."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        body = ET.fromstring(z.read('word/document.xml')).find(W + 'body')
    rows, table_n, para_n = [], 0, 0
    for bi, element in enumerate(body):
        if element.tag == W + 'p':
            elems = [(element, {'body_index': bi, 'paragraph_index': para_n})]
            para_n += 1
        elif element.tag == W + 'tbl':
            elems = []
            for ri, row in enumerate(element.findall(W + 'tr')):
                for ci, cell in enumerate(row.findall(W + 'tc')):
                    for pi, p in enumerate(cell.findall('.//' + W + 'p')):
                        elems.append((p, {'body_index': bi, 'table_index': table_n, 'row_index': ri, 'cell_index': ci, 'cell_paragraph_index': pi}))
            table_n += 1
        else:
            continue
        for element, loc in elems:
            text = ''.join(t.text or '' for t in element.findall('.//' + W + 't'))
            pstyle = element.find('./' + W + 'pPr/' + W + 'pStyle')
            style = pstyle.get(W + 'val') if pstyle is not None else None
            rows.append({'text': text, 'locator': loc, 'style': style})
    return rows


def meeting_key(value):
    return re.sub(r'[^a-z0-9]', '', str(value).lower()).removeprefix('tsgr').removeprefix('ran')


def report_meeting(path, wg):
    stem = Path(path).stem.removeprefix('Final_Report_')
    return stem.removeprefix(wg + '-')


def report_sources(wg):
    base = ROOT / f'ontology/input/tsg/RAN/formal/meetings/{wg}/Final_Report'
    return sorted(base.glob('*.docx'))


def source_report(path, wg):
    """Authenticate retained DOCX against its original downloaded ZIP member."""
    data = path.read_bytes()
    dh = hashlib.sha256(data).hexdigest()
    meeting = report_meeting(path, wg)
    source = ROOT / f'data/corpus/tsg/RAN/formal/meetings/{wg}/source'
    suffix = meeting_key(meeting)
    candidates = []
    for folder in sorted(source.iterdir()):
        folder_id = re.sub(r'^TSGR[1-5]_?', '', folder.name, flags=re.I)
        if meeting_key(folder_id) != suffix:
            continue
        for archive in sorted((folder / 'Report').rglob('*.zip')):
            try:
                archive_before = digest(archive)
                with zipfile.ZipFile(archive) as z:
                    for name in z.namelist():
                        if not name.lower().endswith('.docx'):
                            continue
                        info = z.getinfo(name)
                        if info.file_size != len(data):
                            continue
                        raw = z.read(name)
                        if hashlib.sha256(raw).hexdigest() == dh:
                            candidates.append({'path': relpath(archive), 'sha256': archive_before, 'sha256_after_member_read': digest(archive), 'member': name, 'member_sha256': dh, 'byte_identical_to_retained_docx': True})
            except (OSError, zipfile.BadZipFile):
                continue
    provenance = {'path': relpath(path), 'sha256': dh, 'original_zip_matches': candidates, 'raw_provenance_status': 'exact_original_zip_member' if candidates else 'original_zip_byte_identity_unavailable', 'meeting_label': meeting}
    return paragraphs(data), provenance


def decision_units(rows, path, wg):
    """Explicit source paragraphs under a labelled decision, without graph gold."""
    units, pending, agenda = [], False, None
    for i, row in enumerate(rows):
        t = norm(row['text'])
        h = HEADING.match(t)
        style = str(row['style'] or '').lower()
        if h and ('heading' in style or 'title' in style):
            agenda = h.group(1)
        marker = DECISION.match(t)
        if marker:
            pending = True
            rest = DECISION.sub('', t).strip()
            if not rest:
                continue
        elif not pending or not t:
            continue
        # One full original paragraph is a prospective source unit. It is not
        # silently promoted to a complete multi-paragraph decision record.
        if 'R1-2001086' not in t:
            units.append({'identity': relpath(path) + '#' + json.dumps(row['locator'], sort_keys=True), 'source_path': relpath(path), 'source_text': row['text'], 'normalized_content': content_norm(row['text']), 'locator': row['locator'], 'source_context': rows[max(0, i - 3):i + 4], 'paragraph_position': i, 'agenda_candidate': agenda, 'meeting_label': report_meeting(path, wg), 'unit_scope': 'complete_original_paragraph_under_explicit_decision_marker'})
        pending = False
    return units


def xlsx_candidates(wg):
    base = ROOT / f'ontology/input/tsg/RAN/formal/meetings/{wg}/TDoc_List'
    records = []
    for path in sorted(base.glob('*.xlsx')):
        try:
            source_read_sha256 = digest(path)
            book = openpyxl.load_workbook(path, read_only=True, data_only=True)
            sheet = book.active
            iterator = sheet.iter_rows(values_only=True)
            headers = next(iterator)
            columns = {str(x).strip(): i for i, x in enumerate(headers) if x is not None}
            def field(row, key):
                i = columns.get(key)
                return row[i] if i is not None and i < len(row) else None
            for ri, row in enumerate(iterator, 2):
                tid, kind, to = field(row, 'TDoc'), field(row, 'Type'), field(row, 'To')
                if tid and 'LS' in str(kind) and norm(to):
                    records.append({'identity': relpath(path) + '#' + sheet.title + '!' + str(ri), 'source_path': relpath(path), 'source_read_sha256': source_read_sha256, 'sheet': sheet.title, 'row': ri, 'tdoc': norm(tid), 'to': str(to), 'type': str(kind), 'title': str(field(row, 'Title') or ''), 'agenda': str(field(row, 'Agenda item') or ''), 'headers': list(columns), 'unit_scope': 'complete_original_To_cell'})
            book.close()
        except Exception as e:
            print('source_frame_xlsx_error', relpath(path), type(e).__name__, flush=True)
    return records


def cr_candidates(wg):
    records = []
    base = ROOT / f'data/corpus/tsg/RAN/formal/change-requests/{wg}/source'
    for release in ['Rel-15', 'Rel-16', 'Rel-17', 'Rel-18', 'Rel-19']:
        for archive in sorted((base / release / 'TSG').glob('*.zip')):
            try:
                with zipfile.ZipFile(archive) as z:
                    for member in z.namelist():
                        m = TDOC.search(member)
                        if not m or not re.search(r'_CR\d+', member, re.I) or not member.lower().endswith(('.doc', '.docx')) or m.group().upper() == 'R1-1803551':
                            continue
                        records.append({'identity': relpath(archive) + '::' + member, 'source_path': relpath(archive), 'member': member, 'tdoc': m.group().upper(), 'release': release, 'unit_scope': 'original_CR_cover_Clauses_affected_field'})
            except (OSError, zipfile.BadZipFile) as e:
                print('source_frame_zip_error', relpath(archive), type(e).__name__, flush=True)
    return records


def source_frames(protocol, wg):
    sources = {r: [] for r in RELATIONS}
    report_cache = {}
    for path in report_sources(wg):
        try:
            # Candidate discovery reads retained DOCX directly. Authentication
            # is deferred until sampled cases; missing native identity remains
            # in the denominator, never a replacement condition.
            data = path.read_bytes()
            rows = paragraphs(data)
            units = decision_units(rows, path, wg)
            for unit in units:
                unit['source_read_sha256'] = hashlib.sha256(data).hexdigest()
                sources['MADE_AT'].append(unit)
                sources['RESOLUTION_BELONGS_TO'].append(unit)
                if TDOC.search(unit['source_text']):
                    sources['REFERENCES'].append(unit)
        except Exception as e:
            print('source_frame_report_error', relpath(path), type(e).__name__, flush=True)
    sources['SENT_TO'] = xlsx_candidates(wg)
    sources['MODIFIES_SECTION'] = cr_candidates(wg)
    return {r: choose(protocol, wg, r, 'source_first', v) for r, v in sources.items()}, {r: len(v) for r, v in sources.items()}


def graph_record(m, subject, types, text):
    return {'identity': subject, 'subject': subject, 'types': sorted(types), 'tdoc': m.literal(text, 'spectra:tdocNumber'), 'content': m.literal(text, 'spectra:content'), 'targets': {r: m.objects(text, 'spectra:' + p) for r, p in PREDICATES.items()}, 'block_sha256': hashlib.sha256(text.encode()).hexdigest()}


def prepare(protocol):
    m = reader()
    cases, counts, frozen, selected_inputs = [], {}, {}, {}
    for wg in WGS:
        print('prepare_source_frame', wg, flush=True)
        src, src_counts = source_frames(protocol, wg)
        ttl = ROOT / f'release_package/kg/per_wg/{wg}-body.ttl'
        before = digest(ttl)
        if before != FROZEN[wg]:
            raise ValueError('Frozen input hash differs: ' + wg)
        frozen[wg] = {'path': relpath(ttl), 'sha256': before, 'bytes': ttl.stat().st_size}
        graph = {r: [] for r in RELATIONS}
        graph_counts = Counter()
        source_resolution_keys = {content_norm(v['source_text']) for r in ['REFERENCES', 'MADE_AT', 'RESOLUTION_BELONGS_TO'] for v in src[r]}
        source_tdocs = {v['tdoc'] for r in ['SENT_TO', 'MODIFIES_SECTION'] for v in src[r]}
        resolution_hits, tdoc_hits = defaultdict(list), defaultdict(list)
        print('prepare_frozen_frame', wg, flush=True)
        for subject, types, text in m.blocks(ttl):
            if not any(t in types for t in ['spectra:Resolution', 'spectra:LS', 'spectra:CR']):
                continue
            rec = graph_record(m, subject, types, text)
            content = rec['content'] or ''
            if rec['tdoc'] == 'R1-1803551' or 'R1-2001086' in content:
                continue
            key = content_norm(content)
            if key in source_resolution_keys:
                resolution_hits[key].append(rec)
            if rec['tdoc'] in source_tdocs:
                tdoc_hits[rec['tdoc']].append(rec)
            for relation in RELATIONS:
                if not rec['targets'][relation]:
                    continue
                graph_counts[relation] += 1
                graph[relation].append(rec)
                if len(graph[relation]) > 20:
                    graph[relation] = choose(protocol, wg, relation, 'graph_first', graph[relation])
        for relation in RELATIONS:
            for rec in choose(protocol, wg, relation, 'graph_first', graph[relation]):
                cases.append({'wg': wg, 'relation': relation, 'direction': 'graph_first', 'sample_identity': rec['identity'], 'graph': rec, 'selection_rank': rank(protocol, wg, relation, 'graph_first', rec['identity'])})
            for rec in src[relation]:
                hits = tdoc_hits.get(rec['tdoc'], []) if 'tdoc' in rec else resolution_hits.get(content_norm(rec['source_text']), [])
                cases.append({'wg': wg, 'relation': relation, 'direction': 'source_first', 'sample_identity': rec['identity'], 'source': rec, 'graph_matches': hits, 'selection_rank': rank(protocol, wg, relation, 'source_first', rec['identity'])})
                path = ROOT / rec['source_path']
                selected_inputs[rec['source_path']] = rec.get('source_read_sha256') or digest(path)
            counts[wg + '/' + relation] = {'source_frame': src_counts[relation], 'graph_frame': graph_counts[relation], 'source_selected': len(src[relation]), 'graph_selected': len(choose(protocol, wg, relation, 'graph_first', graph[relation]))}
    sample = {'protocol_sha256': digest(BASE / 'protocol.json'), 'producer_sha256': digest(Path(__file__)), 'reader_sha256': digest(ROOT / 'release_package/tests/reproduce_scenario_counts.py'), 'frozen': frozen, 'frame_counts': counts, 'requested_n': protocol['requested_total'], 'selected_n': len(cases), 'cases': cases, 'selected_source_input_sha256': selected_inputs, 'selection_before_agreement_labels': True}
    write_new(BASE / 'sampling.json', sample)
    print('sampling_pinned', len(cases), flush=True)
    return sample


def target_tail(iri):
    return urllib.parse.unquote(iri.rsplit('/', 1)[-1]).removeprefix('tdoc:')


def cite_set(text):
    return sorted({x.upper() for x in TDOC.findall(text)})


def citation_tags(text):
    tags = []
    if re.search(r'\b(?:use|used|basis|adopt|agree|approved|accept|endors)', text, re.I):
        tags.append('supportive_lexical_cue')
    if re.search(r'\b(?:discuss|consider|comment|refer|see|from|propos)', text, re.I):
        tags.append('contextual_lexical_cue')
    if TDOC.search(text) and not tags:
        tags.append('mere_citation_or_unclassified')
    return tags


def set_difference(source, graph):
    source, graph = sorted(set(source)), sorted(set(graph))
    return {'source_set': source, 'graph_set': graph, 'source_only': sorted(set(source) - set(graph)), 'graph_only': sorted(set(graph) - set(source)), 'exact_set_equal': source == graph}


def raw_cr(record):
    path = ROOT / record['source_path']
    archive_before = digest(path)
    with zipfile.ZipFile(path) as z:
        data = z.read(record['member'])
    provenance = {'path': record['source_path'], 'sha256': archive_before, 'sha256_after_member_read': digest(path), 'member': record['member'], 'member_sha256': hashlib.sha256(data).hexdigest(), 'raw_provenance_status': 'original_zip_member'}
    if not data.startswith(b'PK'):
        return [], provenance, 'original_legacy_DOC_unreadable_without_conversion'
    try:
        rows = paragraphs(data)
    except Exception as e:
        return [], provenance, 'original_member_DOCX_read_error:' + type(e).__name__
    return rows, provenance, None


def cr_fields(rows):
    found, spec, release = [], None, None
    for i, row in enumerate(rows):
        text = norm(row['text'])
        if re.fullmatch(r'\d{2}\.\d{3}(?:-\d+)?', text) and spec is None:
            spec = text
        if re.fullmatch(r'Rel(?:ease)?[- ]?\d+', text, re.I) and release is None:
            release = 'Rel-' + re.search(r'\d+', text).group()
        if re.search(r'clauses?\s+affected', text, re.I):
            inline = re.split(r'clauses?\s+affected\s*[:：]?', text, flags=re.I)[-1].strip()
            if inline:
                found.append({'text': inline, 'locator': row['locator'], 'label': row['text']})
            elif i + 1 < len(rows):
                found.append({'text': rows[i + 1]['text'], 'locator': rows[i + 1]['locator'], 'label': row['text'], 'label_locator': row['locator']})
    return found, spec, release


def clause_tokens(text):
    # Recognize simple explicit clauses only. Ranges, prose and ambiguous list
    # syntax are retained as unresolved rather than silently expanded/dropped.
    parts = [x.strip() for x in re.split(r'[,;\n]', text) if x.strip()]
    simple = all(re.fullmatch(r'(?:[A-Za-z]\.)?\d+(?:\.\d+)*|[A-Za-z](?:\.\d+)*', p) for p in parts)
    return sorted(set(parts)), simple


def cr_compare(case, all_cr_sources):
    if case['direction'] == 'source_first':
        records = [case['source']]
        matches = case['graph_matches']
    else:
        id_match = TDOC.search(case['graph']['subject'])
        tid = case['graph']['tdoc'] or (id_match.group() if id_match else None)
        records = [x for x in all_cr_sources if x['tdoc'] == tid]
        matches = [case['graph']]
    result = {'graph_identity_count': len(matches), 'source_document_count': len(records), 'comparisons': [], 'status': 'unresolved'}
    if not records:
        result['reason'] = 'original_CR_document_not_found_in_declared_frame'
        return result
    for record in records:
        rows, provenance, error = raw_cr(record)
        part = {'source': provenance, 'source_identity': record['identity']}
        if error:
            part.update(status='unresolved', reason=error)
        else:
            fields, spec, release = cr_fields(rows)
            part.update(fields=fields, spec_number=spec, source_release_literal=release, archive_release=record['release'])
            if len(fields) != 1 or not spec or len(matches) != 1 or not release or release != record['release']:
                part.update(status='unresolved', reason='nonunique_clause_field_spec_graph_subject_or_unbound_release')
            else:
                clauses, simple = clause_tokens(fields[0]['text'])
                source = [f'section/{spec}-{release}-{c}' for c in clauses]
                graph = [target_tail(x) for x in matches[0]['targets']['MODIFIES_SECTION']]
                part['set_comparison'] = set_difference(source, graph)
                part['status'] = ('field_set_match' if part['set_comparison']['exact_set_equal'] else 'field_set_mismatch') if simple else 'unresolved'
                if not simple:
                    part['reason'] = 'complex_clause_syntax_requires_adjudication'
        result['comparisons'].append(part)
    statuses = [x['status'] for x in result['comparisons']]
    if len(records) == 1:
        result['status'] = statuses[0]
    else:
        result['reason'] = 'multiple_original_documents_or_revisions_no_silent_choice'
    return result


def recipients(value):
    normalized = re.sub(r'(?i)\b(?:TSG[- ]?)?(RAN|SA|CT)[- ]*(\d+)?\b', lambda m: m.group(1).upper() + (m.group(2) or ''), value)
    ids = sorted(set(re.findall(r'\b(?:RAN|SA|CT)\d*\b', normalized)))
    residue = re.sub(r'\b(?:RAN|SA|CT)\d*\b|[,;/&\s]|\band\b', '', normalized, flags=re.I)
    return ids, not residue


def ls_compare(case, rows):
    matches = case.get('graph_matches', [case.get('graph')])
    if case['direction'] == 'source_first':
        found = [case['source']]
    else:
        found = [r for r in rows if r['tdoc'] == case['graph']['tdoc']]
    out = {'status': 'unresolved', 'source_occurrences': [], 'graph_identity_count': len(matches)}
    for row in found:
        ids, simple = recipients(row['to'])
        path = ROOT / row['source_path']
        out['source_occurrences'].append({'path': row['source_path'], 'sha256': digest(path), 'sheet': row['sheet'], 'row': row['row'], 'tdoc': row['tdoc'], 'title': row['title'], 'agenda': row['agenda'], 'type': row['type'], 'field': 'To', 'quote': row['to'], 'source_set': ids, 'all_text_resolved': simple, 'raw_provenance_status': 'retained_original_XLSX_cell'})
    source_sets = {tuple(x['source_set']) for x in out['source_occurrences']}
    out['source_target_set'] = list(next(iter(source_sets))) if len(source_sets) == 1 and all(x['all_text_resolved'] for x in out['source_occurrences']) else None
    out['graph_target_set'] = sorted({target_tail(x).removeprefix('wg/') for x in matches[0]['targets']['SENT_TO']}) if len(matches) == 1 else None
    if not found:
        out['reason'] = 'original_LS_row_not_found_in_declared_XLSX_frame'
    elif len(matches) != 1:
        out['reason'] = 'graph_identity_absent_or_nonunique'
    elif not all(x['all_text_resolved'] for x in out['source_occurrences']):
        out['reason'] = 'unrecognized_recipient_text_requires_adjudication'
    else:
        sets = {tuple(x['source_set']) for x in out['source_occurrences']}
        if len(sets) != 1:
            out['reason'] = 'multiple_original_rows_disagree_no_silent_choice'
        else:
            source = next(iter(sets))
            graph = [target_tail(x).removeprefix('wg/') for x in matches[0]['targets']['SENT_TO']]
            out['set_comparison'] = set_difference(source, graph)
            out['status'] = 'field_set_match' if out['set_comparison']['exact_set_equal'] else 'field_set_mismatch'
    return out


def report_text(rows):
    flat, spans = '', []
    for i, row in enumerate(rows):
        t = norm(row['text'])
        if not t:
            continue
        begin = len(flat)
        flat += t + ' '
        spans.append((begin, len(flat) - 1, i))
    return flat, spans


def original_occurrences(content, reports):
    target = content_norm(content)
    occurrences = []
    if not target:
        return occurrences
    for path, payload in reports.items():
        rows, provenance = payload['rows'], payload['provenance']
        flat, spans = payload['flat'], payload['spans']
        start = 0
        while True:
            pos = flat.find(target, start)
            if pos < 0:
                break
            end = pos + len(target)
            selected = [i for a, b, i in spans if b > pos and a < end]
            if not selected:
                break
            quotes = [rows[i] for i in selected]
            joined = ' '.join(norm(r['text']) for r in quotes)
            complete = content_norm(joined) == target
            agenda = None
            for before in rows[:selected[0] + 1]:
                h = HEADING.match(norm(before['text']))
                if h and ('heading' in str(before['style'] or '').lower() or 'title' in str(before['style'] or '').lower()):
                    agenda = h.group(1)
            occurrences.append({'source': provenance, 'quotes': quotes, 'source_context': rows[max(0, selected[0] - 3):selected[-1] + 4], 'full_original_paragraph_span_equal': complete, 'source_reference_ids': cite_set(joined), 'agenda_candidate': agenda, 'machine_citation_tags': citation_tags(joined)})
            start = end
    return occurrences


def resolution_compare(case, reports):
    if case['direction'] == 'source_first':
        matches = case['graph_matches']
        src = case['source']
        report = reports.get(src['source_path'])
        if not report:
            return {'status': 'unresolved', 'reason': 'source_report_unavailable'}
        occurrences = [{'source': report['provenance'], 'quotes': [{'text': src['source_text'], 'locator': src['locator']}], 'source_context': src['source_context'], 'full_original_paragraph_span_equal': True, 'source_reference_ids': cite_set(src['source_text']), 'agenda_candidate': src['agenda_candidate'], 'machine_citation_tags': citation_tags(src['source_text'])}]
    else:
        matches = [case['graph']]
        occurrences = original_occurrences(case['graph']['content'], reports)
    out = {'status': 'unresolved', 'graph_identity_count': len(matches), 'source_occurrences': occurrences, 'semantic_adjudication': 'not_performed; machine_lexical_and_provenance_diagnostic_only'}
    if not occurrences:
        out['reason'] = 'complete_graph_content_not_located_in_retained_source_reports'
        return out
    if len(matches) != 1:
        out['reason'] = 'graph_identity_absent_or_nonunique'
        return out
    native = [o for o in occurrences if o['source']['raw_provenance_status'] == 'exact_original_zip_member']
    if len(native) != len(occurrences):
        out['reason'] = 'original_ZIP_byte_identity_unavailable_for_at_least_one_occurrence'
        return out
    if not all(o['full_original_paragraph_span_equal'] for o in occurrences):
        out['reason'] = 'source_occurrence_is_partial_original_paragraph_span'
        return out
    relation = case['relation']
    if relation == 'REFERENCES':
        sets = {tuple(o['source_reference_ids']) for o in native}
        if len(sets) != 1:
            out['reason'] = 'different_original_occurrences_carry_different_citations'
            return out
        source = next(iter(sets))
        graph = [target_tail(t) for t in matches[0]['targets'][relation]]
        out['set_comparison'] = set_difference(source, graph)
        out['status'] = 'citation_token_set_match' if out['set_comparison']['exact_set_equal'] else 'citation_token_set_mismatch'
        out['semantic_adjudication'] = 'all_reference_meanings_unadjudicated; matching_tokens_are_not_verified_process_relationships'
    elif relation == 'MADE_AT':
        source = {o['source']['meeting_label'] for o in native}
        graph = {target_tail(t).removeprefix('meeting/' + case['wg'] + '_') for t in matches[0]['targets'][relation]}
        out['set_comparison'] = set_difference(source, graph)
        if len(graph) > 1 or len(source) > 1:
            out['reason'] = 'multiple_meeting_identity_or_repeated_source_content_requires_adjudication'
            out['supported_original_occurrences'] = sorted(source & graph)
        else:
            out['status'] = 'provenance_set_match' if out['set_comparison']['exact_set_equal'] else 'provenance_set_mismatch'
    else:
        source = {o['agenda_candidate'] for o in native}
        graph = {target_tail(t).removeprefix('agenda/').split('-', 1)[-1] for t in matches[0]['targets'][relation]}
        if None in source:
            out['reason'] = 'source_heading_does_not_supply_unambiguous_agenda_candidate'
            return out
        out['set_comparison'] = set_difference(source, graph)
        out['status'] = 'heading_candidate_set_match' if out['set_comparison']['exact_set_equal'] else 'heading_candidate_set_mismatch'
        out['semantic_adjudication'] = 'agenda_heading_machine_candidate; inherited_scope_requires_human_review'
    return out


def audit(sample):
    cases, evidence_paths = [], set()
    for wg in WGS:
        print('audit_original_sources', wg, flush=True)
        reports = {}
        for path in report_sources(wg):
            try:
                rows, provenance = source_report(path, wg)
                flat, spans = report_text(rows)
                reports[relpath(path)] = {'rows': rows, 'provenance': provenance, 'flat': flat, 'spans': spans}
            except Exception as e:
                print('report_provenance_error', relpath(path), type(e).__name__, flush=True)
        ls_rows, cr_sources = xlsx_candidates(wg), cr_candidates(wg)
        for case in [c for c in sample['cases'] if c['wg'] == wg]:
            if case['relation'] == 'MODIFIES_SECTION':
                result = cr_compare(case, cr_sources)
            elif case['relation'] == 'SENT_TO':
                result = ls_compare(case, ls_rows)
            else:
                result = resolution_compare(case, reports)
            row = {k: case[k] for k in ['wg', 'relation', 'direction', 'sample_identity', 'selection_rank']}
            row['result'] = result
            comparison = result.get('set_comparison')
            if comparison is None and len(result.get('comparisons', [])) == 1:
                comparison = result['comparisons'][0].get('set_comparison')
            row['source_target_set'] = comparison['source_set'] if comparison else result.get('source_target_set')
            row['graph_target_set'] = comparison['graph_set'] if comparison else result.get('graph_target_set')
            row['available_for_field_set_comparison'] = comparison is not None and result['status'] != 'unresolved'
            row['unresolved'] = result['status'] == 'unresolved'
            row['expected_scope'] = {'MODIFIES_SECTION': 'full original cover Clauses affected field with bound spec and release', 'SENT_TO': 'full original To field, canonical addressed working-group roles', 'REFERENCES': 'citation identifiers in full matched original paragraph span; semantics unadjudicated', 'MADE_AT': 'original report occurrence of matched complete paragraph span; identity ambiguity retained', 'RESOLUTION_BELONGS_TO': 'closest original numbered heading, machine scope candidate'}[case['relation']]
            cases.append(row)
        for payload in reports.values():
            evidence_paths.add(payload['provenance']['path'])
            evidence_paths.update(x['path'] for x in payload['provenance']['original_zip_matches'])
    # Audit-selected source paths are already pinned before labels. Other
    # inspected originals are hashed on read and rehashed below.
    before = dict(sample['selected_source_input_sha256'])
    for row in cases:
        r = row['result']
        for o in r.get('source_occurrences', []):
            if 'source' in o:
                p = o['source']
                before.setdefault(p['path'], p['sha256'])
                for z in p.get('original_zip_matches', []):
                    before.setdefault(z['path'], z['sha256'])
            else:
                before.setdefault(o['path'], o['sha256'])
        for c in r.get('comparisons', []):
            p = c['source']
            before.setdefault(p['path'], p['sha256'])
    drift = []
    for path, sha in sorted(before.items()):
        if digest(ROOT / path) != sha:
            drift.append(path)
    frozen_after = {}
    for wg, pin in sample['frozen'].items():
        frozen_after[wg] = digest(ROOT / pin['path'])
        if frozen_after[wg] != pin['sha256']:
            drift.append(pin['path'])
    summary = defaultdict(Counter)
    for row in cases:
        key = row['relation'] + '/' + row['direction']
        summary[key][row['result']['status']] += 1
        summary[key]['selected_n'] += 1
    result = {'protocol_sha256': sample['protocol_sha256'], 'sampling_sha256': digest(BASE / 'sampling.json'), 'producer_sha256': digest(Path(__file__)), 'requested_n': sample['requested_n'], 'selected_n': len(cases), 'validity': 'INVALID_INPUT_DRIFT' if drift else 'INPUTS_UNCHANGED', 'input_drift_paths': drift, 'inspected_source_sha256': before, 'frozen_after_sha256': frozen_after, 'counts': {k: dict(v) for k, v in summary.items()}, 'cases': cases, 'model_calls': 0, 'database_calls': 0, 'domain_expert_validation_n': 0, 'reference_meanings_adjudicated_n': 0, 'limits': ['Balanced fixed record samples are not a representative corpus estimate.', 'Exact sets refer only to completely read sampled source fields; full-corpus completeness is not established.', 'REFERENCES compares original citation tokens; process meaning is unadjudicated.', 'Original legacy DOC members remain unreadable; no LibreOffice conversion or substitute selection was performed.', 'Multiple meeting targets or repeated source passages retain ambiguity.', 'Source-first absence can reflect source/snapshot scope; it is not automatically a false-negative edge.', 'Named agenda headings are machine candidates, not expert semantic gold.']}
    write_new(BASE / 'results.json', result)
    with (BASE / 'evidence.jsonl').open('x', encoding='utf-8') as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + '\n')
    print(json.dumps({'validity': result['validity'], 'selected_n': len(cases), 'counts': result['counts']}, ensure_ascii=False), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['prepare', 'audit'])
    args = p.parse_args()
    protocol = json.loads((BASE / 'protocol.json').read_text())
    if args.mode == 'prepare':
        prepare(protocol)
    else:
        sample = json.loads((BASE / 'sampling.json').read_text())
        if digest(BASE / 'protocol.json') != sample['protocol_sha256'] or digest(Path(__file__)) != sample['producer_sha256'] or digest(ROOT / 'release_package/tests/reproduce_scenario_counts.py') != sample['reader_sha256']:
            raise ValueError('Protocol, producer or frozen reader changed after sampling')
        audit(sample)


if __name__ == '__main__':
    main()
