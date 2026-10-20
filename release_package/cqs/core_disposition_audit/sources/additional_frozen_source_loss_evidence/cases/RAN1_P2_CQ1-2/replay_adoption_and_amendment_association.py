#!/usr/bin/env python3
"""Audit finite adoption/amendment associations, without choosing a new gold."""
import argparse
import copy
import datetime
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'
SOURCE = 'ontology/input/tsg/RAN/formal/meetings/RAN1/Final_Report/Final_Report_RAN1-100-e.docx'
DB = 'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN1.sqlite'
SOURCE_SHA = '31eb6f41049493370cce7e7de9689a86ecc4e080583374ff452404d7d50fe1b9'
DESIGN = 'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/root_evidence/two_agent_unresolved_loop/RAN1_RAN3_RAN4/loop85_RAN1_technical_topics_original_authority_and_dependencies/design_HEAD.md'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def pin(p, root):
    return {'path': str(p.resolve().relative_to(root.resolve())), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}

def txt(e):
    return ''.join(t.text or '' for t in e.findall('.//w:t', NS))

def norm(s):
    return re.sub('[^a-z0-9]', '', s.lower())

def on(e):
    return e is not None and e.get(W + 'val', '1') not in {'0', 'false', 'off'}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project-root', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    a = ap.parse_args()
    root = a.project_root.resolve()
    a.output.mkdir(parents=True, exist_ok=False)
    source = root / SOURCE
    if sha(source.read_bytes()) != SOURCE_SHA:
        raise ValueError('Source bytes changed')
    with zipfile.ZipFile(source) as z:
        raw = z.read('word/document.xml')
        info = z.getinfo('word/document.xml')
    body = list(ET.fromstring(raw).find('w:body', NS))
    source_agreement_groups = [[415], [417, 418], list(range(421, 426)), [436], list(range(447, 451)), [452, 453]]
    all_scope = [{'raw_body_child0': i, 'kind': body[i].tag.rsplit('}', 1)[-1],
        'text': txt(body[i]), 'xml_sha256': sha(ET.tostring(body[i], encoding='utf-8'))} for i in range(395, 473)]
    groups = [{'resolutionId': f'AGR-100-5.1-{j:03d}', 'raw_body_children0': ii,
        'text': '\n'.join(txt(body[i]) for i in ii),
        'explicit_case_or_option23_occurrences': [m.group() for m in re.finditer(r'Case\s*[12]|option\s*2\s*-\s*3', '\n'.join(txt(body[i]) for i in ii), re.I)]}
        for j, ii in enumerate(source_agreement_groups, 1)]
    run_rows = []
    for i in [419, 420, 423, 425, 437, 438, 442, 443, 444, 446, 447]:
        for j, r in enumerate(body[i].findall('.//w:r', NS)):
            t = txt(r)
            if not t:
                continue
            rp = r.find('w:rPr', NS)
            color = r.find('w:rPr/w:color', NS)
            highlight = r.find('w:rPr/w:highlight', NS)
            run_rows.append({'raw_body_child0': i, 'descendant_run0': j, 'text': t,
                'direct_strike': on(r.find('w:rPr/w:strike', NS)),
                'direct_dstrike': on(r.find('w:rPr/w:dstrike', NS)),
                'color': color.get(W+'val') if color is not None else None,
                'highlight': highlight.get(W+'val') if highlight is not None else None,
                'run_xml': ET.tostring(r, encoding='unicode')})
    # A local projection collision: the actual source and a counterfactual
    # unstruck run have equal w:t text, but different amendment status.
    actual = body[423]
    counterfactual = copy.deepcopy(actual)
    strikes = counterfactual.findall('.//w:rPr/w:strike', NS)
    if len(strikes) != 1:
        raise ValueError('Expected exactly one direct strike')
    for rp in counterfactual.findall('.//w:rPr', NS):
        s = rp.find('w:strike', NS)
        if s is not None:
            rp.remove(s)
    collision = {'scope': 'finite unannotated text projection only; not a full parser/whole-graph counterfactual',
        'actual_XML_sha256': sha(ET.tostring(actual, encoding='utf-8')),
        'unstruck_counterfactual_XML_sha256': sha(ET.tostring(counterfactual, encoding='utf-8')),
        'equal_w_t_projection': txt(actual) == txt(counterfactual),
        'actual_direct_strike_text': [x['text'] for x in run_rows if x['raw_body_child0'] == 423 and x['direct_strike']],
        'counterfactual_direct_strike_n': len(counterfactual.findall('.//w:strike', NS)),
        'plain_text': txt(actual)}
    c = sqlite3.connect((root / DB).resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA query_only=ON')
    version_before = c.execute('PRAGMA data_version').fetchone()[0]
    condition_sql = """SELECT p.node_id,p.key,p.value_json,n.labels_json,n.properties_json
      FROM node_property p JOIN _node_record n ON n.node_id=p.node_id
      WHERE instr(lower(p.value_json),'switching')>0 ORDER BY p.node_id,p.key"""
    all_switching = [dict(r) for r in c.execute(condition_sql)]
    condition = 'The switching period is only applicable when the UL transmissions are switched between 1Tx carrier 1 and 2Tx carrier 2'
    old_condition = condition.replace('the UL', 'the scheduled UL')
    matches = []
    for r in all_switching:
        value = json.loads(r['value_json'])
        if not isinstance(value, str):
            continue
        hits = []
        if norm(condition) in norm(value):
            hits.append('unqualified_condition')
        if norm(old_condition) in norm(value):
            hits.append('scheduled_condition')
        if norm('Clarify the following agreements with changes in red') in norm(value):
            hits.append('amendment_instruction_without_run_format')
        if hits:
            r['hits'] = hits
            matches.append(r)
    scope_ids = [247, 248, 249, 250, 251, 252, 24008]
    placeholders = ','.join('?' for _ in scope_ids)
    scope_nodes = [dict(r) for r in c.execute('SELECT * FROM _node_record WHERE node_id IN ('+placeholders+') ORDER BY node_id', scope_ids)]
    scope_edges = [dict(r) for r in c.execute('SELECT * FROM edge WHERE src_id IN ('+placeholders+') OR dst_id IN ('+placeholders+') ORDER BY edge_id', scope_ids + scope_ids)]
    nodes = [249, 251, 24008, 20741, 484]
    q = ','.join('?' for _ in nodes)
    inspected_nodes = [dict(r) for r in c.execute('SELECT * FROM _node_record WHERE node_id IN ('+q+') ORDER BY node_id', nodes)]
    inspected_edges = [dict(r) for r in c.execute('SELECT * FROM edge WHERE src_id IN ('+q+') OR dst_id IN ('+q+') ORDER BY edge_id', nodes + nodes)]
    identity_sql = """SELECT node_id,key,value_json FROM node_property
      WHERE instr(value_json,'WA-100-5.1-001')>0 OR instr(value_json,'AGR-100-5.1-005')>0 ORDER BY node_id,key"""
    identity_occurrences = [dict(r) for r in c.execute(identity_sql)]
    all_properties = [dict(r) for r in c.execute('SELECT * FROM node_property WHERE node_id IN ('+q+') ORDER BY node_id,key', nodes)]
    tables = []
    for row in c.execute('SELECT * FROM "Table" WHERE tableId LIKE \'TBL-100-%\' ORDER BY node_id'):
        r = dict(row)
        r['edges'] = [dict(e) for e in c.execute('SELECT * FROM edge WHERE src_id=? OR dst_id=? ORDER BY edge_id', (r['node_id'], r['node_id']))]
        r['recorded_external_HTML_exists'] = (root / r['filePath']).is_file()
        tables.append(r)
    version_after = c.execute('PRAGMA data_version').fetchone()[0]
    c.close()
    props = {r['node_id']: json.loads(r['properties_json']) for r in inspected_nodes}
    actual_tables = []
    for i in [444, 447]:
        actual_tables.append({'raw_body_child0': i, 'rows': [[txt(cell).strip() for cell in row.findall('w:tc', NS)] for row in body[i].findall('w:tr', NS)],
            'xml_sha256': sha(ET.tostring(body[i], encoding='utf-8'))})
    design = root / DESIGN
    lines = design.read_text().splitlines()
    authority_spans = [{'lines': [lo, hi], 'text': '\n'.join(f'{i+1}: {lines[i]}' for i in range(lo-1, hi))} for lo,hi in [(133,180),(655,666),(765,785),(968,1003),(1053,1060),(1362,1366),(1432,1457)]]
    checks = {
        'source_six_Agreement_groups_same_as_prior': len(groups) == 6,
        'only_group5_own_table_mentions_Case1_Case2': [i+1 for i,g in enumerate(groups) if g['explicit_case_or_option23_occurrences']] == [5],
        'no_own_prose_group_mentions_option23': not any(re.search(r'option\s*2\s*-\s*3',g['text'],re.I) for g in groups),
        'source_WA_different_role_has_conditional_option_and_future_revisit': 'if option 2 is supported' in txt(body[438]) and 'revisited in future' in txt(body[442]),
        'source_Agreement_active_green_and_WA_darkYellow': any(x['raw_body_child0']==446 and x['highlight']=='green' for x in run_rows) and any(x['raw_body_child0']==437 and x['highlight']=='darkYellow' for x in run_rows),
        'actual_amendment_instruction_precedes_own_Agreement': 'Clarify the following agreements with changes in red' == txt(body[419]).strip(),
        'scheduled_only_direct_struck_word_in_actual_scope': collision['actual_direct_strike_text'] == ['scheduled'],
        'run_text_projection_cannot_encode_strike': collision['equal_w_t_projection'] and collision['actual_XML_sha256'] != collision['unstruck_counterfactual_XML_sha256'],
        'frozen99_and100_same_content_different_event': props[249]['content'] == props[20741]['content'],
        'unqualified_condition_only_later_different_role': [(r['node_id'],r['key']) for r in matches if 'unqualified_condition' in r['hits']] == [(484,'content')],
        'source_case_values_retained_under_WA_not_lost_numerics': '| Case 1 | 1T+1T |' in props[24008]['content'] and '| Case 2 | 0T+2T |' in props[24008]['content'],
        'no_promotion_or_Table_edges_on_either_affected_record': all(e['rel_type'] in {'MADE_AT','RESOLUTION_BELONGS_TO'} for e in scope_edges if e['src_id'] in [251,24008] or e['dst_id'] in [251,24008]),
        'id_literals_no_cross_record_adoption_reference': [(r['node_id'],r['key']) for r in identity_occurrences] == [(251,'resolutionId'),(24008,'resolutionId')],
        'read_only_data_version_equal': version_before == version_after,
    }
    if not all(checks.values()):
        raise ValueError('Actual discriminator expectation failed: '+json.dumps(checks))
    out = {'id':'RAN1_P2_CQ1-2','status':'FINITE_ASSOCIATION_AND_AMENDMENT_AUDIT_NOT_ADMISSION',
        'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source':pin(source,root),'source_XML':{'member':'word/document.xml','bytes':len(raw),'CRC':info.CRC,'sha256':sha(raw)},
        'database':{'path':DB,'access':'read-only immutable/query_only','whole_source_sha256_previously_streamed':'aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'},
        'source_agreement_groups':groups,'source_scope_all_raw_blocks':all_scope,'source_run_formatting':run_rows,
        'source_WA_and_Agreement_tables':actual_tables,'finite_text_projection_collision':collision,
        'all_switching_properties_SQL':condition_sql,'all_switching_properties_examined_n':len(all_switching),
        'actual_condition_and_amendment_matches':matches,'scope_nodes':scope_nodes,'scope_all_incident_edges':scope_edges,
        'affected_and_historical_nodes':inspected_nodes,'affected_and_historical_all_properties':all_properties,
        'affected_and_historical_all_incident_edges':inspected_edges,
        'identity_occurrence_SQL':identity_sql,'actual_identity_occurrences':identity_occurrences,
        'all_meeting100_Table_records_and_edges':tables,
        'original_authority':pin(design,root),'original_authority_spans':authority_spans,'checks':checks,
        'limits':['Same-event numeric case equality is retained counterevidence; no global value absence is claimed.',
            'The finite projection collision is not an exact historical loader replay or a whole-graph information-theory proof.',
            'No global active-only redline policy is introduced: this local amendment is explicitly called changes in red under an Agreement marker.',
            'Source table-cell exclusion from Graph DB is preserved as opposing context. The separate amendment-status defect does not depend on requiring all table cells as graph fields.',
            'Old external HTML file paths are observed absent at those paths; no permanent or worldwide absence is claimed.',
            'No model calls, native executions, new gold, central edits or public edits occurred.'],
        'preserved_initial_probe_failure':{'operation':'unquoted SQL Table identifier','error':'sqlite3.OperationalError: near "Table": syntax error','correction':'Quoted canonical table identifier; read-only probe rerun.'}}
    name='actual_adoption_and_amendment_association.json'
    (a.output/name).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    receipt={'status':'BOUNDED_DISCRIMINATOR_PASS_NOT_ADMISSION','id':out['id'],'checks':checks,
        'all_switching_properties_examined_n':len(all_switching),'files':[pin(a.output/name,root)],
        'native_executions':0,'API_calls':0,'central_or_public_changes':0}
    (a.output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':receipt['status'],'all_switching_properties_examined_n':len(all_switching),'checks_n':len(checks)}))

if __name__ == '__main__':
    if sys.flags.optimize:
        raise RuntimeError('Optimized Python unsupported')
    main()
