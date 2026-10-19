#!/usr/bin/env python3
"""Read-only, generic original own-CR-form summary probe; no graph/model writes."""
import collections,hashlib,importlib.util,io,json,pathlib,re,sqlite3,sys,zipfile
import xml.etree.ElementTree as E
sys.dont_write_bytecode=True
ROOT=pathlib.Path('/home/sihyeon/workspace/spectra')
B=ROOT/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit'
HERE=pathlib.Path(__file__).resolve().parent
BASE=ROOT/'data/corpus/tsg/RAN/formal/meetings/RAN4'
PRIOR=B/'RAN3_RAN4/RAN4_93_Annex_D_and_whole_document_decision_roles_v1'
AUTH=HERE.parent/'RAN4_93_default_and_approved_record_authority'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
NS={'w':W[1:-1]}
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):return {'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
def save(n,v):(HERE/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def jl(n,rows):
 with (HERE/n).open('w') as f:
  for r in rows:f.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
def xt(e,final=False):
 def walk(n):
  if final and n.tag==W+'del':return ''
  if n.tag in (W+'t',W+'delText',M+'t'):return n.text or ''
  if n.tag==W+'tab':return '\t'
  if n.tag in (W+'br',W+'cr'):return '\n'
  return ''.join(walk(c) for c in n)
 return walk(e)
def cp(e,final=False):return '\n'.join(xt(p,final) for p in e.findall(W+'p'))
def norm(t):return ' '.join(t.split())
def label(t):
 s=re.sub('[^a-z]','',t.lower())
 return next((v for k,v in [('reasonforchange','reason'),('summaryofchange','summary'),('consequencesifnotapproved','consequences'),('clausesaffected','clauses')] if s==k),None)
def marks(e):return {'deletion_nodes':len(list(e.iter(W+'del'))),'strike_nodes':len(list(e.iter(W+'strike'))),'double_strike_nodes':len(list(e.iter(W+'dstrike'))),'style_references':sorted({n.get(W+'val') for n in e.iter() if n.tag in (W+'pStyle',W+'rStyle')})}
modulepath=ROOT/'scripts/tsg/RAN/formal/common/doc_fields.py'
spec=importlib.util.spec_from_file_location('source_doc_fields_readonly',modulepath)
df=importlib.util.module_from_spec(spec);spec.loader.exec_module(df)
roles=[json.loads(l) for l in (PRIOR/'all1858_CR_family_source_Decision_boundaries.jsonl').read_text().splitlines()]
assert len(roles)==1858 and len({r['tdocNumber']for r in roles})==1858
prefix=json.loads((AUTH/'all17_prefix_own_span_decision_and_corrections_fresh.json').read_text())
prefixids={r['tdocNumber']for r in prefix};assert len(prefixids)==17
db=B.parent/'relational/RAN4.sqlite'
conn=sqlite3.connect('file:'+str(db)+'?mode=ro&immutable=1',uri=True)
frozen=collections.defaultdict(list)
ids={r['tdocNumber']for r in roles}
for r in conn.execute('select node_id,tdocNumber,summaryOfChange,type,status from Tdoc'):
 if r[1] in ids:frozen[r[1]].append({'node_id':r[0],'summaryOfChange':r[2],'type':r[3],'status':r[4]})
conn.close()
inventory=[];results=[];patch=[];prefixdetails=[]
for i,role in enumerate(roles):
 k=role['tdocNumber'];archive=BASE/'source/TSGR4_93/Docs'/(k+'.zip')
 row={'tdocNumber':k,'original_type':role['raw_type'],'original_final_status':role['raw_final_status'],'original_revised_to':role['raw_revised_to'],'original_register_row':role['source_register_row'],'frozen_records':frozen[k],'archive_exists':archive.exists(),'members':[]}
 details=[]
 if archive.exists():
  row['archive']=pin(archive)
  try:
   with zipfile.ZipFile(archive)as z:
    assert z.testzip()is None
    entries=[n for n in z.infolist()if not n.is_dir()]
    for entry in entries:
     raw=z.read(entry);m={'name':entry.filename,'bytes':len(raw),'sha256':sha(raw),'CRC32':entry.CRC}
     row['members'].append(m)
     if pathlib.Path(entry.filename).suffix.lower()not in ('.doc','.docx'):m['access']='unsupported_non_Word_member';continue
     native=None;docx=None;derivative=None
     if raw[:8]==bytes.fromhex('d0cf11e0a1b11ae1'):
      try:
       stories,props=df._doc_read(raw,props=True)
       native={'story_lengths':list(map(len,stories)),'main_story_sha256':sha(stories[0].encode()),'main_story':stories[0]if k in prefixids else None,'deletion_properties_read':props is not False,'strikethrough_properties_directly_decoded':False}
       if props and props is not False and props[0] is not None:
        native['main_story_with_deleted_characters_removed']=props[0][1].replace('\ufdd0','')if k in prefixids else None
      except Exception as e:native={'error':type(e).__name__+': '+str(e)}
      sibling=BASE/'derived/TSGR4_93/Docs'/k/pathlib.Path(entry.filename).name
      candidate=sibling.with_suffix('.docx')
      if sibling.exists()and sibling.read_bytes()==raw and candidate.exists():
       docx=candidate.read_bytes();derivative={'pin':pin(candidate),'exact_original_DOC_sibling_verified':True,'original_DOC':pin(sibling),'new_conversion_run':False}
      else:m['access']='original_CFB_read_existing_conversion_unavailable';m['native_CFB']=native;continue
     elif zipfile.is_zipfile(io.BytesIO(raw)):docx=raw
     else:m['access']='unsupported_or_corrupt_Word';continue
     try:
      with zipfile.ZipFile(io.BytesIO(docx))as dz:
       assert dz.testzip()is None
       xml=dz.read('word/document.xml');tree=E.fromstring(xml)
       styles=dz.read('word/styles.xml')if 'word/styles.xml'in dz.namelist()else b''
      paras=list(tree.iter(W+'p'))
      cover='\n'.join(xt(p,True)for p in paras[:30])
      own=bool(re.search(r'(?<![A-Za-z0-9])'+re.escape(k)+r'(?!\d)',cover))
      own_tokens=sorted(set(re.findall(r'(?<![A-Za-z0-9])R4-\d{6,7}(?!\d)',cover)))
      fields=[]
      for ti,t in enumerate(tree.iter(W+'tbl')):
       rows=t.findall(W+'tr');labs={label(cp(c,True))for rr in rows for c in rr.findall(W+'tc')[:2]}
       if len(labs- {None})<2:continue
       for ri,rr in enumerate(rows):
        cells=rr.findall(W+'tc');texts=[cp(c,True).strip()for c in cells]
        hits=[ci for ci,v in enumerate(texts[:2])if label(v)=='summary']
        for ci in hits:
         values=[v for v in texts[ci+1:]if v]
         val=values[0]if len(values)==1 else None
         ev={'table_index0':ti,'row_index0':ri,'row_ET_UTF8_sha256':sha(E.tostring(rr,encoding='utf-8')),'label':texts[ci],'cells_literal':[cp(c,False)for c in cells],'cells_final_text':texts,'value':val,'value_ambiguous':len(values)>1,**marks(rr)}
         fields.append(ev)
      unique={v['value']for v in fields if v['value']is not None}
      summary=next(iter(unique))if len(unique)==1 else None
      field_status='UNIQUE_EXPLICIT_OWN_CR_FORM_SUMMARY'if own and len(unique)==1 else 'NO_EXPLICIT_CR_FORM_SUMMARY'if not fields else 'AMBIGUOUS_OR_IDENTITY_UNBOUND'
      native_matches=None
      if native and 'error'not in native and summary:
       native_matches=norm(summary)in norm(stories[0])
      found={'member':m,'access':'original_DOCX'if derivative is None else'existing_exact_member_DOC_to_DOCX_derivative','derivative':derivative,'word_document_XML_sha256':sha(xml),'styles_XML_sha256':sha(styles),'cover_first30_ownID_present':own,'cover_first30_R4_tokens':own_tokens,'field_status':field_status,'summary':summary if own else None,'summary_rows':fields,'native_CFB_summary_literal_whitespace_fold_match':native_matches,'native_CFB':native if k in prefixids else {a:b for a,b in(native or{}).items()if a not in('main_story','main_story_with_deleted_characters_removed')}}
      if k in prefixids:
       found['cover_first30_paragraphs']=[{'paragraph_index0':j,'literal':xt(p),'final':xt(p,True),'ET_UTF8_sha256':sha(E.tostring(p,encoding='utf-8')),**marks(p)}for j,p in enumerate(paras[:30])]
       for fi,ev in enumerate(fields):
        tables=list(tree.iter(W+'tbl'));rr=tables[ev['table_index0']].findall(W+'tr')[ev['row_index0']]
        (HERE/(k+'_summary_'+str(fi)+'_row.xml')).write_bytes(E.tostring(rr,encoding='utf-8'))
       found['complete_original_paragraphs']=[{'paragraph_index0':j,'literal':xt(p),'final':xt(p,True),'ET_UTF8_sha256':sha(E.tostring(p,encoding='utf-8')),**marks(p)}for j,p in enumerate(paras)]
      details.append(found)
      m['access']=found['access'];m['ownID_present']=own;m['summary_status']=field_status
     except Exception as e:m['access']='OOXML_parse_failed';m['error']=type(e).__name__+': '+str(e)
  except Exception as e:row['archive_error']=type(e).__name__+': '+str(e)
 vals={d['summary']for d in details if d['summary']is not None and d['field_status']=='UNIQUE_EXPLICIT_OWN_CR_FORM_SUMMARY'}
 row['generic_summary_status']='UNIQUE_EXPLICIT_OWN_CR_FORM_SUMMARY'if len(vals)==1 else 'NO_SUPPORTED_UNIQUE_SUMMARY'
 row['source_summary']=next(iter(vals))if len(vals)==1 else None
 row['source_fields']=details if k in prefixids else [{a:b for a,b in d.items()if a not in('native_CFB',)}for d in details]
 row['source_rules']='exact original archive member; original own cover ID; explicit labelled Summary of change row inside CR form with >=2 form labels; no report Abstract/title inheritance; no revision following; no gold or selected-ID filter'
 row['frozen_delta']=[{'node_id':f['node_id'],'old_summaryOfChange':f['summaryOfChange'],'source_summaryOfChange':row['source_summary'],'relation':'source_unavailable'if row['source_summary']is None else'exact_equal'if f['summaryOfChange']==row['source_summary']else'fill_NULL'if f['summaryOfChange']is None else'different_non_NULL'}for f in frozen[k]]
 results.append(row);inventory.append({a:b for a,b in row.items()if a not in('source_fields','frozen_records','frozen_delta')})
 if row['source_summary']is not None:
  # Proposal includes ALL source-positive records, including existing-equal values;
  # derived/direct provenance and unsupported style boundaries remain explicit.
  patch.append({'tdocNumber':k,'source_summaryOfChange':row['source_summary'],'original_type':row['original_type'],'original_final_status':row['original_final_status'],'archive':row.get('archive'),'frozen_delta':row['frozen_delta'],'source_fields':[{'member':d['member'],'access':d['access'],'word_document_XML_sha256':d['word_document_XML_sha256'],'styles_XML_sha256':d['styles_XML_sha256'],'derivative':d['derivative'],'summary_rows':d['summary_rows'],'native_CFB_summary_literal_whitespace_fold_match':d['native_CFB_summary_literal_whitespace_fold_match']}for d in details if d['summary']==row['source_summary']],'proposal_only':True})
 if k in prefixids:prefixdetails.append(row)
 if(i+1)%200==0:print(json.dumps({'processed_original_family':i+1,'total':len(roles)},ensure_ascii=False),flush=True)
jl('all1858_original_family_source_summary_inventory.jsonl',inventory)
jl('all1858_generic_own_summary_field_observations.jsonl',results)
jl('all_source_positive_generic_summary_patch_proposal.jsonl',patch)
save('all17_rank_dependency_original_own_summary_replay.json',sorted(prefixdetails,key=lambda r:r['tdocNumber']))
save('generic_rule_and_scope.json',{'rule_version':'EXPLICIT_OWN_CR_FORM_SUMMARY_V1','original_family_n':1858,'no_selected_IDs_in_extraction_predicate':True,'original_report_abstract_not_summary':True,'revision_alias_or_next_document_not_followed':True,'all_source_values_retained_no_gold_filter':True,'only_prefix_selection_used_to_include_detailed_full_paragraphs_not_source_value_extraction':True,'strikethrough_limit':'All source XML marks and style references retained. Inherited style resolution is not yet a complete proof; CFB direct reader verifies text and deletion properties, not strikethrough. Do not claim every proposed row certified. Original Word-form/XML source is distinct from a legacy-DOC conversion.','no_graph_model_public_or_central_mutations':True})
count=lambda key:dict(collections.Counter(r[key]for r in results))
receipt={'status':'ACTUAL_GENERIC_WHOLE1858_READONLY_OWN_SOURCE_REPLAY_PROPOSAL_ONLY','original_id':'RAN4_P4_CQ4-5','original_family_records':len(results),'exact_ID_bound_frozen_nodes':sum(len(r['frozen_records'])for r in results),'archive_missing':sum(not r['archive_exists']for r in results),'generic_summary_status_counts':count('generic_summary_status'),'all_original_type_status_counts':dict(collections.Counter(r['original_type']+'/'+r['original_final_status']for r in results)),'all_source_positive_records':len(patch),'delta_counts':dict(collections.Counter(d['relation']for r in results for d in r['frozen_delta'])),'prefix17_status_counts':dict(collections.Counter(r['generic_summary_status']for r in prefixdetails)),'prefix17_delta_counts':dict(collections.Counter(d['relation']for r in prefixdetails for d in r['frozen_delta'])),'prefix17_records':[{'tdocNumber':r['tdocNumber'],'type':r['original_type'],'status':r['original_final_status'],'source_summary':r['source_summary'],'frozen_delta':r['frozen_delta'],'archive_exists':r['archive_exists']}for r in sorted(prefixdetails,key=lambda r:r['tdocNumber'])],'sourcepins':[pin(PRIOR/'all1858_CR_family_source_Decision_boundaries.jsonl'),pin(AUTH/'all17_prefix_own_span_decision_and_corrections_fresh.json'),pin(modulepath),pin(pathlib.Path(__file__))],'SQLite':pin(db),'outputs':[pin(HERE/n)for n in['all1858_original_family_source_summary_inventory.jsonl','all1858_generic_own_summary_field_observations.jsonl','all_source_positive_generic_summary_patch_proposal.jsonl','all17_rank_dependency_original_own_summary_replay.json','generic_rule_and_scope.json']],'admission':False,'native_DB_calls':0,'API_calls':0,'new_DOC_conversions':0,'central_changes':0,'public_changes':0}
save('actual_generic_whole1858_source_replay_receipt.json',receipt)
print(json.dumps({k:v for k,v in receipt.items()if k in('status','original_family_records','archive_missing','all_source_positive_records','delta_counts','prefix17_status_counts','prefix17_delta_counts')},ensure_ascii=False),flush=True)

