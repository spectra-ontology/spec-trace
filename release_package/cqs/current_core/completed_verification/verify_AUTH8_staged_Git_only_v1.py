#!/usr/bin/env python3
"""Read and replay staged public452 files through a fresh Git-only archive.

Root invokes this after staging. No network, API or database execution occurs.
Untracked and ignored local files cannot supply missing public dependencies.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
sys.dont_write_bytecode=True
BUNDLE_SHA='a700010a5f4fcaeb51e9265be7a052629d891c03aed30bc120879a27d4b46205'
EVAL_SHA='5346d0bb52f4a2179431443f4c58299bec899d5f8ee08715fccd0e968ca274db'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(w,out,receipt):
    assert not out.exists() and not receipt.exists(), 'preserve earlier attempts'
    index_rel='release_package/cqs/current_core'
    index=json.loads(subprocess.check_output(['git','show',':'+index_rel+'/index_manifest.json'],cwd=w))
    assert index['repaired_n']==452 and index['pending_n']==108
    assert index['repair_classes']=={'scorer_only':117,'query_and_scorer':335}
    repair_rel='release_package/cqs/original_core_overnight_repairs8'
    eval_rel='release_package/cqs/original_core_overnight_evaluation8'
    assert index['cohort_manifest_pins']['original_core_overnight_repairs8']==BUNDLE_SHA
    roots=list(dict.fromkeys([index_rel,'README.md',*['release_package/cqs/'+k for k in index['cohort_manifest_pins']],eval_rel]))
    tree=subprocess.check_output(['git','write-tree'],cwd=w,text=True).strip()
    out.mkdir(parents=True)
    proc=subprocess.Popen(['git','archive',tree,*roots],cwd=w,stdout=subprocess.PIPE)
    with tarfile.open(fileobj=proc.stdout,mode='r|') as archive:archive.extractall(out,filter='data')
    assert proc.wait()==0
    def run(args):return json.loads(subprocess.check_output([sys.executable,'-B','-S',*args],cwd=out,text=True))
    assert sha(out/repair_rel/'manifest.json')==BUNDLE_SHA
    assert sha(out/eval_rel/'manifest.json')==EVAL_SHA
    current=run([index_rel+'/verify_index.py'])
    assert current['status']=='PASS' and current['repaired_n']==452 and current['pending_n']==108
    evaluation=run([eval_rel+'/runtime/verify_authorized_incremental8_evaluation_v3.py','--evidence',eval_rel,'--bundle',repair_rel])
    assert evaluation['status']=='PASS' and evaluation['actual_basic_controls_n']==7 and evaluation['actual_additional_controls_n']==10 and evaluation['actual_total_controls_n']==17
    assert evaluation['received_http200_response_n']==evaluation['model_request_n']==5
    controls=run([index_rel+'/completed_verification/verify_authorized_incremental8_additional_Tdoc_unit_controls_v1.py','--bundle',repair_rel])
    assert controls['all_pass'] is True and controls['controls_n']==17
    prompt_out=out.parent/(out.name+'_exact5_prompts_and4parsers.json')
    assert not prompt_out.exists()
    prompts=run([index_rel+'/completed_verification/verify_incremental8_exact5_prompts_all4_parsers_v1.py','--evidence',eval_rel,'--out',str(prompt_out)])
    assert prompts['prompt_reconstruction_n']==5 and prompts['evaluation_manifest_sha256']==EVAL_SHA
    assert prompts['native_read_summary_and_rollback_verified'] is True
    assert not list(out.rglob('*.pyc')) and not list(out.rglob('__pycache__'))
    files={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
    result={'status':'PASS_GIT_ONLY_PUBLIC452_AUTH8_EXACT5_PROMPTS_ALL4_PARSERS_SCORES_AND17_CONTROLS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tree':tree,'roots':roots,'files_n':len(files),'files':files,'index':current,'evaluation':evaluation,'prompts':prompts,'actual17controls':controls,'new_API_calls':0,'new_native_calls':0,'prior_cohorts_or_source_variants_changed':False}
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'files','evaluation','index','actual17controls'}},ensure_ascii=False))
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for x in ('worktree','out-dir','receipt'):ap.add_argument('--'+x,type=Path,required=True)
    a=ap.parse_args();main(a.worktree.resolve(),a.out_dir.resolve(),a.receipt.resolve())
