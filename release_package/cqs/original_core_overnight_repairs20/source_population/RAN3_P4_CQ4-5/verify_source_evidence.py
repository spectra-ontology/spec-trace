"""Standard-library source replay. Included projections != omitted original corpus."""
from pathlib import Path
import argparse, base64, collections, gzip, hashlib, importlib.util, io, json, re, sys, xml.etree.ElementTree as ET, zipfile
sys.dont_write_bytecode = True
HERE=Path(__file__).resolve().parent
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}';S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}';M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
sp=importlib.util.spec_from_file_location('pinned_symbol_fonts',HERE/'symbol_fonts.py');symbol_fonts=importlib.util.module_from_spec(sp);sp.loader.exec_module(symbol_fonts)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(name):return json.loads((HERE/name).read_text())
def jl(name):
 b=(HERE/name).read_bytes();return [json.loads(x)for x in (gzip.decompress(b)if name.endswith('.gz')else b).decode().splitlines()]
def text(e,reader=None,paragraphs=False):
 if e.tag in {W+x for x in ['del','moveFrom','delText','drawing','pict','object']}:return ''
 if e.tag==W+'r':reader=symbol_fonts.run_reader(e)
 if e.tag==W+'t':return reader(e.text or '')if reader else e.text or ''
 if e.tag==W+'sym':return symbol_fonts.sym_text(e)
 if e.tag in {W+'br',W+'cr'}:return '\n'
 if e.tag in {W+'tab',W+'ptab'}:return '\t'
 if e.tag==W+'noBreakHyphen':return '-'
 value=''.join(text(c,reader,paragraphs)for c in e);return value+'\n'if paragraphs and e.tag==W+'p'else value

def doc(raw):
 with zipfile.ZipFile(io.BytesIO(raw))as z:xml=z.read('word/document.xml')
 root=ET.fromstring(xml);return root,xml,[text(p)for p in root.findall('.//'+W+'p')]
def xlsx_rows(raw):
 with zipfile.ZipFile(io.BytesIO(raw))as z:
  ss=[''.join(x.itertext())for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(S+'si')]if'xl/sharedStrings.xml'in z.namelist()else[]
  rows=[]
  for row in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//'+S+'sheetData/'+S+'row'):
   vals={}
   for c in row.findall(S+'c'):
    col=re.match('[A-Z]+',c.attrib['r']).group();v=c.find(S+'v');value=v.text if v is not None and v.text is not None else ''
    if c.get('t')=='s':value=ss[int(value)]
    elif c.get('t')=='inlineStr':value=''.join(c.find(S+'is').itertext())
    vals[col]=value
   rows.append((int(row.attrib['r']),vals))
  header=rows[0][1];return [(n,{header[k]:v for k,v in r.items()if k in header})for n,r in rows[1:]]
def summary_from_row(raw,label_index):
 row=ET.fromstring(raw);cells=row.findall(W+'tc')[label_index+1:]
 def visible(e):
  if e.tag in {W+'del',W+'moveFrom',W+'delText'}:return
  yield e
  for c in e:yield from visible(c)
 tags=collections.Counter(x.tag for c in cells for x in visible(c))
 assert not {k:v for k,v in tags.items()if k.startswith(M)or k in {W+n for n in ['drawing','pict','object','instrText','altChunk','footnoteReference','endnoteReference','tbl']}},'Unsupported visible Summary construct'
 return '\n'.join(text(c,paragraphs=True).strip()for c in cells).strip()
def get_field(root,f):
 row=root.findall('.//'+W+'tbl')[f['table_zero_based']].findall(W+'tr')[f['row_zero_based']]
 raw=ET.tostring(row,encoding='utf-8');return raw,summary_from_row(raw,f['label_cell_zero_based'])
def digest(d):
 keys=['id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved']
 return sha(json.dumps({k:d[k]for k in keys},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=Path);args=ap.parse_args();manifest=load('manifest.json')
 for f in manifest['files']:
  p=HERE/f['path'];b=p.read_bytes();assert len(b)==f['bytes']and sha(b)==f['sha256'],f['path']
 scope=load('scope_and_provenance.json');definition=load('definition.json');assert digest(definition)==scope['repair_sha256'];assert definition['collection']=={'kind':'multiset'}and definition['cardinality_policy']=={'mode':'exact','value':10}
 original=load('original_benchmark_row.json');assert definition['question_en']==original['question_en']and definition['original_query']==original['cypher']
 root,xml,ps=doc((HERE/'originals/approved_123_report.docx').read_bytes());assert sha(xml)=='bd457dacf9fae0495181cd82c36114f0c1a13e75914129cceb4caac642a1156b'
 regs={r['TDoc']:(n,r)for n,r in xlsx_rows((HERE/'originals/approved_123_register.xlsx').read_bytes())if r.get('TDoc')};headers={};last=None
 for i,t in enumerate(ps):
  m=re.match(r'^\s*(R3-\d{6,7})(?:\s|$)',t)
  if m:last=(m.group(1),i,t)
  m=re.search(r'^\s*Type:\s*(.*?)\s+For:',t)
  if m:assert last is not None and last[0]not in headers;headers[last[0]]={'Type':m.group(1).strip(),'paragraph':last[1],'type_paragraph':i}
 assert len(regs)==len(headers)==1213 and set(regs)==set(headers)
 for k,(n,r)in regs.items():assert headers[k]['Type']==r['Type'],k
 witnesses=jl('all1213_source_and_frozen_predicate_witness.jsonl.gz');assert len(witnesses)==1213 and {x['tdocNumber']for x in witnesses}==set(regs)
 for row in witnesses:
  k=row['tdocNumber'];r=regs[k][1];fs=row['frozen_records'];assert len(fs)==1;f=fs[0]
  assert f['canonicalMeetingNumber']=='RAN3#123'and f['tdocNumber']==k
  assert r['Type']==f['type']and r['TDoc Status']==f['status']and(r.get('For','')or None)==(f['for']or None)
  assert (r['Type']in['CR','draftCR','pCR'])==bool(f['has_CR_label'])
 family={k for k,(_,r)in regs.items()if r['Type']in['CR','draftCR','pCR']};accepted={k for k,(_,r)in regs.items()if r['Type']=='CR'and r['TDoc Status']=='agreed'};assert len(family)==914 and len(accepted)==202
 ledger=jl('all914_report_decision_source_projection.jsonl.gz');assert len(ledger)==914 and {r['tdocNumber']for r in ledger}==family
 for row in ledger:
  k=row['tdocNumber'];assert row['register']['Type']==regs[k][1]['Type']and row['register']['TDoc Status']==regs[k][1]['TDoc Status']
  for block in row['exact_final_visible_report_records']:
   h=block['heading'];assert ps[h['all_document_paragraph_zero_based']]==h['text']and re.match(r'^\s*'+re.escape(k)+r'(?:\s|$)',h['text'])
   for d in block['decisions']:assert ps[d['all_document_paragraph_zero_based']]==d['text']
  if k in accepted:assert any('The document was agreed.'in d['text']for d in row['exact_agreed_decisions'])
 # Separate next-meeting own report ratification from a CR-version floor event.
 nextroot,nextxml,nps=doc((HERE/'originals/ratifying_123bis_report.docx').read_bytes());matches=[]
 for i,t in enumerate(nps):
  if re.match(r'^\s*R3-241502(?:\s|$)',t):matches.append(nps[i:i+4])
 assert len(matches)==1 and any('The document was approved.'in t for t in matches[0])
 nextreg=[r for n,r in xlsx_rows((HERE/'originals/ratifying_123bis_register.xlsx').read_bytes())if r.get('TDoc')=='R3-241502'];assert len(nextreg)==1 and nextreg[0]['Type']=='report'and nextreg[0]['TDoc Status']=='approved'
 assert 'BEFORE the end of the meeting'in ps[105]and ps[5598]=='Set an email discussion for the following:'and ps[5600]=='Finalize and agree final CRs'
 fixtures=jl('all202_own_summary_source_cells.jsonl.gz');assert len(fixtures)==202 and {r['tdocNumber']for r in fixtures}==accepted
 own={};full_source_n=0;included_selected_n=0;conversions=0
 for row in fixtures:
  k=row['tdocNumber'];assert row['prior_own_cover_full_identity_matches'];values=[]
  for w in row['sources']:
   raw=base64.b64decode(w['summary_row_XML_base64']);assert sha(raw)==w['field']['et_serialized_row_sha256'];v=summary_from_row(raw,w['field']['label_cell_zero_based']);assert v==row['source_authored_summary'];values.append(v)
   member=None
   if w.get('included_original_member'):
    member=(HERE/w['included_original_member']).read_bytes();assert sha(member)==w['member_sha256'];included_selected_n+=1
   if args.source_root:
    a=args.source_root/w['original_repository_path'];araw=a.read_bytes();assert sha(araw)==w['archive_sha256']
    with zipfile.ZipFile(io.BytesIO(araw))as z:actual=z.read(w['member'])
    assert sha(actual)==w['member_sha256'];member=actual;full_source_n+=1
   if member is not None:
    if w['access_path']=='strict_original_native_DOCX_XML':decoded=member
    else:
     decoded=(HERE/w['retained_conversion_file']).read_bytes();assert sha(decoded)==w['retained_conversion_sha256'];conversions+=1
    rr,xx,_=doc(decoded);assert sha(xx)==w['document_XML_sha256'];rrraw,rrvalue=get_field(rr,w['field']);assert sha(rrraw)==w['field']['et_serialized_row_sha256']and rrvalue==v
  assert len(set(values))==1;own[k]=values[0]
 proof=load('source_selection_proof.json');selected=sorted(accepted)[:10];assert proof['source_candidate_IDs']==sorted(accepted)and proof['source_selected_IDs']==selected
 expected=[{'summary':own[k]}for k in selected];stored=jl('source_selected_records.jsonl');assert stored==expected and len(stored)==10
 # Full202 failures stay visible; no nonnull filter is used to construct selected10.
 frozen_bad=[r for r in fixtures if r['frozen_summary']!=r['source_authored_summary']];assert len(frozen_bad)==6 and sum(r['frozen_summary']is None for r in fixtures)==3
 assert all(next(r for r in fixtures if r['tdocNumber']==k)['frozen_summary']==own[k]for k in selected)
 if args.source_root:
  for x in scope['original_source_archives'].values():
   p=args.source_root/x['original_repository_path'];raw=p.read_bytes();assert sha(raw)==x['sha256']
   if x.get('included_members'):
    with zipfile.ZipFile(io.BytesIO(raw))as z:
     for m in x['included_members']:assert z.read(m['member'])==(HERE/m['file']).read_bytes()
  assert full_source_n==202
 # These exact phrases predate repair; output values do not establish semantics.
 p1=(HERE/'original_phase1_design.md').read_text();p4=(HERE/'original_phase4_design.md').read_text();assert '회의에서의 결정 결과'in p1 and 'CQ4-5'in p4
 print(json.dumps({'status':'PASS','mode':'actual_original202_and_archive_members'if args.source_root else'included_originals_and_retained_projection','id':definition['id'],'all_register_records':1213,'all_family_own_records':914,'agreed_own_CR_records':202,'source_summary_cells_recounted':202,'selected_full_original_members_replayed':included_selected_n,'all202_full_original_members_replayed':full_source_n,'selected_records':len(stored),'full202_frozen_failures_preserved':6,'expert_validation_n':0,'native_API_public_mutation':0},ensure_ascii=False))
if __name__=='__main__':main()
