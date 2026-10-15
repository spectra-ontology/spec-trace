"""Authenticate the complete original UL report and rebuild six additive strings.

Standard library only. Source hashes use original bytes; subtree hashes use
ElementTree UTF-8 serialization. The renderer preserves the declared old source
projection, not arbitrary Word layout or paraphrase equivalence.
"""
import argparse
import hashlib
import json
from io import BytesIO
from pathlib import Path
import re
import shutil
import sqlite3
import zipfile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
KEY = 'formalSourceContentWithTables'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def digest(data): return hashlib.sha256(data).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def canonical(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
def quote(name): return '"' + name.replace('"', '""') + '"'


def text(node):
    return ''.join((item.text or '') if item.tag == W + 't' else ' '
                   if item.tag in {W + 'tab', W + 'br', W + 'cr'} else ''
                   for item in node.iter()).strip()


def verify_source(package, manifest):
    for item in manifest['files']:
        path = (package / item['path']).resolve()
        assert path.is_relative_to(package.resolve())
        assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256'], item['path']
        assert '__pycache__' not in path.parts and path.suffix != '.pyc'
    auth = load(package / 'source/raw_source_archive_authentication.json')
    archive = package / 'source/original_report.zip'
    assert sha(archive) == auth['archive']['sha256']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        member = z.read(auth['member'])
    assert digest(member) == auth['member_sha256'] == auth['retained_DOCX']['sha256']
    assert len(member) == auth['retained_DOCX']['bytes']
    with zipfile.ZipFile(BytesIO(member)) as z:
        assert z.testzip() is None
        raw = z.read('word/document.xml')
    assert digest(raw) == auth['document_XML_sha256']
    whole = load(package / 'source/whole_ordered_report_source.json')
    assert whole['document_xml_sha256'] == digest(raw)
    assert whole['source']['sha256'] == auth['member_sha256']
    tree = ET.fromstring(raw)
    body = list(tree.find(W + 'body'))
    paragraphs = list(tree.iter(W + 'p'))
    assert len(paragraphs) == whole['paragraph_n'] == auth['all_paragraphs_n'] == 6017
    paragraph_indices = {id(p): index for index, p in enumerate(paragraphs)}
    assert [i for i, node in enumerate(body) if node.tag in {W + 'p', W + 'tbl'}] == [r['body_child_index'] for r in whole['records']]
    for record in whole['records']:
        node = body[record['body_child_index']]
        assert digest(ET.tostring(node, encoding='utf-8')) == record['xml_sha256']
        assert text(node) == record['text']
        assert [paragraph_indices[id(p)] for p in node.iter(W + 'p')] == record['paragraph_indices']
        if record['kind'] == 'table':
            rows = [[text(cell) for cell in row.findall(W + 'tc')] for row in node.findall(W + 'tr')]
            assert rows == record['table_rows']
            rendered = '\n'.join(' | '.join(row) for row in rows)
        else:
            assert node.tag == W + 'p'
            rendered = text(node)
        assert rendered == record['rendered_text']
    mapping = load(package / 'patch/existing_resolution_property_mapping6.json')
    blocks = load(package / 'source/formal_source_blocks_v2.json')
    assert len(mapping['fills']) == len(blocks['formal_agreement_groups']) == 6
    by_index = {r['body_child_index']: r for r in whole['records']}
    for fill, group in zip(mapping['fills'], blocks['formal_agreement_groups']):
        assert fill['resolutionId'] == group['resolutionId']
        assert re.fullmatch(r'Agreements?\s*:', text(body[group['marker']['body_child_index']]))
        for record in [group['marker'], *group['content_records'], group['end_boundary']['record']]:
            assert record == by_index[record['body_child_index']]
        rendered = '\n'.join(record['rendered_text'] for record in group['content_records'])
        assert rendered == group[KEY] == fill['new_properties'][KEY]
        assert fill['content_records'] == group['content_records']
        for record in group['content_records']:
            for tag in (W+'del', W+'moveFrom', W+'drawing', W+'object', W+'instrText', M+'oMath'):
                assert not list(body[record['body_child_index']].iter(tag)), (fill['resolutionId'], tag)
    assert mapping['fills'][3]['new_properties'][KEY] == text(paragraphs[456])
    assert blocks['separate_optional_working_assumption'][0]['marker']['paragraph_indices'] == [457]
    assert blocks['formal_group4_depends_on_neighboring_working_assumption'] is False
    assert 'Note: 2Tx carrier 2' in mapping['fills'][2]['new_properties'][KEY]
    assert 'Case 1 | 1 Tx' in mapping['fills'][4]['new_properties'][KEY]
    assert 'FFS:' in mapping['fills'][5]['new_properties'][KEY]
    assert sha(package / 'patch/formal_source_content6_add.ttl') == mapping['patch']['sha256']
    return mapping


def rebuild(package, manifest, mapping, base_sql, base_ttl, out):
    assert not out.exists(), 'choose a fresh isolated output directory'
    assert sha(base_sql) == manifest['baseline']['SQLite']['sha256']
    assert sha(base_ttl) == manifest['baseline']['RDF']['sha256']
    out.mkdir(parents=True)
    database, rdf = out / 'RAN1.sqlite', out / 'RAN1-UL-formal-source6-body.ttl'
    shutil.copy2(base_sql, database)
    c = sqlite3.connect(database.as_uri() + '?mode=rw', uri=True)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA cache_size=-8192')
    c.execute('PRAGMA temp_store=FILE')
    c.execute('PRAGMA threads=1')
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    columns = {t: [r[1] for r in c.execute('PRAGMA table_info(' + quote(t) + ')')] for t in tables}
    assert len(tables) == 89
    assert c.execute('SELECT count(*) FROM node').fetchone()[0] == 165418
    assert c.execute('SELECT count(*) FROM edge').fetchone()[0] == 848228
    expected = {}
    with c:
        for table in ('Agreement', 'Resolution'):
            assert KEY not in columns[table]
            c.execute('ALTER TABLE ' + quote(table) + ' ADD COLUMN ' + quote(KEY) + ' ANY')
        for fill in mapping['fills']:
            stored, = c.execute('SELECT * FROM _node_record WHERE source_iri=?', (fill['source_iri'],)).fetchall()
            props = json.loads(stored['properties_json'])
            assert props['resolutionId'] == fill['resolutionId'] and KEY not in props
            assert set(json.loads(stored['labels_json'])) == {'Agreement', 'Resolution'}
            node_id, value = stored['node_id'], fill['new_properties'][KEY]
            props[KEY] = value
            c.execute('UPDATE _node_record SET properties_json=? WHERE node_id=?', (canonical(props), node_id))
            c.execute('INSERT INTO node_property VALUES(?,?,?,?)', (node_id, KEY, 'string', canonical(value)))
            for table in ('Agreement', 'Resolution'):
                assert c.execute('UPDATE ' + quote(table) + ' SET ' + quote(KEY) + '=? WHERE node_id=?', (value, node_id)).rowcount == 1
            expected[node_id] = value
    c.execute('ATTACH DATABASE ? AS frozen', (base_sql.as_uri() + '?mode=ro&immutable=1',))
    preserved = {}
    for table in tables:
        fields = ','.join(map(quote, columns[table]))
        old = 'SELECT ' + fields + ' FROM frozen.' + quote(table)
        new = 'SELECT ' + fields + ' FROM main.' + quote(table)
        if table == '_node_record':
            new = "SELECT node_id,source_iri,labels_json,json_remove(properties_json,'$.formalSourceContentWithTables') AS properties_json FROM main._node_record"
        elif table == 'node_property':
            new += " WHERE key<>'formalSourceContentWithTables'"
        differences = [c.execute('SELECT count(*) FROM ('+a+' EXCEPT '+b+')').fetchone()[0] for a,b in ((old,new),(new,old))]
        old_n = c.execute('SELECT count(*) FROM ('+old+')').fetchone()[0]
        new_n = c.execute('SELECT count(*) FROM ('+new+')').fetchone()[0]
        assert differences == [0,0] and old_n == new_n, table
        preserved[table] = {'original_columns': columns[table], 'original_rows_n': old_n, 'normalized_new_rows_n': new_n, 'two_way_EXCEPT_n': differences}
    for table in ('Agreement', 'Resolution'):
        actual = {r['node_id']:r[KEY] for r in c.execute('SELECT node_id,'+quote(KEY)+' FROM '+quote(table)+' WHERE '+quote(KEY)+' IS NOT NULL')}
        assert actual == expected
    assert c.execute('SELECT count(*) FROM node_property WHERE key=?', (KEY,)).fetchone()[0] == 6
    sql = (package / 'patch/full_source6_query.sql').read_text()
    actual_records = [dict(r) for r in c.execute(sql)]
    gold = load(package / 'evaluation/reference_gold.jsonl')['records']
    assert sorted(map(canonical, actual_records)) == sorted(map(canonical, gold))
    assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    c.close()
    with rdf.open('wb') as dst, base_ttl.open('rb') as source:
        shutil.copyfileobj(source, dst)
        # The original UL materialization appended its delta with no extra byte.
        dst.write((package / 'patch/formal_source_content6_add.ttl').read_bytes())
    assert sha(rdf) == manifest['expected_rebuilt_RDF_sha256']
    assert sha(base_sql) == manifest['baseline']['SQLite']['sha256']
    assert sha(base_ttl) == manifest['baseline']['RDF']['sha256']
    result = {'status':'PASS_FRESH_ISOLATED_SOURCE6_ADDITIVE_REBUILD',
        'original89_all_columns_bidirectional_EXCEPT':preserved, 'full_six_source_strings_equal':True,
        'source_query_records_n':len(actual_records), 'new_nodes_n':0, 'new_edges_n':0,
        'new_properties_n':6, 'SQL_sha256':sha(database), 'RDF_sha256':sha(rdf),
        'baseline_unchanged':True, 'native_execution_n':0, 'model_API_calls_n':0}
    (out/'rebuild_receipt.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--base-sql', type=Path)
    parser.add_argument('--base-ttl', type=Path)
    parser.add_argument('--out-dir', type=Path)
    args = parser.parse_args()
    package = args.package.resolve()
    manifest = load(package/'manifest.json')
    mapping = verify_source(package, manifest)
    result = {'status':'PASS_AUTHENTIC_WHOLE6017_PARAGRAPH_REPORT_AND_SIX_FORMAL_BODIES',
        'formal_groups_n':6, 'whole_report_paragraphs_n':6017, 'source_variant_only':True,
        'new_native_or_model_calls_n':0}
    if any((args.base_sql,args.base_ttl,args.out_dir)):
        assert all((args.base_sql,args.base_ttl,args.out_dir))
        result['isolated_rebuild'] = rebuild(package,manifest,mapping,args.base_sql.resolve(),args.base_ttl.resolve(),args.out_dir.resolve())
    print(json.dumps(result, ensure_ascii=False))
