from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sqlite3,zipfile,io,xml.etree.ElementTree as E
B=Path('logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit').resolve();O=B/'root_evidence/two_agent_unresolved_loop';T=O/'root_RAN3_123_approved_record_exact_gate_v2'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def sha(x):return hashlib.sha256(x).hexdigest()
def pin(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
def text(e):
 if e.tag in {W+'del',W+'moveFrom',W+'delText',W+'object',W+'drawing'}:return ''
 if e.tag==W+'r':
  fonts=e.find(W+'rPr/'+W+'rFonts')
  if fonts is not None:
   assert 'symbol' not in ' '.join(fonts.attrib.values()).lower(),'Symbol font needs explicit decoder'
 if e.tag==W+'sym':raise AssertionError('Symbol node needs explicit decoder')
 if e.tag==W+'t':return e.text or ''
 if e.tag in {W+'br',W+'cr'}:return '\n'
 if e.tag in {W+'tab',W+'ptab'}:return '\t'
 if e.tag==W+'noBreakHyphen':return '-'
 s=''.join(text(c) for c in e)
 return s+'\n' if e.tag==W+'p' else s
p=B/'RAN3_RAN4/RAN3_123_sourceAuthoredSummary202_v2.jsonl';sources={r['tdocNumber']:r for r in [json.loads(l) for l in p.read_text().splitlines()]}
db=B.parent/'relational/RAN3.sqlite';before=pin(db);con=sqlite3.connect('file:'+str(db)+'?mode=ro&immutable=1',uri=True);con.row_factory=sqlite3.Row
q=(T/'RAN3_P4_CQ4-5.sql').read_text();rows=[dict(r) for r in con.execute(q)]
selection=[dict(r) for r in con.execute("SELECT DISTINCT c.node_id,c.tdocNumber,c.summaryOfChange AS summary,m.meetingNumberInt AS meetingNumberInt FROM Meeting m JOIN rel_PRESENTED_AT pa ON pa.dst_id=m.node_id JOIN CR c ON c.node_id=pa.src_id WHERE m.canonicalMeetingNumber='RAN3#123' AND c.type='CR' AND c.status='agreed' ORDER BY m.meetingNumberInt DESC,c.tdocNumber ASC LIMIT 10")];con.close();assert rows==[{'summary':r['summary']} for r in selection]
checks=[]
for r in selection:
 s=sources[r['tdocNumber']];ws=s['source_summary_evidence'];vals=[];evidence=[]
 for w in ws:
  a=Path(w['original_archive_path']);a=a if a.is_absolute() else Path.cwd()/a;ab=a.read_bytes();assert sha(ab)==w['original_archive_sha256'];raw=zipfile.ZipFile(io.BytesIO(ab)).read(w['original_member']);assert sha(raw)==w['original_member_sha256']
  if w['access_path']=='strict_local_converted_DOCX_XML':
   decoded=Path(w['decoded_output_path']);content=decoded.read_bytes();assert sha(content)==w['decoded_output_sha256'];xhash=w['decoded_document_xml_sha256']
  else:content=raw;xhash=w['original_native_document_xml_sha256']
  xml=zipfile.ZipFile(io.BytesIO(content)).read('word/document.xml');assert sha(xml)==xhash;root=E.fromstring(xml);f=w['field'];tbl=root.findall('.//'+W+'tbl')[f['table_zero_based']];row=tbl.findall(W+'tr')[f['row_zero_based']];assert sha(E.tostring(row,encoding='utf-8'))==f['et_serialized_row_sha256'];cells=row.findall(W+'tc')[f['label_cell_zero_based']+1:];value='\n'.join(text(c).strip() for c in cells).strip();vals.append(value);evidence.append({'archive':pin(a),'member':w['original_member'],'member_sha256':sha(raw),'XML_sha256':sha(xml),'converted_access':w['access_path']=='strict_local_converted_DOCX_XML','field_row_sha256':sha(E.tostring(row,encoding='utf-8'))})
 assert len(set(vals))==1 and vals[0]==r['summary']==s['sourceAuthoredSummary'];checks.append({'tdocNumber':r['tdocNumber'],'source_summary_sha256':sha(vals[0].encode()),'source_equals_frozen_SQL':True,'original_access':evidence})
assert before==pin(db) and len(rows)==10
out=T/'root_independent_SQL_selected_records.jsonl';assert not out.exists();out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
receipt={'checked_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_ROOT_INDEPENDENT_SQL_AND_TEN_ACTUAL_ORIGINAL_SUMMARY_FIELDS','repair_sha256':'403ffd325d157916c9ef13d4df6523bf30868b0ce4d5f1e1a3ca30cfb323eb63','root_semantic_review':pin(T/'root_exact_semantic_review.json'),'source_ledger':pin(p),'root_authored_SQL':pin(T/'RAN3_P4_CQ4-5.sql'),'frozen_DB':before,'DB_unchanged':True,'complete_requested_rows':10,'records':pin(out),'source_checks':checks,'independent_reader_scope':'Separate root final-visible ElementTree reader reopens archives/member/XML and exact summary cell. Native-original DOCX9 and retained original-DOC conversion1; no new conversion equivalence claimed. No Symbol-font/sym node tolerated silently. Full source202/914 and source coverage gate remain separate.','source_gate_or_native_or_API_pass_claim':False,'expert_validation_n':0}
(T/'actual_root_SQL_and_ten_original_summary_fields.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'rows':len(rows),'receipt':pin(T/'actual_root_SQL_and_ten_original_summary_fields.json')}))
