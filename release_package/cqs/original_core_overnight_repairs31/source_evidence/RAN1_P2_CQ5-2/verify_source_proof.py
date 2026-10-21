"""Offline finite-source and typed-eligibility supplement; not verify_release."""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Run without Python optimization')
import argparse
import collections
import copy
import gzip
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import stat
from xml.etree import ElementTree as ET

CONSTANTS = {'inventory_sha256': 'b2b283f4fdbdcb5d5121332860d5572ea141b47081840107e8b63606358cd207', 'payload_files': 83, 'repair_sha256': 'c6e02cf9d0ca21ec4888bc24cf13f8d96645947d9704fff966e05c352c2c49ec', 'native': {'saved_output': 'native/ROOT_saved_full_three_column_records.jsonl', 'receipt': 'native/ROOT_actual_native_receipt.json', 'reference_metadata': 'native/lineage/reference_metadata.json', 'input': 'native/lineage/input.jsonl', 'outer_guard_receipt': 'native/lineage/outer_guard_receipt.json', 'coordinator_receipt': 'native/lineage/coordinator_receipt.json', 'outer_guard_code': 'native/lineage/outer_guard_code.py', 'capture_wrapper_code': 'native/lineage/capture_wrapper_code.py', 'coordinator_code': 'native/lineage/coordinator_code.py', 'execution_protocol': 'native/lineage/execution_protocol.json', 'resource_checks': 'native/lineage/resource_checks.jsonl', 'fresh_Windows_observations': 'native/lineage/fresh_Windows_observations.jsonl', 'archival_execute_kernel': 'native/lineage/archival_execute_kernel.py', 'capture_runner': 'native/lineage/capture_runner.py', 'fresh_memory_helper': 'native/lineage/fresh_memory_helper.py', 'actual_native_eligibility_bridge': 'native/lineage/actual_native_eligibility_bridge.json'}}


def no_links(p):
    p = Path(os.path.abspath(p))
    for q in (p, *p.parents):
        if stat.S_ISLNK(q.lstat().st_mode):
            raise ValueError('Symlink path is not accepted')
    return p


SELF = no_links(__file__)
HERE = SELF.parent


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(name):
    rel = Path(name)
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('Only package-relative files are accepted')
    p = no_links(HERE / rel)
    if not stat.S_ISREG(p.lstat().st_mode):
        raise ValueError('A regular file is required')
    return p.read_bytes()


def load(name):
    return json.loads(read(name))


def strict(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def rows_gz(name):
    data = gzip.decompress(read(name)).decode()
    return [json.loads(line) for line in data.splitlines() if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frozen-sqlite', type=Path)
    args = ap.parse_args()
    expected_meta = {'format': 'HARQ-local-source-and-eligibility-supplement', 'status': 'LOCAL_PROPOSAL_NOT_PUBLIC_ADMISSION', 'id': 'RAN1_P2_CQ5-2', 'repair_sha256': CONSTANTS['repair_sha256'], 'original560_pass_increment': 0, 'human_expert_n': 0, 'nonblind_AI': True, 'API_calls': 0, 'native_executed_by_package': False, 'source_eligible_is_native_gold': False, 'immutable_inventory_sha256': CONSTANTS['inventory_sha256'], 'payload_files': CONSTANTS['payload_files'], 'verifier_sha256': sha(SELF.read_bytes()), 'native': CONSTANTS['native']}
    if strict(load('manifest.json')) != strict(expected_meta):
        raise ValueError('Manifest metadata, type, or verifier bytes differ')
    invbytes = read('immutable_inventory.json')
    if sha(invbytes) != CONSTANTS['inventory_sha256']:
        raise ValueError('Immutable inventory differs')
    inventory = json.loads(invbytes)
    if set(inventory) != {'format', 'files'} or inventory['format'] != 'closed-file-inventory':
        raise ValueError('Inventory shape differs')
    entries = inventory['files']
    if type(entries) is not list or len(entries) != CONSTANTS['payload_files']:
        raise ValueError('Inventory count differs')
    allowed = {'manifest.json', 'immutable_inventory.json', 'verify_source_proof.py'}
    for item in entries:
        if set(item) != {'path', 'bytes', 'sha256'} or type(item['bytes']) is not int or item['bytes'] < 0:
            raise ValueError('Inventory entry shape differs')
        name = item['path']
        if type(name) is not str or name in allowed:
            raise ValueError('Duplicate/invalid inventory entry')
        b = read(name)
        if len(b) != item['bytes'] or sha(b) != item['sha256']:
            raise ValueError('Payload bytes differ: ' + name)
        allowed.add(name)
    actual = set()
    for root, dirs, files in os.walk(HERE, followlinks=False):
        for name in dirs + files:
            p = Path(root) / name
            mode = p.lstat().st_mode
            if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise ValueError('Nonregular/symlink package entry')
            if stat.S_ISREG(mode):
                actual.add(str(p.relative_to(HERE)))
    if actual != allowed:
        raise ValueError('Closed package file set differs')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(HERE / 'canonical'))
    import scorer
    import original_scorer
    import review_schema
    import contract_checks
    task = load('contract/definition.json')
    criteria_b = read('canonical/criteria.json')
    criteria = json.loads(criteria_b)
    if sha(criteria_b) != 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4':
        raise ValueError('Original criteria differ')
    exact = scorer.get_kernel().json_exact
    repair = sha(exact(task).encode())
    if repair != CONSTANTS['repair_sha256']:
        raise ValueError('Exact definition differs')
    original = load('contract/original_benchmark_row.json')
    if task['question_en'] != original['question_en'] or task['original_query'] != original['cypher']:
        raise ValueError('Original question/query not preserved')
    if read('contract/original_query.cypher').decode() != task['original_query'] or read('contract/reference_query.cypher').decode() != task['reference_query']:
        raise ValueError('Query files differ')
    reviews = [load('contract/primary_exact_seven_unit_review.json'), load('contract/secondary_exact_seven_unit_review.json')]
    for review in reviews:
        review_schema.check_pass(review, task['question_en'], criteria['semantic_units'], criteria_sha=sha(criteria_b), identity_key='repair_sha256', identity_sha=repair)
    if reviews[0]['reviewer_identity'] == reviews[1].get('reviewer_identity'):
        raise ValueError('Distinct review identities required')
    full_original = json.loads(gzip.decompress(read('projection/all_original_positive_rows.json.gz')))
    full = json.loads(gzip.decompress(read('projection/all_repaired_positive_rows.json.gz')))
    header = re.compile(r'R1-[0-9]{6,8}\t[^\t]+\t.+')

    def prefix(text):
        lines = text.split('\n')
        end = next((i for i, line in enumerate(lines) if header.fullmatch(line.strip())), len(lines))
        return '\n'.join(lines[:end])

    def both(text):
        return 'HARQ' in text and 'feedback' in text

    predicted = [r for r in full_original if both(prefix(r['content']))]
    counter = lambda rows: collections.Counter(exact(r) for r in rows)
    if len(full_original) != 461 or len(full) != 421 or counter(predicted) != counter(full):
        raise ValueError('Generic retained-predicate projection differs')
    eligible = load('contract/separate_source_and_SQL_eligible15_NOT_NATIVE_GOLD.json')['records']
    if counter(eligible) != counter([r for r in full if r['meetingNumberInt'] >= 115]):
        raise ValueError('Separate cutoff eligibility projection differs')
    required = [r for r in eligible if r['meetingNumberInt'] > 115]
    tied = [r for r in eligible if r['meetingNumberInt'] == 115]
    if (len(eligible), len(required), len(tied), len({r['resolutionId'] for r in eligible})) != (15, 9, 6, 15):
        raise ValueError('Cutoff dimensions differ')
    # Reopen every included dependency from original XML. The geometry defines
    # bounded candidate spans; it is not a global semantic ownership assertion.
    W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'

    def literal(e):
        return ''.join(x.text or '' for x in e.iter() if x.tag in (W+'t', M+'t'))

    def tabs(e):
        out = []
        for x in e.iter():
            if x.tag in (W+'t', M+'t'):
                out.append(x.text or '')
            elif x.tag == W+'tab':
                out.append('\t')
            elif x.tag in (W+'br', W+'cr'):
                out.append('\n')
        return ''.join(out)

    flags = ('strike', 'dstrike', 'vanish', 'webHidden')

    def on(e):
        return e.get(W+'val', 'true').lower() not in ('0', 'false', 'off', 'no')

    def active(e, hidden=False):
        if e.tag in (W+'del', W+'moveFrom'):
            return ''
        if e.tag in (W+'r', M+'r'):
            rp = e.find(W+'rPr')
            if rp is not None:
                hidden = hidden or any(on(x) for f in flags for x in rp.findall(W+f))
        if hidden:
            return ''
        if e.tag in (W+'t', M+'t'):
            return e.text or ''
        if e.tag == W+'tab':
            return '\t'
        if e.tag in (W+'br', W+'cr'):
            return '\n'
        return ''.join(active(c, hidden) for c in e)

    docs = load('source/original_source_document_pins.json')
    geometry = rows_gz('source/identity_and_source_geometry.jsonl.gz')
    unbound = rows_gz('source/all112_unbound_full_source_windows.jsonl.gz')
    older = json.loads(gzip.decompress(read('source/older1069_bound_geometry.json.gz')))
    prefix_raw = load('source/independent_all16_own_role_and_format.json')['records']
    broad_ids, cut_ids, older_ids, active_ids = [], [], [], []
    count_broad = count_unbound = count_older = extra_direct = nested_positive = prefix_n = 0
    for doc in docs:
        xb = gzip.decompress(read(doc['document_XML']))
        sb = gzip.decompress(read(doc['styles_XML']))
        if sha(xb) != doc['document_XML_sha256'] or sha(sb) != doc['styles_XML_sha256']:
            raise ValueError('Original source XML/styles bytes differ')
        body = list(ET.fromstring(xb).find(W+'body'))
        sty = ET.fromstring(sb)
        meeting = doc['meeting']
        for g in (r for r in geometry if r['meeting'] == meeting):
            lo, hi = g['original_broad_raw_body_child_range']
            text = '\n'.join(literal(e) for e in body[lo:hi])
            if sha(text.encode()) != g['broad_source_literal_sha256']:
                raise ValueError('Original broad geometry/literal differs')
            count_broad += 1
            lr, hr = g['source_record_raw_body_child_range']
            rec = '\n'.join(literal(e) for e in body[lr:hr])
            if sha(rec.encode()) != g['source_record_literal_sha256']:
                raise ValueError('Derived record boundary bytes differ')
            if both(text):
                broad_ids.append(g['resolutionId'])
                if not both(rec):
                    cut_ids.append(g['resolutionId'])
        for g in (r for r in unbound if r['meeting'] == meeting):
            lo, hi = g['raw_body_child_range']
            text = '\n'.join(literal(e) for e in body[lo:hi])
            if text != g['full_source_candidate_window_literal'] or both(text):
                raise ValueError('Unbound candidate changed or is an extra literal entrant')
            count_unbound += 1
        older_meeting = [r for r in older if r['meeting'] == meeting]
        for g in older_meeting:
            lo, hi = g['raw_body_child_range']
            text = '\n'.join(literal(e) for e in body[lo:hi])
            if not literal(body[lo]).strip().lower().startswith('agreement') or sha(text.encode()) != g['literal_sha256']:
                raise ValueError('Older original registry identity/span differs')
            count_older += 1
            if both(text):
                older_ids.append(g['resolutionId'])
        if older_meeting:
            starts = {g['raw_body_child_range'][0] for g in older_meeting}
            for i, e in enumerate(body):
                if e.tag == W+'p' and re.match(r'^\s*Agreement\b', literal(e), re.I) and i not in starts:
                    end = len(body)
                    for j in range(i+1, len(body)):
                        b = body[j]
                        styles = [s.get(W+'val', '') for s in b.iter(W+'pStyle')]
                        if re.match(r'^\s*(?:Agreement|Conclusion|Working\s+Assumption)\b', literal(b), re.I) or any(re.match(r'heading[1-9]$', s, re.I) for s in styles):
                            end = j
                            break
                    extra_direct += 1
                    if both('\n'.join(literal(b) for b in body[i:end])):
                        raise ValueError('Unregistered older direct positive entrant')
                elif e.tag == W+'tbl':
                    ps = list(e.iter(W+'p'))
                    for j, p in enumerate(ps):
                        if re.match(r'^\s*Agreement\b', literal(p), re.I) and both('\n'.join(literal(z) for z in ps[j:])):
                            nested_positive += 1
        sm = {x.get(W+'styleId'): x for x in sty.findall(W+'style')}
        for g in (r for r in prefix_raw if r['meetingNumber'] == meeting):
            lo, hi = g['raw_range']
            blocks = body[lo:hi]
            if [sha(ET.tostring(e)) for e in blocks] != [x['XML_sha256'] for x in g['blocks']]:
                raise ValueError('Original possible-prefix block XML differs')
            if '\n'.join(tabs(e) for e in blocks[1:]) != '\n'.join(x['text'] for x in g['blocks'][1:]):
                raise ValueError('Raw source text/tab coordinates differ')
            used = {x.get(W+'styleId') for x in sm.values() if x.get(W+'default') in ('1', 'true', 'on')}
            for e in blocks:
                for tag in ('pStyle', 'rStyle', 'tblStyle'):
                    used.update(x.get(W+'val') for x in e.iter(W+tag))
            closure = set()

            def add(sid):
                if sid in closure:
                    return
                if sid not in sm:
                    raise ValueError('Unresolved source style')
                closure.add(sid)
                b = sm[sid].find(W+'basedOn')
                if b is not None:
                    add(b.get(W+'val'))

            for sid in used:
                add(sid)
            if sorted(closure) != g['applicable_style_closure'] or any(on(x) for sid in closure for f in flags for x in sm[sid].iter(W+f)):
                raise ValueError('Applicable style closure has an unhandled active flag')
            dd = sty.find(W+'docDefaults')
            if dd is not None and any(on(x) for f in flags for x in dd.iter(W+f)):
                raise ValueError('Document default flag needs separate resolution')
            own = prefix('\n'.join(tabs(e) for e in blocks[1:]))
            active_own = prefix('\n'.join(active(e) for e in blocks[1:]))
            if both(own) != g['literal_kept'] or both(active_own) != g['literal_kept']:
                raise ValueError('Own/active source keyword membership differs')
            if g['literal_kept']:
                active_ids.append(g['resolutionId'])
            prefix_n += 1
    if (len(docs), count_broad, count_unbound, count_older, extra_direct, nested_positive, prefix_n) != (13, 3176, 112, 1069, 27, 0, 16):
        raise ValueError('Finite source coverage counts differ')
    if len(broad_ids) != 7 or cut_ids or len(older_ids) != 9 or set(active_ids) != {r['resolutionId'] for r in eligible}:
        raise ValueError('Finite literal/source-prefix membership differs')
    if set(broad_ids + older_ids) != {r['resolutionId'] for r in full_original if r['meetingNumberInt'] >= 115}:
        raise ValueError('Raw possible entrant frontier differs from original retained prefix')
    gold = [{'resolutionId': r['resolutionId']} for r in eligible]
    groups = original_scorer.make_order_groups(task, eligible, gold)
    mandatory = [{'resolutionId': r['resolutionId']} for r in required]
    boundary = [{'resolutionId': r['resolutionId']} for r in tied]
    legal = [mandatory + [x] for x in boundary]
    full_fields = [{'name': 'm.meetingNumber', 'type': 'string', 'nullable': False}, {'name': 'a.resolutionId', 'type': 'string', 'nullable': False}, {'name': 'a.content', 'type': 'string', 'nullable': True}]
    byid = {r['resolutionId']: {'m.meetingNumber': r['meetingNumber'], 'a.resolutionId': r['resolutionId'], 'a.content': r['content']} for r in eligible}

    def score(rows):
        return original_scorer.score(task, gold, rows, diagnostic=True, order_groups=groups)

    def bridge(selected, eligibility):
        if exact(eligibility) != exact(eligible) or type(selected) is not list or len(selected) != 10:
            raise ValueError('Limited10 and eligibility15 must stay separate and exact')
        if any(type(r) is not dict or set(r) != {f['name'] for f in full_fields} for r in selected):
            raise ValueError('Full original projection shape differs')
        if not score([{'resolutionId': r['a.resolutionId']} for r in selected])['exact']:
            raise ValueError('Limited output has an inadmissible identity set')
        expected = [byid[r['a.resolutionId']] for r in selected]
        if collections.Counter(scorer.record_token(r, full_fields) for r in selected) != collections.Counter(scorer.record_token(r, full_fields) for r in expected):
            raise ValueError('Full context value/type differs')
        return True

    control_n = 0

    def sc(rows, want):
        nonlocal control_n
        if score(rows)['exact'] is not want:
            raise ValueError('Typed ID eligibility control failed')
        control_n += 1

    def bc(rows, e, want):
        nonlocal control_n
        try:
            bridge(rows, e)
            yes = True
        except (ValueError, KeyError, TypeError):
            yes = False
        if yes is not want:
            raise ValueError('Full-value bridge control failed')
        control_n += 1

    for rows in legal:
        sc(rows, True)
        sc(list(reversed(rows)), True)
        sc([{**r, 'content': 'incidental'} for r in rows], True)
        selected = [copy.deepcopy(byid[r['resolutionId']]) for r in rows]
        bc(selected, eligible, True)
        for k in range(10):
            sc(rows[:k]+rows[k+1:], False)
            for bad in (None, 'None', False, 115, 115.0, [], {}, ''):
                changed = copy.deepcopy(rows); changed[k]['resolutionId'] = bad
                sc(changed, False)
            changed = copy.deepcopy(rows); changed[k] = {'id': changed[k]['resolutionId']}
            sc(changed, False)
            for other in range(10):
                if other != k:
                    changed = copy.deepcopy(rows); changed[k] = copy.deepcopy(rows[other]); sc(changed, False)
            for field in ('m.meetingNumber', 'a.content'):
                changed = copy.deepcopy(selected); changed[k][field] = 'WRONG'; bc(changed, eligible, False)
        sc([], False); sc(rows+[copy.deepcopy(rows[-1])], False)
        for low in sorted({r['resolutionId'] for r in full if r['meetingNumberInt'] < 115}) + ['AGR-122b-8.7.2-011']:
            changed = copy.deepcopy(rows); changed[-1] = {'resolutionId': low}; sc(changed, False)
        for alt in boundary:
            if alt not in rows:
                for k in range(9):
                    changed = copy.deepcopy(rows); changed[k] = copy.deepcopy(alt); sc(changed, False)
        changed = copy.deepcopy(eligible); changed[0]['content'] = 'WRONG'; bc(selected, changed, False)
        changed = copy.deepcopy(eligible); changed[-1]['meetingNumberInt'] = 114; bc(selected, changed, False)
        bc(selected, eligible[:-1], False)
        changed = copy.deepcopy(selected); changed[0].pop('a.content'); bc(changed, eligible, False)
    generic = contract_checks.checks(task, gold, order_groups=groups)
    if len(generic) != 9 or not all(x['pass'] for x in generic) or control_n != 3984:
        raise ValueError('Canonical/supplement control inventory differs')
    sql_limited = load('contract/actual_immutable_SQL_limited10_NOT_NATIVE.json')['all_original_columns']
    bridge(sql_limited, eligible)
    failure = None
    try:
        original_scorer.make_order_groups(task, full, [{'resolutionId': r['resolutionId']} for r in full])
    except ValueError as exc:
        failure = str(exc)
    if failure != 'captured native rows violate requested ordering':
        raise ValueError('Saved projection order failure not reproduced')
    sorted_failure = None
    ordered_full = sorted(full, key=lambda r: -r['meetingNumberInt'])
    try:
        original_scorer.make_order_groups(task, ordered_full, [{'resolutionId': r['resolutionId']} for r in ordered_full])
    except ValueError as exc:
        sorted_failure = str(exc)
    if sorted_failure != 'top-k population contains duplicate requested records':
        raise ValueError('Original-order full-pool duplicate rejection not reproduced')
    native_checked = False
    if CONSTANTS['native'] is not None:
        n = CONSTANTS['native']
        rawbytes = read(n['saved_output'])
        raw = [json.loads(x) for x in rawbytes.decode().splitlines() if x.strip()]
        native_input_bytes = read(n['input'])
        if native_input_bytes != read('contract/native_input_development_probe.jsonl'):
            raise ValueError('Actual native input differs from reviewed exact input')
        inputs = [json.loads(x) for x in native_input_bytes.decode().splitlines() if x.strip()]
        if len(inputs) != 1 or inputs[0]['id'] != task['id'] or inputs[0]['wg'] != 'RAN1' or inputs[0]['status'] != 'development_probe' or inputs[0]['candidate_query'] != task['reference_query']:
            raise ValueError('Exact native input identity or status differs')
        query_sha = sha(task['reference_query'].encode())
        reference = load(n['reference_metadata'])
        required_reference = {'id': task['id'], 'wg': 'RAN1', 'query_sha256': query_sha, 'query': task['reference_query'], 'status': 'OK', 'columns': ['m.meetingNumber', 'a.resolutionId', 'a.content'], 'truncated': False, 'rollback_completed': True, 'plan_query_type': 'r', 'execution_query_type': 'r', 'execution_summary_complete': True, 'rows_retained': 10, 'bytes_retained': len(rawbytes), 'rows_sha256': sha(rawbytes), 'full_rows_available': True}
        for key, value in required_reference.items():
            if strict(reference.get(key)) != strict(value):
                raise ValueError('Saved read-only native metadata differs: ' + key)
        if len(raw) != 10:
            raise ValueError('Actual native cardinality differs')
        execution = load(n['receipt'])
        expected_item = {'id': task['id'], 'status': 'OK', 'query_sha256': query_sha, 'rows': 10}
        if strict(execution.get('items')) != strict([expected_item]) or execution.get('input_sha256') != sha(native_input_bytes):
            raise ValueError('Actual execution does not bind exact input and rows')
        if strict(execution.get('inventory_unchanged')) != 'true' or strict(execution.get('source_before')) != strict(execution.get('source_after')):
            raise ValueError('Frozen source before/after evidence differs')
        src = execution['source_before']
        if src['wg'] != 'RAN1' or type(src['nodes']) is not int or src['nodes'] != 165418 or type(src['relationships']) is not int or src['relationships'] != 848228 or src['source']['sha256'] != '9540683df5407bb3f8978ad4d05ddc7f7880f10c94f21273f588d737f145e231':
            raise ValueError('Actual native frozen source identity differs')
        if execution['runner_sha256'] != sha(read(n['archival_execute_kernel'])) or execution['protocol_sha256'] != sha(read(n['execution_protocol'])):
            raise ValueError('Actual native runner/protocol differs')
        if strict(execution.get('model_calls')) != '0' or strict(execution.get('expert_validation')) != 'false':
            raise ValueError('Native execution provenance differs')
        guard = load(n['outer_guard_receipt'])
        for key, value in {'status': 'PASS', 'stage': 'execute_RAN1', 'child_started': True, 'child_exit': 0, 'failure': None, 'prestart_available_minimum_bytes': 26*1024**3, 'continuous_reserve_minimum_bytes': 16*1024**3, 'Linux_check_seconds': 2, 'Windows_check_seconds': 10, 'quality_rerolls': 0}.items():
            if strict(guard.get(key)) != strict(value):
                raise ValueError('Actual outer guard field differs: ' + key)
        if guard['scope_sha256'] != sha(read('contract/definition.json')) or guard['wrapper_sha256'] != sha(read(n['outer_guard_code'])):
            raise ValueError('Outer guard identity differs')
        if guard['owned_cleanup']['owned_stopped'] is not True or guard['owned_cleanup']['common_lock_held'] is not True or guard['owned_cleanup']['container'] != 'kdd-db-frozen-v1-ran1':
            raise ValueError('Owned cleanup proof differs')
        for key in ('Linux_available_bytes', 'Windows_available_bytes'):
            if type(guard['initial_memory'][key]) is not int or guard['initial_memory'][key] < 26*1024**3:
                raise ValueError('Initial dual-host reserve was not demonstrated')
        if not guard['memory_samples']:
            raise ValueError('Continuous host observations missing')
        for sample in guard['memory_samples']:
            if min(sample['Linux_available_bytes'], sample['Windows_available_bytes']) < 16*1024**3:
                raise ValueError('Recorded dual-host reserve was violated')
        coordinator = load(n['coordinator_receipt'])
        if coordinator['status'] != 'NATIVE_WRAPPER_PASS_PENDING_SCIENTIFIC_BINDING' or strict(coordinator['child_exit']) != '0' or coordinator['guard_sha256'] != guard['wrapper_sha256'] or strict(coordinator['paid_API_calls']) != '0' or strict(coordinator['public_mutations']) != '0':
            raise ValueError('Native coordinator provenance differs')
        resource = [json.loads(x) for x in read(n['resource_checks']).decode().splitlines() if x.strip()]
        if not resource or any(min(x['linux_available_bytes'], x['windows_available_bytes']) < 26*1024**3 for x in resource):
            raise ValueError('Capture-bound fresh reserve proof differs')
        observations = [json.loads(x) for x in read(n['fresh_Windows_observations']).decode().splitlines() if x.strip()]
        if not observations or any(x['status'] != 'FRESH_NUMERIC_OBSERVATION' or x['cached_values_used'] != 0 or x['Get_CimInstance_calls_for_this_request'] != 1 for x in observations):
            raise ValueError('Fresh Windows observation provenance differs')
        selected = [dict(zip([f['name'] for f in full_fields], r)) if type(r) is list and len(r) == 3 else r for r in raw]
        bridge(selected, eligible)
        historical_bridge = load(n['actual_native_eligibility_bridge'])
        if historical_bridge['status'] != 'PASS' or historical_bridge['attached_ROOT_native']['output']['sha256'] != sha(rawbytes) or historical_bridge['attached_ROOT_native']['input']['sha256'] != sha(native_input_bytes) or historical_bridge['controls_passed'] != 3984:
            raise ValueError('Historical native eligibility bridge binding differs')
        native_checked = True
    full_SQL_replayed = False
    if args.frozen_sqlite is not None:
        import sqlite3
        p = no_links(args.frozen_sqlite)
        h = hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda: f.read(1048576), b''):
                h.update(block)
        if h.hexdigest() != 'aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af':
            raise ValueError('Explicit original frozen SQL file differs')
        c = sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1', uri=True)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA query_only=ON')
        actual_full = [dict(r) for r in c.execute(read('replay/independent_SQL.sql').decode())]
        c.close()
        if counter(actual_full) != counter(full):
            raise ValueError('Actual whole immutable SQL differs from included projection')
        full_SQL_replayed = True
    print(json.dumps({'status': 'PASS', 'id': task['id'], 'repair_sha256': repair, 'semantic_AI_reviews': 2, 'human_expert_n': 0, 'source_documents': 13, 'latest_broad_windows_replayed': count_broad, 'latest_unbound_windows_replayed': count_unbound, 'older_bound_windows_replayed': count_older, 'older_unregistered_direct_candidates_replayed': extra_direct, 'possible_frozen_prefix': 16, 'source_eligible15_NOT_native_gold': 15, 'mandatory': 9, 'boundary_choose1_of6': 6, 'generic_controls': len(generic), 'supplement_controls': control_n, 'saved_uncapped_projection_order_failure_preserved': failure, 'correctly_ordered_uncapped_duplicate_rejection_preserved': sorted_failure, 'saved_ROOT_native_full10_checked': native_checked, 'explicit_full_frozen_SQL_replayed': full_SQL_replayed, 'API_calls': 0, 'native_executions': 0, 'new_public_admissions': 0, 'original560_pass_increment': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
