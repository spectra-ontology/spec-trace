"""Offline finite source-fragment replay. No source-root fallback or DB/API.

This preflight validates included source fragments only. It is deliberately not
an admission gate or a substitute for full-original ZIP/XML re-access.
"""
from pathlib import Path
import argparse, collections, gzip, hashlib, json, re, xml.etree.ElementTree as E
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
sha=lambda b:hashlib.sha256(b).hexdigest()
def jt(p):return json.loads(p.read_text())
def gzj(p):return json.loads(gzip.decompress(p.read_bytes()))
def text(x):return ''.join(t.text or '' for t in x.iter(W+'t'))
def accepted(x):
 if x.tag in (W+'del',W+'moveFrom',W+'delText'):return ''
 if x.tag in (W+'t',M+'t'):return x.text or ''
 if x.tag in (W+'tab',W+'br',W+'cr'):return ' '
 return ''.join(accepted(c) for c in x)
def squash(s):return re.sub(r'\s+','',s)
def math_tree(x):
 if x.tag in (W+'del',W+'moveFrom',W+'delText'):return []
 local=x.tag.rsplit('}',1)[-1]
 if local.endswith('Pr') or x.tag in (W+'proofErr',W+'bookmarkStart',W+'bookmarkEnd'):return []
 if x.tag==M+'t':return [squash(x.text or '')]
 merged=[]
 for v in [v for c in x for v in math_tree(c)]:
  if not v:continue
  if isinstance(v,str) and merged and isinstance(merged[-1],str):merged[-1]+=v
  else:merged.append(v)
 if x.tag.startswith(M) and local not in ('r','oMath'):return [[local,{k.rsplit('}',1)[-1]:v for k,v in x.attrib.items()},merged]]
 return merged
def rows_from_fragment(x):
 shared={int(k):''.join(t.text or '' for t in E.fromstring(v).iter(S+'t')) for k,v in x['raw_shared_string_items'].items()}
 def values(r):
  result={}
  for c in r.findall(S+'c'):
   col=re.match('[A-Z]+',c.get('r')).group();v=c.find(S+'v')
   result[col]=(''.join(t.text or '' for t in c.iter(S+'t')) if c.get('t')=='inlineStr' else '' if v is None else shared[int(v.text)] if c.get('t')=='s' else v.text or '')
  return result
 header=values(E.fromstring(x['raw_rows'][str(x['header_row'])]))
 out={}
 for k,raw in x['raw_rows'].items():
  if int(k)==x['header_row']:continue
  vals=values(E.fromstring(raw));out[int(k)]={name:vals.get(col,'') for col,name in header.items() if name}
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--preparation',type=Path,default=Path(__file__).resolve().parent);args=ap.parse_args()
 here=args.preparation; receipt=jt(here/'source_fragment_extraction_receipt.json');fragments=here/'fragments'
 references={};count=0
 for pin in receipt['register_fragments']:
  p=fragments/pin['path'];assert p.stat().st_size==pin['bytes'] and sha(p.read_bytes())==pin['sha256'];x=gzj(p);actual=rows_from_fragment(x)
  for exp in x['selected_rows_expected']:
   got=actual[exp['excel_row']];assert got==exp['properties'];assert 'NR_FeMIMO-Core' in [v.strip() for v in got['Related WIs'].split(',')];assert got['Type'] in ('CR','draftCR','pCR')
   references[got['TDoc']]=got;count+=1
 assert count==482 and len(references)==482
 expected_counts={'38.211':5,'38.212':22,'38.213':152,'38.214':303};assert dict(collections.Counter(x['Spec'] for x in references.values()))==expected_counts
 ids=sorted(k for k,v in references.items() if v['Spec']=='38.211');assert len(ids)==5
 occurrences=[]
 for pin in receipt['report_streams']:
  p=fragments/pin['path'];assert p.stat().st_size==pin['bytes'] and sha(p.read_bytes())==pin['sha256'];x=gzj(p)
  counts={i:sum(i in b['text'] for b in x['blocks']) for i in ids};assert counts==pin['block_counts']
  for n,b in enumerate(x['blocks']):
   hit=sorted(i for i in ids if i in b['text'])
   if hit:occurrences.append((pin['original_locator'],n,hit))
 assert len(receipt['report_streams'])==61 and len(occurrences)==8
 normative=fragments/'normative'
 result=[]
 for spec,cr,tdoc,ci,target in [('38.212','0117','R1-2208069',12,None),('38.213','0345','R1-2208068',25,476),('38.214','0318','R1-2208181',18,1362)]:
  old=list(E.fromstring(gzip.decompress((normative/(spec.replace('.','')+'-h20_document.xml.gz')).read_bytes())).find(W+'body'))
  new=list(E.fromstring(gzip.decompress((normative/(spec.replace('.','')+'-h30_document.xml.gz')).read_bytes())).find(W+'body'))
  final=list(E.fromstring(gzip.decompress((normative/(tdoc+'_final_pack_document.xml.gz')).read_bytes())).find(W+'body'))
  assert tdoc in '\n'.join(text(b) for b in final[:8])
  history=lambda body:[list(map(lambda c:text(c).strip(),r.findall(W+'tc'))) for b in body if b.tag==W+'tbl' for r in b.findall(W+'tr') if len(r.findall(W+'tc'))>=8 and text(r.findall(W+'tc')[0]).strip()=='2022-09' and text(r.findall(W+'tc')[1]).strip()=='RAN#97-e' and text(r.findall(W+'tc')[3]).strip()==cr]
  assert not history(old);hh=history(new);assert len(hh)==1 and hh[0][2]=='RP-222400' and hh[0][-1]=='17.3.0'
  if target is not None:
   assert squash(accepted(final[ci]))==squash(accepted(new[target]));assert math_tree(final[ci])==math_tree(new[target]);assert not any(squash(accepted(b))==squash(accepted(final[ci])) for b in old if b.tag==final[ci].tag)
   result.append({'spec':spec,'accepted_target_exact':True,'math_structure_equal':True})
  else:
   a,b=old[2911],new[2932]
   assert squash(accepted(a).replace('codeBook','codebook'))==squash(accepted(b));assert accepted(a).count('codeBook')==3;assert math_tree(a)==math_tree(b)
   assert squash(accepted(final[ci]))!=squash(accepted(b))
   result.append({'spec':spec,'old_to_new_codeBook_case_edits':3,'whole_final_CR_vs_new_TS_table_exact':False})
 for name in ['RP-223436_document.xml.gz','rp-222691_document.xml.gz']:
  body=list(E.fromstring(gzip.decompress((normative/name).read_bytes())).find(W+'body'))
  assert text(body[3608]).startswith('RP-222400') and 'For: Approval' in text(body[3609]) and text(body[3610])=='Decision: The document was approved.'
 print(json.dumps({'status':'PASS','scope':'Included source-derived streams, exact source-row XML fragments and normative raw XML. Full61 original DOCX replay is separate and not claimed here.','register_CR_rows':482,'source_target_counts':expected_counts,'reports':61,'outside_ID_occurrence_blocks':8,'normative_comparisons':result,'original560_pass_increment':0,'human_expert_n':0,'native_calls':0,'API_calls':0}))
if __name__=='__main__':main()
