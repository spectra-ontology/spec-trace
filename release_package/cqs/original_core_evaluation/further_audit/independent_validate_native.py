#!/usr/bin/env python3
"""Read-only independent check of a separate further-repair snapshot.

Writes only this auditor's report. Never executes a database, model or admission.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ORIG = BASE.parent
sys.path.insert(0, str(ORIG))
import continue_original as continuation

RUN = BASE / 'native_capture'
FROZEN = ORIG / 'final_staging/release_package/cqs/original_core_repair'


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def load(path):
    raw = Path(path).read_bytes()
    return raw, [continuation.scorer.get_kernel().loads_exact(line)
                 for line in raw.decode().splitlines() if line.strip()]


def main():
    names = ('tasks.jsonl', 'reference_gold.jsonl', 'scorer_checks.jsonl', 'dispositions.jsonl')
    snapshots = {name: load(RUN / name) for name in names}
    tasks = continuation.unique(snapshots['tasks.jsonl'][1])
    gold = continuation.unique(snapshots['reference_gold.jsonl'][1])
    controls = continuation.unique(snapshots['scorer_checks.jsonl'][1])
    dispositions = continuation.unique(snapshots['dispositions.jsonl'][1])
    originals = continuation.unique(continuation.read(
        continuation.native.PUBLIC / 'spectra_cq_v2.0/benchmark.jsonl'))
    frozen = continuation.unique(continuation.read(FROZEN / 'tasks.jsonl'))
    criteria = json.loads((ORIG / 'criteria.json').read_text())
    criteria_sha = file_sha(ORIG / 'criteria.json')
    manifest_sha = file_sha(FROZEN / 'manifest.json')
    assert manifest_sha == '18b301baac1bdacffd7b9f93917f3362c516d54ed5ad2ed7826c7df96e57edb5'
    assert len(frozen) == 350 and not (set(tasks) & set(frozen))
    assert set(tasks) == set(gold) == set(controls)
    source_pins = json.loads((continuation.PREP / 'source_pins.json').read_text())
    source_checks = []
    for pin in source_pins['files']:
        actual = file_sha(pin['path'])
        assert actual == pin['sha256'], 'Original source pin changed: ' + pin['path']
        source_checks.append({'path': pin['path'], 'sha256': actual})
    continuation.RUN = RUN
    rows_total = checks_total = 0
    categories = Counter()
    results = []
    for identifier, task in tasks.items():
        original = originals[identifier]
        assert task['question_en'] == original['question_en']
        assert task['original_query'] == original['cypher']
        assert task['original_question_preserved'] is True
        assert task['original_question_sha256'] == text_sha(original['question_en'])
        assert task['original_query_sha256'] == text_sha(original['cypher'])
        assert task['reference_query_sha256'] == text_sha(task['reference_query'])
        assert task['criteria_sha256'] == criteria_sha
        definition = {k: task[k] for k in continuation.DEFINITION_KEYS}
        assert task['repair_sha256'] == continuation.digest(definition)
        assert task['repair_class'] == ('scorer_only' if task['reference_query'] == original['cypher'] else 'query_and_scorer')
        for review in (task['primary_review'], task['secondary_review']):
            continuation.review_schema.check_pass(review, task['question_en'], criteria['semantic_units'],
                criteria_sha=criteria_sha, identity_key='repair_sha256', identity_sha=task['repair_sha256'])
        assert task['human_author_review_completed'] is False
        assert task['expert_validation_n'] == task['model_calls'] == 0
        native_rows, receipt = continuation.references(task)
        assert native_rows is not None
        # Native loader uses ordinary float for elapsed time; retained exact
        # JSON codec uses Decimal. Compare the canonical JSON, not binary-float
        # identity, while retaining every actual receipt field and hash.
        assert continuation.digest(receipt) == continuation.digest(task['reference_evidence'])
        assert len(native_rows) == task['native_rows'] == receipt['rows_retained']
        assert receipt['status'] == 'OK' and receipt['truncated'] is False
        assert receipt['full_rows_available'] is True and receipt['execution_summary_complete'] is True
        manual_records = []
        for native in native_rows:
            record = {}
            for field in task['required_fields']:
                name, source = field['name'], field['source_column_or_expression']
                assert source in receipt['columns'] and source in native
                value = native[source]
                assert value is not None or field['nullable']
                if value is not None:
                    expected = {'string': str, 'integer': int, 'boolean': bool}.get(field['type'])
                    assert expected is not None and type(value) is expected
                record[name] = value
            manual_records.append(record)
        assert manual_records == gold[identifier]['records']
        assert continuation.digest(manual_records) == task['projected_records_sha256']
        assert gold[identifier]['repair_sha256'] == task['repair_sha256']
        tokens = [continuation.digest(record) for record in manual_records]
        assert len(tokens) == len(set(tokens)), 'Duplicate requested identities: ' + identifier
        groups = gold[identifier]['order_groups']
        if task['collection']['kind'] == 'top_k_boundary_ties':
            source_keys = task['collection']['source_order_keys']
            assert len(source_keys) == 1 and source_keys[0]['direction'] == 'desc'
            column = source_keys[0]['source_column']
            manual_groups, previous = [], None
            for native, record in zip(native_rows, manual_records):
                key = native[column]
                assert type(key) is int and key >= 0
                assert previous is None or previous >= key
                if previous is None or key != previous:
                    manual_groups.append([])
                manual_groups[-1].append(record)
                previous = key
            assert groups == manual_groups
            assert task['collection']['value'] == task['cardinality_policy']['value']
            assert task['collection']['require_rank_order'] is False
        else:
            assert groups is None
        fresh = continuation.checks(task, manual_records, groups)
        assert fresh == controls[identifier]['checks']
        assert controls[identifier]['repair_sha256'] == task['repair_sha256']
        assert controls[identifier]['pass'] is True and all(c['pass'] for c in fresh)
        assert dispositions[identifier]['status'] == 'pass'
        assert dispositions[identifier]['repair_sha256'] == task['repair_sha256']
        rows_total += len(native_rows)
        checks_total += len(fresh)
        categories.update(c['check'].split(':')[0] for c in fresh)
        results.append({'id': identifier, 'repair_sha256': task['repair_sha256'],
                        'native_rows': len(native_rows), 'actual_replayed_scorer_checks': len(fresh),
                        'original_question_bytes_preserved': True, 'technical_artifact_checks_pass': True,
                        'separate_maximum_pool_witness_required': identifier in {'RAN5_P3_CQ2-4', 'RAN3_P3_CQ2-3'}})
    stable = {name: hashlib.sha256(raw).hexdigest() == file_sha(RUN / name)
              for name, (raw, values) in snapshots.items()}
    assert all(stable.values()), 'Further snapshot changed during audit; rerun after capture completes'
    assert file_sha(FROZEN / 'manifest.json') == manifest_sha
    report = {'kind': 'Independent read-only technical artifact replay, distinct from raw-source truth/expert review',
              'status': 'artifact_checks_pass', 'additional_n': len(tasks), 'prior_frozen_cohort_n': len(frozen),
              'union_artifact_n': len(tasks) + len(frozen), 'native_rows': rows_total,
              'actual_replayed_scorer_controls': checks_total, 'control_categories': dict(categories),
              'snapshot_pins': {name: hashlib.sha256(raw).hexdigest() for name, (raw, values) in snapshots.items()},
              'snapshot_stable_through_audit': stable, 'source_pins_actual_hash_checked': source_checks,
              'frozen_prior_manifest_sha256': manifest_sha, 'criteria_sha256': criteria_sha,
              'expert_validation_n': 0, 'human_author_reviews_completed': 0, 'database_queries_by_auditor': 0,
              'model_calls_by_auditor': 0, 'does_not_assert_full_560_or_archive_truth': True,
              'maximum_pool_witness_gate_reported_separately': True, 'items': results}
    (BASE / 'independent_native_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'additional_n', 'union_artifact_n', 'native_rows', 'actual_replayed_scorer_controls')}))


if __name__ == '__main__':
    main()
