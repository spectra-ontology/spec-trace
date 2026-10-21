#!/usr/bin/env python3
"""Replay the frozen RAN3 approved-change metadata trace case without host files, network, or a model call.

This verifies a captured case and its diagnostic controls. It does not decide
question meaning or turn a local check into an independent review/native run.
"""
from __future__ import annotations

import argparse
import collections
import copy
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
if sys.flags.optimize:
    raise SystemExit('Verification requires enabled checks; -O/-OO refused.')
HERE = Path(os.path.abspath(__file__)).parent
INVENTORY_SHA256 = '90a9a7e01f54a8bf2f9606d01193fa71d2b523b88d5084ed163be44588934921'
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
W = "{" + NS["w"] + "}"
TEXT_TAGS = {W + "t", "{" + NS["m"] + "}t"}

def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, "duplicate JSON object key")
        out[key] = value
    return out


def parse_json(raw):
    return json.loads(raw, object_pairs_hook=unique_pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def read_json(name):
    path = safe(HERE / name)
    raw = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
    return parse_json(raw)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(path):
    path = Path(os.path.abspath(path))
    for ancestor in (path, *path.parents):
        require(not ancestor.is_symlink(), 'symlink forbidden: ' + str(ancestor))
    if path.exists():
        mode = path.lstat().st_mode
        require(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'nonregular entry forbidden: ' + str(path))
    return path


def local_module(name):
    # Explicit members support -I -S and prevent ambient/PYTHONPATH fallbacks.
    path = safe(HERE / (name + '.py'))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def no_host_audit():
    counts = {'network_calls': 0, 'subprocess_calls': 0, 'SQL_calls': 0,
              'host_private_open_attempts': 0, 'write_open_attempts': 0,
              'packet_read_opens': 0, 'stdlib_read_opens': 0}
    stdlib = Path(os.__file__).resolve().parent
    def hook(event, args):
        if event.startswith(('socket.', 'http.client.', 'urllib.')):
            counts['network_calls'] += 1
            raise RuntimeError('No-host replay forbids network: ' + event)
        if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp', 'os.fork', 'os.exec', 'os.spawn'}:
            counts['subprocess_calls'] += 1
            raise RuntimeError('No-host replay forbids subprocess: ' + event)
        if event.startswith('sqlite3.'):
            counts['SQL_calls'] += 1
            raise RuntimeError('No-host replay forbids SQL: ' + event)
        if event == 'open':
            path, mode, flags = args
            if isinstance(path, int):
                counts['host_private_open_attempts'] += 1
                raise RuntimeError('No-host replay forbids descriptor file opens')
            if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)):
                counts['write_open_attempts'] += 1
                raise RuntimeError('No-host replay forbids file writes')
            target = Path(os.path.abspath(os.fsdecode(path)))
            if target.is_relative_to(HERE):
                safe(target)
                counts['packet_read_opens'] += 1
            elif target.is_relative_to(stdlib):
                counts['stdlib_read_opens'] += 1
            else:
                counts['host_private_open_attempts'] += 1
                raise RuntimeError('No-host replay forbids host-private open: ' + str(target))
    sys.addaudithook(hook)
    return counts


def parse_native(item):
    meta = read_json(item['meta'])
    raw = gzip.decompress(safe(HERE / item['rows']).read_bytes())
    values = [parse_json(line) for line in raw.splitlines()]
    require(all(type(r) is list and len(r) == 3 and type(r[0]) is str and type(r[1]) is str
                and (r[2] is None or type(r[2]) is str) for r in values), 'complete native three-field types')
    query = safe(HERE / item['query']).read_bytes()
    require(meta['id'] == 'RAN3_P4_CQ4-2' and meta['wg'] == 'RAN3' and meta['status'] == 'OK', 'native case/status')
    require(meta['query'].encode() == query and meta['query_sha256'] == sha(query), 'exact native query bytes')
    require(meta['columns'] == ['tdocNumber', 'reason', 'summary'], 'full native projection')
    require(meta['rows_retained'] == len(values) == item['rows_n'] and meta['bytes_retained'] == len(raw)
            and meta['rows_sha256'] == sha(raw), 'full untruncated native rows')
    require(meta['full_rows_available'] and not meta['truncated'] and meta['rollback_completed']
            and meta['execution_summary_complete'], 'actual native capture completed')
    require(meta['plan_query_type'] == meta['execution_query_type'] == 'r'
            and meta['limits']['timeout_s'] == 20, 'read-only EXPLAIN and actual execution')
    return [dict(zip(meta['columns'], row)) for row in values], meta, raw

def main():
    audit = no_host_audit()
    require(sha(safe(HERE / 'immutable_inventory.json').read_bytes()) == INVENTORY_SHA256, 'immutable inventory pin')
    inventory, manifest = read_json('immutable_inventory.json'), read_json('manifest.json')
    require(manifest['files'] == inventory and manifest['immutable_inventory_sha256'] == INVENTORY_SHA256, 'manifest inventory binding')
    actual = set()
    for path in HERE.rglob('*'):
        safe(path)
        mode = path.lstat().st_mode
        require(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'nonregular packet entry')
        if stat.S_ISREG(mode):
            actual.add(path.relative_to(HERE).as_posix())
    require(actual == set(inventory) | {'manifest.json', 'immutable_inventory.json', 'verify.py'}, 'closed payload inventory')
    for name, pin in inventory.items():
        rel = Path(name)
        require(type(name) is str and name and '\\' not in name and not rel.is_absolute() and '..' not in rel.parts, 'safe member name')
        raw = safe(HERE / rel).read_bytes()
        require(len(raw) == pin['bytes'] and sha(raw) == pin['sha256'], 'payload identity: ' + name)
    require(sha((HERE / 'verify.py').read_bytes()) == manifest['verifier_sha256'], 'verifier identity')
    declarations = read_json('packet_declarations.json')
    require(set(manifest) == set(declarations) | {'files', 'immutable_inventory_sha256', 'verifier_sha256'}, 'manifest declaration keys')
    require(all(manifest[key] == value for key, value in declarations.items()), 'scientific declaration values')
    typed = local_module('typed_values')
    local_module('scorer')
    scorer, controls, schema = local_module('original_scorer'), local_module('contract_checks'), local_module('review_schema')
    local_module('binary_reader_v2')
    local_module('binary_styles_v2')
    local_module('original_ooxml_reader_v2')
    local_module('source_replay_v1')
    rule = local_module('technical_approval_rule_v4')
    source = local_module('technical_source_replay_v2')
    role_controls = local_module('technical_approval_controls_v5')
    task = read_json('repair_technical_approval_v5.json')
    original, criteria = read_json('authority/original.json'), read_json('authority/criteria.json')
    benchmark = (HERE / 'authority/original_benchmark_row.jsonl').read_bytes()
    origin = read_json('authority/original_benchmark_provenance.json')
    require(parse_json(benchmark) == original and sha(benchmark) == origin['extracted_line_sha256']
            and len(benchmark) == origin['extracted_line_bytes'] and origin['line_number_1based'] == 374, 'original benchmark row')
    require(task['id'] == original['id'] == manifest['id'] == 'RAN3_P4_CQ4-2', 'case identity')
    require(task['question_en'] == original['question_en'] and task['original_query'] == original['cypher'], 'unchanged original EN and authored query')
    require(sha(task['question_en'].encode()) == manifest['question_sha256'] == '6336c9f659885b2bdd004ca66d589bcbbec45377320ee99cbc582016ee1d20e7', 'original question bytes')
    require(sha(task['original_query'].encode()) == '0bff9b5b999debe3af18af26ed023edad4dfffc93e236c892e529fdb28ee53f9', 'original authored query identity')
    require(len(task) == 9 and sha(typed.json_exact(task).encode()) == manifest['canonical_repair_sha256']
            == '7309bfe374e2e3f9b2770ade378ba81311dcc28f01fc49d42e45445ce032869e', 'canonical original-meaning repair')
    require(sha((HERE / 'authority/criteria.json').read_bytes()) == manifest['criteria_sha256']
            == 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'fixed original seven criteria')
    require([(f['name'], f['type'], f['nullable']) for f in task['required_fields']]
            == [('tdocNumber', 'string', False), ('reason', 'string', False), ('summary', 'string', True)], 'three complete requested roles')
    require(task['collection'] == {'kind': 'top_k_boundary_ties', 'value': 5,
            'source_order_keys': [{'source_column': 'tdocNumber', 'direction': 'asc'}],
            'tie_policy': 'any_subset_at_boundary', 'within_tie_order': 'any', 'require_rank_order': False}, 'ASC5 membership and unordered serialization')
    primary, secondary = read_json('reviews/primary.json'), read_json('reviews/secondary.json')
    for review in [primary, secondary]:
        schema.check_pass(review, task['question_en'], criteria['semantic_units'], criteria_sha=manifest['criteria_sha256'],
                          identity_key='repair_sha256', identity_sha=manifest['canonical_repair_sha256'])
        require((review.get('nonblind') is True or review.get('review_kind') == 'second nonblind AI judgment')
                and review.get('human_expert_n', review.get('expert_validation_n', 0)) == 0
                and review.get('human_author_review_completed', False) is False, 'nonblind AI provenance')
    require(primary['reviewer'] != secondary['reviewer'] and secondary['reviewer'] == 'ROOT /root', 'distinct two AI reviews')
    proof, binding = read_json('reviews/ROOT_actual_source_SQL_replay.json'), read_json('reviews/main_D_actual_native_SQL_binding.json')
    require(proof['status'].startswith('PASS') and binding['status'].startswith('PASS'), 'actual independent source/SQL and native binding')
    identity_review = read_json('actual_ROOT_semantic_review_identity_and_v3_native_preparation_audit.json')
    require(identity_review['status'] == 'PASS_TWO_NONBLIND_EXACT7_AND_NATIVE_INPUT_PREPARATION'
            and identity_review['primary']['sha256'] == sha((HERE / 'reviews/primary.json').read_bytes())
            and identity_review['secondary']['sha256'] == sha((HERE / 'reviews/secondary.json').read_bytes())
            and identity_review['canonical_repair_sha256'] == manifest['canonical_repair_sha256']
            and identity_review['fixed_criteria_sha256'] == manifest['criteria_sha256'], 'ROOT independent seven-unit identity and preparation proof')
    for evidence in secondary['evidence_pins']:
        member = ('reviews/primary.json' if evidence['path'] == 'canonical_primary_review_technical_approval_v5.json'
                  else 'reviews/ROOT_actual_source_SQL_replay.json' if evidence['path'] == 'actual_ROOT_fresh_SQL_original_CR10_fields_and_controls_v5.json'
                  else evidence['path'])
        raw = safe(HERE / member).read_bytes()
        require(len(raw) == evidence['bytes'] and sha(raw) == evidence['sha256'], 'ROOT secondary evidence identity')
    require(binding['SQLite_sha256_before'] == binding['SQLite_sha256_after'] == manifest['SQLite_sha256']
            == 'ff55fe57ee9435c25b59e1d90c5ee09ee0ff167696c4afeb05f21e367f4c6a29', 'immutable SQL database identity')
    require(binding['bounded_source_CR_paths_objects'] == [142, 145, 37]
            and binding['full426_global_approval_source_classifier'] is False, 'bounded source certification')
    frozen = read_json('actual_frozen_full_input_v1.json.gz')
    require(frozen['SQLite_sha256'] == manifest['SQLite_sha256'], 'frozen database binding')
    require([len(frozen[key]) for key in ['CR', 'Agreement', 'REFERENCES']] == [19974, 1192, 2849], 'complete frozen class inputs')
    bycr, byag = {r['node_id']: r for r in frozen['CR']}, {r['node_id']: r for r in frozen['Agreement']}
    refs = frozen['REFERENCES']
    require(len(bycr) == 19974 and len(byag) == 1192 and all(a in byag and c in bycr for a, c in refs), 'original node and relation keys')
    referenced = {c for a, c in refs}
    original_population = sorted((r for r in frozen['CR'] if r['reasonForChange'] is not None and r['node_id'] in referenced), key=lambda r: r['tdocNumber'])
    project = lambda rows: [{'tdocNumber': r['tdocNumber'], 'reason': r['reasonForChange'], 'summary': r['summaryOfChange']} for r in rows]
    original_full = project(original_population)
    repaired_population, repaired_paths = rule.project(frozen)
    repaired_full = project(repaired_population)
    require(len(original_full) == 426 and len(repaired_full) == len(repaired_paths) == 8, 'original and repaired frozen projections')
    cutoff = repaired_population[4]['tdocNumber']
    original_prefix = [(a, c) for a, c in refs if bycr[c]['reasonForChange'] is not None and bycr[c]['tdocNumber'] <= cutoff]
    require((len({c for a, c in original_prefix}), len(original_prefix), len({a for a, c in original_prefix})) == (142, 145, 37), 'original pre-predicate dependency frontier')
    metadata = {c['tdocNumber']: c for c in frozen['CR'] if c['reasonForChange'] is not None and c['tdocNumber'] <= cutoff}
    edges = set(map(tuple, refs))
    mentions = []
    for a in frozen['Agreement']:
        for tdoc in sorted(set(re.findall(r'R3-\d{6}', (a['content'] or '') + '\n' + (a['note'] or '')))):
            if tdoc in metadata:
                mentions.append({'resolutionId': a['resolutionId'], 'tdocNumber': tdoc,
                                 'existing_REFERENCE': (a['node_id'], metadata[tdoc]['node_id']) in edges})
    frontier = read_json('actual_technical_approval_full142_145path_source_matrix_v5.json')
    require(len(metadata) == 1275 and len(mentions) == 145 and all(m['existing_REFERENCE'] for m in mentions)
            and frontier['all_metadata_literal_mentions'] == mentions, 'complete captured metadata target scan over1192 bodies/notes')
    require(frontier['later_complete_source_classifier_certified'] is False and frontier['positive_paths_n'] == 5
            and frontier['negative_pre_cutoff_paths_n'] == 140, 'source judgement coverage')
    require(sum(c['tdocNumber'] < cutoff for c in repaired_population) == 4
            and sum(c['tdocNumber'] == cutoff for c in repaired_population) == 1, 'fifth cutoff membership')
    for span in read_json('authority/spans.json')['spans']:
        raw = (HERE / span['file']).read_bytes()
        part = ''.join(raw.decode().splitlines(keepends=True)[span['first_line'] - 1:span['last_line']])
        require(sha(raw) == span['file_sha256'] and part == span['text'] and sha(part.encode()) == span['text_sha256'], 'original authority span bytes')
    native, metas = {}, {}
    for item in read_json('native/index.json'):
        rows, meta, raw = parse_native(item)
        native[item['kind']], metas[item['kind']] = rows, meta
        bp = next(v for v in binding['captures'] if v['kind'] == item['kind'])
        require(bp['metadata']['sha256'] == sha((HERE / item['meta']).read_bytes())
                and bp['retained_rows']['sha256'] == sha(raw), 'actual SQL/native capture pins')
    require(native == {'original_full': original_full, 'repaired_full': repaired_full, 'limited': repaired_full[:5]}, 'native original426/repaired8/selected5 all three fields')
    require((HERE / 'queries/limited.cypher').read_bytes() == task['reference_query'].encode(), 'canonical limited query exact UTF8 bytes')
    require((HERE / 'queries/repaired_full.cypher').read_bytes() == task['reference_query'].replace(' LIMIT 5', '').encode(), 'full repaired exact query')
    require((HERE / 'queries/original_full.cypher').read_bytes() == task['original_query'].replace(' LIMIT 5', '').encode(), 'original full exact query')
    execution, protocol, guard = read_json('native/execution_RAN3.json'), read_json('native/execution_protocol.json'), read_json('native/guard_receipt.json')
    require(execution['inventory_unchanged'] and execution['source_before'] == execution['source_after'], 'actual original inventory unchanged')
    require(execution['source_before']['nodes'] == 87980 and execution['source_before']['relationships'] == 481498
            and execution['source_before']['source']['sha256'] == manifest['ttl_sha256']
            == 'd9791c08773a0e38b89869b3882d3098d879a37ddd7109630c346200d6776e95', 'original RAN3 graph identity')
    require(execution['model_calls'] == 0 and len(execution['items']) == 3 and all(v['status'] == 'OK' for v in execution['items']), 'actual three native queries model0')
    input_raw = (HERE / 'native/requested_input.jsonl').read_bytes()
    inputs = [parse_json(line) for line in input_raw.splitlines()]
    require(execution['input_sha256'] == sha(input_raw) and len(inputs) == 3
            and {v['query_sha256'] for v in inputs} == {v['query_sha256'] for v in metas.values()}, 'exact input native binding')
    require(all(v['query_sha256'] == sha(v['candidate_query'].encode()) for v in inputs), 'input query byte hashes')
    require(protocol['container_memory_bytes'] == protocol['python_address_space_limit_bytes'] == 2 * 1024**3
            and protocol['container_cpu_cores'] == protocol['concurrent_containers'] == 1
            and protocol['query_timeout_seconds'] == 20, 'unchanged native resources and timeout')
    require(guard['status'] == 'PASS' and guard['child_exit'] == 0 and guard['quality_rerolls'] == 0, 'actual operational guard pass')
    require(guard['prestart_available_minimum_bytes'] == 26 * 1024**3 and guard['continuous_reserve_minimum_bytes'] == 16 * 1024**3, 'dual host26/16')
    require(all(value >= 26 * 1024**3 for key, value in guard['initial_memory'].items() if key.endswith('available_bytes')), 'both host admission')
    require(all(sample[key] >= 16 * 1024**3 for sample in guard['memory_samples'] for key in ['Linux_available_bytes', 'Windows_available_bytes']), 'both host continuous reserve')
    require(guard['owned_cleanup']['owned_stopped'] and guard['owned_cleanup']['common_lock_held'], 'owned stopped under common lock')
    require(role_controls.run() == read_json('actual_technical_approval_query_and_typed_controls_v5.json'), 'actual25 grammar and30 typed controls with2849 literal regex comparisons')
    source_result = source.replay()
    require(source_result == read_json('actual_technical_original_members_source37_fields10_replay_v2.json'), 'original15 source members/37objects/145paths/10metadatafields')
    root_source = read_json('actual_ROOT_fresh_source37_original15_archive_member_replay_v2.json')
    require(root_source['status'] == 'PASS_ROOT_FRESH_ORIGINAL_ARCHIVES_SOURCE37_AND_FIELDS10'
            and root_source['replay'] == source_result and len(root_source['original_archives_and_members']) == 15
            and all(row['exact_original_archive_member'] for row in root_source['original_archives_and_members']), 'ROOT fresh original archive/member and source replay')
    policy = read_json('actual_original_metadata_cell_policy_and_nested_table_v1.json')
    parser = (HERE / policy['original_parser']['preserved_file']).read_bytes()
    require(sha(parser) == policy['original_parser']['sha256'] and b'cells = [c.text.strip() for c in row.cells]' in parser, 'original metadata parser policy')
    field_receipt = read_json('actual_provisional_repair_five_original_CR_ten_fields_v2.json')
    source_field = {(r['tdocNumber'], f['field']): f for r in field_receipt['CR_fields'] for f in r['source_fields']}
    differences = []
    cover = sys.modules['source_replay_v1']
    for record in policy['ten_fields']:
        field = source_field[(record['tdocNumber'], record['field'])]
        cell = ET.fromstring(record['original_cell_XML'])
        direct = '\n'.join(cover.inline(p) for p in cell.findall(W + 'p')).strip()
        descendant = '\n'.join(cover.inline(p) for p in cell.iter(W + 'p')).strip()
        require(direct == record['direct_paragraph_text'] == field['frozen_value']
                and descendant == record['all_descendant_paragraph_text']
                and sha(ET.tostring(cell, encoding='utf-8')) == record['cell_XML_sha256'], 'original complete captured metadata field')
        if direct != descendant:
            differences.append((record['tdocNumber'], record['field'], len(direct), len(descendant)))
    require(differences == [('R3-221213', 'reasonForChange', 555, 677)], 'preserved nested-table source witness')
    require(all(audit[key] == 0 for key in ['network_calls', 'subprocess_calls', 'SQL_calls', 'host_private_open_attempts', 'write_open_attempts']), 'default no-host execution')
    print(json.dumps({'status': 'PASS', 'id': task['id'], 'native_counts': [426, 8, 5],
        'source_frontier': [142, 145, 37], 'source_members': 15, 'requested_fields': 10,
        'typed_role_controls': 30, 'approval_grammar_controls': 25, 'literal_regex_comparisons': 2849,
        'distinct_nonblind_AI_reviews': 2, 'semantic_units': 7, 'human_n': 0, 'model_calls': 0,
        'ROOT_final_seal_included': False, 'no_host_audit': audit}, ensure_ascii=False))

if __name__ == '__main__':
    main()
