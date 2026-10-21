"""Resolve original styles and preserve actual naming-based recovery alternatives."""
import gzip,hashlib,json,re,sqlite3,sys,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
from reopen_original_source_and_frozen import active_text,para,N,W,pin,sha
L=Path(__file__).resolve().parent;F=L/'actual_source_and_frozen'
R=next(p for p in L.parents if (p/'CLAUDE.md').is_file())
if sys.flags.optimize:raise SystemExit('Enabled checks required')
def save(name,value):
 p=F/name;assert not p.exists();p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');return pin(p)
styles=[]
for s in json.loads((F/'direct_original_source_and_format.json').read_bytes()):
 if not s['key'].startswith('TR'):continue
 body=ET.fromstring(gzip.decompress((F/'source'/s['key']/'document.xml.gz').read_bytes())).find('w:body',N)
 st=ET.fromstring(gzip.decompress((F/'source'/s['key']/'styles.xml.gz').read_bytes()))
 sm={x.get(W+'styleId'):x for x in st if x.tag==W+'style'}
 def outline(style,seen=()):
  if style not in sm or style in seen:return None
  el=sm[style];v=el.find('w:pPr/w:outlineLvl',N)
  if v is not None:return int(v.get(W+'val'))
  nm=el.find('w:name',N)
  if nm is not None and re.fullmatch(r'heading\s*1',nm.get(W+'val',''),re.I):return 0
  par=el.find('w:basedOn',N)
  return outline(par.get(W+'val'),seen+(style,)) if par is not None else None
 ps=body.findall('w:p',N);paras=[para(p,i) for i,p in enumerate(ps)]
 heads=[];sections=[]
 for i,p in enumerate(ps):
  row=paras[i];direct=p.find('w:pPr/w:outlineLvl',N)
  level=int(direct.get(W+'val')) if direct is not None else outline(row['style'])
  if level==0:heads.append(row)
  if re.fullmatch(r'\d+\s*(?:Scope|Conclusions?|Summary)(?:\s+and\s+recommendations)?\s*',row['text'],re.I):
   end=len(ps)
   for j in range(i+1,len(ps)):
    pr=ps[j];ol=pr.find('w:pPr/w:outlineLvl',N)
    lev=int(ol.get(W+'val')) if ol is not None else outline(paras[j]['style'])
    if lev==0 or re.match(r'Annex\s+[<A-Z]',paras[j]['text']):end=j;break
   sections.append({'heading':row,'heading_outline':level,'direct_body_paragraphs':paras[i:end]})
 styles.append({'key':s['key'],'document_xml':s['document_xml'],'styles_xml':s['styles_xml'],
  'resolved_outline0_headings':heads,'numeric_scope_and_conclusion_blocks':sections,
  'meaning':'Original raw XML/style role audit, including localized style IDs and physically unstyled numbered Conclusion headings. This is source evidence, not a new benchmark population rule.'})
save('actual_original_style_and_scope_role_reopen.json',styles)
db=R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/authorized_incremental48_OpenRouter_release/evaluation/runtime/relational/RAN1.sqlite'
before=pin(db);c=sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
common=""" FROM TechnicalReport tr JOIN rel_RELATED_TO_WORK_ITEM r ON r.src_id=tr.node_id JOIN WorkItem sw ON sw.node_id=r.dst_id JOIN WorkItem w ON substr(sw.workItemCode,1,3)='FS_' AND w.workItemCode IN (substr(sw.workItemCode,4),substr(sw.workItemCode,4)||'-Core') """
queries={
 'all_WorkItem_identities':'SELECT * FROM WorkItem ORDER BY workItemCode,node_id',
 'all_prefix_related_normative_candidates':'''SELECT tr.trNumber,sw.workItemCode AS study_code,w.node_id AS naming_candidate_node,w.workItemCode AS naming_candidate_code,count(distinct cr.node_id) AS target_CR_n'''+common+'''LEFT JOIN rel_RELATED_TO k ON k.dst_id=w.node_id LEFT JOIN CR cr ON cr.node_id=k.src_id AND cr.node_id IN (SELECT m.src_id FROM rel_MODIFIES m JOIN Spec sp ON sp.node_id=m.dst_id WHERE sp.specNumber='38.211') GROUP BY tr.trNumber,sw.workItemCode,w.node_id,w.workItemCode ORDER BY tr.trNumber,w.workItemCode''',
 'full_prefix_candidate_CR_target_projection':'''SELECT tr.trNumber,sw.workItemCode AS study_code,w.workItemCode AS naming_candidate_code,cr.node_id AS cr_node,cr.id,cr.tdocNumber,cr.title,cr.status,cr.crCategory,cr.clausesAffected,cr.reasonForChange,cr.summaryOfChange,s.sectionId,s.sectionTitle'''+common+'''JOIN rel_RELATED_TO k ON k.dst_id=w.node_id JOIN CR cr ON cr.node_id=k.src_id JOIN rel_MODIFIES m ON m.src_id=cr.node_id JOIN Spec sp ON sp.node_id=m.dst_id LEFT JOIN rel_MODIFIES_SECTION n ON n.src_id=cr.node_id LEFT JOIN Section s ON s.node_id=n.dst_id WHERE sp.specNumber='38.211' ORDER BY tr.trNumber,w.workItemCode,cr.tdocNumber,s.sectionId''',
 'source_witness_CR_R12504980':"SELECT cr.* FROM CR cr WHERE tdocNumber='R1-2504980' ORDER BY node_id"
}
results={}
for name,sql in queries.items():
 rs=[dict(x) for x in c.execute(sql)];results[name]={'sql':sql,'sql_sha256':sha(sql.encode()),'rows':rs,'row_count':len(rs)}
save('actual_named_workitem_recovery_SQL.json',results)
base=json.loads((F/'all_retained_TR_impacts_target_specs_workitems_and_CR_incident_slice.json').read_bytes())
core=set(base['core_node_ids'])|{x['node_id'] for x in results['all_WorkItem_identities']['rows']}
core|={x['cr_node'] for x in results['full_prefix_candidate_CR_target_projection']['rows']}
marks=','.join('?' for _ in core)
edges=[dict(x) for x in c.execute('SELECT * FROM edge WHERE src_id IN ('+marks+') OR dst_id IN ('+marks+') ORDER BY edge_id',tuple(sorted(core))*2)]
nodes=core|{e[k] for e in edges for k in ['src_id','dst_id']}
records=[dict(x) for n in sorted(nodes) for x in c.execute('SELECT * FROM _node_record WHERE node_id=?',(n,))]
save('extended_all_TR_WI_and_candidate_CR_incident_slice.json',{'core_node_ids':sorted(core),'records':records,'edges':edges,
 'scope':'Original full slice plus all 423 WorkItem identity nodes and complete incidence of every target-TS CR from the reproducible FS-prefix naming candidate recovery. A naming correspondence is preserved as a candidate, not assumed causal proof.'})
c.close();assert pin(db)==before
ps=list((R/'ontology/input/tsg/RAN/formal/CR/RAN1').rglob('*2504980*'));assert len(ps)==1;p=ps[0]
with zipfile.ZipFile(p) as z:xml=z.read('word/document.xml');sty=z.read('word/styles.xml')
key='CR2504980'
for name,data in [('document.xml',xml),('styles.xml',sty)]:
 d=F/'source'/key/(name+'.gz');d.parent.mkdir(parents=True,exist_ok=True);assert not d.exists();d.write_bytes(gzip.compress(data,mtime=0))
body=ET.fromstring(xml).find('w:body',N)
tables=[{'body_child':i,'rows':[[active_text(tc) for tc in tr.findall('w:tc',N)] for tr in x.findall('w:tr',N)]} for i,x in enumerate(body) if x.tag==W+'tbl' and re.search(r'Work item code|Clauses affected|CHANGE REQUEST',active_text(x),re.I)]
save('actual_source_CR2504980_and_named_role_receipt.json',{'key':key,'archive':pin(p),'document_xml':{'bytes':len(xml),'sha256':sha(xml)},'styles_xml':{'bytes':len(sty),'sha256':sha(sty)},'cover_tables':tables,
 'actual_SQL_roles':{k:v['row_count'] for k,v in results.items()},'slice_core':len(core),'slice_records':len(records),'slice_edges':len(edges),
 'sqlite_before':before,'sqlite_after':pin(db),'API_calls':0,'native_calls':0,'P_mutations':0})
print(json.dumps({'status':'COMPLETED','original_TR_style_audits':len(styles),'additional_source_CR':key,'slice_records':len(records),'slice_edges':len(edges),'SQL_roles':{k:v['row_count'] for k,v in results.items()}}))
