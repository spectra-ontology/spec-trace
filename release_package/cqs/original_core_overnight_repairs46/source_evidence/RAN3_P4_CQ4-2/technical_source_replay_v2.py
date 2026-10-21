"""Replay original report-object bindings and selected CR metadata cover fields."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
H = lambda data: hashlib.sha256(data).hexdigest()
norm = lambda value: re.sub(r'\s+', ' ', value or '').strip()

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def replay():
    sys.path.insert(0, str(HERE))
    import original_ooxml_reader_v2 as ooxml
    import source_replay_v1 as cover
    import technical_approval_rule_v4 as rule
    manifest = json.loads((HERE / 'technical_source_member_manifest_v2.json').read_bytes())
    frozen = json.loads(gzip.decompress((HERE / 'actual_frozen_full_input_v1.json.gz').read_bytes()))
    source37 = json.loads((HERE / 'actual_prefix142_145paths_37Agreement_original_source_v4.json').read_bytes())
    manual = json.loads((HERE / 'source_37_manual_role_judgements_v2.json').read_bytes())
    report_receipt = json.loads((HERE / 'actual_original_technical_approval_frontier_v4.json').read_bytes())
    cover_receipt = json.loads((HERE / 'actual_provisional_repair_five_original_CR_ten_fields_v2.json').read_bytes())
    reports, fields, opened = {}, [], []
    by_tdoc = {cr['tdocNumber']: cr for cr in frozen['CR']}
    for item in manifest:
        name = item['payload_file']
        if Path(name).name != name:
            raise ValueError('source member filename escapes payload directory')
        raw = (HERE / 'technical_source_members_v2' / name).read_bytes()
        if H(raw) != item['member_sha256'] or len(raw) != item['member_bytes']:
            raise ValueError('original member bytes changed')
        opened.append({'kind': item['kind'], 'member_sha256': H(raw), 'member_bytes': len(raw)})
        if item['kind'] == 'report':
            report = ooxml.open_report_bytes(raw)
            original = next(row for row in report_receipt['sources'] if row['meeting'] == item['meeting'])
            if {key: value for key, value in report.items() if key != 'blocks'} != original['report_metadata']:
                raise ValueError('original report parse metadata differs')
            reports[item['meeting']] = report
        elif item['kind'] == 'CR':
            actual = cover.read_fields(item, raw, by_tdoc[item['tdocNumber']])
            expected = next(row for row in cover_receipt['CR_fields'] if row['tdocNumber'] == item['tdocNumber'])
            if actual != expected:
                raise ValueError('original CR cover fields or active formatting changed')
            fields.append(actual)
        else:
            raise ValueError('unexpected source member role')
    if len(reports) != 10 or len(fields) != 5 or len(manifest) != 15:
        raise ValueError('wrong source manifest cardinality')
    agreements = {a['node_id']: a for a in frozen['Agreement']}
    crs = {c['node_id']: c for c in frozen['CR']}
    all_rows, full_paths = rule.project(frozen)
    cutoff = all_rows[4]['tdocNumber']
    original_prefix = [(u, v) for u, v in frozen['REFERENCES']
                       if u in agreements and v in crs and crs[v]['reasonForChange'] is not None
                       and crs[v]['tdocNumber'] <= cutoff]
    if (len(original_prefix), len({u for u, v in original_prefix}), len({v for u, v in original_prefix})) != (145, 37, 142):
        raise ValueError('source frontier is not the unfiltered original pre-cutoff population')
    if len(source37) != 37 or {row['resolutionId'] for row in source37} != set(manual):
        raise ValueError('manual/source coverage differs')
    bound_objects, path_results = [], []
    for row in source37:
        rid, a = row['resolutionId'], row['full_retained_Agreement']
        if agreements[a['node_id']] != a:
            raise ValueError('frozen source Agreement altered')
        blocks = reports[row['meeting']]['blocks']
        anchor = row['source_anchor_index0']
        if norm(blocks[anchor]['text']) != norm(row['original_firstline']):
            raise ValueError('source first-line binding differs')
        for block in row['source_context_for_independent_scope_adjudication']:
            if blocks[block['index']] != block:
                raise ValueError('source context/active styles/XML binding differs')
        prior = row['source_prior_document_header']
        if prior is not None and blocks[prior['index']] != prior:
            raise ValueError('prior document source object changed')
        stop = min(row['source_next_full_document_header_index0'],
                   row['source_next_document_decision_index0'], row['source_next_Resolution_index0'])
        original_technical = blocks[anchor:stop]
        if original_technical != row['initial_transition_diagnostic_only']:
            raise ValueError('original technical source scope differs')
        if not all(block['text'] == block['active_text'] for block in original_technical):
            raise ValueError('technical approval text is removed, struck or hidden')
        if norm('\n'.join(rule.technical_lines(a['content']))) != norm('\n'.join(block['text'] for block in original_technical)):
            raise ValueError('frozen rule scope differs from the adjudicated original source object')
        linked = sorted((crs[v]['tdocNumber'], v) for u, v in original_prefix if u == a['node_id'])
        if linked != [(cr['tdocNumber'], cr['CR_node_id']) for cr in row['original_pre_cutoff_linked_CR_records']]:
            raise ValueError('unfiltered earlier source-eligible CR path missing')
        for tdoc, node_id in linked:
            wanted = tdoc in manual[rid]['approved_CR_objects']
            actual = bool(rule.approves(a['content'], tdoc))
            if actual != wanted:
                raise ValueError('rule disagrees with the independently frozen source judgement')
            path_results.append({'resolutionId': rid, 'tdocNumber': tdoc,
                                 'frozen_manual_source_adoption': wanted, 'rule_matches_judgement': True})
        bound_objects.append({'resolutionId': rid, 'source_anchor_index0': anchor,
                              'original_technical_body_indices': [block['index'] for block in original_technical],
                              'source_exact_and_active': True, 'original_prefix_path_n': len(linked)})
    if sum(row['frozen_manual_source_adoption'] for row in path_results) != 5:
        raise ValueError('source-backed original ASC5 membership changed')
    if len(path_results) != 145:
        raise ValueError('wrong source-backed path coverage')
    return {'status': 'PASS_ORIGINAL_MEMBERS_TECHNICAL_OBJECT_BINDINGS_AND_COMPLETE_CR_FIELDS',
            'original_source_members': opened, 'report_n': 10, 'CR_n': 5, 'cover_field_n': 10,
            'technical_objects': bound_objects, 'unfiltered_prefix_CR_n': 142, 'unfiltered_prefix_path_n': 145,
            'technical_object_n': 37, 'source_manual_positive_paths': 5, 'source_manual_negative_paths': 140,
            'source_manual_vs_rule': path_results, 'selected5': [cr['tdocNumber'] for cr in all_rows[:5]],
            'manual_role_interpretation': 'Frozen nonblind primary judgements are supplied as semantic evidence; this replay verifies exact original source bindings, active text, full frontier and rule consistency.',
            'later_global_source_classifier_certified': False, 'new_native_API_calls': 0, 'ROOT_seal': False}

if __name__ == '__main__':
    if sys.flags.optimize:
        raise SystemExit('optimized mode is not accepted')
    result = replay()
    path = HERE / 'actual_technical_original_members_source37_fields10_replay_v2.json'
    with path.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'reports': result['report_n'], 'fields': result['cover_field_n'],
                      'objects': result['technical_object_n'], 'paths': result['unfiltered_prefix_path_n'],
                      'receipt_sha256': H(path.read_bytes())}))
