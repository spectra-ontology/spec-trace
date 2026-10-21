#!/usr/bin/env python3
"""Offline replay of original source authority, full census, native and scoring."""
import sys
if sys.flags.optimize:
    raise SystemExit('Assertions must remain enabled; -O/-OO refused')
sys.dont_write_bytecode = True
import argparse
import encodings.cp437
from collections import Counter
import decimal
import fractions
import gzip
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import stat
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
H = lambda b: hashlib.sha256(b).hexdigest()
C = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
ID = 'RAN4_P1_CQ6-3'
CRITERIA = 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
QUESTION_SHA = 'fff0066e8d73c8a481d36e18e4762b718c75068ff951baef91feb20911abd109'
QUERY_SHA = '12f1bc8faab308b35c2c9a6863e710016120f2346f415ef7a8aedaec6a3d8949'
CANONICAL = 'fd4ae11928d21631419c20e19f089ca75130068fa8cc6816d419735f34c9f422'
OBS = {'local_read_opens': 0, 'private_opens': 0, 'writes': 0,
       'network': 0, 'subprocess': 0, 'SQL': 0}


def audit(event, args):
    if event == 'open':
        path, mode, flags = args
        if isinstance(path, int):
            raise RuntimeError('File descriptor opens refused')
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            OBS['writes'] += 1
            raise RuntimeError('Write refused')
        p = Path(path).resolve()
        if not p.is_relative_to(HERE):
            OBS['private_opens'] += 1
            raise RuntimeError('Host-private open refused')
        OBS['local_read_opens'] += 1
    if event.startswith(('socket.', 'urllib.', 'http.client.')):
        OBS['network'] += 1
        raise RuntimeError('Network refused')
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn')) or event == 'os.system':
        OBS['subprocess'] += 1
        raise RuntimeError('Subprocess refused')
    if event.startswith('sqlite3.'):
        OBS['SQL'] += 1
        raise RuntimeError('SQL refused')
    if event in {'os.remove', 'os.rename', 'os.rmdir', 'os.mkdir', 'os.link', 'os.symlink', 'os.truncate', 'os.chmod'}:
        OBS['writes'] += 1
        raise RuntimeError('Filesystem mutation refused')
    if event in {'os.scandir', 'os.listdir'} and args:
        p = Path(args[0]).resolve()
        if not p.is_relative_to(HERE):
            raise RuntimeError('Host-private directory access refused')


sys.addaudithook(audit)


def read(name):
    return (HERE / name).read_bytes()


def js(name):
    return json.loads(read(name))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, HERE / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def check_pin(name, value):
    raw = read(name)
    assert len(raw) == value['bytes'] and H(raw) == value['sha256'], name


def original_sources():
    source = js('source_membership_diagnostics_v1/five_original_source_reopenings.json')
    assert len(source['cases']) == 5
    total_entries, retained = 0, 0
    W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
    def literal(p, ns):
        return ''.join(e.text or '' if e.tag == ns + 't' else '\t' if e.tag == ns + 'tab' else '\n' if e.tag in (ns + 'br', ns + 'cr') else '' for e in p.iter())
    for case in source['cases']:
        suffix = Path(case['original_member']['name']).suffix
        raw = read('source_membership_diagnostics_v1/original_members/' + case['tdocNumber'] + suffix)
        assert H(raw) == case['original_member']['sha256'] and len(raw) == case['original_member']['bytes']
        actual = []
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for entry in case['XML_entries']:
                xml = z.read(entry['member'])
                assert H(xml) == entry['sha256'] and len(xml) == entry['bytes']
                ns = W if suffix == '.docx' else A
                ps = list(ET.fromstring(xml).iter(ns + 'p'))
                assert len(ps) == entry['paragraphs']
                for i, p in enumerate(ps):
                    row = {'paragraph_index0': i, 'literal_text': literal(p, ns),
                           'paragraph_ET_serialization_sha256': H(ET.tostring(p, encoding='utf-8'))}
                    if suffix == '.pptx':
                        row = {'member': entry['member'], **row}
                    actual.append(row)
                total_entries += 1
        assert len(actual) == case['visible_paragraphs_scanned']
        take = actual[:100] if case['source_role_observation'] == 'positive_own_CR_form' else actual
        assert take == case['retained_paragraphs']
        retained += len(take)
    return {'byte_exact_original_members': 5, 'XML_parts': total_entries,
            'retained_literal_paragraphs': retained}


def memberships():
    matrix = json.loads(gzip.decompress(read('source_membership_diagnostics_v1/full167442_exact_identity_memberships.json.gz')))
    assert matrix['columns'] == ['node_id', 'is_Tdoc', 'is_CR', 'tdocNumber', 'type', 'id', 'title']
    rs = matrix['rows']
    assert len(rs) == len({r[0] for r in rs})
    assert all(type(r[0]) is int and type(r[1]) is int and r[1] in (0, 1) and type(r[2]) is int and r[2] in (0, 1) and (r[1] or r[2]) for r in rs)
    assert [r[0] for r in rs] == sorted(r[0] for r in rs)
    assert all(type(r[3]) is str for r in rs)
    for col in (1, 2):
        assert sum(r[col] for r in rs) == len({r[3] for r in rs if r[col]})
    types = {'CR', 'draftCR', 'pCR'}
    counts = {
        'explicit_Tdoc_nodes': sum(r[1] for r in rs), 'explicit_CR_nodes': sum(r[2] for r in rs),
        'Tdoc_CR_intersection': sum(r[1] and r[2] for r in rs),
        'CR_without_explicit_Tdoc': sum(r[2] and not r[1] for r in rs),
        'Tdoc_OR_CR_subclass_union': len(rs),
        'Tdoc_Type_CR_set': sum(r[1] and r[4] in types for r in rs),
        'Tdoc_CR_label_OR_Type_CR_set': sum(r[1] and (r[2] or r[4] in types) for r in rs),
        'Tdoc_exact_distinct_IDs': len({r[3] for r in rs if r[1]}),
        'Tdoc_trimmed_distinct_IDs_DIAGNOSTIC_ONLY': len({r[3].strip() for r in rs if r[1]}),
        'Tdoc_Type_CR_trimmed_IDs_DIAGNOSTIC_ONLY': len({r[3].strip() for r in rs if r[1] and r[4] in types}),
        'Tdoc_no_id': sum(r[1] and r[5] is None for r in rs),
        'Tdoc_no_id_Type_CR_set': sum(r[1] and r[5] is None and r[4] in types for r in rs)}
    assert counts == js('source_membership_diagnostics_v1/receipt.json')['counts']
    assert counts == js('source_membership_diagnostics_v1/full_frozen_population_diagnostics.json')['counts']
    return counts


def native_and_SQL(task, counts):
    base = 'native_preparation_v1/'
    capture = base + 'ROOT_actual_native_capture_v1/'
    q = task['reference_query']
    meta = js(capture + 'reference_outputs/' + ID + '/' + QUERY_SHA + '.json')
    raw = read(capture + 'reference_outputs/' + ID + '/' + QUERY_SHA + '.jsonl')
    positional = [json.loads(line) for line in raw.splitlines()]
    assert meta['id'] == ID and meta['wg'] == 'RAN4'
    assert meta['query'].encode() == q.encode() and meta['query_sha256'] == H(q.encode()) == QUERY_SHA
    assert meta['status'] == 'OK' and meta['columns'] == ['total', 'crs']
    assert meta['truncated'] is False and meta['rollback_completed'] is True
    assert meta['plan_query_type'] == meta['execution_query_type'] == 'r'
    assert meta['execution_summary_complete'] is True and meta['full_rows_available'] is True
    assert meta['limits']['timeout_s'] == 20 and meta['rows_retained'] == 1
    assert meta['rows_sha256'] == H(raw) and meta['bytes_retained'] == len(raw)
    assert len(positional) == 1 and len(positional[0]) == 2 and all(type(v) is int for v in positional[0])
    rows = [dict(zip(meta['columns'], positional[0]))]
    assert rows == [{'total': counts['explicit_Tdoc_nodes'], 'crs': counts['explicit_CR_nodes']}]
    assert rows == js('actual_immutable_SQL_original_census_v2.json')['rows']
    root = js('actual_ROOT_fresh_original_census_SQL_authority_review_v2.json')
    assert rows == root['SQL']['rows']
    assert root['SQL']['duplicate_node_label_pairs'] == 0
    assert root['SQL']['CR_without_explicit_Tdoc'] == counts['CR_without_explicit_Tdoc']
    execution = js(capture + 'execution_RAN4.json')
    assert execution['inventory_unchanged'] is True and execution['source_before'] == execution['source_after']
    assert execution['source_before']['wg'] == 'RAN4'
    assert execution['source_before']['source']['sha256'] == '90c6bf7d4420949b7395e8a0b5700a07f8866ddd461699d4516fe4e4f5deec5d'
    assert execution['items'] == [{'id': ID, 'status': 'OK', 'query_sha256': QUERY_SHA, 'rows': 1}]
    assert execution['input_sha256'] == H(read(base + 'requested_repaired_native_input.jsonl'))
    inp = [json.loads(line) for line in read(base + 'requested_repaired_native_input.jsonl').splitlines()]
    assert len(inp) == 1 and inp[0]['wg'] == 'RAN4' and inp[0]['candidate_query'].encode() == q.encode()
    assert inp[0]['query_sha256'] == QUERY_SHA
    guard = js(base + 'ROOT_actual_guarded_persistent_cim_execute_RAN4/receipt.json')
    assert guard['status'] == 'PASS' and guard['stage'] == 'execute_RAN4'
    assert guard['child_started'] is True and guard['child_exit'] == 0 and guard['failure'] is None
    assert guard['prestart_available_minimum_bytes'] == 26 * 1024**3
    assert guard['continuous_reserve_minimum_bytes'] == 16 * 1024**3
    assert min(guard['initial_memory'].values()) >= 26 * 1024**3
    assert all(min(r['Linux_available_bytes'], r['Windows_available_bytes']) >= 16 * 1024**3 for r in guard['memory_samples'])
    assert guard['owned_cleanup']['owned_stopped'] is True and guard['owned_cleanup']['common_lock_held'] is True
    assert guard['owned_cleanup']['container'] == 'kdd-db-frozen-v1-ran4' and guard['quality_rerolls'] == 0
    assert guard['scope_sha256'] == H(read(base + 'definition.json')) == H(read('definition_original_census_frozen_v2.json'))
    assert guard['wrapper_sha256'] == H(read(base + 'ROOT_outer_native_reserve_guard.py'))
    protocol = js(capture + 'execution_protocol.json')
    assert protocol['container_memory_bytes'] == 2 * 1024**3 and protocol['container_cpu_cores'] == 1 and protocol['query_timeout_seconds'] == 20
    assert protocol['model_calls'] == 0 and execution['model_calls'] == 0
    failure = js(base + 'actual_ROOT_initial_preexecution_inspector_field_lookup_failure.json')
    assert failure['actual_native_rerun'] is False
    return rows


def main():
    manifest = js('manifest.json')
    selfhash = manifest.pop('self_sha256')
    assert H(C(manifest)) == selfhash
    files = manifest['files']
    names = [r['path'] for r in files]
    assert len(names) == len(set(names)) and 'manifest.json' not in names and 'verify.py' in names
    actual = []
    for p in HERE.rglob('*'):
        mode = p.lstat().st_mode
        assert not stat.S_ISLNK(mode), 'Symlinks refused'
        assert stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'Special files refused'
        if stat.S_ISREG(mode):
            actual.append(str(p.relative_to(HERE)))
    assert sorted(actual) == sorted(names + ['manifest.json']), 'Closed inventory mismatch'
    for row in files:
        name = row['path']
        assert name and not Path(name).is_absolute() and '..' not in Path(name).parts
        check_pin(name, row)
    task = js('repair_original_census_v2.json')
    assert task['id'] == ID and H(C(task)) == CANONICAL
    assert H(task['question_en'].encode()) == QUESTION_SHA
    assert task['original_query'].encode() == task['reference_query'].encode() == read('reference_original_census_v2.cypher')
    assert H(read('reference_original_census_v2.cypher')) == QUERY_SHA
    assert H(read('authority/criteria.json')) == CRITERIA
    criteria = js('authority/criteria.json')
    spans = js('original_operational_authority_spans_v2.json')
    lines = read('authority/original_preserved_Phase1_INDEX.md').decode().splitlines(keepends=True)
    check_pin('authority/original_preserved_Phase1_INDEX.md', spans['source'])
    for row in spans['spans']:
        text = ''.join(lines[row['first_line']-1:row['last_line']])
        assert text == row['text'] and H(text.encode()) == row['sha256']
    primary = js('canonical_primary_original_census_review_v2.json')
    secondary = js('ROOT_canonical_secondary_exact_seven_original_census_v2.json')
    review = load_module('review_schema', 'scoring/review_schema.py')
    for r in (primary, secondary):
        review.check_pass(r, task['question_en'], criteria['semantic_units'], criteria_sha=CRITERIA, identity_key='repair_sha256', identity_sha=CANONICAL)
    assert primary['reviewer'] != secondary['reviewer']
    assert primary['human_expert_n'] == secondary['human_expert_n'] == 0
    for p in secondary['native_proofs']:
        check_pin(p['path'], p)
    counts = memberships()
    rows = native_and_SQL(task, counts)
    source = original_sources()
    load_module('scorer', 'scoring/scorer.py')
    load_module('original_scorer', 'scoring/original_scorer.py')
    load_module('contract_checks', 'scoring/contract_checks.py')
    runner = load_module('original_census_controls', 'original_census_controls_v2.py')
    controls = runner.controls(task, rows, counts)
    saved = js('actual_original_census_requested_field_controls_v2.json')
    assert controls == saved['controls'] and len(controls) == saved['control_count']
    assert all(OBS[k] == 0 for k in ('private_opens', 'writes', 'network', 'subprocess', 'SQL'))
    print(json.dumps({'status': 'PASS_PORTABLE_ORIGINAL_CENSUS_SOURCE_NATIVE_SQL_AND_TYPED_CONTROLS',
        'id': ID, 'ROOT_seal': False, 'manifest_self_sha256': selfhash,
        'closed_payload_files': len(files), 'authority_spans': len(spans['spans']),
        'independent_AI_reviews': 2, 'human_expert_n': 0, 'native_queries': 1,
        'native_full_columns': ['total', 'crs'], 'native_rows': rows,
        'requested_fields': ['crs'], 'typed_controls': len(controls),
        'complete_frozen_memberships': counts['Tdoc_OR_CR_subclass_union'],
        'source': source, 'audit': OBS, 'new_API_calls': 0, 'new_native': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
