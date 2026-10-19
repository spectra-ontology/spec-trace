#!/usr/bin/env python3
"""Serialize a whole released graph into a separately named lexical corpus.

The only fact input is the supplied TTL. A pinned released lexical parser is
code, not a second fact source. There is no task, query, answer, prefix, raw
cover, repair-delta or positive-ID input. Every node property and directed edge
is preserved. Build and verify operate only on newly named SQLite FTS files.
"""
from collections import Counter, defaultdict
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import resource
import sqlite3
import sys
import time

sys.dont_write_bytecode = True
CHARS = 4000
OVERLAP = 200
ENDPOINT_SCALAR_CHARS = 256
LEXER_SHA = '9499ac120ea4fcf1c2707f6e3151e399530d9b4f43f5aec9d2d93040792d6e25'
PROTOCOL = {
    'experiment': 'Separate full-graph source cohort; not the historical Qdrant-text cohort',
    'fact_input': 'All instance subjects, labels, literal properties and directed instance-to-instance relationships in the one pinned whole TTL',
    'ordering': 'Node IRI ascending; property keys/labels ascending; outgoing edges by relationship name then target IRI ascending',
    'serialization': 'A canonical JSON node fact followed by one canonical JSON directed-edge fact per outgoing edge, separated by newlines',
    'endpoint_metadata': 'IRI and all labels, plus every scalar property whose canonical JSON representation has at most 256 Unicode characters; no property-name or node whitelist',
    'all_properties_retained': 'Every property, irrespective of size/type, occurs unabridged in its own node fact. Endpoint metadata is redundant context only.',
    'chunk_characters': CHARS,
    'overlap_characters': OVERLAP,
    'chunk_rule': 'Contiguous Unicode-code-point windows [start,min(start+4000,length)); next start=end-200; stop at end=length; no gaps or text normalization',
    'point_identity': 'sha256(original_node_IRI UTF-8), colon, zero-based chunk ordinal padded to eight digits',
    'engine': 'SQLite FTS5 BM25; unicode61 remove_diacritics 2; text-only lexical index',
    'ranking_candidates_per_round': 160,
    'final_context_documents': 12,
    'characters_per_formatted_document': 4000,
    'total_context_characters': 48000,
    'search_wall_seconds': 15,
    'search_vm_instruction_cap': 20000000,
    'sqlite_cache_mib': 32,
    'sqlite_threads': 1,
    'sqlite_mmap_bytes': 0,
    'retrieval_or_model_run': False,
    'historical_text_corpus_reused': False,
    'fact_equality_is_not_retrieval_completeness': True,
    'repeated_subject_policy': 'Union labels and directed edges; merge disjoint properties and exact canonical-JSON equal repeated property values; reject conflicting values including bool/integer confusion. Never create auxiliary subjects.',
    'provider_tokens_or_cost': 'Not measured; exact characters and UTF-8 bytes only',
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def load_lexer(path):
    assert sha(path) == LEXER_SHA, 'Released parser pin mismatch'
    spec = importlib.util.spec_from_file_location('corpus_pinned_released_lexer', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_graph(ttl, lexer):
    records, edges = {}, set()
    with Path(ttl).open(encoding='utf-8', newline='') as stream:
        for statement in lexer.StatementReader(stream):
            parsed = lexer.parse_statement(statement)
            if parsed is None:
                continue
            iri, predicates = parsed
            if not lexer.INST_RE.match(iri):
                continue
            existing = records.get(iri, {'iri':iri,'labels':[],'properties':{}})
            labels, properties = set(existing['labels']), dict(existing['properties'])
            for (prefix, name), objects in predicates:
                if (prefix, name) == ('rdf', 'type'):
                    assert all(kind == 'pname' and value[0] == 'spectra' for kind, value in objects)
                    labels.update(value[1] for kind, value in objects)
                elif prefix == 'spectra':
                    literals = [value for kind, value in objects if kind == 'lit']
                    if literals:
                        value = literals[0] if len(literals) == 1 else sorted(map(str, literals))
                        if name in properties:
                            assert canonical(properties[name]) == canonical(value), 'Conflicting repeated property: ' + iri + ' / ' + name
                        else:
                            properties[name] = value
                    for kind, target in objects:
                        if kind == 'iri':
                            assert lexer.INST_RE.match(target), 'Unexpected non-instance relationship'
                            edges.add((iri, lexer.decode_rel_type(name), target))
                        else:
                            assert kind == 'lit', 'Unexpected property object'
                else:
                    raise AssertionError('Unrepresented instance predicate ' + prefix + ':' + name)
            records[iri] = {'iri': iri, 'labels': sorted(labels), 'properties': properties}
    assert records
    assert all(source in records and target in records for source, _, target in edges)
    return records, edges


def endpoint(record):
    props = {key: value for key, value in record['properties'].items()
             if not isinstance(value, (list, dict)) and len(canonical(value)) <= ENDPOINT_SCALAR_CHARS}
    return {'iri': record['iri'], 'labels': record['labels'], 'identity_context': props}


def serialize_node(record, outgoing, endpoints):
    facts = [canonical({'record_type': 'node', **record})]
    facts.extend(canonical({'record_type': 'directed_edge', 'source': endpoints[record['iri']],
                            'relationship': relationship, 'target': endpoints[target]})
                 for relationship, target in outgoing)
    return '\n'.join(facts) + '\n'


def chunks(text):
    start, ordinal = 0, 0
    while True:
        end = min(start + CHARS, len(text))
        yield ordinal, start, end, text[start:end]
        if end == len(text):
            return
        start = end - OVERLAP
        ordinal += 1


def graph_inventory(records, edges):
    return {'nodes': len(records), 'edges': len(edges),
            'labels': dict(sorted(Counter(label for row in records.values() for label in row['labels']).items())),
            'relationships': dict(sorted(Counter(rel for _, rel, _ in edges).items())),
            'node_records_sha256': digest([records[iri] for iri in sorted(records)]),
            'directed_edges_sha256': digest(sorted(edges))}


def build(args):
    began = time.monotonic()
    assert sha(args.ttl) == args.ttl_sha256
    assert not args.output.exists(), 'Output directory already exists'
    args.output.mkdir(parents=True)
    write_new(args.output / 'protocol.json', PROTOCOL)
    lexer = load_lexer(args.lexer)
    records, edges = read_graph(args.ttl, lexer)
    inventory = graph_inventory(records, edges)
    print(canonical({'phase': 'all_TTL_facts_parsed', **{k: inventory[k] for k in ('nodes','edges')}}), flush=True)
    outgoing = defaultdict(list)
    for source, rel, target in sorted(edges):
        outgoing[source].append((rel, target))
    endpoints = {iri: endpoint(record) for iri, record in records.items()}
    groups = {lexer.INST_RE.match(iri).group('wg') for iri in records}
    assert len(groups) == 1, 'One WG per supplied whole TTL'
    group = next(iter(groups))
    db = args.output / (group.lower() + '.sqlite3')
    connection = sqlite3.connect(db)
    connection.execute('PRAGMA page_size=4096')
    connection.execute('PRAGMA journal_mode=DELETE')
    connection.execute('PRAGMA synchronous=OFF')
    connection.execute('PRAGMA cache_size=-32768')
    connection.execute('PRAGMA temp_store=FILE')
    connection.execute('PRAGMA threads=1')
    connection.execute('CREATE TABLE docs(id INTEGER PRIMARY KEY, collection TEXT NOT NULL, point_id TEXT NOT NULL, chunk_id TEXT NOT NULL, metadata TEXT NOT NULL, text TEXT NOT NULL)')
    connection.execute('CREATE UNIQUE INDEX docs_identity ON docs(collection,point_id)')
    connection.execute('CREATE TABLE graph_nodes(iri TEXT PRIMARY KEY, labels TEXT NOT NULL, properties TEXT NOT NULL, whole_text_characters INTEGER NOT NULL, whole_text_sha256 TEXT NOT NULL, chunk_count INTEGER NOT NULL) WITHOUT ROWID')
    count = total_chars = total_bytes = source_chars = source_bytes = 0
    longest = 0
    for position, iri in enumerate(sorted(records), 1):
        record = records[iri]
        text = serialize_node(record, outgoing[iri], endpoints)
        identity = hashlib.sha256(iri.encode()).hexdigest()
        rows = []
        for ordinal, start, end, payload in chunks(text):
            point = identity + ':' + f'{ordinal:08d}'
            metadata = {**endpoints[iri]['identity_context'], 'source': iri, 'node_iri': iri,
                        'labels': record['labels'], 'chunk_ordinal': ordinal,
                        'node_text_start_character_0_based': start,
                        'node_text_end_character_0_based_exclusive': end,
                        'whole_node_text_characters': len(text)}
            rows.append((group.lower() + '_whole_graph_nodes', point, iri + '#' + f'{ordinal:08d}',
                         canonical(metadata), payload))
            count += 1
            total_chars += len(payload)
            total_bytes += len(payload.encode())
        longest = max(longest, len(rows))
        source_chars += len(text)
        source_bytes += len(text.encode())
        connection.executemany('INSERT INTO docs(collection,point_id,chunk_id,metadata,text) VALUES(?,?,?,?,?)', rows)
        connection.execute('INSERT INTO graph_nodes VALUES(?,?,?,?,?,?)',
                           (iri, canonical(record['labels']), canonical(record['properties']), len(text),
                            hashlib.sha256(text.encode()).hexdigest(), len(rows)))
        if position % 5000 == 0:
            connection.commit()
            print(canonical({'phase': 'all_node_serialization', 'nodes_done': position, 'chunks': count}), flush=True)
    connection.commit()
    connection.execute("CREATE VIRTUAL TABLE search USING fts5(text, content='docs', content_rowid='id', tokenize='unicode61 remove_diacritics 2')")
    print(canonical({'phase': 'FTS_full_rebuild', 'chunks': count}), flush=True)
    connection.execute("INSERT INTO search(search) VALUES('rebuild')")
    connection.execute("INSERT INTO search(search,rank) VALUES('integrity-check',1)")
    connection.commit()
    assert connection.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
    connection.close()
    assert sha(args.ttl) == args.ttl_sha256, 'Source changed during build'
    receipt = {'status': 'BUILT_NOT_MODEL_EVALUATED', 'fact_source_sha256': args.ttl_sha256,
               'lexer_sha256': LEXER_SHA, 'protocol_sha256': digest(PROTOCOL), 'inventory': inventory,
               'chunks': count, 'max_chunks_for_one_node': longest,
               'node_text_characters_without_overlap': source_chars,
               'node_text_UTF8_bytes_without_overlap': source_bytes,
               'stored_chunk_characters_with_overlap': total_chars,
               'stored_chunk_UTF8_bytes_with_overlap': total_bytes,
               'database': {'filename': db.name, 'sha256': sha(db), 'bytes': db.stat().st_size},
               'elapsed_seconds': time.monotonic() - began,
               'peak_RSS_KiB': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'fact_selection_query_or_answer_inputs': [], 'raw_covers_or_prefix_fixtures_used': False,
               'model_API_native_calls': 0, 'public_or_operational_graph_mutations': 0,
               'new_FTS_database_write_only': True}
    write_new(args.output / 'build_receipt.json', receipt)
    print(canonical(receipt), flush=True)


def verify(args):
    began = time.monotonic()
    assert sha(args.ttl) == args.ttl_sha256
    build_receipt = json.loads((args.output / 'build_receipt.json').read_text())
    assert build_receipt['fact_source_sha256'] == args.ttl_sha256
    assert json.loads((args.output / 'protocol.json').read_text()) == PROTOCOL
    assert build_receipt['protocol_sha256'] == digest(PROTOCOL)
    db = args.output / build_receipt['database']['filename']
    assert sha(db) == build_receipt['database']['sha256']
    records, edges = read_graph(args.ttl, load_lexer(args.lexer))
    assert graph_inventory(records, edges) == build_receipt['inventory']
    connection = sqlite3.connect(db.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    connection.execute('PRAGMA query_only=ON')
    connection.execute('PRAGMA cache_size=-32768')
    seen_nodes, seen_edges, seen_docs = {}, set(), 0
    collection = connection.execute('SELECT DISTINCT collection FROM docs').fetchall()
    assert len(collection) == 1
    collection = collection[0][0]
    for iri, labels, properties, chars, text_sha, number in connection.execute('SELECT iri,labels,properties,whole_text_characters,whole_text_sha256,chunk_count FROM graph_nodes ORDER BY iri'):
        assert {'iri': iri, 'labels': json.loads(labels), 'properties': json.loads(properties)} == records[iri]
        texts, previous_end = [], 0
        identity = hashlib.sha256(iri.encode()).hexdigest()
        rows = connection.execute('SELECT point_id,chunk_id,metadata,text FROM docs WHERE collection=? AND point_id>=? AND point_id<? ORDER BY point_id',
                                  (collection, identity+':', identity+';')).fetchall()
        assert len(rows) == number
        for ordinal, (point, chunk_id, meta, payload) in enumerate(rows):
            metadata = json.loads(meta)
            start = metadata['node_text_start_character_0_based']
            end = metadata['node_text_end_character_0_based_exclusive']
            assert point == identity+':'+f'{ordinal:08d}' and chunk_id == iri+'#'+f'{ordinal:08d}'
            assert metadata['node_iri'] == iri and metadata['chunk_ordinal'] == ordinal
            assert end - start == len(payload) <= CHARS
            assert start == (0 if ordinal == 0 else previous_end - OVERLAP)
            if ordinal:
                assert texts[-1][-OVERLAP:] == payload[:OVERLAP]
            texts.append(payload if ordinal == 0 else payload[OVERLAP:])
            previous_end = end
            seen_docs += 1
        text = ''.join(texts)
        assert len(text) == chars == previous_end and hashlib.sha256(text.encode()).hexdigest() == text_sha
        facts = [json.loads(line) for line in text.splitlines()]
        assert facts[0] == {'record_type': 'node', **records[iri]}
        seen_nodes[iri] = {key: facts[0][key] for key in ('iri','labels','properties')}
        for fact in facts[1:]:
            assert set(fact) == {'record_type','source','relationship','target'} and fact['record_type'] == 'directed_edge'
            source, target = fact['source']['iri'], fact['target']['iri']
            assert source == iri
            assert fact['source'] == endpoint(records[source]) and fact['target'] == endpoint(records[target])
            triple = (source, fact['relationship'], target)
            assert triple not in seen_edges
            seen_edges.add(triple)
        if len(seen_nodes) % 10000 == 0:
            print(canonical({'phase':'full_corpus_reverse_reconstruction','nodes_done':len(seen_nodes),'edges_done':len(seen_edges)}),flush=True)
    assert seen_nodes == records and seen_edges == edges
    assert seen_docs == connection.execute('SELECT count(*) FROM docs').fetchone()[0] == build_receipt['chunks']
    assert connection.execute('SELECT count(*) FROM search').fetchone()[0] == seen_docs
    assert connection.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
    connection.close()
    assert sha(db) == build_receipt['database']['sha256'] and sha(args.ttl) == args.ttl_sha256
    receipt = {'status':'PASS','every_TTL_node_label_property_equal':True,'every_directed_TTL_edge_equal':True,
               'nodes_reconstructed':len(seen_nodes),'edges_reconstructed':len(seen_edges),'chunks_reconstructed':seen_docs,
               'all_chunk_overlaps_and_full_text_SHA_replayed':True,'no_missing_or_added_node_or_edge':True,
               'FTS_integrity_and_row_population_equal':True,'immutable_database_sha256':sha(db),
               'fact_source_sha256':args.ttl_sha256,'protocol_sha256':digest(PROTOCOL),
               'elapsed_seconds':time.monotonic()-began,'peak_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'model_API_native_calls':0,'public_or_operational_graph_mutations':0}
    write_new(args.output / 'all_fact_reconstruction_receipt.json',receipt)
    print(canonical(receipt),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('build','verify'))
    parser.add_argument('--ttl',type=Path,required=True)
    parser.add_argument('--ttl-sha256',required=True)
    parser.add_argument('--lexer',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    (build if args.mode=='build' else verify)(args)


if __name__=='__main__':
    main()
