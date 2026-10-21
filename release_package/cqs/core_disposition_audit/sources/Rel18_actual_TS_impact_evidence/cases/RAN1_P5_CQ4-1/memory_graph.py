"""Rebuild retained typed SQLite tables and exact raw-node provenance in memory."""
import json,re,sqlite3
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
    c.execute('CREATE TABLE node(node_id INTEGER PRIMARY KEY,labels TEXT)')
    for nid,r in records.items():
        c.execute('INSERT INTO node VALUES(?,?)',(nid,json.dumps(r['labels'],separators=(',',':'))))
    c.execute('CREATE TABLE _node_record(node_id INTEGER PRIMARY KEY,source_iri TEXT,labels_json TEXT,properties_json TEXT)')
    c.executemany('INSERT INTO _node_record VALUES(?,?,?,?)', [[r[k] for k in ['node_id','source_iri','labels_json','properties_json']] for r in slice_data['records']])
    return c, records
