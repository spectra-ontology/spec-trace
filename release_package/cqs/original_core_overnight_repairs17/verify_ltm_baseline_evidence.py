#!/usr/bin/env python3
"""Recount the preserved recorded LTM fixture and strict Boolean scoring offline.

This verifies saved source and membership evidence. It does not execute a graph,
SQLite database, model, or original Git server, and does not certify the original
artifact's capability classification or standards truth.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
IDENT = 'RAN2_P3_P3-S8-CQ07'
PINS = {
    'original_recorded_baseline28_source_fixture.json': 'd33499f36a1dc405697de7698dd3dc4f6e35903b59f8ac21a9813a0b70996c5c',
    'historical_baseline_v5.md': '7563af03b7bf1eb409e205432a7802897c6e8eb1262d6dd0849998c74d1f665c',
    'original_Git_reference_chain.json': '236651be2b6eea3e7e798d821fe997fc13fd934608f5cc385763bfe3354e28a2',
    'historical_original_Step8_baseline_introduction.md': '67ad1b3c8aa5e004a15efa20fa2bb526a31714ffcdcca518809a6aeb2ebc4d64',
    'saved_conditional_membership_evidence.json': 'feceb0a07f36ec6262ae0e81d96f1908b06b5bd6c428c2a12774e69c5ccea95d',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def verify_source(directory, task, native):
    directory = Path(directory)
    for name, expected in PINS.items():
        assert sha(directory / name) == expected, name
    fixture = load(directory / 'original_recorded_baseline28_source_fixture.json')
    chain = load(directory / 'original_Git_reference_chain.json')
    text = (directory / 'historical_baseline_v5.md').read_text()
    assert fixture['id'] == task['id'] == IDENT
    assert fixture['source_commit'] == '23e3c03cbabb81948d92be7bf3c0aee88c24ac5f'
    assert fixture['source_original_path'] == 'docs/usecase/answers/spectra_v5_disjoint_features/q4_ltm_rel18.md'
    assert fixture['source_complete_blob_pin']['sha256'] == PINS['historical_baseline_v5.md']
    assert fixture['new_expected_names_or_answers_in_model_prompts'] is False
    # Heading boundaries, rather than the old human line-range label, define §6.
    starts = list(re.finditer(r'^## 6\.', text, re.MULTILINE))
    ends = list(re.finditer(r'^## 7\.', text, re.MULTILINE))
    assert len(starts) == len(ends) == 1 and starts[0].start() < ends[0].start()
    section = text[starts[0].start():ends[0].start()]
    names = sorted(set(re.findall(r'`((?:ltm-|LTM-)[A-Za-z0-9-]+-r\d+)`', section)))
    entries = fixture['entries']
    assert len(entries) == fixture['entries_n'] == len(names) == 28
    assert entries == [{'capabilityItemName': n, 'specNumber': '38.306', 'granularity': 'item'} for n in names]
    assert 'IE links' in section
    expected_query_names = json.loads(task['reference_query'].split(' AS expectedName', 1)[0].removeprefix('UNWIND '))
    assert expected_query_names == names
    assert "cap.specNumber = '38.306'" in task['reference_query']
    assert "cap.granularity = 'item'" in task['reference_query']
    assert 'count(cap) > 0 AS loaded' in task['reference_query']
    assert task['reference_query'].endswith('RETURN all(loaded IN expectedItemLoaded WHERE loaded) AS all_loaded')
    original = (directory / 'historical_original_Step8_baseline_introduction.md').read_text()
    assert 'P3-S8-CQ07' in original and 'cycle-02 D-B baseline' in original
    origin = chain['original_design_complete_Step8_context']
    assert origin['commit'] == '99f469c2a0ba5f60f5695ab7f03c7545d2809a0a'
    assert origin['whole_blob_sha256'] == PINS['historical_original_Step8_baseline_introduction.md']
    assert len(chain['source_reference_chain']) == 5
    assert chain['opposing_interpretation'] and chain['chronology_limit']
    saved = load(directory / 'saved_conditional_membership_evidence.json')['actual_readonly_execution']
    assert saved['db_before'] == saved['db_after']
    assert saved['SQL_parameters'] == names
    rows = saved['all28_left_join_rows']
    assert set(r['expected_name'] for r in rows) == set(names)
    loaded = set()
    for row in rows:
        if row['node_id'] is None:
            assert all(row[k] is None for k in ('capabilityItemName', 'specNumber', 'granularity'))
        else:
            assert row['capabilityItemName'] == row['expected_name']
            assert row['specNumber'] == '38.306' and row['granularity'] == 'item'
            loaded.add(row['expected_name'])
    missing = sorted(set(names) - loaded)
    assert len(loaded) == saved['exact_expected_loaded_n'] == 25
    assert missing == saved['exact_expected_not_CapabilityItem_names'] == sorted(n for n in names if n.startswith('LTM-'))
    assert len(native) == 1 and set(native[0]) == {'all_loaded'}
    assert type(native[0]['all_loaded']) is bool
    assert native[0]['all_loaded'] is (len(loaded) == len(names)) is False
    return {'status': 'PASS', 'recorded_inventory_n': len(names), 'saved_exact_identity_matches_n': len(loaded),
            'missing_recorded_identities_n': len(missing), 'all_loaded': native[0]['all_loaded'],
            'source_section_boundary': 'heading6 through before heading7',
            'new_database_queries_n': 0, 'new_API_calls_n': 0,
            'limits': 'Recounts supplied saved evidence; no new full-graph or original-source execution. Original historical IE-role defect remains disclosed.'}


def strict_boolean_controls(task, records, original_scorer):
    assert records == [{'all_loaded': False}] and type(records[0]['all_loaded']) is bool
    controls = []
    for name, prediction, expected in (
        ('literal_false', [{'all_loaded': False}], True),
        ('opposite_literal_true', [{'all_loaded': True}], False),
        ('integer_zero_is_not_boolean', [{'all_loaded': 0}], False),
        ('string_false_is_not_boolean', [{'all_loaded': 'false'}], False),
        ('null_is_not_boolean', [{'all_loaded': None}], False),
        ('duplicate_singleton', [{'all_loaded': False}, {'all_loaded': False}], False),
        ('missing_required_boolean', [{}], False),
    ):
        actual = original_scorer.score(task, records, prediction, diagnostic=True)
        assert actual['exact'] is expected, (name, actual)
        controls.append({'check': name, 'pass': True, 'expected_exact': expected})
    return controls
