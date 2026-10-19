#!/usr/bin/env python3
"""Build a separate SQLite encoding of the exact shipped graph restoration.

Reuses the shipped Turtle lexer, statement parser and relationship-name codec.
The information equality checked here is to that frozen Neo4j restoration,
including its documented multiple-literal list codec, not to an arbitrary RDF
interpretation or to a live graph. Existing relational databases are untouched.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sqlite3
import time


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def quoted(name):
    return '"' + name.replace('"', '""') + '"'


def native_type(value):
    return {type(None): 'null', bool: 'boolean', int: 'integer', float: 'number',
            str: 'string', list: 'array', dict: 'object'}[type(value)]


def encode(value):
    if type(value) in {list, dict}:
        return canonical(value)
    if type(value) is bool:
        return int(value)
    return value


def parser_module(path):
    spec = importlib.util.spec_from_file_location('frozen_sqlite_shipped_parser', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build(ttl, output, loader_path, expected_source_sha=None, expected_inventory=None):
    ttl, output, loader_path = map(Path, (ttl, output, loader_path))
    if output.exists() or output.with_suffix('.manifest.json').exists():
        raise ValueError('refusing to overwrite an existing database or manifest')
    source_sha = sha(ttl)
    if expected_source_sha and source_sha != expected_source_sha:
        raise ValueError('TTL differs from pinned frozen graph schema source')
    parser = parser_module(loader_path)
    started = time.monotonic()
    output.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(output)
    con.executescript('''PRAGMA journal_mode=DELETE; PRAGMA synchronous=NORMAL;
      PRAGMA cache_size=-65536; PRAGMA temp_store=FILE;
      CREATE TABLE _node_record(node_id INTEGER PRIMARY KEY,source_iri TEXT UNIQUE NOT NULL,
        labels_json TEXT NOT NULL,properties_json TEXT NOT NULL) STRICT;
      CREATE TABLE _edge_staging(src_iri TEXT NOT NULL,rel_type TEXT NOT NULL,dst_iri TEXT NOT NULL,
        PRIMARY KEY(src_iri,rel_type,dst_iri)) WITHOUT ROWID, STRICT;
      CREATE TABLE node(node_id INTEGER PRIMARY KEY,labels TEXT NOT NULL) STRICT;
      CREATE TABLE node_label(node_id INTEGER NOT NULL,label TEXT NOT NULL,
        PRIMARY KEY(node_id,label)) WITHOUT ROWID, STRICT;
      CREATE TABLE node_property(node_id INTEGER NOT NULL,key TEXT NOT NULL,native_type TEXT NOT NULL,
        value_json TEXT NOT NULL,PRIMARY KEY(node_id,key)) WITHOUT ROWID, STRICT;
      CREATE TABLE edge(edge_id INTEGER PRIMARY KEY,src_id INTEGER NOT NULL,
        rel_type TEXT NOT NULL,dst_id INTEGER NOT NULL,UNIQUE(src_id,rel_type,dst_id)) STRICT;''')
    label_fields, property_types = {}, {}
    raw_edge_count = 0
    statements = skipped = nodes = 0
    source_records_hash = hashlib.sha256()
    try:
        with ttl.open(encoding='utf-8') as stream:
            for statement in parser.StatementReader(stream):
                parsed = parser.parse_statement(statement)
                if parsed is None:
                    continue
                statements += 1
                iri, predicates = parsed
                if not parser.INST_RE.match(iri):
                    skipped += 1
                    continue
                labels, properties = set(), {}
                for (prefix, name), objects in predicates:
                    if prefix == 'rdf' and name == 'type':
                        labels.update(value[1] for kind, value in objects
                                      if kind == 'pname' and value[0] == 'spectra')
                        continue
                    if prefix != 'spectra':
                        continue
                    literals = [value for kind, value in objects if kind == 'lit']
                    if literals:
                        value = literals[0] if len(literals) == 1 else sorted(map(str, literals))
                        if name in properties and properties[name] != value:
                            raise ValueError('conflicting property within source statement')
                        properties[name] = value
                    for kind, target in objects:
                        if kind != 'iri' or not parser.INST_RE.match(target):
                            continue
                        rel_type = parser.decode_rel_type(name)
                        raw_edge_count += 1
                        con.execute('INSERT OR IGNORE INTO _edge_staging VALUES(?,?,?)',
                                    (iri, rel_type, target))
                # Shipped regular source serializes each node once. Refuse to
                # silently overwrite/merge unexpected duplicate subject blocks.
                labels = sorted(labels)
                labels_json, properties_json = canonical(labels), canonical(properties)
                cur = con.execute('INSERT INTO _node_record(source_iri,labels_json,properties_json) VALUES(?,?,?)',
                                  (iri, labels_json, properties_json))
                node_id = cur.lastrowid
                con.execute('INSERT INTO node VALUES(?,?)', (node_id, labels_json))
                con.executemany('INSERT INTO node_label VALUES(?,?)', [(node_id, label) for label in labels])
                con.executemany('INSERT INTO node_property VALUES(?,?,?,?)',
                                [(node_id, key, native_type(value), canonical(value)) for key, value in properties.items()])
                for label in labels:
                    label_fields.setdefault(label, set()).update(properties)
                    for key, value in properties.items():
                        property_types.setdefault((label, key), set()).add(native_type(value))
                source_records_hash.update((canonical([iri, labels, properties]) + '\n').encode())
                nodes += 1
                if nodes % 2000 == 0:
                    con.commit()
                if nodes % 20000 == 0:
                    print(canonical({'status': 'parsing', 'wg': ttl.stem, 'nodes': nodes,
                                     'elapsed_s': round(time.monotonic()-started, 2)}), flush=True)
        con.commit()
        dangling = con.execute('''SELECT count(*) FROM _edge_staging e
          LEFT JOIN _node_record s ON s.source_iri=e.src_iri
          LEFT JOIN _node_record d ON d.source_iri=e.dst_iri
          WHERE s.node_id IS NULL OR d.node_id IS NULL''').fetchone()[0]
        if dangling:
            raise ValueError('source has missing relationship endpoints')
        con.execute('''INSERT INTO edge(src_id,rel_type,dst_id)
          SELECT s.node_id,e.rel_type,d.node_id FROM _edge_staging e
          JOIN _node_record s ON s.source_iri=e.src_iri
          JOIN _node_record d ON d.source_iri=e.dst_iri
          ORDER BY s.node_id,e.rel_type,d.node_id''')
        edges = con.execute('SELECT count(*) FROM edge').fetchone()[0]
        if expected_inventory and (nodes, edges) != tuple(expected_inventory):
            raise ValueError('SQL inventory differs from frozen restored graph inventory')
        for label, keys in sorted(label_fields.items()):
            keys = sorted(keys)
            con.execute('CREATE TABLE ' + quoted(label) + '(node_id INTEGER PRIMARY KEY'
                        + ''.join(',' + quoted(key) + ' ANY' for key in keys) + ') STRICT')
            insert = 'INSERT INTO ' + quoted(label) + ' VALUES(' + ','.join('?' for _ in range(len(keys)+1)) + ')'
            reader = con.execute('''SELECT r.node_id,r.properties_json FROM _node_record r
               JOIN node_label l USING(node_id) WHERE l.label=? ORDER BY r.node_id''', (label,))
            for node_id, properties_json in reader:
                properties = json.loads(properties_json)
                con.execute(insert, [node_id] + [encode(properties.get(key)) for key in keys])
            for key in keys:
                if key.lower().endswith(('id', 'number', 'name', 'release', 'status', 'code')):
                    con.execute('CREATE INDEX ' + quoted('idx_'+label+'_'+key) + ' ON ' + quoted(label)
                                + '(' + quoted(key) + ')')
        rel_counts = dict(con.execute('SELECT rel_type,count(*) FROM edge GROUP BY rel_type'))
        for rel_type in sorted(rel_counts):
            table = quoted('rel_' + rel_type)
            con.execute('CREATE TABLE ' + table + '(edge_id INTEGER PRIMARY KEY,src_id INTEGER NOT NULL,dst_id INTEGER NOT NULL) STRICT')
            con.execute('INSERT INTO ' + table + ' SELECT edge_id,src_id,dst_id FROM edge WHERE rel_type=?', (rel_type,))
            con.execute('CREATE INDEX ' + quoted('idx_'+rel_type+'_src') + ' ON ' + table + '(src_id)')
            con.execute('CREATE INDEX ' + quoted('idx_'+rel_type+'_dst') + ' ON ' + table + '(dst_id)')
        con.commit()
        # Read every encoded property back, checking the wide SQL codec and
        # canonical type registry against the original parsed native values.
        reread_hash = hashlib.sha256()
        values_checked = 0
        for node_id, iri, labels_json, properties_json in con.execute('SELECT * FROM _node_record ORDER BY node_id'):
            labels, original = json.loads(labels_json), json.loads(properties_json)
            registry = {key: json.loads(value) for key, value in con.execute(
                'SELECT key,value_json FROM node_property WHERE node_id=?', (node_id,))}
            if canonical(registry) != canonical(original):
                raise ValueError('canonical property registry mismatch')
            for label in labels:
                keys = sorted(label_fields[label])
                row = con.execute('SELECT * FROM '+quoted(label)+' WHERE node_id=?', (node_id,)).fetchone()
                if row != tuple([node_id]+[encode(original.get(key)) for key in keys]):
                    raise ValueError('wide property value/type mismatch')
                # STRICT ANY must preserve strings and numeric native storage.
                types = con.execute('SELECT '+','.join('typeof('+quoted(key)+')' for key in keys)
                                    +' FROM '+quoted(label)+' WHERE node_id=?', (node_id,)).fetchone() if keys else ()
                for key, storage in zip(keys, types):
                    value = original.get(key)
                    expected = ('null' if value is None else 'integer' if type(value) in {int, bool}
                                else 'real' if type(value) is float else 'text')
                    if storage != expected:
                        raise ValueError('wide SQLite native storage type mismatch')
                    values_checked += 1
            reread_hash.update((canonical([iri, labels, registry])+'\n').encode())
        if reread_hash.digest() != source_records_hash.digest():
            raise ValueError('complete source record hash mismatch')
        edge_hash = hashlib.sha256()
        sql_edge_hash = hashlib.sha256()
        for row in con.execute('SELECT * FROM _edge_staging ORDER BY src_iri,rel_type,dst_iri'):
            edge_hash.update((canonical(row)+'\n').encode())
        for row in con.execute('''SELECT s.source_iri,e.rel_type,d.source_iri FROM edge e
              JOIN _node_record s ON s.node_id=e.src_id JOIN _node_record d ON d.node_id=e.dst_id
              ORDER BY s.source_iri,e.rel_type,d.source_iri'''):
            sql_edge_hash.update((canonical(row)+'\n').encode())
        if edge_hash.digest() != sql_edge_hash.digest():
            raise ValueError('complete directed relationship hash mismatch')
        con.execute('DROP TABLE _edge_staging')
        con.execute('CREATE INDEX idx_edge_src ON edge(src_id,rel_type)')
        con.execute('CREATE INDEX idx_edge_dst ON edge(dst_id,rel_type)')
        con.commit()
        if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('SQLite integrity check failed')
        labels_counts = dict(con.execute('SELECT label,count(*) FROM node_label GROUP BY label'))
        triples = [list(r) for r in con.execute('''SELECT DISTINCT a.label,e.rel_type,b.label FROM edge e
             JOIN node_label a ON a.node_id=e.src_id JOIN node_label b ON b.node_id=e.dst_id
             ORDER BY a.label,e.rel_type,b.label''')]
        con.close()
        if sha(ttl) != source_sha:
            raise ValueError('source changed during construction')
        schema = {'node_identity': 'node_id INTEGER; same entity shares node_id across every label table',
                  'node': {'node_id': 'integer', 'labels': 'JSON string array'},
                  'node_label': {'node_id': 'integer', 'label': 'string'},
                  'node_property': {'node_id': 'integer', 'key': 'string', 'native_type': 'string',
                                    'value_json': 'canonical JSON preserving null/bool/number/string/array/object'},
                  'edge': {'edge_id':'integer','src_id':'integer','rel_type':'string','dst_id':'integer'},
                  'label_tables': {label: {'node_id':['integer'], **{key: sorted(property_types[(label,key)])
                                     for key in sorted(keys)}} for label,keys in sorted(label_fields.items())},
                  'relationship_tables': {rel: ['edge_id','src_id','dst_id'] for rel in sorted(rel_counts)},
                  'directed_relationships': triples,
                  'value_codec': 'STRICT ANY columns preserve native string/integer/real storage. Booleans are 0/1; arrays/objects canonical JSON text. Absent properties are SQL NULL; node_property distinguishes stored null from absence. Nested JSON outputs use SQLite JSON functions. Private _ tables are inaccessible.',
                  'source_values_or_population_counts_in_schema': False}
        manifest = {'status':'complete_record_value_and_inventory_match', 'source':{'path':str(ttl.resolve()),
                     'sha256':source_sha,'bytes':ttl.stat().st_size}, 'db_sha256':sha(output),
                    'db_bytes':output.stat().st_size,'loader_sha256':sha(loader_path),'builder_sha256':sha(__file__),
                    'nodes':nodes,'relationships':edges,'raw_relationship_occurrences':raw_edge_count,
                    'identical_directed_edges_collapsed':raw_edge_count-edges,
                    'parallel_edge_policy':'Identical (source,predicate,target) triples collapse exactly as shipped Neo4j restoration; distinct predicates/targets remain distinct. This does not reconstruct multiplicity absent from the released RDF.',
                    'labels':labels_counts,'relationship_counts':rel_counts,
                    'complete_native_record_sha256':source_records_hash.hexdigest(),
                    'complete_sql_record_sha256':reread_hash.hexdigest(),
                    'complete_source_edge_sha256':edge_hash.hexdigest(),
                    'complete_sql_edge_sha256':sql_edge_hash.hexdigest(),
                    'wide_values_storage_types_checked':values_checked,'missing_endpoints':dangling,
                    'statements':statements,'skipped_non_instance_subjects':skipped,
                    'schema':schema,'elapsed_s':round(time.monotonic()-started,3),
                    'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    'claims_scope':'Equivalence to the exact frozen shipped graph restoration projection, not live graph or causal equality of representations.'}
        output.with_suffix('.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        return manifest
    except BaseException:
        con.close()
        # Preserve failed partial output for diagnosis; it cannot be admitted.
        raise


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ttl',required=True,type=Path);ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--loader',required=True,type=Path);ap.add_argument('--schema',required=True,type=Path)
    args=ap.parse_args();wg=args.ttl.name.split('-')[0]
    schema=json.loads(args.schema.read_text())['working_groups'][wg]
    inventories={'RAN1':(165418,848228),'RAN2':(156288,939037),'RAN3':(87980,481498),
                 'RAN4':(342161,1592845),'RAN5':(215012,1047242)}
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    import os
    if hasattr(os,'sched_getaffinity'):
        os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    report=build(args.ttl,args.output,args.loader,schema['source_sha256'],inventories[wg])
    print(canonical({key:report[key] for key in ('status','nodes','relationships','elapsed_s','max_rss_kib')}),flush=True)


if __name__=='__main__':
    main()
