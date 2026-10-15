#!/usr/bin/env python3
"""Verify the separate FFS-marker contract and its preserved calendar dependency.

Spec: original recent10 FFS-marker Agreement identity contract.
Ontology: retained FFS marker, Agenda order and source-reported Meeting periods.
Cycle: offline verification and optional fresh baseline rebuild.
배경: the earlier CQ017 calendar task remains a distinct dependency.
사용: --existing-sql PATH, or --base-sql PATH --base-ttl PATH --rebuild-dir NEW.
LLM 호출: none; this code never invokes a provider or graph container.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'evaluation'))
import original_scorer
import review_schema
import scorer

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''): h.update(block)
    return h.hexdigest()
def load(p): return json.loads(p.read_text())
def rows(p): return [json.loads(x) for x in p.read_text().splitlines() if x]
def canon(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def main():
    ap=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--existing-sql',type=Path)
    ap.add_argument('--base-sql',type=Path);ap.add_argument('--base-ttl',type=Path);ap.add_argument('--rebuild-dir',type=Path)
    args=ap.parse_args()
    manifest=load(HERE/'manifest.json')
    declared={item['path'] for item in manifest['files']}
    actual={str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file() and p!=HERE/'manifest.json'}
    assert actual==declared,(sorted(actual-declared),sorted(declared-actual))
    for item in manifest['files']:
        p=(HERE/item['path']).resolve();assert p.is_relative_to(HERE.resolve())
        assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],item['path']
    assert sha(HERE/'calendar_source_patch/manifest.json')==manifest['reused_calendar_dependency']['manifest_sha256']
    dependency=[sys.executable,'-B',str(HERE/'calendar_source_patch/verify_rebuild.py')]
    if args.base_sql or args.base_ttl or args.rebuild_dir:
        assert args.base_sql and args.base_ttl and args.rebuild_dir and not args.existing_sql
        dependency += ['--base-sql',str(args.base_sql),'--base-ttl',str(args.base_ttl),'--rebuild-dir',str(args.rebuild_dir)]
    source_result=json.loads(subprocess.check_output(dependency,text=True))
    assert source_result['status']=='pass' and source_result['all192_actual_authored_XML_windows_n']==192
    task=load(HERE/'evaluation/tasks.jsonl');gold=load(HERE/'evaluation/reference_gold.jsonl')
    definition=load(HERE/'original_context/canonical_source_only_definition.json')
    assert task==dict(definition,validation_status='validated')
    assert task['repair_sha256']==gold['repair_sha256']==manifest['repair_sha256']
    criteria=load(HERE/'evaluation/criteria.json')
    for f in task['required_fields']: scorer.get_kernel().field_schema(f)
    for name in ('primary','secondary'):
        review=load(HERE/f'evidence/{name}_exact_original_semantic_review.json')
        review_schema.check_pass(review,task['question_en'],criteria['semantic_units'],criteria_sha=task['criteria_sha256'],identity_key='repair_sha256',identity_sha=task['repair_sha256'])
        assert review['human_author_review_completed'] is False and review['expert_validation_n']==0
    native=rows(HERE/'evidence/full_native_all4635_records.jsonl')
    root_sql=rows(HERE/'evidence/root_independent_full_SQL_all4635_records.jsonl')
    assert len(native)==len(root_sql)==4635 and native==root_sql
    assert all(set(r)=={'resolutionId','content','meetingPeriodEndDate','agendaNumber','sequence'} for r in native)
    actual_gate=load(HERE/'evidence/actual_complete_gate.json')
    assert actual_gate['status']=='source_variant_execution_and_semantic_gates_complete' and actual_gate['all_five_fields_multiset_and_presentation_order_equal'] is True
    assert sha(HERE/'evidence/actual_complete_gate.json')==manifest['actual_complete_gate_sha256']
    projected=[{'resolutionId':r['resolutionId']} for r in native]
    assert len({r['resolutionId'] for r in native})==4635
    assert gold['records']==projected and gold['order_groups']==original_scorer.make_order_groups(task,native,projected)
    controls=load(HERE/'evaluation/actual14_controls.json');assert len(controls)==14
    measured=[]
    for c in controls:
        diagnostic=original_scorer.score(task,projected,c['predictions'],order_groups=gold['order_groups'],diagnostic=True)
        validated=original_scorer.score(task,projected,c['predictions'],order_groups=gold['order_groups'])
        assert diagnostic==c['actual_diagnostic'] and diagnostic['exact'] is c['expected_exact']
        assert {k:v for k,v in diagnostic.items() if k!='diagnostic_only'}=={k:v for k,v in validated.items() if k!='diagnostic_only'}
        measured.append({'name':c['name'],'pass':True,'exact':validated['exact']})
    database=args.existing_sql or (args.rebuild_dir/'RAN1.sqlite' if args.rebuild_dir else None)
    database_checked=False
    if database:
        with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as db:
            db.row_factory=sqlite3.Row
            computed=[dict(r) for r in db.execute((HERE/'evaluation/full_uncapped_SQL.sql').read_text())]
        assert computed==native and Counter(map(canon,computed))==Counter(map(canon,native))
        database_checked=True
    result={'status':'PASS','reused_calendar_manifest_sha256':manifest['reused_calendar_dependency']['manifest_sha256'],
        'source_dependency':source_result,'separate_id':task['id'],'full_native_population_n':4635,
        'all_five_native_and_root_SQL_fields_and_order_equal':True,'actual_controls_n':14,'all_actual_controls_pass':True,
        'optional_SQL_all4635_checked':database_checked,'original_question_frozen_status':'pending',
        'required_fields':['resolutionId'],'content_and_date_auxiliary':True,'raw_report_n':192,'raw_paragraph_window_n':8,
        'whole_report_body_equivalence_claimed':False,'human_author_review_completed':False,'expert_validation_n':0,
        'new_native_API_calls_n':0,'model_performance_claimed':False}
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
