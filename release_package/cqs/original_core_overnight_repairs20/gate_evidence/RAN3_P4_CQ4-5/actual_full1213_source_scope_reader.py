from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import zipfile,io,json,hashlib,sqlite3,re,xml.etree.ElementTree as E
B=Path('logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit').resolve();T=B/'root_evidence/two_agent_unresolved_loop/root_RAN3_123_approved_record_exact_gate_v2';S=Path('data/corpus/tsg/RAN/formal/meetings/RAN3/source/TSGR3_123-bis/Docs/R3-241502.zip').resolve()
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}';X='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
def tx(e):
 if e.tag in {W+'del',W+'moveFrom',W+'delText',W+'object',W+'drawing'}:return ''
 if e.tag==W+'t':return e.text or ''
 if e.tag in {W+'br',W+'cr'}:return '\n'
 if e.tag in {W+'tab',W+'ptab'}:return '\t'
 return ''.join(tx(c) for c in e)
z=zipfile.ZipFile(S);member='R3-241502_RAN3#123_TDoc_List_Meeting_v20240314.xlsx';raw=z.read(member);assert sha(raw)=='6376400bc7c352954aae7435a9fb396972b1b4627df51d6c95ba96ab7b0da478';a=zipfile.ZipFile(io.BytesIO(raw));ss=[]
if 'xl/sharedStrings.xml' in a.namelist():ss=[''.join(e.itertext()) for e in E.fromstring(a.read('xl/sharedStrings.xml')).findall(X+'si')]
rows=[]
for row in E.fromstring(a.read('xl/worksheets/sheet1.xml')).findall(X+'sheetData/'+X+'row'):
 out={}
 for c in row:
  v=c.find(X+'v');t=c.find(X+'is');val=v.text if v is not None else ''.join(t.itertext()) if t is not None else '';out[re.sub(r'\d','',c.attrib['r'])]=ss[int(val)] if c.get('t')=='s' else val
 rows.append(out)
header=rows[0];assert list(header.values())[0]=='TDoc';rdata=[]
for row in rows[1:]:
 d={header[k]:v for k,v in row.items() if k in header}
 if d.get('TDoc'):rdata.append(d)
reg={r['TDoc']:r for r in rdata};assert len(reg)==len(rdata)==1213
report_member='R3-241502_RAN3#123_MeetingReport_v2024-03-14.docx';doc=z.read(report_member);xml=zipfile.ZipFile(io.BytesIO(doc)).read('word/document.xml');assert sha(xml)=='bd457dacf9fae0495181cd82c36114f0c1a13e75914129cceb4caac642a1156b';ps=[tx(e) for e in E.fromstring(xml).find(W+'body').findall(W+'p')]
starts=[]
for n,p in enumerate(ps[:-1]):
 m=re.match(r'^(R3-\d{6})\s+',p)
 if m and 'Type:' in ps[n+1] and 'For:' in ps[n+1]:starts.append((n,m[1]))
assert len(starts)==len(set(t for n,t in starts))==1213
own={}
for k,(n,tid) in enumerate(starts):
 end=starts[k+1][0] if k+1<len(starts) else len(ps)
 match=re.search(r'Type:\s*(.*?)\s+For:',ps[n+1],re.S);assert match
 typ=match[1].strip();decs=[(j,ps[j]) for j in range(n+2,end) if re.match(r'^\s*Decision\s*:',ps[j])]
 assert len(decs)>=1,tid
 primary=decs[0];positive=bool(re.search(r'\bthe document was agreed\b',primary[1],re.I));own[tid]={'type':typ,'agreed':positive,'p':n,'decision_p':primary[0],'decision':primary[1]}
assert set(own)==set(reg)
db=B.parent/'relational/RAN3.sqlite';bp=pin(db);c=sqlite3.connect('file:'+str(db)+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
qr="SELECT DISTINCT t.node_id,t.tdocNumber,t.type,t.status,EXISTS(SELECT 1 FROM CR cr WHERE cr.node_id=t.node_id) AS has_CR_label FROM Meeting m JOIN rel_PRESENTED_AT a ON a.dst_id=m.node_id JOIN Tdoc t ON t.node_id=a.src_id WHERE m.canonicalMeetingNumber='RAN3#123'";fr=[dict(r) for r in c.execute(qr)];c.close();f={r['tdocNumber']:r for r in fr};assert len(f)==len(fr)==1213 and set(f)==set(reg)
for tid,r in reg.items():
 assert own[tid]['type']==r['Type']==f[tid]['type'],tid
 assert r['TDoc Status']==f[tid]['status'],tid
 assert bool(f[tid]['has_CR_label'])==(r['Type'] in {'CR','draftCR','pCR'}),tid
src={tid for tid,r in own.items() if r['type']=='CR' and r['agreed']};froz={tid for tid,r in f.items() if r['type']=='CR' and r['status']=='agreed'};assert len(src)==202 and src==froz
assert bp==pin(db)
result={'checked_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_ROOT_ORIGINAL_REGISTER_FULL1213_AND_OWN_DECISION_POPULATION','original_archive':pin(S),'register_member':member,'register_sha256':sha(raw),'report_member':report_member,'report_XML_sha256':sha(xml),'all1213_ID_type_status_CRlabel_equal':True,'own_header_n':len(own),'own_formal_CR_agreed_n':len(src),'own_positive202_equals_frozen_predicate':True,'draftCR_status_counts':dict(Counter(r['status'] for r in fr if r['type']=='draftCR')),'all_CR_family_n':sum(r['type'] in {'CR','draftCR','pCR'} for r in fr),'source_population_IDs':sorted(src),'frozen_DB':bp,'frozen_DB_unchanged':True,'SQL':qr,'scope':'Original named-meeting register plus each own first Decision paragraph. This is not every physical CR mentioning this meeting or proof of before-closure approval of the exact revision. Separate202 own-cover/summary binding remains required. Unrelated participant XLSX is not read or included.','new_API_calls':0,'new_native_calls':0,'expert_validation_n':0}
p=T/'actual_root_full1213_register_and_own_decision_population.json';assert not p.exists();p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':result['status'],'receipt':pin(p),'draftCR_status_counts':result['draftCR_status_counts']}))
