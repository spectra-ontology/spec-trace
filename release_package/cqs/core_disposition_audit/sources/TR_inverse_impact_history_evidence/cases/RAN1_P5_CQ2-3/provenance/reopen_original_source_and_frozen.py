"""Reopen the original inverse TR-impact question, all retained TR sources and SQL."""
import argparse,csv,gzip,hashlib,io,json,re,sqlite3,sys,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
if sys.flags.optimize:raise SystemExit('Enabled checks required')
L=Path(__file__).resolve().parent
R=next(p for p in L.parents if (p/'CLAUDE.md').is_file())
ID='RAN1_P5_CQ2-3'
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W='{'+N['w']+'}'
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def active_text(x):
 out=[]
 def visit(y):
  if y.tag in {W+'del',W+'moveFrom'}:return
  if y.tag==W+'t':out.append(y.text or '')
  for z in y:visit(z)
 visit(x);return ''.join(out)
def para(x,i):
 sty=x.find('w:pPr/w:pStyle',N)
 return {'index':i,'style':sty.get(W+'val') if sty is not None else None,'text':active_text(x),
         'insertions':len(x.findall('.//w:ins',N)),'deletions':len(x.findall('.//w:del',N)),
         'moves_from':len(x.findall('.//w:moveFrom',N))}
def main(a):
 D=a.out.resolve();assert not D.exists();D.mkdir(parents=True)
 def save(n,x):
  p=D/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');return pin(p)
 def cp(n,p):
  d=D/n;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(p.read_bytes());return pin(p)
 b=a.public_root/'release_package/cqs/original_core_repair/provenance/original_benchmark.jsonl'
 raw=[l for l in b.read_bytes().splitlines(keepends=True) if json.loads(l)['id']==ID];assert len(raw)==1
 q=json.loads(raw[0]);assert q['question_en']=='List every TR that affected TS 38.211 and its impact type (revision history of 38.211).'
 (D/'original_benchmark_record.jsonl').write_bytes(raw[0])
 cqpath=R/'logs/tsg/RAN/formal/RAN1/phase-5/cq_test_dataset.json';cq=json.loads(cqpath.read_bytes())
 own=[x for x in cq['questions'] if x['id']=='CQ2-3'];assert len(own)==1 and own[0]['cypher']==q['cypher']
 cp('original_author_CQ_dataset.json',cqpath)
 criteria=a.public_root/'release_package/cqs/original_core_overnight_repairs48/criteria.json'
 assert pin(criteria)['sha256']=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
 cp('criteria.json',criteria)
 save('original_question_and_query.json',{'id':ID,'original_record':q,'raw_record_sha256':sha(raw[0]),
   'question_sha256':sha(q['question_en'].encode()),'query_sha256':sha(q['cypher'].encode()),'criteria':pin(criteria),
   'original_benchmark':pin(b),'author_CQ_file':pin(cqpath),'author_CQ_record':own[0],
   'scope_rule':'Preserve original TS38.211 inverse research-to-specification history and every TR/type. Five projected columns provide supporting original-query evidence; no additional mandatory answer field or arbitrary release cutoff is invented.'})
 refs=[]
 for rel in ['docs/tsg/RAN/formal/RAN1/phase-5/step1_tr_parsing.md','docs/tsg/RAN/formal/RAN1/phase-5/step2_neo4j_loading.md',
  'docs/tsg/RAN/formal/RAN1/phase-5/step3_validation.md','docs/tsg/RAN/formal/RAN1/phase-5/design-spec/tdoc_ontology_specs(TR).md',
  'scripts/tsg/RAN/formal/RAN1/phase-5/tr-parser/02_generate_tr_jsonld.py']:
  p=R/rel;cp('author_context/'+p.name,p);refs.append({'source':pin(p),'included':'author_context/'+p.name,
   'role':'Original-author design context and current implementation counterauthority, read separately from factual standardization evidence'})
 save('author_implementation_and_counterauthority_sources.json',refs)
 for name in ['tr_impact_mapping.csv','tr_workitem_mapping.csv']:
  p=R/'ontology/input/tsg/RAN/formal/TR/RAN1'/name;cp('original_'+name,p)
  rs=list(csv.DictReader(io.StringIO(p.read_text())))
  save(name+'.selected.json',{'source':pin(p),'all_rows':len(rs),'TS38211_rows':[x for x in rs if x.get('impactsSpec')=='38.211']})
 meta=R/'ontology/output/tsg/RAN/formal/parsed_tr/RAN1/tr_metadata.json'
 cp('source_selection_metadata.json',meta);ms=json.loads(meta.read_bytes())['technicalReports'];assert len(ms)==26
 # Metadata chooses an existing original body file only; it does not supply factual impacts.
 defs=[('TR'+x['trNumber'].replace('.','').replace('-','_'),R/'ontology/input/tsg/RAN/formal/TR/RAN1'/x['trNumber']/x['sourceFile']) for x in ms]
 ts=list((R/'ontology/input/tsg/RAN/formal/TS/RAN1/38.211').glob('*.docx'));assert len(ts)==1
 cr=list((R/'ontology/input/tsg/RAN/formal/CR/RAN1').rglob('*1913630*'));assert len(cr)==1
 defs += [('TS38211',ts[0]),('CR1913630',cr[0])]
 sources=[]
 for key,p in defs:
  with zipfile.ZipFile(p) as z:xml=z.read('word/document.xml');styles=z.read('word/styles.xml')
  body=ET.fromstring(xml).find('w:body',N);ps=body.findall('w:p',N);paras=[para(x,i) for i,x in enumerate(ps)]
  s={'key':key,'archive':pin(p),'document_xml':{'bytes':len(xml),'sha256':sha(xml)},'styles_xml':{'bytes':len(styles),'sha256':sha(styles)},
   'body_children':len(body),'direct_body_paragraphs':len(ps),'all_heading1_paragraphs':[x for x in paras if x['style']=='Heading1']}
  for name,data in [('document.xml',xml),('styles.xml',styles)]:
   out=D/'source'/key/(name+'.gz');out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(gzip.compress(data,mtime=0))
  scopes=[]
  for j,x in enumerate(paras):
   if x['style']=='Heading1' and re.search(r'Scope|Conclusions?|Summary',x['text'],re.I):
    end=next((k for k in range(j+1,len(paras)) if paras[k]['style']=='Heading1'),len(paras))
    scopes.append({'heading':x,'direct_body_paragraphs':paras[j:end]})
  s['scope_conclusions_and_summary_sections']=scopes
  witnesses=[]
  for i,x in enumerate(body):
   t=active_text(x)
   if re.search(r'(?:TS\s*)?38[. ]211|avoid any changes to physical layer channels|no\s+(?:new\s+)?(?:physical\s+)?channels?\s+or\s+signals?',t,re.I):
    witnesses.append({'body_child':i,'tag':x.tag.removeprefix(W),'text':t,
      'preceding_text':active_text(body[i-1]) if i else '', 'following_text':active_text(body[i+1]) if i+1<len(body) else '',
      'table_rows':[[active_text(tc) for tc in tr.findall('w:tc',N)] for tr in x.findall('w:tr',N)]})
  s['all_target_TS_or_avoid_channel_reference_blocks']=witnesses
  if key=='TS38211':
   s['top_level_headings']=s['all_heading1_paragraphs']
   s['sensing_repeater_LPWUS_mentions']=[x for x in paras if re.search(r'ISAC|integrated sensing|network.controlled repeat|low.power wake|LP.WUS|LP.WUR',x['text'],re.I)]
  if key=='CR1913630':
   tbl=body[6];assert tbl.tag==W+'tbl'
   s['cover_table_body_child']=6;s['cover_rows']=[{'row':i,'cells':[active_text(tc) for tc in tr.findall('w:tc',N)]} for i,tr in enumerate(tbl.findall('w:tr',N))]
   s['all_heading_or_inserted_4446_blocks']=[{'body_child':i,**para(x,i)} for i,x in enumerate(body) if x.tag==W+'p' and (re.match(r'4\.4\.(?:4\.)?6\D',active_text(x)) or ((x.find('w:pPr/w:pStyle',N) is not None) and x.find('w:pPr/w:pStyle',N).get(W+'val','').startswith('Heading')))]
  sources.append(s)
 save('direct_original_source_and_format.json',sources)
 before=pin(a.sqlite);assert before['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
 c=sqlite3.connect(a.sqlite.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
 queries={
 'original_projection':'''SELECT tr.trNumber AS "tr.trNumber",tr.trTitle AS "tr.trTitle",ti.impactType AS "ti.impactType",ti.affectedSection AS "ti.affectedSection",ti.impactDescription AS "ti.impactDescription"
 FROM Spec sp JOIN rel_IMPACTS_SPEC m ON m.dst_id=sp.node_id JOIN TRImpact ti ON ti.node_id=m.src_id JOIN rel_HAS_TR_IMPACT h ON h.dst_id=ti.node_id JOIN TechnicalReport tr ON tr.node_id=h.src_id WHERE sp.specNumber='38.211' ORDER BY tr.trNumber''',
 'inverse_alias_projection':'''SELECT tr.trNumber AS "tr.trNumber",tr.trTitle AS "tr.trTitle",ti.impactType AS "ti.impactType",ti.affectedSection AS "ti.affectedSection",ti.impactDescription AS "ti.impactDescription"
 FROM Spec sp JOIN rel_SPEC_IMPACTED_BY m ON m.src_id=sp.node_id JOIN TRImpact ti ON ti.node_id=m.dst_id JOIN rel_IMPACT_OF_TR h ON h.src_id=ti.node_id JOIN TechnicalReport tr ON tr.node_id=h.dst_id WHERE sp.specNumber='38.211' ORDER BY tr.trNumber''',
 'all_original_TRs_and_all_impacts':'''SELECT tr.*,r.releaseName,ti.node_id AS impact_node,ti.trImpactId,ti.impactType,ti.affectedSection,ti.impactDescription,sp.node_id AS spec_node,sp.specNumber,sp.specRelease,s.sectionId,s.sectionTitle
 FROM TechnicalReport tr LEFT JOIN rel_TARGET_RELEASE rr ON rr.src_id=tr.node_id LEFT JOIN Release r ON r.node_id=rr.dst_id LEFT JOIN rel_HAS_TR_IMPACT h ON h.src_id=tr.node_id LEFT JOIN TRImpact ti ON ti.node_id=h.dst_id LEFT JOIN rel_IMPACTS_SPEC m ON m.src_id=ti.node_id LEFT JOIN Spec sp ON sp.node_id=m.dst_id LEFT JOIN rel_IMPACTS_SECTION k ON k.src_id=ti.node_id LEFT JOIN Section s ON s.node_id=k.dst_id ORDER BY tr.trNumber,sp.specNumber,s.sectionId''',
 'all_target_TS38211_impacts_and_sections':'''SELECT tr.trNumber,tr.trTitle,ti.*,sp.node_id AS spec_node,sp.specNumber,sp.specRelease,sp.specVersion,s.node_id AS section_node,s.sectionId,s.sectionTitle
 FROM Spec sp JOIN rel_IMPACTS_SPEC m ON m.dst_id=sp.node_id JOIN TRImpact ti ON ti.node_id=m.src_id JOIN rel_HAS_TR_IMPACT h ON h.dst_id=ti.node_id JOIN TechnicalReport tr ON tr.node_id=h.src_id LEFT JOIN rel_IMPACTS_SECTION k ON k.src_id=ti.node_id LEFT JOIN Section s ON s.node_id=k.dst_id WHERE sp.specNumber='38.211' ORDER BY tr.trNumber,s.sectionId''',
 'TR_workitem_CR_target_alternative':'''SELECT tr.trNumber,w.workItemCode,cr.node_id AS cr_node,cr.id,cr.title,cr.status,cr.crCategory,cr.clausesAffected,cr.reasonForChange,cr.summaryOfChange,sp.specNumber,sp.specRelease,s.sectionId,s.sectionTitle
 FROM TechnicalReport tr JOIN rel_RELATED_TO_WORK_ITEM w1 ON w1.src_id=tr.node_id JOIN WorkItem w ON w.node_id=w1.dst_id LEFT JOIN rel_RELATED_TO w2 ON w2.dst_id=w.node_id LEFT JOIN CR cr ON cr.node_id=w2.src_id LEFT JOIN rel_MODIFIES m ON m.src_id=cr.node_id LEFT JOIN Spec sp ON sp.node_id=m.dst_id LEFT JOIN rel_MODIFIES_SECTION k ON k.src_id=cr.node_id LEFT JOIN Section s ON s.node_id=k.dst_id WHERE sp.specNumber='38.211' OR cr.node_id IS NULL ORDER BY tr.trNumber,cr.id,s.sectionId''',
 'all_TR_workitem_role_populations':'''SELECT tr.trNumber,w.workItemCode,e.rel_type,n.labels,count(*) AS edge_n FROM TechnicalReport tr JOIN rel_RELATED_TO_WORK_ITEM w1 ON w1.src_id=tr.node_id JOIN WorkItem w ON w.node_id=w1.dst_id LEFT JOIN edge e ON e.src_id=w.node_id OR e.dst_id=w.node_id LEFT JOIN node n ON n.node_id=CASE WHEN e.src_id=w.node_id THEN e.dst_id ELSE e.src_id END GROUP BY tr.trNumber,w.workItemCode,e.rel_type,n.labels ORDER BY tr.trNumber,w.workItemCode,e.rel_type,n.labels''',
 'NRU_normative_workitem_source_alternative':'''SELECT w.workItemCode,cr.node_id,cr.id,cr.title,cr.status,cr.crCategory,cr.clausesAffected,cr.reasonForChange,cr.summaryOfChange,s.sectionId,s.sectionTitle FROM WorkItem w JOIN rel_RELATED_TO r ON r.dst_id=w.node_id JOIN CR cr ON cr.node_id=r.src_id JOIN rel_MODIFIES m ON m.src_id=cr.node_id JOIN Spec sp ON sp.node_id=m.dst_id LEFT JOIN rel_MODIFIES_SECTION k ON k.src_id=cr.node_id LEFT JOIN Section s ON s.node_id=k.dst_id WHERE w.workItemCode='NR_unlic-Core' AND sp.specNumber='38.211' ORDER BY cr.id,s.sectionId'''}
 results={}
 for name,sql in queries.items():
  rows=[dict(x) for x in c.execute(sql)];results[name]={'sql':sql,'sql_sha256':sha(sql.encode()),'rows':rows,'row_count':len(rows)}
 assert results['original_projection']['rows']==results['inverse_alias_projection']['rows']
 save('actual_immutable_SQL_diagnostics.json',results)
 labels=['TechnicalReport','TRImpact','Spec','Section','CR','WorkItem','Release']
 save('original_SQL_table_schemas.json',{t:[dict(x) for x in c.execute('PRAGMA table_info("'+t+'")')] for t in labels})
 core={x[0] for x in c.execute("SELECT node_id FROM TechnicalReport UNION SELECT node_id FROM TRImpact UNION SELECT node_id FROM Spec WHERE specNumber='38.211'")}
 core|={x[0] for x in c.execute('SELECT w.dst_id FROM rel_RELATED_TO_WORK_ITEM w JOIN TechnicalReport t ON t.node_id=w.src_id')}
 core|={x[0] for x in c.execute('SELECT cr.node_id FROM TechnicalReport t JOIN rel_RELATED_TO_WORK_ITEM w ON w.src_id=t.node_id JOIN rel_RELATED_TO q ON q.dst_id=w.dst_id JOIN CR cr ON cr.node_id=q.src_id')}
 core|={x[0] for x in c.execute("SELECT cr.node_id FROM CR cr JOIN rel_RELATED_TO r ON r.src_id=cr.node_id JOIN WorkItem w ON w.node_id=r.dst_id WHERE w.workItemCode='NR_unlic-Core'")}
 marks=','.join('?' for _ in core)
 edges=[dict(x) for x in c.execute('SELECT * FROM edge WHERE src_id IN ('+marks+') OR dst_id IN ('+marks+') ORDER BY edge_id',tuple(sorted(core))*2)]
 nodes=core|{e[k] for e in edges for k in ['src_id','dst_id']}
 records=[dict(x) for n in sorted(nodes) for x in c.execute('SELECT * FROM _node_record WHERE node_id=?',(n,))]
 save('all_retained_TR_impacts_target_specs_workitems_and_CR_incident_slice.json',{'core_node_ids':sorted(core),'records':records,'edges':edges,
 'scope':'Every retained TechnicalReport and TRImpact, all TS38.211 Spec versions, every TR WorkItem, all associated CRs and NR_unlic-Core CRs have complete incident edges. Endpoint records are preserved; this is not a substitute complete global graph.'})
 def strings(x):
  if isinstance(x,str):yield x
  elif isinstance(x,list):
   for v in x:yield from strings(v)
  elif isinstance(x,dict):
   for v in x.values():yield from strings(v)
 allnodes=0;scalar_n=0;hits=[]
 for row in c.execute('SELECT node_id,labels_json,properties_json FROM _node_record ORDER BY node_id'):
  allnodes+=1;vals=list(strings(json.loads(row['properties_json'])));scalar_n+=len(vals)
  for value in vals:
   if re.search(r'38\.211',value):hits.append({'node_id':row['node_id'],'labels':json.loads(row['labels_json']),'value':value})
 save('whole_decoded_frozen_target_TS_literal_frontier.json',{'all_node_records_scanned':allnodes,'decoded_string_scalars_scanned':scalar_n,
  'target_TS_literal_values':hits,'meaning':'Explicit retained-role recovery alternative only; literal presence/absence is not proof of arbitrary causal attribution or complete history.'})
 c.close();after=pin(a.sqlite);assert before==after
 receipt={'status':'COMPLETED_ORIGINAL_SOURCE_AND_IMMUTABLE_SQL_REOPEN','id':ID,'original_question_sha256':sha(q['question_en'].encode()),
  'original_SQL_roles':{k:v['row_count'] for k,v in results.items()},'source_n':len(sources),'TR_source_n':26,
  'complete_incident_core_nodes':len(core),'slice_records':len(records),'slice_edges':len(edges),
  'sqlite_before':before,'sqlite_after':after,'API_calls':0,'native_calls':0,'P_mutations':0}
 save('actual_source_and_frozen_reopen_receipt.json',receipt);print(json.dumps(receipt))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--sqlite',type=Path,required=True);ap.add_argument('--public-root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
 main(ap.parse_args())
