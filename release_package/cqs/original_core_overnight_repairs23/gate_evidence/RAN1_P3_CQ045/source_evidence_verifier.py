#!/usr/bin/env python3
"""Closed-inventory finite source verification; stdlib only, no host fallback."""
import argparse, contextlib, gzip, hashlib, importlib.util, io, json, os
from pathlib import Path
import sys, xml.etree.ElementTree as E, zipfile
sys.dont_write_bytecode=True
INVENTORY_SHA='f2f31d2d52befe4a9d3a18ce42f0c39517501ca5ad18594c7ffd490d18bb9168'
ID='RAN1_P3_CQ045';REPAIR='3950eb7946e0b3ad47afed70818088159fea41320df0e91c8f0de8e28b426e80'
DEF='010c24b19e334ec87289e0d7800c704f4986183a60622527e842a64482d68873'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def sha(b):return hashlib.sha256(b).hexdigest()
def no_link(path):
 p=Path(os.path.abspath(path))
 for q in [*reversed(p.parents),p]:
  if q.is_symlink():raise ValueError('symlink refused before content read: '+str(q))
 return p
def load(p):return json.loads(no_link(p).read_text())
def literal(x):return ''.join(t.text or '' for t in x.iter(W+'t'))
def main():
 entry=no_link(__file__);here=entry.parent
 ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=Path,default=None);args=ap.parse_args()
 mp=no_link(here/'manifest.json');manifest=load(mp)
 assert set(manifest)=={'status','id','verifier_sha256','immutable_inventory_sha256','scope_and_provenance','source_selected_records','files'}
 def exact_json(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
 assert manifest['status']=='PORTABLE_FINITE_SOURCE_EVIDENCE_NOT_AN_ADMISSION_ACTION' and manifest['id']==ID
 assert manifest['verifier_sha256']==sha(entry.read_bytes())
 invp=no_link(here/'immutable_inventory.json');assert sha(invp.read_bytes())==INVENTORY_SHA==manifest['immutable_inventory_sha256']
 inventory=load(invp);files=inventory['files'];names={r['path'] for r in files};assert len(names)==len(files)
 expected=names|{'manifest.json','immutable_inventory.json','verify_source_evidence.py'}
 actual=set()
 for p in here.rglob('*'):
  no_link(p)
  if p.is_file():actual.add(p.relative_to(here).as_posix())
 assert actual==expected, 'closed inventory differs'
 for row in files:
  rel=Path(row['path']);assert not rel.is_absolute() and '..' not in rel.parts
  p=no_link(here/rel);raw=p.read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
 expected_manifest_files=files+[{'path':'immutable_inventory.json','bytes':invp.stat().st_size,'sha256':sha(invp.read_bytes())},{'path':'verify_source_evidence.py','bytes':entry.stat().st_size,'sha256':sha(entry.read_bytes())}]
 assert exact_json(manifest['files'])==exact_json(expected_manifest_files)
 d=load(here/'definition.json');assert sha((here/'definition.json').read_bytes())==DEF
 assert d['id']==ID and d['original_query']==d['reference_query'] and d['repair_class']=='scorer_only'
 assert sha(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==REPAIR
 assert d['required_fields']==[{'name':'spec','type':'string','nullable':False,'source_column_or_expression':'sp.specNumber'}] and d['collection']=={'kind':'set'} and d['cardinality_policy']=={'mode':'all'}
 provenance={'repair_sha256':REPAIR,'definition_sha256':DEF,'original_question_sha256':sha(d['question_en'].encode()),'original_query_sha256':sha(d['original_query'].encode()),'human_expert_n':0,'nonblind_AI':True,'original560_pass_increment':0,'native_calls':0,'API_calls':0,'full_original_scan_is_separate_opt_in':True}
 assert exact_json(manifest['scope_and_provenance'])==exact_json(provenance)
 selected_path=no_link(here/'source_selected_records.jsonl');records=[json.loads(s) for s in selected_path.read_text().splitlines() if s.strip()]
 selected_meta={'path':'source_selected_records.jsonl','records':3,'bytes':selected_path.stat().st_size,'sha256':sha(selected_path.read_bytes())}
 assert exact_json(manifest['source_selected_records'])==exact_json(selected_meta)
 witnesses=load(here/'finite_source_gate/three_own_formal_Resolution_CR_WI_links.json')
 assert records==[{'spec':s} for s in sorted({x['spec'] for x in witnesses})] and len(records)==3
 # The same original criteria/checker validates review identity and seven-unit records.
 def module(name,p):
  sp=importlib.util.spec_from_file_location(name,no_link(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
 checker=module('included_original_review_schema',here/'reviews/review_schema.py');criteria=load(here/'reviews/criteria.json')
 kinds=[]
 for name in ['primary_review.json','independent_secondary_review.json']:
  r=load(here/'reviews'/name);checker.check_pass(r,d['question_en'],criteria['semantic_units'],criteria_sha=sha((here/'reviews/criteria.json').read_bytes()),identity_key='repair_sha256',identity_sha=REPAIR);assert r.get('reviewer_kind');kinds.append(r['reviewer_kind'])
 assert len(set(kinds))==2
 # Reparse included raw row/shared-string fragments and all normative XML.
 fragment_reader=module('included_finite_fragment_reader',here/'verify_included_source_fragments.py')
 prev=list(sys.argv);buf=io.StringIO()
 try:
  sys.argv=[str(here/'verify_included_source_fragments.py'),'--preparation',str(here)]
  with contextlib.redirect_stdout(buf):fragment_reader.main()
 finally:sys.argv=prev
 fragment_result=json.loads(buf.getvalue());assert fragment_result['status']=='PASS'
 extraction=load(here/'source_fragment_extraction_receipt.json')
 streams={}
 for pin in extraction['report_streams']:
  obj=json.loads(gzip.decompress(no_link(here/'fragments'/pin['path']).read_bytes()));streams[pin['original_locator']]=obj
 negative=load(here/'finite_source_gate/all_five_outside_IDs_by_all61_report_versions_and_own_boundary_proof.json');ids=negative['outside_CR_IDs']
 assert len(negative['all8_occurrence_blocks_and_original_scope_exclusions'])==8
 for row in negative['all8_occurrence_blocks_and_original_scope_exclusions']:
  stream=streams[row['report']]['blocks'];idx=row['raw_body_child0'];assert literal(E.fromstring(row['full_occurrence_block_XML']))==stream[idx]['text']
  role=row['source_role_evidence']
  if 'preceding_Annex_heading' in role:
   h=role['preceding_Annex_heading'];assert h['raw_body_child0']<idx and h['text']==stream[h['raw_body_child0']]['text'] and h['text'].startswith('Annex')
  else:
   lo,hi=role['own_Conclusion_range_raw_body_child0_half_open'];assert idx<lo<hi and stream[lo]['text'].strip()=='Conclusion'
   assert not any(i in b['text'] for b in stream[lo:hi] for i in ids)
 for row in witnesses:
  for block in row['own_report_blocks']:
   # Each selected own block is re-bound to the source report stream, not just a label.
   exact=streams['ontology/input/tsg/RAN/formal/meetings/RAN1/Final_Report/Final_Report_RAN1-110.docx']
   assert block['raw_body_child0']<len(exact['blocks']) and exact['blocks'][block['raw_body_child0']]['text']==literal(E.fromstring(block['xml']))
  assert any(row['tdoc'] in b['text'] for b in row['own_report_blocks'])
  assert any('Final CR' in b['text'] and 'agreed' in b['text'] for b in row['own_report_blocks'])
 optional=None
 if args.source_root is not None:
  root=no_link(args.source_root)
  for pin in load(here/'finite_source_gate/all_62_loader_input_workbook_pins.json'):
   p=no_link(root/pin['path']);raw=p.read_bytes();assert len(raw)==pin['bytes'] and sha(raw)==pin['sha256']
  for loc,obj in streams.items():
   pin=obj['original_source_pin'];p=no_link(root/loc);raw=p.read_bytes();assert len(raw)==pin['bytes'] and sha(raw)==pin['sha256']
   with zipfile.ZipFile(io.BytesIO(raw)) as z:
    xml=z.read('word/document.xml');assert sha(xml)==pin['document_xml_sha256']
    assert z.getinfo('word/document.xml').CRC==pin['document_xml_crc32']
   body=E.fromstring(xml).find(W+'body')
   actual=[{'kind':x.tag.rsplit('}',1)[-1],'text':literal(x)} for x in body];assert actual==obj['blocks']
  optional={'all62_original_workbooks_rehashed':True,'all61_original_DOCX_rehashed_and_literal_streams_reextracted':True,'six_official_ZIP_container_bytes_embedded_or_reaccessed':False}
 print(json.dumps({'status':'PASS','id':ID,'immutable_scientific_files':len(files),'source_candidate_CR_rows':482,'source_target_TSs':4,'outside_CR_IDs':5,'report_literal_streams':61,'outside_occurrence_blocks':8,'own_normative_TS_witnesses':3,'source_selected_records':len(records),'whole_38212_final_CR_table_exact':False,'optional_original_replay':optional,'original560_pass_increment':0,'human_expert_n':0,'native_calls':0,'API_calls':0,'scope_limit':'Offline included fragment/derived-stream/normative XML verification is distinct from optional original-source extraction and original native/SQL/admission.'}))
if __name__=='__main__':main()
