#!/usr/bin/env python3
"""Spec: replay complete four-method separate-source predictions.
Ontology: exact requested typed fields and frozen collection contracts.
Cycle: KDD Datasets and Benchmarks Cycle1.
배경: failures remain measured outcomes; source facts do not imply query provenance.
사용: --evidence PATH; writes new score files only when requested.
LLM 호출: none.
"""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
METHODS = ('text2cypher', 'text2sql', 'single_retrieval', 'iterative_retrieval')


def load(p): return json.loads(Path(p).read_text())
def read(p): return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
def unique(rows):
    result = {}
    for row in rows:
        if row['id'] in result: raise ValueError('duplicate ID: ' + row['id'])
        result[row['id']] = row
    return result


def calculate(evidence):
    evidence = Path(evidence).resolve()
    contract_path = load(evidence / 'evaluation_contract_location.json')['evaluation_contract_subdir']
    bundle, run = evidence / contract_path, evidence / 'results'
    if not bundle.resolve().is_relative_to(evidence): raise ValueError('contract path escapes evidence')
    sys.path.insert(0, str(bundle))
    spec = importlib.util.spec_from_file_location('retained_source_score', bundle / 'score_predictions.py')
    scorer = importlib.util.module_from_spec(spec); spec.loader.exec_module(scorer)
    tasks = unique(read(bundle / 'tasks.jsonl'))
    gold = unique(read(bundle / 'reference_gold.jsonl'))
    if set(tasks) != set(gold) or len(tasks) != 1: raise ValueError('source cohort must contain exactly one task')
    method_results, summary = {}, {}
    for method in METHODS:
        predictions = unique(read(run / method / 'predictions.jsonl'))
        statuses = unique(read(run / method / 'statuses.jsonl'))
        if set(predictions) != set(tasks) or set(statuses) != set(tasks):
            raise ValueError('all four method denominators must be complete')
        for id, task in tasks.items():
            if statuses[id]['repair_sha256'] != task['repair_sha256']:
                raise ValueError('status is bound to another repair')
        raw = scorer.run(bundle / 'tasks.jsonl', bundle / 'reference_gold.jsonl', run / method / 'predictions.jsonl')
        rows = []
        for outcome in raw['outcomes']:
            status = statuses[outcome['id']]['status']
            row = dict(outcome, execution_status=status, failure_gated=False)
            if status not in {'OK', 'PARTIAL'} or (status == 'PARTIAL' and outcome['gold_records'] == 0):
                row.update(precision=0.0, recall=0.0, f1=0.0, exact=False,
                           matched_records=0, failure_gated=True, raw_scorer_exact=outcome['exact'])
            rows.append(row)
        method_results[method] = {'raw_scores': raw, 'failure_gated_scores': rows}
        summary[method] = {'n': len(rows), 'requested_complete_record_macro_f1': sum(r['f1'] for r in rows) / len(rows),
                          'exact_output_rate': sum(r['exact'] for r in rows) / len(rows),
                          'exact_outputs': sum(r['exact'] for r in rows),
                          'execution_status_counts': dict(Counter(r['execution_status'] for r in rows)),
                          'gold_answer_records': sum(r['gold_records'] for r in rows),
                          'predicted_records': sum(r['predicted_records'] for r in rows),
                          'matched_requested_records': sum(r['matched_records'] for r in rows)}
    analysis = {'kind': 'Retained separate-source four-method requested-record scoring',
                'cohort_ids': list(tasks), 'cohort_n': len(tasks), 'method_items': 4,
                'separate_source_snapshot': True, 'merged_with_frozen_core': False,
                'tables': summary, 'human_expert_validation_n': 0,
                'failure_policy': 'Failures and abstention contribute F1=0 and exact=false. Parsed partial content may receive record credit. No quality regeneration.',
                'metric_boundary': 'Scores only requested output records; does not validate generated query source predicates, reasoning, provenance or causality.',
                'limitations': ['One question per separate source snapshot and one model; no aggregate Core560 claim.',
                                'Base graph/text cutoff and coverage equivalence is not established.',
                                'Live graph, SQL and retrieval executions are retained receipts, not rerun by scoring.']}
    return method_results, analysis


def write_new(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f: json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    methods, analysis = calculate(args.evidence)
    if args.write:
        for method, values in methods.items():
            for name, value in values.items(): write_new(args.evidence / 'results' / method / (name + '.json'), value)
        write_new(args.evidence / 'results/analysis.json', analysis)
    print(json.dumps(analysis, ensure_ascii=False))
