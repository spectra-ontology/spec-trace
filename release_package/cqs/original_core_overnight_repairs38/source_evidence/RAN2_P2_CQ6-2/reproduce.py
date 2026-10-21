#!/usr/bin/env python3
"""Fixed-domain rate replay; scientific modules are unchanged."""
import sys
if sys.flags.optimize:
    raise SystemExit('Optimization unsupported')
sys.dont_write_bytecode = True
import argparse
import ast
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
import enum
import gzip
import hashlib
import json
from pathlib import Path
import re
import types
import xml.etree.ElementTree as E

BASE = Path(__file__).absolute().parent
INVENTORY = '2e59e63368e76fe503e14e87cc54717ea7dd6ed827530e1ecfb1b0779c14c560'
REPAIR = '2e686158064dfef7f6e830e55ef1e1c8f342a2b37f402a3165068be957e5ca35'
CRITERIA = 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
QUERY = '5b9b9b05344dd1747ec164ad908670bca166457ac7c8f1ad085846ff9f0b340d'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
S = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


def no_link(path):
    for p in (path, *path.parents):
        if p.is_symlink():
            raise ValueError('symlink path refused')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(rel):
    p = BASE / rel
    no_link(p)
    return p.read_bytes()


def load(rel):
    raw = read(rel)
    if rel.endswith('.gz'):
        raw = gzip.decompress(raw)
    return json.loads(raw, parse_float=Decimal)


def json_exact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def main():
    no_link(Path(__file__).absolute())
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', type=Path)
    args = ap.parse_args()
    inventory_raw = read('immutable_inventory.json')
    assert sha(inventory_raw) == INVENTORY
    inventory = json.loads(inventory_raw)
    expected = set(inventory['files']) | {'immutable_inventory.json', 'manifest.json', 'reproduce.py'}
    actual = set()
    expected_dirs = {str(Path(x).parent) for x in expected}
    expected_dirs |= {str(p) for x in expected for p in Path(x).parents if str(p) != '.'}
    for p in BASE.rglob('*'):
        if p.is_symlink():
            raise ValueError('tree symlink refused')
        relative = str(p.relative_to(BASE))
        if p.is_file():
            actual.add(relative)
        elif p.is_dir():
            if relative not in expected_dirs:
                raise ValueError('unexpected directory')
        else:
            raise ValueError('nonregular tree entry')
    assert actual == expected
    for name, info in inventory['files'].items():
        raw = read(name)
        assert len(raw) == info['bytes'] and sha(raw) == info['sha256'], name
    manifest = load('manifest.json')
    expected_manifest = {'id': 'RAN2_P2_CQ6-2', 'artifact_type': 'local_recorded_documentary_rate_evidence',
        'repair_sha256': REPAIR, 'new_admissions': 0, 'API_calls': 0,
        'inventory_sha256': INVENTORY, 'verifier_sha256': sha(read('reproduce.py'))}
    assert json_exact(manifest) == json_exact(expected_manifest)
    definition = load('contract/definition.json')
    assert len(definition) == 9 and sha(json_exact(definition).encode()) == REPAIR
    assert definition['reference_query'] == definition['original_query']
    assert sha(definition['reference_query'].encode()) == QUERY
    assert sha(read('contract/criteria.json')) == CRITERIA
    sys.path.insert(0, str(BASE / 'scoring'))
    import review_schema
    import original_scorer as scorer
    criteria = load('contract/criteria.json')
    for rel in ['contract/primary.json', 'contract/secondary.json']:
        review_schema.check_pass(load(rel), definition['question_en'], criteria['semantic_units'],
            criteria_sha=CRITERIA, identity_key='repair_sha256', identity_sha=REPAIR)
    assert load('contract/primary.json')['reviewer'] == 'main_A /root/priority71_fast_closure'
    assert load('contract/secondary.json')['reviewer_identity'] == '/root'
    geometry = {x['resolutionId']: x for x in load('source/recorded_geometry.json.gz')}
    records = load('source/fixed_recorded_Resolution_projection.json.gz')
    assert len(geometry) == len(records) == 3773
    assert len({x['node_id'] for x in records}) == 3773
    by_meeting = defaultdict(list)
    for r in records:
        by_meeting[r['resolutionId'].split('-')[1]].append(r)
    inputs = load('source/original_source_pins.json')
    assert len(inputs) == len(by_meeting) == 58
    class DT(enum.Enum):
        AGREEMENT = 'Agreement'
        CONCLUSION = 'Conclusion'
        WORKING_ASSUMPTION = 'WorkingAssumption'
    tree = ast.parse(read('source/original_INDEX_decision_extractor.py.txt').decode())
    tree.body = [x for x in tree.body if not (isinstance(x, ast.ImportFrom) and x.module == 'models')]
    ns = {'DecisionType': DT, 'Decision': lambda **kw: types.SimpleNamespace(**kw), 'Section': object}
    exec(compile(tree, 'included_pinned_INDEX_extractor', 'exec'), ns)
    marker_seen = set()
    source_literal_equal_n = 0
    source_capture_exact_body_n = 0
    for item in inputs:
        meeting = item['meeting']
        doc = gzip.decompress(read('source/raw_loader_XML/' + meeting + '/document.xml.gz'))
        st = gzip.decompress(read('source/raw_loader_XML/' + meeting + '/styles.xml.gz'))
        assert sha(doc) == item['loader_XML']['document_XML_sha256']
        assert sha(st) == item['loader_XML']['styles_XML_sha256']
        styles = {s.get(W + 'styleId'): s.find(W + 'name').get(W + 'val') if s.find(W + 'name') is not None else ''
                  for s in E.fromstring(st).findall(W + 'style')}
        body = E.fromstring(doc).find(W + 'body')
        ps = []
        for p in body:
            if p.tag != W + 'p':
                continue
            style = p.find(W + 'pPr/' + W + 'pStyle')
            sid = style.get(W + 'val') if style is not None else 'Normal'
            text = ''.join(e.text or '' if e.tag == W + 't' else '\t' if e.tag == W + 'tab'
                           else '\n' if e.tag in (W + 'br', W + 'cr') else '' for e in p.iter())
            ps.append(types.SimpleNamespace(text=text, style=types.SimpleNamespace(name=styles.get(sid, sid))))
        # Original parser's XML body retains source table cells. Its report_path
        # loader normally opens DOCX; attach the included parsed body directly.
        ex = ns['DecisionExtractor']([], None)
        ex._body_children = list(body)
        ex._para_to_body = {}
        paragraph_index = 0
        for body_index, child in enumerate(ex._body_children):
            if child.tag == W + 'p':
                ex._para_to_body[paragraph_index] = body_index
                paragraph_index += 1
        candidates = ex._find_candidates(ps)
        candidate_by_marker = {x[1]: (i, x) for i, x in enumerate(candidates)}
        for r in by_meeting[meeting]:
            g = geometry[r['resolutionId']]
            marker = g['marker_paragraph']
            assert (meeting, marker) not in marker_seen
            marker_seen.add((meeting, marker))
            i, candidate = candidate_by_marker[marker]
            dtype, pi, keyword, inline = candidate
            assert dtype.name == g['kind'] and keyword == g['marker_text']
            hi = ex._find_content_boundary(pi, ps, candidates[i + 1][1] if i + 1 < len(candidates) else len(ps))
            content = ex._extract_content(ps, pi + 1, hi)
            if inline:
                content = inline + ('\n' + content if content else '')
            content, note = ex._split_note(content)
            assert sha(content.encode()) == g['source_capture_sha256'], r['resolutionId']
            assert sha(r['content'].encode()) == g['content_sha256']
            literals = sorted(set(re.findall(r'R2-\d{7}', content)))
            assert literals == g['full_source_capture_R2_literals'] == sorted(set(re.findall(r'R2-\d{7}', r['content'])))
            source_literal_equal_n += 1
            source_capture_exact_body_n += g['method'].startswith('exact_')
    assert len(marker_seen) == source_literal_equal_n == 3773 and source_capture_exact_body_n == 3766
    # Original worksheet fragments keep shared-string indices and actual XML;
    # they are explicitly not represented as full included XLSX files.
    formal_numbers = set()
    fragments = load('source/formal_Huawei_original_register_XML_fragments.json.gz')
    def decode(row, shared):
        vals = {}
        for c in row.findall(S + 'c'):
            v = c.find(S + 'v')
            value = v.text if v is not None else ''
            if c.get('t') == 's':
                value = ''.join(e.text or '' for e in E.fromstring(shared[str(int(value))]).iter(S + 't'))
            elif c.get('t') == 'inlineStr':
                value = ''.join(e.text or '' for e in c.iter(S + 't'))
            vals[re.sub(r'\d', '', c.get('r'))] = value or ''
        return vals
    for f in fragments:
        shared = f['shared_string_elements']
        head = {v: k for k, v in decode(E.fromstring(f['header_row_XML']), shared).items()}
        assert 'TDoc' in head and 'Source' in head
        for raw in f['selected_rows_XML']:
            values = decode(E.fromstring(raw), shared)
            if re.search(r'(?<![A-Za-z])Huawei(?![A-Za-z])', values.get(head['Source'], ''), re.I):
                formal_numbers.add(values[head['TDoc']].strip())
    tdocs = load('source/all_Tdoc_number_projection.json.gz')
    tdoc_by_number = defaultdict(set)
    for node, number in tdocs:
        if number:
            tdoc_by_number[number].add(node)
    Huawei_nodes = {a for a, b in load('source/Huawei_SUBMITTED_BY_projection.json')}
    tdoc_numbers = dict(tdocs)
    meetings = {x['node_id']: x for x in load('source/meetings.json')}
    totals, numerators = Counter(), Counter()
    used_Huawei_numbers = set()
    reference_pairs = 0
    for r in records:
        assert len(r['meeting_nodes']) == 1
        mid = r['meeting_nodes'][0]
        assert mid in meetings
        totals[mid] += 1
        expected_refs = set()
        for number in re.findall(r'R2-\d{7}', r['content']):
            expected_refs.update(tdoc_by_number[number])
        assert sorted(expected_refs) == r['REFERENCES']
        reference_pairs += len(expected_refs)
        Huawei_refs = expected_refs & Huawei_nodes
        if Huawei_refs:
            numerators[mid] += 1
            used_Huawei_numbers.update(tdoc_numbers[x] for x in Huawei_refs)
    assert len(totals) == 58 and sum(totals.values()) == 3773
    assert len(numerators) == 52 and sum(numerators.values()) == 742
    assert reference_pairs == 12995
    assert len(used_Huawei_numbers) == 1716 and used_Huawei_numbers <= formal_numbers
    case = load('execution/native_case.json')
    native = [json.loads(x, parse_float=Decimal) for x in read('execution/native_rows.jsonl').decode().splitlines() if x]
    assert case['query_sha256'] == QUERY and case['status'] == 'OK'
    assert case['rows_sha256'] == sha(read('execution/native_rows.jsonl'))
    assert case['truncated'] is False and case['full_rows_available'] is True and case['rollback_completed'] is True
    assert case['plan_query_type'] == case['execution_query_type'] == 'r'
    columns = ['m.canonicalMeetingNumber', 'm.meetingNumberInt', 'huaweiCount', 'total', 'ratio']
    assert case['columns'] == columns and len(native) == case['rows_retained'] == 52
    fields = [{'name': n, 'type': 'string' if i == 0 else 'number' if i == 4 else 'integer', 'nullable': False}
              for i, n in enumerate(columns)]
    named = [dict(zip(columns, x)) for x in native]
    sql = load('execution/SQL_full5.json')
    expected = []
    for mid, n in numerators.items():
        m = meetings[mid]
        ratio = (100 * Decimal(n) / totals[mid]).quantize(Decimal('.1'), rounding=ROUND_HALF_UP)
        expected.append([m['canonicalMeetingNumber'], m['meetingNumberInt'], n, totals[mid], ratio])
    typed = lambda rows: Counter(scorer.typed.record_token(dict(zip(columns, x)), fields) for x in rows)
    assert typed(native) == typed(sql) == typed(expected)
    assert [x[1] for x in native] == sorted(x[1] for x in native)
    requested = [{'canonicalMeetingNumber': x[0], 'ratio': x[4]} for x in native]
    groups = scorer.make_order_groups(definition, named, requested)
    score = scorer.score(definition, requested, requested, diagnostic=True, order_groups=groups)
    assert score['exact'] is True
    prediction = list(requested)
    offset = 0
    for group in groups:
        prediction[offset:offset + len(group)] = reversed(prediction[offset:offset + len(group)])
        offset += len(group)
    assert scorer.score(definition, requested, prediction, diagnostic=True, order_groups=groups)['exact'] is True
    cross = list(requested)
    cross[0], cross[len(groups[0])] = cross[len(groups[0])], cross[0]
    assert scorer.score(definition, requested, cross, diagnostic=True, order_groups=groups)['exact'] is False
    wrong = [dict(x) for x in requested]
    wrong[0]['ratio'] = str(wrong[0]['ratio'])
    assert scorer.score(definition, requested, wrong, diagnostic=True, order_groups=groups)['exact'] is False
    for panel in load('source/two_original_Huawei_citation_panels.json'):
        for t in panel['Huawei_targets']:
            assert re.search(re.escape(t) + r'(?![0-9])', panel['full_original_interval'])
    outer = load('execution/outer_guard.json')
    assert outer['status'] == 'PASS' and outer['child_exit'] == 0 and outer['owned_cleanup']['owned_stopped'] is True
    assert outer['prestart_available_minimum_bytes'] == 26 * 1024 ** 3
    assert outer['continuous_reserve_minimum_bytes'] == 16 * 1024 ** 3
    execution = load('execution/native_execution.json')
    assert execution['source_before'] == execution['source_after'] and execution['inventory_unchanged'] is True
    optional_files = 0
    if args.source_root is not None:
        root = args.source_root.absolute()
        no_link(root)
        pins = [p for x in inputs for p in [x['archive'], x['loader']]]
        pins += [x['archive'] for x in fragments]
        seen = set()
        for entry in pins:
            if entry['path'] in seen:
                continue
            seen.add(entry['path'])
            relative = Path(entry['path'])
            assert not relative.is_absolute() and '..' not in relative.parts
            p = root / relative
            no_link(p)
            assert p.stat().st_size == entry['bytes'] and sha(p.read_bytes()) == entry['sha256']
            optional_files += 1
    print(json.dumps({'status': 'PASS', 'id': 'RAN2_P2_CQ6-2', 'repair_sha256': REPAIR,
          'recorded_source_markers': len(marker_seen), 'source_capture_exact_body_n': source_capture_exact_body_n,
          'source_capture_literal_sets_equal_n': source_literal_equal_n, 'Resolution_REFERENCE_pairs': reference_pairs,
          'Huawei_positive_Resolution_n': 742, 'formal_Huawei_Tdocs_n': len(used_Huawei_numbers),
          'meeting_n': 58, 'native_n': len(native), 'requested_fields': ['canonicalMeetingNumber', 'ratio'],
          'all_full_five_columns_equal': True, 'optional_original_hash_checked_files': optional_files,
          'native_executions': 0, 'API_calls': 0, 'new_admissions': 0}))


if __name__ == '__main__':
    main()
