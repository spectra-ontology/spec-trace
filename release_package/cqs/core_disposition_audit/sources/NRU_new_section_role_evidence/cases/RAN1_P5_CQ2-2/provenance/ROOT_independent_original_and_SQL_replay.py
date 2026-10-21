"""Independent ROOT read-only checks; classification evidence, not an answer oracle."""
import hashlib,json,sqlite3,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
L=Path(__file__).resolve().parent
D=L/'actual_source_and_frozen'
R=next(p for p in L.parents if (p/'CLAUDE.md').is_file())
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def text(e):
 if e.tag in (W+'del',W+'moveFrom'):return ''
 return (e.text or '') if e.tag==W+'t' else ''.join(text(x) for x in e)
q=json.loads((D/'original_question_and_query.json').read_text())
assert sha(q['original_record']['question_en'].encode())=='82d9d530485d742e54e34a6382e553b05169f8e2927f50fa18ce22a4054643db'
assert sha(Path(q['criteria']['path']).read_bytes())=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
receipt=json.loads((D/'actual_source_and_frozen_reopen_receipt.json').read_text())
db=R/receipt['sqlite_before']['path'];before=pin(db)
assert before['sha256']==receipt['sqlite_before']['sha256']
src=json.loads((D/'direct_original_source_and_format.json').read_text())
source_checks=[]
for s in src:
 p=Path(s['archive']['path']);assert pin(p)==s['archive']
 with zipfile.ZipFile(p) as z:
  xml=z.read('word/document.xml');styles=z.read('word/styles.xml')
 assert sha(xml)==s['document_xml']['sha256'] and sha(styles)==s['styles_xml']['sha256']
 body=ET.fromstring(xml).find(W+'body');paras=body.findall(W+'p')
 selected=[]
 for field in ['scope','conclusions','own_reference_to_TS38213_section13','top_level_headings','section16_start']:
  for item in s.get(field,[]):
   assert text(paras[item['index']])==item['text'];selected.append([field,item['index'],sha(item['text'].encode())])
 for item in s.get('all_heading_or_explicit_new_section_paragraphs',[]):
  e=body[item['body_child']];assert text(e)==item['text']
  assert len(list(e.iter(W+'ins')))==item['insertions']
  selected.append(['current_heading',item['body_child'],sha(item['text'].encode())])
 if 'cover_rows' in s:
  tbl=body[s['cover_table_body_child']]
  rows=[[text(tc) for tc in tr.findall(W+'tc')] for tr in tbl.findall(W+'tr')]
  assert rows==[a['cells'] for a in s['cover_rows']]
 if s['key']=='CR1913631':
  import re
  new=re.findall(r'(\d+(?:\.\d+)*)\(new\)',rows[17][1]);assert len(new)==6
  assert [a['body_child'] for a in s['all_heading_or_explicit_new_section_paragraphs']]==[385,391,482,507,533,542]
 if s['key']=='TS38213':assert text(paras[4362])=='16UE procedures for sidelink'
 source_checks.append({'key':s['key'],'original_archive':s['archive'],'XML_and_styles':'PASS','selected_original_spans':selected})
sqls=json.loads((D/'actual_immutable_SQL_diagnostics.json').read_text())
c=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
sql_checks=[]
for k,v in sqls.items():
 assert sha(v['sql'].encode())==v['sql_sha256']
 rows=[dict(r) for r in c.execute(v['sql'])]
 assert rows==v['rows'] and len(rows)==v['row_count']
 sql_checks.append({'role':k,'row_count':len(rows),'all_fields_all_rows_equal':True})
assert sqls['all_own_impacts']['row_count']==4
assert sum(r['section_node'] is not None for r in sqls['all_own_impacts']['rows'])==1
node=dict(c.execute("SELECT * FROM CR WHERE tdocNumber='R1-1913631'").fetchone())
assert node['clausesAffected'] is None
edges=[dict(r) for r in c.execute("SELECT s.sectionId,s.sectionNumber FROM rel_MODIFIES_SECTION m JOIN Section s ON s.node_id=m.dst_id WHERE m.src_id=? ORDER BY s.sectionId",(node['node_id'],))]
assert len(edges)==11 and not (set(new)&{r['sectionNumber'] for r in edges})
for num in new:
 assert c.execute("SELECT count(*) FROM Section WHERE sectionNumber=? AND sectionId LIKE '38.212-Rel-16-%'",(num,)).fetchone()[0]>0
c.close();assert pin(db)==before
out={'status':'PASS_INDEPENDENT_ROOT_ORIGINAL_SOURCE_AND_IMMUTABLE_SQL_CLASSIFICATION_CHECKS','id':q['id'],'original_question_sha256':q['question_sha256'],'criteria_sha256':q['criteria']['sha256'],'source_checks':source_checks,'SQL_checks':sql_checks,'CR1913631':{'node_id':node['node_id'],'clausesAffected':node['clausesAffected'],'source_explicit_new_sections':new,'all_11_frozen_section_links':edges,'source_new_sections_present_as_frozen_entities':True,'new_section_role_not_in_CR_incidence':True},'DB_before_after':before,'complete_oracle_created':False,'native_API_public_mutations':0}
o=L/'actual_ROOT_independent_original_and_SQL_replay.json'
assert not o.exists();o.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':out['status'],'receipt':pin(o),'source_archives':len(source_checks),'SQL_roles':len(sql_checks)},ensure_ascii=False))
