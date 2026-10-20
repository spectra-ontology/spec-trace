#!/usr/bin/env python3
"""Replay the bounded UL source/projection diagnostic; never certify admission."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
INVENTORY_SHA256 = '48a4de1e83795665d8dc79ccbc0d1b1451d36877a8c61090e9a5df0c8ab1cabf'
ID = 'RAN1_P2_CQ1-2'
DECLARATIONS = {
    'id': ID, 'status': 'LOCAL_TWO_REVIEW_DIAGNOSTIC_NOT_ADMISSION',
    'diagnostic_subtype': 'source_explicit_agreement_amendment_status_unretained',
    'distinct_nonblind_AI_reviews': 2, 'root_seal_required': True,
    'proposed_disposition': 'unsupported_frozen_data',
    'original560_pass_increment': 0, 'human_expert_n': 0,
    'new_model_calls': 0, 'new_native_executions': 0,
    'full_graph_embedded': False, 'same_event_WA_is_adopted': False,
}
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def safe(path):
    path = Path(os.path.abspath(path))
    for p in [path, *path.parents]:
        need(not p.is_symlink(), 'symlink forbidden: ' + str(p))
    return path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def literal(e):
    return ''.join(x.text or '' for x in e.findall('.//w:t', NS))


def rendered(e):
    if e.tag == W + 'tbl':
        return '\n'.join(' | '.join(literal(c).strip() for c in r.findall('w:tc', NS))
                         for r in e.findall('w:tr', NS))
    return literal(e).strip()


def verify():
    need(sys.flags.optimize == 0, 'optimization unsupported')
    entry = safe(__file__)
    root = entry.parent
    manifest_path = safe(root / 'manifest.json')
    inv_path = safe(root / 'immutable_inventory.json')
    need(digest(inv_path.read_bytes()) == INVENTORY_SHA256, 'immutable inventory mismatch')
    manifest, inventory = load(manifest_path), load(inv_path)
    need(set(manifest) == {'declarations', 'verifier_sha256', 'inventory_sha256'}, 'manifest key set')
    need(json.dumps(manifest['declarations'], sort_keys=True) == json.dumps(DECLARATIONS, sort_keys=True),
         'scientific declarations changed')
    need(manifest['inventory_sha256'] == INVENTORY_SHA256, 'manifest inventory mismatch')
    need(manifest['verifier_sha256'] == digest(entry.read_bytes()), 'verifier bytes changed')
    observed = set()
    for path in root.rglob('*'):
        safe(path)
        mode = path.lstat().st_mode
        need(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'nonregular entry')
        if stat.S_ISREG(mode):
            observed.add(path.relative_to(root).as_posix())
    need(observed == set(inventory) | {'manifest.json', 'immutable_inventory.json', entry.name},
         'closed inventory mismatch')
    for rel, pin in inventory.items():
        need(type(pin['bytes']) is int and type(pin['sha256']) is str, 'pin types')
        raw = safe(root / rel).read_bytes()
        need(len(raw) == pin['bytes'] and digest(raw) == pin['sha256'], 'payload mismatch: ' + rel)

    proof = load(root / 'evidence/actual_source_and_frozen_replay.json')
    context = load(root / 'evidence/actual_same_event_case_equivalence_and_generic_context.json')
    final = load(root / 'local_final_review.json')
    need(proof['id'] == context['id'] == final['id'] == ID, 'question identity')
    original = load(root / 'original.json')
    need(original == proof['original'], 'original bytes/value mismatch')
    need(digest(original['question_en'].encode()) == proof['original_question_sha256'], 'question SHA')
    need(digest(original['cypher'].encode()) == proof['original_query_sha256'], 'query SHA')
    need(digest((root / 'canonical/release_package/cqs/original_core_repair/criteria.json').read_bytes())
         == proof['criteria']['sha256'], 'criteria SHA')
    source = safe(root / 'source/Final_Report_RAN1-100-e.docx')
    need(digest(source.read_bytes()) == proof['source']['sha256'], 'original DOCX SHA')
    with zipfile.ZipFile(source) as z:
        raw = z.read('word/document.xml')
        member = z.getinfo('word/document.xml')
        need(digest(z.read('word/styles.xml')) == proof['source_XML']['styles_sha256'], 'styles SHA')
    need(digest(raw) == proof['source_XML']['sha256'] and member.CRC == proof['source_XML']['CRC'],
         'original XML bytes/CRC')
    body = list(ET.fromstring(raw).find('w:body', NS))
    for block in proof['source_scope_raw_blocks']:
        e = body[block['raw_body_child0']]
        need(digest(ET.tostring(e, encoding='utf-8')) == block['xml_sha256'], 'raw block XML mismatch')
        need(rendered(e) == block['rendered_with_table_cells'], 'raw block text mismatch')
    markers = [i for i in range(395, 472) if literal(body[i]).strip() in {'Agreement:', 'Agreements:'}]
    need(markers == [414, 416, 420, 435, 446, 451], 'complete six-group source boundary')
    for row in proof['source_records_not_gold']:
        need(row['literal_marked_transcript'] == '\n'.join(rendered(body[i]) for i in row['content_raw_body_child0']),
             'source group text changed')
    groups = proof['actual_original_SQL_records']
    need(groups == proof['actual_original_SQL_whole_records'] and len(groups) == 6, 'LIMIT10/source population')
    need([r['sequence'] for r in groups] == list(range(1, 7)), 'sequence/count')
    # Reproduce exact original SQL over the included, pinned finite graph projection.
    nodes = {x['node_id']: x for x in proof['agenda_all_resolution_nodes'] + proof['scope_edge_targets']}
    projected = []
    edges = proof['scope_edges']
    for node in proof['agenda_all_resolution_nodes']:
        if 'Agreement' not in json.loads(node['labels_json']):
            continue
        props = json.loads(node['properties_json'])
        own_edges = [e for e in edges if e['src_id'] == node['node_id']]
        agendas = [nodes[e['dst_id']] for e in own_edges if e['rel_type'] == 'RESOLUTION_BELONGS_TO']
        meetings = [nodes[e['dst_id']] for e in own_edges if e['rel_type'] == 'MADE_AT']
        count = sum(json.loads(a['properties_json'])['agendaNumber'] == '5.1' for a in agendas)
        count *= sum(json.loads(m['properties_json'])['meetingNumber'] == 'RAN1#100' for m in meetings)
        projected.extend([{'node_id': node['node_id'], **{k: props.get(k) for k in
            ['resolutionId', 'content', 'contentWithEquations', 'note', 'sequence']}}] * count)
    projected.sort(key=lambda x: x['sequence'])
    need(projected[:10] == groups, 'included graph projection/original SQL mismatch')
    native = load(root / 'native/receipt.json')
    native_raw = (root / 'native/rows.jsonl').read_bytes()
    native_rows = [json.loads(line) for line in native_raw.splitlines()]
    native_run = load(root / 'native/full560_run.json')
    native_freeze_raw = (root / 'native/frozen_manifest.json').read_bytes()
    need(digest(native_raw) == native['execution']['rows_file_sha256'], 'archived full native rows SHA')
    need(native['reference_query_utf8_sha256'] == proof['original_query_sha256'], 'exact actual native query')
    need(native['original_question_utf8_sha256'] == proof['original_question_sha256'], 'native question identity')
    need(native_rows == [[r['resolutionId'], r['content']] for r in groups], 'native all fields vs SQL projection')
    need(native['execution']['full_json_rows_available'] is True and native['execution']['truncated'] is False,
         'native full rows not established')
    need(native['execution']['rollback_completed'] is True and native['execution']['execution_query_type'] == 'r',
         'historical read/rollback proof')
    need(native_run['source_inventory_unchanged'] is True, 'historical source inventory changed')
    need(native_run['frozen_manifest_sha256'] == digest(native_freeze_raw), 'historical freeze chain')
    need(any(x['id'] == ID and x['receipt_sha256'] == digest((root / 'native/receipt.json').read_bytes())
             for x in native_run['items']), 'native receipt run membership')
    wa = next(x for x in proof['agenda_all_resolution_nodes'] if x['node_id'] == 24008)
    need(json.loads(wa['labels_json']) == ['Resolution', 'WorkingAssumption'], 'WA role changed')
    wa_cases = []
    for line in json.loads(wa['properties_json'])['content'].splitlines():
        cells = [s.strip() for s in line.strip().strip('|').split('|')]
        if len(cells) == 3 and re.fullmatch(r'Case \d+', cells[0]):
            match = re.fullmatch(r'(\d+)T\+(\d+)T', cells[1])
            need(match is not None, 'WA case grammar')
            wa_cases.append({'case': cells[0], 'carrier1_Tx_chains': int(match[1]), 'carrier2_Tx_chains': int(match[2])})
    need(wa_cases == context['frozen_WA_case_values'] == context['source_agreement_case_values'], 'case value tuples')
    need(context['adopted_role_not_inferred'] is True, 'adoption claim')
    need(final['recommended_disposition'] == 'unsupported_frozen_data' and final['public_change_supported'] is False,
         'classification proposal changed or claimed public admission')
    need(final['classification_only_original_pass_increment'] == 0 and final['root_seal_required'] is True,
         'root independent seal is still required')
    amendment = load(root / 'evidence/actual_adoption_and_amendment_association.json')
    need(amendment['id'] == ID and amendment['status'] == 'FINITE_ASSOCIATION_AND_AMENDMENT_AUDIT_NOT_ADMISSION', 'amendment identity')
    need(len(amendment['checks']) == 14 and all(v is True for v in amendment['checks'].values()), 'actual discriminator checks')
    need(type(amendment['all_switching_properties_examined_n']) is int and amendment['all_switching_properties_examined_n'] == 3140, 'captured search extent')
    need(amendment['source_XML']['sha256'] == digest(raw), 'amendment original XML pin')
    for b in amendment['source_scope_all_raw_blocks']:
        e = body[b['raw_body_child0']]
        need(digest(ET.tostring(e, encoding='utf-8')) == b['xml_sha256'] and literal(e) == b['text'], 'amendment raw block')
    for rr in amendment['source_run_formatting']:
        run = body[rr['raw_body_child0']].findall('.//w:r', NS)[rr['descendant_run0']]
        need(ET.tostring(run, encoding='unicode') == rr['run_xml'] and literal(run) == rr['text'], 'actual run formatting')
    need(literal(body[419]).strip() == 'Clarify the following agreements with changes in red', 'explicit local amendment instruction')
    struck = []
    for run in body[423].findall('.//w:r', NS):
        strike = run.find('w:rPr/w:strike', NS)
        if strike is not None and strike.get(W+'val', '1') not in {'0','false','off'}:
            struck.append(literal(run))
            color = run.find('w:rPr/w:color', NS)
            need(color is not None and color.get(W+'val') == 'FF0000', 'actual deleted qualifier red')
    need(struck == ['scheduled'], 'necessary local qualifier deletion')
    actual_scoped = {n['node_id']: n for n in amendment['scope_nodes']}
    need(actual_scoped[249] == next(n for n in proof['agenda_all_resolution_nodes'] if n['node_id'] == 249), 'same frozen affected record')
    historic = {n['node_id']: json.loads(n['properties_json']) for n in amendment['affected_and_historical_nodes']}
    need(historic[249]['content'] == historic[20741]['content'], 'actual old/new frozen condition collision')
    need('scheduled' in historic[249]['content'] and 'scheduled' not in historic[484]['content'], 'separate later role')
    affected_edges = [e for e in amendment['scope_all_incident_edges'] if e['src_id'] in {251,24008} or e['dst_id'] in {251,24008}]
    need(len(affected_edges) == 6 and all(e['rel_type'] in {'MADE_AT','RESOLUTION_BELONGS_TO'} for e in affected_edges), 'no adopted-role edge in captured projection')
    need(amendment['original_authority']['sha256'] == digest((root/'authority/design_HEAD.md').read_bytes()), 'original authority provenance')
    secondary = load(root / 'contract/ROOT_secondary_exact_seven_unit_review.json')
    independent = load(root / 'evidence/ROOT_actual_independent_amendment_and_frozen_reopen.json')
    record = load(root / 'two_review_disposition_record.json')
    need(secondary['id'] == record['id'] == ID, 'independent review identity')
    need(secondary['recommendation'] == record['recommended_disposition'] == 'unsupported_frozen_data', 'independent recommendation')
    need(secondary['subtype'] == record['diagnostic_subtype'] == DECLARATIONS['diagnostic_subtype'], 'precise diagnostic subtype')
    need(secondary['original_question_sha256'] == record['original_question_sha256'] == proof['original_question_sha256'], 'independent question SHA')
    need(secondary['original_query_sha256'] == record['original_query_sha256'] == proof['original_query_sha256'], 'independent original query SHA')
    need(secondary['criteria']['sha256'] == record['criteria_sha256'] == proof['criteria']['sha256'], 'independent original criteria')
    need(secondary['reviewer_kind'] != final['reviewer_kind'] and 'ROOT secondary' in secondary['reviewer_kind'], 'distinct AI identities')
    need(len(secondary['semantic_units']) == len(final['seven_unit_review']) == 7, 'both seven-unit reviews')
    need(all(x['assessment'] == 'BOUNDED_NECESSARY_SOURCE_STATUS_FAILURE' for x in secondary['semantic_units']), 'secondary actual assessments')
    need(secondary['primary']['sha256'] == record['primary']['sha256'] == digest((root/'local_final_review.json').read_bytes()), 'secondary primary exact pin')
    need(record['primary']['path'] == 'local_final_review.json' and record['secondary']['path'] == 'contract/ROOT_secondary_exact_seven_unit_review.json', 'review portable paths')
    for key in ['primary','secondary','ROOT_actual_source_reopen']:
        pin = record[key]; payload = safe(root/pin['path']).read_bytes()
        need(type(pin['bytes']) is int and len(payload) == pin['bytes'] and digest(payload) == pin['sha256'], 'two-review identity pin '+key)
    need(secondary['actual_ROOT_reopen']['sha256'] == digest((root/'evidence/ROOT_actual_independent_amendment_and_frozen_reopen.json').read_bytes()), 'secondary independent reopen pin')
    need(independent['status'] == 'PASS_ROOT_INDEPENDENT_RAW_AMENDMENT_AND_FROZEN_REOPEN', 'actual independent reaccess status')
    need(independent['original_XML_sha256'] == digest(raw) and independent['raw_instruction'] == literal(body[419]).strip(), 'independent authentic XML/instruction')
    need(independent['raw_qualification'] == literal(body[423]) and independent['struck_word'] == 'scheduled' and independent['direct_strike_color'] == 'FF0000', 'independent local amendment')
    need(independent['necessary_affected_node'] == 249 and independent['exact_matches_to_saved_proof'] is True and independent['all_switching_property_values_actually_rechecked_n'] == 3140, 'independent finite frozen scope')
    need(independent['no_new_native_or_model_calls'] is True and independent['source_fidelity_only_not_ontology_superiority'] is True, 'independent attribution limits')
    need(record['status'] == 'TWO_REVIEW_SUPPORTED_AWAITING_ROOT_SEAL' and record['root_seal_required'] is True and record['public_change_supported'] is False, 'local seal/public state')
    need(type(record['distinct_nonblind_AI_reviews']) is int and record['distinct_nonblind_AI_reviews'] == 2, 'review count strict type')
    for key in ['human_expert_n','new_model_calls','new_native_executions','new_admissions','original560_pass_increment']:
        need(type(record[key]) is int and record[key] == 0, 'no experiment/admission increment '+key)
    need(record['not_ontology_effectiveness'] is True and record['not_model_comparison'] is True, 'classification scope limits')
    module_path = root / 'replay_original_source_and_frozen.py'
    spec = importlib.util.spec_from_file_location('ul_bounded_replay', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    controls = module.scoring_controls(proof, root / 'canonical')
    need(len(controls['controls']) == 34, 'typed diagnostic controls')
    need(controls['raw_SQL_content_against_source_marked_transcript_not_gold']['matched_records'] == 3,
         'raw content discrepancy changed')
    need(controls['note_plus_editorial_query_repair_diagnostic_not_gold']['matched_records'] == 5,
         'retained note/editorial repair frontier changed')
    return {**DECLARATIONS, 'artifact_status': DECLARATIONS['status'], 'status': 'PASS', 'source_agreement_groups': 6,
            'original_SQL_projection_records': 6, 'typed_diagnostic_controls': 34,
            'reused_exact_original_native_all_field_match': True,
            'same_event_case_value_tuple_equivalence': True,
            'whole_frozen_graph_replayed': False, 'new_admissions': 0,
            'captured_full_SQL_switching_property_search_n': 3140, 'source_amendment_status_reopened': True,
            'limits': 'Included raw source and pinned finite projection replay only; full DB search is an actually captured receipt, not recomputed offline. Bounded unsupported recommendation requires ROOT independent seal; no admission or global impossibility proof.'}


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
