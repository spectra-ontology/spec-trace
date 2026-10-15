#!/usr/bin/env python3
"""Spec: root-only staged Git-only public463/AUTH11 saved-output verification.
Ontology: original frozen graph contracts, source records and exact-share hooks.
Cycle: KDD2027 Datasets and Benchmarks Cycle1.
배경: a fresh staged archive must reproduce the three admitted cases only.
사용: root invokes after staging; no local untracked fallback or network.
LLM 호출: none; no research database or native graph query is executed.
"""
import argparse,datetime,hashlib,json,subprocess,sys,tarfile
from pathlib import Path
sys.dont_write_bytecode=True
BUNDLE_SHA='861e9cf2a6d5c64b5682960c74d0555a4ccceb010e29ad4c9744fcb1f6cd65db'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(q):
 w=q.worktree.resolve();out=q.out_dir.resolve();receipt=q.receipt.resolve();eval_sha=q.expected_evaluation_manifest
 assert len(eval_sha)==64 and not out.exists() and not receipt.exists(),'Preserve prior attempts'
 index_rel='release_package/cqs/current_core';repair_rel='release_package/cqs/original_core_overnight_repairs11';eval_rel='release_package/cqs/original_core_overnight_evaluation11'
 index=json.loads(subprocess.check_output(['git','show',':'+index_rel+'/index_manifest.json'],cwd=w))
 assert(index['repaired_n'],index['pending_n'])==(463,97) and index['repair_classes']=={'scorer_only':117,'query_and_scorer':346}
 assert index['cohort_manifest_pins']['original_core_overnight_repairs11']==BUNDLE_SHA
 assert set(index['latest_scope']['cohort_ids'])=={'RAN1_P1_CQ2-6','RAN1_P2_CQ3-2','RAN2_P2_CQ3-1'} and index['latest_scope']['central60_excluded'] is True
 roots=list(dict.fromkeys([index_rel,'README.md',*['release_package/cqs/'+k for k in index['cohort_manifest_pins']],eval_rel]))
 tree=subprocess.check_output(['git','write-tree'],cwd=w,text=True).strip();out.mkdir(parents=True)
 proc=subprocess.Popen(['git','archive',tree,*roots],cwd=w,stdout=subprocess.PIPE)
 with tarfile.open(fileobj=proc.stdout,mode='r|') as archive:archive.extractall(out,filter='data')
 assert proc.wait()==0
 def run(args):return json.loads(subprocess.check_output([sys.executable,'-B','-S',*args],cwd=out,text=True))
 assert sha(out/repair_rel/'manifest.json')==BUNDLE_SHA and sha(out/eval_rel/'manifest.json')==eval_sha
 current=run([index_rel+'/verify_index.py']);assert current['status']=='PASS' and(current['repaired_n'],current['pending_n'])==(463,97)
 evaluation=run([eval_rel+'/runtime/verify_authorized_incremental11_evaluation_v3.py','--evidence',eval_rel,'--bundle',repair_rel])
 assert evaluation['status']=='PASS' and evaluation['additional_n']==3 and evaluation['method_items']==12
 assert evaluation['actual_additional_controls_n']==50 and evaluation['contract_verification']['actual_scorer_controls']==23
 assert evaluation['received_http200_response_n']==evaluation['model_request_n']==15 and evaluation['unknown_cost_attempts']==0
 controls=run([repair_rel+'/verify_saved_controls.py','--bundle',repair_rel]);assert controls['status']=='PASS' and controls['additional_saved_controls_n']==50
 assert controls['source_free_boundary_and_lexical_controls_n']==7
 prompt_out=out.parent/(out.name+'_exact15_prompts_and12parsers.json');assert not prompt_out.exists()
 prompts=run([index_rel+'/completed_verification/verify_incremental11_exact_prompts_and_parsers_v1.py','--evidence',eval_rel,'--out',str(prompt_out)])
 assert prompts['prompt_reconstruction_n']==15 and prompts['output_parser_replay_n']==12 and prompts['structured_generation_parser_replay_n']==6
 assert prompts['evaluation_manifest_sha256']==eval_sha
 assert not list(out.rglob('*.pyc')) and not list(out.rglob('__pycache__'))
 files={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
 result=dict(status='PASS_GIT_ONLY_PUBLIC463_AUTH11_EXACT15_PROMPTS_ALL12_PARSERS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),tree=tree,roots=roots,files_n=len(files),files=files,index=current,evaluation=evaluation,prompts=prompts,additional50controls=controls,generic_control_replays_n=23,additional_saved_control_replays_n=50,separate_synthetic_boundary_lexical_controls_n=7,new_API_calls=0,new_native_calls=0,research_database_queries=0,central60_excluded=True,prior_cohorts_or_source_variants_changed=False)
 receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in {'files','evaluation','index','additional50controls'}},ensure_ascii=False))
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__)
 for x in ('worktree','out-dir','receipt'):a.add_argument('--'+x,type=Path,required=True)
 a.add_argument('--expected-evaluation-manifest',required=True);main(a.parse_args())
