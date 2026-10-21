"""Capture original Rel18 study population, original sources and complete candidate roles."""
import csv,gzip,hashlib,json,re,sqlite3,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
D=Path(__file__).resolve().parent
R=next(p for p in D.parents if (p/'CLAUDE.md').is_file())
P=R.parent/'spectra-public/spec-trace'
B=next(p for p in D.parents if p.name=='overnight_reaudit')
A=Path("/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/root_evidence/two_agent_unresolved_loop/adjudication62/resumed_deep_verification/sequential_two_main/local_only41/main_A/RAN1_P5_CQ2-3")/'actual_source_and_frozen'
O=D/'actual_original_sources_and_complete_frozen_v1'
assert not O.exists();O.mkdir()
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}';N={'w':W[1:-1]}
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def save(n,x):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);b=(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
 p.write_bytes(gzip.compress(b,mtime=0) if n.endswith('.gz') else b);return pin(p)
def active(x):
 if x.tag in {W+'del',W+'moveFrom'}:return ''
 return (x.text or '') if x.tag==W+'t' else ''.join(active(y) for y in x)
raw=next(b for b in (P/'release_package/cqs/original_core_repair/provenance/original_benchmark.jsonl').read_bytes().splitlines(keepends=True) if json.loads(b)['id']=='RAN1_P5_CQ4-1')
q=json.loads(raw);assert sha(q['question_en'].encode())=='9b6364d79aad4a4af0b626e2d43753133030a3d937f6629406354ab96d67b130'
(O/'original_benchmark_record.jsonl').write_bytes(raw)
author=R/'logs/tsg/RAN/formal/RAN1/phase-5/cq_test_dataset.json';aq=json.loads(author.read_bytes());kr=next(x for x in aq['questions'] if x['id']=='CQ4-1')
assert kr['cypher']==q['cypher'];(O/'original_author_CQ_dataset.json').write_bytes(author.read_bytes())
save('original_question_and_query.json',{'original_record':q,'original_Korean_record':kr,'question_sha256':sha(q['question_en'].encode()),'query_sha256':sha(q['cypher'].encode()),'natural_requested_roles':'All retained Rel18-targeting study identities and actual type(s) of their effects on TSs. Study-release selector does not constrain the later normative effect release; original title/status are diagnostic context.'})
meta=json.loads((A/'direct_original_source_and_format.json').read_text());loc=json.loads((A/'actual_original_style_and_scope_role_reopen.json').read_text())
keys={'TR38858','TR38859','TR38864','TR38865','TR38867','TR38869'}
sources=[];capsules=[]
for m in meta:
 if m['key'] not in keys:continue
 archive=Path(m['archive']['path']);assert pin(archive)==m['archive']
 with zipfile.ZipFile(archive) as z:xml=z.read('word/document.xml');sty=z.read('word/styles.xml')
 for b,k in [(xml,'document_xml'),(sty,'styles_xml')]:assert len(b)==m[k]['bytes'] and sha(b)==m[k]['sha256']
 ET.fromstring(sty);body=ET.fromstring(xml).find('w:body',N);paras=body.findall('w:p',N);texts=[active(x) for x in paras]
 locator=next(x for x in loc if x['key']==m['key']);sections=locator['numeric_scope_and_conclusion_blocks']
 for s in sections:
  for v in s['direct_body_paragraphs']:assert texts[v['index']]==v['text']
 for name,b in [('document.xml.gz',xml),('styles.xml.gz',sty)]:
  t=O/'source'/m['key']/name;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(gzip.compress(b,mtime=0))
 source={'key':m['key'],'archive':m['archive'],'document_xml':m['document_xml'],'styles_xml':m['styles_xml'],'source_dir':'source/'+m['key'],'direct_paragraph_n':len(paras),'original_cover':[{'paragraph':i,'text':t} for i,t in enumerate(texts[:80]) if t],'source_scope_conclusions':sections}
 sources.append(source);capsules.append({'key':m['key'],'cover_release_lines':[x for x in source['original_cover'] if re.search(r'18\.\d|Release\s*18',x['text'])],'scope':sections[0],'conclusion_relevant_original_paragraphs':[v for s in sections[1:] for v in s['direct_body_paragraphs'] if re.search(r'normative|specification|work item|WI phase|further|Rel-19|recommended',v['text'],re.I)]})
m=json.loads((A/'actual_source_CR2504980_and_named_role_receipt.json').read_text());archive=Path(m['archive']['path']);assert pin(archive)==m['archive']
with zipfile.ZipFile(archive) as z:xml=z.read('word/document.xml');sty=z.read('word/styles.xml')
for b,k in [(xml,'document_xml'),(sty,'styles_xml')]:assert len(b)==m[k]['bytes'] and sha(b)==m[k]['sha256']
ET.fromstring(sty);body=ET.fromstring(xml).find('w:body',N)
for name,b in [('document.xml.gz',xml),('styles.xml.gz',sty)]:
 t=O/'source/CR2504980'/name;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(gzip.compress(b,mtime=0))
cover=[{'body_child':i,'text':active(x)} for i,x in enumerate(body) if i<9]
sources.append({'key':'CR2504980','archive':m['archive'],'document_xml':m['document_xml'],'styles_xml':m['styles_xml'],'source_dir':'source/CR2504980','cover_current_original_blocks':cover})
save('source_originals_metadata_and_locators.json',sources);save('readable_own_Rel18_source_capsule.json',capsules)
db=B.parent/'relational/RAN1.sqlite';before=pin(db);assert before['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
c=sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
diag=json.loads(gzip.decompress((D/'actual_ROOT_Rel18_complete_roles_SQL_v2.json.gz').read_bytes()))
crids={r['node_id'] for k in ['complete_six_naming_CR_spec_section_projection','complete_six_direct_study_CR','SBFD_original_CR_source_witness'] for r in diag[k]['rows']}
core={x[0] for x in c.execute('SELECT node_id FROM TechnicalReport UNION SELECT node_id FROM TRImpact')}|crids|{r['node_id'] for r in diag['complete_six_naming_candidates']['rows']}
core|={x[0] for x in c.execute("SELECT w.node_id FROM WorkItem w JOIN rel_RELATED_TO_WORK_ITEM k ON k.dst_id=w.node_id JOIN TechnicalReport tr ON tr.node_id=k.src_id JOIN rel_TARGET_RELEASE rr ON rr.src_id=tr.node_id JOIN Release r ON r.node_id=rr.dst_id WHERE r.releaseName='Rel-18'")}
marks=','.join('?' for _ in core);args=tuple(sorted(core))*2
edges=[dict(x) for x in c.execute('SELECT * FROM edge WHERE src_id IN ('+marks+') OR dst_id IN ('+marks+') ORDER BY edge_id',args)]
ident={x[0] for x in c.execute('SELECT node_id FROM WorkItem')}
nodes=core|ident|{e[k] for e in edges for k in ['src_id','dst_id']}
records=[dict(x) for n in sorted(nodes) for x in c.execute('SELECT * FROM _node_record WHERE node_id=?',(n,))]
save('complete_own_source_records_and_edges.json.gz',{'complete_incident_core_node_ids':sorted(core),'identity_only_WorkItems':sorted(ident-core),'records':records,'edges':edges,'scope':'All26 original TRs, every retained TRImpact, six Rel18 study WIs, twelve exact-name implementation candidates and every corresponding typed CR preserve their whole incident relations. All423 WorkItem identities retained. Candidate correspondence is discovery evidence rather than causal attribution.'})
save('original_SQL_table_schemas.json',{t:[dict(x) for x in c.execute('PRAGMA table_info("'+t+'")')] for t in ['TechnicalReport','TRImpact','Release','WorkItem','CR','Spec','Section']})
save('actual_original_eight_SQL_roles.json.gz',diag)
five=sorted({r['node_id'] for r in diag['complete_six_direct_study_CR']['rows']});sql='SELECT cr.id,e.rel_type,n.labels,p.properties_json FROM CR cr JOIN edge e ON e.src_id=cr.node_id OR e.dst_id=cr.node_id JOIN node n ON n.node_id=CASE WHEN e.src_id=cr.node_id THEN e.dst_id ELSE e.src_id END JOIN _node_record p ON p.node_id=n.node_id WHERE cr.node_id IN ('+','.join(map(str,five))+') ORDER BY cr.id,e.rel_type,e.src_id,e.dst_id'
rows=[dict(x) for x in c.execute(sql)];save('actual_all_five_direct_CR_incidence.json.gz',{'sql':sql,'sql_sha256':sha(sql.encode()),'rows':rows,'row_count':len(rows)})
save('actual_frozen_capture_summary.json',{'source_record_n':len(records),'complete_core_n':len(core),'edge_n':len(edges),'direct_study_CR_n':len(five),'direct_study_CR_incident_rows':len(rows),'named_implementation_CR_n':len(crids),'all_SQL_roles':{k:v['row_count'] for k,v in diag.items()}})
for name in ['tr_impact_mapping.csv','tr_workitem_mapping.csv']:
 f=R/'ontology/input/tsg/RAN/formal/TR/RAN1'/name;(O/('original_'+name)).write_bytes(f.read_bytes())
c.close();after=pin(db);assert before==after
save('actual_ROOT_capture_receipt.json',{'status':'ACTUAL_SEVEN_ORIGINAL_SOURCE_PAIRS_AND_COMPLETE_FROZEN_ROLE_CAPTURE','source_pairs':len(sources),'source_keys':[x['key'] for x in sources],'original_question_sha256':sha(q['question_en'].encode()),'frozen_before':before,'frozen_after':after,'complete_core_n':len(core),'source_record_n':len(records),'incident_edge_n':len(edges),'API_calls':0,'native_calls':0,'public_writes':0,'queue_mutations':0,'not_a_complete_answer_or_final_classification':True})
print(json.dumps({'source_pairs':len(sources),'core':len(core),'records':len(records),'edges':len(edges),'capsule':str(O/'readable_own_Rel18_source_capsule.json')}))

