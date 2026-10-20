#!/usr/bin/env python3
"""Bounded read-only audit of original UL switching CQ; never an admission."""
import argparse
import copy
import datetime
import hashlib
import importlib
import json
from pathlib import Path
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'
ID = 'RAN1_P2_CQ1-2'
SOURCE = 'ontology/input/tsg/RAN/formal/meetings/RAN1/Final_Report/Final_Report_RAN1-100-e.docx'
DB = 'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN1.sqlite'
CRITERIA_SHA = 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
SOURCE_SHA = '31eb6f41049493370cce7e7de9689a86ecc4e080583374ff452404d7d50fe1b9'
SQL = '''SELECT a.node_id,a.resolutionId,a.content,a.contentWithEquations,a.note,a.sequence
FROM Agreement a
JOIN edge ea ON ea.src_id=a.node_id AND ea.rel_type='RESOLUTION_BELONGS_TO'
JOIN AgendaItem ai ON ai.node_id=ea.dst_id AND ai.agendaNumber='5.1'
JOIN edge em ON em.src_id=a.node_id AND em.rel_type='MADE_AT'
JOIN Meeting m ON m.node_id=em.dst_id AND m.meetingNumber='RAN1#100'
ORDER BY a.sequence LIMIT 10'''


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pin(p, root=None):
    return {'path': str(p.relative_to(root)) if root else str(p),
            'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size}


def text(e):
    return ''.join(t.text or '' for t in e.findall('.//w:t', NS))


def on(e):
    return e is not None and e.get(W + 'val', '1') not in {'0', 'false', 'off'}


def render(e):
    if e.tag == W + 'tbl':
        return '\n'.join(' | '.join(text(c).strip() for c in row.findall('w:tc', NS))
                         for row in e.findall('w:tr', NS))
    return text(e).strip()


def collect(root, public):
    benchmark = public / 'release_package/cqs/original_core_repair/provenance/original_benchmark.jsonl'
    criteria = public / 'release_package/cqs/original_core_repair/criteria.json'
    original = next(json.loads(s) for s in benchmark.read_text().splitlines() if json.loads(s)['id'] == ID)
    if sha(criteria.read_bytes()) != CRITERIA_SHA:
        raise ValueError('criteria changed')
    p = root / SOURCE
    if sha(p.read_bytes()) != SOURCE_SHA:
        raise ValueError('original source changed')
    with zipfile.ZipFile(p) as z:
        raw = z.read('word/document.xml')
        styles_raw = z.read('word/styles.xml')
        member = z.getinfo('word/document.xml')
    body = list(ET.fromstring(raw).find('w:body', NS))
    def style(e):
        s = e.find('w:pPr/w:pStyle', NS)
        return s.get(W + 'val') if s is not None else None
    lo = next(i for i, e in enumerate(body) if style(e) == 'Heading2' and text(e).strip() == 'RAN1 Aspects for RF requirements for NR frequency range 1 (FR1)')
    hi = next(i for i in range(lo + 1, len(body)) if style(body[i]) in {'Heading1', 'Heading2'})
    if (lo, hi) != (395, 472):
        raise ValueError('source scope changed')
    markers = [i for i in range(lo, hi) if text(body[i]).strip() in {'Agreement:', 'Agreements:'}]
    if markers != [414, 416, 420, 435, 446, 451]:
        raise ValueError('six-group source population changed')
    # Body ordinals count every direct w:body child, including any bookmarks.
    groups = [[415], [417, 418], list(range(421, 426)), [436], list(range(447, 451)), [452, 453]]
    source_records = [{'resolutionId': f'AGR-100-5.1-{j:03d}',
                       'marker_raw_body_child0': markers[j - 1],
                       'content_raw_body_child0': indices,
                       'literal_marked_transcript': '\n'.join(render(body[i]) for i in indices),
                       'scope': 'source-only diagnostic, not native gold'}
                      for j, indices in enumerate(groups, 1)]
    formatting = []
    for i in range(lo, hi):
        for n, run in enumerate(body[i].findall('.//w:r', NS)):
            marked = [x for x in ['strike', 'dstrike', 'vanish'] if on(run.find('w:rPr/w:' + x, NS))]
            if marked:
                formatting.append({'raw_body_child0': i, 'descendant_run0': n,
                                   'text': text(run), 'direct_marks': marked,
                                   'run_xml': ET.tostring(run, encoding='unicode')})
    c = sqlite3.connect((root / DB).resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA query_only=ON')
    version_before = c.execute('PRAGMA data_version').fetchone()[0]
    selected = [dict(x) for x in c.execute(SQL)]
    whole = [dict(x) for x in c.execute(SQL.replace(' LIMIT 10', ''))]
    if len(selected) != 6 or selected != whole or [x['sequence'] for x in whole] != list(range(1, 7)):
        raise ValueError('original exact result population changed')
    agenda_id = 162012
    agenda_nodes = [dict(x) for x in c.execute('''SELECT DISTINCT n.* FROM edge e
        JOIN _node_record n ON n.node_id=e.src_id
        WHERE e.rel_type='RESOLUTION_BELONGS_TO' AND e.dst_id=? ORDER BY n.node_id''', (agenda_id,))]
    selected_ids = [r['node_id'] for r in selected]
    scoped_edges = [dict(x) for x in c.execute('SELECT * FROM edge WHERE src_id IN (' + ','.join('?' for _ in selected_ids + [24008]) + ') ORDER BY edge_id', selected_ids + [24008])]
    target_ids = sorted({x['dst_id'] for x in scoped_edges})
    targets = [dict(x) for x in c.execute('SELECT * FROM _node_record WHERE node_id IN (' + ','.join('?' for _ in target_ids) + ') ORDER BY node_id', target_ids)]
    # A complete actual-property search, not a node-label-only search.
    candidate_sql = '''SELECT node_id,key,value_json FROM node_property
      WHERE (instr(lower(value_json),'1t+1t')>0 AND instr(lower(value_json),'0t+2t')>0)
         OR (instr(lower(value_json),'1 tx on carrier 1')>0 AND instr(lower(value_json),'2tx on carrier 2')>0)
      ORDER BY node_id,key'''
    cases = [dict(x) for x in c.execute(candidate_sql)]
    auxiliary_ids = sorted({x['node_id'] for x in cases} | {489, 61783, 61784, 61785})
    auxiliary_nodes = [dict(x) for x in c.execute('SELECT * FROM _node_record WHERE node_id IN (' + ','.join('?' for _ in auxiliary_ids) + ') ORDER BY node_id', auxiliary_ids)]
    auxiliary_edges = [dict(x) for x in c.execute('SELECT * FROM edge WHERE src_id IN (' + ','.join('?' for _ in auxiliary_ids) + ') ORDER BY edge_id', auxiliary_ids)]
    # Inspect every actual property of the agreement with the omitted table.
    group5 = [dict(x) for x in c.execute('SELECT * FROM node_property WHERE node_id=251 ORDER BY key')]
    # Both alias edges exist; exact named meeting avoids multiplying agreements.
    alias_join = [dict(x) for x in c.execute('''SELECT a.resolutionId,m.meetingNumber
       FROM Agreement a JOIN edge e ON e.src_id=a.node_id AND e.rel_type='MADE_AT'
       JOIN Meeting m ON m.node_id=e.dst_id WHERE a.node_id BETWEEN 247 AND 252
       ORDER BY a.sequence,m.meetingNumber''')]
    after = c.execute('PRAGMA data_version').fetchone()[0]
    c.close()
    if after != version_before:
        raise ValueError('database version changed during readonly audit')
    wa = next(x for x in agenda_nodes if x['node_id'] == 24008)
    wa_props = json.loads(wa['properties_json'])
    checks = {
      'source_scope_raw_children': [lo, hi], 'source_group_markers6': markers,
      'original_SQL_rows6_all_unique_no_limit_truncation': len(selected) == len({x['resolutionId'] for x in selected}) == len(whole) == 6,
      'unfiltered_alias_join_rows12_not12agreements': len(alias_join) == 12,
      'same_event_WA_case_values_retained': '| Case 1 | 1T+1T |' in wa_props['content'] and '| Case 2 | 0T+2T |' in wa_props['content'],
      'same_event_WA_has_distinct_WorkingAssumption_role': json.loads(wa['labels_json']) == ['Resolution', 'WorkingAssumption'],
      'group3_note_retained_in_note_property': selected[2]['note'] is not None and text(body[425]).replace('Note: ', '', 1) == selected[2]['note'],
      'group2_editorial_trailer_1_present': selected[1]['content'].endswith('\n' + text(body[419])),
      'group5_all_properties_no_table': set(x['key'] for x in group5) == {'content', 'hasFFS', 'hasTBD', 'resolutionId', 'sequence'},
      'source_scheduled_direct_strike_frozen_unmarked': any(x['raw_body_child0'] == 423 and x['text'] == 'scheduled' and x['direct_marks'] == ['strike'] for x in formatting) and 'scheduled' in selected[2]['content'],
      'source_scope_OMML0': sum(len(x.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath')) for x in body[lo:hi]) == 0,
      'source_scope_OLE0': sum(len(x.findall('.//w:object', NS)) for x in body[lo:hi]) == 0,
      'source_group6_FFS_retained': text(body[453]) in selected[-1]['content'],
      'source_excluded_workstream01_no_consensus': 'not pursued' in text(body[407]),
      'source_excluded_workstream04_no_consensus': 'no consensus' in text(body[462]),
    }
    if not all(v for k, v in checks.items() if isinstance(v, bool)):
        raise ValueError('bounded source/frozen expectation failed')
    return {
      'id': ID, 'original': original,
      'original_question_sha256': sha(original['question_en'].encode()),
      'original_query_sha256': sha(original['cypher'].encode()),
      'criteria': pin(criteria), 'benchmark': pin(benchmark), 'source': pin(p, root),
      'source_XML': {'member': member.filename, 'CRC': member.CRC, 'bytes': len(raw), 'sha256': sha(raw), 'styles_sha256': sha(styles_raw)},
      'database': {'path': DB, 'access': 'mode=ro&immutable=1/query_only; no native execution', 'bytes': (root / DB).stat().st_size},
      'original_SQL': SQL, 'actual_original_SQL_records': selected, 'actual_original_SQL_whole_records': whole,
      'alias_join': alias_join, 'agenda_all_resolution_nodes': agenda_nodes,
      'scope_edges': scoped_edges, 'scope_edge_targets': targets,
      'all_property_case_candidate_SQL': candidate_sql, 'all_property_case_candidates': cases,
      'auxiliary_nodes': auxiliary_nodes, 'auxiliary_edges': auxiliary_edges,
      'group5_all_properties': group5, 'source_records_not_gold': source_records,
      'source_scope_raw_blocks': [{'raw_body_child0': i, 'kind': body[i].tag.rsplit('}', 1)[-1],
          'text': text(body[i]), 'rendered_with_table_cells': render(body[i]), 'style': style(body[i]),
          'xml_sha256': sha(ET.tostring(body[i], encoding='utf-8'))} for i in range(lo, hi + 1)],
      'source_formatting_direct_markers': formatting, 'checks': checks,
      'scope_limits': ['Source records are not a new frozen gold, native output, or an admission.',
        'Same-event WorkingAssumption numeric case values do not prove that its complete working assumption was agreed.',
        'A direct strike is observed, but active-versus-marked-transcript answer policy is not chosen by this replay.',
        'No information-theoretic absence or global permanent impossibility is inferred from a local omission.']}


def scoring_controls(proof, public):
    core = public / 'release_package/cqs/original_core_repair'
    sys.path.insert(0, str(core))
    kernel = importlib.import_module('original_scorer')
    contract = {'id': ID, 'validation_status': 'pending',
       'required_fields': [{'name': 'content', 'type': 'string', 'nullable': False}],
       'collection': {'kind': 'multiset'}, 'cardinality_policy': {'mode': 'all'}}
    actual = [{'content': r['content']} for r in proof['actual_original_SQL_records']]
    src = [{'content': r['literal_marked_transcript']} for r in proof['source_records_not_gold']]
    controls = []
    def check(name, predicted, expected):
        result = kernel.score(contract, actual, predicted, diagnostic=True)
        if bool(result['exact']) != expected:
            raise ValueError('typed scorer control failed: ' + name)
        controls.append({'name': name, 'expected_exact': expected, 'result': result})
    check('SQL_diagnostic_identity_only_not_semantic_certification', actual, True)
    check('unordered_permutation', list(reversed(actual)), True)
    for i in range(6):
        x = copy.deepcopy(actual);x[i]['content'] += ' WRONG';check('wrong_value_row_' + str(i), x, False)
        x = copy.deepcopy(actual);x[i].pop('content');check('missing_field_row_' + str(i), x, False)
        x = copy.deepcopy(actual);x[i]['content'] = None;check('null_row_' + str(i), x, False)
        x = copy.deepcopy(actual);x[i]['content'] = 1;check('integer_row_' + str(i), x, False)
        check('missing_row_' + str(i), actual[:i] + actual[i+1:], False)
    check('extra_row', actual + [actual[0]], False)
    check('empty', [], False)
    raw_against_source = kernel.score(contract, src, actual, diagnostic=True)
    if raw_against_source['exact'] or raw_against_source['matched_records'] != 3:
        raise ValueError('expected raw content/source diagnostic changed')
    note_repair = copy.deepcopy(actual)
    note_repair[1]['content'] = note_repair[1]['content'].rsplit('\n', 1)[0]
    note_repair[2]['content'] += '\nNote: ' + proof['actual_original_SQL_records'][2]['note']
    repaired = kernel.score(contract, src, note_repair, diagnostic=True)
    if repaired['exact'] or repaired['matched_records'] != 5:
        raise ValueError('expected note/editorial repair frontier changed')
    return {'scope': 'Canonical typed scorer diagnostics, not a semantic gate pass or new reference gold.',
      'contract_not_admitted': contract, 'controls': controls,
      'raw_SQL_content_against_source_marked_transcript_not_gold': raw_against_source,
      'note_plus_editorial_query_repair_diagnostic_not_gold': repaired,
      'canonical_source_pins': [pin(core / name) for name in ['original_scorer.py', 'scorer.py', 'typed_values.py']]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project-root', type=Path, required=True)
    ap.add_argument('--public-root', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    proof = collect(args.project_root.resolve(), args.public_root.resolve())
    controls = scoring_controls(proof, args.public_root.resolve())
    for name, obj in [('actual_source_and_frozen_replay.json', proof), ('actual_canonical_typed_diagnostics.json', controls)]:
        (args.output / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    receipt = {'status': 'BOUNDED_AUDIT_PASS_NOT_ADMISSION', 'id': ID,
       'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'checks': proof['checks'], 'typed_controls_n': len(controls['controls']),
       'files': [pin(args.output / n) for n in ['actual_source_and_frozen_replay.json', 'actual_canonical_typed_diagnostics.json']],
       'native_executions': 0, 'model_calls': 0, 'central_or_public_changes': 0}
    (args.output / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'typed_controls_n': receipt['typed_controls_n'], 'source_groups': 6, 'SQL_records': 6}))


if __name__ == '__main__':
    if sys.flags.optimize:
        raise RuntimeError('optimization unsupported')
    main()
