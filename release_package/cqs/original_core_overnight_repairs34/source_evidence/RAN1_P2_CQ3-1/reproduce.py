#!/usr/bin/env python3
"""Replay the finite documentary-reference contract using included evidence only."""
import sys
if sys.flags.optimize:raise SystemExit('Assertions must remain enabled')
sys.dont_write_bytecode=True
import gzip,hashlib,importlib.util,io,json,re,stat,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
H=Path(__file__).absolute().parent
for p in(H,*H.parents):
 if p.is_symlink():raise SystemExit('Entry/ancestor symlink refused')
INVENTORY='e8d4cb53521ecf0129dddc0eb4fe86b8210075f49054b7c742dc48be5957e103'
REPAIR='f77c0272592b43bed41286996d8803dc3b77c165b8156dda78ebb414a765d007'
QUERY='70be13e4f11b15489292f065051765b3cd179dc3a03f943e7654e0f90275b92c'
CRITERIA='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
ID='RAN1_P2_CQ3-1'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def load(n):return json.loads((H/n).read_text())
def lines(n):return[json.loads(s)for s in(H/n).read_text().splitlines()]
def module(name,n):
 s=importlib.util.spec_from_file_location(name,H/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def text(e):
 out=[]
 for n in e.iter():
  if n.tag in(W+'t',M+'t'):out.append(n.text or'')
  elif n.tag==W+'tab':out.append('\t')
  elif n.tag in(W+'br',W+'cr'):out.append('\n')
 return ''.join(out)
def main():
 actual=set()
 for p in H.rglob('*'):
  if p.is_symlink():raise AssertionError('Tree symlink refused')
  mode=p.lstat().st_mode
  if stat.S_ISREG(mode):actual.add(p.relative_to(H).as_posix())
  elif not stat.S_ISDIR(mode):raise AssertionError('Nonregular tree entry refused')
 assert sha((H/'immutable_inventory.json').read_bytes())==INVENTORY
 inv=load('immutable_inventory.json');assert inv['id']==ID
 expected={f['path']for f in inv['files']}|{'immutable_inventory.json','manifest.json','reproduce.py'}
 assert actual==expected
 for f in inv['files']:
  p=H/f['path'];assert p.is_file()and p.stat().st_size==f['bytes']and sha(p.read_bytes())==f['sha256'],f['path']
 expectedmeta={'artifact_type':'local_documentary_company_reference_evidence','id':ID,'new_admissions':0,'model_calls':0,'inventory_sha256':INVENTORY,'repair_sha256':REPAIR,'reference_query_sha256':QUERY,'verifier_sha256':sha((H/'reproduce.py').read_bytes()),'files':inv['files']}
 assert canon(load('manifest.json'))==canon(expectedmeta)
 d=load('contract/definition.json');assert len(d)==9 and d['id']==ID and sha(canon(d))==REPAIR
 assert sha(d['question_en'].encode())=='429be9a0bc70ea5b47cb17fd3d270920cf0eff368d0ea53f4ead105e23932d0c'
 assert sha(d['original_query'].encode())=='4f38d477c4cd01499db852563b56952bb0cfe1cc4ab9095ca8d6b42ea40e1fc9'
 assert sha(d['reference_query'].encode())==QUERY
 assert d['required_fields']==[{'name':'tdocNumber','type':'string','nullable':False,'source_column_or_expression':'t.tdocNumber'}]
 assert d['collection']=={'kind':'set'}and d['cardinality_policy']=={'mode':'at_most','value':15}
 assert d['original_question_preserved']is True and d['repair_class']=='query_and_scorer'
 assert sha((H/'contract/criteria.json').read_bytes())==CRITERIA
 criteria=load('contract/criteria.json');schema=module('local_review_schema','scoring/review_schema.py')
 for n in['contract/primary.json','contract/secondary.json']:
  schema.check_pass(load(n),d['question_en'],criteria['semantic_units'],criteria_sha=CRITERIA,identity_key='repair_sha256',identity_sha=REPAIR)
 assert load('contract/primary.json')['reviewer']!=load('contract/secondary.json')['reviewer']
 own=module('local_own_reference','source/own_reference_role.py')
 docs={};raw={};formats={};reader=module('local_raw_format','source/raw_word_formatting_reader.py')
 reader.FFS=re.compile(r'R1-\d{7}(?!\d)|\bAgreement\b|\b(?:endorsed|agreed|Adopt|following Tdocs|Final CRs?|Final summary|Comeback for draft LS)\b',re.I)
 for sd in load('source/original_source_parts.json'):
  xb=gzip.decompress((H/'source'/sd['document_file']).read_bytes());st=gzip.decompress((H/'source'/sd['styles_file']).read_bytes())
  assert sha(xb)==sd['document_XML_sha256']and sha(st)==sd['styles_XML_sha256']
  docs[sd['meeting']]=sd;raw[sd['meeting']]=list(ET.fromstring(xb).find(W+'body'))
  bio=io.BytesIO()
  with zipfile.ZipFile(bio,'w')as z:z.writestr('word/document.xml',xb);z.writestr('word/styles.xml',st)
  formats[sd['meeting']]=reader.audit_document(bio.getvalue())
 frozen=json.loads(gzip.decompress((H/'source/frozen_latest869_projection.json.gz').read_bytes()))
 geo={g['resolutionId']:g for g in load('source/source869_geometry.json')}
 assert len(frozen)==len(geo)==869 and {a['resolutionId']for a in frozen}==set(geo)
 original=[];eligible=[];source_checks=[]
 for a in frozen:
  g=geo[a['resolutionId']];assert a['node_id']==g['node_id']and g['source_DOCX_sha256']==docs[g['meeting']]['DOCX_sha256']
  lo,hi=g['broad_raw_body_child_range'];body=raw[g['meeting']];assert 0<=lo<hi<=len(body)
  src='\n'.join(text(e)for e in body[lo:hi]);fown=own.own_record(a['content']or'')[0];sown=own.own_record(src)[0]
  for m in a['meetings']:
   assert type(m['meetingNumberInt'])is int and m['meetingNumberInt']>=122
   for td in a['references']:
    for co in td['companies']:
     if co['companyName']!='Huawei':continue
     r={'order':[-m['meetingNumberInt'],td['tdocNumber'],a['resolutionId']],'row':[td['tdocNumber'],td['title'],a['resolutionId'],m['meetingNumber']]}
     original.append(r)
     fp=td['tdocNumber']in own.TD.findall(fown);sp=td['tdocNumber']in own.TD.findall(sown)
     assert fp==sp,(a['resolutionId'],td['tdocNumber'])
     source_checks.append({'resolutionId':a['resolutionId'],'tdocNumber':td['tdocNumber'],'source_own_reference':sp})
     if fp:eligible.append(r)
 original.sort(key=lambda r:r['order']);eligible.sort(key=lambda r:r['order'])
 assert len(original)==87 and len(eligible)==33 and len(source_checks)==87
 selected=[x['row']for x in eligible[:15]];assert len({r[0]for r in selected})==15
 old=lines('source/original_latest87.jsonl')
 assert [r['row']for r in original]==[[r['tdocNumber'],r['title'],r['resolutionId'],r['meetingNumber']]for r in old]
 nc=load('execution/native_case.json');nr=lines('execution/native_rows.jsonl')
 assert nc['id']==ID and nc['status']=='OK'and nc['query_sha256']==QUERY and nc['query']==d['reference_query']
 assert nc['columns']==['t.tdocNumber','t.title','a.resolutionId','m.meetingNumber']
 assert nc['rows_retained']==15 and nc['truncated']is False and nc['rollback_completed']is True
 assert nc['plan_query_type']==nc['execution_query_type']=='r'and nc['full_rows_available']is True
 assert sha((H/'execution/native_rows.jsonl').read_bytes())==nc['rows_sha256']
 assert nr==selected==load('execution/independent_SQL_selected15.json')and all(type(v)is str for r in nr for v in r)
 ex=load('execution/native_execution.json');assert ex['inventory_unchanged']is True and ex['source_before']==ex['source_after']
 assert ex['source_before']['source']['sha256']=='9540683df5407bb3f8978ad4d05ddc7f7880f10c94f21273f588d737f145e231'
 assert ex['input_sha256']==sha((H/'execution/native_input.jsonl').read_bytes())and ex['protocol_sha256']==sha((H/'execution/native_protocol.json').read_bytes())
 assert lines('execution/native_input.jsonl')[0]['candidate_query']==d['reference_query']
 guard=load('execution/outer_guard.json');assert guard['status']=='PASS'and guard['child_exit']==0 and guard['owned_cleanup']['owned_stopped']is True
 assert guard['scope_sha256']==sha((H/'contract/definition.json').read_bytes())
 assert guard['wrapper_sha256']==sha((H/'execution/outer_native_reserve_guard.py').read_bytes())
 assert guard['prestart_available_minimum_bytes']==26*1024**3 and guard['continuous_reserve_minimum_bytes']==16*1024**3
 for key in['Linux_available_bytes','Windows_available_bytes']:
  assert type(guard['initial_memory'][key])is int and guard['initial_memory'][key]>=26*1024**3
  assert all(type(s[key])is int and s[key]>=16*1024**3 for s in guard['memory_samples'])
 regs=load('source/selected_register_rows.json');assert{r['tdocNumber']for r in regs}=={r[0]for r in nr}
 N={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
 register_parts={}
 for sd in load('source/original_register_files.json'):
  rb=(H/'source'/sd['included_file']).read_bytes();assert sha(rb)==sd['sha256']
  with zipfile.ZipFile(io.BytesIO(rb))as z:
   ss=[''.join(n.itertext())for n in ET.fromstring(z.read('xl/sharedStrings.xml'))]
   sx=z.read('xl/worksheets/sheet1.xml');rows=ET.fromstring(sx).find('s:sheetData',N)
   register_parts[sd['original_file']]=(ss,sx,{int(row.attrib['r']):row for row in rows})
 for r in regs:
  ss,sx,rows=register_parts[r['file']];assert sha(sx)==r['sheet_XML_sha256']
  row=rows[r['row']];assert ET.tostring(row,encoding='unicode')==r['row_XML'];cells={}
  for cell in row:
   v=cell.find('s:v',N);value=ss[int(v.text)]if cell.attrib.get('t')=='s'and v is not None else v.text if v is not None else ''.join(cell.itertext())
   cells[re.sub(r'\d','',cell.attrib['r'])]=value
  assert cells['A']==r['tdocNumber']and cells['B']==r['Title']and cells['C']==r['Source']
  assert 'Huawei'in r['Source']and r['frozen_title_equal']is True and next(x[1]for x in nr if x[0]==r['tdocNumber'])==r['Title']
 # Recompute active Tdoc/Agreement runs in the original source window.
 for td,title,aid,meeting in nr:
  g=geo[aid];lo,hi=g['broad_raw_body_child_range'];fmt=formats[meeting];body=raw[meeting]
  blockraw=[i for i,e in enumerate(body)if e.tag in(W+'p',W+'tbl')];assert len(blockraw)==len(fmt['blocks'])
  idocc=[];headings=[]
  for p in fmt['paragraphs']:
   if not lo<=blockraw[p['body_block_index']]<hi:continue
   idocc.extend(o for o in p['occurrences']if o['literal']==td)
   headings.extend(o for o in p['occurrences']if o['literal'].lower()=='agreement')
  assert idocc and headings and all(o['active_formatting_status']=='all_active'for o in idocc+headings)
 alt=load('source/Original_source_alternative_receipt.json');assert alt['extra_Huawei_members_from_this_alternative']==0 and alt['Huawei_Original_source_unique_Tdocs']==8
 scorer=module('local_scorer','scoring/scorer.py');gold=[{'tdocNumber':r[0]}for r in nr]
 checks=[('exact',gold,True),('reversed_set',list(reversed(gold)),True),('duplicate_set',gold+[gold[0]],True),('missing',gold[:-1],False),('extra',gold+[{'tdocNumber':'R1-0000000'}],False),('wrong_type',[{'tdocNumber':1}]+gold[1:],False),('missing_field',[{}]+gold[1:],False),('null',[{'tdocNumber':None}]+gold[1:],False)]
 for name,pred,want in checks:assert scorer.score(d,gold,pred,diagnostic=True)['exact']is want,name
 return{'status':'PASS','id':ID,'repair_sha256':REPAIR,'requested_records':len(gold),'all_four_native_columns_equal_frozen_prefix_and_SQL':True,'latest_original_Huawei_paths':len(original),'latest_own_Huawei_paths':len(eligible),'source_original_reports_replayed':3,'source_window_geometry':len(geo),'selected_ID_and_Agreement_heading_active':True,'typed_scorer_controls':len(checks),'scope':'Original graph-relative content-derived documentary REFERENCES and recorded Source/Huawei; no full physical-causal contribution completeness claim','new_admissions':0,'model_calls':0}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False))
