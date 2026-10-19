#!/usr/bin/env python3
"""Safely extract immutable saved evaluation and replay prompts/parsers/scores offline."""
import argparse,hashlib,json,subprocess,sys,tarfile
from pathlib import Path,PurePosixPath
ARCHIVE_SHA='f4a2e559dea41413196cbd4ee9c54b4c0f4b4fc3f7dd592276ce59eafec310ab'
VERIFIER_SHA='99870eea8f4e62740d257e56804656b0b41d0e68c70b5d8055fb3056e99391c2'
INNER_MANIFEST_SHA='2d086518ec55433b35e777929a4b0688d0a8ffb34cba25119b7007e4d0163271'
SOURCE_SHA='32911109eb83be5716ae00f41ae17c6a444bc708f81fb77b8171e3c557c14480'
MEMBERS=123
UNCOMPRESSED=2327532
def sha(p):
 no_symlink(p)
 return hashlib.sha256(p.read_bytes()).hexdigest()
def no_symlink(path):
 path=path.absolute()
 for p in (path,*path.parents):
  if p.is_symlink():raise ValueError('Symlink rejected')
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--output',type=Path,required=True);a.add_argument('--source-evidence',type=Path);v=a.parse_args()
 script=Path(__file__).absolute();no_symlink(script);home=script.parent.resolve(strict=True)
 for item in home.rglob('*'):no_symlink(item)
 no_symlink(home/'manifest.json')
 no_symlink(v.output)
 output=v.output.resolve()
 if output.is_relative_to(home):raise ValueError('Extract outside immutable package')
 if output.exists():raise FileExistsError('Choose a new output directory')
 if (output.parent/(output.name+'.verification.json')).exists():raise FileExistsError('Existing sibling replay receipt would be overwritten')
 source_arg=v.source_evidence or home.parent/'source_evidence';no_symlink(source_arg)
 source_evidence=source_arg.resolve(strict=True)
 receipt_path=output.parent/(output.name+'.verification.json')
 if output.is_relative_to(source_evidence) or receipt_path.is_relative_to(source_evidence):raise ValueError('Extraction output and receipt must stay outside source evidence')
 no_symlink(source_evidence/'manifest.json')
 if sha(source_evidence/'manifest.json')!=SOURCE_SHA:raise ValueError('Source manifest changed')
 archive=home/'evidence.tar.gz';no_symlink(archive)
 if sha(archive)!=ARCHIVE_SHA:raise ValueError('Saved evidence archive changed')
 m=json.loads((home/'manifest.json').read_text())
 expected={'cohort':'RAN2_density_finite_dependency_current64_original_query_fourfield_N1','N_per_method':1,'original560_admission_delta':0,'saved_first_attempt_calls':5,'known_provider_reported_cost_USD':'0.497470','macro_F1':{'Text2Cypher':0,'Text2SQL':0,'C':0,'D':0},'quality_retries':0,'transport_retries':0,'human_experts':0,'archive_members':MEMBERS,'uncompressed_bytes':UNCOMPRESSED,'source_manifest_sha256':SOURCE_SHA,'inner_manifest_sha256':INNER_MANIFEST_SHA}
 if json.dumps({k:m[k] for k in expected},sort_keys=True)!=json.dumps(expected,sort_keys=True):raise ValueError('Scientific declarations changed')
 paths=[]
 for e in m['files']:
  r=PurePosixPath(e['path'])
  if r.is_absolute() or not r.parts or any(x in {'.','..'} for x in r.parts):raise ValueError('Unsafe manifest path')
  p=home/r;no_symlink(p)
  if not p.resolve().is_relative_to(home) or sha(p)!=e['sha256'] or p.stat().st_size!=e['bytes']:raise ValueError('Outer package changed')
  paths.append(str(r))
 if len(paths)!=len(set(paths)):raise ValueError('Duplicate manifest path')
 if {str(p.relative_to(home)) for p in home.rglob('*') if p.is_file()}!=set(paths)|{'manifest.json'}:raise ValueError('Unlisted outer file')
 with tarfile.open(archive,'r:gz') as tar:
  members=tar.getmembers();names=set()
  for member in members:
   r=PurePosixPath(member.name)
   if not member.isfile() or r.is_absolute() or not r.parts or any(x in {'.','..'} for x in r.parts) or member.name in names:raise ValueError('Unsafe or duplicate archive member')
   names.add(member.name)
  if len(members)!=MEMBERS or sum(x.size for x in members)!=UNCOMPRESSED:raise ValueError('Archive population changed')
  output.mkdir(parents=True)
  for member in members:
   p=output/member.name;p.parent.mkdir(parents=True,exist_ok=True)
   with tar.extractfile(member) as archive_stream,p.open('xb') as dest:dest.write(archive_stream.read())
 if sha(output/'verify_saved_outputs.py')!=VERIFIER_SHA or sha(output/'manifest.json')!=INNER_MANIFEST_SHA:raise ValueError('Inner verifier/manifest changed')
 result=subprocess.run([sys.executable,'-B','-I',str(output/'verify_saved_outputs.py'),'--source-evidence',str(source_evidence)],capture_output=True,text=True,timeout=120)
 receipt={'archive_sha256':ARCHIVE_SHA,'source_manifest_sha256':SOURCE_SHA,'included_files':len(names),'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'new_API_calls':0,'native_operations':0,'database_connections':0,'FTS_queries':0,'generated_query_executions':0}
 p=output.parent/(output.name+'.verification.json')
 with p.open('x') as f:f.write(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
 if result.returncode:raise RuntimeError(result.stderr)
 print(result.stdout.strip())
if __name__=='__main__':main()
