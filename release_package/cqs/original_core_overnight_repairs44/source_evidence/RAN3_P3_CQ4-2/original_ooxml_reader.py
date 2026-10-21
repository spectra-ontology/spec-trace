"""Replay the bounded original RAN3 approval-provenance source frontier."""
from pathlib import Path
import hashlib,json,re,zipfile,xml.etree.ElementTree as E

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
FLAGS=('strike','dstrike','vanish','webHidden')
HEADER=re.compile(r'^R3-[0-9]{6}[ \t]+\S')
DECISION=re.compile(r'(?i)^[ \t]*(?:Decision:[ \t]*)?The[ \t]+document[ \t]+was[ \t]+([^\r\n]*)')
POSITIVE=re.compile(r'(?i)^(?:agreed(?:[ \t]+in[ \t]+principle)?|endorsed|approved|conditionally[ \t]+agreed)(?=[ \t.,!(;]|$)')

def H(b):return hashlib.sha256(b).hexdigest()
def text(e):
 return ''.join((x.text or '') if x.tag==W+'t' else '\t' if x.tag==W+'tab' else '\n' if x.tag in {W+'br',W+'cr'} else '' for x in e.iter())
def flags(pr):
 if pr is None:return {}
 return {k:pr.find(W+k).get(W+'val','true').lower() not in {'false','off','0'} for k in FLAGS if pr.find(W+k) is not None}

def open_report_bytes(raw):
 with zipfile.ZipFile(__import__('io').BytesIO(raw)) as z:
  assert z.testzip() is None
  document=z.read('word/document.xml');styles_raw=z.read('word/styles.xml')
 body=E.fromstring(document).find(W+'body');styles=E.fromstring(styles_raw)
 style_by_id={s.get(W+'styleId'):s for s in styles.findall(W+'style')}
 defaults=flags(styles.find(W+'docDefaults/'+W+'rPrDefault/'+W+'rPr'))
 def inherited(sid,seen=()):
  if not sid:return {}
  assert sid not in seen,('style cycle',sid)
  s=style_by_id.get(sid)
  assert s is not None,('missing style',sid)
  base=s.find(W+'basedOn');result=inherited(base.get(W+'val') if base is not None else None,seen+(sid,))
  return result|flags(s.find(W+'rPr'))
 default_p=next((s.get(W+'styleId') for s in styles.findall(W+'style') if s.get(W+'type')=='paragraph' and s.get(W+'default') in {'1','true','on'}),None)
 parent={child:par for par in body.iter() for child in par}
 out=[]
 for i,e in enumerate(body):
  runs=[]
  for r in e.iter(W+'r'):
   ancestors=[];cur=r
   while cur in parent:
    cur=parent[cur];ancestors.append(cur)
   p=next((a for a in ancestors if a.tag==W+'p'),None)
   pp=p.find(W+'pPr') if p is not None else None
   ps=pp.find(W+'pStyle') if pp is not None else None
   rp=r.find(W+'rPr');rs=rp.find(W+'rStyle') if rp is not None else None
   psid=ps.get(W+'val') if ps is not None else default_p
   rsid=rs.get(W+'val') if rs is not None else None
   effective=defaults|inherited(psid)|inherited(rsid)|flags(rp)
   removed=any(a.tag in {W+'del',W+'moveFrom'} for a in ancestors)
   deleted_text=''.join(x.text or '' for x in r.iter(W+'delText'))
   runs.append({'text':text(r),'deleted_text':deleted_text,'paragraph_style':psid,'character_style':rsid,
    'effective_flags':effective,'removed_ancestor':removed,'active':not removed and not any(effective.values()),
    'run_XML_sha256':H(E.tostring(r,encoding='utf-8'))})
  out.append({'index':i,'text':text(e),'active_text':''.join(r['text'] for r in runs if r['active']),
   'runs':runs,'body_XML_sha256':H(E.tostring(e,encoding='utf-8'))})
 return {'file_sha256':H(raw),'file_bytes':len(raw),'document_XML_sha256':H(document),
  'styles_XML_sha256':H(styles_raw),'body_elements_n':len(out),'style_definitions_n':len(style_by_id),'blocks':out}

def source_path(folder,resolution_id):
 meeting=resolution_id.split('-')[1]
 name={'97bis':'97bis','118':'118','111':'111-e','121bis':'121-bis'}[meeting]
 return folder/('Final_Report_RAN3-'+name+'.docx')

def replay(frontier,folder):
 paths={source_path(folder,r['resolutionId']) for r in frontier}
 reports={p:open_report(p) for p in sorted(paths)}
 rows=[]
 for row in frontier:
  p=source_path(folder,row['resolutionId']);blocks=reports[p]['blocks'];td=row['tdocNumber']
  headers=[b['index'] for b in blocks if re.match(re.escape(td)+r'[ \t]+\S',b['text'])]
  events=[]
  for start in headers:
   end=next((b['index'] for b in blocks[start+1:] if HEADER.match(b['text'])),len(blocks))
   ds=[b for b in blocks[start+1:end] if DECISION.match(b['text'])]
   assert len(ds)==1,(td,'own source terminal decision cardinality',len(ds))
   decision=ds[0];status=DECISION.match(decision['text']).group(1)
   # The entire own header and outcome are active, including inherited styles.
   assert blocks[start]['text']==blocks[start]['active_text'],(td,'inactive header')
   assert decision['text']==decision['active_text'],(td,'inactive decision')
   type_blocks=[b for b in blocks[start+1:end] if 'Type:' in b['text']]
   events.append({'header':blocks[start],'end_before_next_header':end,'metadata':type_blocks,
    'decision':decision,'source_outcome':status,'source_positive':bool(POSITIVE.match(status))})
  mentions=[{'index':b['index'],'text':b['text'],'active_text':b['active_text'],'body_XML_sha256':b['body_XML_sha256']} for b in blocks if td in b['text']]
  assert mentions,(row['resolutionId'],td,'no original report occurrence')
  source_positive=any(e['source_positive'] for e in events)
  assert source_positive==row['generic_positive'],(td,'source vs frozen event mismatch')
  if source_positive:
   assert all(any(re.search(r'\bType:[ \t]+(?:CR|draftCR|pCR)\b',b['text']) and '38.423' in b['text'] for b in e['metadata']) for e in events if e['source_positive']),(td,'CR object or target Spec missing')
  # A headerless occurrence does not inherit the outcome of the replacing CR.
  assert events or all(not re.match(re.escape(td)+r'[ \t]+\S',m['text']) for m in mentions)
  rows.append({'resolutionId':row['resolutionId'],'tdocNumber':td,'final_status_diagnostic':row['status'],
   'source_report':p.name,'own_source_events':events,'source_mentions':mentions,
   'frozen_events':row['events'],'frozen_positive':row['generic_positive'],
   'source_role_positive':source_positive,'classification':'same_CR_endorsed' if source_positive else 'same_CR_nonapproval' if events else 'reference_only_without_own_current_meeting_approval',
   'source_scope':'Source corroboration of this existing Resolution→CR path; the original Resolution boundary/REFERENCES proxy is retained.'})
 result={'status':'PASS_ACTUAL_FOUR_ORIGINAL_REPORTS_ALL35_PRE_CUTOFF_SOURCE_ROLES',
  'scope':'Original 617 path population, unfiltered pre-cutoff 35 paths/10 Resolution bodies. Full125 query diagnostics are not a globally source-certified approval classifier.',
  'reports':[{k:v for k,v in item.items() if k!='blocks'}|{'filename':p.name} for p,item in reports.items()],
  'rows':rows,'counts':{'pre_cutoff_paths':len(rows),'pre_cutoff_Resolution_ids':len({r['resolutionId'] for r in rows}),
   'positive_paths':sum(r['source_role_positive'] for r in rows),'negative_own_paths':sum(r['classification']=='same_CR_nonapproval' for r in rows),
   'reference_only_paths':sum(r['classification']=='reference_only_without_own_current_meeting_approval' for r in rows)},
  'source_fields':{'CR_object':'Own original report Type: CR and Spec38.423 for all ten selected paths.',
   'approval':'Own terminal document outcome in active original WordXML, direct+paragraph/character inherited strike/deletion/hidden checked.'},
  'new_API_calls':0,'new_native_calls':0,'ROOT_seal':False,'human_expert_n':0}
 assert result['counts']=={'pre_cutoff_paths':35,'pre_cutoff_Resolution_ids':10,'positive_paths':10,'negative_own_paths':15,'reference_only_paths':10},result['counts']
 return result

if __name__=='__main__':
 HERE=Path(__file__).resolve().parent
 ROOT=next(p for p in HERE.parents if (p/'CLAUDE.md').is_file())
 frontier=json.loads((HERE/'actual_unfiltered_pre_cutoff_source_role_frontier_v1.json').read_text())
 out=replay(frontier,ROOT/'ontology/input/tsg/RAN/formal/meetings/RAN3/Final_Report')
 p=HERE/'actual_four_reports_all35_active_source_role_replay_v1.json'
 with p.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'status':out['status'],'counts':out['counts'],'receipt_sha256':H(p.read_bytes())}))
