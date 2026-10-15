#!/usr/bin/env python3
"""Spec: root-only staged Git-only public467/AUTH14 saved-output verification.
Ontology: original frozen graph contracts, source records and exact-share hooks.
Cycle: KDD2027 Datasets and Benchmarks Cycle1.
배경: a fresh staged archive must reproduce the one admitted case only.
사용: root invokes after staging; no local untracked fallback or network.
LLM 호출: none; no research database or native graph query is executed.
"""
import argparse,datetime,hashlib,json,subprocess,sys,tarfile
from pathlib import Path
sys.dont_write_bytecode=True
BUNDLE_SHA=None
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(q):
 global BUNDLE_SHA
 BUNDLE_SHA=q.expected_bundle_manifest;assert len(BUNDLE_SHA)==64
 w=q.worktree.resolve();out=q.out_dir.resolve();receipt=q.receipt.resolve();eval_sha=q.expected_evaluation_manifest
 assert len(eval_sha)==64 and not out.exists() and not receipt.exists(),'Preserve prior attempts'
 index_rel='release_package/cqs/current_core';repair_rel='release_package/cqs/original_core_overnight_repairs14';eval_rel='release_package/cqs/original_core_overnight_evaluation14'
 index=json.loads(subprocess.check_output(['git','show',':'+index_rel+'/index_manifest.json'],cwd=w))
 assert(index['repaired_n'],index['pending_n'])==(467,93) and sum(index['repair_classes'].values())==467
 assert index['cohort_manifest_pins']['original_core_overnight_repairs14']==BUNDLE_SHA
 assert set(index['latest_scope']['cohort_ids'])=={'RAN1_P2_CQ5-6'} and index['latest_scope']['central63_included'] is True
 roots=list(dict.fromkeys([index_rel,'README.md',*['release_package/cqs/'+k for k in index['cohort_manifest_pins']],eval_rel]))
 tree=subprocess.check_output(['git','write-tree'],cwd=w,text=True).strip();out.mkdir(parents=True)
 proc=subprocess.Popen(['git','archive',tree,*roots],cwd=w,stdout=subprocess.PIPE)
 with tarfile.open(fileobj=proc.stdout,mode='r|') as archive:archive.extractall(out,filter='data')
 assert proc.wait()==0
 def run(args):return json.loads(subprocess.check_output([sys.executable,'-B','-S',*args],cwd=out,text=True))
 assert sha(out/repair_rel/'manifest.json')==BUNDLE_SHA and sha(out/eval_rel/'manifest.json')==eval_sha
 current=run([index_rel+'/verify_index.py']);assert current['status']=='PASS' and(current['repaired_n'],current['pending_n'])==(467,93)
 evaluation=run([eval_rel+'/runtime/verify_authorized_incremental14_evaluation_v1.py','--evidence',eval_rel,'--bundle',repair_rel])
 assert evaluation['status']=='PASS' and evaluation['additional_n']==1 and evaluation['method_items']==4
 assert evaluation['actual_additional_controls_n']==12 and evaluation['contract_verification']['actual_scorer_controls']==10
 assert evaluation['received_http200_response_n']==evaluation['model_request_n']==5 and evaluation['unknown_cost_attempts']==0
 controls=run([repair_rel+'/verify_saved_controls.py','--bundle',repair_rel]);assert controls['status']=='PASS' and controls['additional_saved_controls_n']==12 and controls['actual_population_control_replays_n']==12 and controls['separate_synthetic_control_replays_n']==0
 prompt_out=out.parent/(out.name+'_exact5_prompts_and4parsers.json');assert not prompt_out.exists()
 prompts=run([index_rel+'/completed_verification/verify_incremental14_exact_prompts_and_parsers_v1.py','--evidence',eval_rel,'--out',str(prompt_out)])
 assert prompts['prompt_reconstruction_n']==5 and prompts['output_parser_replay_n']==4 and prompts['structured_generation_parser_replay_n']==2
 assert prompts['evaluation_manifest_sha256']==eval_sha
 assert not list(out.rglob('*.pyc')) and not list(out.rglob('__pycache__'))
 files={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
 result=dict(status='PASS_GIT_ONLY_PUBLIC467_AUTH14_EXACT5_PROMPTS_ALL4_PARSERS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),tree=tree,roots=roots,files_n=len(files),files=files,index=current,evaluation=evaluation,prompts=prompts,additional12controls=controls,generic_control_replays_n=10,additional_saved_control_replays_n=12,new_API_calls=0,new_native_calls=0,research_database_queries=0,central63_included=True,prior_cohorts_or_source_variants_changed=False)
 receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in {'files','evaluation','index','additional12controls'}},ensure_ascii=False))
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__)
 for x in ('worktree','out-dir','receipt'):a.add_argument('--'+x,type=Path,required=True)
 a.add_argument('--expected-evaluation-manifest',required=True);a.add_argument('--expected-bundle-manifest',required=True);main(a.parse_args())
