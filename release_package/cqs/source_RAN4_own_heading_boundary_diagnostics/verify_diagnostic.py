#!/usr/bin/env python3
"""One pinned original-source witness. Standard library; no host fallback."""
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import types
import zipfile

INVENTORY_SHA='aec86c956882e0996246636a2726fd15dc474dbbc79d59a552bd83da80d22402'
INVENTORY_BYTES=1948
PAYLOAD_N=11
SCOPE={'source_id':'RAN4-86bis-own-heading-boundary','related_original_question_id':'RAN4_P3_CQ4-4',
 'whole_question_status':'evidence_pending','source_counterexamples':1,'original_versions':3,
 'frozen_Resolution_node_id':22099,'frozen_REFERENCE_edge_id':24184,'original560_pass_increment':0,
 'human_expert_n':0,'nonblind_AI':True,'independent_package_review_n':0,'API_calls':0,'native_DB_calls':0,
 'claim':'One physical own-heading/frozen-content boundary counterexample; no corrected answer or all-population certification.'}
def sha(b):return hashlib.sha256(b).hexdigest()
def no_links(p):
 p=Path(os.path.abspath(os.fspath(p)))
 for q in [p,*p.parents]:assert not stat.S_ISLNK(os.lstat(q).st_mode),('symlink refused',str(q))
 return p
ENTRY=no_links(__file__)
PACKAGE_ROOT=no_links(ENTRY.parent)
def read(rel):
 assert type(rel) is str and rel and not rel.startswith('/')
 p=Path(rel);assert p.as_posix()==rel and not {'..','.'}&set(p.parts)
 f=no_links(PACKAGE_ROOT/p);assert f.is_file();return f.read_bytes()
def load(rel):
 def pairs(xs):
  d={}
  for k,v in xs:assert k not in d,('duplicate JSON key',k);d[k]=v
  return d
 return json.loads(read(rel),object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
def canon(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def same(a,b):assert canon(a)==canon(b),'exact canonical typed values differ'
def main():
 if sys.flags.optimize != 0: raise RuntimeError('Assertions required; Python -O refused')
 ib=read('immutable_inventory.json');assert len(ib)==INVENTORY_BYTES and sha(ib)==INVENTORY_SHA
 inv=load('immutable_inventory.json');assert set(inv)=={'schema_version','scope','files'}
 assert type(inv['schema_version']) is int and inv['schema_version']==1 and len(inv['files'])==PAYLOAD_N
 files=set()
 for item in inv['files']:
  assert set(item)=={'path','bytes','sha256'} and type(item['bytes']) is int and item['bytes']>=0
  assert item['path'] not in files;files.add(item['path']);b=read(item['path'])
  assert len(b)==item['bytes'] and sha(b)==item['sha256'],('immutable file altered',item['path'])
 expected_files=files|{'immutable_inventory.json','verify_diagnostic.py','manifest.json'}
 expected_dirs={q.as_posix() for f in expected_files for q in Path(f).parents if q.as_posix()!='.'}
 actual_files=set();actual_dirs=set()
 for p in PACKAGE_ROOT.rglob('*'):
  no_links(p);rel=p.relative_to(PACKAGE_ROOT).as_posix()
  if p.is_file():actual_files.add(rel)
  elif p.is_dir():actual_dirs.add(rel)
  else:raise AssertionError(('unsupported package entry',rel))
 same(sorted(actual_files),sorted(expected_files));same(sorted(actual_dirs),sorted(expected_dirs))
 own=read('verify_diagnostic.py')
 same(load('manifest.json'),{'schema_version':1,'id':'RAN4-WI-single-own-heading-boundary',
  'status':'LOCAL_PORTABLE_DIAGNOSTIC_PROPOSAL','artifact_type':'bounded_original_source_boundary_counterexample',
  'scope_and_provenance':SCOPE,
  'immutable_inventory':{'path':'immutable_inventory.json','bytes':INVENTORY_BYTES,'sha256':INVENTORY_SHA,'files':PAYLOAD_N},
  'verifier':{'path':'verify_diagnostic.py','bytes':len(own),'sha256':sha(own)}})
 modules={}
 for name,rel in [('native_reader','code/native_reader.py'),('boundary_rule','code/boundary_rule.py')]:
  m=types.ModuleType(name);m.__file__=str(PACKAGE_ROOT/rel);sys.modules[name]=m;exec(compile(read(rel),m.__file__,'exec'),m.__dict__);modules[name]=m
 proof=load('evidence/observed_boundary.json');mapping=load('provenance/source_mapping.json')
 assert len(mapping['versions'])==len(proof['raw_original_report_replays'])==3
 windows=[]
 for v,expected in zip(mapping['versions'],proof['raw_original_report_replays']):
  archive=read(v['included_archive']);assert len(archive)==v['bytes'] and sha(archive)==v['sha256']
  same({k:v[k] for k in ('path','bytes','sha256')},expected['original_archive'])
  with zipfile.ZipFile(io.BytesIO(archive)) as z:
   infos=[x for x in z.infolist() if x.filename==v['member']['name']];assert len(infos)==1
   info=infos[0];raw=z.read(info)
  same({'name':info.filename,'bytes':len(raw),'CRC32':format(info.CRC,'08x'),'sha256':sha(raw)},v['member'])
  assert len(raw)==info.file_size
  actual=modules['boundary_rule'].witness(raw,modules['native_reader'].__dict__)
  same(actual,expected['source_witness']);windows.append(actual['physical_local_window']['raw_text'])
 assert len(set(windows))==1
 n=proof['frozen_Resolution'];paths=proof['frozen_dependency_paths']
 assert len(paths)==1
 p=paths[0];assert n['node_id']==p['resolution_node_id']==22099
 assert n['resolutionId']==p['resolutionId']=='AGR-86bis-7.10.3-001'
 assert p['reference_edge_id']==24184 and p['tdocNumber']=='R4-1804834' and p['specNumber']=='38.133'
 assert n['content'].splitlines()[0]==modules['boundary_rule'].ANCHOR
 assert 'R4-1804833' in n['content'] and 'R4-1804834' in n['content']
 assert sha(proof['question_en'].encode())==proof['question_sha256']=='6b3b0679cf3334e8aa0bef7733258fcc2e05ea97248338688d73d0a5b1b132f2'
 assert sha(proof['authored_query'].encode())==proof['authored_query_sha256']=='a81576558564f0a7d979077cf3c46769fbb95bcc80e4003b0df4a406e1b62424'
 assert proof['whole_question_status']=='evidence_pending' and type(proof['original560_pass_increment']) is int and proof['original560_pass_increment']==0
 print(json.dumps({'status':'PASS','id':'RAN4-WI-single-own-heading-boundary','original_versions_reopened':3,
  'native_own_document':'R4-1804616','following_document':'R4-1804833','following_CR':'R4-1804834',
  'frozen_REFERENCE_edge_id':24184,'own_Agreement_literal_Tdoc_tokens':0,
  'source_counterexamples':1,'whole_question_status':'evidence_pending','original560_pass_increment':0,
  'human_expert_n':0,'independent_package_review_n':0,'network_or_host_fallback':False,
  'API_calls':0,'native_DB_calls':0,'SQL_FTS_calls':0,'immutable_files':PAYLOAD_N},sort_keys=True))
if __name__=='__main__':main()
