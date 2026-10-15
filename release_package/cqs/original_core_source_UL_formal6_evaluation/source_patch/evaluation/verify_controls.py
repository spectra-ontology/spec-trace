#!/usr/bin/env python3
"""Spec: replay the existing seven basic and twelve literal UL source controls.
Ontology: content-only, unordered complete formal groups; optional context ignored.
Cycle: separately measured KDD source snapshot, no frozen-core count change.
배경: preserve prior controls while checking a self-contained public scorer package.
사용: --bundle PATH containing task/gold/controls and unchanged scorer dependencies.
LLM 호출: none; no database, graph, provider or retrieval execution.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def read(p): return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
def load(p): return json.loads(Path(p).read_text())


def verify(bundle):
    bundle = Path(bundle).resolve()
    sys.path.insert(0, str(bundle))
    import scorer
    import original_scorer
    import contract_checks
    tasks, gold = read(bundle / 'tasks.jsonl'), read(bundle / 'reference_gold.jsonl')
    assert len(tasks) == len(gold) == 1
    task, answer = tasks[0], gold[0]
    assert task['id'] == answer['id'] == 'RAN1_P2_CQ1-2'
    assert task['repair_sha256'] == answer['repair_sha256'] == '7903f18f960a1da17e4e67aebbab4e0d6575d65a8f6718073a0ed6f6272301f9'
    assert task['validation_status'] == 'validated'
    assert len(answer['records']) == 6 and task['collection'] == {'kind': 'set'}
    assert task['cardinality_policy'] == {'mode': 'all'}
    assert task['required_fields'] == [{'name': 'content', 'nullable': False,
                                       'source_column_or_expression': 'a.formalSourceContentWithTables', 'type': 'string'}]
    prior = load(bundle / 'controls.json')
    assert prior['repair_sha256'] == task['repair_sha256']
    basic = contract_checks.checks(task, answer['records'])
    assert basic == prior['basic_controls'] and len(basic) == 7 and all(c['pass'] for c in basic)
    outcomes = []
    for c in prior['source_content_controls']:
        diag = original_scorer.score(task, answer['records'], c['predicted_records'], diagnostic=True)
        assert diag == c['actual_score'] and diag['exact'] is c['expected_exact'], c['name']
        validated = original_scorer.score(task, answer['records'], c['predicted_records'], order_groups=answer['order_groups'])
        assert {k: v for k, v in validated.items() if k != 'diagnostic_only'} == {k: v for k, v in diag.items() if k != 'diagnostic_only'}, c['name']
        outcomes.append({'name': c['name'], 'diagnostic_and_validated_metrics_identical': True,
                         'expected_exact': c['expected_exact'], 'pass': True})
    assert len(outcomes) == 12
    return {'status': 'PASS', 'id': task['id'], 'repair_sha256': task['repair_sha256'],
            'gold_records_n': 6, 'basic_controls_n': 7, 'literal_source_controls_n': len(outcomes),
            'all_existing_recorded_scores_reproduced': True, 'validated_mode_equivalent': True,
            'basic_controls': basic, 'literal_source_controls': outcomes,
            'new_model_native_retrieval_calls_n': 0,
            'metric_limit': 'Exact literal content only; not paraphrase equivalence or truthfulness of optional commentary.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--bundle', type=Path, default=Path(__file__).resolve().parent)
    print(json.dumps(verify(p.parse_args().bundle), ensure_ascii=False))
