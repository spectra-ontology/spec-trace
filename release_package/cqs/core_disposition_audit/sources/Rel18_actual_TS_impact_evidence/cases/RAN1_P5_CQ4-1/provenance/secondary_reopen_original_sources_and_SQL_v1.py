"""Independent secondary actual raw archive, immutable SQL and complete incident replay."""
import datetime,gzip,hashlib,json,sqlite3,sys,zipfile
import xml.etree.ElementTree as E
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;A=D/'actual_original_sources_and_complete_frozen_v1'
R=next(p for p in D.parents if (p/'CLAUDE.md').is_file());B=next(p for p in D.parents if p.name=='overnight_reaudit')
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}';N={'w':W[1:-1]}
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):
 b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def pin(p):
 b=p.read_bytes();return {'path':str(p.relative_to(R)),'bytes':len(b),'sha256':sha(b)}
def save(p,x):
 assert not p.exists();b=(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode();p.write_bytes(gzip.compress(b,mtime=0) if p.suffix=='.gz' else b)
def active(x):
 if x.tag in {W+'del',W+'moveFrom'}:return ''
 return ((x.text or '') if x.tag==W+'t' else '')+''.join(active(y) for y in x)
source_rows=[];source_texts=[]
for m in load(A/'source_originals_metadata_and_locators.json'):
 archive=Path(m['archive']['path']);b=archive.read_bytes();assert len(b)==m['archive']['bytes'] and sha(b)==m['archive']['sha256']
 with zipfile.ZipFile(archive) as z:
  xml=z.read('word/document.xml');styles=z.read('word/styles.xml')
 for raw,key,name in [(xml,'document_xml','document.xml.gz'),(styles,'styles_xml','styles.xml.gz')]:
  assert {'bytes':len(raw),'sha256':sha(raw)}=={k:m[key][k] for k in ['bytes','sha256']}
  assert gzip.decompress((A/m['source_dir']/name).read_bytes())==raw
 body=E.fromstring(xml).find('w:body',N);sty=E.fromstring(styles);paras=body.findall('w:p',N);texts=[active(x) for x in paras]
 groups=[]
 for group in m.get('source_scope_conclusions',[]):
  rows=[]
  for row in group['direct_body_paragraphs']:
   assert texts[row['index']]==row['text'];rows.append({'direct_paragraph':row['index'],'text':texts[row['index']]})
  groups.append({'heading':group['heading'],'paragraphs':rows})
 cover=[{'body_child':i,'text':active(x)} for i,x in enumerate(body) if i<9]
 inserted=[{'body_child':i,'text':active(x)} for i,x in enumerate(body) if x.tag==W+'p' and x.find('w:pPr/w:rPr/w:ins',N) is not None]
 source_rows.append({'key':m['key'],'archive':pin(archive),'document_xml':{'bytes':len(xml),'sha256':sha(xml)},'styles_xml':{'bytes':len(styles),'sha256':sha(styles)},'scope_conclusion_paragraphs_verified':sum(len(g['paragraphs']) for g in groups),'cover_contains_release18':any('Release 18' in x['text'] for x in cover),'paragraph_count':len(paras)})
 source_texts.append({'key':m['key'],'cover_current_blocks':cover,'scope_conclusion_sections':groups,'paragraph_mark_inserted_rows':inserted})
assert len(source_rows)==7 and all(x['cover_contains_release18'] for x in source_rows if x['key'].startswith('TR'))
db=B.parent/'relational/RAN1.sqlite';before=pin(db);assert before['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
c=sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
queries=load(D/'actual_ROOT_Rel18_complete_roles_SQL_v2.json.gz');roles=[]
for name,role in queries.items():
 assert sha(role['sql'].encode())==role['sql_sha256'];rows=[dict(x) for x in c.execute(role['sql'])];assert rows==role['rows'] and len(rows)==role['row_count']
 roles.append({'name':name,'sql_sha256':role['sql_sha256'],'row_count':len(rows),'all_rows_and_fields_equal':True})
five=load(A/'actual_all_five_direct_CR_incidence.json.gz');assert sha(five['sql'].encode())==five['sql_sha256'];rows=[dict(x) for x in c.execute(five['sql'])];assert rows==five['rows'] and len(rows)==53
roles.append({'name':'all_five_direct_CR_incidence','sql_sha256':five['sql_sha256'],'row_count':len(rows),'all_rows_and_fields_equal':True})
crids={r['node_id'] for key in ['complete_six_naming_CR_spec_section_projection','complete_six_direct_study_CR','SBFD_original_CR_source_witness'] for r in queries[key]['rows']}
core={x[0] for x in c.execute('SELECT node_id FROM TechnicalReport UNION SELECT node_id FROM TRImpact')}|crids|{r['node_id'] for r in queries['complete_six_naming_candidates']['rows']}
core|={x[0] for x in c.execute("SELECT w.node_id FROM WorkItem w JOIN rel_RELATED_TO_WORK_ITEM k ON k.dst_id=w.node_id JOIN TechnicalReport tr ON tr.node_id=k.src_id JOIN rel_TARGET_RELEASE rr ON rr.src_id=tr.node_id JOIN Release r ON r.node_id=rr.dst_id WHERE r.releaseName='Rel-18'")}
marks=','.join('?' for _ in core);args=tuple(sorted(core))*2
edges=[dict(x) for x in c.execute('SELECT * FROM edge WHERE src_id IN ('+marks+') OR dst_id IN ('+marks+') ORDER BY edge_id',args)]
ident={x[0] for x in c.execute('SELECT node_id FROM WorkItem')};nodes=core|ident|{e[k] for e in edges for k in ['src_id','dst_id']}
records=[dict(x) for n in sorted(nodes) for x in c.execute('SELECT * FROM _node_record WHERE node_id=?',(n,))]
snapshot=load(A/'complete_own_source_records_and_edges.json.gz')
assert sorted(core)==snapshot['complete_incident_core_node_ids'] and sorted(ident-core)==snapshot['identity_only_WorkItems']
assert edges==snapshot['edges'] and records==snapshot['records'];assert (len(core),len(records),len(edges),len(ident),len(crids))==(367,9634,12428,423,294)
c.close();assert pin(db)==before
textpath=D/'secondary_actual_original_cover_scope_conclusion_text_v1.json.gz';save(textpath,source_texts)
receipt={'status':'PASS_SECONDARY_ACTUAL_SEVEN_RAW_ARCHIVES_NINE_SQL_AND_COMPLETE_INCIDENT_REPLAY','id':'RAN1_P5_CQ4-1','actor':'/root/d52_finish_prefix','review_role':'Distinct nonblind AI secondary actual source and SQL reopen; not human or expert endorsement','source_pairs':source_rows,'SQL_roles':roles,'frozen_before_after':before,'frozen_database_unchanged':True,'complete_core_nodes':len(core),'frozen_records':len(records),'frozen_edges':len(edges),'all_workitem_identities':len(ident),'recovered_distinct_CR':len(crids),'complete_incident_all_rows_equal':True,'source_texts':pin(textpath),'API_calls':0,'native_calls':0,'public_writes':0,'queue_writes':0,'not_a_complete_answer_oracle':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
save(D/'secondary_actual_original_source_and_SQL_review_v1.json',receipt);print(json.dumps({'status':receipt['status'],'source_pairs':7,'SQL_roles':len(roles),'core':len(core),'records':len(records),'edges':len(edges)}))
