"""Offline original-source diagnostic. No models, DB, host fallback or admission."""
import sys
if sys.flags.optimize != 0:
    raise SystemExit('Run without -O/-OO; assertions are required')
import gzip
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).absolute().parent
for p in [ROOT, *ROOT.parents, Path(__file__).absolute()]:
    if p.is_symlink():
        raise SystemExit('Symlink entry/ancestor refused')
IMMUTABLE_SHA = 'bff815260482efdd6eeb29354d3404c639bbe9312eeed7145b1d24ae9265a356'
EXPECTED_ID = 'RAN1_P2_CQ5-9'
def sha(b): return hashlib.sha256(b).hexdigest()
def exact(a,b): return type(a) is type(b) and json.dumps(a,sort_keys=True,separators=(',',':'))==json.dumps(b,sort_keys=True,separators=(',',':'))
actual=set()
for p in ROOT.rglob('*'):
    if p.is_symlink(): raise SystemExit('Tree symlink refused')
    if p.is_file(): actual.add(p.relative_to(ROOT).as_posix())
    elif not p.is_dir(): raise SystemExit('Nonregular entry refused')
inventory_bytes=(ROOT/'immutable_inventory.json').read_bytes()
assert sha(inventory_bytes)==IMMUTABLE_SHA
inventory=json.loads(inventory_bytes)
assert set(inventory)=={'files'}
assert actual==set(inventory['files'])|{'README.md','reproduce.py','manifest.json','immutable_inventory.json'}
for n,v in inventory['files'].items():
    assert n==Path(n).as_posix() and not Path(n).is_absolute() and '..' not in Path(n).parts
    b=(ROOT/n).read_bytes()
    assert exact(v,{'bytes':len(b),'sha256':sha(b)})
manifest=json.loads((ROOT/'manifest.json').read_bytes())
assert set(manifest)=={'artifact_type','id','classification','subtype','new_admissions','original560_increment','model_evaluation_completed','files'}
assert exact(manifest['artifact_type'],'bounded_source_classification_evidence')
assert exact(manifest['id'],EXPECTED_ID)
assert exact(manifest['classification'],'unsupported_frozen_data')
assert exact(manifest['subtype'],'own_source_span_loss')
assert exact(manifest['new_admissions'],0) and exact(manifest['original560_increment'],0)
assert exact(manifest['model_evaluation_completed'],False)
assert set(manifest['files'])==actual-{'manifest.json'}
for n,v in manifest['files'].items():
    b=(ROOT/n).read_bytes()
    assert exact(v,{'bytes':len(b),'sha256':sha(b)})
def load(n): return json.loads((ROOT/n).read_bytes())
q=load('contract/original_question_and_query.json')
assert q['id']==EXPECTED_ID and q['question_en']=='List the agreements on slot aggregation.'
assert sha(q['question_en'].encode())==q['question_sha256']=='7b8fc483bc5b4b867ebd099a84e6bf565e48342f44609c480f74c851791f8b84'
assert sha(q['original_Cypher'].encode())==q['query_sha256']=='409f7242a20e30c402db08ffcdfc493618a5c9911b2f932282bb78807d706a5c'
assert sha((ROOT/'contract/criteria.json').read_bytes())==q['criteria']['sha256']=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
criteria=load('contract/criteria.json')
primary=load('contract/primary_seven_unit_review.json')
assert primary['recommendation']=='unsupported_frozen_data' and primary['id']==EXPECTED_ID
assert [x['semantic_unit'] for x in primary['semantic_units']]==criteria['semantic_units']
secondary=load('contract/ROOT_secondary_review.json')
assert secondary['id']==EXPECTED_ID
assert secondary.get('decision',secondary.get('recommendation'))=='unsupported_frozen_data'
assert [x['semantic_unit'] for x in secondary['semantic_units']]==criteria['semantic_units']
assert secondary['criteria']['sha256']==q['criteria']['sha256']
minimum=load('contract/minimum_necessary_membership_contract.json')
assert minimum['canonical_9_key_repair_binding'] is None
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
xb=gzip.decompress((ROOT/'source/document.xml.gz').read_bytes())
sb=gzip.decompress((ROOT/'source/styles.xml.gz').read_bytes())
source=load('source/direct_original_source_and_format.json')
assert sha(xb)==source['document_XML_sha256']=='361ad487a69a1980d91690d792ccaeaa819063572be9d58cafc94fd005bc3ed2'
assert sha(sb)==source['styles_XML_sha256']=='9d607daff9d87d6392163e27ddfdc8f6a9449e9098813533bf999afeb9f78121'
body=list(ET.fromstring(xb).find(W+'body'))
text=lambda e:''.join(x.text or '' for x in e.iter(W+'t'))
frontier=load('source/all286_latest_source_geometry_and_keyword_frontier.json')
assert len(frontier)==286 and len({x['resolutionId'] for x in frontier})==286
for x in frontier:
    lo,hi=x['range'];t='\n'.join(text(e) for e in body[lo:hi])
    assert text(body[lo]).startswith('Agreement')
    assert sha(t.encode())==x['own_literal_sha256']
    assert exact(x['slot'],'slot' in t) and exact(x['aggregation'],'aggregation' in t)
positives=sorted(x['resolutionId'] for x in frontier if x['slot'] and x['aggregation'])
assert positives==['AGR-123-8.8-001','AGR-123-8.8-002','AGR-123-9.3-004']
markers=[]
for i,e in enumerate(body):
    for j,p in enumerate([e] if e.tag==W+'p' else list(e.iter(W+'p'))):
        if re.match(r'^Agreement\b',text(p).strip(),re.I):
            markers.append({'raw_body_child0':i,'paragraph_within_child0':j,'heading':text(p)})
assert len(markers)==293
for m in markers:
    lo=m['raw_body_child0'];hi=next((n['raw_body_child0'] for n in markers if n['raw_body_child0']>lo),len(body))
    t='\n'.join(text(e) for e in body[lo:hi])
    m.update({'conservative_range':[lo,hi],'slot':'slot' in t,'aggregation':'aggregation' in t})
assert markers==load('source/all293_literal_heading_candidate_upper_bound.json')
assert sum(m['slot'] and m['aggregation'] for m in markers)==3
lo,hi=source['range']
assert [lo,hi]==[1650,1653] and body[1651].tag==W+'tbl'
assert text(body[lo])==source['heading'] and text(body[hi])==source['next_boundary']
own=ET.Element('original_own_window',{'start':str(lo),'end_exclusive':str(hi)})
for e in body[lo:hi]:own.append(e)
assert ET.tostring(own,encoding='utf-8',xml_declaration=True)==(ROOT/'source/original_own_Agreement_window.xml').read_bytes()
styles=ET.fromstring(sb)
stmap={e.get(W+'styleId'):e for e in styles.findall(W+'style')}
ids={k for k,e in stmap.items() if e.get(W+'default') in ('1','true','on')}
for e in body[lo:hi]:
    for tag in ['pStyle','rStyle','tblStyle']:ids.update(x.get(W+'val') for x in e.iter(W+tag))
closure=set()
def visit(k):
    if k in closure:return
    assert k in stmap;closure.add(k)
    b=stmap[k].find(W+'basedOn')
    if b is not None:visit(b.get(W+'val'))
for k in ids:visit(k)
assert sorted(closure)==source['style_closure']
on=lambda e:e.get(W+'val','true').lower() not in ('0','false','off','no')
flags=['strike','dstrike','vanish','webHidden']
for el in [styles.find(W+'docDefaults'),*[stmap[k] for k in closure]]:
    assert not [e for f in flags for e in el.iter(W+f) if on(e)]
    assert not [e for e in el.iter(W+'highlight') if e.get(W+'val')=='yellow']
active=set()
for c in source['keyword_cells']:
    tc=body[1651].findall(W+'tr')[c['row0']].findall(W+'tc')[c['cell0']]
    assert text(tc)==c['text']
    pp=[p for p in tc.iter(W+'p') if 'slot' in text(p) or 'aggregation' in text(p)]
    assert len(pp)==len(c['paragraphs'])
    for p,saved in zip(pp,c['paragraphs']):
        assert text(p)==saved['text'] and ET.tostring(p,encoding='unicode')==saved['XML']
        actual_flags=[f for f in flags+['del','moveFrom'] for e in p.iter(W+f) if f in ('del','moveFrom') or on(e)]
        yellow=any(e.get(W+'val')=='yellow' for e in p.iter(W+'highlight'))
        assert actual_flags==saved['direct_flags'] and exact(yellow,saved['yellow_highlight'])
        if not actual_flags and not yellow:
            active.update(t for t in ['slot','aggregation'] if t in text(p))
assert active=={'slot','aggregation'}
frozen=load('frozen/whole_frozen_decoded_values_and_all_association_challenge.json')
assert frozen['all_node_records_scanned']==165418
assert len(frozen['ID_aliases'])==1 and frozen['typed_Agreement']['node_id']==13705
assert frozen['typed_Agreement']['resolutionId']=='AGR-123-9.3-004'
assert frozen['typed_Agreement']['content']==source['heading'].split('Agreement: ',1)[1]
assert frozen['typed_Agreement']['note'] is None and frozen['typed_Agreement']['contentWithEquations'] is None
assert len(frozen['all_incident_edges'])==2 and {e['rel_type'] for e in frozen['all_incident_edges']}=={'MADE_AT','RESOLUTION_BELONGS_TO'}
hits=frozen['needles'];assert [len(v) for v in hits.values()]==[1,0,0]
hist=next(iter(hits.values()))[0]
assert hist['node_id']==6280 and hist['properties']['resolutionId']=='AGR-110-9.18-005'
sql10=load('frozen/actual_original_SQL_three_column_projection.json')
assert len(sql10['records'])==10 and 'AGR-123-9.3-004' not in {r['resolutionId'] for r in sql10['records']}
summary=load('frozen/MADE_AT_full_projection_summary.json')
assert summary['max_meetingNumberInt']==123
assert set(summary['latest123_IDs'])=={x['resolutionId'] for x in frontier}
assert summary['full_projection_rows']==21288
provenance=load('provenance/actual_source_and_frozen_reopen_receipt.json')
assert provenance['DB_before_after']['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
assert all(exact(provenance[k],0) for k in ['API_calls','native_calls','DB_mutations'])
print(json.dumps({'status':'PASS','cases':[{'id':EXPECTED_ID,'classification':'unsupported_frozen_data','subtype':'own_source_span_loss','necessary_source_ID':'AGR-123-9.3-004','latest_existing_identity_rank':3,'conservative_latest_marker_positives':3}],'new_admissions':0,'native_executions':0,'API_calls':0,'scope':'Raw included source/prefix and saved original frozen projection/provenance replay. Whole165418 scan, DB immutability and archive extraction are pinned actual local receipts, not freshly rerun by this offline script.'},ensure_ascii=False))
