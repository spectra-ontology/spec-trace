#!/usr/bin/env python3
"""Build a separate Qualcomm Agreement contract over the unchanged calendar patch.

Spec: exact RAN1_P2_CQ3-4 English and all1094 native-ranked observations.
Ontology: retained Agreement attribution and own reported Meeting periods.
Cycle: source companion preparation; frozen question remains pending.
배경: preserve the earlier CQ017 calendar package byte for byte as a dependency.
사용: run once; the companion reader optionally checks or rebuilds SQLite.
LLM 호출: none; no native, API, public or central mutation is performed.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B = HERE.parent
TASK = B.parents[1]
WORK = HERE / 'P2_CQ3_4_original_calendar_Agreement_source_variant_v1'
PRIOR = B / 'RAN3_RAN4/source60_portable_public_patch_v1'
OUT = HERE / 'Qualcomm_source60_portable_companion_v1'

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''): h.update(block)
    return h.hexdigest()

def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f: json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')

def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    assert not dst.exists()
    shutil.copy2(src, dst)

VERIFIER = '''#!/usr/bin/env python3
"""Verify the separate Qualcomm contract and its preserved calendar dependency.

Spec: original recent10 Qualcomm Agreement identity contract.
Ontology: documentary attribution plus source-reported Meeting periods.
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
    native=rows(HERE/'evidence/full_native_all1094_records.jsonl')
    root_sql=rows(HERE/'evidence/root_independent_full_SQL_all1094_records.jsonl')
    assert len(native)==len(root_sql)==1094 and native==root_sql
    projected=[{'resolutionId':r['resolutionId']} for r in native]
    assert len({r['resolutionId'] for r in native})==1094
    assert gold['records']==projected and gold['order_groups']==original_scorer.make_order_groups(task,native,projected)
    controls=load(HERE/'evaluation/actual15_controls.json');assert len(controls)==15
    measured=[]
    for c in controls:
        diagnostic=original_scorer.score(task,projected,c['input_records'],order_groups=gold['order_groups'],diagnostic=True)
        validated=original_scorer.score(task,projected,c['input_records'],order_groups=gold['order_groups'])
        assert diagnostic==c['actual'] and diagnostic['exact'] is c['expected_exact']
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
        'source_dependency':source_result,'separate_id':task['id'],'full_native_population_n':1094,
        'all_three_native_and_root_SQL_fields_and_order_equal':True,'actual_controls_n':15,'all_actual_controls_pass':True,
        'optional_SQL_all1094_checked':database_checked,'original_question_frozen_status':'pending',
        'required_fields':['resolutionId'],'content_and_date_auxiliary':True,'raw_report_n':192,'raw_paragraph_window_n':8,
        'whole_report_body_equivalence_claimed':False,'human_author_review_completed':False,'expert_validation_n':0,
        'new_native_API_calls_n':0,'model_performance_claimed':False}
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
'''

def main():
    assert not OUT.exists()
    assert sha(PRIOR/'manifest.json')=='90efdbdb3537e270ac3686e1d04167d4b1561f56012cabf32d384af55c7f5823'
    gate_path=WORK/'actual_complete_native_SQL_and15_controls_gate_v1.json'
    assert sha(gate_path)=='c13447043fbf00cd8455f8b34e8c48897d3b75defdaebc3deb8a867411ef7d8b'
    gate=json.loads(gate_path.read_text());assert gate['all_actual_controls_pass'] and gate['full_native_SQL_rows_n']==1094
    OUT.mkdir()
    prior=json.loads((PRIOR/'manifest.json').read_text())
    for item in prior['files']:
        src=PRIOR/item['path'];assert sha(src)==item['sha256'] and src.stat().st_size==item['bytes']
        copy(src,OUT/'calendar_source_patch'/item['path'])
    copy(PRIOR/'manifest.json',OUT/'calendar_source_patch/manifest.json')
    clean=WORK/'source_only_independent_review'
    for src in clean.iterdir():
        assert src.is_file() and src.suffix in {'.json','.jsonl','.ttl','.md'}
        copy(src,OUT/'original_context'/src.name)
    for name in ('score_predictions.py','scorer.py','typed_values.py','original_scorer.py','source_pins.json','contract_checks.py'):
        copy(PRIOR/'evaluation'/name,OUT/'evaluation'/name)
    copy(TASK/'original_repair/review_schema.py',OUT/'evaluation/review_schema.py')
    copy(TASK/'original_repair/criteria.json',OUT/'evaluation/criteria.json')
    definition=json.loads(Path(gate['definition_pin']['path']).read_text())
    task=dict(definition,validation_status='validated')
    (OUT/'evaluation/tasks.jsonl').write_text(json.dumps(task,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')
    copies={
        'evaluation/reference_gold.jsonl':gate['full_projected_gold_pin']['path'],
        'evaluation/actual15_controls.json':gate['controls_input_pin']['path'],
        'evaluation/full_uncapped_SQL.sql':WORK/'native_gate_inputs_v2/RAN1_P2_CQ3-4_independent_full_SQL.sql',
        'evidence/full_native_all1094_records.jsonl':gate['native_all_fields_records_pin']['path'],
        'evidence/root_independent_full_SQL_all1094_records.jsonl':gate['root_independent_SQL_records_pin']['path'],
        'evidence/actual_complete_gate.json':gate_path,
        'evidence/actual_full_native_capture.json':gate['actual_full_native_pin']['path'],
        'evidence/root_independent_SQL_receipt.json':gate['actual_root_independent_SQL_receipt_pin']['path'],
        'evidence/root_full_native_and_independent_SQL_agreement.json':B/'root_evidence/Qualcomm_Agreement_root_full1094_native_and_independent_SQL_agreement_v1.json',
        'evidence/SUBMITTED_BY_Tdoc_Company_endpoint_class_closure.json':WORK/'all_SUBMITTED_BY_original_Tdoc_Company_endpoint_class_closure_v1.json',
    }
    for rel,src in copies.items():copy(Path(src),OUT/rel)
    for review in gate['exact_two_reviews']:
        src=Path(review['pin']['path']);assert sha(src)==review['pin']['sha256']
        copy(src,OUT/f"evidence/{review['role']}_exact_original_semantic_review.json")
    (OUT/'verify_companion.py').write_text(VERIFIER)
    compile(VERIFIER,str(OUT/'verify_companion.py'),'exec')
    copy(Path(__file__),OUT/'evidence/companion_preparation_reader.py')
    (OUT/'README.md').write_text('''# Separate Qualcomm Agreement calendar companion

This companion answers the unchanged question, "List Qualcomm's 10 most recent agreements." It uses the retained Agreement→REFERENCES→Tdoc→SUBMITTED_BY→Company attribution and own reported Meeting periods. This is documentary participation; ownership, leadership, causal contribution, approval and within-meeting chronology are not established.

The earlier source60 calendar package is preserved byte for byte under `calendar_source_patch/`. Its manifest is `90efdbdb3537e270ac3686e1d04167d4b1561f56012cabf32d384af55c7f5823`. Its CQ017 task, 3,041-record reference and earlier model evaluation remain a separate case. The companion's `evaluation/` contains the Qualcomm task, complete 1,094-record reference and date boundary groups, and 15 actual typed controls. Four Agreements are strictly newer than the boundary; any six of the 28 Agreements in the cutoff meeting complete the requested ten. Required output is Agreement identity; content and date are auxiliary context. A particular lexical order within a tied meeting is not required.

The reused source evidence provides exactly eight authored paragraphs from each of 192 retained report members. Those windows contain all witnesses used for the 60 Meeting dates. Complete report body equivalence is unestablished. The frozen original question remains pending and this case is not added to the frozen question count. No model performance, human author review or expert validation is claimed by this source preparation.

Run `python -B verify_companion.py` for packaged source, contract and control checks. To rebuild, provide `--base-sql <baseline RAN1.sqlite> --base-ttl <baseline RAN1-body.ttl> --rebuild-dir <new directory>`. The preserved dependency rebuild checks every original column in all 89 tables and preserves the original RDF byte prefix; the companion then checks all three fields of all 1,094 native Agreement observations against the rebuilt SQL. `--existing-sql <source60 RAN1.sqlite>` checks an existing additive snapshot read-only. These commands do not invoke a model or a graph container.

Historical absolute paths remain immutable provenance. Payloads and their dependency manifest are pinned by the companion manifest. Model inputs and paid retained outputs will be packaged separately after root execution; reference queries, gold and these reviews are not retrieval inputs.
''')
    files=[{'path':str(p.relative_to(OUT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file()]
    assert not any('__pycache__' in x['path'] or x['path'].endswith('.pyc') for x in files)
    save(OUT/'manifest.json',{'kind':'Separate Qualcomm Agreement contract over preserved source60 dependency','id':task['id'],
        'repair_sha256':task['repair_sha256'],'actual_complete_gate_sha256':sha(gate_path),
        'reused_calendar_dependency':{'path':'calendar_source_patch/manifest.json','manifest_sha256':sha(PRIOR/'manifest.json'),'payload_bytes_unchanged':True,'original_case_id':'RAN1_P3_CQ017'},
        'required_fields':['resolutionId'],'auxiliary_fields':['content','meetingPeriodEndDate'],
        'full_native_population_n':1094,'actual_controls_n':15,'raw_report_n':192,'raw_paragraph_window_n':8,
        'whole_report_body_equivalence_claimed':False,'frozen_original_question_status':'pending',
        'frozen_original_index_modified_or_merged':False,'human_author_review_completed':False,'expert_validation_n':0,
        'child_API_native_public_calls_n':0,'files':files})
    print(json.dumps({'path':str(OUT),'manifest_sha256':sha(OUT/'manifest.json'),'payload_files_n':len(files),'payload_bytes':sum(x['bytes'] for x in files)},ensure_ascii=False))

if __name__=='__main__':main()
