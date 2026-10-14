import pathlib,importlib.util,hashlib,json,collections,contextlib,io,re
lp=pathlib.Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/pipeline/load_released_kg.py');spec=importlib.util.spec_from_file_location('released_loader',lp);L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)
out={}
for wg in ['RAN1','RAN2']:
 p=pathlib.Path('/home/sihyeon/workspace/spectra/release_package/kg/per_wg')/(wg+'-body.ttl')
 sh=hashlib.sha256(p.read_bytes()).hexdigest();print(wg,'READ',sh,flush=True)
 with contextlib.redirect_stdout(io.StringIO()):nodes,rels,stats=L.parse_ttl(p)
 adj=collections.defaultdict(lambda:collections.defaultdict(set))
 for s,t,d in rels:adj[s][t].add(d)
 def prop(k,n):return nodes[k]['props'].get(n)
 def label(k,n):return n in nodes[k]['labels']
 companies={k:prop(k,'companyName') for k in nodes if label(k,'Company')}
 d={'graph_source_sha256':sh,'source_path':str(p),'scanner_path':'/tmp/ran12_source_semantics.py','loader_sha256':hashlib.sha256(lp.read_bytes()).hexdigest(),'nodes':len(nodes),'relationships':len(rels),'company_name_variants':{s:sorted(c for c in companies.values() if isinstance(c,str) and s.lower() in c.lower()) for s in ['Samsung','Qualcomm','Huawei','Nokia','Ericsson']}}
 tid='R1-2501234' if wg=='RAN1' else 'R2-2509337';tk=[k for k in nodes if prop(k,'tdocNumber')==tid];d['anchor_doc']={'tdocNumber':tid,'matches':len(tk),'company_names':sorted({companies.get(c) for k in tk for c in adj[k]['SUBMITTED_BY']}),'agenda_items':sorted({prop(a,'agendaNumber') for k in tk for a in adj[k]['BELONGS_TO']}),'meeting_numbers':sorted({prop(a,'meetingNumber') for k in tk for a in adj[k]['PRESENTED_AT']})}
 mn='RAN1#120' if wg=='RAN1' else 'RAN2#132';mk=[k for k in nodes if label(k,'Meeting') and mn in [prop(k,'meetingNumber'),prop(k,'canonicalMeetingNumber')]]
 if not mk and wg=='RAN2':mk=[k for k in nodes if label(k,'Meeting') and prop(k,'meetingNumber')=='132']
 ms=set(mk);docs=[k for k in nodes if label(k,'Tdoc') and ms & adj[k]['PRESENTED_AT']];incoming=[k for k in docs if prop(k,'type')=='LS in'] if wg=='RAN1' else [k for k in docs if label(k,'LS') and prop(k,'direction')=='in'];d['incoming_liaison_meeting']={'meeting':mn,'matching_source_meeting_properties':[nodes[k]['props'] for k in mk],'all_presented_tdocs':len(docs),'incoming_tdocs':len(incoming),'incoming_missing_agenda':sorted(str(prop(k,'tdocNumber')) for k in incoming if not adj[k]['BELONGS_TO']),'incoming_agenda_pairs':len({(prop(k,'tdocNumber'),prop(a,'agendaNumber')) for k in incoming for a in adj[k]['BELONGS_TO']}),'incoming_labels':sorted({l for k in incoming for l in nodes[k]['labels']})}
 if wg=='RAN1':
  sec=[k for k in nodes if label(k,'Section') and isinstance(prop(k,'sectionTitle'),str) and 'pdsch' in prop(k,'sectionTitle').lower()];d['PDSCH_title']={'all_literal_case_insensitive_matches':len(sec),'newlines':sum('\n' in prop(k,'sectionTitle') for k in sec),'regex_fullmatch_missing_ids':[prop(k,'sectionId') for k in sec if not re.fullmatch('.*PDSCH.*',prop(k,'sectionTitle'),re.I)],'missing_spec_membership_ids':[prop(k,'sectionId') for k in sec if not adj[k]['BELONGS_TO_SPEC']]}
  tr=[k for k in nodes if label(k,'TechnicalReport')];nums=collections.Counter(prop(k,'trNumber') for k in tr);rc=collections.Counter();src=collections.defaultdict(set)
  for k in tr:
   for q in adj[k]['REFERENCES_TR']:
    if label(q,'TechnicalReport'):rc[prop(q,'trNumber')]+=1;src[prop(q,'trNumber')].add(prop(k,'trNumber'))
  d['TR_references']={'TR_nodes':len(tr),'duplicate_TR_number_groups':{str(k):v for k,v in nums.items() if v>1},'edge_vs_distinct_source_number_mismatches':{str(k):{'edge_count':v,'distinct_source_numbers':len(src[k])} for k,v in rc.items() if v!=len(src[k])},'complete_incoming_reference_counts':dict(rc),'rank5_boundary':sorted(rc.items(),key=lambda x:(-x[1],x[0]))[4:7]}
 d['scanner_sha256']=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest();out[wg]=d;print(wg,json.dumps(d,ensure_ascii=False),flush=True);del nodes,rels,adj
pathlib.Path('/tmp/ran12_source_semantics.json').write_text(json.dumps(out,ensure_ascii=False))
