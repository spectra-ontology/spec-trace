#!/usr/bin/env python3
"""Replay a finite original-source UCI decision-status diagnostic, not admission."""
import argparse
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import re
import stat
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
INVENTORY_SHA256 = '9aa391ef2158b0ca6264976f07b9da8b158ed4dc2c46e649d824f98bbd4cb484'
DECLARATIONS = {'id': 'RAN1_P2_CQ5-10', 'status': 'LOCAL_BOUNDED_SOURCE_STATUS_DIAGNOSTIC_NOT_ADMISSION', 'diagnostic_subtype': 'source_explicit_agreement_amendment_status_unretained', 'proposed_disposition': 'unsupported_frozen_data', 'distinct_nonblind_AI_reviews': 2, 'root_seal_required': True, 'original560_pass_increment': 0, 'human_expert_n': 0, 'new_model_calls': 0, 'new_native_executions': 0, 'full_graph_embedded': False, 'all_semantic_alternates_absent_claimed': False, 'generic_boundary_is_universally_correct': False}
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
ID = 'RAN1_P2_CQ5-10'
CONDITION = 'if no additional specification impact is identified'
STEMS = ['The above agreement applies to PUCCH with repetitions',
         'The above agreement applies to different priority indexes for PUCCH/PUSCH']


def need(ok, message):
    if not ok:
        raise ValueError(message)


def safe(path):
    path = Path(os.path.abspath(path))
    for p in [path, *path.parents]:
        need(not p.is_symlink(), 'symlink forbidden: ' + str(p))
    return path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(p):
    return json.loads(p.read_bytes())


def literal(e):
    return ''.join(t.text or '' for t in e.iter(W+'t'))


def struck(e):
    result = []
    for r in e.iter(W+'r'):
        s = r.find(W+'rPr/'+W+'strike')
        if s is not None and s.get(W+'val', '1') not in {'0', 'false', 'off'}:
            result.append(literal(r))
    return result


def boundary(text):
    lines = text.split('\n')
    boundaries = []
    for i, line in enumerate(lines):
        if re.fullmatch(r'R1-[0-9]{6,8}\t[^\t]+\t.+', line.strip()):
            boundaries.append(i)
        if re.fullmatch(r'Proposal\s+[0-9]+(?:\.[0-9]+)*\s*:.*', line.strip(), re.I):
            j = i-1
            while j >= 0 and not lines[j].strip():
                j -= 1
            boundaries.append(j if j >= 0 and re.fullmatch(r'TP\s+for\s+.+\s*:',lines[j].strip(),re.I) else i)
    return '\n'.join(lines[:min(boundaries)]) if boundaries else text


def scalar_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, list):
        for v in obj:
            yield from scalar_strings(v)
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from scalar_strings(v)


def verify(frozen_sql=None):
    need(sys.flags.optimize == 0, 'optimization unsupported')
    entry = safe(__file__)
    root = entry.parent
    mp, ip = safe(root/'manifest.json'), safe(root/'immutable_inventory.json')
    invraw = ip.read_bytes()
    need(sha(invraw) == INVENTORY_SHA256, 'immutable inventory mismatch')
    inv, m = json.loads(invraw), load(mp)
    need(set(m) == {'declarations','inventory_sha256','verifier_sha256'}, 'manifest exact keys')
    need(json.dumps(m['declarations'], sort_keys=True) == json.dumps(DECLARATIONS, sort_keys=True), 'strict scientific declarations')
    need(m['inventory_sha256'] == INVENTORY_SHA256 and m['verifier_sha256'] == sha(entry.read_bytes()), 'manifest/self pins')
    observed = set()
    for p in root.rglob('*'):
        safe(p)
        mode = p.lstat().st_mode
        need(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'nonregular file')
        if stat.S_ISREG(mode):
            observed.add(p.relative_to(root).as_posix())
    need(observed == set(inv) | {'manifest.json','immutable_inventory.json',entry.name}, 'closed file inventory')
    for rel, meta in inv.items():
        need(Path(rel).as_posix() == rel and not Path(rel).is_absolute() and '..' not in Path(rel).parts, 'inventory path')
        need(set(meta) == {'bytes','sha256'} and type(meta['bytes']) is int and type(meta['sha256']) is str, 'inventory pin types')
        b = safe(root/rel).read_bytes()
        need(len(b) == meta['bytes'] and sha(b) == meta['sha256'], 'payload changed: '+rel)
    original = load(root/'contract/original_question.json')
    need(original['id'] == ID, 'original question identity')
    need(sha(original['question_en'].encode()) == 'caeee40fdb6e5ec6848deda1fd54c9e553e10e244c5696ca64e7d797bb1b4727', 'original EN changed')
    need(sha(original['cypher'].encode()) == 'bb4d3c24f9fd6d58410de3ab17bf9695a75d6890aa50ad41b0df6332cf2f3192', 'original query changed')
    need(sha((root/'contract/criteria.json').read_bytes()) == 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'original criteria changed')
    source_info = load(root/'evidence/original_sources.json')
    parsed = {}
    for src in source_info:
        label = src['meeting'].replace('RAN1#','')
        b = (root/'source'/('Final_Report_RAN1-'+label+'.docx')).read_bytes()
        need(len(b) == src['DOCX_bytes'] and sha(b) == src['DOCX_sha256'], 'original DOCX pin')
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            need(z.testzip() is None, 'DOCX CRC failure')
            raw, styles = z.read('word/document.xml'), z.read('word/styles.xml')
            need(z.getinfo('word/document.xml').CRC == src['document_XML']['CRC'], 'XML CRC')
            need(z.getinfo('word/styles.xml').CRC == src['styles_XML']['CRC'], 'styles CRC')
        need(sha(raw) == src['document_XML']['sha256'] and len(raw) == src['document_XML']['bytes'], 'XML original bytes')
        need(sha(styles) == src['styles_XML']['sha256'], 'styles original bytes')
        body = list(ET.fromstring(raw).find(W+'body'))
        hits = [(i,literal(el),struck(el)) for i,el in enumerate(body) if any(s in literal(el) for s in STEMS)]
        expected = [(h['raw_body_child0'],h['literal'],h['struck_run_literals']) for h in src['condition_stem_source_hits']]
        need(hits == expected and len(hits) == 2, 'complete exact source-stem scope')
        parsed[src['meeting']] = body
    now, prior = parsed['RAN1#121'], parsed['RAN1#120b']
    for marker, intro, p in [(4483,4484,4485),(4487,4488,4489)]:
        need(literal(now[marker]).strip() == 'Agreement', 'own source Agreement marker')
        need('Confirm RAN1#120bis Working Assumption' in literal(now[intro]) and 'with revised text' in literal(now[intro]), 'source explicit amendment introduction')
        need(struck(now[p]) == [CONDITION], 'actual local deleted condition')
        r = next(r for r in now[p].iter(W+'r') if literal(r) == CONDITION)
        need(r.find(W+'rPr/'+W+'color').get(W+'val') == 'FF0000', 'source deleted condition red')
    need(struck(prior[3614]) == struck(prior[3616]) == [], 'historical condition is not struck')
    need(all(CONDITION in literal(prior[p]) for p in [3614,3616]), 'historical qualified counterevidence')
    # A finite loss discriminator only: removing the actual strike changes semantic annotation,
    # while the same literal w:t serializer still emits the identical condition-bearing text.
    import copy
    for p in [4485,4489]:
        unmarked = copy.deepcopy(now[p])
        for rp in unmarked.iter(W+'rPr'):
            for child in list(rp):
                if child.tag == W+'strike':
                    rp.remove(child)
        need(literal(unmarked) == literal(now[p]) and struck(unmarked) != struck(now[p]), 'finite annotation-loss discriminator')
    witnesses = load(root/'evidence/two_witnesses.json')
    need({w['resolutionId'] for w in witnesses} == {'AGR-121-9.11.3-007','AGR-121-9.11.3-008'}, 'witness identity set')
    for witness in witnesses:
        node = witness['frozen_node_record']
        props = json.loads(node['properties_json'])
        need(set(props) == {'content','hasFFS','hasTBD','resolutionId','sequence'}, 'affected retained field inventory')
        need(literal(now[witness['raw_body_child0']]) in props['content'], 'frozen unmarked condition fidelity comparison')
        need(witness['frozen_Agreement']['contentWithEquations'] is None and witness['frozen_Agreement']['note'] is None, 'retained nullable alternate')
        need({e['rel_type'] for e in witness['all_incident_edges']} == {'MADE_AT','RESOLUTION_BELONGS_TO'}, 'captured incident-role scope')
    pool = load(root/'evidence/all_original_positive_rows.json')
    repaired = load(root/'evidence/all_prospectively_repaired_positive_rows.json')
    derived = [{**r, 'repaired_own_content':boundary(r['content'])} for r in pool if 'UCI' in boundary(r['content']) and 'multiplex' in boundary(r['content'])]
    # Repaired file preserves original full content, and also its derived own-prefix separately.
    need(len(pool) == 182 and len(derived) == len(repaired) == 159, 'actual bounded generic repair population')
    need({(r['node_id'],r['meetingNumber']) for r in derived} == {(r['node_id'],r['meetingNumber']) for r in repaired}, 'bounded repair exact membership')
    above = [r for r in pool if r['meetingNumberInt'] > 121]
    ties = [r for r in pool if r['meetingNumberInt'] == 121]
    need(len(above) == 6 and len(ties) == 5, 'original cutoff authority')
    target = {w['resolutionId'] for w in witnesses}
    possibilities = list(itertools.combinations(ties,10-len(above)))
    need(len(possibilities) == 5 and all({r['resolutionId'] for r in a} & target for a in possibilities), 'all original legal tie selections require affected content')
    latest = [r for r in derived if r['meetingNumberInt'] >= 121]
    need(len(latest) == 10 and target <= {r['resolutionId'] for r in latest}, 'repaired finite prefix still requires both amendments')
    alternatives = load(root/'evidence/all_frozen_scalar_alternative_matches.json')
    need([r['node_id'] for r in alternatives] == [12221,12567,12568], 'captured exact scalar alternate set')
    event = load(root/'evidence/same_event_nodes_and_edges.json')
    broad = load(root/'evidence/broad_applicability_alternatives.json')
    need(len(event) == 13 and len(broad) == 15, 'bounded alternate scopes')
    primary = load(root/'contract/primary_seven_unit_review.json')
    need(primary['id'] == ID and primary['criteria_sha256'] == sha((root/'contract/criteria.json').read_bytes()), 'primary identity/criteria')
    need(len(primary['seven_unit_review']) == 7 and primary['recommended_disposition'] == 'unsupported_frozen_data', 'primary actual judgment')
    reviews = load(root/'contract/review_binding.json')
    need(reviews['distinct_nonblind_AI_reviews'] == DECLARATIONS['distinct_nonblind_AI_reviews'], 'review count')
    for key in ['primary','secondary']:
        if key not in reviews:
            continue
        meta = reviews[key]; b = safe(root/meta['path']).read_bytes()
        need(type(meta['bytes']) is int and len(b) == meta['bytes'] and sha(b) == meta['sha256'], 'review exact pin '+key)
    need(set(reviews) == {'id','primary','secondary','distinct_nonblind_AI_reviews','root_seal_required'}, 'exact two-review binding keys')
    need(reviews['id'] == ID and type(reviews['distinct_nonblind_AI_reviews']) is int and reviews['distinct_nonblind_AI_reviews'] == 2 and reviews['root_seal_required'] is True, 'strict independent review binding')
    secondary = load(root/'contract/ROOT_secondary_exact_seven_unit_review.json')
    independent_path = root/'evidence/ROOT_actual_independent_source_reopen.json'
    independent = load(independent_path)
    need(secondary['id'] == independent['id'] == ID and secondary['original'] == original, 'independent original identity')
    need(secondary['reviewer_kind'] == 'separate_nonblind_AI_secondary' and primary['reviewer_kind'] == 'independent_AI_local_primary_audit', 'two distinct AI reviewer roles')
    need(secondary['nonblind_AI'] is True and type(secondary['human_expert_validation_n']) is int and secondary['human_expert_validation_n'] == 0, 'independent validation attribution')
    need(secondary['criteria_sha256'] == primary['criteria_sha256'] and secondary['diagnostic_subtype'] == primary['diagnostic_subtype'] == DECLARATIONS['diagnostic_subtype'], 'exact semantic criteria/subtype')
    need(secondary['recommended_disposition'] == primary['recommended_disposition'] == 'unsupported_frozen_data', 'two independent recommendations')
    criteria = load(root/'contract/criteria.json')
    for review in [primary,secondary]:
        need([u['unit'] for u in review['seven_unit_review']] == criteria['semantic_units'], 'exact seven semantic units')
        need(all(type(u['assessment']) is str and len(u['assessment']) > 0 for u in review['seven_unit_review']), 'substantive actual judgment required')
    need(secondary['actual_reopen_receipt_sha256'] == sha(independent_path.read_bytes()), 'independent actual reaccess pin')
    need(independent['status'] == 'PASS' and independent['direct_original_archive_reopens'] == 2, 'independent original source access')
    need(independent['SQLite_SHA256_before_after'] == 'aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af', 'independent frozen data identity')
    need(independent['original_literal_five_tie_selections_each_has_required_witness'] is True, 'independent necessary inclusion')
    for obs in independent['raw_source_observations']:
        el = parsed[obs['meeting']][obs['body_child0']]
        need(obs['text'] == literal(el) and obs['direct_struck_text'] == struck(el), 'independent original XML observation reproduced')
    source_witness_nodes = {w['frozen_node_record']['node_id']:w['frozen_node_record'] for w in witnesses}
    for obs in independent['direct_immutable_SQL_records']:
        node = source_witness_nodes[obs['node_id']]
        need(obs['source_iri'] == node['source_iri'] and obs['labels'] == json.loads(node['labels_json']) and obs['properties'] == json.loads(node['properties_json']), 'independent own frozen record full fields')
    mapping = {'all_same_event_agenda_retained_nodes_and_edges.json':'evidence/same_event_nodes_and_edges.json','broad_applicability_alternative_candidates.json':'evidence/broad_applicability_alternatives.json','all_original_literal_cutoff_combinations_NOT_GOLD.json':'evidence/original_tie_possibilities_NOT_GOLD.json'}
    for original_name, rel in mapping.items():
        meta = independent['alternative_and_tie_artifact_pins'][original_name]; b = (root/rel).read_bytes()
        need(len(b) == meta['bytes'] and sha(b) == meta['sha256'], 'independent actual artifact pin '+original_name)
    full_sql = False
    if frozen_sql:
        import sqlite3
        db = safe(frozen_sql)
        h = hashlib.sha256()
        with db.open('rb') as f:
            for chunk in iter(lambda:f.read(8*1024*1024),b''):
                h.update(chunk)
        need(h.hexdigest() == 'aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af', 'optional original DB SHA')
        c = sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True)
        c.row_factory = sqlite3.Row;c.execute('PRAGMA query_only=ON')
        q = (root/'recipe/readonly_original_projection.sql').read_text()
        actual = [dict(r) for r in c.execute(q) if isinstance(r['content'],str) and 'UCI' in r['content'] and 'multiplex' in r['content']]
        need(actual == pool, 'optional entire original SQL pool')
        matches = []
        for row in c.execute('SELECT node_id,properties_json FROM _node_record ORDER BY node_id'):
            if any(any(s in v for s in STEMS) for v in scalar_strings(json.loads(row['properties_json']))):
                matches.append(row['node_id'])
        need(matches == [12221,12567,12568], 'optional whole frozen alternate scalar scan')
        need(c.execute('SELECT count(*) FROM _node_record').fetchone()[0] == 165418, 'optional whole node extent')
        c.close();full_sql = True
    return {'status':'PASS_BOUNDED_SOURCE_STATUS_DIAGNOSTIC','id':ID,'source_DOCX_replayed':2,'all_original_cutoff_combinations':5,'original_pool':182,'prospective_boundary_pool':159,'affected_condition_status_records':2,'same_event_records':13,'broad_alternate_records':15,'distinct_nonblind_AI_reviews':DECLARATIONS['distinct_nonblind_AI_reviews'],'optional_full_frozen_SQL_replayed':full_sql,'root_seal_required':True,'original560_pass_increment':0,'human_expert_n':0,'new_native_executions':0,'new_model_calls':0,'whole_semantic_absence_claim':False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--frozen-sql',type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.frozen_sql),ensure_ascii=False,sort_keys=True))
