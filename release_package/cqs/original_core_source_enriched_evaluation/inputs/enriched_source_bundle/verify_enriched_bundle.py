#!/usr/bin/env python3
"""Offline verifier of source-enriched repair, not historical model results."""
import argparse,hashlib,io,json,sys,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def read(p):return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
KEYS=('id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved')

def verify(base):
 base=base.resolve();m=load(base/'manifest.json')
 actual={str(p.relative_to(base)) for p in base.rglob('*') if p.is_file() and p.name!='manifest.json'}
 if actual!=set(m['files']):raise ValueError('manifest file set mismatch')
 for name,h in m['files'].items():
  p=(base/name).resolve()
  if not p.is_relative_to(base) or sha(p)!=h:raise ValueError('manifest hash mismatch:'+name)
 sys.path.insert(0,str(base));sys.dont_write_bytecode=True
 import original_scorer,review_schema
 from contract_checks import checks
 t,=read(base/'tasks.jsonl');original=load(base/'provenance/original_benchmark_record.json');criteria=load(base/'criteria.json')
 if t['question_en']!=original['question_en'] or t['original_query']!=original['cypher'] or t['original_question_preserved'] is not True:raise ValueError('original bytes changed')
 if hashlib.sha256(canonical({k:t[k] for k in KEYS}).encode()).hexdigest()!=t['repair_sha256']:raise ValueError('definition pin differs')
 if t['criteria_sha256']!=sha(base/'criteria.json'):raise ValueError('criteria changed')
 for r in (t['primary_review'],t['secondary_review']):review_schema.check_pass(r,t['question_en'],criteria['semantic_units'],criteria_sha=t['criteria_sha256'],identity_key='repair_sha256',identity_sha=t['repair_sha256'])
 n=load(base/'provenance/native_reference.json');e=n['actual_execution'];g=load(base/'reference_gold.json');sql=load(base/'provenance/sql_reference_check.json')
 if n['query']!=t['reference_query'] or n['query_sha256']!=hashlib.sha256(t['reference_query'].encode()).hexdigest():raise ValueError('native query changed')
 if n['source_before']!=n['source_after'] or n['inventory_unchanged'] is not True:raise ValueError('source guards changed')
 if not (e['status']=='OK' and e['complete'] and not e['truncated'] and e['execution_summary_complete'] and e['rollback_completed'] and e['plan_query_type']==e['execution_query_type']=='r'):raise ValueError('native incomplete/unsafe')
 imported=load(base/'provenance/import_manifest.json');snapshot=load(base/'provenance/snapshot_manifest.json')
 if imported['status']!='restored_inventory_match' or imported['source']['sha256']!=m['source_snapshot_sha256'] or n['source_before']['ttl_sha256']!=m['source_snapshot_sha256']:raise ValueError('wrong snapshot')
 if sha(base/'provenance/import_manifest.json')!=n['source_before']['import_manifest_sha256']:raise ValueError('wrong import receipt')
 if m['source_snapshot_sha256']!=snapshot['new_snapshot']['sha256'] or snapshot['new_snapshot']['bytes']!=imported['source']['bytes']:raise ValueError('new source pin mismatch')
 if len(snapshot['node_additions'])!=9 or m['added_nodes']!=9 or m['added_relationships']!=0:raise ValueError('source patch scope changed')
 sources=read(base/'source/original_register_rows.jsonl');sourceids={r['fields']['TSG Tdoc'] for r in sources}
 if len(sources)!=240 or len(sourceids)!=35:raise ValueError('source population changed')
 if any(r['fields']['Meeting TSG-level']!='3GPPRAN#110' or not r['fields']['Meeting WG-level'].startswith('3GPP RAN2#') for r in sources):raise ValueError('raw source roles/scope mismatch')
 if e['rows']!=g['records'] or {r['crPackId'] for r in e['rows']}!=sourceids or len(e['rows'])!=35:raise ValueError('native/source/gold mismatch')
 if sql['records']!=[{'crPackId':v} for v in sorted(sourceids)] or not sql['read_only'] or not sql['full_rows_available']:raise ValueError('SQL cross-check incomplete')
 if n['source_before']['nodes']!=156297 or n['source_before']['relationships']!=939037:raise ValueError('native inventory changed')
 tests=checks(t,g['records'],None)
 if not all(c['pass'] for c in tests) or tests!=load(base/'scorer_checks.json')['checks']:raise ValueError('requested-field controls failed')
 covers=load(base/'source/missing_pack_original_covers.json')
 # Re-read the actual original cover bytes, source roles and forwarding passage.
 for r in covers['cover_records']:
  p=base/'source/downloads'/(r['crPackId']+'.zip')
  if sha(p)!=r['archive_sha256']:raise ValueError('source archive differs')
  with zipfile.ZipFile(p) as z:
   if z.testzip() is not None:raise ValueError('damaged source archive')
   member=z.read(r['cover_member'])
  if hashlib.sha256(member).hexdigest()!=r['cover_member_sha256']:raise ValueError('cover member differs')
  with zipfile.ZipFile(io.BytesIO(member)) as z:xml=z.read('word/document.xml')
  if hashlib.sha256(xml).hexdigest()!=r['document_xml_sha256']:raise ValueError('cover XML differs')
  root=ET.fromstring(xml);ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
  paragraphs=[''.join(p.itertext()) for p in root.findall('.//w:p',ns)]
  plain=[''.join(p.itertext()) for p in root.findall('.//w:p',ns)]
  # Literal text runs, excluding document formatting metadata.
  plain=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in root.findall('.//w:p',ns)]
  if len(plain)!=r['full_cover_paragraph_n']:raise ValueError('cover paragraph inventory differs')
  for key in ('meeting_heading','source_role','forwarding_passage'):
   for passage in r[key]:
    if plain[passage['paragraph_1based']-1]!=passage['text']:raise ValueError('source passage differs')
  if not any('Source:RAN2'==p for p in plain) or not any('These CRs were agreed by RAN2 and are forwarded to TSG-RAN#110 for approval:'==p for p in plain):raise ValueError('submission role not established')
 if len(list((base/'source/downloads').glob('*.zip')))!=9:raise ValueError('source covers missing')
 if t['validation_status']!='validated' or t['admitted'] is not True or t['expert_validation_n']!=0 or t['model_calls']!=0:raise ValueError('scope/count differs')
 return {'status':'PASS','admitted_n':1,'native_rows':35,'scorer_controls':len(tests),'source_rows':240,'source_cover_zips':9,'files':len(m['files']),'manifest_sha256':sha(base/'manifest.json'),'source_snapshot_sha256':m['source_snapshot_sha256'],'new_model_predictions':0,'human_expert_validation_n':0,'merged_into_original402':False,'limits':'Recorded two-AI semantics and native/scorer/source evidence. Does not establish all-world submission completeness, human expert validity, graph/text coverage equivalence or model quality.'}

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parent);args=a.parse_args();print(json.dumps(verify(args.bundle),ensure_ascii=False))
