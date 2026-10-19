"""Offline source proof replay; no model, native connection or operational writes."""
from pathlib import Path
from collections import Counter
from xml.etree import ElementTree as ET
import argparse, hashlib, importlib.util, io, json, re, sqlite3, sys, zipfile
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
X='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rawsha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def rows(p):return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]
def module(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def checked(p,rec):
 assert Path(p).stat().st_size==rec['bytes'] and sha(p)==rec['sha256'],str(p)
def visible(e):
 if e.tag in (W+'del',W+'moveFrom'):return ''
 if e.tag==W+'t':return e.text or ''
 if e.tag==W+'tab':return '\t'
 if e.tag in (W+'br',W+'cr'):return '\n'
 return ''.join(visible(c) for c in e)
def cell(e):return '\n'.join(visible(p) for p in e.findall(W+'p')).strip()
def fold(t):return ' '.join(t.split())
def quoted(s):return '"'+s.replace('"','""')+'"'

def replay(package):
 p=Path(package)
 assert not p.is_symlink() and not any(f.is_symlink() for f in p.rglob('*')),'Portable tree must not contain symlinks'
 inventory_path=p/'immutable_inventory.json'
 assert sha(inventory_path)=='0deb93ce209429ab2c1a4366d5b441390c3f36ead95c3ce6527ab5a91c668069','Immutable inventory identity mismatch'
 inventory=load(inventory_path)
 metadata={'README.md','manifest.json','verify_exact_DESC_source.py','immutable_inventory.json'}
 assert set(inventory['metadata_exclusions'])==metadata
 frozen={r['path']:r for r in inventory['files']}
 assert len(frozen)==len(inventory['files']) and not set(frozen)&metadata
 all_files={str(f.relative_to(p)) for f in p.rglob('*') if f.is_file()}
 assert all_files==set(frozen)|metadata,'Immutable complete file set mismatch'
 for rel,rec in frozen.items():checked(p/rel,rec)
 m=load(p/'manifest.json')
 assert m['immutable_inventory_sha256']==sha(inventory_path)
 actual={str(f.relative_to(p)) for f in p.rglob('*') if f.is_file()}
 assert actual=={'manifest.json'}|{r['path'] for r in m['files']},'Unexpected or missing portable file'
 for rec in m['files']:checked(p/rec['path'],rec)
 old=p/'inherited_source_snapshot'
 assert sha(old/'manifest.json')=='80ee20cf1e335f6231ee35850a81c3ec684d49dc3130de73db321c344f3e9565'
 common=module(old/'source_snapshot_common.py','portable_inherited_source')
 inherited=common.verify_package(old,old/'pipeline/load_released_kg.py')
 definition=load(p/'contract/definition.json');en=(old/'query/original_English.txt').read_text()
 original=(old/'query/original_query.cypher').read_text();q=(p/'query/separate_source_exact_DESC_query.cypher').read_text()
 assert en==definition['question_en'] and original==definition['original_query']
 assert rawsha(en.encode())==definition['original_question_sha256']==m['original_question_sha256']
 assert rawsha(original.encode())==definition['original_query_sha256']==m['original_query_sha256']
 assert q==definition['reference_query'] and rawsha(q.encode())==definition['reference_query_sha256']
 assert 'ORDER BY d.tdocNumber DESC LIMIT 10' in q and 'AND s.sourceSummary IS NOT NULL' in q
 assert definition['required_fields']==[
  {'name':'tdocNumber','type':'string','nullable':False,'source_column_or_expression':'d.tdocNumber'},
  {'name':'summary','type':'string','nullable':False,'source_column_or_expression':'s.sourceSummary'}]
 assert definition['collection']=={'kind':'set'} and definition['cardinality_policy']=={'mode':'exact','value':10}
 repair=rawsha(canonical({k:v for k,v in definition.items() if k!='repair_sha256'}).encode())
 assert repair==definition['repair_sha256']==m['repair_sha256']
 primary=load(p/'contract/primary_seven_unit_review.json');secondary=load(p/'contract/independent_secondary_seven_unit_review.json')
 schema=module(p/'contract/review_schema.py','portable_review_schema')
 criteria_path=p/'contract/criteria.json'
 assert sha(criteria_path)=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'==definition['criteria_sha256']==m['official_criteria_sha256']
 units=load(criteria_path)['semantic_units'];assert len(units)==len(set(units))==7
 for review in (primary,secondary):
  schema.check_pass(review,en,units,criteria_sha=definition['criteria_sha256'],identity_key='repair_sha256',identity_sha=repair)
  assert review['definition_file_sha256']==sha(p/'contract/definition.json')
  assert review['expert_validation_n']==0 and review['human_author_review_completed'] is False
 roles=load(p/'contract/review_role_disclosure.json')
 assert roles['primary_author']!=roles['secondary_author'] and roles['primary_same_agent_as_definition']
 assert roles['secondary_distinct_agent_nonblind'] and roles['expert_validation_n']==0
 assert roles['primary_historical_filename_does_not_mean_independent']
 register=common.rows(old/'source/all3112_register.jsonl');observations=common.rows(old/'source/all1858_observations.jsonl')
 reg={r['tdocNumber']:r for r in register};obs={r['tdocNumber']:r for r in observations}
 assert len(reg)==3112 and len(obs)==1858
 family={'CR','draftCR','pCR'};accepted={'agreed','approved','endorsed'}
 eligible=[td for td,r in reg.items() if r['properties']['Type'] in family and r['properties']['TDoc Status'] in accepted]
 positive=[td for td in eligible if obs[td]['source_summary'] is not None]
 assert len(eligible)==1027 and len(positive)==808
 pool=[[td,obs[td]['source_summary']] for td in sorted(positive,reverse=True)];expected=pool[:10]
 assert len({r[0] for r in expected})==10 and all(reg[td]['properties']['TDoc Status']=='agreed' for td,_ in expected)
 variants=[eligible,[td for td in eligible if reg[td]['properties']['TDoc Status']=='agreed'],
  [td for td in eligible if reg[td]['properties']['Type']=='CR' and reg[td]['properties']['TDoc Status']=='agreed']]
 assert all(sorted(v,reverse=True)[:10]==[r[0] for r in expected] for v in variants)
 mapping=load(old/'patch/additive_node_edge_mapping.json')
 db=sqlite3.connect(':memory:');common.create_new_tables(db,mapping);common.insert_new_records(db,mapping,False)
 sql=(p/'query/separate_source_exact_DESC_query.sql').read_text()
 assert sql.endswith('ORDER BY d.tdocNumber DESC LIMIT 10')
 actual=[list(r) for r in db.execute(sql)]
 assert actual==expected
 assert [list(r) for r in db.execute(sql.rsplit(' LIMIT 10',1)[0])]==pool
 # Meaningful canonical query controls: each changes the returned record membership or value.
 controls={}
 controls['ASC_changes_prefix']=[list(r) for r in db.execute(sql.replace('tdocNumber DESC','tdocNumber ASC'))]!=expected
 controls['LIMIT9_is_incomplete']=len(db.execute(sql.replace('LIMIT 10','LIMIT 9')).fetchall())==9
 first=expected[0][0]
 db.execute('UPDATE SourceOwnCRSummary SET sourceSummary=NULL WHERE tdocNumber=?',(first,))
 missing=[list(r) for r in db.execute(sql)]
 controls['nonnull_before_limit_refills_from_next_source_record']=len(missing)==10 and missing!=expected and first not in {r[0] for r in missing}
 db.rollback()
 # The table was populated inside an implicit transaction; rebuild after rollback.
 db.close();db=sqlite3.connect(':memory:');common.create_new_tables(db,mapping);common.insert_new_records(db,mapping,False);db.commit()
 db.execute('UPDATE SourceMeetingDocument SET finalDocumentaryStatus=? WHERE tdocNumber=?',('noted',first))
 changed=[list(r) for r in db.execute(sql)]
 controls['noted_is_excluded_without_deleting_source_record']=len(changed)==10 and changed!=expected and first not in {r[0] for r in changed}
 assert all(controls.values())
 capture=load(p/'native_evidence/actual_native_two_field_DESC_capture.json')
 reference=load(p/'native_evidence/actual_immutable_SQL_two_field_DESC_reference.json')
 nr=load(p/'native_evidence/actual_native_exact_DESC_receipt.json')
 assert sha(p/'native_evidence/actual_native_two_field_DESC_capture.json')==nr['capture_sha256']
 assert sha(p/'native_evidence/actual_immutable_SQL_two_field_DESC_reference.json')==nr['SQL_reference_sha256']
 assert sha(p/'native_evidence/requested_two_field_records.jsonl')==nr['reference_jsonl_sha256']
 assert nr['whole_eligible_rows']==808 and nr['selected_rows']==10 and nr['owned_container_stopped']
 assert nr['query_sha256']==rawsha(q.encode()) and nr['definition_sha256']==sha(p/'contract/definition.json')
 for name,wanted in [('selected',expected),('whole_eligible_pool',pool)]:
  c=capture[name]
  assert c['columns']==['tdocNumber','summary'] and c['rows']==reference['rows'][name]==wanted
  assert c['complete'] and not c['truncated'] and c['transaction_rolled_back'] and not c['contains_updates']
  assert c['EXPLAIN_query_type']==c['actual_query_type']=='r'
 assert capture['selected']['literal_query']==q
 assert reference['queries']['selected']==sql
 assert rows(p/'native_evidence/requested_two_field_records.jsonl')==[dict(zip(['tdocNumber','summary'],r)) for r in expected]
 own=load(p/'source_evidence/selected10_own_summary_XML_and_binary_limits.json')
 assert len(own)==10 and [r['tdocNumber'] for r in own]==[r[0] for r in expected]
 for field,(td,summary) in zip(own,expected):
  row=field['independently_found_own_summary_row']
  assert row['summary']==summary and row['cells'][0]=='Summary of change:'
  xml=ET.fromstring(row['row_xml']);cells=[cell(tc) for tc in xml.findall(W+'tc')]
  assert '\n'.join(cells[1:]).strip()==summary and cells[0]=='Summary of change:'
  assert field['own_summary_and_styles_positive_strike_hidden']==[]
  if field['access']!='original_DOCX':
   b=field['original_binary_corroboration'];assert b['visible_field_result_folded_summary_present'] and not b['original_CFB_strike_decoded']
 scope=load(p/'scope_and_limits.json');assert scope['original560_pass_increment']==0 and scope['exact_nonnull_inner_join_pool']==808
 assert scope['type_and_status_candidates_before_own_summary_join']==1027
 external=load(p/'whole_graph_evidence/external_large_artifact_pins.json')
 assert nr['source_sha256']==external['source_RDF']['sha256'] and nr['db_sha256']==external['source_SQLite']['sha256']
 assert (external['nodes'],external['directed_edges'],external['FTS_chunks'])==(346617,1600412,537311)
 return {'status':'PASS_PORTABLE_EXACT_DESC_SOURCE_CONTRACT_AND_SAVED_NATIVE_REPLAY',
 'whole_source_register':3112,'CR_family_observations':1858,'type_status_candidates':1027,'nonnull_pool':808,
 'selected_pairs':10,'required_fields':['tdocNumber','summary'],'meaningful_query_controls':controls,
 'inherited_ASC_result_is_separate_historical_contract':True,'new_native_executions':0,'API_calls':0,
 'original560_pass_increment':0,'expert_validation_n':0,'whole1343_source_certified':False}

def source_reopen(p,source_root):
 source_root=Path(source_root);old=p/'inherited_source_snapshot'
 report=load(p/'source_evidence/actual_primary_toolpath_source_reopen_receipt.json')
 archive=source_root/report['report_archive']['path'];checked(archive,report['report_archive'])
 with zipfile.ZipFile(archive) as z:wb=z.read(report['workbook_member'])
 assert rawsha(wb)==report['workbook_member_sha256']
 with zipfile.ZipFile(io.BytesIO(wb)) as z:
  shared=[''.join(t.text or '' for t in si.iter(X+'t')) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(X+'si')]
  tree=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
 header=None;reg={}
 for row in tree.iter(X+'row'):
  values={}
  for c in row.findall(X+'c'):
   col=re.match('[A-Z]+',c.attrib['r']).group();v=c.find(X+'v');typ=c.get('t')
   values[col]=shared[int(v.text)] if typ=='s' and v is not None else ''.join(t.text or '' for t in c.iter(X+'t')) if typ=='inlineStr' else (v.text or '') if v is not None else ''
  if header is None:header=values;assert 'TDoc' in header.values();continue
  props={name:values.get(col,'') for col,name in header.items() if name}
  if not props.get('TDoc'):continue
  assert props['TDoc'] not in reg
  reg[props['TDoc']]={'properties':props,'excel_row':int(row.get('r')),'ET_UTF8_row_sha256':rawsha(ET.tostring(row,encoding='utf-8'))}
 retained={r['tdocNumber']:r for r in rows(old/'source/all3112_register.jsonl')}
 assert len(reg)==3112 and set(reg)==set(retained)
 for td,r in reg.items():assert all(r[k]==retained[td][k] for k in r),td
 fields=load(p/'source_evidence/selected10_own_summary_XML_and_binary_limits.json');binary=module(p/'recipes/original_binary_doc_fields.py','portable_binary_fields')
 ncfb=0
 for f in fields:
  arc=source_root/f['archive']['path'];checked(arc,f['archive'])
  with zipfile.ZipFile(arc) as z:member=z.read(f['member_name'])
  assert rawsha(member)==f['member_sha256']
  summary=f['independently_found_own_summary_row']['summary']
  if f['access']=='original_DOCX':docx=member
  else:
   ncfb+=1;der=source_root/f['existing_derivative']['path'];checked(der,f['existing_derivative']);docx=der.read_bytes()
   stories,props=binary._doc_read(member,props=True);main=stories[0]
   assert fold(summary) in fold(binary._visible(main))
   live=props[0][1].replace('\ufdd0','') if props and props[0] is not None else None
   assert (live is not None)==f['original_binary_corroboration']['live_deletion_story_available']
   if live is not None:assert fold(summary) in fold(binary._visible(live))
  with zipfile.ZipFile(io.BytesIO(docx)) as z:xml=z.read('word/document.xml');styles=z.read('word/styles.xml')
  assert rawsha(xml)==f['document_xml_sha256'] and rawsha(styles)==f['styles_xml_sha256']
  root=ET.fromstring(xml);candidates=[]
  for table in root.iter(W+'tbl'):
   for row in table.findall(W+'tr'):
    values=[cell(tc) for tc in row.findall(W+'tc')]
    if values and re.fullmatch(r'\s*Summary\s+of\s+change\s*:\s*',values[0],re.I):candidates.append('\n'.join(values[1:]).strip())
  assert candidates==[summary]
 return {'status':'PASS_FRESH_ORIGINAL_ARCHIVE_MEMBERS_REGISTER_AND_SELECTED10_OWN_FIELDS','register':3112,'selected':10,'CFB':ncfb,'original_CFB_strike_decoded':False}

def full_base(p,base_sql,base_rdf,source_sql,source_rdf):
 external=load(p/'whole_graph_evidence/external_large_artifact_pins.json')
 for path,key in [(base_sql,'baseline_SQLite'),(base_rdf,'baseline_RDF'),(source_sql,'source_SQLite'),(source_rdf,'source_RDF')]:checked(path,external[key])
 with Path(base_rdf).open('rb') as old,Path(source_rdf).open('rb') as new:
  for b in iter(lambda:old.read(1048576),b''):assert new.read(len(b))==b
  assert new.read()==(p/'inherited_source_snapshot/patch/additive_source_records.ttl').read_bytes()
 db=sqlite3.connect(Path(source_sql).resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
 db.execute('PRAGMA query_only=ON');db.execute('PRAGMA temp_store=MEMORY');db.execute('PRAGMA cache_size=-32768')
 db.execute('ATTACH DATABASE ? AS frozen',(Path(base_sql).resolve().as_uri()+'?mode=ro&immutable=1',))
 names=[r[0] for r in db.execute("SELECT name FROM frozen.sqlite_master WHERE type='table' ORDER BY name")];assert len(names)==80
 for table in names:
  q=quoted(table);old_schema=db.execute('SELECT sql FROM frozen.sqlite_master WHERE name=?',(table,)).fetchone()
  assert old_schema==db.execute('SELECT sql FROM main.sqlite_master WHERE name=?',(table,)).fetchone()
  cols=[r[1] for r in db.execute('PRAGMA frozen.table_info('+q+')')];field=','.join(quoted(c) for c in cols)
  tail=' WHERE node_id<=342161' if 'node_id' in cols else ' WHERE edge_id<=1592845' if 'edge_id' in cols else ''
  old='SELECT '+field+' FROM frozen.'+q;new='SELECT '+field+' FROM main.'+q+tail
  assert db.execute('SELECT count(*) FROM ('+old+' EXCEPT '+new+')').fetchone()[0]==0,table
  assert db.execute('SELECT count(*) FROM ('+new+' EXCEPT '+old+')').fetchone()[0]==0,table
  assert db.execute('SELECT count(*) FROM frozen.'+q).fetchone()==db.execute('SELECT count(*) FROM main.'+q+tail).fetchone()
 assert db.execute('SELECT count(*) FROM node').fetchone()[0]==346617
 assert db.execute('SELECT count(*) FROM edge').fetchone()[0]==1600412
 sql=(p/'query/separate_source_exact_DESC_query.sql').read_text()
 capture=load(p/'native_evidence/actual_native_two_field_DESC_capture.json')
 assert [list(r) for r in db.execute(sql)]==capture['selected']['rows']
 assert [list(r) for r in db.execute(sql.rsplit(' LIMIT 10',1)[0])]==capture['whole_eligible_pool']['rows']
 db.close()
 return {'status':'PASS_ACTUAL_FULL_BASE_EXACT_PREFIX_ALL80_OLD_TABLES_AND_FULL808_SQL','old_tables':80,'source_nodes':346617,'source_edges':1600412,'new_native_API_calls':0,'writes':0}

def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--source-root',type=Path)
 a.add_argument('--baseline-sql',type=Path);a.add_argument('--baseline-rdf',type=Path)
 a.add_argument('--source-sql',type=Path);a.add_argument('--source-rdf',type=Path);args=a.parse_args()
 result=replay(ROOT)
 if args.source_root:result['actual_original_source_reopen']=source_reopen(ROOT,args.source_root)
 paths=[args.baseline_sql,args.baseline_rdf,args.source_sql,args.source_rdf]
 if any(paths):assert all(paths),'All four full-base paths required';result['full_base']=full_base(ROOT,*paths)
 print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
