#!/usr/bin/env python3
"""Safely extract immutable saved evaluation and replay prompts/parsers/scores offline."""
import argparse,hashlib,json,subprocess,sys,tarfile
from pathlib import Path,PurePosixPath
ARCHIVE_SHA='f19d3e9e0dbc59932bd6bcf3309b2147d9c3fbfdcc3f1f3e642fb0c204ad7768'
VERIFIER_SHA='47dc8170f3ade836a5d04d745c3830fd7545957565a6772d5f5dbfaff46c75ca'
INNER_MANIFEST_SHA='5bd4dda4c628cabf0963252fa062f78d40614970dca9aecf28eafcbef88c3ec1'
SOURCE_SHA='2832f351d2fce599b0d6d1f3727e605be59dd93cf4e8521f3dbae6d237201d8b'
MEMBERS=183
UNCOMPRESSED=3434313
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def no_symlink(path):
 for p in (path,*path.parents):
  if p.is_symlink():raise ValueError('Symlink rejected')
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--output',type=Path,required=True);a.add_argument('--source-evidence',type=Path);v=a.parse_args()
 home=Path(__file__).resolve().parent
 no_symlink(v.output)
 output=v.output.resolve()
 if output.is_relative_to(home):raise ValueError('Extract outside immutable package')
 if output.exists():raise FileExistsError('Choose a new output directory')
 if (output.parent/(output.name+'.verification.json')).exists():raise FileExistsError('Existing sibling replay receipt would be overwritten')
 source_arg=v.source_evidence or home.parent/'original_core_source_RAN4_source93_exact_DESC';no_symlink(source_arg)
 source_evidence=source_arg.resolve(strict=True)
 if sha(source_evidence/'manifest.json')!=SOURCE_SHA:raise ValueError('Source manifest changed')
 archive=home/'evidence.tar.gz';no_symlink(archive)
 if sha(archive)!=ARCHIVE_SHA:raise ValueError('Saved evidence archive changed')
 m=json.loads((home/'manifest.json').read_text())
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
