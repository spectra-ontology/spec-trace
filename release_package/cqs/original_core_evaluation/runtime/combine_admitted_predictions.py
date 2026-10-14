#!/usr/bin/env python3
"""Combine disjoint frozen cohorts without generating or re-running predictions."""
import argparse
import hashlib
import json
from pathlib import Path

METHODS = ('text2cypher', 'text2sql', 'single_retrieval', 'iterative_retrieval')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    values = [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
    if len({v['id'] for v in values}) != len(values):
        raise ValueError('Duplicate IDs: ' + str(path))
    return values


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def combine(bundle, main, extension, output):
    if output.exists():
        raise ValueError('Existing union must be preserved')
    tasks = {t['id']: t for t in rows(bundle / 'tasks.jsonl')}
    if len(tasks) != 371:
        raise ValueError('Expected final measured 371-contract union')
    cohorts = []
    components = []
    for run, expected in ((main, 350), (extension, 21)):
        protocol = read(run / 'protocol.json')
        ids = set(protocol['cohort_ids'])
        if len(ids) != expected or not ids.issubset(tasks):
            raise ValueError('Cohort denominator mismatch')
        complete = read(run / 'generation_complete.json')
        if complete['completed_method_items'] != expected * 4:
            raise ValueError('Cohort dispositions incomplete')
        if read(run / 'analysis.json')['admitted_n'] != expected:
            raise ValueError('Cohort must be scored before union')
        cohorts.append(ids)
        components.append({'run_name': run.name, 'n': expected,
                           'protocol_sha256': sha(run / 'protocol.json'),
                           'analysis_sha256': sha(run / 'analysis.json'),
                           'generation_complete_sha256': sha(run / 'generation_complete.json')})
    if cohorts[0] & cohorts[1] or cohorts[0] | cohorts[1] != set(tasks):
        raise ValueError('Overlapping or missing union IDs')
    all_outputs = {}
    source_pins = {}
    for method in METHODS:
        all_outputs[method] = {}
        for name in ('predictions.jsonl', 'statuses.jsonl'):
            merged = {}
            for run in (main, extension):
                path = run / method / name
                values = rows(path)
                expected = set(read(run / 'protocol.json')['cohort_ids'])
                if {v['id'] for v in values} != expected:
                    raise ValueError('Missing source ID: ' + str(path))
                source_pins[str(path)] = sha(path)
                for value in values:
                    id = value['id']
                    if id in merged or value['repair_sha256'] != tasks[id]['repair_sha256']:
                        raise ValueError('Duplicate ID or changed repair SHA')
                    merged[id] = value
            if set(merged) != set(tasks):
                raise ValueError('Incomplete union denominator')
            all_outputs[method][name] = [merged[id] for id in sorted(tasks)]
    output.mkdir(parents=True)
    for method, files in all_outputs.items():
        (output / method).mkdir()
        for name, values in files.items():
            (output / method / name).write_text(''.join(json.dumps(v, ensure_ascii=False, allow_nan=False) + '\n' for v in values))
    write(output / 'protocol.json', {
        'kind': 'Disjoint union of two already frozen and evaluated original-question cohorts',
        'cohort_ids': sorted(tasks), 'n': len(tasks), 'admitted_n': len(tasks),
        'tasks_sha256': sha(bundle / 'tasks.jsonl'),
        'gold_sha256': sha(bundle / 'reference_gold.jsonl'),
        'bundle_manifest_sha256': sha(bundle / 'manifest.json'),
        'scorer_sha256': sha(bundle / 'score_predictions.py'),
        'original_scorer_sha256': sha(bundle / 'original_scorer.py'),
        'typed_scorer_sha256': sha(bundle / 'scorer.py'),
        'typed_kernel_sha256': sha(bundle / 'typed_values.py'),
        'components': components, 'source_prediction_and_status_pins': source_pins,
        'new_model_calls': 0, 'new_query_executions': 0, 'quality_retries': 0,
        'interpretation': 'One model; all admitted original IDs exactly once. Original attempts and pre-provider transport recovery remain separately archived. This cohort does not represent all Core560.',
    })
    write(output / 'generation_complete.json', {'completed_method_items': len(tasks) * 4,
          'required': len(tasks) * 4, 'combined_existing_dispositions': True, 'new_model_calls': 0})
    print(json.dumps({'combined_n': len(tasks), 'output': str(output), 'new_model_calls': 0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle', 'main', 'extension', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    combine(args.bundle, args.main, args.extension, args.output)
