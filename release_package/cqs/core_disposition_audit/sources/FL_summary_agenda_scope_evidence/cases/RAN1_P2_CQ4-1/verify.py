#!/usr/bin/env python3
"""Offline replay of a bounded, question-specific scope-classification record."""
import argparse
import collections
import gzip
import hashlib
import io
import json
import os
import re
import stat
import sys
import xml.etree.ElementTree as E
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
INVENTORY_SHA256 = '5efdab02dac96021b55a1e8891f5a7fcf88a130469998403f9353645fa41b7b2'
DECLARATIONS = {'id': 'RAN1_P2_CQ4-1', 'artifact_type': 'bounded_question_scope_classification_diagnostic', 'recommended_disposition': 'clarification_required', 'diagnostic_subtype': 'cross_meeting_numeric_agenda_and_technology_scope_conflict', 'original560_pass_increment': 0, 'human_expert_n': 0, 'nonblind_AI': True, 'independent_semantic_reviews': 2, 'actual_source_reports': 2, 'actual_same_report_own_FL_headers': 9, 'all_retained_FL_nodes': 2743, 'all_retained_FL_role_paths': 2710, 'source_world_topic_completeness_claimed': False, 'gold_selected': False, 'ROOT_seal_included': False, 'new_model_calls': 0, 'new_native_calls': 0}
ID = 'RAN1_P2_CQ4-1'
QUESTION_SHA = '471a52294d3de115ff2f1cc2921ad407f6834c3c5cd80ae2e9e84a9554850375'
QUERY_SHA = '27da50a7e14e8b3b8c65077b4d025fc965c830bee3f742106624c09047c4c7ba'
CRITERIA_SHA = 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
DB_SHA = 'aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def need(ok, msg):
    if not ok:
        raise ValueError(msg)


def safe(p):
    p = Path(os.path.abspath(p))
    for q in [p, *p.parents]:
        need(not q.is_symlink(), 'symlink forbidden: ' + str(q))
    return p


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load(p):
    return json.loads(p.read_bytes())


def tx(el):
    return ''.join(n.text or '' for n in el.iter(W + 't'))


def tabtext(el):
    return ''.join('\t' if n.tag == W + 'tab' else n.text or '' for n in el.iter() if n.tag in {W + 'tab', W + 't'})


def join_paths(d):
    ts = {v['node_id']: v for v in d['FL_Tdocs']}
    ai = {v['node_id']: v for v in d['AgendaItems']}
    cs = {v['node_id']: v for v in d['Companies']}
    mm = collections.defaultdict(list)
    for e in d['MODERATED_BY']:
        if e['dst_id'] in cs:
            mm[e['src_id']].append(e['dst_id'])
    out = []
    for e in d['BELONGS_TO']:
        if e['src_id'] not in ts or e['dst_id'] not in ai:
            continue
        t, a = ts[e['src_id']], ai[e['dst_id']]
        for company in mm[e['src_id']]:
            c = cs[company]
            out.append({**t, 'agenda_node_id': a['node_id'], 'meetingNumber': a['meetingNumber'], 'agendaNumber': a['agendaNumber'], 'agendaDescription': a['agendaDescription'], 'company_node_id': c['node_id'], 'companyName': c['companyName']})
    out.sort(key=lambda v: tuple((v[k] is not None, v[k]) for k in ['meetingNumber', 'agendaNumber', 'tdocNumber', 'companyName']))
    return out


def scope_policies(d, paths):
    bymeeting = collections.defaultdict(list)
    for a in d['AgendaItems']:
        bymeeting[a['meetingNumber']].append(a)
    def has_parent(row, term):
        return any(term in (p['agendaDescription'] or '').lower() and (row['agendaNumber'] == p['agendaNumber'] or row['agendaNumber'].startswith(p['agendaNumber'] + '.')) for p in bymeeting[row['meetingNumber']])

    def component(row):
        return row['agendaNumber'] == '7.1' or row['agendaNumber'].startswith('7.1.')

    predicates = {
        'authored_numeric_startswith_7_1': lambda v: v['agendaNumber'].startswith('7.1'),
        'numeric_component_7_1': component,
        'numeric_component_7_1_AND_MIMO_parent': lambda v: component(v) and has_parent(v, 'mimo'),
        'MIMO_parent_any_numeric_agenda': lambda v: has_parent(v, 'mimo'),
        'explicit_NR_MIMO_parent_any_numeric_agenda': lambda v: has_parent(v, 'nr mimo')
    }
    out = {}
    for name, f in predicates.items():
        chosen = [v for v in paths if f(v)]
        counts = collections.Counter((v['company_node_id'], v['companyName']) for v in chosen)
        whole = []
        for (node, namec), n in counts.items():
            whole.append({'node_id': node, 'companyName': namec, 'flCount': n, 'distinctTdocDiagnostic': len({v['node_id'] for v in chosen if v['company_node_id'] == node})})
        whole.sort(key=lambda v: (-v['flCount'], v['companyName']))
        out[name] = {'paths': chosen, 'whole': whole, 'top5': whole[:5]}
    return out


def verify(frozen_sql=None):
    need(sys.flags.optimize == 0, 'optimization unsupported')
    entry = safe(__file__)
    root = entry.parent
    ip, mp = safe(root / 'immutable_inventory.json'), safe(root / 'manifest.json')
    raw = ip.read_bytes()
    need(sha(raw) == INVENTORY_SHA256, 'immutable inventory mismatch')
    inv, m = json.loads(raw), load(mp)
    need(set(m) == {'declarations', 'inventory_sha256', 'verifier_sha256'}, 'exact manifest keys')
    need(json.dumps(m['declarations'], sort_keys=True) == json.dumps(DECLARATIONS, sort_keys=True), 'strict declarations')
    need(m['inventory_sha256'] == INVENTORY_SHA256 and m['verifier_sha256'] == sha(entry.read_bytes()), 'self/inventory pin')
    actual = set()
    for p in root.rglob('*'):
        safe(p)
        mode = p.lstat().st_mode
        need(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'nonregular file')
        if stat.S_ISREG(mode):
            actual.add(p.relative_to(root).as_posix())
    need(actual == set(inv) | {'manifest.json', 'immutable_inventory.json', 'verify.py'}, 'closed file inventory')
    for rel, f in inv.items():
        need(not Path(rel).is_absolute() and '..' not in Path(rel).parts and Path(rel).as_posix() == rel, 'inventory relative path')
        need(set(f) == {'bytes', 'sha256'} and type(f['bytes']) is int and type(f['sha256']) is str, 'exact inventory types')
        b = safe(root / rel).read_bytes()
        need(len(b) == f['bytes'] and sha(b) == f['sha256'], 'payload changed: ' + rel)
    q = load(root / 'contract/original_question.json')
    need(q['id'] == ID and sha(q['question_en'].encode()) == QUESTION_SHA and sha(q['cypher'].encode()) == QUERY_SHA, 'immutable original question/query')
    criteria = load(root / 'contract/criteria.json')
    need(sha((root / 'contract/criteria.json').read_bytes()) == CRITERIA_SHA, 'unchanged criteria')
    d = json.loads(gzip.decompress((root / 'frozen/all_FL_role_dependency.json.gz').read_bytes()))
    need(d['provenance']['frozen_SQL_sha256'] == DB_SHA, 'frozen dependency source identity')
    counts = {k: len(v) for k, v in d.items() if isinstance(v, list)}
    need(counts == {'FL_Tdocs': 2743, 'AgendaItems': 6439, 'Companies': 222, 'BELONGS_TO': 2743, 'MODERATED_BY': 2710, 'all_FL_role_paths': 2710}, 'full retained dependency counts')
    need(all(v['summaryType'] == 'FL' for v in d['FL_Tdocs']), 'FL node role')
    need(len({v['companyName'] for v in d['Companies']}) == len(d['Companies']), 'group-by company name has no node collision')
    for key in ['FL_Tdocs', 'AgendaItems', 'Companies']:
        need(len({v['node_id'] for v in d[key]}) == len(d[key]), 'unique dependency identity')
    paths = join_paths(d)
    need(paths == d['all_FL_role_paths'], 'independent edge-join full2710 paths')
    pol = scope_policies(d, paths)
    saved = load(root / 'evidence/rank_sensitivities.json')
    need(set(pol) == set(saved['paths']), 'same explicit diagnostic policies')
    for name, v in pol.items():
        need(v['paths'] == saved['paths'][name], 'whole diagnostic path population')
        need(v['whole'] == saved['policies'][name]['whole'] and v['top5'] == saved['policies'][name]['top5'], 'original count-path ranking')
    need(pol['authored_numeric_startswith_7_1']['paths'] == pol['numeric_component_7_1']['paths'], 'no invented7.10 current defect')
    need([v['companyName'] for v in pol['authored_numeric_startswith_7_1']['top5']] != [v['companyName'] for v in pol['explicit_NR_MIMO_parent_any_numeric_agenda']['top5']], 'scope sensitivity is substantive, not only a tie')
    scoped = load(root / 'evidence/two_original_report_scope_reopen.json')
    bodies = {}
    for s in scoped['sources']:
        meeting = s['meeting']
        b = (root / ('source/Final_Report_RAN1-' + meeting + '.docx')).read_bytes()
        need(sha(b) == s['loader']['sha256'], 'actual DOCX loader pin')
        need(any(v['bytes'] == len(b) for v in s['original_archive_exact_matches']), 'retained physical archive-member byte equality receipt')
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            need(z.testzip() is None, 'source CRC')
            xml, styles = z.read('word/document.xml'), z.read('word/styles.xml')
        need(sha(xml) == s['document_XML_sha256'] and sha(styles) == s['styles_XML_sha256'], 'source XML/styles identity')
        body = list(E.fromstring(xml).find(W + 'body'))
        bodies[meeting] = body
        for sn in s['own_heading_snippets'] + s['TOC_number_title_snippets']:
            el = body[sn['raw_body_child0']]
            need(tx(el) == sn['text'], 'original source heading/TOC text')
            if 'pStyle' in sn:
                need([n.get(W + 'val') for n in el.iter(W + 'pStyle')] == sn['pStyle'], 'actual own heading style')
    own = load(root / 'evidence/nine_own_FL_headers.json')
    need(own['source_coordinate'] == 'unfiltered raw w:body child ordinal0; native w:tab delimits header fields', 'source coordinate convention')
    need(len(own['own_header_rows']) == 9 and own['numeric_7_1_own_FL_rows'] == 2 and own['actual_NR_MIMO_8_1_own_FL_rows'] == 7, 'bounded same-report FL contrast')
    dbcompanies = {v['node_id']: v for v in d['Companies']}
    for row in own['own_header_rows']:
        frozen = row['frozen_path']
        need(frozen in paths, 'actual role witness exists in frozen full dependency')
        el = bodies['115'][row['raw_body_child0']]
        fields = tabtext(el).split('\t')
        need(fields == row['fields_preserving_Word_tabs'] and fields[0].strip() == frozen['tdocNumber'], 'own first-field identity, not citation')
        need(re.search(r'FL\s+summary', fields[1], re.I) is not None and fields[2] == 'Moderator (' + row['own_role_company_literal'] + ')', 'own original FL/Moderator literal')
        company = dbcompanies[frozen['company_node_id']]
        need(company == row['original_frozen_Company'], 'existing original company attributes')
        aliases = json.loads(company['aliases'] or '[]')
        need(row['own_role_company_literal'] in [company['companyName'], *aliases], 'no invented company alias merge')
        headings = []
        for i, el in enumerate(bodies['115'][:row['raw_body_child0']]):
            if el.tag != W + 'p':
                continue
            s = el.find(W + 'pPr/' + W + 'pStyle')
            mt = re.fullmatch(r'Heading([1-9])', s.get(W + 'val', '') if s is not None else '')
            if mt:
                level = int(mt.group(1))
                headings = [v for v in headings if v['level'] < level]
                headings.append({'raw_body_child0': i, 'level': level, 'text': tx(el)})
        need(headings == row['nearest_heading_stack'], 'actual own Heading ancestry')
        anchor = 612 if frozen['agendaNumber'] == '7.1' else 1643
        need(any(v['raw_body_child0'] == anchor for v in headings), 'own numeric/NR-MIMO different parent witness')
    p1 = (root / 'authority/phase1_HEAD.md').read_text()
    p2 = (root / 'authority/phase2_HEAD.md').read_text()
    need('같은 agendaNumber가 다른 미팅에서 다른 description을 가질 수 있음' in p1, 'original meeting-local agenda authority')
    need('두 표현은 **동일한 역할**' in p2 and 'Summary의 Moderator 회사' in p2, 'original documented company-role authority')
    reviews = [load(root / ('contract/' + name + '_review.json')) for name in ['primary', 'secondary']]
    need(reviews[0] != reviews[1] and reviews[0]['reviewer'] != reviews[1]['reviewer'], 'two distinct AI semantic judgments')
    for r in reviews:
        need(r['id'] == ID and r['question_sha256'] == QUESTION_SHA and r['original_query_sha256'] == QUERY_SHA, 'exact review task binding')
        units = r.get('semantic_units', r.get('seven_unit_review'))
        need([u['unit'] for u in units] == criteria['semantic_units'], 'seven original semantic units')
        need(all(type(u.get('judgment')) is str and u['judgment'] and type(u.get('assessment')) is str and u['assessment'] for u in units), 'actual seven-unit judgments')
        need(r.get('recommendation', r.get('recommended_disposition')) == 'clarification_required', 'scope classification, no fake semantic pass')
    independent = load(root / 'evidence/ROOT_independent_source_and_SQL_review.json')
    need(independent['id'] == ID and independent['status'] == 'ACTUAL_ROOT_SOURCE_AND_IMMUTABLE_SQL_CHECKS_PASS', 'distinct actual source/SQL check receipt')
    need(independent['all_frozen_FL_role_paths'] == 2710 and independent['numeric_paths'] == independent['numeric_distinct_Tdoc_n'] == 18, 'independent original matched-path unit')
    need(independent['all18_own_company_roles_corroborated'] is True and independent['nine_own_scope_headers_reopened'] == 9, 'positive own-role counterevidence retained')
    need(independent['SQL_before_sha256'] == independent['SQL_after_sha256'] == DB_SHA and independent['gold_selected'] is False, 'read-only distinct replay, no selected gold')
    for name, v in pol.items():
        need(independent['diagnostic_rank_checks'][name]['top5'] == v['top5'], 'independent SQL policy ranking agrees')
    sqlreplay = False
    if frozen_sql is not None:
        import sqlite3
        p = safe(frozen_sql)
        need(p.is_file() and sha(p.read_bytes()) == DB_SHA, 'explicit frozen SQL identity')
        con = sqlite3.connect(p.as_uri() + '?mode=ro&immutable=1', uri=True)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA query_only=ON')
        receipt = load(root / 'frozen/export_receipt.json')
        for key, query in receipt['queries'].items():
            need([dict(v) for v in con.execute(query)] == d[key], 'explicit full SQL dependency equality: ' + key)
        need([dict(v) for v in con.execute(receipt['full_path_query'])] == d['all_FL_role_paths'], 'explicit whole SQL path projection')
        con.close()
        sqlreplay = True
    return {'status': 'PASS_BOUNDED_SCOPE_DIAGNOSTIC_REPLAY', 'id': ID, 'recommended_disposition': 'clarification_required', 'diagnostic_subtype': DECLARATIONS['diagnostic_subtype'], 'all_retained_FL_nodes': 2743, 'all_retained_FL_role_paths': 2710, 'scope_diagnostic_policies': 5, 'physical_report_witnesses': 2, 'same_report_own_FL_role_headers': 9, 'semantic_reviews': 2, 'source_world_topic_completeness_claimed': False, 'gold_selected': False, 'explicit_SQL_replay': sqlreplay, 'original560_pass_increment': 0, 'human_expert_n': 0, 'new_model_calls': 0, 'new_native_calls': 0}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--frozen-sql', type=Path)
    a = ap.parse_args()
    print(json.dumps(verify(a.frozen_sql), ensure_ascii=False, sort_keys=True))
