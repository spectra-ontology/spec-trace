#!/usr/bin/env python3
"""Replay the actual count/multiplicity17 controls from a portable AUTH8 bundle.

No database or provider is needed. The preserved source-unit receipt supplies
actual alternative-unit counts; the scorer/kernel and frozen bundle are read
without modification. This supplementary reader is outside the frozen runtime.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def load(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(bundle):
    bundle = Path(bundle).resolve()
    sys.path.insert(0, str(bundle))
    import original_scorer
    import contract_checks
    manifest = load(bundle / 'manifest.json')
    assert all(sha(bundle / rel) == wanted for rel, wanted in manifest['files'].items())
    tasks = [json.loads(line) for line in (bundle / 'tasks.jsonl').read_text().splitlines() if line.strip()]
    gold = [json.loads(line) for line in (bundle / 'reference_gold.jsonl').read_text().splitlines() if line.strip()]
    assert len(tasks) == len(gold) == 1
    d = tasks[0]
    assert d['id'] == gold[0]['id'] == 'RAN3_P2_CQ3-1'
    records = gold[0]['records']
    gate = d['portable_gate_evidence']
    actual = load(bundle / gate['actual17controls_and_native_SQL']['file'])
    witness = load(bundle / gate['source_unit_full_set_SQL_witness']['file'])
    assert actual['all_controls_pass'] is True and actual['controls_n'] == 17
    assert actual['repair_sha256'] == witness['repair_sha256'] == d['repair_sha256']
    assert witness['full_requested_records'] == records
    count = witness['linked_distinct_Tdocs_n']
    assert records == [{'resolutionLinkedTdocCount': count}]
    assert len(witness['complete_contributing_Tdoc_identity_records']) == count
    assert len({r['tdocNumber'] for r in witness['complete_contributing_Tdoc_identity_records']}) == count
    assert witness['multiple_resolutions_for_same_Tdoc_witnesses']
    old = witness['old_original_aggregate_records']
    key = 'resolutionLinkedTdocCount'
    cases = [
        ('complete_actual_native_count', records, True),
        ('auxiliary_total_and_decision_count_not_required', [{**records[0], **old[0]}], True),
        ('duplicate_same_count_set_equivalent', records + records, True),
        ('wrong_string_count', [{key: str(count)}], False),
        ('wrong_boolean_count', [{key: True}], False),
        ('wrong_null_count', [{key: None}], False),
        ('old_original_wrong_required_alias', old, False),
        ('actual_all_company_Tdocs_not_linked_subset', [{key: witness['all_company_Tdocs_n']}], False),
        ('actual_decision_count_not_Tdoc_count', [{key: witness['linked_distinct_resolutions_n']}], False),
        ('actual_reference_edge_count_not_Tdoc_count', [{key: witness['reference_edges_n']}], False),
    ]
    basic = contract_checks.checks(d, records)
    assert basic == actual['basic_controls'] and len(basic) == 7 and all(r['pass'] for r in basic)
    replayed = []
    for (name, prediction, expected), saved in zip(cases, actual['additional_controls']):
        assert name == saved['name'] and expected is saved['expected_exact']
        outcome = original_scorer.score(d, records, prediction, diagnostic=True)
        assert outcome['exact'] is expected and outcome == saved['actual']
        replayed.append({'name': name, 'prediction': prediction, 'outcome': outcome, 'pass': True})
    assert len(replayed) == 10
    assert all(sha(bundle / rel) == wanted for rel, wanted in manifest['files'].items())
    print(json.dumps({'status': 'PASS_ACTUAL17_REQUESTED_TDOC_COUNT_AND_MULTIPLICITY_CONTROLS',
        'id': d['id'], 'repair_sha256': d['repair_sha256'], 'bundle_manifest_sha256': sha(bundle / 'manifest.json'),
        'basic_controls_n': len(basic), 'additional_actual_unit_controls_n': len(replayed), 'controls_n': 17,
        'actual_additional_replays': replayed, 'all_pass': True, 'frozen_bundle_unchanged': True,
        'native_model_database_calls': 0, 'human_expert_validation_n': 0}, ensure_ascii=False))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle', type=Path, required=True)
    main(ap.parse_args().bundle)
