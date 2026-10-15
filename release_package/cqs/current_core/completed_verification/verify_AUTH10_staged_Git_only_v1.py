#!/usr/bin/env python3
"""Root-only full offline public460/AUTH10 replay through fresh staged Git-only files.
No network, research database/native execution, model or API calls. Temporary
synthetic SQLite checks inside the declared source-free suite remain explicit.
"""
import argparse,datetime,hashlib,json,subprocess,sys,tarfile
from pathlib import Path
sys.dont_write_bytecode=True
BUNDLE_SHA='5634343419e18c48b3fb0083375ae972c14dc8515bbec8788dc71487d006d59b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(q):
 w=q.worktree.resolve();out=q.out_dir.resolve();receipt=q.receipt.resolve();eval_sha=q.expected_evaluation_manifest
 assert len(eval_sha)==64 and not out.exists() and not receipt.exists(),'preserve earlier attempts'
 index_rel='release_package/cqs/current_core';repair_rel='release_package/cqs/original_core_overnight_repairs10';eval_rel='release_package/cqs/original_core_overnight_evaluation10'
 index=json.loads(subprocess.check_output(['git','show',':'+index_rel+'/index_manifest.json'],cwd=w))
 assert(index['repaired_n'],index['pending_n'])==(460,100)
 assert index['repair_classes']=={'scorer_only':117,'query_and_scorer':343}
 assert index['cohort_manifest_pins']['original_core_overnight_repairs10']==BUNDLE_SHA
 roots=list(dict.fromkeys([index_rel,'README.md',*['release_package/cqs/'+k for k in index['cohort_manifest_pins']],eval_rel]))
 tree=subprocess.check_output(['git','write-tree'],cwd=w,text=True).strip();out.mkdir(parents=True)
 proc=subprocess.Popen(['git','archive',tree,*roots],cwd=w,stdout=subprocess.PIPE)
 with tarfile.open(fileobj=proc.stdout,mode='r|') as archive:archive.extractall(out,filter='data')
 assert proc.wait()==0
 def run(args):return json.loads(subprocess.check_output([sys.executable,'-B','-S',*args],cwd=out,text=True))
 assert sha(out/repair_rel/'manifest.json')==BUNDLE_SHA and sha(out/eval_rel/'manifest.json')==eval_sha
 current=run([index_rel+'/verify_index.py']);assert current['status']=='PASS' and(current['repaired_n'],current['pending_n'])==(460,100)
 evaluation=run([eval_rel+'/runtime/verify_authorized_incremental10_evaluation_v1.py','--evidence',eval_rel,'--bundle',repair_rel])
 assert evaluation['status']=='PASS' and evaluation['additional_n']==2 and evaluation['method_items']==8
 assert evaluation['actual_additional_controls_n']==63 and evaluation['contract_verification']['actual_scorer_controls']==15
 assert evaluation['received_http200_response_n']==evaluation['model_request_n']==10 and evaluation['unknown_cost_attempts']==0
 controls=run([repair_rel+'/verify_saved_controls.py','--bundle',repair_rel]);assert controls['status']=='PASS' and controls['additional_saved_controls_n']==63
 assert controls['synthetic_tie_and_source_free_runtime_controls_n']==31 and controls['additional_actual_counts_include_overlap'] is True
 prompt_out=out.parent/(out.name+'_exact10_prompts_and8parsers.json');assert not prompt_out.exists()
 prompts=run([index_rel+'/completed_verification/verify_incremental10_exact_prompts_and_parsers_v1.py','--evidence',eval_rel,'--out',str(prompt_out)])
 assert prompts['prompt_reconstruction_n']==10 and prompts['output_parser_replay_n']==8 and prompts['structured_generation_parser_replay_n']==4
 assert prompts['evaluation_manifest_sha256']==eval_sha
 assert not list(out.rglob('*.pyc')) and not list(out.rglob('__pycache__'))
 files={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
 result=dict(status='PASS_GIT_ONLY_PUBLIC460_AUTH10_EXACT10_PROMPTS_ALL8_PARSERS_SAVED_CONTROLS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),tree=tree,roots=roots,files_n=len(files),files=files,index=current,evaluation=evaluation,prompts=prompts,additional63controls=controls,generic_control_replays_n=15,additional_saved_control_replays_n=63,source_free_tie_and_runtime_checks_n=31,control_sets_overlap=True,new_API_calls=0,new_native_calls=0,research_database_queries=0,prior_cohorts_or_source_variants_changed=False)
 receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in {'files','evaluation','index','additional63controls'}},ensure_ascii=False))
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__)
 for x in ('worktree','out-dir','receipt'):a.add_argument('--'+x,type=Path,required=True)
 a.add_argument('--expected-evaluation-manifest',required=True);main(a.parse_args())
