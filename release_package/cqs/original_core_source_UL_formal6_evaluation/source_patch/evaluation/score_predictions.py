#!/usr/bin/env python3
"""Spec: exact separate UL formal-source content prediction scoring.
Ontology: requested complete formal content strings, unordered set.
Cycle: KDD2027 Cycle1 separate-source comparison.
배경: no historical score transfer or source/causality claim.
사용: --predictions PATH; exact pinned task/gold.
LLM 호출: none.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import scorer
import original_scorer

BASE = Path(__file__).resolve().parent


def read(path):
    return [scorer.get_kernel().loads_exact(s) for s in path.read_text().splitlines() if s.strip()]


def unique(rows):
    result = {}
    for row in rows:
        if row['id'] in result:
            raise ValueError('duplicate prediction/task ID: ' + row['id'])
        result[row['id']] = row
    return result


def run(tasks_path, gold_path, predictions_path):
    tasks, gold, predictions = map(lambda p: unique(read(p)), (tasks_path, gold_path, predictions_path))
    if set(tasks) != set(gold) or not set(predictions) <= set(tasks):
        raise ValueError('prediction IDs must belong to the admitted task/gold set')
    outcomes = []
    for id, prediction in predictions.items():
        task = tasks[id]
        if (task.get('validation_status') != 'validated'
                or prediction.get('repair_sha256') != task['repair_sha256']
                or gold[id].get('repair_sha256') != task['repair_sha256']):
            raise ValueError('prediction/gold belongs to a different or unvalidated contract: ' + id)
        result = original_scorer.score(task, gold[id]['records'], prediction['records'],
                                        order_groups=gold[id]['order_groups'])
        outcomes.append(dict(id=id, repair_sha256=task['repair_sha256'], **result))
    return {'kind': 'Supplied predictions scored against exact admitted repaired contracts; no historical-score transfer',
            'admitted_n': len(tasks), 'predicted_n': len(predictions),
            'prediction_file_sha256': hashlib.sha256(predictions_path.read_bytes()).hexdigest(),
            'outcomes': outcomes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--tasks', type=Path, default=BASE / 'tasks.jsonl')
    parser.add_argument('--gold', type=Path, default=BASE / 'reference_gold.jsonl')
    args = parser.parse_args()
    print(scorer.get_kernel().json_exact(run(args.tasks, args.gold, args.predictions)))
