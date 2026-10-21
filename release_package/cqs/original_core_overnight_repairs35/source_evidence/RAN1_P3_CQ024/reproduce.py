#!/usr/bin/env python3
"""Reproduce the recorded CR-linked Agreement trace, using package bytes only."""
import sys
if sys.flags.optimize:raise SystemExit('optimized mode rejected')
sys.dont_write_bytecode=True
import collections,gzip,hashlib,importlib.util,io,json,re,stat,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
H=Path(__file__).absolute().parent
for p in [H,*H.parents]:
 if p.is_symlink():raise SystemExit('entry/ancestor symlink rejected')
INVENTORY='470b3d2103baa0c0b3422b17f970563ad6b8cd0c480e00b9bf7a71626ed0d926'
ID='RAN1_P3_CQ024'
REPAIR='3481219419b45416eec1c8f694b09ea7810150caf0295432c4a9bac3f359aa66'
QUERY='5abb5ae3f8222158aa866c07fb7e50341c629f842ca9fe946da929e749495d8d'
CRITERIA='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
DB='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def load(n):return json.loads((H/n).read_text())
def ungz(n):return json.loads(gzip.decompress((H/n).read_bytes()))
def lines(n):return [json.loads(s)for s in(H/n).read_text().splitlines()]
def token(x):return None if x is None else sha(json.dumps(x,ensure_ascii=False,separators=(',',':')).encode())
def module(name,n):
 s=importlib.util.spec_from_file_location(name,H/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def text(e):
 out=[]
 for n in e.iter():
  if n.tag in (W+'t',M+'t'):out.append(n.text or'')
  elif n.tag==W+'tab':out.append('\t')
  elif n.tag in(W+'br',W+'cr'):out.append('\n')
 return ''.join(out)
def boundary():
 actual=set()
 for p in H.rglob('*'):
  if p.is_symlink():raise ValueError('tree symlink rejected')
  mode=p.lstat().st_mode
  if stat.S_ISREG(mode):actual.add(p.relative_to(H).as_posix())
  elif not stat.S_ISDIR(mode):raise ValueError('nonregular tree entry rejected')
 assert sha((H/'immutable_inventory.json').read_bytes())==INVENTORY
 inv=load('immutable_inventory.json');assert inv['id']==ID
 assert actual=={x['path']for x in inv['files']}|{'immutable_inventory.json','manifest.json','reproduce.py'}
 for x in inv['files']:
  p=H/x['path'];assert p.stat().st_size==x['bytes']and sha(p.read_bytes())==x['sha256'],x['path']
 metadata={'artifact_type':'local_recorded_CR_Agreement_trace_evidence','id':ID,'new_admissions':0,'model_calls':0,'inventory_sha256':INVENTORY,'repair_sha256':REPAIR,'reference_query_sha256':QUERY,'verifier_sha256':sha((H/'reproduce.py').read_bytes()),'files':inv['files']}
 assert canon(load('manifest.json'))==canon(metadata)
def contract():
 d=load('contract/definition.json');assert len(d)==9 and d['id']==ID and sha(canon(d))==REPAIR
 assert sha(d['question_en'].encode())=='9a4faa480e12cd519184f29f5ab8cf43ece06b1d6e0e54db2517912955ef24ba'
 assert sha(d['original_query'].encode())=='5e65b4fb1f2b5e4ab5989c41384efb36464a929f74e0aa1280b462fbd0952da0'
 assert sha(d['reference_query'].encode())==QUERY
 assert d['required_fields']==[{'name':'resolutionId','type':'string','nullable':False,'source_column_or_expression':'agr.resolutionId'}]
 assert d['collection']=={'kind':'set'}and d['cardinality_policy']=={'mode':'exact','value':10}
 assert d['original_question_preserved']is True and d['repair_class']=='query_and_scorer'
 assert sha((H/'contract/criteria.json').read_bytes())==CRITERIA
 schema=module('local_review_schema','scoring/review_schema.py');criteria=load('contract/criteria.json')
 for f in ['contract/primary.json','contract/secondary.json']:schema.check_pass(load(f),d['question_en'],criteria['semantic_units'],criteria_sha=CRITERIA,identity_key='repair_sha256',identity_sha=REPAIR)
 assert load('contract/primary.json')['reviewer']!=load('contract/secondary.json')['reviewer']
 for a in load('contract/authority_spans.json'):
  p=H/'authority'/Path(a['original']['path']).name;assert sha(p.read_bytes())==a['original']['sha256']
  ls=p.read_text().splitlines()
  for s in a['spans']:assert '\n'.join(ls[s['first_line']-1:s['last_line']])==s['text']
 scope=load('contract/scope_and_supersession.json');assert scope['repair_sha256']==REPAIR
 assert load('history/superseded_source_complete_primary.json')['recommendation']=='unsupported_frozen_data'
 return d
def graph(own):
 f=ungz('frozen/whole_query_dependencies.json.gz')
 assert {k:len(v)for k,v in f.items()}=={'Agreement':21058,'Meeting':60,'Spec':127,'CR':10715,'Tdoc':123677,'rel_MADE_AT':24956,'rel_REFERENCES':19454,'rel_MODIFIES':10671}
 receipt=load('frozen/fresh_query_projection_receipt.json');assert receipt['DB_sha256_before']==receipt['DB_sha256_after']==DB
 assert receipt['all_query_dependency_projections_freshly_reopened_and_equal']is True
 props={r['node_id']:r for r in ungz('frozen/all_graph_path_Agreement_properties.json.gz')}
 ids={n:(r,t)for n,r,t in f['Agreement']};meets={n:(m,i)for n,m,i in f['Meeting']}
 targets={n for n,s in f['Spec']if s=='38.213'};crids=set(f['CR']);crtargets={n for n,d in f['rel_MODIFIES']if d in targets and n in crids}
 td={n:t for n,t in f['Tdoc']};refs=collections.defaultdict(list);at=collections.defaultdict(list)
 for n,t in f['rel_REFERENCES']:
  if t in crtargets:refs[n].append(td[t])
 for n,m in f['rel_MADE_AT']:
  if m in meets:at[n].append(meets[m])
 participants={n for n in refs if n in ids and n in at};assert set(props)==participants
 raw=[];eligible=[]
 for n in participants:
  a=props[n];assert (a['resolutionId'],token(a['answer_content']))==ids[n]
  owntext=own.own_record(a['content']or'')[0]
  for t in refs[n]:
   accepted=t in own.TD.findall(owntext)
   for m,i in at[n]:
    row=[a['resolutionId'],a['answer_content'],m,i];raw.append((n,t,row,accepted))
    if accepted:eligible.append(row)
 distinct={canon(r):r for r in eligible};ordered=list(distinct.values())
 ordered.sort(key=lambda r:r[0]);ordered.sort(key=lambda r:r[2],reverse=True);ordered.sort(key=lambda r:r[3],reverse=True)
 assert len(raw)==927 and len({canon(r)for _,_,r,_ in raw})==496 and len(ordered)==322
 sql=load('execution/all322_independent_SQL_full4.json');assert len(sql)==len(ordered)
 for nr,sr in zip(ordered,sql):assert len(nr)==len(sr)==4 and all(type(x)is type(y)and x==y for x,y in zip(nr,sr))
 latest=[(n,t,r,ok)for n,t,r,ok in raw if r[3]>=122];latestids={r[0]for _,_,r,_ in latest};latestown={r[0]for _,_,r,ok in latest if ok}
 selected=ordered[:10];assert len(latestids)==11 and latestown=={r[0]for r in selected}
 assert latestids-latestown=={'AGR-122b-UNKNOWN-020'}
 assert selected[-1][0]=='AGR-122-8.11.1-002'
 assert 'AGR-123-7-011'not in latestids
 return f,props,raw,selected
def source(f,raw,selected,own):
 reader=module('local_raw_reader','source/raw_word_formatting_reader.py')
 reader.FFS=re.compile(r'R1-\d{7}(?!\d)|\b(?:endorsed|agreed|adopt)\b',re.I)
 attr=load('source/source_attribution.json');bodies={};formats={};pins={}
 for s in attr['reports']:
  xb=gzip.decompress((H/'source'/s['document_XML']).read_bytes());st=gzip.decompress((H/'source'/s['styles_XML']).read_bytes())
  assert sha(xb)==s['document_XML_sha256']and sha(st)==s['styles_XML_sha256']
  root=ET.fromstring(xb);body=list(root.find(W+'body'));bodies[s['meeting']]=body;pins[s['meeting']]=s
  cover='\n'.join(text(e)for e in body[:15]);assert {'RAN1#123':'November 17th','RAN1#122b':'October 13th','RAN1#122':'August 25th'}[s['meeting']]in cover and '2025'in cover
  buf=io.BytesIO()
  with zipfile.ZipFile(buf,'w')as z:z.writestr('word/document.xml',xb);z.writestr('word/styles.xml',st)
  audit=reader.audit_document(buf.getvalue());blocks=list(reader.iter_blocks(root.find(W+'body')));rawmap={e:i for i,b in enumerate(body)for e in b.iter()}
  formats[s['meeting']]=(audit,blocks,rawmap)
 geo={r['resolutionId']:r for r in ungz('source/source_geometry869.json.gz')}
 current=[json.loads(s)for s in gzip.decompress((H/'source/latest869_frozen_metadata.jsonl.gz').read_bytes()).decode().splitlines()]
 assert len(current)==len(geo)==869 and {r['resolutionId']for r in current}==set(geo)
 tokens={r:t for _,r,t in f['Agreement']};identity={(n,r)for n,r,_ in f['Agreement']}
 for a in current:
  g=geo[a['resolutionId']];assert (a['node_id'],a['resolutionId'])in identity and g['source_DOCX_sha256']==pins[g['meeting']]['original_DOCX_sha256']
  lo,hi=g['source_record_raw_body_child_range'];body=bodies[g['meeting']]
  # Original geometry serializer intentionally omits Word tab/br nodes.
  literal='\n'.join(''.join(n.text or''for n in e.iter()if n.tag in(W+'t',M+'t'))for e in body[lo:hi])
  assert sha(literal.encode())==g['source_record_literal_sha256'],a['resolutionId']
  ans=a['contentWithEquations']if a['contentWithEquations']is not None else a['content'];assert token(ans)==tokens[a['resolutionId']]
 witnesses=load('source/selected10_actual_source_witnesses.json');assert {w['resolutionId']for w in witnesses}=={r[0]for r in selected}and len(witnesses)==10
 for w in witnesses:
  aid=w['resolutionId'];g=geo[aid];lo,hi=w['raw_own_range'];assert lo==g['source_record_raw_body_child_range'][0]
  body=bodies[w['meeting']];audit,blocks,rawmap=formats[w['meeting']]
  target={t for _,t,r,ok in raw if r[0]==aid and ok};assert target==set(w['source_positive_existing_CR_targets'])
  found=set();adopt=False;observations=[];alltext=[]
  for p in audit['paragraphs']:
   child=rawmap[blocks[p['body_block_index']]]
   if not lo<=child<hi:continue
   alltext.append(p['final_literal'])
   relevant=[o for o in p['occurrences']if o['literal']in target or re.fullmatch(r'(?i)endorsed|agreed|adopt',o['literal'])]
   if relevant:observations.append({'raw_body_child':child,'final_literal':p['final_literal'],'XML_sha256_ET_UTF8':sha(ET.tostring(p['element'],encoding='utf-8')),'occurrences':relevant})
   for o in relevant:
    if o['active_formatting_status']=='all_active':
     if o['literal']in target:found.add(o['literal'])
     if re.fullmatch(r'(?i)endorsed|agreed|adopt',o['literal']):adopt=True
  assert target<=found and adopt and observations==w['paragraph_observations']
  assert '\n'.join(alltext)==w['own_final_literal']
  assert target<=set(own.TD.findall('\n'.join(text(e)for e in body[lo:hi])))
 roles=load('source/fourteen_own_role_assessments.json');assert len(roles)==14
 foreign=geo['AGR-122b-UNKNOWN-020'];lo=foreign['source_record_raw_body_child_range'][0];hi=roles['AGR-122b-UNKNOWN-020']['own_end_exclusive'];body=bodies[foreign['meeting']]
 ownforeign='\n'.join(text(e)for e in body[lo:hi]);latesttarget={t for _,t,r,_ in raw if r[0]=='AGR-122b-UNKNOWN-020'}
 assert not(latesttarget&set(own.TD.findall(ownforeign)))
 # Source-positive augmentation is preserved, without changing the recorded domain.
 alt=load('frozen/source_only_13604_alternative.json');rid=alt['frozen_Agreement']['resolutionId'];assert rid=='AGR-123-7-011'
 a=next(a for a in current if a['resolutionId']==rid);assert a==alt['frozen_Agreement']
 assert not[d for n,d in f['rel_REFERENCES']if n==a['node_id']]
 g=geo[rid];lo=g['source_record_raw_body_child_range'][0];hi=roles[rid]['own_end_exclusive'];literal='\n'.join(text(e)for e in bodies[g['meeting']][lo:hi])
 assert set(own.TD.findall(literal))=={'R1-2509603','R1-2509604'}and 'TS38.213'in a['content']
 return {'original_reports':3,'latest_retained_windows_replayed':869,'selected_own_reference_and_adoption_witnesses':10,'foreign_catalogue_negative_replayed':True,'source_only_augmentation_alternative_preserved':True}
def execution(d,selected):
 x=load('execution/native_case.json');nr=lines('execution/native_rows.jsonl')
 assert x['id']==ID and x['query']==d['reference_query']and x['query_sha256']==QUERY and x['status']=='OK'
 assert x['columns']==['agr.resolutionId','content','m.meetingNumber','m.meetingNumberInt']
 assert x['rows_retained']==10 and x['truncated']is False and x['full_rows_available']is True and x['rollback_completed']is True
 assert x['plan_query_type']==x['execution_query_type']=='r'and x['rows_sha256']==sha((H/'execution/native_rows.jsonl').read_bytes())
 sql=load('execution/selected10_independent_SQL_full4.json');assert len(nr)==len(sql)==len(selected)==10
 for a,b,c in zip(nr,sql,selected):assert all(type(v)is type(w)is type(t)and v==w==t for v,w,t in zip(a,b,c))and len(a)==len(b)==len(c)==4
 ex=load('execution/native_execution.json');assert ex['inventory_unchanged']is True and ex['source_before']==ex['source_after']
 assert ex['source_before']['source']['sha256']=='9540683df5407bb3f8978ad4d05ddc7f7880f10c94f21273f588d737f145e231'
 assert ex['input_sha256']==sha((H/'execution/native_input.jsonl').read_bytes())and ex['protocol_sha256']==sha((H/'execution/native_protocol.json').read_bytes())
 assert lines('execution/native_input.jsonl')[0]['candidate_query']==d['reference_query']
 guard=load('execution/outer_guard.json');assert guard['status']=='PASS'and guard['child_exit']==0 and guard['owned_cleanup']['owned_stopped']is True
 assert guard['scope_sha256']==sha((H/'contract/definition.json').read_bytes())and guard['wrapper_sha256']==sha((H/'execution/outer_native_reserve_guard.py').read_bytes())
 assert guard['prestart_available_minimum_bytes']==26*1024**3 and guard['continuous_reserve_minimum_bytes']==16*1024**3
 for key in ['Linux_available_bytes','Windows_available_bytes']:
  assert type(guard['initial_memory'][key])is int and guard['initial_memory'][key]>=26*1024**3
  assert all(type(s[key])is int and s[key]>=16*1024**3 for s in guard['memory_samples'])
 obs=lines('execution/actual_fresh_memory_observations.jsonl');assert obs and len({o['nonce']for o in obs})==len(obs)
 assert all(o['status']=='FRESH_NUMERIC_OBSERVATION'and type(o['windows_available_bytes'])is int and o['Get_CimInstance_calls_for_this_request']==1 and o['cached_values_used']==0 for o in obs)
 return {'saved_native_rows':10,'all_four_typed_native_SQL_columns_equal':True,'read_only_and_rollback':True,'source_inventory_unchanged':True,'owned_container_stopped':True}
def controls(d,own,selected):
 scope=[('Draft CR R1-2000001 is endorsed.','R1-2000001',True),('Agreement\nR1-2000001\tForeign catalogue','R1-2000001',False),('Adopt TP related to the following Tdocs\nR1-2000001\tNamed attachment','R1-2000001',True),('Final CRs capturing this TP are in:\nR1-2000001\tCR title\n(Rel-18,38.213,CR0737) is agreed.','R1-2000001',True),('Final CRs capturing this TP are in:\nR1-2000001\tCR title','R1-2000001',False),('CR R1-20000010 is endorsed.','R1-2000001',False),('CR R1-2000001 is endorsed.\nR1-2000002\tForeign','R1-2000001',True),('Following TPs are endorsed.\nR1-2000001\tForeign','R1-2000001',False)]
 for text,td,want in scope:assert (td in own.TD.findall(own.own_record(text)[0]))is want
 assert all(x['pass']is True for x in load('execution/actual_scope_controls.json'))
 scorer=module('local_scorer','scoring/scorer.py');gold=[{'resolutionId':r[0]}for r in selected]
 tests=[(gold,True),(list(reversed(gold)),True),(gold+[gold[0]],True),(gold[:-1],False),(gold+[{'resolutionId':'AGR-000-0-000'}],False),([{'resolutionId':'AGR-000-0-000'}]+gold[1:],False),([{'resolutionId':1}]+gold[1:],False),([{'resolutionId':True}]+gold[1:],False),([{'resolutionId':None}]+gold[1:],False),([{}]+gold[1:],False),([{**r,'extra_audit_field':'not requested'}for r in gold],True)]
 for pred,want in tests:assert scorer.score(d,gold,pred,diagnostic=True)['exact']is want
 saved=load('execution/actual_typed_controls.json');assert len(saved)==len(tests)and all(x['pass']is True for x in saved)
 return {'unchanged_typed_scorer_controls':len(tests),'synthetic_own_scope_controls':len(scope)}
def main():
 boundary();d=contract();own=module('local_own_reference','source/own_reference_role.py');f,props,raw,selected=graph(own)
 src=source(f,raw,selected,own);ex=execution(d,selected);ctrl=controls(d,own,selected)
 return {'status':'PASS','id':ID,'repair_sha256':REPAIR,'cases':[{'id':ID,'requested_records':10,'requested_answer_role':'Agreement identity set','complete_recorded_graph_paths':len(raw),'distinct_own_full4_rows':322,'source':src,'execution':ex,'controls':ctrl}],'model_calls':0,'new_admissions':0}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False))
