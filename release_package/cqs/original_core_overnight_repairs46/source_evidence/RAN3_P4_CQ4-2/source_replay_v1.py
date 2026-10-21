"""Replay original CR cover fields and same-CR documentary approval witnesses."""
import hashlib,io,json,re,zipfile,xml.etree.ElementTree as E
from pathlib import Path
import binary_reader_v2 as binary_reader
import binary_styles_v2 as binary_styles
import original_ooxml_reader_v2 as ooxml
H=lambda b:hashlib.sha256(b).hexdigest()
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
HEADER=re.compile(r'^R3-\d{6}[ \t]+\S')
norm=lambda s:re.sub(r'\s+',' ',s or '').strip()
def inline(e):
 return ''.join((x.text or '') if x.tag in {W+'t',W+'delText'} else '\t' if x.tag==W+'tab' else '\n' if x.tag in {W+'br',W+'cr'} else '' for x in e.iter())
def text(e):
 if e.tag==W+'p':return inline(e)
 if e.tag==W+'tbl':return '\n'.join('\t'.join(text(c) for c in row.findall(W+'tc')) for row in e.findall(W+'tr'))
 return '\n'.join(inline(p) for p in e.findall(W+'p'))
def read_fields(item,raw,cr):
 fields=[];meta={}
 if item['original_format']=='CFB':
  body,direct,meta=binary_reader.parse_doc(raw)
  assert cr['tdocNumber'] in body[:2500]
  styles=binary_styles.stylesheet(raw)
  # Every character-style branch is checked rather than assuming an applied
  # style cannot add a watched property to a cover-field run.
  assert not styles['watched_style_operations']
  meta['style_graph']=styles
  for f in binary_styles.source_fields(body):
   direct_watched=[];runs={}
   for cp in range(f['cp_start'],f['cp_end']):
    info=direct(cp);key=(info['FKP_page'],info['FKP_run'],info['piece']['cp_start'])
    runs.setdefault(key,dict(info,cp_first=cp))
    for op in info['direct_PRLs']+info['piece_character_PRLs']:
     if int(op['sprm'],16) in binary_styles.WATCH:direct_watched.append({'cp':cp,'text':body[cp],**op})
   assert not direct_watched,(cr['tdocNumber'],f['field'],'watched direct/piece property')
   value=f['transcribed_value'].strip()
   assert (value if value else None)==cr[f['field']],(cr['tdocNumber'],f['field'],'exact trimmed cover field')
   fields.append(dict(f,source_value_after_trim=value or None,frozen_value=cr[f['field']],exact_after_text_trim=True,
    direct_piece_watched_properties=direct_watched,character_runs=list(runs.values())))
  return {'tdocNumber':cr['tdocNumber'],'source_format':'original_CFB_root_WordDocument','cover_identity':body[:2500],
   'source_fields':fields,'original_main_story_sha256':H(body.encode()),'source_reader_metadata':meta}
 assert item['original_format']=='OOXML'
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  document=z.read('word/document.xml');styles=z.read('word/styles.xml')
 tree=E.fromstring(document);active=ooxml.open_report_bytes(raw)
 cover='\n'.join(text(x) for x in tree.find(W+'body'))[:2500]
 assert cr['tdocNumber'] in cover
 for field,label in [('reasonForChange','Reason for change:'),('summaryOfChange','Summary of change:')]:
  hits=[]
  for ti,table in enumerate(tree.iter(W+'tbl')):
   for ri,row in enumerate(table.findall(W+'tr')):
    cells=row.findall(W+'tc')
    if len(cells)>=2 and norm(text(cells[0]))==label:hits.append((ti,ri,cells[1]))
  assert len(hits)==1,(cr['tdocNumber'],field,len(hits))
  ti,ri,cell=hits[0];value=text(cell).strip()
  assert (value or None)==cr[field],(cr['tdocNumber'],field,repr(value),repr(cr[field]))
  # The entire cover fields must be active here. Literal text authority is
  # retained; active equality is an observed fact of these two source cells.
  runs_by_hash={r['run_XML_sha256']:r for b in active['blocks'] for r in b['runs']}
  runs=[runs_by_hash[H(E.tostring(r,encoding='utf-8'))] for r in cell.iter(W+'r')]
  assert all(r['active'] and not r['deleted_text'] for r in runs)
  fields.append({'field':field,'table_index0':ti,'row_index0':ri,'source_value_after_trim':value or None,'frozen_value':cr[field],
   'exact_after_text_trim':True,'source_cell_XML':E.tostring(cell,encoding='unicode'),'direct_inherited_runs':runs})
 return {'tdocNumber':cr['tdocNumber'],'source_format':'original_OOXML','cover_identity':cover,'source_fields':fields,
  'document_XML_sha256':H(document),'styles_XML_sha256':H(styles)}
def replay(manifest,folder,witnesses):
 bytid={r['CR']['tdocNumber']:r['CR'] for r in witnesses}
 fields=[];reports={};opened=[]
 for item in manifest:
  raw=(folder/item['payload_file']).read_bytes()
  assert H(raw)==item['member_sha256'] and len(raw)==item['member_bytes']
  opened.append({k:item[k] for k in ['kind','tdocNumber','meeting','archive_sha256','member','member_sha256','member_bytes','original_format']})
  if item['kind']=='CR':fields.append(read_fields(item,raw,bytid[item['tdocNumber']]))
  else:reports[item['meeting']]=ooxml.open_report_bytes(raw)
 approvals=[];bindings=[]
 agreement_seen=set()
 for witness in witnesses:
  cr=witness['CR'];td=cr['tdocNumber']
  assert len(witness['Agreement'])==1
  agreement=witness['Agreement'][0];rid=agreement['resolutionId'];meeting=rid.split('-')[1]
  blocks=reports[meeting]['blocks'];headers=[b for b in blocks if HEADER.match(b['text'])]
  targets=[b for b in headers if re.match(re.escape(td)+r'[ \t]+\S',b['text'])]
  assert len(targets)==1,(td,'own anchored header',len(targets))
  start=targets[0]['index'];end=next((b['index'] for b in headers if b['index']>start),len(blocks))
  own=blocks[start:end]
  ds=[b for b in own if re.search(r'\bDecision\s*:\s*The document was\s+agreed\s*\.',b['text'],re.I)]
  assert len(ds)==1,(td,'own document agreed',len(ds))
  assert ds[0]['text']==ds[0]['active_text'] and targets[0]['text']==targets[0]['active_text']
  metadata=[b for b in own if re.search(r'\bType:\s*CR\b',b['text'])]
  assert metadata and all(b['text']==b['active_text'] for b in metadata)
  content=agreement['content']
  retained_heads=[l.strip() for l in content.splitlines() if HEADER.match(l.strip())]
  assert td in [HEADER.match(l).group(0).split()[0] for l in retained_heads]
  assert norm(ds[0]['text']) in norm(content)
  # Identity and own outcomes are source checks of the existing reference
  # proxy. They do not replace the original Resolution body with an own-prefix.
  first=next(l.strip() for l in content.splitlines() if l.strip())
  anchors=[b for b in blocks if norm(b['text'])==norm(first)]
  assert len(anchors)==1,(rid,'original first-line anchor',first,len(anchors))
  anchor=anchors[0]['index'];assert anchor<start
  assert any(re.search(r'\bAgreement\s*:',b['text']) for b in blocks[max(0,anchor-2):anchor+1])
  source_heads=[b for b in headers if b['index']>=anchor]
  assert [norm(b['text']) for b in source_heads[:len(retained_heads)]]==[norm(x) for x in retained_heads],(rid,'all retained headers source order')
  if rid not in agreement_seen:
   bindings.append({'resolutionId':rid,'source_first_body_child0':anchor,'original_anchor':anchors[0],
    'retained_Agreement_content_sha256':H(content.encode()),'retained_header_count':len(retained_heads),
    'all_retained_header_binding':[{'retained_header':a,'source_body_child0':b['index'],'source_text':b['text'],'source_XML_sha256':b['body_XML_sha256']} for a,b in zip(retained_heads,source_heads)],
    'original_Resolution_boundary_preserved':True})
   agreement_seen.add(rid)
  approvals.append({'tdocNumber':td,'resolutionId':rid,'own_header_start0':start,'next_header_start0':end,
   'header':targets[0],'CR_metadata':metadata,'active_own_agreed':ds[0],
   'sameCR_agreed_in_retained_content':True,'all_report_target_mentions':[{'body_child0':b['index'],'text':b['text'],'active_text':b['active_text']} for b in blocks if td in b['text']]})
 assert len(fields)==5 and sum(len(x['source_fields']) for x in fields)==10 and len(approvals)==5 and len(bindings)==2
 return {'status':'PASS_ORIGINAL_SEVEN_ARCHIVES_TEN_COVER_FIELDS_FIVE_SAME_CR_ACTIVE_AGREED','original_source_members':opened,
  'CR_fields':fields,'same_CR_approval_roles':approvals,'retained_Agreement_source_bindings':bindings,
  'report_format_metadata':[{'meeting':k,**{a:b for a,b in v.items() if a!='blocks'}} for k,v in reports.items()],
  'source_blank_summary_to_null':[r['tdocNumber'] for r in fields if next(f for f in r['source_fields'] if f['field']=='summaryOfChange')['source_value_after_trim']is None],
  'bounded_scope':'The authored captured-reason ASC5 frontier and its original same-CR source witnesses. No global approval classifier or source-empty conclusion for captured null fields.',
  'new_API_native_calls':0,'human_expert_n':0,'ROOT_seal':False}
