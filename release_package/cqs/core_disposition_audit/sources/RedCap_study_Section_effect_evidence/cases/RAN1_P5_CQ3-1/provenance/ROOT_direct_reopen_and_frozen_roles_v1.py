"""ROOT independent direct original-source reopening and frozen role checks."""
import gzip,hashlib,json,re,sqlite3,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
D=Path(__file__).resolve().parent
R=next(p for p in D.parents if (p/'CLAUDE.md').is_file())
P=D/'portable_primary_source_roles_v1'
DB=R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN1.sqlite'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
N={'w':W[1:-1]}
def sha(b):return hashlib.sha256(b).hexdigest()
def rd(n):
 p=P/n
 return json.loads(p.read_bytes() if p.exists() else gzip.decompress((P/(n+'.gz')).read_bytes()))
def active(x):
 if x.tag in {W+'del',W+'moveFrom'}:return ''
 return (x.text or '') if x.tag==W+'t' else ''.join(active(v) for v in x)
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,list):
  for v in x:yield from strings(v)
 elif isinstance(x,dict):
  for v in x.values():yield from strings(v)
meta=rd('source/source_XML_metadata.json')
caps=json.loads((D/'readable_actual_original_source_capsule.json').read_text())
checks=[]
for m in meta:
 p=Path(m['archive']['path']);data=p.read_bytes()
 assert len(data)==m['archive']['bytes'] and sha(data)==m['archive']['sha256']
 with zipfile.ZipFile(p) as z:
  xml=z.read('word/document.xml');sty=z.read('word/styles.xml')
 for b,k in [(xml,'document_xml'),(sty,'styles_xml')]:
  assert len(b)==m[k]['bytes'] and sha(b)==m[k]['sha256']
  assert b==gzip.decompress((P/m['retained_source_directory']/(('document.xml' if k=='document_xml' else 'styles.xml')+'.gz')).read_bytes())
 ET.fromstring(sty)
 body=ET.fromstring(xml).find('w:body',N)
 blocks=[{'body_child':i,'tag':x.tag.removeprefix(W),'text':active(x),'table_rows':[[active(tc) for tc in row.findall('w:tc',N)] for row in x.findall('w:tr',N)]} for i,x in enumerate(body)]
 selected=next((x['selected_original_blocks'] for x in caps['source_amendment_and_TS_capsules'] if x['key']==m['key']),[])
 if m['key']=='TR38875':
  for s in caps['all_12_actual_TR_specification_impact_analysis_sections']:
   assert blocks[s['heading']['body_child']]==s['heading']
   for b in s['blocks']:assert blocks[b['body_child']]==b
  selected=[s['heading'] for s in caps['all_12_actual_TR_specification_impact_analysis_sections']]
 for b in selected:assert blocks[b['body_child']]==b
 checks.append({'key':m['key'],'archive_sha256':sha(data),'document_xml_sha256':sha(xml),'styles_xml_sha256':sha(sty),'actual_body_children':len(blocks),'selected_exact_body_children':len(selected)})
before=sha(DB.read_bytes());assert before=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
c=sqlite3.connect(DB.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
groups=[rd('frozen/actual_immutable_SQL_diagnostics.json'),rd('frozen/actual_additional_SQL_diagnostics.json'),{'direct_study_workitem_typed_CR_query':rd('frozen/all_RedCap_candidate_frozen_CR_role_summary.json')['direct_study_workitem_typed_CR_query']}]
roles=[]
for group in groups:
 for name,x in group.items():
  assert sha(x['sql'].encode())==x['sql_sha256']
  rows=[dict(r) for r in c.execute(x['sql'])]
  assert rows==x['rows'] and len(rows)==x['row_count'],name
  roles.append({'role':name,'actual_rows':len(rows),'sql_sha256':x['sql_sha256'],'complete_rows_sha256':sha(json.dumps(rows,ensure_ascii=False,sort_keys=True).encode())})
sem=set();nn=sn=0
for r in c.execute('SELECT node_id,labels_json,properties_json FROM _node_record ORDER BY node_id'):
 nn+=1;values=list(strings(json.loads(r['properties_json'])));sn+=len(values)
 if 'CR' in json.loads(r['labels_json']) and any(re.search(r'red[ -]?cap|reduced capabilit',v,re.I) for v in values):sem.add(r['node_id'])
expected=set(groups[1]['all_semantic_CR_candidates']['candidate_node_ids_from_original_full_property_scan'])
assert sem==expected and len(sem)==146
c.close();after=sha(DB.read_bytes());assert before==after
out=D/'actual_ROOT_direct_11_sources_and_frozen_9_roles_v1.json';assert not out.exists()
value={'status':'PASS_ROOT_INDEPENDENT_DIRECT_ORIGINAL_SOURCE_AND_FROZEN_ROLE_REPLAY','reviewer':'ROOT AI agent','id':'RAN1_P5_CQ3-1','source_XML_style_pair_n':len(checks),'actual_direct_original_source_reopens':checks,'actual_immutable_SQL_roles':roles,'SQL_role_n':len(roles),'whole_original_node_records_scanned':nn,'whole_decoded_string_scalars_scanned':sn,'semantic_CR_candidates':len(sem),'semantic_candidate_membership_equal':True,'frozen_DB_before_sha256':before,'frozen_DB_after_sha256':after,'API_calls':0,'native_calls':0,'public_writes':0}
out.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':value['status'],'source_pairs':len(checks),'SQL_roles':len(roles),'semantic_CR_candidates':len(sem),'receipt_sha256':sha(out.read_bytes())}))

