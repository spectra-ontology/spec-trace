"""Root-only public projection and staged Git archive verification.

Spec: immutable retained FFS evaluation and original458 frozen index.
Ontology: separate source60 calendar companion; no frozen-scope merge.
Cycle: project exact payload, stage separately, verify only staged Git objects.
배경: extra serialization reproducibility evidence stays outside frozen manifests.
사용: project --worktree W --receipt NEW; then root stages files; verify-staged --worktree W --archive NEW --receipt NEW.
LLM 호출: none. Does not start native containers, call providers, commit or push.
"""
import argparse,hashlib,json,os,shutil,subprocess,sys,tarfile
from pathlib import Path,PurePosixPath
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
EVAL=HERE/'source_variant_evaluation_exports/source60_FFS_Agreement_eval_v2'
REL=Path('release_package/cqs/original_core_source_Meeting_calendar60_FFS_Agreement_evaluation')
EXTRA=Path('release_package/cqs/completed_verification/FFS_source60_serialization_correction_v1')
EVAL_SHA='d505eb09ac68973e9a0cad87f88fc62918d3e9c8eae2f2f38ca5e358a1d2caa0'
COMPANION_SHA='689a76b39f8825a83248c58f8048189d24e22c4655cbb53c3091b8e1598f2e5f'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,x):
 assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def safe(rel):
 p=PurePosixPath(rel);assert not p.is_absolute() and '..' not in p.parts;return Path(*p.parts)
def freeze_core(w):
 p=w/'release_package/cqs/current_core/index_manifest.json';m=load(p)
 assert m['repaired_n']==458 and m['pending_n']==102
 files={str(p.relative_to(w)):sha(p) for p in sorted((w/'release_package/cqs/current_core').rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
 return files
def project(a):
 before=freeze_core(a.worktree);m=load(EVAL/'evaluation_manifest.json')
 assert sha(EVAL/'evaluation_manifest.json')==EVAL_SHA
 dest=a.worktree/REL;assert not dest.exists()
 for rel,v in m['files'].items():
  src=EVAL/safe(rel);assert sha(src)==v['sha256'] and src.stat().st_size==v['bytes']
  dst=dest/safe(rel);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
 shutil.copyfile(EVAL/'evaluation_manifest.json',dest/'evaluation_manifest.json')
 extra=a.worktree/EXTRA;assert not extra.exists();extra.mkdir(parents=True)
 sources=[HERE/'reproduce_FFS_companion_exact_JSONL_correction_v1.py',
 HERE/'FFS_source60_companion_exact_reproduction_receipt_v1.json',
 HERE/'FFS_source60_portable_companion_v4/jsonl_serialization_correction_receipt.json',
 HERE/'prepare_FFS_source60_portable_companion_v4.py',Path(__file__),*a.extra]
 for src in sources:shutil.copyfile(src,extra/src.name)
 files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(extra.iterdir())}
 save(extra/'manifest.json',{'kind':'Ancillary exact FFS serialization reproduction evidence','files':files,
 'immutable_evaluation_manifest_sha256':EVAL_SHA,'immutable_companion_manifest_sha256':COMPANION_SHA,
 'evaluation_runtime_provider_query_source_score_changed':False})
 assert before==freeze_core(a.worktree)
 save(a.receipt,{'status':'PROJECTED_NOT_STAGED_NOT_PUSHED','evaluation_path':str(REL),'evaluation_manifest_sha256':EVAL_SHA,
 'payload_files_n':len(m['files']),'extra_evidence_path':str(EXTRA),'extra_manifest_sha256':sha(extra/'manifest.json'),
 'frozen_current_core_all_file_hashes_unchanged':True,'current_index_n':458,'new_provider_native_calls_n':0})
def run_json(cmd,cwd):
 r=subprocess.run(cmd,cwd=cwd,check=True,text=True,capture_output=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 return json.loads(r.stdout.strip().splitlines()[-1])
def verify(a):
 assert not a.archive.exists() and not a.receipt.exists()
 git=lambda args:subprocess.check_output(['git','-C',str(a.worktree),*args])
 tree=git(['write-tree']).decode().strip()
 index_raw=git(['ls-files','--cached','-z']);paths=[p.decode() for p in index_raw.split(b'\0') if p]
 assert not any('__pycache__' in PurePosixPath(p).parts or p.endswith('.pyc') for p in paths)
 a.archive.mkdir(parents=True)
 process=subprocess.Popen(['git','-C',str(a.worktree),'archive','--format=tar',tree],stdout=subprocess.PIPE)
 extracted=0
 with tarfile.open(fileobj=process.stdout,mode='r|') as tf:
  for member in tf:
   rel=safe(member.name);target=a.archive/rel
   assert not member.issym() and not member.islnk()
   if member.isdir():target.mkdir(parents=True,exist_ok=True);continue
   assert member.isfile() and member.size<100*1024*1024
   target.parent.mkdir(parents=True,exist_ok=True)
   with tf.extractfile(member) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
   extracted+=1
 assert process.wait()==0 and extracted==len(paths)
 before=freeze_core(a.archive);evaluation=a.archive/REL
 assert sha(evaluation/'evaluation_manifest.json')==EVAL_SHA
 assert sha(evaluation/'source_patch/manifest.json')==COMPANION_SHA
 oldcwd=Path.cwd()
 try:
  index_result=run_json([sys.executable,'-B','verify_index.py'],a.archive/'release_package/cqs/current_core')
  eval_result=run_json([sys.executable,'-B','tools/verify_retained_four_methods.py','--evidence','.'],evaluation)
  source_result=run_json([sys.executable,'-B','verify_companion.py'],evaluation/'source_patch')
 finally:os.chdir(oldcwd)
 assert index_result['repaired_n']==458 and index_result['pending_n']==102
 assert eval_result['status']=='PASS' and eval_result['files_verified']==1688 and eval_result['exact_prompt_reconstruction_n']==5 and eval_result['strict_score_replays_n']==4
 assert source_result['status']=='PASS' and source_result['actual_controls_n']==14 and source_result['raw_report_n']==192
 assert source_result['source_dependency']['raw_paragraphs_n']==1536
 assert before==freeze_core(a.archive)
 extra=a.archive/EXTRA;m=load(extra/'manifest.json')
 for p,v in m['files'].items():assert sha(extra/safe(p))==v['sha256'] and (extra/safe(p)).stat().st_size==v['bytes']
 assert tree==git(['write-tree']).decode().strip()
 assert not any(p.suffix=='.pyc' or '__pycache__' in p.parts for p in a.archive.rglob('*'))
 save(a.receipt,{'status':'PASS','git_staged_tree':tree,'git_only_files_n':extracted,'evaluation_manifest_sha256':EVAL_SHA,
 'current_index':index_result,'four_method_exact_prompt_parser_score_replay':eval_result,'source_companion_replay':source_result,
 'frozen_index_files_unchanged_during_replay':True,'generated_caches_n':0,'quality_regeneration_n':0,
 'raw_scope':'192 authentic report members, first8 authored paragraphs each; complete report bodies not claimed',
 'model_performance_is_requested_record_metric_not_query_semantics_or_source_effect':True})
 print(json.dumps({'status':'PASS','receipt':str(a.receipt),'receipt_sha256':sha(a.receipt)}))
def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
 for mode in ('project','verify-staged'):
  q=sub.add_parser(mode);q.add_argument('--worktree',type=Path,required=True);q.add_argument('--receipt',type=Path,required=True)
  if mode=='project':q.add_argument('--extra',type=Path,action='append',default=[])
  if mode=='verify-staged':q.add_argument('--archive',type=Path,required=True)
 a=p.parse_args();project(a) if a.mode=='project' else verify(a)
if __name__=='__main__':main()
