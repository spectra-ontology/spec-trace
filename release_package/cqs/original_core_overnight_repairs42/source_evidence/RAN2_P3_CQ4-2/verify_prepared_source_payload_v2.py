"""Self-contained prepared source replay for current-CQ direct CR outcome evidence.
This verifies saved source/graph bindings. Independent review/native final gates remain separate.
"""
import collections,gzip,hashlib,importlib.util,json,pathlib,re,sys,xml.etree.ElementTree as E
if sys.flags.optimize:raise SystemExit('Optimization unsupported')
F=pathlib.Path(__file__).absolute().parent
S=F/'source_payload_v1'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
X='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def readgz(p):return json.loads(gzip.decompress(p.read_bytes()))
def norm(s):return ' '.join(s.split())
def tokens(s):return ' '.join(re.findall(r'\w+|[^\w\s|]',''.join(' ' if ord(c)<32 else c for c in s),re.UNICODE))
def text(e):return ''.join(t.text or '' if t.tag==W+'t' else '\t' if t.tag==W+'tab' else '\n' if t.tag in {W+'br',W+'cr'} else '' for t in e.iter())
def field_results(s):
 stack=[];out=[]
 for ch in s:
  if ch=='\x13':stack.append(False)
  elif ch=='\x14':assert stack;stack[-1]=True
  elif ch=='\x15':assert stack;stack.pop()
  elif all(stack):out.append(ch)
 assert not stack
 return ''.join(out)
def format_runs(paragraph,styles_raw):
 st=E.fromstring(styles_raw);styles={s.get(W+'styleId'):s for s in st.findall(W+'style')};defaults=st.find(W+'docDefaults/'+W+'rPrDefault/'+W+'rPr')
 def chain(sid):
  seen=set();out=[]
  while sid:
   assert sid not in seen and sid in styles;seen.add(sid);s=styles[sid];out.append(s);b=s.find(W+'basedOn');sid=b.get(W+'val') if b is not None else None
  return out
 ps=paragraph.find(W+'pPr/'+W+'pStyle');pc=chain(ps.get(W+'val')) if ps is not None else [s for d in styles.values() if d.get(W+'type')=='paragraph' and d.get(W+'default') in {'1','true','on'} for s in chain(d.get(W+'styleId'))]
 parents={ch:p for p in paragraph.iter() for ch in p};out=[]
 for run in paragraph.iter(W+'r'):
  lit=text(run)
  if not lit.strip():continue
  rp=run.find(W+'rPr');rs=None if rp is None else rp.find(W+'rStyle');rc=chain(rs.get(W+'val')) if rs is not None else [];flags=[]
  for holder in [defaults]+[s.find(W+'rPr') for s in pc+rc]+[rp]:
   if holder is None:continue
   for k in ['strike','dstrike','vanish','webHidden']:
    prop=holder.find(W+k)
    if prop is not None and prop.get(W+'val','true').lower() not in {'0','false','off'}:flags.append(k)
  ancestors=[];p=parents.get(run)
  while p is not None:ancestors.append(p.tag);p=parents.get(p)
  deleted=any(t in {W+'del',W+'moveFrom'} for t in ancestors)
  out.append({'literal':lit,'strike_hidden_flags':flags,'deleted_or_moveFrom':deleted})
 assert out and all(not r['strike_hidden_flags'] and not r['deleted_or_moveFrom'] for r in out)
 return out

def main():
 definition=read(F/'definition.json');criteria=read(F/'criteria.json')
 repair=sha(json.dumps(definition,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
 assert repair=='e932ae9fdc67fc5ce77fbd321a52a0d55e6933721618262aebf6fd446c66aad0'
 assert sha((F/'criteria.json').read_bytes())=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
 scope=read(S/'preparation_scope_and_actual_reopen.json')
 for p in scope['files']:
  file=S/pathlib.Path(p['path']).name;assert file.stat().st_size==p['bytes'] and sha(file.read_bytes())==p['sha256']
 frontier=readgz(S/'complete_recorded_frontier_projection.json.gz')
 assert len(frontier['paths'])==2351 and len(frontier['Resolution_content'])==474
 content={r['node_id']:r for r in frontier['Resolution_content']};geo={r['node_id']:r for r in frontier['source_geometry']}
 original=[r for r in frontier['paths'] if r['specNumber']=='38.331'];assert len(original)==857 and len({r['resolutionId'] for r in original})==233
 original.sort(key=lambda r:r['resolutionId'],reverse=True)
 components=read(F/'actual_generic_predicate_translation_receipt.json')['regex_components']
 def positive(content,tdoc):return bool(re.fullmatch(components['header_prefix']+tdoc+components['header_suffix'],content) or re.fullmatch(components['named_prefix']+tdoc+components['named_suffix'],content))
 selected_pool=[r for r in original if positive(content[r['resolution_node']]['content'],r['tdocNumber'])]
 assert len(selected_pool)==160 and len({r['resolutionId'] for r in selected_pool})==92
 selected=selected_pool[:10];assert selected[-1]['resolutionId']>selected_pool[10]['resolutionId']
 expected=read(F/'expected_SQL_all160_full_two_columns.json');select_expected=read(F/'expected_SQL_selected10_full_two_columns.json')
 tuples=lambda rows:collections.Counter((r['resolutionId'],r['tdocNumber']) for r in rows)
 assert tuples(selected_pool)==collections.Counter((r['r.resolutionId'],r['cr.tdocNumber']) for r in expected)
 assert tuples(selected)==collections.Counter((r['r.resolutionId'],r['cr.tdocNumber']) for r in select_expected)
 assert {r['resolutionId'] for r in selected}=={r['resolutionId'] for r in read(F/'expected_requested_resolutionId_set8.json')}
 prefix=[r for r in original if r['resolutionId']>=selected[-1]['resolutionId']];assert len(prefix)==45 and len({r['resolutionId'] for r in prefix})==19
 source_ox=readgz(S/'nineteen_original_body_fragments_and45_role_witnesses.json.gz')
 source_bin=read(S/'original_native_CFB_lexical_witnesses.json')
 source={r['node_id']:r for r in source_ox+source_bin};assert len(source)==19 and set(source)=={r['resolution_node'] for r in prefix}
 styles={r['member_sha256']:r for r in readgz(S/'original_style_parts.json.gz')};assert len(styles)==8
 for x in styles.values():assert sha(x['XML'].encode())==x['styles_XML_sha256']
 role_paths=[]
 for node,p in source.items():
  assert p['retained_content']==content[node]['content'] and p['source_geometry']==geo[node]
  assert sha(p['retained_content'].encode())==p['retained_content_sha256']==geo[node]['content_sha256']
  for r in p['source_roles']:
   role_paths.append(r['path']);assert r['direct_outcome_candidate'] is positive(p['retained_content'],r['path']['tdocNumber'])
  if p in source_ox:
   fr=p['source_fragments'];assert fr[0]['raw_body_child']==p['marker_raw_body_child']
   assert all(fr[i+1]['raw_body_child']==fr[i]['raw_body_child']+1 for i in range(len(fr)-1))
   for e in fr:assert text(E.fromstring(e['XML']))==e['text']
   assert norm(fr[0]['text'])==norm(geo[node]['marker_text'])
   assert tokens(p['retained_content']) in tokens('\n'.join(e['text'] for e in fr))
   assert styles[p['member_sha256']]['styles_XML_sha256']==p['styles_XML_sha256']
 assert tuples(role_paths)==tuples(prefix)
 # Decode complete original native Word lexical field results, with both source streams pinned by member hash.
 sys.path.insert(0,str(S));sp=importlib.util.spec_from_file_location('native_CFB_text',S/'native_CFB_text.py');module=importlib.util.module_from_spec(sp);sp.loader.exec_module(module)
 native_text={}
 for p in source_bin:
  raw=gzip.decompress((S/p['source_file']).read_bytes());assert sha(raw)==p['member_sha256'] and len(raw)==p['raw_member_bytes']
  if p['member_sha256'] not in native_text:
   decoded,meta=module.retained_CFB_text(raw);native_text[p['member_sha256']]=field_results(decoded)
  original_text=native_text[p['member_sha256']]
  assert sha(original_text.encode())==p['original_text_sha256']
  assert tokens(p['retained_content']) in tokens(original_text)
 # Decode exact original named register fields for every one of the45 unfiltered prefix paths.
 fields={};registers=readgz(S/'selected_original_register_header_cells.json.gz')
 for register in registers:
  strings={int(i):''.join(t.text or '' for t in E.fromstring(x).iter(X+'t')) for i,x in register['selected_shared_strings'].items()}
  def cells(xml):
   out={}
   for c in E.fromstring(xml).findall(X+'c'):
    v=c.find(X+'v');v=v.text if v is not None else ''
    if c.get('t')=='s':v=strings[int(v)]
    elif c.get('t')=='inlineStr':v=''.join(t.text or '' for t in c.iter(X+'t'))
    out[re.sub(r'\d','',c.get('r'))]=v or ''
   return out
  header={name:col for col,name in cells(register['header_row_XML']).items()}
  for row in register['rows']:
   raw=cells(row['row_XML']);decoded={name:raw.get(header.get(name,''),'') for name in row['expected_fields']};assert decoded==row['expected_fields']
   assert decoded['Spec'].strip()=='38.331';tdoc=decoded['TDoc'];assert tdoc not in fields or fields[tdoc]==decoded;fields[tdoc]=decoded
 assert set(fields)=={r['tdocNumber'] for r in prefix}
 for p in prefix:
  f=fields[p['tdocNumber']];assert f['TDoc Status']==p['status'] and f['Title']==p['title']
 # Actual source-positive paragraph active-status check for the selected OOXML events.
 active=[]
 for row in selected:
  p=source[row['resolution_node']]
  ev=next(r for r in p['source_roles'] if r['path']['tdocNumber']==row['tdocNumber'])['outcome_evidence']
  assert ev
  if p in source_bin:
   assert fields[row['tdocNumber']]['TDoc Status']=='agreed'
   active.append({'resolutionId':row['resolutionId'],'tdocNumber':row['tdocNumber'],'scope':'Original nativeCFB lexical fullbody and formal agreed; native formatting not certified'});continue
  fragments=p['source_fragments'];style=styles[p['member_sha256']]['XML'];supported=[]
  for e in ev:
   hits=[r for r in fragments if norm(r['text'])==norm(e['literal'])]
   for h in hits:
    if e['header_line'] is not None:
     headerline=p['retained_content'].splitlines()[e['header_line']];head=[r for r in fragments if norm(r['text'])==norm(headerline)]
     pairs=[(hh,h) for hh in head if hh['raw_body_child']<h['raw_body_child'] and not any(re.match(r'^R2-\d{7}\t',z['text']) for z in fragments if hh['raw_body_child']<z['raw_body_child']<h['raw_body_child'])]
     if not pairs:continue
     format_runs(E.fromstring(pairs[0][0]['XML']),style)
    runs=format_runs(E.fromstring(h['XML']),style);supported.append({'source_raw_body_child':h['raw_body_child'],'literal':e['literal'],'runs_n':len(runs)})
  assert supported,(row,'original active outcome not bound')
  active.append({'resolutionId':row['resolutionId'],'tdocNumber':row['tdocNumber'],'scope':'Original OOXML own event paragraph/direct+inherited strike/deletion/hidden checked','evidence':supported})
 return {'status':'PASS_PREPARED_SOURCE_ONLY','id':definition['id'],'repair_sha256':repair,'original_paths':857,'source_prefix_paths':45,'source_prefix_Resolution_n':19,'original_OOXML_members':8,'original_CFB_members':2,'direct_source_prefix_event_paths':sum(positive(p['retained_content'],r['path']['tdocNumber']) for p in source.values() for r in p['source_roles']),'selected_rows':10,'requested_Resolution_identity_n':8,'active_selected_source_evidence':active,'source_native_CFB_scope':'native lexical fullbody and formal agreed status, not rendering certification','source_metadata_scope':'Included fragments/field projections and immutable input pins; optional full archives remain separate','formal_register_row_occurrences':sum(len(r['rows']) for r in registers),'formal_unique_CR_rows':len(fields),'native_gate':'pending actual Java/Cypher execution and full typed SQL binding','semantic_secondary':'pending independent ROOT judgment','API_calls':0,'native_calls':0,'new_admissions':0}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False))
