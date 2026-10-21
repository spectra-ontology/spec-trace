"""Explicit analysis API for the predeclared partitioned complete-WI scorer.
The unchanged generic score_predictions.py remains included and is not patched.
"""
import hashlib
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode=True
if sys.flags.optimize:raise ValueError('Enabled checks required')
BASE=Path(__file__).absolute().parent
sys.path[:0]=[str(BASE),str(BASE/'outer_WI_metrics')]
import scorer
import score_predictions_partitioned_dispatch as dispatcher

def read(path):
    return [scorer.get_kernel().loads_exact(s) for s in Path(path).read_text().splitlines() if s.strip()]

def run(tasks_path,gold_path,predictions_path):
    tasks_path,gold_path,predictions_path=map(Path,(tasks_path,gold_path,predictions_path))
    if tasks_path.absolute()!=BASE/'tasks.jsonl' or gold_path.absolute()!=BASE/'reference_gold.jsonl':
        raise ValueError('Use this package exact task/gold declaration')
    tasks,gold,predictions=map(read,(tasks_path,gold_path,predictions_path))
    if len(tasks)!=1 or len(gold)!=1 or len(predictions)!=1:
        raise ValueError('Explicit one-question complete denominator required')
    task,g=tasks[0],gold[0]
    if task['id']!=g['id'] or task['repair_sha256']!=g['repair_sha256']:
        raise ValueError('Task/gold identity differs')
    native=read(BASE/'actual_limited_native_records.jsonl')
    if g['records']!=native:raise ValueError('Native exemplar/gold differs')
    # read_run checks all declared input byte pins and uses diagnostic=False.
    result=dispatcher.read_run(BASE,BASE/'dispatch_declaration.json',predictions_path)
    if result['diagnostic_only'] is not False or result['gold_records']!=5:
        raise ValueError('Non-production or changed complete-WI metric')
    return {'kind':'Explicit declared partitioned top-k supplement; unchanged canonical inner and outer scorers',
      'admitted_n':1,'predicted_n':1,'prediction_file_sha256':hashlib.sha256(predictions_path.read_bytes()).hexdigest(),
      'scoring_dispatch':'explicit_partitioned_top_k_complete_outer_WI_record',
      'full_eligibility_population_is_limited_native_gold':False,'outcomes':[result]}
