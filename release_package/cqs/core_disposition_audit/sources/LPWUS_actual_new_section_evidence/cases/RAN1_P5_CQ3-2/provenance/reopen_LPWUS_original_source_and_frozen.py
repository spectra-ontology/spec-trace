"""Original LP-WUS question, source-format roles and independent frozen recovery."""
import csv,gzip,hashlib,io,json,re,sqlite3,sys,zipfile
from pathlib import Path
import xml.etree.ElementTree as E
if sys.flags.optimize:raise SystemExit('Enabled checks required')
L=Path(__file__).resolve().parent
R=next(p for p in L.parents if (p/'CLAUDE.md').is_file())
P=R.parent/'spectra-public/spec-trace';F=L/'actual_source_and_frozen'
A55=L.parent/'RAN1_P5_CQ2-3';ID='RAN1_P5_CQ3-2'
DB=R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/authorized_incremental48_OpenRouter_release/evaluation/runtime/relational/RAN1.sqlite'
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};W='{'+N['w']+'}'
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return {'path':str(p.relative_to(R)) if p.is_relative_to(R) else str(p),'bytes':len(b),'sha256':sha(b)}
def save(n,v):
 p=F/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');return pin(p)
def copy(n,p):
 d=F/n;assert not d.exists();d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(p.read_bytes());return pin(d)
def active_text(x):
 if x.tag in {W+'del',W+'moveFrom'}:return ''
 return ((x.text or '') if x.tag==W+'t' else '')+''.join(active_text(y) for y in x)
def source_roles(key,xml,styles):
 body=E.fromstring(xml).find('w:body',N);st=E.fromstring(styles)
 sm={x.get(W+'styleId'):x for x in st if x.tag==W+'style'}
 def outline(k,seen=()):
  if k not in sm or k in seen:return None
  el=sm[k];v=el.find('w:pPr/w:outlineLvl',N)
  if v is not None:return int(v.get(W+'val'))
  nm=el.find('w:name',N)
  if nm is not None and re.fullmatch(r'heading\s*[1-9]',nm.get(W+'val',''),re.I):return int(re.search('[1-9]',nm.get(W+'val')).group())-1
  parent=el.find('w:basedOn',N)
  return outline(parent.get(W+'val'),seen+(k,)) if parent is not None else None
 paragraphs=[];heads=[];cover=[]
 for i,x in enumerate(body):
  if x.tag==W+'tbl':
   if re.search(r'Work item code|Clauses affected|CHANGE REQUEST',active_text(x),re.I):cover.append({'body_child':i,'rows':[[active_text(tc) for tc in tr.findall('w:tc',N)] for tr in x.findall('w:tr',N)]})
   continue
  if x.tag!=W+'p':continue
  s=x.find('w:pPr/w:pStyle',N);style=s.get(W+'val') if s is not None else None
  direct=x.find('w:pPr/w:outlineLvl',N);level=int(direct.get(W+'val')) if direct is not None else outline(style)
  row={'body_child':i,'style':style,'outline':level,'text':active_text(x),'insertions':len(x.findall('.//w:ins',N)),'deletions':len(x.findall('.//w:del',N)),'moves_from':len(x.findall('.//w:moveFrom',N)),'paragraph_mark_inserted':x.find('w:pPr/w:rPr/w:ins',N) is not None}
  paragraphs.append(row)
  if level is not None and level<9:heads.append(row)
 sections=[]
 for j,row in enumerate(paragraphs):
  if re.fullmatch(r'\d+\s*(?:Scope|Conclusions?)(?:\s+and\s+recommendations)?\s*',row['text'],re.I):
   end=next((k for k in range(j+1,len(paragraphs)) if paragraphs[k]['outline']==0 or re.match(r'Annex\s*[A-Z]?$',paragraphs[k]['text'])),len(paragraphs))
   sections.append({'heading':row,'paragraphs':paragraphs[j:end]})
 mentions=[row for row in paragraphs if re.search(r'38[.]211|38[.]213|38[.]869|NR_LPWUS|new.{0,25}clause|clause.{0,25}new|WI phase|work item|study item',row['text'],re.I)]
 return {'key':key,'document_xml':{'bytes':len(xml),'sha256':sha(xml)},'styles_xml':{'bytes':len(styles),'sha256':sha(styles)},'body_children':len(body),'resolved_headings':heads,'inserted_numbered_headings':[x for x in heads if x['paragraph_mark_inserted'] and re.match(r'\d',x['text'])],'scope_conclusion_sections':sections,'cover_tables':cover,'all_target_or_workitem_context_mentions':mentions}
def main():
 assert not F.exists();F.mkdir()
 bp=P/'release_package/cqs/original_core_repair/provenance/original_benchmark.jsonl'
 raw=next(x for x in bp.read_bytes().splitlines(keepends=True) if json.loads(x)['id']==ID);q=json.loads(raw)
 assert q['question_en']=='Which new sections did the LP-WUS (Low-Power Wake-Up Signal) study TR 38.869 add to TS 38.211 and 38.213? (UE power-saving implementation)'
 (F/'original_benchmark_record.jsonl').write_bytes(raw)
 aq=R/'logs/tsg/RAN/formal/RAN1/phase-5/cq_test_dataset.json';a=load(aq);own=next(x for x in a['questions'] if x['id']=='CQ3-2');assert own['cypher']==q['cypher']
 copy('original_author_CQ_dataset.json',aq)
 criteria=A55/'actual_source_and_frozen/criteria.json';assert pin(criteria)['sha256']=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4';copy('criteria.json',criteria)
 save('original_question_and_query.json',{'id':ID,'original_record':q,'raw_record_sha256':sha(raw),'question_sha256':sha(q['question_en'].encode()),'query_sha256':sha(q['cypher'].encode()),'author_CQ_record':own,'original_benchmark':pin(bp),'scope_rule':'Both TS38.211 and38.213; actual new-section extent attributable to original LP-WUS study TR38.869, not merely manually declared NewSection records. Original four projected fields retained as evidence, no additional mandatory text field, arbitrary release cutoff or approved-only population invented.'})
 refs=[]
 for rel in ['docs/tsg/RAN/formal/RAN1/phase-5/step1_tr_parsing.md','docs/tsg/RAN/formal/RAN1/phase-5/step2_neo4j_loading.md','docs/tsg/RAN/formal/RAN1/phase-5/step3_validation.md','docs/tsg/RAN/formal/RAN1/phase-5/design-spec/tdoc_ontology_specs(TR).md','scripts/tsg/RAN/formal/RAN1/phase-5/tr-parser/02_generate_tr_jsonld.py']:
  p=R/rel;copy('author_context/'+p.name,p);refs.append(pin(p))
 save('original_author_context_provenance.json',refs)
 for n in ['tr_impact_mapping.csv','tr_workitem_mapping.csv']:copy('original_'+n,R/'ontology/input/tsg/RAN/formal/TR/RAN1'/n)
 before=pin(DB);assert before['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
 c=sqlite3.connect(DB.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
 base=""" FROM TechnicalReport tr JOIN rel_RELATED_TO_WORK_ITEM a ON a.src_id=tr.node_id JOIN WorkItem sw ON sw.node_id=a.dst_id JOIN WorkItem w ON substr(sw.workItemCode,1,3)='FS_' AND w.workItemCode IN(substr(sw.workItemCode,4),substr(sw.workItemCode,4)||'-Core') """
 queries={
 'original_projection':'''SELECT tr.trNumber AS "tr.trNumber",ti.affectedSection AS "ti.affectedSection",s.sectionId AS "s.sectionId",ti.impactDescription AS "ti.impactDescription" FROM TechnicalReport tr JOIN rel_HAS_TR_IMPACT h ON h.src_id=tr.node_id JOIN TRImpact ti ON ti.node_id=h.dst_id JOIN rel_IMPACTS_SECTION k ON k.src_id=ti.node_id JOIN Section s ON s.node_id=k.dst_id WHERE tr.trNumber='38.869' AND ti.impactType='NewSection' ORDER BY s.sectionId''',
 'inverse_projection':'''SELECT tr.trNumber AS "tr.trNumber",ti.affectedSection AS "ti.affectedSection",s.sectionId AS "s.sectionId",ti.impactDescription AS "ti.impactDescription" FROM TechnicalReport tr JOIN rel_IMPACT_OF_TR h ON h.dst_id=tr.node_id JOIN TRImpact ti ON ti.node_id=h.src_id JOIN rel_SECTION_IMPACTED_BY k ON k.dst_id=ti.node_id JOIN Section s ON s.node_id=k.src_id WHERE tr.trNumber='38.869' AND ti.impactType='NewSection' ORDER BY s.sectionId''',
 'all_own_impacts_and_section_titles':'''SELECT tr.*,ti.node_id AS impact_node,ti.trImpactId,ti.impactType,ti.affectedSection,ti.impactDescription,sp.node_id AS spec_node,sp.specNumber,s.node_id AS section_node,s.sectionId,s.sectionTitle FROM TechnicalReport tr LEFT JOIN rel_HAS_TR_IMPACT h ON h.src_id=tr.node_id LEFT JOIN TRImpact ti ON ti.node_id=h.dst_id LEFT JOIN rel_IMPACTS_SPEC k ON k.src_id=ti.node_id LEFT JOIN Spec sp ON sp.node_id=k.dst_id LEFT JOIN rel_IMPACTS_SECTION j ON j.src_id=ti.node_id LEFT JOIN Section s ON s.node_id=j.dst_id WHERE tr.trNumber='38.869' ORDER BY sp.specNumber,s.sectionId''',
 'all_own_study_WI_incident_roles':'''SELECT w.node_id AS WI_node,w.workItemCode,e.edge_id,e.src_id,e.rel_type,e.dst_id,n.labels FROM TechnicalReport tr JOIN rel_RELATED_TO_WORK_ITEM a ON a.src_id=tr.node_id JOIN WorkItem w ON w.node_id=a.dst_id JOIN edge e ON e.src_id=w.node_id OR e.dst_id=w.node_id JOIN node n ON n.node_id=CASE WHEN e.src_id=w.node_id THEN e.dst_id ELSE e.src_id END WHERE tr.trNumber='38.869' ORDER BY e.edge_id''',
 'all_WorkItem_identities':'SELECT * FROM WorkItem ORDER BY workItemCode,node_id',
 'all_own_naming_candidate_WIs':'''SELECT tr.trNumber,sw.workItemCode AS study_code,w.node_id AS candidate_node,w.workItemCode AS candidate_code'''+base+'''WHERE tr.trNumber='38.869' ORDER BY w.workItemCode''',
 'all_candidate_CR_all_spec_roles':'''SELECT w.workItemCode,cr.*,sp.specNumber'''+base+'''JOIN rel_RELATED_TO b ON b.dst_id=w.node_id JOIN CR cr ON cr.node_id=b.src_id LEFT JOIN rel_MODIFIES m ON m.src_id=cr.node_id LEFT JOIN Spec sp ON sp.node_id=m.dst_id WHERE tr.trNumber='38.869' ORDER BY w.workItemCode,cr.tdocNumber,sp.specNumber''',
 'all_candidate_CR_target_fields':'''SELECT w.workItemCode,cr.*,sp.node_id AS spec_node,sp.specNumber'''+base+'''JOIN rel_RELATED_TO b ON b.dst_id=w.node_id JOIN CR cr ON cr.node_id=b.src_id JOIN rel_MODIFIES m ON m.src_id=cr.node_id JOIN Spec sp ON sp.node_id=m.dst_id WHERE tr.trNumber='38.869' AND sp.specNumber IN ('38.211','38.213') ORDER BY sp.specNumber,cr.tdocNumber''',
 'all_candidate_CR_target_sections':'''SELECT w.workItemCode,cr.node_id AS CR_node,cr.tdocNumber,cr.status,cr.crCategory,cr.clausesAffected,sp.specNumber,s.node_id AS section_node,s.sectionId,s.sectionTitle'''+base+'''JOIN rel_RELATED_TO b ON b.dst_id=w.node_id JOIN CR cr ON cr.node_id=b.src_id JOIN rel_MODIFIES m ON m.src_id=cr.node_id JOIN Spec sp ON sp.node_id=m.dst_id LEFT JOIN rel_MODIFIES_SECTION j ON j.src_id=cr.node_id LEFT JOIN Section s ON s.node_id=j.dst_id WHERE tr.trNumber='38.869' AND sp.specNumber IN ('38.211','38.213') ORDER BY sp.specNumber,cr.tdocNumber,s.sectionId''',
 'all_target_Section_identities':"SELECT * FROM Section WHERE sectionId LIKE '38.211-%' OR sectionId LIKE '38.213-%' ORDER BY sectionId,node_id",
 'all_target_Spec_identities':"SELECT * FROM Spec WHERE specNumber IN ('38.211','38.213') ORDER BY specNumber,node_id",
 'all_TechnicalReport_identities':'SELECT * FROM TechnicalReport ORDER BY trNumber,node_id',
 'target_CR_topic_recovery':'''SELECT cr.*,sp.specNumber FROM CR cr JOIN rel_MODIFIES m ON m.src_id=cr.node_id JOIN Spec sp ON sp.node_id=m.dst_id WHERE sp.specNumber IN ('38.211','38.213') AND (lower(coalesce(cr.title,'')) LIKE '%wake%up%' OR lower(coalesce(cr.reasonForChange,'')) LIKE '%lp%wus%' OR lower(coalesce(cr.summaryOfChange,'')) LIKE '%lp%wus%') ORDER BY sp.specNumber,cr.tdocNumber'''}
 results={}
 for k,sql in queries.items():
  rows=[dict(x) for x in c.execute(sql)];results[k]={'sql':sql,'sql_sha256':sha(sql.encode()),'rows':rows,'row_count':len(rows)}
 assert results['original_projection']['rows']==results['inverse_projection']['rows']
 save('actual_immutable_SQL_diagnostics.json',results)
 labels=['TechnicalReport','TRImpact','Spec','Section','CR','WorkItem','Release','Tdoc']
 save('original_SQL_table_schemas.json',{t:[dict(x) for x in c.execute('PRAGMA table_info('+t+')')] for t in labels})
 core={x[0] for x in c.execute("SELECT node_id FROM TechnicalReport WHERE trNumber='38.869' UNION SELECT h.dst_id FROM rel_HAS_TR_IMPACT h JOIN TechnicalReport t ON t.node_id=h.src_id WHERE t.trNumber='38.869' UNION SELECT node_id FROM WorkItem WHERE workItemCode IN ('FS_NR_LPWUS','NR_LPWUS','NR_LPWUS-Core') UNION SELECT node_id FROM Spec WHERE specNumber IN ('38.211','38.213')")}
 core|={x['node_id'] for x in results['all_candidate_CR_all_spec_roles']['rows']}
 core|={x['node_id'] for x in results['target_CR_topic_recovery']['rows']}
 marks=','.join('?' for _ in core)
 edges=[dict(x) for x in c.execute('SELECT * FROM edge WHERE src_id IN ('+marks+') OR dst_id IN ('+marks+') ORDER BY edge_id',tuple(sorted(core))*2)]
 nodes=core|{e[k] for e in edges for k in ['src_id','dst_id']}|{x['node_id'] for x in results['all_target_Section_identities']['rows']}|{x['node_id'] for x in results['all_WorkItem_identities']['rows']}|{x['node_id'] for x in results['all_TechnicalReport_identities']['rows']}
 records=[dict(x) for n in sorted(nodes) for x in c.execute('SELECT * FROM _node_record WHERE node_id=?',(n,))]
 save('complete_own_and_alternative_role_slice.json',{'core_node_ids':sorted(core),'records':records,'edges':edges,'scope':'Complete incidence of own TR/impacts, both target Specs, all three study/naming-candidate WIs and every candidate or topic-recovered target CR. All target Section, WorkItem and TechnicalReport identities are additionally retained without asserting complete incidence of those extra population-only nodes. Naming/topic recovery are diagnostics, not causal gold.'})
 def strings(x):
  if isinstance(x,str):yield x
  elif isinstance(x,list):
   for y in x:yield from strings(y)
  elif isinstance(x,dict):
   for y in x.values():yield from strings(y)
 hits=[];node_n=0;scalar_n=0
 for x in c.execute('SELECT node_id,labels_json,properties_json FROM _node_record ORDER BY node_id'):
  node_n+=1;vs=list(strings(json.loads(x['properties_json'])));scalar_n+=len(vs)
  for v in vs:
   if re.search(r'38[.]869|LP[-_ ]?WUS|LP[-_ ]?WUR|low[- ]power wake',v,re.I):hits.append({'node_id':x['node_id'],'labels':json.loads(x['labels_json']),'value':v})
 save('whole_decoded_LPWUS_literal_frontier.json',{'nodes_scanned':node_n,'decoded_string_scalars_scanned':scalar_n,'literal_values':hits,'scope':'Explicit frozen-property topic/identity recovery frontier only, not universal causal completeness.'})
 candidates=results['all_candidate_CR_target_fields']['rows'];nums={x['tdocNumber'] for x in candidates}
 defs=[('TR38869',R/'ontology/input/tsg/RAN/formal/TR/RAN1/38.869/38869-i00.docx'),('TS38211',R/'ontology/input/tsg/RAN/formal/TS/RAN1/38.211/38211-j30.docx'),('TS38213',R/'ontology/input/tsg/RAN/formal/TS/RAN1/38.213/38213-j30.docx')]
 missing=[]
 for n in sorted(nums):
  ps=list((R/'ontology/input/tsg/RAN/formal/CR/RAN1').rglob('*'+n[3:]+'*'))
  if not ps:missing.append(n);continue
  assert len(ps)==1;defs.append(('CR'+n[3:],ps[0]))
 sources=[]
 for key,p in defs:
  with zipfile.ZipFile(p) as z:xml=z.read('word/document.xml');styles=z.read('word/styles.xml')
  for n,b in [('document.xml',xml),('styles.xml',styles)]:
   dst=F/'source'/key/(n+'.gz');dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(gzip.compress(b,mtime=0))
  sources.append({'archive':pin(p),**source_roles(key,xml,styles)})
 save('direct_original_source_format_and_scope.json',sources)
 shared=[]
 for n in ['ROOT_final_disposition.json','actual_source_and_frozen/source/TR38869/document.xml.gz','actual_source_and_frozen/source/TR38869/styles.xml.gz','actual_source_and_frozen/source/TS38211/document.xml.gz','actual_source_and_frozen/source/TS38211/styles.xml.gz','actual_source_and_frozen/actual_immutable_SQL_diagnostics.json','actual_source_and_frozen/actual_named_workitem_recovery_SQL.json']:
  shared.append(pin(A55/n))
 save('read_only_A55_shared_dependencies.json',shared)
 save('source_candidate_frontier.json',{'frozen_target_CR_n':len(candidates),'candidate_ids':sorted(nums),'actual_original_CR_form_n':len(defs)-3,'original_CR_forms_not_in_local_formal_CR_tree':missing,'meaning':'Every original formal CR file for the nine frozen target candidate IDs was reopened. The three earlier postponed/endorsed/reserved records retain their full frozen fields and incident roles; absence from this formal-CR tree is not universal original-document absence.'})
 c.close();after=pin(DB);assert before==after
 result={'status':'PASS_ORIGINAL_SOURCE_AND_IMMUTABLE_RECOVERY_REOPEN','id':ID,'question_sha256':sha(q['question_en'].encode()),'SQL_roles':{k:v['row_count'] for k,v in results.items()},'source_XML_style_pairs':len(sources),'complete_incident_core_nodes':len(core),'slice_records':len(records),'slice_edges':len(edges),'sqlite_before':before,'sqlite_after':after,'API_calls':0,'native_calls':0,'public_writes':0}
 save('actual_source_and_frozen_reopen_receipt.json',result);print(json.dumps(result))
def load(p):return json.loads(p.read_bytes())
if __name__=='__main__':main()
