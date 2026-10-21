#!/usr/bin/env python3
"""Replay bounded CSI-RS chronological-reference source evidence offline."""
import argparse
import collections
import copy
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import sys
import xml.etree.ElementTree as E
import zipfile

sys.dont_write_bytecode = True
INVENTORY_SHA256 = 'b63bcf10e85f9163075834c1c00b1749b9f95026a229a249e6625adae7cf647f'
DECLARATIONS = {'id': 'RAN1_P2_CQ5-1', 'artifact_type': 'bounded_frozen_chronological_reference_source_diagnostic', 'recommended_disposition': 'unsupported_frozen_data', 'diagnostic_subtype': 'source_explicit_agreement_amendment_status_unretained', 'original560_pass_increment': 0, 'human_expert_n': 0, 'nonblind_AI': True, 'independent_semantic_reviews': 2, 'archived_native_rows': 15, 'full_native_columns': 3, 'original_positives': 1423, 'generic_prefix_positives': 1371, 'original_cutoff_mandatory': 10, 'original_cutoff_ties': 6, 'original_boundary_choose': 5, 'generic_prefix_mandatory': 14, 'generic_prefix_ties': 27, 'active_two_or_more_port_positive_retained': True, 'all_legal_fifteen_fail_claimed': False, 'new_model_calls': 0, 'new_native_calls': 0, 'ROOT_seal_included': False}
ID = 'RAN1_P2_CQ5-1'
QUESTION_SHA = '420fcb6befc294a67781e7a3d231fdb12191e7d171152675f0c7a1ca54ae1750'
QUERY_SHA = '3aaf20190a53f22c477f0ffe85957bc91486914951c5529cd871d64d14bdbd40'
CRITERIA_SHA = 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
DB_SHA = 'aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
HEADER = re.compile(r'R1-[0-9]{6,8}\t[^\t]+\t.+')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict_equal(a, b):
    return json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)


def safe(path):
    path = Path(os.path.abspath(path))
    for p in [path, *path.parents]:
        need(not p.is_symlink(), 'symlink forbidden before read: ' + str(p))
    return path


def load(path):
    raw = path.read_bytes()
    if path.suffix == '.gz':
        raw = gzip.decompress(raw)
    return json.loads(raw)


def prefix(value):
    lines = value.split('\n')
    for i, line in enumerate(lines):
        if HEADER.fullmatch(line.strip()):
            return '\n'.join(lines[:i])
    return value


def text(node):
    return ''.join(t.text or '' if t.tag in {W+'t', W+'delText', M+'t'}
                   else '\t' if t.tag == W+'tab'
                   else '\n' if t.tag in {W+'br', W+'cr'} else '' for t in node.iter())


def direct_strike(run):
    prop = run.find(W+'rPr')
    return prop is not None and any(t.tag in {W+'strike', W+'dstrike'}
            and t.get(W+'val', 'true') not in {'0', 'false', 'off'} for t in prop)


def cutoff(rows):
    ordered = sorted(rows, key=lambda row: row['meetingNumberInt'])
    at = ordered[14]['meetingNumberInt']
    return at, [r for r in ordered if r['meetingNumberInt'] < at], [r for r in ordered if r['meetingNumberInt'] == at]


def verify(frozen_sql=None):
    need(sys.flags.optimize == 0, 'Python optimization is unsupported; validation must run')
    entry = safe(__file__)
    root = entry.parent
    ip, mp = safe(root/'immutable_inventory.json'), safe(root/'manifest.json')
    ib = ip.read_bytes()
    need(sha(ib) == INVENTORY_SHA256, 'hard-pinned immutable inventory')
    inventory = json.loads(ib)
    manifest = load(mp)
    need(set(manifest) == {'declarations', 'inventory_sha256', 'verifier_sha256'}, 'exact manifest key set')
    need(strict_equal(manifest['declarations'], DECLARATIONS), 'strict scientific declaration values and types')
    need(manifest['inventory_sha256'] == INVENTORY_SHA256, 'manifest inventory identity')
    need(manifest['verifier_sha256'] == sha(entry.read_bytes()), 'running verifier identity')
    actual = set()
    for path in root.rglob('*'):
        safe(path)
        mode = path.lstat().st_mode
        need(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'nonregular path forbidden')
        if stat.S_ISREG(mode):
            actual.add(path.relative_to(root).as_posix())
    need(actual == set(inventory) | {'manifest.json', 'immutable_inventory.json', entry.name}, 'closed package inventory')
    for rel, pin in inventory.items():
        rp = Path(rel)
        need(not rp.is_absolute() and '..' not in rp.parts and rp.as_posix() == rel, 'canonical relative payload path')
        need(set(pin) == {'bytes', 'sha256'} and type(pin['bytes']) is int and type(pin['sha256']) is str, 'strict payload pin types')
        raw = safe(root/rel).read_bytes()
        need(len(raw) == pin['bytes'] and sha(raw) == pin['sha256'], 'payload changed: ' + rel)

    original = load(root/'contract/original.json')
    need(original['id'] == ID and sha(original['question_en'].encode()) == QUESTION_SHA, 'exact original English')
    need(sha(original['cypher'].encode()) == QUERY_SHA, 'exact original query')
    need((root/'contract/original_query.cypher').read_bytes() == original['cypher'].encode(), 'unchanged query bytes')
    cb = (root/'contract/criteria.json').read_bytes()
    need(sha(cb) == CRITERIA_SHA, 'original seven-unit criteria')
    criteria = json.loads(cb)
    authorities = load(root/'contract/authority_analysis.json')
    for span in authorities['exact_original_spans']:
        name = Path(span['source']['path']).name
        p = root/'authority'/name
        b = p.read_bytes()
        need(sha(b) == span['source']['sha256'], 'prior design/validation identity')
        lines = b.decode().splitlines()
        for line in span['lines']:
            need(lines[line['line']-1] == line['text'], 'exact prior authority line')
    primary = load(root/'contract/primary_review.json')
    secondary = load(root/'contract/secondary_review.json')
    for review in [primary, secondary]:
        need(review['id'] == ID and review['criteria_sha256'] == CRITERIA_SHA, 'semantic review task and criteria')
        need(review['recommended_disposition'] == 'unsupported_frozen_data', 'review recommendation')
        need(review['diagnostic_subtype'] == 'source_explicit_agreement_amendment_status_unretained', 'bounded review subtype')
        need([v['unit'] for v in review['seven_unit_review']] == criteria['semantic_units'], 'all seven original review units')
        need(all(type(v.get('assessment')) is str and v['assessment']
                 and type(v.get('judgment')) is str and v['judgment'] for v in review['seven_unit_review']), 'actual seven-unit assessments')
    need(primary['reviewer'] != secondary['reviewer'] and primary != secondary, 'separate nonblind AI judgments')
    need(secondary['primary_review']['sha256'] == sha((root/'contract/primary_review.json').read_bytes()), 'secondary exact primary observation')
    need(secondary['independent_actual_source_SQL_native_reopen']['sha256'] == sha((root/'evidence/ROOT_independent_source_SQL_native_reopen.json').read_bytes()), 'separate actual source replay receipt identity')

    # This projection is evidence extracted from the frozen database, not new gold.
    projection = load(root/'evidence/all_original_generic_projection.json.gz')
    need(len(projection) == 1423, 'all original positive relationship rows')
    need(len({r['resolutionId'] for r in projection}) == 1409, 'original distinct ID count')
    need(all('CSI-RS' in r['content'] and r['own_prefix'] == prefix(r['content']) for r in projection), 'all finite generic prefix replay')
    kept = [r for r in projection if 'CSI-RS' in r['own_prefix']]
    need(len(kept) == 1371, 'tested generic retained-prefix positives')
    at, mandatory, boundary = cutoff(projection)
    kat, km, kb = cutoff(kept)
    need((at, len(mandatory), len(boundary)) == (85, 10, 6), 'original ASC-only cutoff')
    need((kat, len(km), len(kb)) == (86, 14, 27), 'candidate generic repair cutoff')
    need(any(r['node_id'] == 13993 for r in km), 'status witness mandatory under tested generic repair')
    finite = load(root/'evidence/full_cutoff.json')
    need(strict_equal(finite['original']['mandatory'], mandatory)
         and strict_equal(finite['original']['boundary'], boundary), 'original cutoff evidence')
    need(strict_equal(finite['generic_repair_candidate']['mandatory'], km)
         and strict_equal(finite['generic_repair_candidate']['boundary'], kb), 'generic cutoff evidence')
    need(finite['no_clean_member_selection'] is True and finite['native_execution_claim'] is False, 'candidate is not a selected gold/native capture')
    # A valid original fifteen can omit this particular tied witness. Preserve it.
    alternate15 = mandatory + [r for r in boundary if r['node_id'] != 13993]
    need(len(alternate15) == 15 and all(r['node_id'] != 13993 for r in alternate15), 'actual legal counterexample to every-fifteen failure')

    source_pins = load(root/'evidence/generic_source_receipt.json')['source_pins']
    bodies = {}
    source_data = {}
    for sp in source_pins:
        name = Path(sp['source']['path']).name
        raw_doc = (root/'source'/name).read_bytes()
        need(sha(raw_doc) == sp['source']['sha256'], 'original report bytes')
        with zipfile.ZipFile(io.BytesIO(raw_doc)) as z:
            need(z.testzip() is None, 'all DOCX members CRC')
            xml, styles = z.read('word/document.xml'), z.read('word/styles.xml')
            need(z.getinfo('word/document.xml').CRC == sp['document_xml']['CRC'], 'original XML CRC')
        need(sha(xml) == sp['document_xml']['sha256'] and sha(styles) == sp['styles_xml']['sha256'], 'original document and style XML')
        bodies[name] = list(E.fromstring(xml).find(W+'body'))
        source_data[name] = (raw_doc, xml, styles)
    packets = load(root/'evidence/frontier_source_packets.json.gz')
    need(len(packets) == 47 and sum(r['predicate_kept'] for r in packets) == 41, 'full bounded original/repaired frontier')
    blocks_reopened = 0
    for packet in packets:
        body = bodies[Path(packet['source_pin']['source']['path']).name]
        need(packet['retained_prefix'] == prefix(packet['frozen']['content']), 'source packet generic prefix')
        for block in packet['source_blocks'] + [b for a in packet['additional_anchor_contexts'] for b in a['blocks']]:
            element = body[block['raw_body_child0']]
            need(text(element) == block['text'], 'unfiltered w:body child coordinate and text')
            runs = []
            for run in element.iter(W+'r'):
                if not text(run):
                    continue
                strikes = []
                for tag in ['strike', 'dstrike']:
                    t = run.find(W+'rPr/'+W+tag)
                    if t is not None and t.get(W+'val', 'true') not in {'0', 'false', 'off'}:
                        strikes.append(tag)
                runs.append({'text': text(run), 'direct_strike': strikes})
            need(runs == block['runs'], 'all captured raw runs and direct-strike flags')
            need(len(list(element.iter(M+'oMath'))) == block['OMML'], 'bounded OMML objects')
            need(len(list(element.iter(W+'object'))) == block['OLE'], 'bounded OLE objects')
            blocks_reopened += 1

    doc85, xml85, sty85 = source_data['Final_Report_RAN1-85.docx']
    physical = load(root/'evidence/physical85_equality.json')
    archive = (root/'source/original85.zip').read_bytes()
    need(sha(archive) == physical['archive']['sha256'], 'physical original archive pin')
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        need(z.testzip() is None, 'physical ZIP all-member CRC')
        member = z.read(physical['member']['path'])
        need(z.getinfo(physical['member']['path']).CRC == physical['member']['CRC'], 'original DOCX member CRC')
    need(member == doc85 and sha(member) == physical['member']['sha256'], 'physical member equals loader bytes')
    body = bodies['Final_Report_RAN1-85.docx']
    amendment = load(root/'evidence/actual85_amendment_runs.json')
    need(sha(xml85) == amendment['document_xml_sha256'] and sha(sty85) == amendment['styles_xml_sha256'], 'amendment source identity')
    style = E.fromstring(sty85)
    need(not [n for tag in ['strike', 'dstrike'] for n in style.iter(W+tag)
              if n.get(W+'val', 'true') not in {'0', 'false', 'off'}], 'actual no positive style-strike observation')
    for block in amendment['blocks']:
        node = body[block['raw_body_child0']]
        literal = ''.join(t.text or '' for t in node.iter(W+'t'))
        need(literal == block['text'], 'exact own amendment original text')
        need(sha(E.tostring(node)) == block['XML_sha256'], 'actual own block XML identity')
    need(text(body[3559]).strip() == 'Agreement:' and 'agreed, with the following updates' in text(body[3560]), 'own adopted updates marker')
    raw_runs = list(body[3568].iter(W+'r'))
    active = ''.join(text(r) for r in raw_runs if not direct_strike(r))
    deleted = ''.join(text(r) for r in raw_runs if direct_strike(r))
    need(active.strip() == 'CS/CB for FD-MIMO: 2 or more ports per NZP CSI-RS resource', 'real positive minimum decision')
    need(deleted == '(total number of CSI-RS ports up to 16)', 'actual source-deleted same-decision qualifier')
    changed = copy.deepcopy(body[3568])
    for rp in changed.iter(W+'rPr'):
        for v in list(rp):
            if v.tag in {W+'strike', W+'dstrike'}:
                rp.remove(v)
    need(text(changed) == text(body[3568]) and not any(direct_strike(r) for r in changed.iter(W+'r')), 'plain-text status-collision control')

    own = load(root/'evidence/own_fields_and_endpoints.json')
    props = own['target']['properties']
    need(own['target']['node_id'] == 13993 and props['resolutionId'] == 'AGR-85-6.2.11.1-001', 'actual frozen own identity')
    need(deleted in props['content'] and active.strip() in props['content'], 'deleted restriction and genuine positive both retained')
    need(set(props) == {'content','hasFFS','hasTBD','resolutionId','sequence'}, 'all retained own property names')
    # The complete property-name set is checked instead of relying on a prose count.
    need(sorted(e['rel_type'] for e in own['edges']) == ['MADE_AT','RESOLUTION_BELONGS_TO'], 'bounded own incident relations')
    wf = load(root/'evidence/WF_and_property_table.json')
    need(len(wf['own_property_rows']) == 5 and {r['key'] for r in wf['own_property_rows']} == set(props), 'five actual typed own property rows')
    need(wf['same_agenda_resolution_ids'] == [13993], 'same-agenda Resolution alternatives')
    wprops = json.loads(wf['WF_node']['properties_json'])
    need(wprops['id'] == 'tdoc:R1-165852' and wprops['status'] == 'noted', 'WF metadata identity and distinct status role')
    need('content' not in wprops and 'note' not in wprops, 'tested WF has no alternate body/status marker')
    alternatives = load(root/'evidence/all84_retained_feature_candidates.json')
    need(len(alternatives) == 84, 'full observed normalized alternative set')
    for r in alternatives:
        s = json.dumps(r['properties'], ensure_ascii=False).casefold()
        need('fecomp' in s or ('cs/cb' in s and '16' in s and 'csi-rs' in s), 'broad observed alternatives criterion')
    same_event = load(root/'evidence/all14_same_event_records.json')
    need(len(same_event) == 14, 'all observed same-event lexical alternatives')

    native_receipt = load(root/'native/receipt.json')
    rows_raw = (root/'native/rows.jsonl').read_bytes()
    rows = [json.loads(v) for v in rows_raw.splitlines()]
    ex = native_receipt['execution']
    need(native_receipt['original_question'] == original['question_en'], 'archived native exact question')
    need(native_receipt['reference_query_utf8_sha256'] == QUERY_SHA and ex['query_utf8_sha256'] == QUERY_SHA, 'archived native exact query')
    need(ex['status'] == 'OK' and ex['query_modified'] is False and ex['truncated'] is False
         and ex['full_json_rows_available'] is True and ex['execution_summary_complete'] is True
         and ex['rollback_completed'] is True and ex['plan_query_type'] == ex['execution_query_type'] == 'r', 'full archived read-only capture')
    need(ex['columns'] == ['m.meetingNumber','a.resolutionId','a.content'] and ex['rows_file_sha256'] == sha(rows_raw), 'actual full columns and row pin')
    need(len(rows) == ex['row_count_retained'] == 15 and all(type(r) is list and len(r) == 3 and all(type(v) is str for v in r) for r in rows), 'full native fifteen typed positional rows')
    ix = {r['resolutionId']:r for r in mandatory+boundary}
    need(len({r[1] for r in rows}) == 15 and all([ix[r[1]]['meetingNumber'],r[1],ix[r[1]]['content']] == r for r in rows), 'full native values equal immutable-SQL witness')
    need(collections.Counter(ix[r[1]]['meetingNumberInt'] for r in rows) == {84:10,85:5}, 'native actual original membership quotas')
    selected = next(r for r in rows if r[1] == props['resolutionId'])
    need(deleted in selected[2], 'actual native includes the unmarked deleted qualifier')
    np = load(root/'evidence/actual_native15_current_SQL_match.json')
    need(np['actual_native_receipt']['sha256'] == sha((root/'native/receipt.json').read_bytes())
         and np['actual_positional_rows']['sha256'] == sha(rows_raw), 'native provenance observation linkage')
    need(np['source_before'] == np['source_after'] and np['source_before']['nodes'] == 165418
         and np['source_before']['relationships'] == 848228, 'historical native before/after observations')
    need(np['actual_item_receipt_link']['receipt_sha256'] == sha((root/'native/receipt.json').read_bytes()), 'historical exact item receipt pin')

    sys.path.insert(0, str(root/'canonical'))
    import original_scorer
    diagnostic = load(root/'evidence/fixed_reference_status_diagnostic.json')
    dc = diagnostic['contract']
    gold = [{'content':r['content']} for r in mandatory+boundary]
    groups = original_scorer.make_order_groups(dc, mandatory+boundary, gold)
    stale = [{'content':r[2]} for r in rows]
    accepted = original_scorer.score(dc, gold, stale, diagnostic=True, order_groups=groups)
    correction = copy.deepcopy(stale)
    corrected_n = 0
    for r in correction:
        if r['content'] == selected[2]:
            r['content'] = r['content'].replace(' '+deleted, '')
            corrected_n += 1
    rejected = original_scorer.score(dc, gold, correction, diagnostic=True, order_groups=groups)
    need(corrected_n == 1 and accepted == diagnostic['stale_native15_against_SQL_reference']
         and rejected == diagnostic['candidate_removing_actual_source_struck_qualifier'], 'actual unchanged-kernel diagnostic replay')
    need(accepted['exact'] is True and rejected['exact'] is False and rejected['matched_records'] == 14, 'bounded stale-reference diagnostic')
    need(diagnostic['candidate_is_not_replacement_gold'] is True, 'source candidate is not new gold')

    sql_replayed = False
    if frozen_sql is not None:
        import sqlite3
        dbpath = safe(frozen_sql)
        need(dbpath.is_file() and sha(dbpath.read_bytes()) == DB_SHA, 'explicit frozen database pin')
        con = sqlite3.connect(dbpath.as_uri()+'?mode=ro&immutable=1', uri=True)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA query_only=ON')
        actual_projection = [dict(r) for r in con.execute((root/'recipes/independent_generic_prefix.sql').read_text())]
        need(strict_equal(actual_projection, projection), 'explicit complete SQL/Python positive and prefix equality')
        actual_own = dict(con.execute('SELECT * FROM _node_record WHERE node_id=13993').fetchone())
        need(actual_own['properties_json'] == own['target']['properties_json'], 'explicit all own properties')
        actual_edges = [dict(r) for r in con.execute('SELECT * FROM edge WHERE src_id=13993 OR dst_id=13993 ORDER BY edge_id')]
        need(actual_edges == own['edges'], 'explicit all own incident edges')
        broad = []
        for row in con.execute('SELECT * FROM _node_record ORDER BY node_id'):
            pr = json.loads(row['properties_json'])
            s = json.dumps(pr, ensure_ascii=False).casefold()
            if 'fecomp' in s or ('cs/cb' in s and '16' in s and 'csi-rs' in s):
                r = dict(row);r['properties'] = pr;broad.append(r)
        need(strict_equal(broad, alternatives), 'explicit whole normalized-property candidate scan')
        con.close()
        sql_replayed = True
    return {'status':'PASS_BOUNDED_TWO_REVIEW_SOURCE_REPLAY_NOT_PUBLIC_ADMISSION', 'id':ID,
            'actual_archived_native_rows':15, 'native_full_columns':3,
            'original_cutoff_mandatory':10, 'original_cutoff_ties':6, 'original_boundary_choose':5,
            'generic_candidate_mandatory':14, 'generic_candidate_ties':27,
            'raw_frontier_records':47, 'raw_source_blocks_reopened':blocks_reopened,
            'source_active_minimum_retained':True, 'all_legal_fifteen_fail_claimed':False,
            'independent_semantic_reviews':2, 'explicit_SQL_replay':sql_replayed,
            'new_native_calls':0, 'model_calls':0, 'human_expert_n':0, 'original560_pass_increment':0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--frozen-sql', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.frozen_sql), sort_keys=True))
