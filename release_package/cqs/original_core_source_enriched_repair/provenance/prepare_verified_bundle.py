#!/usr/bin/env python3
"""Capture/admit one original question on a separately source-enriched snapshot.

No model calls, original source edits or public writes. AI reviews do not stand
for human/expert validation; the new source date is separate from frozen402.
"""
import datetime,hashlib,importlib.util,json,shutil,sqlite3,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
EMP=HERE.parents[1];PREP=EMP.parent;ORIG=PREP/'original_repair'
PUB=Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs')
REG=EMP/'runs/ran2-pack110-enriched/registration'
DEST=HERE/'bundle'
sys.dont_write_bytecode=True
sys.path.insert(0,str(ORIG));sys.path.insert(0,str(PREP))
import continue_original as impl

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n')
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 if DEST.exists():raise ValueError('refuse replacing existing bundle/native attempt')
 task,=rows(HERE/'candidates.jsonl');second,=rows(HERE/'RAN2_pack110_secondary_scope_review.jsonl')
 criteria=read(ORIG/'criteria.json')
 original=next(r for r in rows(PUB/'spectra_cq_v2.0/benchmark.jsonl') if r['id']==task['id'])
 definition={k:task[k] for k in impl.DEFINITION_KEYS}
 assert impl.digest(definition)==task['repair_sha256']
 assert task['question_en']==original['question_en'] and task['original_query']==original['cypher']
 assert task['criteria_sha256']==sha(ORIG/'criteria.json')
 for review in (task['primary_review'],second):
  impl.review_schema.check_pass(review,task['question_en'],criteria['semantic_units'],criteria_sha=task['criteria_sha256'],identity_key='repair_sha256',identity_sha=task['repair_sha256'])
 config=read(REG/'source_config_prepared.json');snapshot=read(HERE/'snapshot_manifest.json');imported=read(config['graph_import_manifest_path'])
 assert imported['status']=='restored_inventory_match'
 assert sha(config['graph_ttl_path'])==snapshot['new_snapshot']['sha256']==imported['source']['sha256']
 assert (imported['measured_counts']['total_nodes'],sum(imported['measured_counts']['rel_counts'].values()))==(156297,939037)
 module=load(REG/'enriched_evaluation.py','enriched_native_capture')
 before=module.graph_guard(config)
 outcome=module.run_cypher(config,task['reference_query'])
 after=module.graph_guard(config)
 assert before==after and outcome['status']=='OK' and outcome['rollback_completed'] and outcome['execution_summary_complete']
 assert outcome['plan_query_type']==outcome['execution_query_type']=='r'
 records=outcome['rows'];assert len(records)==35
 assert all(set(r)=={'crPackId'} and type(r['crPackId']) is str for r in records)
 source_records=rows(HERE/'source_records.jsonl')
 # Original register column role: exact source TSG Tdoc, deduplicated; no gold or previous model input.
 ids=sorted({r['fields']['TSG Tdoc'] for r in source_records})
 assert len(source_records)==240 and len(ids)==35 and sorted(r['crPackId'] for r in records)==ids
 con=sqlite3.connect(Path(config['sql_db_path']).resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
 sqlq="SELECT DISTINCT crPackId FROM CRPack WHERE tsgMeeting='RAN#110' ORDER BY crPackId"
 sqlrecords=[{'crPackId':r[0]} for r in con.execute(sqlq)];con.close()
 assert sqlrecords==[{'crPackId':v} for v in ids]
 checks=impl.checks(task,records,None)
 assert checks and all(c['pass'] for c in checks)
 DEST.mkdir();
 def copy(p,relative):
  dst=DEST/relative;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst);return relative
 for name in ('criteria.json','original_scorer.py','scorer.py','typed_values.py','contract_checks.py','review_schema.py','score_predictions.py','source_pins.json'):
  copy(PUB/'original_core_repair'/name,name)
 copy(HERE/'prepare_verified_bundle.py','provenance/prepare_verified_bundle.py')
 copy(HERE/'verify_enriched_bundle.py','verify_enriched_bundle.py')
 copy(HERE/'rebuild_snapshot.py','rebuild_snapshot.py')
 copy(HERE/'candidates.jsonl','provenance/proposal.jsonl')
 copy(HERE/'RAN2_pack110_secondary_scope_review.jsonl','semantic_evidence/secondary.jsonl')
 copy(REG/'enriched_evaluation.py','provenance/enriched_evaluation.py')
 copy(REG/'source_config_prepared.json','provenance/source_config.json')
 copy(config['graph_import_manifest_path'],'provenance/import_manifest.json')
 copy(HERE/'snapshot_manifest.json','provenance/snapshot_manifest.json')
 copy(HERE/'relational/RAN2.manifest.json','provenance/sql_manifest.json')
 copy(HERE/'native_handoff.json','provenance/native_handoff.json')
 copy(HERE/'CRDB_20260319_CRPack_additions.ttl','source/CRPack_additions.ttl')
 copy(HERE/'source_records.jsonl','source/original_register_rows.jsonl')
 copy(HERE/'original_scope_evidence.json','semantic_evidence/original_scope.json')
 copy(HERE/'missing_pack_original_covers.json','source/missing_pack_original_covers.json')
 copy(HERE/'all_WG_TSG110_source_witness.json','source/all_WG_scope_diagnostic.json')
 copy(HERE/'whole_RAN2_RAN110_source_inventory.jsonl','source/whole_RAN2_RAN110_source_inventory.jsonl')
 copy(HERE/'failed_import_attempt/failure_note.json','provenance/failed_import_attempt_note.json')
 copy(HERE.parent/'RAN2_pack110_candidates/source_vs_frozen_completeness.json','source/source_vs_frozen_completeness.json')
 copy(HERE.parent/'RAN2_pack110_candidates/source_pack110_witness.json','source/source_pack110_witness.json')
 for p in sorted((HERE/'source_downloads').glob('*.zip')):copy(p,'source/downloads/'+p.name)
 write(DEST/'provenance/original_benchmark_record.json',original)
 write(DEST/'provenance/native_reference.json',{'id':task['id'],'repair_sha256':task['repair_sha256'],'query':task['reference_query'],'query_sha256':task['reference_query_sha256'],'source_before':before,'source_after':after,'inventory_unchanged':True,'actual_execution':outcome,'full_rows_available':True,'model_calls':0,'expert_validation_n':0})
 write(DEST/'provenance/sql_reference_check.json',{'query':sqlq,'db_sha256':sha(config['sql_db_path']),'source_snapshot_sha256':snapshot['new_snapshot']['sha256'],'records':sqlrecords,'full_rows_available':True,'read_only':True,'encoding_role':'Same new source-backed CRPack ID/TSG meeting facts; independent SQL projection.'})
 write(DEST/'reference_gold.json',{'id':task['id'],'repair_sha256':task['repair_sha256'],'records':records,'order_groups':None})
 impl.write(DEST/'reference_gold.jsonl',[read(DEST/'reference_gold.json')])
 write(DEST/'scorer_checks.json',{'id':task['id'],'repair_sha256':task['repair_sha256'],'checks':checks,'pass':True})
 completed=dict(task,secondary_review=second,validation_status='validated',admitted=True,
  reference_evidence={'receipt_file':'provenance/native_reference.json','query_sha256':task['reference_query_sha256'],'source_kind':'separate_source_enriched_snapshot','rows':35},
  native_rows=35,projected_records_sha256=impl.digest(records),expert_validation_n=0,human_author_review_completed=False,model_calls=0,
  model_call_scope='No new benchmark predictions in this repair bundle; separate model experiment requires a pre-call protocol.',
  snapshot_sha256=snapshot['new_snapshot']['sha256'],source_enrichment_date='2026-03-19',
  completeness_scope='All 35 pack identifiers in the retained RAN2/RAN110 CRDB source population; not complete real-world submitted archive and not the original frozen graph.')
 impl.write(DEST/'tasks.jsonl',[completed])
 (DEST/'README.md').write_text('# RAN2 CRPack source-enriched repair\n\nOne unchanged original question is admitted on a separately source-enriched snapshot. This is an additive data repair: 9 source-backed CRPack nodes (27 triples, 0 invented relationships) supplement 26 existing RAN#110 packs. The reference removes the undeclared ten-row cap and scores exactly the requested `crPackId` set. All 35 identifiers in the retained RAN2/RAN110 register population are captured from the restored new graph and cross-checked with SQL.\n\nThe original 402-item evidence and graph bytes are preserved. The source register is dated 19 March 2026; this supplement does not claim the same original frozen snapshot, a complete real-world submission archive, human/expert validation, or new model performance. Two separate nonblind AI semantic reviews are recorded under the unchanged criteria. The requested-field scorer controls pass on complete native outputs.\n\nC/D experiment inputs must be the original 240 register rows indexed alongside the retained text corpus; the computed 35-ID audit inventory is not a model appendix. A/B use the new graph and exact additive SQL copy. Whole graph/text coverage or cutoff equality remains unestablished.\n\nRun `python3 -B -S verify_enriched_bundle.py --bundle .` for offline evidence verification.\n')
 manifest={'kind':'One original question on separately source-enriched RAN2 snapshot','admitted_n':1,'cohort_ids':[task['id']],
 'original_question_preserved':True,'repair_sha256':task['repair_sha256'],'criteria_sha256':task['criteria_sha256'],
 'source_snapshot_sha256':snapshot['new_snapshot']['sha256'],'graph_sources':{'RAN2':snapshot['new_snapshot']['sha256']},
 'original_frozen_snapshot_preserved':True,'merged_into_original402':False,'model_predictions_n':0,'expert_validation_n':0,
 'native_rows':35,'actual_scorer_controls':len(checks),'source_records_n':240,'added_nodes':9,'added_triples':27,'added_relationships':0,
 'files':{str(p.relative_to(DEST)):sha(p) for p in sorted(DEST.rglob('*')) if p.is_file()}}
 write(DEST/'manifest.json',manifest)
 print(json.dumps({'status':'VALIDATED_NEW_SNAPSHOT','bundle':str(DEST),'manifest_sha256':sha(DEST/'manifest.json'),'native_rows':35,'controls':len(checks),'model_calls':0}),flush=True)
 # Leave owned target idle before the registered model experiment starts.
 subprocess.run(['docker','stop','--time','20',config['graph_container']],check=True,stdout=subprocess.DEVNULL)

if __name__=='__main__':main()
