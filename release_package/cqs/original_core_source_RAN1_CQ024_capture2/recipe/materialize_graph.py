#!/usr/bin/env python3
"""Create an isolated whole frozen graph plus source-derived generic capture links.

No query, spec number, resolution/answer whitelist or gold is used to derive the
patch. Existing nodes, properties, storage schemas and every old row remain.
The separate evaluation reference is replayed only after graph construction.
"""
from pathlib import Path
from collections import Counter
from xml.etree import ElementTree as ET
import hashlib,importlib.util,json,shutil,sqlite3,sys,zipfile
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if(p/'CLAUDE.md').exists())
O=HERE.parent.parent;OUR=O/'RAN1_RAN3_RAN4';G=OUR/'loop140_generic_three_report_reference_capture_rule_NOT_ADMITTED';SEM=OUR/'loop139_CQ024_two_reference_edges_calendar_repair_semantic_proposal_NOT_ADMITTED'
BASE_TTL=ROOT/'release_package/kg/per_wg/RAN1-body.ttl'
BASE_SQL=ROOT/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN1.sqlite'
TTL_SHA='9540683df5407bb3f8978ad4d05ddc7f7880f10c94f21273f588d737f145e231'
SQL_SHA='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
DELTA_MANIFEST_SHA='f0fe4f4465bfd2d79d4eb8d93bc8dde95a334834549c4dca7a0f8411e131b239'
LEXER=ROOT.parent/'spectra-public/spec-trace/release_package/pipeline/load_released_kg.py'
BUILDER=HERE/'build_generic_graph_corpus.py'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}';M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def pin(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def load(p):return json.loads(Path(p).read_text())
def rows(p):return [json.loads(l)for l in p.read_text().splitlines()if l.strip()]
def save(n,x):
 p=HERE/n;assert not p.exists(),p;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def module(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def ro(p):
 c=sqlite3.connect(p.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.execute('PRAGMA query_only=ON');c.execute('PRAGMA cache_size=-32768');c.execute('PRAGMA temp_store=MEMORY');return c
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def quote(s):return '"'+s.replace('"','""')+'"'
assert sha(BASE_TTL)==TTL_SHA and sha(BASE_SQL)==SQL_SHA and sha(G/'generic_source_delta_manifest.json')==DELTA_MANIFEST_SHA
manifest=load(G/'generic_source_delta_manifest.json')
for r in manifest['files']:
 p=G/r['path'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],p
rule=module(G/'replay_generic_capture_reference_rule.py','fixed_generic_capture_rule');assert all(x['pass']for x in rule.controls())
db=ro(BASE_SQL);db.row_factory=sqlite3.Row
ledger=rows(G/'all869_scope_ledger.jsonl');captured=rows(G/'all_capture_candidates_full_source_and_formatting.jsonl');assert len(ledger)==869
source_receipt=load(G/'actual_generic_capture_delta_receipt.json');bodies={}
for s in source_receipt['sources']:
 p=Path(s['DOCX']['path']);assert sha(p)==s['DOCX']['sha256']
 with zipfile.ZipFile(p)as z:xml=z.read('word/document.xml');styles=z.read('word/styles.xml')
 assert hashlib.sha256(xml).hexdigest()==s['document_xml_sha256'] and hashlib.sha256(styles).hexdigest()==s['styles_xml_sha256']
 bodies[s['report']]=list(ET.fromstring(xml).find(W+'body'))
replayed=[]
for item in ledger:
 rid=item['resolutionId'];a=db.execute('SELECT node_id FROM Agreement WHERE resolutionId=?',(rid,)).fetchall();assert len(a)==1 and a[0][0]==item['src_id']
 lo,hi=item['raw_body_child_range'];elements=bodies[rid.split('-')[1]][lo:hi]
 blocks=[{'kind':e.tag.rsplit('}',1)[-1],'text':''.join(n.text or ''for n in e.iter()if n.tag in(W+'t',M+'t'))}for e in elements]
 raw='\n'.join(b['text']for b in blocks);assert hashlib.sha256(raw.encode()).hexdigest()==item['raw_window_sha256']
 findings=rule.candidate_blocks(blocks);assert len(findings)==item['capture_candidate_count']
 for f in findings:
  same=[c for c in captured if c['resolutionId']==rid and c['intro_raw_body_child']==lo+f['intro_offset']];assert len(same)==1
  c=same[0];assert all(c[k]==f[k]for k in ['intro_offset','capture_offsets','tdoc_ids','status','prior_unclaimed_header_offsets'])
  assert c['full_source_window_text']==raw and c['source_raw_range']==[lo,hi]
  for b in c['capture_blocks']:
   assert hashlib.sha256(ET.tostring(elements[b['raw_body_child']-lo])).hexdigest()==b['XML_sha256']
  replayed.append(c)
assert len(replayed)==21
accepted=[c for c in replayed if c['status']=='accepted_explicit_capture_prefix'];assert len(accepted)==20 and all(c['all_capture_markers_active']for c in accepted)
# All accepted source links participate; no target-spec/answer filter exists here.
derived={};all_links=[]
for c in accepted:
 src=c['src_id']
 for link in c['matched_existing_Tdoc_nodes']:
  dst=link['dst_id'];matches=db.execute('SELECT node_id FROM Tdoc WHERE tdocNumber=?',(link['tdocNumber'],)).fetchall();assert dst in [r[0]for r in matches]
  old=db.execute("SELECT edge_id FROM edge WHERE src_id=? AND rel_type='REFERENCES' AND dst_id=?",(src,dst)).fetchall();assert bool(old)==link['already_exists']
  assert db.execute('SELECT count(*)FROM rel_REFERENCES WHERE src_id=? AND dst_id=?',(src,dst)).fetchone()[0]==len(old)
  all_links.append((src,dst))
  if not old:
   derived[src,dst]={'src_id':src,'dst_id':dst,'resolutionId':c['resolutionId'],'tdocNumber':link['tdocNumber'],'source_DOCX_sha256':c['source_DOCX_sha256'],'intro_raw_body_child':c['intro_raw_body_child']}
delta=[derived[k]for k in sorted(derived)];assert len(all_links)==38 and len(delta)==2
assert delta==rows(G/'generic_derived_additive_reference_edges.jsonl')
uri={r['node_id']:r['source_iri']for r in db.execute('SELECT node_id,source_iri FROM _node_record')};assert len(uri)==db.execute('SELECT count(*)FROM node').fetchone()[0]
patch='\n'+''.join('<'+uri[r['src_id']]+'> spectra:references <'+uri[r['dst_id']]+'> .\n'for r in delta)
(HERE/'source_derived_additive_references.ttl').write_text(patch)
new_ttl=HERE/'RAN1-capture2-body.ttl';assert not new_ttl.exists()
with BASE_TTL.open('rb')as old,new_ttl.open('xb')as new:shutil.copyfileobj(old,new);new.write(patch.encode())
new_sql=HERE/'RAN1-capture2.sqlite';assert not new_sql.exists();shutil.copy2(BASE_SQL,new_sql)
w=sqlite3.connect(new_sql);w.execute('PRAGMA foreign_keys=ON');w.execute('BEGIN IMMEDIATE');edge_max=db.execute('SELECT max(edge_id)FROM edge').fetchone()[0]
for i,r in enumerate(delta,1):
 eid=edge_max+i;w.execute('INSERT INTO edge(edge_id,src_id,rel_type,dst_id)VALUES(?,?,?,?)',(eid,r['src_id'],'REFERENCES',r['dst_id']));w.execute('INSERT INTO rel_REFERENCES(edge_id,src_id,dst_id)VALUES(?,?,?)',(eid,r['src_id'],r['dst_id']))
w.commit();assert w.execute('PRAGMA integrity_check').fetchone()[0]=='ok';w.close()
new=ro(new_sql);new.execute('ATTACH DATABASE ? AS frozen',(BASE_SQL.resolve().as_uri()+'?mode=ro&immutable=1',))
old_schema=db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type,name").fetchall();new_schema=new.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type,name").fetchall();assert [tuple(r)for r in old_schema]==[tuple(r)for r in new_schema]
names=[r[0]for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")];assert len(names)==89
preserved=[]
for name in names:
 table=quote(name);cols=[r[1]for r in db.execute('PRAGMA table_info('+table+')')]
 expr=','.join(quote(c)+',typeof('+quote(c)+')'for c in cols)
 suffix=' WHERE edge_id<='+str(edge_max) if name in('edge','rel_REFERENCES')else''
 before='SELECT '+expr+' FROM frozen.'+table;after='SELECT '+expr+' FROM main.'+table+suffix
 assert new.execute('SELECT count(*)FROM('+before+' EXCEPT '+after+')').fetchone()[0]==0,name
 assert new.execute('SELECT count(*)FROM('+after+' EXCEPT '+before+')').fetchone()[0]==0,name
 nold=db.execute('SELECT count(*)FROM '+table).fetchone()[0];nnew=new.execute('SELECT count(*)FROM '+table+suffix).fetchone()[0];assert nold==nnew
 preserved.append({'table':name,'old_rows':nold,'typed_original_rows_preserved':True})
new_edge_ids=[tuple(r)for r in new.execute('SELECT edge_id,src_id,rel_type,dst_id FROM edge WHERE edge_id>? ORDER BY edge_id',(edge_max,))];assert len(new_edge_ids)==2
for name in names:
 if name.startswith('rel_'):
  rel=name[4:];table=quote(name)
  assert new.execute('SELECT count(*)FROM '+table+' r LEFT JOIN edge e ON r.edge_id=e.edge_id WHERE e.edge_id IS NULL OR e.src_id!=r.src_id OR e.dst_id!=r.dst_id OR e.rel_type!=?',(rel,)).fetchone()[0]==0
  assert new.execute('SELECT count(*)FROM '+table).fetchone()[0]==new.execute('SELECT count(*)FROM edge WHERE rel_type=?',(rel,)).fetchone()[0]
with BASE_TTL.open('rb')as old,new_ttl.open('rb')as full:
 for b in iter(lambda:old.read(1048576),b''):assert full.read(len(b))==b
 assert full.read()==patch.encode()
assert sha(LEXER)=='9499ac120ea4fcf1c2707f6e3151e399530d9b4f43f5aec9d2d93040792d6e25'
# Reparse the entire resulting graph using the exact public lexer and generic
# repeated-subject merger. No answer/prefix enters this fact equivalence proof.
builder=module(BUILDER,'generic_allfact_builder');lexer=builder.load_lexer(LEXER);records,edges=builder.read_graph(new_ttl,lexer)
assert len(records)==len(uri)==165418
for r in db.execute('SELECT source_iri,labels_json,properties_json FROM _node_record'):
 parsed=records[r['source_iri']];assert parsed['labels']==sorted(json.loads(r['labels_json'])) and canon(parsed['properties'])==canon(json.loads(r['properties_json'])),r['source_iri']
expected_edges={(uri[r['src_id']],r['rel_type'],uri[r['dst_id']])for r in db.execute('SELECT src_id,rel_type,dst_id FROM edge')}
expected_edges|={(uri[r['src_id']],'REFERENCES',uri[r['dst_id']])for r in delta}
assert edges==expected_edges and len(edges)==848230
save('actual_all89_tables_and_full_graph_fact_equivalence.json',{'status':'PASS','all89_original_storage_schemas_and_typed_rows':preserved,'new_edges':new_edge_ids,'all_node_labels_properties_unchanged':len(records),'whole_directed_edges':len(edges),'global_and_all_typed_edges_consistent':True,'old_TTL_exact_byte_prefix':True,'base_SQL':pin(BASE_SQL),'base_TTL':pin(BASE_TTL),'source_SQL':pin(new_sql),'source_TTL':pin(new_ttl),'public_lexer':pin(LEXER),'generic_builder':pin(BUILDER),'no_native_API_calls':True})
# Evaluation-only reference/projections are deliberately downstream of allfact
# construction and are not graph/corpus builder inputs.
definition=load(SEM/'prospective_definition.json')
sql='''SELECT DISTINCT a.resolutionId,COALESCE(a.contentWithEquations,a.content) AS content,m.meetingNumber,m.meetingNumberInt
FROM Agreement a JOIN rel_REFERENCES r ON r.src_id=a.node_id JOIN CR c ON c.node_id=r.dst_id
JOIN rel_MODIFIES x ON x.src_id=c.node_id JOIN Spec s ON s.node_id=x.dst_id
JOIN rel_MADE_AT am ON am.src_id=a.node_id JOIN Meeting m ON m.node_id=am.dst_id
WHERE s.specNumber='38.213'
ORDER BY m.meetingNumberInt DESC,m.meetingNumber DESC,a.resolutionId LIMIT 10'''
result=[list(r)for r in new.execute(sql)];whole=[list(r)for r in new.execute(sql.rsplit(' LIMIT 10',1)[0])]
source_prefix=load(OUR/'loop137_CQ024_whole_latest_report_reference_scope_NOT_ADMITTED/prospective_two_edges_and_source_valid_prefix_NOT_ADMISSION.json')
save('actual_new_full_SQL_calendar_reference.json',{'status':'ACTUAL_FULL_SQL_REFERENCE_AFTER_GRAPH_CONSTRUCTION','definition':pin(SEM/'prospective_definition.json'),'primary_review':pin(SEM/'prospective_primary_exact_seven_unit_review.json'),'reference_query':definition['reference_query'],'SQL':sql,'columns':['resolutionId','content','meetingNumber','meetingNumberInt'],'rows':result,'complete_pool_rows':whole,'required_ID_records':[{'resolutionId':r[0]}for r in result],'earlier_source_prefix_packet':source_prefix,'original_query_bytes_unchanged_in_definition':True,'native_calls':0,'API_calls':0})
(HERE/'reference_query.cypher').write_text(definition['reference_query']);(HERE/'reference_query.sql').write_text(sql)
save('actual_materialization_manifest.json',{'status':'PASS_ISOLATED_FULL_FROZEN_PLUS_SOURCE_GENERIC2_ONLY','source_TTL':pin(new_ttl),'source_SQL':pin(new_sql),'base_TTL':pin(BASE_TTL),'base_SQL':pin(BASE_SQL),'source_delta_manifest':pin(G/'generic_source_delta_manifest.json'),'full_all869_XML_windows_replayed':len(ledger),'all21_capture_candidates_reproduced':len(replayed),'accepted38_links':len(all_links),'existing36_links_retained':len(all_links)-len(delta),'derived_new_edges':delta,'whole_nodes':len(records),'whole_directed_edges':len(edges),'original_old_tables':len(names),'allfact_proof':pin(HERE/'actual_all89_tables_and_full_graph_fact_equivalence.json'),'new_SQL_reference':pin(HERE/'actual_new_full_SQL_calendar_reference.json'),'reference_query':pin(HERE/'reference_query.cypher'),'no_common3176_used':True,'source_window_limit':'Additive final-CR capture ownership only; existing foreign spillover and all unrelated source records are retained. No full historical source-faithfulness certification.','expert_validation_n':0,'API_calls':0,'native_calls':0,'original560_pass_increment':0})
assert sha(BASE_SQL)==SQL_SHA and sha(BASE_TTL)==TTL_SHA
print(json.dumps({'status':'PASS','manifest':pin(HERE/'actual_materialization_manifest.json'),'nodes':len(records),'edges':len(edges),'selected_rows':len(result),'whole_reference_rows':len(whole)}))
