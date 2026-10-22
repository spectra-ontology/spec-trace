"""Offline replay of original sources and independent frozen-role interpreters.

Source archives certify semantics. Runtime answers are reconstructed exclusively
from the exported immutable retained fields; source annotations are not inputs.
"""
import hashlib,json,re,sqlite3,sys,zipfile,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path[:0]=[str(R/'retained'),str(R/'scoring')]
from repair_interpreter import graph_components,sql_components,aggregate
import contract_checks,original_scorer
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
NS={'w':W[1:-1]}
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads((R/p).read_text())
def active(x):
 if x.tag in [W+'del',W+'moveFrom']:return ''
 return (x.text or '') if x.tag==W+'t' else ''.join(active(c) for c in x)
def norm(s):return re.sub(r'\s+','',s).casefold()
def ordered(text,source):
 at=0
 for p in re.split(r'\n\s*\n',text):
  p=norm(p)
  if not p:continue
  at2=source.find(p,at)
  if at2<0:return False
  at=at2+len(p)
 return True

def scorer_controls(task,rows):
 generic=contract_checks.checks(task,rows)
 assert all(z['pass'] for z in generic)
 custom=[]
 def require(name,prediction,exact):
  actual=original_scorer.score(task,rows,prediction,diagnostic=True)
  assert actual['exact'] is exact,(name,actual)
  custom.append({'check':name,'expected_exact':exact,'actual_exact':actual['exact'],'pass':True})
 require('requested_TS_order',list(reversed(rows)),False)
 require('both_requested_TS_records',rows[:1],False)
 require('duplicate_TS_record',rows[:1]*2,False)
 require('cross_TS_description_binding',[dict(rows[0],**{'ti.impactDescription':rows[1]['ti.impactDescription']}),rows[1]],False)
 require('cross_TS_section_binding',[dict(rows[0],**{'ti.affectedSection':rows[1]['ti.affectedSection']}),rows[1]],False)
 require('authored_manual_generic_section_is_distinct',[dict(r,**{'ti.affectedSection':'5'}) for r in rows],False)
 require('supporting_source_paragraph_completeness',[rows[0],dict(rows[1],**{'ti.impactDescription':rows[1]['ti.impactDescription'].split('\n\n',1)[1]})],False)
 require('unrequested_mixed_WI_paragraph',[rows[0],dict(rows[1],**{'ti.impactDescription':rows[1]['ti.impactDescription']+'\n\nUnrelated work item amendment'})],False)
 require('impact_type_role',[dict(rows[0],**{'ti.impactType':'NewTS'}),rows[1]],False)
 require('study_identity_role',[dict(rows[0],**{'tr.trNumber':'38.825'}),rows[1]],False)
 return generic+custom

def replay():
 export=load('actual_export_receipt.json');graph=load('retained/frozen_graph_roles.json')
 assert sha((R/'retained/frozen_dependency_projection.sqlite').read_bytes())==export['projection_sha256']
 assert graph['source_DB_sha256']==export['source_DB_sha256']
 assert graph['complete_role_counts']==export['role_counts']
 c=sqlite3.connect((R/'retained/frozen_dependency_projection.sqlite').resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
 counts={t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in export['role_counts']};assert counts==export['role_counts'];c.close()
 a,types,n=graph_components(R);b,types2,n2=sql_components(R)
 assert (a,types,n)==(b,types2,n2)
 rows=aggregate(a,types);saved=load('review/actual_independent_SQL_and_literal_reducer_rows.json')
 assert rows==saved['rows'];assert n==72 and len(a)==70
 inv=load('source/source_inventory.json');raw={};source_proofs=[]
 for z in inv['sources']:
  p=R/z['path'];data=p.read_bytes();assert len(data)==z['archive_bytes'] and sha(data)==z['archive_sha256']
  with zipfile.ZipFile(p) as f:xml=f.read('word/document.xml');styles=f.read('word/styles.xml')
  assert sha(xml)==z['document_xml_sha256'] and sha(styles)==z['styles_xml_sha256']
  children=list(E.fromstring(xml).find('w:body',NS));texts=[active(x) for x in children]
  assert len(children)==z['current_body_children']
  assert sha(json.dumps(texts,ensure_ascii=False,separators=(',',':')).encode())==z['current_all_child_texts_sha256']
  raw[z['id']]={'children':children,'texts':texts,'cover':norm('\n'.join(texts[:8]))}
  source_proofs.append({'id':z['id'],'archive_sha256':z['archive_sha256'],'current_body_children':len(children)})
 review=load('review/actual_source_component_and_scope_review.json')
 byid={z['id']:z for z in review['CR_source_and_retained_roles']}
 assert len(byid)==40 and len(raw)==41
 workitem_proofs=[];paragraph_checks=[];section_checks=[]
 for ci,z in sorted(byid.items()):
  src=raw[ci];cover=src['cover'];codes=None
  for child in src['children'][:8]:
   for table_row in child.iter(W+'tr'):
    cells=[active(tc) for tc in table_row.findall('w:tc',NS)]
    for i,cell in enumerate(cells[:-1]):
     if re.sub(r'\W','',cell).casefold()=='workitemcode':codes=[v for v in cells[i+1].split(',') if v.strip()]
  assert codes is not None,(ci,'source Work item code cell missing')
  assert {norm(v) for v in codes}=={norm(v) for v in z['related_WorkItemCodes']},(ci,codes,z['related_WorkItemCodes'])
  workitem_proofs.append({'id':ci,'current_source_workitem_cell':codes,'retained_codes':z['related_WorkItemCodes'],'lexical_equivalence':'whitespace and case only'})
  for p in z['selected_components']:
   assert ordered(p['text'],cover),(ci,p['property'],'not ordered current cover')
   paragraph_checks.append({'CRid':ci,'field':p['property'],'sha256':sha(p['text'].encode()),'ordered_current_cover_match':True})
  for s in z['selected_sectionNumbers']:
   assert re.search(r'(?<![0-9.])'+re.escape(s)+r'(?![0-9.])','\n'.join(src['texts'][:8])),(ci,s)
   section_checks.append({'CRid':ci,'sectionNumber':s,'current_source_cover_match':True})
  observed=[p for p in a if p['CRid']==ci]
  for p in observed:
   expected=[q['text'] for q in z['selected_components'] if q['property']==p['field']]
   assert p['pieces']==expected and set(p['sections'])<=set(z['selected_sectionNumbers'])
  assert bool(observed)==bool(z['selected_components'])
 assert len(paragraph_checks)==74 and len({p['CRid'] for p in a})==35
 kernel=load('scoring/source_pins.json')['copied_kernel'];assert sha((R/'scoring'/kernel['path']).read_bytes())==kernel['sha256']
 definition=load('definition.json');assert definition['reference_query']==(R/'retained/candidate.cypher').read_text()
 controls=scorer_controls(definition,rows)
 selfscore=original_scorer.score(definition,rows,rows,diagnostic=True);assert selfscore['exact'] and selfscore['f1']==1
 return {'status':'PASS_SOURCE_RETAINED_SQL_GRAPH_AND_UNCHANGED_SCORER','source_DB_sha256':export['source_DB_sha256'],'dependency_projection_sha256':export['projection_sha256'],'role_counts':counts,'original_source_archives':len(raw),'original_source_body_children':sum(len(z['texts']) for z in raw.values()),'source_inventory_sha256':sha((R/'source/source_inventory.json').read_bytes()),'source_archive_proofs':source_proofs,'source_workitem_lexical_binding':workitem_proofs,'source_component_checks':paragraph_checks,'source_section_checks_n':len(section_checks),'candidate_CR_n':n,'selected_CR_n':35,'component_records_n':len(a),'selected_paragraphs_n':len(paragraph_checks),'answer_rows_n':len(rows),'rows_sha256':sha(json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode()),'components_sha256':sha(json.dumps(a,ensure_ascii=False,separators=(',',':')).encode()),'answer_self_score':selfscore,'scorer_controls':controls,'scorer_controls_n':len(controls),'scorer_human_expert_judgments':0,'paid_API_calls':0,'native_calls':0,'public_mutations':0,'queue_mutations':0}
if __name__=='__main__':print(json.dumps(replay(),ensure_ascii=False,indent=2))
