"""Replay included original-source and frozen-role diagnostics with standard library."""
import csv
import gzip
import hashlib
import io
import json
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

if sys.flags.optimize:
    raise SystemExit('Run without optimization')
INVENTORY_SHA256 = 'be1239f997a4b8c7c7a454d8a238c4bf1ecc9db972570a7f6808341c0671a4ce'
N = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + N['w'] + '}'


def digest(b):
    return hashlib.sha256(b).hexdigest()


def read(D, name):
    return json.loads((D / name).read_bytes())


def active_text(x):
    out = []
    def visit(y):
        if y.tag in {W + 'del', W + 'moveFrom'}:
            return
        if y.tag == W + 't':
            out.append(y.text or '')
        for z in y:
            visit(z)
    visit(x)
    return ''.join(out)


def paragraph(x, i):
    sty = x.find('w:pPr/w:pStyle', N)
    return {'index': i, 'style': sty.get(W + 'val') if sty is not None else None,
            'text': active_text(x), 'insertions': len(x.findall('.//w:ins', N)),
            'deletions': len(x.findall('.//w:del', N)),
            'moves_from': len(x.findall('.//w:moveFrom', N))}


def parse_original_query(cypher):
    """Generic exact grammar for this preserved node/property/edge path and projection."""
    ident = r'[A-Za-z_][A-Za-z0-9_]*'
    literal = r"'([^']*)'"
    node = r'\((' + ident + r'):(' + ident + r')\s*\{(' + ident + r'):\s*' + literal + r'\}\)'
    last = r'\((' + ident + r'):(' + ident + r')\)'
    edge = r'-\[:(' + ident + r')\]->'
    pattern = r'MATCH\s+' + node + edge + node + edge + last + r'\s+RETURN\s+(.+?)\s+ORDER BY\s+(' + ident + r'\.' + ident + r')'
    m = re.fullmatch(pattern, cypher)
    assert m, 'Original query outside the independently implemented exact grammar'
    av, al, ak, astring, e1, bv, bl, bk, bstring, e2, cv, cl, projections, order = m.groups()
    aliases = {av: al, bv: bl, cv: cl}
    fields = [x.strip() for x in projections.split(',')]
    assert len(fields) == len(set(fields))
    for field in fields + [order]:
        v, k = field.split('.')
        assert v in aliases and re.fullmatch(ident, k)
    ast = {'nodes': [{'variable': av, 'label': al, 'properties': {ak: astring}},
                     {'variable': bv, 'label': bl, 'properties': {bk: bstring}},
                     {'variable': cv, 'label': cl, 'properties': {}}],
           'relationships': [{'source': av, 'type': e1, 'target': bv},
                             {'source': bv, 'type': e2, 'target': cv}],
           'projections': fields, 'order_by': order}
    select = ','.join(f'{f} AS "{f}"' for f in fields)
    sql = f'SELECT {select} FROM "{al}" {av} JOIN edge e1 ON e1.src_id={av}.node_id AND e1.rel_type=? JOIN "{bl}" {bv} ON {bv}.node_id=e1.dst_id JOIN edge e2 ON e2.src_id={bv}.node_id AND e2.rel_type=? JOIN "{cl}" {cv} ON {cv}.node_id=e2.dst_id WHERE {av}."{ak}"=? AND {bv}."{bk}"=? ORDER BY {order}'
    return ast, sql, (e1, e2, astring, bstring)


def memory_graph(slice_data, original_schemas):
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    records = {}
    for r in slice_data['records']:
        assert r['node_id'] not in records
        records[r['node_id']] = {'labels': json.loads(r['labels_json']),
                                 'properties': json.loads(r['properties_json'])}
    schemas = {}
    for r in records.values():
        for label in r['labels']:
            assert re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', label)
            schemas.setdefault(label, set()).update(r['properties'])
    for label, columns in original_schemas.items():
        schemas.setdefault(label, set()).update(x['name'] for x in columns if x['name'] != 'node_id')
    for label, properties in schemas.items():
        names = sorted(properties)
        assert all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', k) for k in names)
        columns = ','.join('"' + k + '"' for k in names)
        c.execute('CREATE TABLE "' + label + '"(node_id INTEGER PRIMARY KEY' + (',' + columns if columns else '') + ')')
        for nid, r in records.items():
            if label in r['labels']:
                vals = [r['properties'].get(k) for k in names]
                vals = [json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x for x in vals]
                c.execute('INSERT INTO "' + label + '" VALUES(' + ','.join('?' for _ in range(1 + len(names))) + ')', [nid] + vals)
    c.execute('CREATE TABLE edge(edge_id INTEGER PRIMARY KEY,src_id INTEGER,rel_type TEXT,dst_id INTEGER)')
    for e in slice_data['edges']:
        assert e['src_id'] in records and e['dst_id'] in records
        c.execute('INSERT INTO edge VALUES(?,?,?,?)', [e[k] for k in ['edge_id', 'src_id', 'rel_type', 'dst_id']])
    for kind in {e['rel_type'] for e in slice_data['edges']}:
        assert re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', kind)
        c.execute('CREATE TABLE "rel_' + kind + '" AS SELECT edge_id,src_id,dst_id FROM edge WHERE rel_type=?', (kind,))
    return c, records


def semantic_checks(D):
    q = read(D, 'contract/original_question_and_query.json')
    original = json.loads((D / 'contract/original_benchmark_record.jsonl').read_bytes())
    assert original == q['original_record']
    assert digest((D / 'contract/original_benchmark_record.jsonl').read_bytes()) == q['raw_record_sha256']
    assert digest(original['question_en'].encode()) == q['question_sha256']
    assert digest(original['cypher'].encode()) == q['query_sha256']
    criteria = read(D, 'contract/criteria.json')
    assert digest((D / 'contract/criteria.json').read_bytes()) == q['criteria']['sha256']
    primary = read(D, 'contract/primary_seven_unit_review.json')
    assert [u['semantic_unit'] for u in primary['semantic_units']] == criteria['semantic_units']
    assert primary['recommendation'] == 'unsupported_frozen_data'
    assert primary['question_sha256'] == q['question_sha256']
    assert primary['expert_validation_n'] == 0 and primary['nonblind_AI'] is True
    secondary_path = D / 'contract/ROOT_secondary_review.json'
    secondary = json.loads(secondary_path.read_bytes()) if secondary_path.is_file() else None
    if secondary is not None:
        assert secondary['id'] == q['id']
        assert secondary.get('decision', secondary.get('recommendation', secondary.get('classification'))) == 'unsupported_frozen_data'
        su = secondary['semantic_units']
        assert [u.get('semantic_unit', u.get('unit')) for u in su] == criteria['semantic_units']

    source = read(D, 'source/direct_original_source_and_format.json')
    bodies = {}
    source_checks = 0
    for s in source:
        key = s['key']
        xml = gzip.decompress((D / 'source' / key / 'document.xml.gz').read_bytes())
        styles = gzip.decompress((D / 'source' / key / 'styles.xml.gz').read_bytes())
        assert len(xml) == s['document_xml']['bytes'] and digest(xml) == s['document_xml']['sha256']
        assert len(styles) == s['styles_xml']['bytes'] and digest(styles) == s['styles_xml']['sha256']
        ET.fromstring(styles)
        body = ET.fromstring(xml).find('w:body', N)
        ps = body.findall('w:p', N)
        assert len(body) == s['body_children'] and len(ps) == s['direct_body_paragraphs']
        bodies[key] = body
        if key == 'TR38889':
            for name in ['scope', 'conclusions', 'own_reference_to_TS38213_section13']:
                assert [paragraph(ps[x['index']], x['index']) for x in s[name]] == s[name]
            assert [paragraph(x, i) for i, x in enumerate(ps) if re.search(r'38\.21[1-4]', active_text(x))] == s['all_TS38_211_to_214_mentions']
        elif key.startswith('TS'):
            actual = [paragraph(x, i) for i, x in enumerate(ps)]
            assert [x for x in actual if x['style'] == 'Heading1'] == s['top_level_headings']
            if key == 'TS38213':
                assert [actual[x['index']] for x in s['section16_start']] == s['section16_start']
        else:
            tbl = body[s['cover_table_body_child']]
            assert tbl.tag == W + 'tbl'
            rows = [{'row': i, 'cells': [active_text(tc) for tc in tr.findall('w:tc', N)]}
                    for i, tr in enumerate(tbl.findall('w:tr', N))]
            assert rows == s['cover_rows']
            for x in s['all_heading_or_explicit_new_section_paragraphs']:
                assert {'body_child': x['body_child'], **paragraph(body[x['body_child']], x['body_child'])} == x
        source_checks += 1
    bykey = {x['key']: x for x in source}
    assert bykey['TS38213']['section16_start'][0]['text'] == '16UE procedures for sidelink'
    cover = bykey['CR1913631']['cover_rows']
    assert cover[6]['cells'][1] == 'NR_unlic-Core'
    assert cover[8]['cells'][1] == 'B' and cover[8]['cells'][4] == 'Rel-16'
    assert 'NR based access to unlicensed spectrum' in cover[1]['cells'][1]
    new_sections = re.findall(r'([0-9]+(?:\.[0-9]+)+)\s*\(new\)', cover[17]['cells'][1])
    assert len(new_sections) == len(set(new_sections)) == 6
    new_heading_rows = []
    for i, x in enumerate(bodies['CR1913631']):
        if x.tag != W + 'p':
            continue
        t = active_text(x)
        for number in new_sections:
            if t.startswith(number) and len(t) > len(number) and not (t[len(number)].isdigit() or t[len(number)] == '.'):
                p = paragraph(x, i)
                assert p['insertions'] > 0 and p['deletions'] == 0 and p['moves_from'] == 0
                new_heading_rows.append({'section_number': number, 'body_child': i, 'text': t})
    assert len(new_heading_rows) == 6

    slice_data = read(D, 'frozen/own_TR_impact_and_two_CR_all_incident_frozen_slice.json')
    diagnostics = read(D, 'frozen/actual_immutable_SQL_diagnostics.json')
    c, records = memory_graph(slice_data, read(D, 'frozen/original_SQL_table_schemas.json'))
    ast, sql, params = parse_original_query(original['cypher'])
    rows = [dict(x) for x in c.execute(sql, params)]
    assert rows == diagnostics['original_projection']['rows'] and len(rows) == 1
    own = [r for r in records.values() if 'TechnicalReport' in r['labels'] and r['properties'].get('trNumber') == '38.889']
    assert len(own) == 1
    all_impacts = [dict(x) for x in c.execute(diagnostics['all_own_impacts']['sql'])]
    assert all_impacts == diagnostics['all_own_impacts']['rows'] and len(all_impacts) == 4
    assert sum(x['sectionId'] is None for x in all_impacts) == 3
    resolved = [x for x in all_impacts if x['sectionId'] is not None]
    assert len(resolved) == 1 and resolved[0]['sectionTitle'] == 'UE procedures for sidelink'
    assert resolved[0]['sectionId'] == rows[0]['s.sectionId']
    csv_rows = list(csv.DictReader(io.StringIO((D / 'source/original_TR_impact_mapping.csv').read_text())))
    selected = [x for x in csv_rows if x['trNumber'] == '38.889']
    assert len(selected) == 4
    for x in all_impacts:
        matched = [v for v in selected if v['impactsSpec'] == x['specNumber']]
        assert len(matched) == 1
        v = matched[0]
        assert v['impactType'] == x['impactType'] == 'NewSection'
        assert v['impactsSection'] == x['affectedSection'] == '16'
        assert v['impactDescription'] == x['impactDescription']
    target = [nid for nid, r in records.items() if 'CR' in r['labels'] and r['properties'].get('tdocNumber') == 'R1-1913631']
    assert len(target) == 1
    crid = target[0]
    assert records[crid]['properties'].get('clausesAffected') is None
    modedges = [e for e in slice_data['edges'] if e['src_id'] == crid and e['rel_type'] == 'MODIFIES_SECTION']
    assert len(modedges) == 11
    modnumbers = {records[e['dst_id']]['properties']['sectionNumber'] for e in modedges}
    assert set(new_sections).isdisjoint(modnumbers)
    frontier = read(D, 'frozen/whole_decoded_frozen_explicit_role_frontier.json')
    assert frontier['all_node_records_scanned'] == 165418
    assert frontier['decoded_string_scalars_scanned'] == 1112204
    assert len(frontier['hits']['TR_number']) == 34 and frontier['hits']['new_marker'] == []
    receipt = read(D, 'provenance/actual_source_and_frozen_reopen_receipt.json')
    assert receipt['sqlite_before'] == receipt['sqlite_after']
    assert receipt['original_question_sha256'] == q['question_sha256']
    assert receipt['original_query_sha256'] == q['query_sha256']
    assert all(receipt[k] == 0 for k in ['native_calls', 'API_calls', 'DB_mutations', 'P_mutations'])
    c.close()
    return {'status': 'PASS', 'id': original['id'], 'classification': 'unsupported_frozen_data',
            'source_documents_reopened': source_checks, 'original_query_rows': len(rows),
            'own_impacts': len(all_impacts), 'unresolved_impact_targets': 3,
            'explicit_new_source_sections': new_sections, 'lost_new_section_CR_roles': len(new_sections),
            'query_ast': ast, 'independent_SQL_sha256': digest(sql.encode()),
            'AI_reviews': 2 if secondary is not None else 1, 'human_expert_reviews': 0,
            'new_admitted_originals': 0, 'fresh_model_or_native_calls': 0,
            'offline_scope': 'Included raw-source XML/styles, saved bounded graph slice and pinned actual full-frozen receipts. Original archive/frozen DB reopening is a separate explicitly supplied-input operation.'}


def verify(D):
    inventory_bytes = (D / 'immutable_inventory.json').read_bytes()
    assert digest(inventory_bytes) == INVENTORY_SHA256
    inv = json.loads(inventory_bytes)
    for name, expected in inv['files'].items():
        p = D / name
        assert p.is_file() and not p.is_symlink()
        b = p.read_bytes()
        assert len(b) == expected['bytes'] and digest(b) == expected['sha256'], name
    manifest = read(D, 'manifest.json')
    assert manifest['files'].keys() == {p.relative_to(D).as_posix() for p in D.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    for name, expected in manifest['files'].items():
        b = (D / name).read_bytes()
        assert {'bytes': len(b), 'sha256': digest(b)} == expected, name
    assert manifest['classification'] == 'unsupported_frozen_data'
    assert manifest['new_admitted_originals'] == 0 and manifest['new_model_evaluations'] == 0
    result = semantic_checks(D)
    assert result['AI_reviews'] == manifest['AI_reviews']
    return result


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parent), ensure_ascii=False))
