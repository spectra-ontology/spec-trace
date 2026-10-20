"""Offline bounded own-record membership diagnostic, not corrected gold."""
import sys
if sys.flags.optimize:
    raise SystemExit('Use Python without -O/-OO')
import gzip
import hashlib
import io
import json
from pathlib import Path
import stat
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
FIXED_PAYLOAD_SHA256 = '49e798213d187df44200a3d76ffb16b66c660338d6d24051c218fc54fc8d61db'
sha = lambda x: hashlib.sha256(x).hexdigest()
def need(ok, why):
    if not ok:
        raise RuntimeError(why)
def read(name):
    p = ROOT / name
    need(not p.is_symlink() and p.is_file(), 'Missing regular file: '+name)
    return p.read_bytes()
def load(name):
    return json.loads(read(name))
def main():
    inv = load('inventory.json')
    actual = set()
    for p in ROOT.rglob('*'):
        need(not p.is_symlink(), 'Package symlink')
        need(p.is_file() or p.is_dir(), 'Nonregular entry')
        if p.is_file():
            actual.add(p.relative_to(ROOT).as_posix())
    need(actual == set(inv['files']) | {'inventory.json'}, 'Closed file set')
    for name, p in inv['files'].items():
        raw = read(name)
        need(len(raw) == p['bytes'] and sha(raw) == p['sha256'], 'Inventory pin: '+name)
    payload = read('fixed_payload_inventory.json')
    need(sha(payload) == FIXED_PAYLOAD_SHA256, 'Fixed scientific payload inventory')
    for name, p in json.loads(payload)['files'].items():
        raw = read(name)
        need(len(raw) == p['bytes'] and sha(raw) == p['sha256'], 'Fixed payload pin: '+name)
    original = load('contract/original_question_and_query.json')
    query = original['original_Cypher']
    need(sha(query.encode()) == '6f4c725979918aa3faeeb35c4561ff57b958ac0f9018f25acf2991c4595693d8', 'Original query')
    need(sha(original['question_en'].encode()) == 'b9622ccfd0b50c7b1397629c397b5a661b48424667801782579dba089649801e', 'Original English')
    criteria = load('contract/criteria.json')
    need(sha(read('contract/criteria.json')) == 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'Fixed criteria')
    for n in ['primary.json', 'secondary.json']:
        review = load('contract/'+n)
        need(review['id'] == original['id'], 'Reviewer identity')
        need([x['semantic_unit'] for x in review['semantic_units']] == criteria['semantic_units'], 'Original seven units')
    with zipfile.ZipFile(io.BytesIO(read('source/original_report_123.docx'))) as z:
        xb, sb = z.read('word/document.xml'), z.read('word/styles.xml')
    source = load('source/direct_original_source_and_format.json')
    need(sha(xb) == source['document_XML_sha256'] and sha(sb) == source['styles_XML_sha256'], 'Actual source XML')
    W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    body = list(ET.fromstring(xb).find(W+'body'))
    text = lambda e: ''.join(x.text or '' for x in e.iter(W+'t'))
    geometry = [json.loads(x) for x in gzip.decompress(read('source/geometry.jsonl.gz')).splitlines()]
    latest = [x for x in geometry if x['meeting'] == 'RAN1#123']
    need(len(geometry) == 3176 and len(latest) == 286, 'Retained source population')
    source_records = {}
    for g in latest:
        lo, hi = g['source_record_raw_body_child_range']
        need(0 <= lo < hi < len(body) and text(body[lo]).startswith('Agreement'), 'Source geometry')
        source_records[g['resolutionId']] = '\n'.join(text(e) for e in body[lo:hi])
    candidates = sorted(r for r,t in source_records.items() if 'MIMO' in t and 'codebook' in t)
    expected = load('source/actual_source_and_frozen_reopen_receipt.json')
    need(candidates == expected['source_literal_candidates'] and len(candidates)==6, 'Broad prefix bound')
    rid = 'AGR-123-9.3-009'
    need(candidates.index(rid)+1==4 and 'NR_MIMO_Ph5' in text(body[1666]) and 'codebook' in text(body[1666]), 'Necessary active own member')
    need(source['range']==[1665,1668] and not source['style_flags'] and not source['default_flags'] and all(not p['flags'] for p in source['keyword_paragraphs']), 'Inspected active keyword formatting')
    need(text(body[1665]).startswith('Agreement: Adopt') and text(body[1668]).startswith('Agreement: Adopt'), 'Own table boundary')
    f = json.loads(gzip.decompress(read('frozen/retained_projection.json.gz')))
    agreements = {x['node_id']:x for x in f['Agreement']}
    meetings = {x['node_id']:x for x in f['Meeting']}
    need(len(agreements)==3176, 'Frozen retained population')
    paths = [(agreements[e['src_id']],meetings[e['dst_id']]) for e in f['MADE_AT']]
    need(len(paths)==3176 and max(m['meetingNumberInt'] for a,m in paths)==123, 'Recorded path population')
    need({a['resolutionId'] for a,m in paths if m['meetingNumberInt']==123}==set(source_records), 'Latest source/frozen identity equality')
    result = [{'meetingNumber':m['meetingNumber'],'resolutionId':a['resolutionId'],'content':a['content']} for a,m in sorted(paths,key=lambda x:(-x[1]['meetingNumberInt'],x[0]['resolutionId'])) if a['content'] and 'MIMO' in a['content'] and 'codebook' in a['content']][:10]
    need(result==load('frozen/actual_original_SQL_three_column_projection.json')['records'], 'Original SQL10 replay')
    provenance=load('frozen/projection_provenance.json')
    need(provenance['excluded_max_meetingNumberInt']==116 and provenance['whole_original_Agreement_n']==21058, 'Older excluded prefix bound')
    selected={x['resolutionId'] for x in result}
    need(len(result)==10 and rid not in selected, 'Necessary source member omitted')
    need(min(m['meetingNumberInt'] for a,m in paths if a['resolutionId'] in selected)>116, 'Excluded older records cannot enter prefix')
    alt=load('frozen/whole_frozen_decoded_values_and_all_association_challenge.json')
    own=next(x for x in agreements.values() if x['resolutionId']==rid)
    need(own==alt['typed_Agreement'] and own['contentWithEquations'] is None and own['note'] is None, 'Alternate own fields')
    need({e['rel_type'] for e in alt['all_incident_edges']}=={'MADE_AT','RESOLUTION_BELONGS_TO'} and len(alt['all_incident_edges'])==2, 'Saved exhaustive own-role census')
    need(alt['all_node_records_scanned']==165418 and len(alt['ID_aliases'])==1, 'Saved full-frozen scan scope')
    need(not alt['needles']['Extended Rel-18 eType-II Doppler codebook for 128 Tx ports'] and len(alt['needles']['Group-specific 3-bit scaling factors'])==1, 'Preserved missing and positive alternate evidence')
    print(json.dumps({'status':'PASS','id':original['id'],'bounded_recommendation':'unsupported_frozen_data','necessary_member':rid,'latest_retained_source_n':286,'broad_candidates_n':6,'witness_rank':4,'original_SQL_rows':10,'full_frozen_global_scan_reexecuted_here':False,'full_scan_is_pinned_saved_actual_evidence':True,'corrected_gold_claimed':False,'API_calls':0,'public_admissions':0}))
if __name__ == '__main__':
    main()
