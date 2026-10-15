#!/usr/bin/env python3
"""Root-only full offline replay of public458 through fresh staged Git-only files.
Untracked/ignored dependencies cannot mask omissions. No network/API/DB queries.
"""
import argparse,datetime,hashlib,json,subprocess,sys,tarfile
from pathlib import Path
sys.dont_write_bytecode=True
BUNDLE_SHA='e977f99339e55fdcdf3db5f08edc3498ba950f082cd926af744412e8227012dc'
EVAL_SHA='f76fad56f67e35b2ed49add8a545aeab7f41ad7ace28ca23fbf07afe8834026d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(w,out,receipt):
 assert not out.exists() and not receipt.exists(),'preserve earlier attempts'
 index_rel='release_package/cqs/current_core';repair_rel='release_package/cqs/original_core_overnight_repairs9';eval_rel='release_package/cqs/original_core_overnight_evaluation9'
 index=json.loads(subprocess.check_output(['git','show',':'+index_rel+'/index_manifest.json'],cwd=w))
 assert(index['repaired_n'],index['pending_n'])==(458,102)
 assert index['repair_classes']=={'scorer_only':117,'query_and_scorer':341}
 assert index['cohort_manifest_pins']['original_core_overnight_repairs9']==BUNDLE_SHA
 roots=list(dict.fromkeys([index_rel,'README.md',*['release_package/cqs/'+k for k in index['cohort_manifest_pins']],eval_rel]))
 tree=subprocess.check_output(['git','write-tree'],cwd=w,text=True).strip();out.mkdir(parents=True)
 proc=subprocess.Popen(['git','archive',tree,*roots],cwd=w,stdout=subprocess.PIPE)
 with tarfile.open(fileobj=proc.stdout,mode='r|') as archive:archive.extractall(out,filter='data')
 assert proc.wait()==0
 def run(args):return json.loads(subprocess.check_output([sys.executable,'-B','-S',*args],cwd=out,text=True))
 assert sha(out/repair_rel/'manifest.json')==BUNDLE_SHA and sha(out/eval_rel/'manifest.json')==EVAL_SHA
 current=run([index_rel+'/verify_index.py']);assert current['status']=='PASS' and(current['repaired_n'],current['pending_n'])==(458,102)
 evaluation=run([eval_rel+'/runtime/verify_authorized_incremental9_evaluation_v3.py','--evidence',eval_rel,'--bundle',repair_rel])
 assert evaluation['status']=='PASS' and evaluation['additional_n']==6 and evaluation['method_items']==24
 assert evaluation['actual_additional_controls_n']==77 and evaluation['contract_verification']['status']=='PASS'
 assert evaluation['received_http200_response_n']==evaluation['model_request_n']==30
 assert evaluation['unknown_cost_attempts']==0 and abs(evaluation['known_actual_cost_usd']-1.6716)<1e-10
 controls=run([repair_rel+'/verify_saved_controls.py','--bundle',repair_rel]);assert controls['status']=='PASS' and controls['additional_saved_controls_n']==77 and controls['synthetic_source_free_controls_n']==12
 prompt_out=out.parent/(out.name+'_exact30_prompts_and24parsers.json');assert not prompt_out.exists()
 prompts=run([index_rel+'/completed_verification/verify_incremental9_exact_prompts_and_parsers_v1.py','--evidence',eval_rel,'--out',str(prompt_out)])
 assert prompts['prompt_reconstruction_n']==30 and prompts['output_parser_replay_n']==24 and prompts['structured_generation_parser_replay_n']==12
 assert prompts['evaluation_manifest_sha256']==EVAL_SHA
 assert not list(out.rglob('*.pyc')) and not list(out.rglob('__pycache__'))
 files={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
 result=dict(status='PASS_GIT_ONLY_PUBLIC458_AUTH9_EXACT30_PROMPTS_ALL24_PARSERS_126CONTROLS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),tree=tree,roots=roots,files_n=len(files),files=files,index=current,evaluation=evaluation,prompts=prompts,additional77controls=controls,new_API_calls=0,new_native_calls=0,prior_cohorts_or_source_variants_changed=False)
 receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in {'files','evaluation','index','additional77controls'}},ensure_ascii=False))
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__)
 for x in ('worktree','out-dir','receipt'):a.add_argument('--'+x,type=Path,required=True)
 q=a.parse_args();main(q.worktree.resolve(),q.out_dir.resolve(),q.receipt.resolve())
