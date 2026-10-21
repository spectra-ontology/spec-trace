"""Replay saved BWP own-record and associated-CR evidence; no live services."""
import sys
if sys.flags.optimize:
    raise SystemExit('Run without optimization')
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
from collections import Counter
import xml.etree.ElementTree as ET

ROOT = Path(__file__).absolute().parent
QID = 'RAN1_P2_CQ5-8'
REPAIR = 'cc1ba3d9d67d1716ffdee8bb1e5c2d6353b22be4a13f410f5268dc633068a342'
INVENTORY_SHA = 'edd8b0214d00cd24d8667d5c7e57a340b8ce968e62d8e66a93865f75634a6cb6'
CRITERIA_SHA = 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def canonical(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def forbid_links(p):
    p = p.absolute()
    for part in (p, *p.parents):
        if part.is_symlink():
            raise ValueError('Symlink path is not allowed')
    return p

def read(name):
    p = forbid_links(ROOT / name)
    return p.read_bytes()

def js(name):
    return json.loads(read(name))

def gz(name):
    return json.loads(gzip.decompress(read(name)))

def jl(name):
    return [json.loads(line) for line in read(name).splitlines()]

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    out = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(out)
    return out

def own(text):
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if re.fullmatch(r'R1-[0-9]{7}\t.*', line):
            final_attachment = (i + 1 < len(lines)
                and re.fullmatch(r'\(Rel-[0-9]+,.*\bCR[0-9]+.*\) is agreed\.', lines[i+1].strip())
                and any(re.fullmatch(r'(?i).*(?:final\s+CRs?\s+in|comeback\s+for\s+final\s+CR).*', p)
                        for p in lines[:i]))
            if not final_attachment:
                return '\n'.join(lines[:i])
    return text

def positive(s):
    return 'BWP' in s and 'switch' in s

def same_tp(text, meeting, cr):
    if not cr.get('summaryOfChange'):
        return False
    if meeting + ' agreed on a text proposal' not in (cr.get('reasonForChange') or ''):
        return False
    tokens = [x.split(']', 1)[0].strip() for x in text.split('[')[1:] if ']' in x]
    return any('[' + token + ']' in (cr.get('title') or '') for token in tokens)

def literal(el):
    return ''.join(t.text or '' for t in el.iter() if t.tag in (W+'t', M+'t'))

def plain(el):
    return ''.join(t.text or '' for t in el.iter(W+'t'))

def quote_locator(s):
    # A locator, not a normalization of scored values: preserve punctuation.
    return ''.join(s.split()).casefold()

def main():
    forbid_links(Path(__file__))
    forbid_links(ROOT)
    found = set()
    directories = set()
    for p in ROOT.rglob('*'):
        forbid_links(p)
        mode = p.lstat().st_mode
        rel = p.relative_to(ROOT).as_posix()
        if stat.S_ISREG(mode):
            found.add(rel)
        elif stat.S_ISDIR(mode):
            directories.add(rel)
        else:
            raise ValueError('Nonregular tree entry')
    inventory_bytes = read('immutable_inventory.json')
    assert sha(inventory_bytes) == INVENTORY_SHA
    inventory = json.loads(inventory_bytes)
    assert set(inventory) == {'files'}
    expected = set(inventory['files']) | {'immutable_inventory.json', 'manifest.json', 'reproduce.py'}
    assert found == expected, 'Closed file tree mismatch'
    expected_dirs = {p.parent.as_posix() for n in expected for p in (Path(n), *Path(n).parents)
                     if p.parent.as_posix() != '.'}
    assert directories == expected_dirs, 'Closed directory tree mismatch'
    for name, pinned in inventory['files'].items():
        data = read(name)
        assert canonical(pinned) == canonical({'bytes': len(data), 'sha256': sha(data)}), name
    manifest = js('manifest.json')
    expected_meta = {'artifact_type': 'original_question_preserving_query_repair_evidence',
        'id': QID, 'local_gate_status': 'completed_candidate_awaiting_ROOT_seal',
        'repair_sha256': REPAIR, 'new_admissions': 0, 'original560_increment': 0,
        'model_evaluation_completed': False, 'API_calls': 0}
    assert set(manifest) == set(expected_meta) | {'files'}
    assert canonical({k: v for k, v in manifest.items() if k != 'files'}) == canonical(expected_meta)
    assert set(manifest['files']) == expected - {'manifest.json'}
    for name, pinned in manifest['files'].items():
        data = read(name)
        assert canonical(pinned) == canonical({'bytes': len(data), 'sha256': sha(data)}), name

    original = js('contract/original_question_and_query.json')
    baseline = json.loads(read('contract/original_benchmark_row.json'))
    assert original['id'] == baseline['id'] == QID
    assert sha(read('contract/original_benchmark_row.json')) == original['original_row_sha256']
    assert original['question_en'] == baseline['question_en']
    assert original['original_query'] == baseline['cypher']
    assert sha(original['question_en'].encode()) == original['question_sha256'] == 'fa90e3fc9bf9d6207a5ce712c8fa94f386ac17828b61dadb5dae6be458146bb1'
    assert sha(original['original_query'].encode()) == original['query_sha256'] == '01da1619fc313bbacde6657e9c9ea2189f1c6aa3622ceadcc48ac3745b3d0c0c'
    criteria = js('contract/criteria.json')
    assert sha(read('contract/criteria.json')) == CRITERIA_SHA
    definition = js('contract/definition.json')
    assert len(definition) == 9 and sha(canonical(definition).encode()) == REPAIR
    assert definition['id'] == QID and definition['question_en'] == original['question_en']
    assert definition['original_query'] == original['original_query']
    assert definition['required_fields'] == [{'name':'content','type':'string','nullable':False,'source_column_or_expression':'content'}]
    assert definition['collection'] == {'kind':'multiset'}
    assert definition['cardinality_policy'] == {'mode':'exact','value':10}
    assert definition['repair_class'] == 'query_and_scorer'
    reviews = [js('contract/primary_seven_unit_review.json'), js('contract/independent_secondary_seven_unit_review.json')]
    schema = module('bwp_review_schema', 'contract/review_schema.py')
    for review in reviews:
        assert review['id'] == QID
        schema.check_pass(review, original['question_en'], criteria['semantic_units'],
            criteria_sha=CRITERIA_SHA, identity_key='repair_sha256', identity_sha=REPAIR)
    assert reviews[0]['reviewer'] != reviews[1]['reviewer']
    assert 'main_B' in reviews[1]['reviewer']

    authority = js('contract/authority_and_counterauthority_spans.json')
    # Historical path strings inside receipts are provenance only, never opened.
    for row in authority:
        data = read('contract/' + Path(row['source']['path']).name)
        assert sha(data) == row['source']['sha256'] and len(data) == row['source']['bytes']
        lines = data.decode().splitlines()
        for span in row['spans']:
            lo, hi = span['lines_inclusive']
            assert '\n'.join(lines[lo-1:hi]) == span['text']
    frontier = gz('source/all3176_frontier.json.gz')
    panels = gz('source/eighteen_source_panels.json.gz')
    assert len(frontier) == 3176 and len(panels) == 18
    assert js('source/extra_unbound_literal_positive.json') == []
    upper = {x['resolutionId'] for x in frontier if x['broad_keyword_positive'] and x['meetingNumberInt'] >= 119}
    assert upper == {x['resolutionId'] for x in panels}
    by_id = {}
    for panel in panels:
        lo, hi = panel['direct_own_range']
        broad_lo, broad_hi = panel['broad_range']
        assert broad_lo == lo < hi <= broad_hi
        blocks = panel['blocks']
        assert [x['raw_body_child0'] for x in blocks] == list(range(lo, min(broad_hi, hi + 2)))
        own_xml = []
        for block in blocks:
            xml = ET.fromstring(block['XML'])
            assert plain(xml) == block['plain_text'] and literal(xml) == block['literal_text']
            if block['raw_body_child0'] < hi:
                own_xml.append(xml)
        own_literal = '\n'.join(literal(x) for x in own_xml)
        assert positive(own_literal) is panel['own_positive']
        count = sum(len(list(x.iter(M+'oMath'))) for x in own_xml)
        assert count == panel['OMML_count']
        by_id[panel['resolutionId']] = {'panel': panel, 'plain': '\n'.join(plain(x) for x in own_xml), 'math': count}
    own_ids = {rid for rid, x in by_id.items() if x['panel']['own_positive']}
    assert len(own_ids) == 10

    frozen = gz('frozen/original170_and_recovered160.json.gz')
    original170 = frozen['original_rows']
    recovered = [x for x in original170 if positive(own(x['content']))]
    assert len(original170) == 170 and len(recovered) == 160
    assert [x['node_id'] for x in recovered] == [x['node_id'] for x in frozen['recovered_rows']]
    assert all(own(a['content']) == b['own_content'] for a,b in zip(recovered, frozen['recovered_rows']))
    assert sum(x['meetingNumberInt'] > 119 for x in recovered) == 9
    assert sum(x['meetingNumberInt'] == 119 for x in recovered) == 1
    selected = recovered[:10]
    assert {x['resolutionId'] for x in selected} == own_ids
    assert sum(x['meetingNumberInt'] >= 119 and not positive(own(x['content'])) for x in original170) == 2
    attached = next(x for x in selected if x['resolutionId'] == 'AGR-121-7-022')
    assert all(t in own(attached['content']) for t in ['R1-2504844','R1-2504845'])

    association = js('frozen/matched_CR_projection.json')
    crs = [x for row in association['whole160_associations'] for x in row['matched_CR']]
    assert len(crs) == 1
    cr = crs[0]
    source_cr = js('source/original_CR_cover_and_frozen_summary.json')
    xb = gzip.decompress(read('source/CR_document.xml.gz'))
    sb = gzip.decompress(read('source/CR_styles.xml.gz'))
    assert sha(xb) == source_cr['document_XML_sha256']
    assert sha(sb) == source_cr['styles_XML_sha256']
    doc = ET.fromstring(xb)
    cover = list(doc.find(W+'body'))[source_cr['raw_body_child0']]
    rows = list(cover.findall(W+'tr'))
    roles = {'Title:':'title','Reason for change:':'reasonForChange','Summary of change:':'summaryOfChange'}
    for label, role in roles.items():
        field = source_cr['fields'][label]
        cell = rows[field['row0']].findall(W+'tc')[field['cell0']]
        text = plain(cell)
        assert text == field['text']
        assert quote_locator(text) == quote_locator(cr[role])
        assert quote_locator(cr[role]) == quote_locator(source_cr['frozen_properties'][role])
    independent_cr = js('provenance/independent_original_CR_cover_and_association.json')
    assert cr == independent_cr['frozen_CR']
    assert cr['tdocNumber'] == source_cr['frozen_properties']['tdocNumber']
    assert source_cr['frozen_node'] == 'styles.xml.gz'  # Preserved erroneous metadata is not used as an identity.

    output = []
    actual_matches = []
    for a in recovered:
        body = own(a['contentWithEquations'] if a['contentWithEquations'] is not None else a['content'])
        matches = sorted([c for c in crs if same_tp(own(a['content']), a['meetingNumber'], c)], key=lambda c:c['tdocNumber'])
        text = body + ('' if a['note'] is None or a['note'] == '' else '\n' + a['note'])
        for c in matches:
            text += '\nRecorded associated CR ' + c['tdocNumber'] + ' summary: ' + c['summaryOfChange']
        output.append({'m.meetingNumber': a['meetingNumber'], 'a.resolutionId': a['resolutionId'], 'content': text})
        if matches:
            actual_matches.append((a['resolutionId'], [c['node_id'] for c in matches]))
    assert actual_matches == [(association['whole160_associations'][0]['resolutionId'], [cr['node_id']])]
    full_sql = jl('frozen/SQL_all160_full3columns.jsonl')
    key = lambda row: (row['m.meetingNumber'], row['a.resolutionId'], row['content'])
    assert len(full_sql) == 160 and Counter(map(key, output)) == Counter(map(key, full_sql))
    expected10 = jl('frozen/SQL_selected10_full3columns.jsonl')
    assert Counter(map(key, output[:10])) == Counter(map(key, expected10))
    gold = jl('frozen/requested_content_records.jsonl')
    assert Counter(x['content'] for x in gold) == Counter(x['content'] for x in output[:10])
    mapping = js('source/all10_substantive_mapping.json')
    assert len(mapping['cases']) == 10
    quote_n = 0
    for case in mapping['cases']:
        rid = case['resolutionId']
        assert rid in own_ids and case['source_own_range'] == by_id[rid]['panel']['direct_own_range']
        assert case['source_OMML_count'] == by_id[rid]['math']
        value = next(x['content'] for x in expected10 if x['a.resolutionId'] == rid)
        for check in case['actual_literal_checks']:
            locator = quote_locator(check['quote'])
            assert locator in quote_locator(by_id[rid]['plain']) and locator in quote_locator(value)
            quote_n += 1
    assert quote_n == 48
    assert sum(x['math'] > 0 for rid,x in by_id.items() if rid in own_ids) == 5
    critical = next(x for x in expected10 if cr['summaryOfChange'] in x['content'])
    assert 'maximum of the SRS-CS switching time' in critical['content']
    assert 'a sum of the two switching times' in critical['content']

    native = js('native/reference_output.json')
    native_rows = jl('native/reference_rows.jsonl')
    qhash = sha(definition['reference_query'].encode())
    assert native['id'] == QID and native['wg'] == 'RAN1'
    assert native['query'] == definition['reference_query'] and native['query_sha256'] == qhash
    assert native['status'] == 'OK' and native['truncated'] is False
    assert native['columns'] == ['m.meetingNumber','a.resolutionId','content']
    assert all(native[k] is True for k in ['full_rows_available','rollback_completed','execution_summary_complete'])
    assert native['execution_query_type'] == native['plan_query_type'] == 'r'
    assert type(native['rows_retained']) is int and native['rows_retained'] == 10
    assert sha(read('native/reference_rows.jsonl')) == native['rows_sha256']
    assert all(type(row) is list and len(row) == 3 and all(type(v) is str for v in row) for row in native_rows)
    assert Counter(map(tuple,native_rows)) == Counter(map(key,expected10))
    execution = js('native/execution_RAN1.json')
    inp = jl('native/input.jsonl')
    assert len(inp) == 1 and inp[0]['candidate_query'] == definition['reference_query']
    assert execution['input_sha256'] == sha(read('native/input.jsonl'))
    assert execution['inventory_unchanged'] is True
    assert execution['source_before'] == execution['source_after']
    assert execution['source_before']['source']['sha256'] == '9540683df5407bb3f8978ad4d05ddc7f7880f10c94f21273f588d737f145e231'
    outer = js('native/owned_outer_receipt.json')
    assert outer['status'] == 'PASS' and type(outer['child_exit']) is int and outer['child_exit'] == 0
    assert outer['owned_cleanup']['owned_stopped'] is True
    assert outer['scope_sha256'] == sha(read('contract/definition.json'))
    assert outer['prestart_available_minimum_bytes'] == 26 * 1024**3
    assert outer['continuous_reserve_minimum_bytes'] == 16 * 1024**3

    scorer = module('bwp_typed_scorer', 'scoring/scorer.py')
    assert scorer.score(definition, gold, gold, diagnostic=True)['exact'] is True
    assert scorer.score(definition, gold, list(reversed(gold)), diagnostic=True)['exact'] is True
    for prediction in ([], [{} for _ in gold], [{'content': None} for _ in gold], gold[:-1], gold[:-1]+gold[:1]):
        assert scorer.score(definition, gold, prediction, diagnostic=True)['exact'] is False
    without_summary = [dict(x,content=x['content'].replace('\nRecorded associated CR '+cr['tdocNumber']+' summary: '+cr['summaryOfChange'],'')) for x in gold]
    assert scorer.score(definition, gold, without_summary, diagnostic=True)['exact'] is False
    source_a = next(x for x in recovered if x['resolutionId'] == critical['a.resolutionId'])
    assert same_tp(own(source_a['content']), source_a['meetingNumber'], cr)
    assert not same_tp(own(source_a['content']), 'RAN1#1210', cr)
    assert not same_tp('[OTHER_FEATURE]', source_a['meetingNumber'], cr)
    assert not same_tp(own(source_a['content']), source_a['meetingNumber'], dict(cr,reasonForChange='No attribution'))
    assert not same_tp(own(source_a['content']), source_a['meetingNumber'], dict(cr,summaryOfChange=''))
    print(json.dumps({'status':'PASS','cases':[{'id':QID,'repair_sha256':REPAIR,
        'source_broad_frontier':3176,'source_windows':18,'source_own_selected':10,
        'frozen_original_pool':170,'recovered_pool':160,'native_rows':10,
        'native_full3_columns_exact':True,'same_TP_CR_summary_in_requested_output':True,
        'source_and_output_quote_locators':48,'quote_locator_mode':'Unicode whitespace removal and casefold; punctuation preserved; scored values remain byte-sensitive',
        'new_native_calls':0,'new_API_calls':0}], 'new_admissions':0,
        'scope':'Included raw XML fragments and saved frozen projections/capture replay; no fresh archive/whole-DB/native/model execution'}))

if __name__ == '__main__':
    main()
