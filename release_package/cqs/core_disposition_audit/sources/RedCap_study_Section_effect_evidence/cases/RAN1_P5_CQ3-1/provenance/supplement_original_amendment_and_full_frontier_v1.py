"""Reopen strongest actual-amendment recovery witnesses and all named-source routes."""
import gzip,hashlib,json,re,sqlite3,sys,zipfile
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET
if sys.flags.optimize:raise SystemExit('Enabled checks required')
L=Path(__file__).resolve().parent;R=next(x for x in L.parents if (x/'CLAUDE.md').is_file())
D=L/'actual_original_and_frozen_v2';O=L/'actual_amendment_frontier_v1'
B=R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit'
DB=B/'authorized_incremental48_OpenRouter_release/evaluation/runtime/relational/RAN1.sqlite'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}';NS={'w':W[1:-1]}
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def save(n,x):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');return pin(p)
def active(x):
 if x.tag in {W+'del',W+'moveFrom'}:return ''
 return (x.text or '') if x.tag==W+'t' else ''.join(active(y) for y in x)
def blocks(xml):
 body=ET.fromstring(xml).find('w:body',NS)
 return [{'body_child':i,'tag':x.tag.removeprefix(W),'text':active(x),'table_rows':[[active(tc) for tc in row.findall('w:tc',NS)] for row in x.findall('w:tr',NS)]} for i,x in enumerate(body)]
def main():
 assert not O.exists();O.mkdir(parents=True)
 original=json.loads((D/'TR38875_all_original_active_body_blocks.json').read_text())
 bs=original['blocks'];windows=[]
 for i,x in enumerate(bs):
  if re.match(r'\d+(?:\.\d+)+\s*Analysis of specification impacts',x['text']):
   end=next((j for j in range(i+1,len(bs)) if re.match(r'\d+(?:\.\d+)*[A-Z]',bs[j]['text'])),min(i+30,len(bs)))
   windows.append({'heading':x,'blocks':bs[i:end]})
 save('TR38875_all_actual_analysis_of_specification_impact_sections.json',{'source':original['archive'],'index_scheme':original['index_scheme'],'sections':windows,'all_explicit_TS_and_clause_blocks':[x for x in bs if re.search(r'\b(?:TS\s*)?38\.\d{3}|RP-201677',x['text'])]})
 srcroot=R/'ontology/input/tsg/RAN/formal/CR/RAN1';allpaths=list(srcroot.rglob('*.docx'))
 keys=['2112935','2112954','2202986','2205674','2401911','2401912'];sources=[]
 for key in keys:
  paths=[p for p in allpaths if key in p.name];assert paths
  seen={}
  for p in paths:
   with zipfile.ZipFile(p) as z:xml=z.read('word/document.xml');styles=z.read('word/styles.xml')
   h=sha(xml);entry=seen.get(h)
   if entry:entry['same_XML_archive_aliases'].append(pin(p));continue
   rel='source/CR'+key+'/'+h[:12]
   for name,b in [('document.xml',xml),('styles.xml',styles)]:
    out=O/rel/(name+'.gz');out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(gzip.compress(b,mtime=0))
   bb=blocks(xml);entry={'key':'CR'+key,'archive':pin(p),'same_XML_archive_aliases':[],'document_xml':{'bytes':len(xml),'sha256':h},'styles_xml':{'bytes':len(styles),'sha256':sha(styles)},'retained_source_directory':rel,'blocks':bb}
   seen[h]=entry;sources.append(entry)
 # Independently reopen actual TS 38.212 to test original 5.5 target; 38.211 counterpart already shared-source verified but reopens own archive too.
 for ts in ['38.211','38.212','38.213','38.214']:
  paths=list((R/'ontology/input/tsg/RAN/formal/TS/RAN1'/ts).glob('*.docx'));assert len(paths)==1
  p=paths[0]
  with zipfile.ZipFile(p) as z:xml=z.read('word/document.xml');styles=z.read('word/styles.xml')
  bb=blocks(xml);rel='source/TS'+ts.replace('.','')
  for name,b in [('document.xml',xml),('styles.xml',styles)]:
   out=O/rel/(name+'.gz');out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(gzip.compress(b,mtime=0))
  sources.append({'key':'TS'+ts.replace('.',''),'archive':pin(p),'document_xml':{'bytes':len(xml),'sha256':sha(xml)},'styles_xml':{'bytes':len(styles),'sha256':sha(styles)},'retained_source_directory':rel,'blocks':bb})
 save('actual_original_amendment_and_TS_active_body_blocks.json',sources)
 before=pin(DB);c=sqlite3.connect(DB.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
 frontier=json.loads((D/'whole_decoded_frozen_TR_and_RedCap_literal_frontier.json').read_text())
 named={x['node_id'] for k in ['named_TR','named_study_item'] for x in frontier['hits'][k]}
 named|={x[0] for x in c.execute("SELECT node_id FROM Spec WHERE specNumber='38.875'")}
 marks=','.join('?' for _ in named);args=tuple(sorted(named))*2
 edges=[dict(x) for x in c.execute('SELECT * FROM edge WHERE src_id IN ('+marks+') OR dst_id IN ('+marks+') ORDER BY edge_id',args)]
 ids=named|{x[k] for x in edges for k in ['src_id','dst_id']}
 rec=[dict(x) for i in sorted(ids) for x in c.execute('SELECT * FROM _node_record WHERE node_id=?',(i,))]
 save('complete_TR_number_study_item_and_RP_literal_frontier_incident_slice.json',{'literal_frontier_source':pin(D/'whole_decoded_frozen_TR_and_RedCap_literal_frontier.json'),'core_node_ids':sorted(named),'records':rec,'edges':edges,'scope':'Every incident edge for all retained 38.875/FS_NR_redcap/RP201677 literal-role nodes, plus Spec identity38.875. Endpoint records retained. No token occurrence is converted into causal attribution.'})
 q='''SELECT tr.trNumber,w.workItemCode,cr.* FROM TechnicalReport tr JOIN rel_RELATED_TO_WORK_ITEM r ON r.src_id=tr.node_id JOIN WorkItem w ON w.node_id=r.dst_id JOIN rel_RELATED_TO a ON a.dst_id=w.node_id JOIN CR cr ON cr.node_id=a.src_id WHERE tr.trNumber='38.875' ORDER BY cr.id'''
 rows=[dict(x) for x in c.execute(q)]
 allr=json.loads((D/'actual_immutable_SQL_diagnostics.json').read_text())['all_RedCap_named_workitem_CR_TS_Section_candidates']['rows']
 own=[r for r in allr if r['workItemCode']=='NR_redcap-Core' and r['id']];crs={r['id']:r for r in own}
 save('all_RedCap_candidate_frozen_CR_role_summary.json',{'direct_study_workitem_typed_CR_query':{'sql':q,'sql_sha256':sha(q.encode()),'rows':rows,'row_count':len(rows)},'all_core_CR_ids':sorted(crs),'CR_count':len(crs),'all_modifies_specs':sorted({r['specNumber'] for r in own if r['specNumber']}),'distinct_section_ids':sorted({r['sectionId'] for r in own if r['sectionId']}),'status_counts':dict(Counter(r['status'] for r in crs.values())),'field_nonempty_n':{k:sum(bool(v[k]) for v in crs.values()) for k in ['clausesAffected','reasonForChange','summaryOfChange']},'all_CR_frozen_fields':[crs[i] for i in sorted(crs)],'current_role_note':'Candidate population includes introduction, maintenance, editorial, mirror, draft, revised, withdrawn and reserved records. Naming and all clauses affected are not a complete adopted original-study attribution.'})
 c.close();after=pin(DB);assert before==after
 save('actual_supplement_receipt.json',{'status':'COMPLETED_ORIGINAL_AMENDMENT_AND_ROLE_FRONTIER_REOPEN','original_amendment_archive_unique_XML_n':sum(s['key'].startswith('CR') for s in sources),'TS_archive_n':sum(s['key'].startswith('TS') for s in sources),'source_archive_alias_observations_n':sum(1+len(s.get('same_XML_archive_aliases',[])) for s in sources),'named_frontier_core_n':len(named),'incident_record_n':len(rec),'incident_edge_n':len(edges),'direct_study_WI_typed_CR_n':len(rows),'source_n':len(sources),'sqlite_before':before,'sqlite_after':after,'API_calls':0,'native_calls':0,'public_mutations':0,'queue_mutations':0})
 print(json.dumps({'source_n':len(sources),'named_frontier_core_n':len(named),'incident_record_n':len(rec),'incident_edge_n':len(edges),'direct_study_WI_typed_CR_n':len(rows)}))
if __name__=='__main__':main()
