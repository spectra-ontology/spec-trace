#!/usr/bin/env python3
"""Complete-denominator scoring and paired uncertainty, with failure gating."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

METHODS = ('text2cypher','text2sql','single_retrieval','iterative_retrieval')
SUCCESS = 'OK'
CONTENT_STATUSES = {'OK','PARTIAL'}


def read(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def unique(rows):
    d = {}
    for row in rows:
        if row['id'] in d: raise ValueError('duplicate ID: '+row['id'])
        d[row['id']] = row
    return d


def gated(raw, status):
    if status in CONTENT_STATUSES and not (status=='PARTIAL' and raw.get('gold_records')==0):
        return dict(raw, execution_status=status, failure_gated=False)
    return dict(raw, precision=0.0, recall=0.0, f1=0.0, exact=False,
                matched_records=0, execution_status=status, failure_gated=True,
                raw_scorer_exact=raw['exact'])


def summary(rows):
    n=len(rows)
    if not n: return {'n':0}
    matched=sum(r['matched_records'] for r in rows)
    ng=sum(r['gold_records'] for r in rows)
    np=sum(r['predicted_records'] for r in rows)
    return {'n':n,'requested_complete_record_macro_f1':sum(r['f1'] for r in rows)/n,
            'exact_output_rate':sum(r['exact'] for r in rows)/n,
            'exact_outputs':sum(r['exact'] for r in rows),
            'execution_status_counts':dict(Counter(r['execution_status'] for r in rows)),
            'failed_n':sum(r['execution_status'] not in CONTENT_STATUSES for r in rows),
            'self_reported_partial_n':sum(r['execution_status']=='PARTIAL' for r in rows),
            'matched_requested_records':matched,'gold_answer_records':ng,
            'predicted_records':np}


def paired(a,b,metric,seed=20261014,replicates=2000):
    ids=sorted(a)
    if ids!=sorted(b):raise ValueError('paired populations differ')
    differences=[float(a[i][metric])-float(b[i][metric]) for i in ids]
    rng=random.Random(seed)
    n=len(ids)
    sampled=sorted(sum(differences[rng.randrange(n)] for _ in range(n))/n
                   for _ in range(replicates))
    return {'n':n,'metric':metric,'difference_a_minus_b':sum(differences)/n,
            'paired_bootstrap_95_percentile_ci':[sampled[int(.025*replicates)],sampled[int(.975*replicates)]],
            'replicates':replicates,'seed':seed,
            'interpretation':'Within this fixed admitted cohort and one model; not sampling over original Core560 or all models.'}


def run(bundle,run_dir):
    sys.path.insert(0,str(bundle))
    reader_path = Path(__file__).with_name('score_predictions_joint_sample.py')
    reader_spec = importlib.util.spec_from_file_location('auth48_explicit_joint_sample_reader', reader_path)
    score_predictions = importlib.util.module_from_spec(reader_spec)
    reader_spec.loader.exec_module(score_predictions)
    tasks=unique(read(bundle/'tasks.jsonl'))
    gold=unique(read(bundle/'reference_gold.jsonl'))
    all_results={}
    tables={}
    for method in METHODS:
        pred_path=run_dir/method/'predictions.jsonl'
        status_path=run_dir/method/'statuses.jsonl'
        predictions=unique(read(pred_path))
        statuses=unique(read(status_path))
        if set(predictions)!=set(tasks) or set(statuses)!=set(tasks):
            raise ValueError(method+' missing or unexpected IDs; partial scores cannot be reported')
        for id,t in tasks.items():
            if statuses[id]['repair_sha256']!=t['repair_sha256']:
                raise ValueError('execution status concerns a different repair')
        raw=score_predictions.run(bundle/'tasks.jsonl',bundle/'reference_gold.jsonl',pred_path)
        (run_dir/method/'raw_scores.json').write_text(json.dumps(raw,indent=2)+'\n')
        results={r['id']:gated(r,statuses[r['id']]['status']) for r in raw['outcomes']}
        all_results[method]=results
        partitions=defaultdict(list)
        for id,r in results.items():
            task=tasks[id]
            partitions['WG:'+id.split('_')[0]].append(r)
            partitions['phase:'+id.split('_')[1]].append(r)
            partitions['collection:'+task['collection']['kind']].append(r)
            partitions['asked_fields:'+('multiple' if len(task['required_fields'])>1 else 'single')].append(r)
            types=[f['type'] for f in task['required_fields']]
            shape=('ranked' if task['collection']['kind']=='top_k_boundary_ties' else
                   'boolean' if types==['boolean'] else
                   'scalar_numeric' if len(types)==1 and types[0] in {'integer','number'} else
                   'grouped_numeric' if any(t in {'integer','number'} for t in types) else 'enumeration')
            partitions['contract_output_type:'+shape].append(r)
        tables[method]={'overall':summary(list(results.values())),
                        'strata':{k:summary(v) for k,v in sorted(partitions.items())},
                        'prediction_sha256':hashlib.sha256(pred_path.read_bytes()).hexdigest(),
                        'statuses_sha256':hashlib.sha256(status_path.read_bytes()).hexdigest()}
        (run_dir/method/'failure_gated_scores.json').write_text(json.dumps(list(results.values()),indent=2)+'\n')
    pairs=[]
    for ai,a in enumerate(METHODS):
        for b in METHODS[ai+1:]:
            for metric in ['f1','exact']:
                pairs.append(dict(a=a,b=b,**paired(all_results[a],all_results[b],metric)))
    output={'kind':'New predictions under a frozen original-question repair contract',
            'admitted_n':len(tasks),'original_registered_n':560,
            'nonadmitted_original_n':560-len(tasks),'tables':tables,'paired':pairs,
            'failure_policy':'Every execution failure or abstention contributes F1=0 and exact=false, including empty-gold items. Successfully parsed self-reported partial content receives record credit; partial empty output never establishes an empty-gold success.',
            'taxonomies':'WG, original phase, collection policy, asked-field count and deterministic contract output shape.',
            'limitations':['One model; no transfer from historical nine-model runs.',
                           'Admitted subset representativeness for Core560 is unestablished.',
                           'Information-access differences prohibit causal claims about graph storage.']}
    (run_dir/'analysis.json').write_text(json.dumps(output,indent=2)+'\n')
    lines=['| Method | N | Complete-record macro F1 | Exact output | Failures |',
           '| --- | ---: | ---: | ---: | ---: |']
    for m in METHODS:
        r=tables[m]['overall']
        lines.append(f"| {m} | {r['n']} | {r['requested_complete_record_macro_f1']:.4f} | {r['exact_outputs']}/{r['n']} | {r['failed_n']} |")
    (run_dir/'performance_table.md').write_text('\n'.join(lines)+'\n')
    return output


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--run-dir',type=Path,required=True)
    a=p.parse_args();r=run(a.bundle,a.run_dir);print(json.dumps({'admitted_n':r['admitted_n'],'methods':list(r['tables'])}))
