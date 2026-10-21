"""Actual read-only original-question and complete retained role diagnostics."""
import csv,gzip,hashlib,io,json,re,sqlite3,sys,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
if sys.flags.optimize: raise SystemExit('Enabled checks required')
L=Path(__file__).resolve().parent
R=next(x for x in L.parents if (x/'CLAUDE.md').is_file())
B=R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit'
A=L.parents[1]/'main_A/RAN1_P5_CQ2-3/actual_source_and_frozen'
P=R.parent/'spectra-public/spec-trace'
DB=B/'authorized_incremental48_OpenRouter_release/evaluation/runtime/relational/RAN1.sqlite'
D=L/'actual_original_and_frozen_v2'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
NS={'w':W[1:-1]}
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def save(name,x):
 p=D/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');return pin(p)
def cp(name,p):
 t=D/name;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(p.read_bytes());return pin(t)
def active(x):
 if x.tag in {W+'del',W+'moveFrom'}:return ''
 return (x.text or '') if x.tag==W+'t' else ''.join(active(y) for y in x)
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,list):
  for v in x:yield from strings(v)
 elif isinstance(x,dict):
  for v in x.values():yield from strings(v)
def main():
 assert not D.exists();D.mkdir(parents=True)
 benchmark=P/'release_package/cqs/original_core_repair/provenance/original_benchmark.jsonl'
 raw=[x for x in benchmark.read_bytes().splitlines(keepends=True) if json.loads(x)['id']=='RAN1_P5_CQ3-1'];assert len(raw)==1
 q=json.loads(raw[0]);assert q['question_en']=='Which TS sections did the RedCap (Reduced Capability) study TR 38.875 affect? (low-power IoT reference)'
 (D/'original_benchmark_record.jsonl').write_bytes(raw[0])
 author=R/'logs/tsg/RAN/formal/RAN1/phase-5/cq_test_dataset.json'
 aq=[x for x in json.loads(author.read_bytes())['questions'] if x['id']=='CQ3-1'];assert len(aq)==1 and aq[0]['cypher']==q['cypher']
 cp('original_author_CQ_dataset.json',author);cp('criteria.json',A/'criteria.json')
 save('original_question_and_query.json',{'id':q['id'],'original_record':q,'raw_record_sha256':sha(raw[0]),'question_sha256':sha(q['question_en'].encode()),'query_sha256':sha(q['cypher'].encode()),'benchmark':pin(benchmark),'author_file':pin(author),'original_Korean_record':aq[0], 'requested_role':'Actual affected TS Sections for the named RedCap study, with TS identity carried by each Section ID. Original projected title/type/description remain evidence; mandatory answer roles must follow original question rather than all projected diagnostic columns.'})
 for name in ['step1_tr_parsing.md','step2_neo4j_loading.md','step3_validation.md','tdoc_ontology_specs(TR).md','02_generate_tr_jsonld.py']:
  cp('author_context/'+name,A/'author_context'/name)
 for n in ['tr_impact_mapping.csv','tr_workitem_mapping.csv']:
  p=R/'ontology/input/tsg/RAN/formal/TR/RAN1'/n;cp('original_'+n,p)
  rows=list(csv.DictReader(io.StringIO(p.read_text())));save(n+'.own.json',{'source':pin(p),'all_row_n':len(rows),'own_rows':[x for x in rows if x['trNumber']=='38.875']})
 original=next(x for x in json.loads((A/'direct_original_source_and_format.json').read_text()) if x['key']=='TR38875')
 p=Path(original['archive']['path']);assert pin(p)==original['archive']
 with zipfile.ZipFile(p) as z:xml=z.read('word/document.xml');styles=z.read('word/styles.xml')
 assert sha(xml)==original['document_xml']['sha256'] and sha(styles)==original['styles_xml']['sha256']
 for n,b in [('document.xml',xml),('styles.xml',styles)]:
  t=D/'source/TR38875'/(n+'.gz');t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(gzip.compress(b,mtime=0))
 body=ET.fromstring(xml).find('w:body',NS)
 blocks=[{'body_child':i,'tag':x.tag.removeprefix(W),'text':active(x),'table_rows':[[active(tc) for tc in row.findall('w:tc',NS)] for row in x.findall('w:tr',NS)]} for i,x in enumerate(body)]
 save('TR38875_all_original_active_body_blocks.json',{'archive':pin(p),'document_xml':original['document_xml'],'styles_xml':original['styles_xml'],'index_scheme':'Zero-based direct w:body child, tables retained as single blocks and structured rows; deleted/moveFrom text excluded, current inserted text retained.','blocks':blocks})
 styles_reopen=next(x for x in json.loads((A/'actual_original_style_and_scope_role_reopen.json').read_text()) if x['key']=='TR38875')
 save('TR38875_independently_reopened_source_and_prior_style_locator.json',{'own_archive_reopened':pin(p),'own_XML_sha256':sha(xml),'prior_source_metadata':original,'prior_resolved_style_locator':styles_reopen,'role':'Prior style resolution locates source passages; own current archive and XML have been reopened directly.'})
 before=pin(DB);assert before['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
 c=sqlite3.connect(DB.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
 qs={
 'original_projection':'''SELECT tr.trNumber AS "tr.trNumber",tr.trTitle AS "tr.trTitle",ti.impactType AS "ti.impactType",s.sectionId AS "s.sectionId",ti.impactDescription AS "ti.impactDescription" FROM TechnicalReport tr JOIN rel_HAS_TR_IMPACT h ON h.src_id=tr.node_id JOIN TRImpact ti ON ti.node_id=h.dst_id JOIN rel_IMPACTS_SECTION k ON k.src_id=ti.node_id JOIN Section s ON s.node_id=k.dst_id WHERE tr.trNumber='38.875' ORDER BY s.sectionId''',
 'inverse_alias_projection':'''SELECT tr.trNumber AS "tr.trNumber",tr.trTitle AS "tr.trTitle",ti.impactType AS "ti.impactType",s.sectionId AS "s.sectionId",ti.impactDescription AS "ti.impactDescription" FROM TechnicalReport tr JOIN rel_IMPACT_OF_TR h ON h.dst_id=tr.node_id JOIN TRImpact ti ON ti.node_id=h.src_id JOIN rel_SECTION_IMPACTED_BY k ON k.dst_id=ti.node_id JOIN Section s ON s.node_id=k.src_id WHERE tr.trNumber='38.875' ORDER BY s.sectionId''',
 'all_own_impacts_specs_and_optional_sections':'''SELECT tr.*,r.releaseName,ti.node_id AS impact_node,ti.trImpactId,ti.impactType,ti.affectedSection,ti.impactDescription,sp.node_id AS spec_node,sp.specNumber,sp.specRelease,sp.specVersion,s.node_id AS section_node,s.sectionId,s.sectionNumber,s.sectionTitle FROM TechnicalReport tr LEFT JOIN rel_TARGET_RELEASE rr ON rr.src_id=tr.node_id LEFT JOIN Release r ON r.node_id=rr.dst_id LEFT JOIN rel_HAS_TR_IMPACT h ON h.src_id=tr.node_id LEFT JOIN TRImpact ti ON ti.node_id=h.dst_id LEFT JOIN rel_IMPACTS_SPEC m ON m.src_id=ti.node_id LEFT JOIN Spec sp ON sp.node_id=m.dst_id LEFT JOIN rel_IMPACTS_SECTION k ON k.src_id=ti.node_id LEFT JOIN Section s ON s.node_id=k.dst_id WHERE tr.trNumber='38.875' ORDER BY sp.specNumber,s.sectionId''',
 'own_workitem_CR_all_TS_alternative':'''SELECT tr.trNumber,w.node_id AS workitem_node,w.workItemCode,cr.*,sp.specNumber,sp.specRelease,s.sectionId,s.sectionTitle FROM TechnicalReport tr JOIN rel_RELATED_TO_WORK_ITEM w1 ON w1.src_id=tr.node_id JOIN WorkItem w ON w.node_id=w1.dst_id LEFT JOIN rel_RELATED_TO w2 ON w2.dst_id=w.node_id LEFT JOIN CR cr ON cr.node_id=w2.src_id LEFT JOIN rel_MODIFIES m ON m.src_id=cr.node_id LEFT JOIN Spec sp ON sp.node_id=m.dst_id LEFT JOIN rel_MODIFIES_SECTION k ON k.src_id=cr.node_id LEFT JOIN Section s ON s.node_id=k.dst_id WHERE tr.trNumber='38.875' ORDER BY cr.id,s.sectionId''',
 'all_WorkItem_identities':'''SELECT * FROM WorkItem ORDER BY workItemCode,node_id''',
 'all_RedCap_named_workitem_CR_TS_Section_candidates':'''SELECT w.node_id AS workitem_node,w.workItemCode,cr.*,sp.node_id AS spec_node,sp.specNumber,sp.specRelease,s.node_id AS section_node,s.sectionId,s.sectionTitle FROM WorkItem w LEFT JOIN rel_RELATED_TO r ON r.dst_id=w.node_id LEFT JOIN CR cr ON cr.node_id=r.src_id LEFT JOIN rel_MODIFIES m ON m.src_id=cr.node_id LEFT JOIN Spec sp ON sp.node_id=m.dst_id LEFT JOIN rel_MODIFIES_SECTION k ON k.src_id=cr.node_id LEFT JOIN Section s ON s.node_id=k.dst_id WHERE lower(w.workItemCode) LIKE '%redcap%' ORDER BY w.workItemCode,cr.id,s.sectionId''',
 'own_affected_sections_same_number_all_spec_releases':'''SELECT ti.trImpactId,sp.specNumber,ti.affectedSection,s.* FROM TechnicalReport tr JOIN rel_HAS_TR_IMPACT h ON h.src_id=tr.node_id JOIN TRImpact ti ON ti.node_id=h.dst_id JOIN rel_IMPACTS_SPEC m ON m.src_id=ti.node_id JOIN Spec sp ON sp.node_id=m.dst_id JOIN Section s ON s.sectionNumber=ti.affectedSection AND substr(s.sectionId,1,length(sp.specNumber)+1)=sp.specNumber||'-' WHERE tr.trNumber='38.875' ORDER BY sp.specNumber,s.sectionId'''
 }
 # Discover actual inverse alias name before recording a query; no assumed relation.
 rels={x[0] for x in c.execute('SELECT DISTINCT rel_type FROM edge')}
 if 'SECTION_IMPACTED_BY' not in rels:
  del qs['inverse_alias_projection']
 results={}
 for name,sql in qs.items():
  rows=[dict(x) for x in c.execute(sql)];results[name]={'sql':sql,'sql_sha256':sha(sql.encode()),'rows':rows,'row_count':len(rows)}
 if 'inverse_alias_projection' in results:assert results['original_projection']['rows']==results['inverse_alias_projection']['rows']
 save('actual_immutable_SQL_diagnostics.json',results)
 save('original_SQL_table_schemas.json',{t:[dict(x) for x in c.execute('PRAGMA table_info("'+t+'")')] for t in ['TechnicalReport','TRImpact','Spec','Section','CR','WorkItem','Release']})
 # Preserve complete incident roles for named study, all its impacts, all six RedCap WIs and every incident CR.
 core={x[0] for x in c.execute("SELECT node_id FROM TechnicalReport WHERE trNumber='38.875' UNION SELECT h.dst_id FROM rel_HAS_TR_IMPACT h JOIN TechnicalReport t ON t.node_id=h.src_id WHERE t.trNumber='38.875' UNION SELECT node_id FROM WorkItem WHERE lower(workItemCode) LIKE '%redcap%' UNION SELECT cr.node_id FROM CR cr JOIN rel_RELATED_TO r ON r.src_id=cr.node_id JOIN WorkItem w ON w.node_id=r.dst_id WHERE lower(w.workItemCode) LIKE '%redcap%'")}
 marks=','.join('?' for _ in core);args=tuple(sorted(core))*2
 edges=[dict(x) for x in c.execute('SELECT * FROM edge WHERE src_id IN ('+marks+') OR dst_id IN ('+marks+') ORDER BY edge_id',args)]
 nodes=core|{e[k] for e in edges for k in ['src_id','dst_id']}
 records=[dict(x) for n in sorted(nodes) for x in c.execute('SELECT * FROM _node_record WHERE node_id=?',(n,))]
 save('complete_own_TR_impacts_RedCap_workitems_and_CR_incident_slice.json',{'core_node_ids':sorted(core),'records':records,'edges':edges,'scope':'All incident edges and endpoint records for named study, all its TRImpacts, every RedCap-named WI and every CR incident through RELATED_TO. Candidate naming is not treated as study-to-actual-amendment attribution.'})
 patterns={'named_TR':r'38[. ]875','named_study_item':r'FS_NR_redcap(?!_enh)|RP[- ]?201677','RedCap_semantic':r'red[ -]?cap|reduced capabilit'}
 hits={k:[] for k in patterns};nn=sn=0
 for row in c.execute('SELECT node_id,labels_json,properties_json FROM _node_record ORDER BY node_id'):
  nn+=1;values=list(strings(json.loads(row['properties_json'])));sn+=len(values)
  for value in values:
   for k,pat in patterns.items():
    if re.search(pat,value,re.I):hits[k].append({'node_id':row['node_id'],'labels':json.loads(row['labels_json']),'value':value})
 save('whole_decoded_frozen_TR_and_RedCap_literal_frontier.json',{'all_node_records_scanned':nn,'decoded_string_scalars_scanned':sn,'patterns':patterns,'hits':hits,'scope':'Complete retained string-property literal/semantic recovery frontier. Matches are candidates and never causal proof by themselves.'})
 c.close();after=pin(DB);assert before==after
 receipt={'status':'COMPLETED_ORIGINAL_SOURCE_AND_IMMUTABLE_SQL_REOPEN','id':q['id'],'original_question_sha256':sha(q['question_en'].encode()),'SQL_roles':{k:v['row_count'] for k,v in results.items()},'original_source_reopened':pin(p),'SQLite_before':before,'SQLite_after':after,'core_n':len(core),'slice_records':len(records),'slice_edges':len(edges),'full_literal_frontier':{k:len(v) for k,v in hits.items()},'API_calls':0,'native_calls':0,'public_mutations':0,'queue_mutations':0}
 save('actual_reopen_receipt.json',receipt);print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
