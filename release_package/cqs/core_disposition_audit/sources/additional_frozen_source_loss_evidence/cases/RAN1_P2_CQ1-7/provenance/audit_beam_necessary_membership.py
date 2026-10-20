"""Read-only bounded source-membership test; no gold, native, or API generation."""
import sys
if sys.flags.optimize:
    raise SystemExit('Assertions must remain enabled')
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import sqlite3
import zipfile
import xml.etree.ElementTree as ET

resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
ap = argparse.ArgumentParser()
ap.add_argument('--repo', type=Path, required=True)
ap.add_argument('--cqs', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
args = ap.parse_args()
R, C, D = args.repo.resolve(), args.cqs.resolve(), args.out.resolve()
D.mkdir(parents=True, exist_ok=False)
sha = lambda b: hashlib.sha256(b).hexdigest()
def pin(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024**2), b''):
            h.update(b)
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': h.hexdigest()}
def save(n, x):
    p = D / n
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n')
    return pin(p)
qid, rid = 'RAN1_P2_CQ1-7', 'AGR-123-9.3-010'
base = C / 'original_core_repair'
row = next(json.loads(l) for l in (base / 'provenance/original_benchmark.jsonl').read_text().splitlines() if json.loads(l)['id'] == qid)
assert sha(row['question_en'].encode()) == 'b6725b079b8eae22ff1566df69a8b7ce1269027f04d84e23582c657aeafcb3a7'
assert sha(row['cypher'].encode()) == '763a87501c5baf430405f1ac7b266ae4a42e6bd61df60ef0c0e0dd7bdd34abb8'
criteria = pin(base / 'criteria.json')
assert criteria['sha256'] == 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
original = save('original_question_and_query.json', {'id': qid, 'question_en': row['question_en'], 'question_sha256': sha(row['question_en'].encode()), 'original_Cypher': row['cypher'], 'query_sha256': sha(row['cypher'].encode()), 'criteria': criteria, 'legacy_gold_used_for_choice': False, 'nonblind_original_row_read': True})
raw = C / 'original_core_source_RAN1_common3176/raw_extraction'
spec = next(x for x in json.loads((raw / 'manifest.json').read_text())['source_documents'] if x['meeting'] == 'RAN1#123')
archive = R / spec['original_archive']['path']
assert pin(archive)['sha256'] == spec['original_archive']['sha256']
with zipfile.ZipFile(archive) as z:
    zi = z.getinfo(spec['original_archive']['member'])
    doc = z.read(zi)
assert sha(doc) == spec['original_DOCX_sha256']
with zipfile.ZipFile(io.BytesIO(doc)) as z:
    xb, sb = z.read('word/document.xml'), z.read('word/styles.xml')
assert sha(xb) == spec['document_XML_sha256'] and sha(sb) == spec['styles_XML_sha256']
for n, b in [('document.xml.gz', xb), ('styles.xml.gz', sb)]:
    (D / n).write_bytes(gzip.compress(b, mtime=0))
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
body = list(ET.fromstring(xb).find(W + 'body'))
styles = ET.fromstring(sb)
text = lambda el: ''.join(x.text or '' for x in el.iter(W + 't'))
with gzip.open(raw / 'identity_and_source_geometry.jsonl.gz', 'rt') as f:
    latest = [x for x in map(json.loads, f) if x['meeting'] == 'RAN1#123']
assert len(latest) == 286
frontier = []
for x in latest:
    lo, hi = x['source_record_raw_body_child_range']
    t = '\n'.join(text(e) for e in body[lo:hi])
    assert text(body[lo]).startswith('Agreement')
    frontier.append({'resolutionId': x['resolutionId'], 'range': [lo, hi], 'own_literal_sha256': sha(t.encode()), 'beam': 'beam' in t, 'management_or_indication': ('management' in t or 'indication' in t)})
candidates = sorted(x['resolutionId'] for x in frontier if x['beam'] and x['management_or_indication'])
assert rid in candidates and len(candidates) == 5
save('all286_latest_source_geometry_and_keyword_frontier.json', frontier)
# All literal heading candidates, including nested and historical labels, are a
# conservative marker superset. Next STRICTLY later child avoids omitting the
# whole table containing multiple nested headings. This is not a topic oracle.
markers = []
for i, el in enumerate(body):
    for j, p in enumerate([el] if el.tag == W+'p' else list(el.iter(W+'p'))):
        if re.match(r'^Agreement\b', text(p).strip(), re.I):
            markers.append({'raw_body_child0': i, 'paragraph_within_child0': j, 'heading': text(p)})
assert len(markers) == 293
for m in markers:
    lo = m['raw_body_child0']
    hi = next((n['raw_body_child0'] for n in markers if n['raw_body_child0'] > lo), len(body))
    t = '\n'.join(text(e) for e in body[lo:hi])
    m.update({'conservative_range': [lo, hi], 'beam': 'beam' in t, 'management_or_indication': ('management' in t or 'indication' in t)})
assert sum(m['beam'] and m['management_or_indication'] for m in markers) == 7
save('all293_literal_heading_candidate_upper_bound.json', markers)
g = next(x for x in frontier if x['resolutionId'] == rid)
lo, hi = g['range']
assert [lo, hi] == [1668, 1671]
assert text(body[lo]).startswith('Agreement: Adopt the following changes highlighted in chromatic fonts')
assert body[lo+1].tag == W+'tbl' and text(body[hi]).startswith('Agreement')
own = ET.Element('original_own_window', {'start': str(lo), 'end_exclusive': str(hi)})
for e in body[lo:hi]:
    own.append(e)
(D/'original_own_Agreement_window.xml').write_bytes(ET.tostring(own, encoding='utf-8', xml_declaration=True))
stmap = {e.get(W+'styleId'): e for e in styles.findall(W+'style')}
ids = {k for k,e in stmap.items() if e.get(W+'default') in ('1','true','on')}
for e in body[lo:hi]:
    for tag in ['pStyle','rStyle','tblStyle']:
        ids.update(x.get(W+'val') for x in e.iter(W+tag))
closure = set()
def add_style(k):
    if k in closure: return
    assert k in stmap
    closure.add(k)
    b = stmap[k].find(W+'basedOn')
    if b is not None: add_style(b.get(W+'val'))
for k in ids: add_style(k)
on = lambda e:e.get(W+'val','true').lower() not in ('0','false','off','no')
flags = ['strike','dstrike','vanish','webHidden']
style_flags = [{'style':k,'flag':f} for k in sorted(closure) for f in flags for e in stmap[k].iter(W+f) if on(e)]
default_flags = [f for f in flags for e in styles.find(W+'docDefaults').iter(W+f) if on(e)]
keyword_cells = []
for ri, tr in enumerate(body[lo+1].findall(W+'tr')):
    for ci, tc in enumerate(tr.findall(W+'tc')):
        if 'beam' in text(tc) or 'management' in text(tc) or 'indication' in text(tc):
            paras = []
            for p in tc.iter(W+'p'):
                if 'beam' in text(p) or 'management' in text(p) or 'indication' in text(p):
                    paras.append({'text':text(p),'XML':ET.tostring(p,encoding='unicode'),'direct_flags':[f for f in flags+['del','moveFrom'] for e in p.iter(W+f) if f in ('del','moveFrom') or on(e)],'yellow_highlight':any(e.get(W+'val')=='yellow' for e in p.iter(W+'highlight'))})
            keyword_cells.append({'row0':ri,'cell0':ci,'text':text(tc),'paragraphs':paras})
assert not style_flags and not default_flags
assert any('beam' in c['text'] and all(not p['direct_flags'] and not p['yellow_highlight'] for p in c['paragraphs']) for c in keyword_cells)
assert any(('management' in c['text'] or 'indication' in c['text']) and all(not p['direct_flags'] and not p['yellow_highlight'] for p in c['paragraphs']) for c in keyword_cells)
source = save('direct_original_source_and_format.json', {'archive':pin(archive),'member':zi.filename,'CRC32':f'{zi.CRC:08x}','DOCX_sha256':sha(doc),'document_XML_sha256':sha(xb),'styles_XML_sha256':sha(sb),'range':[lo,hi],'next_boundary':text(body[hi]),'heading':text(body[lo]),'keyword_cells':keyword_cells,'style_closure':sorted(closure),'style_flags':style_flags,'default_flags':default_flags,'formatting_claim':'At least one active own cell for each exact literal, not full adopted-table or general Word-rendering certification. The raw adopted table and any retained formatting remain inspectable; this is not a clean technical rewrite.'})
dp = R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN1.sqlite'
before = pin(dp)
assert before['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
c=sqlite3.connect(dp.as_uri()+'?mode=ro&immutable=1',uri=True)
c.row_factory=sqlite3.Row
c.execute('PRAGMA query_only=ON')
meet=[dict(x) for x in c.execute('SELECT a.node_id,a.resolutionId,m.meetingNumber,m.meetingNumberInt FROM Agreement a JOIN edge e ON e.src_id=a.node_id AND e.rel_type="MADE_AT" JOIN Meeting m ON m.node_id=e.dst_id')]
assert max(x['meetingNumberInt'] for x in meet)==123
assert {x['resolutionId'] for x in meet if x['meetingNumberInt']==123}=={x['resolutionId'] for x in frontier}
save('all_original_Agreement_MADE_AT_identity_frontier.json',meet)
sql='SELECT a.resolutionId,m.meetingNumber,a.content FROM Agreement a JOIN edge e ON e.src_id=a.node_id AND e.rel_type="MADE_AT" JOIN Meeting m ON m.node_id=e.dst_id WHERE instr(a.content,"beam")>0 AND (instr(a.content,"management")>0 OR instr(a.content,"indication")>0) ORDER BY m.meetingNumberInt DESC,a.resolutionId LIMIT 10'
frozen10=[dict(x) for x in c.execute(sql)]
assert len(frozen10)==10 and rid not in {x['resolutionId'] for x in frozen10}
sqlpin=save('actual_original_SQL_three_column_projection.json',{'SQL':sql,'records':frozen10,'native_execution_claimed':False})
a=dict(c.execute('SELECT * FROM Agreement WHERE resolutionId=?',(rid,)).fetchone());wid=a['node_id']
assert isinstance(wid,int) and a['contentWithEquations'] is None and a['note'] is None
edges=[dict(x) for x in c.execute('SELECT * FROM edge WHERE src_id=? OR dst_id=? ORDER BY edge_id',(wid,wid))]
assert len(edges)==2 and {x['rel_type'] for x in edges}=={'MADE_AT','RESOLUTION_BELONGS_TO'}
norm=lambda s:re.sub('[^a-z0-9]','',s.lower())
needles=['UE-initiated/event-driven beam management for Event-2 based measurement and report for Mode A','Support of UE-initiated/event-driven beam report based on one event instance','Support of current beam measurement by using QCL RS in the indicated TCI state and the corresponding QCL SSB for Scheme-1 and Scheme-2, respectively']
hits={n:[] for n in needles}
def values(v,k=''):
    if isinstance(v,dict):
        for a,b in v.items():yield from values(b,k+'/'+a)
    elif isinstance(v,list):
        for i,b in enumerate(v):yield from values(b,k+'/'+str(i))
    elif isinstance(v,str):yield k,v
n,scalars,aliases=0,0,[]
for r in c.execute('SELECT * FROM _node_record ORDER BY node_id'):
    r=dict(r);p=json.loads(r['properties_json']);vs=list(values(p));n+=1;scalars+=len(vs)
    if norm(rid) in norm(r['source_iri']) or any(norm(rid) in norm(v) for _,v in vs): aliases.append(r)
    for needle in needles:
        matching=[{'path':k,'value':v} for k,v in vs if norm(needle) in norm(v)]
        if matching:hits[needle].append({'node_id':r['node_id'],'source_iri':r['source_iri'],'labels':json.loads(r['labels_json']),'properties':p,'matches':matching})
assert n==165418 and len(aliases)==1 and aliases[0]['node_id']==wid
neighbors=sorted({x[k] for x in edges for k in ['src_id','dst_id']}-{wid})
alt=save('whole_frozen_decoded_values_and_all_association_challenge.json',{'all_node_records_scanned':n,'decoded_string_scalars_scanned':scalars,'needles':hits,'ID_aliases':aliases,'typed_Agreement':a,'generic_properties':[dict(x) for x in c.execute('SELECT * FROM node_property WHERE node_id=? ORDER BY key',(wid,))],'all_incident_edges':edges,'neighbor_records':[dict(c.execute('SELECT * FROM _node_record WHERE node_id=?',(i,)).fetchone()) for i in neighbors],'claim_boundary':'Historical/other-node vocabulary hits are preserved, not silently removed. They do not supply this Agreement own-table association without an actual path or property.'})
c.close()
assert pin(dp)==before
receipt={'status':'BOUNDED_ACTUAL_SOURCE_AND_FROZEN_TESTS_COMPLETED_NOT_FINAL_ADJUDICATION','id':qid,'utc':datetime.now(timezone.utc).isoformat(),'original':original,'source':source,'latest_source_frontier':pin(D/'all286_latest_source_geometry_and_keyword_frontier.json'),'literal_heading_upper_bound':pin(D/'all293_literal_heading_candidate_upper_bound.json'),'source_literal_candidates':candidates,'witness_rank_among_latest_existing_IDs':candidates.index(rid)+1,'all_latest_literal_marker_positive_upper_bound':7,'source_population':286,'frontier_limit':'Original fixed literal marker/retained identity universe, not arbitrary implicit decisions or a whole technical-topic truth set. Older meetings cannot outrank this latest positive; no full corrected 10-record gold is claimed.','original_SQL':sqlpin,'frozen_alternatives':alt,'DB_before_after':before,'API_calls':0,'native_calls':0,'DB_mutations':0,'public_mutations':0,'original560_increment':0,'nonblind_AI':True,'expert_validation_n':0}
save('actual_source_and_frozen_reopen_receipt.json',receipt)
print(json.dumps({'status':receipt['status'],'candidates':candidates,'witness_rank':receipt['witness_rank_among_latest_existing_IDs'],'fragment_hit_counts':{k:len(v) for k,v in hits.items()}},ensure_ascii=False))
