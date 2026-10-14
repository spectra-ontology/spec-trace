#!/usr/bin/env python3
"""Score complete predictions against a validated canonical Core contract.

Every prediction declares its definition hash and status: answer or abstain.
An answer with records=[] is a formal empty result; abstention is records=null
and receives no credit even when the reference is empty. This program cannot
certify prediction-generation provenance or external domain correctness.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import scorer

BASE = Path(__file__).resolve().parent


def load_records(path):
    return load_snapshot(path)[0]


def load_snapshot(path):
    """Return parsed records and the hash of the exact bytes parsed."""
    raw = Path(path).read_bytes()
    records = [scorer.get_kernel().loads_exact(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
    return records, hashlib.sha256(raw).hexdigest()


def unique(rows, name):
    ids = [row['id'] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate ' + name + ' identity')
    return {row['id']:row for row in rows}


def evaluate(tasks, gold, predictions):
    tasks = unique(tasks,'task'); gold = unique(gold,'gold'); predictions = unique(predictions,'prediction')
    if set(tasks) != set(gold) or set(tasks) != set(predictions):
        raise ValueError('task, reference and prediction populations must match exactly')
    if len(tasks) != 560:
        raise ValueError('this endpoint requires the complete revised canonical Core560')
    results = []
    for id in sorted(tasks):
        task, reference, prediction = tasks[id],gold[id],predictions[id]
        if task.get('validation_status') != 'validated' or reference.get('validation_status') != 'validated':
            raise ValueError('unvalidated task/reference: ' + id)
        if (reference['definition_sha256'] != task['definition_sha256']
                or prediction.get('definition_sha256') != task['definition_sha256']):
            raise ValueError('prediction or gold belongs to another contract: ' + id)
        state = prediction.get('status')
        if state == 'abstain':
            if prediction.get('records','missing') is not None:
                raise ValueError('explicit abstention must have records=null')
            # Abstention still requires a valid saved reference. It cannot hide
            # a malformed gold type, cardinality, or declared ordering.
            if not scorer.score(task, reference['records'], reference['records'])['exact']:
                raise ValueError('reference violates its own contract: ' + id)
            result = {'exact':False,'precision':0.0,'recall':0.0,'f1':0.0,'abstained':True}
        elif state == 'answer':
            if type(prediction.get('records')) is not list:
                raise ValueError('answer must provide named records, including [] for formal empty')
            result = scorer.score(task,reference['records'],prediction['records'])
            result['abstained']=False
        else:
            raise ValueError('prediction status must explicitly be answer or abstain')
        results.append({'id':id,'definition_sha256':task['definition_sha256'],**result})
    return {'scope':'complete revised canonical Core; supplied predictions scored under matching revised definitions',
            'n':len(results),'exact':sum(row['exact'] for row in results)/len(results),
            'macro_f1':sum(row['f1'] for row in results)/len(results),
            'explicit_abstentions':sum(row['abstained'] for row in results),'items':results,
            'external_truth_or_expert_validation':False,
            'prediction_generation_provenance_certified':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predictions',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--reference-contract-check',action='store_true',
                        help='label the output as a reference smoke check, never model performance')
    args = parser.parse_args()
    if args.output.resolve() in {args.predictions.resolve(),(BASE/'canonical_tasks.jsonl').resolve(),(BASE/'canonical_reference_gold.jsonl').resolve()}:
        raise ValueError('output cannot overwrite predictions or benchmark inputs')
    tasks, tasks_sha = load_snapshot(BASE/'canonical_tasks.jsonl')
    gold, gold_sha = load_snapshot(BASE/'canonical_reference_gold.jsonl')
    predictions, predictions_sha = load_snapshot(args.predictions)
    result = evaluate(tasks,gold,predictions)
    if args.reference_contract_check:
        references = {row['id']:row for row in gold}
        if not all(row['exact'] for row in result['items']):
            raise ValueError('reference check requires valid exact typed reference matches')
        for row in predictions:
            if row['status'] != 'answer' or row['records'] != references[row['id']]['records']:
                raise ValueError('reference check requires exact saved reference records')
        result['kind']='reference contract smoke check; not model performance'
    else:
        result['kind']='scores for supplied predictions; generation provenance must be reported separately'
    result['input_sha256'] = predictions_sha
    result['canonical_tasks_sha256'] = tasks_sha
    result['canonical_reference_gold_sha256'] = gold_sha
    result['scorer_sha256'] = hashlib.sha256((BASE/'scorer.py').read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='items'},ensure_ascii=False))


if __name__=='__main__':main()
