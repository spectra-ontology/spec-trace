#!/usr/bin/env python3
"""Relocatable source-enriched full-graph materialization recipe.

Functions named in function_lineage.json retain the reviewed original bodies.
The portable command glue receives explicit immutable baseline paths. No API,
network or Neo4j operation is implemented. SQLite clone mode is an explicit
separate materialization action; default verification does not open a DB.
"""
from collections import Counter
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import argparse
import ast
import hashlib
import importlib.util
import json
import re
import shutil
import sqlite3
import sys
sys.dont_write_bytecode = True
BUNDLE = Path(__file__).resolve().parents[1]
HERE = BUNDLE / 'authority'
PACKET = BUNDLE / 'source'
BASE_TTL_SHA = 'd9791c08773a0e38b89869b3882d3098d879a37ddd7109630c346200d6776e95'
BASE_DB_SHA = 'ff55fe57ee9435c25b59e1d90c5ee09ee0ff167696c4afeb05f21e367f4c6a29'
FULL_TTL_SHA = '5fac3bb2adf9f8ea5ac632700a9bebaf9c753c90e388783f82ad10c6dface589'
PREDICATES = {'core': 'affectsCoreSpec', 'test': 'affectsTestSpec', 'om': 'affectsOmSpec'}
RELATIONS = {'core': 'AFFECTS_CORE_SPEC', 'test': 'AFFECTS_TEST_SPEC', 'om': 'AFFECTS_OM_SPEC'}
SQL = 'SELECT c."tdocNumber",c."summaryOfChange"\nFROM "Spec" AS s\nJOIN edge AS e ON e.dst_id=s.node_id\n  AND e.rel_type IN (\'AFFECTS_CORE_SPEC\',\'AFFECTS_TEST_SPEC\',\'AFFECTS_OM_SPEC\')\nJOIN "CR" AS c ON c.node_id=e.src_id\nWHERE s."specNumber"=\'38.473\'\nORDER BY c."tdocNumber" COLLATE BINARY DESC LIMIT 10'


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def raw_sha(raw):
    return hashlib.sha256(raw).hexdigest()

def save(path, value):
    assert not path.exists(), f'Refusing overwrite: {path}'
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def read_full_base(ttl, parser):
    """Read every label/property and directed edge; never call parse_ttl/native."""
    records, edges, statement_hashes = {}, set(), {}
    with ttl.open(encoding='utf-8', newline='') as stream:
        for statement in parser.StatementReader(stream):
            parsed = parser.parse_statement(statement)
            if parsed is None:
                continue
            iri, predicates = parsed
            if not parser.INST_RE.match(iri):
                continue
            assert iri not in records, 'Duplicate subject would violate SQLite base restoration'
            labels, properties = set(), {}
            for (prefix, name), objects in predicates:
                if (prefix, name) == ('rdf', 'type'):
                    labels.update(v[1] for kind, v in objects if kind == 'pname' and v[0] == 'spectra')
                elif prefix == 'spectra':
                    literals = [v for kind, v in objects if kind == 'lit']
                    if literals:
                        assert name not in properties
                        properties[name] = literals[0] if len(literals) == 1 else sorted(map(str, literals))
                    for kind, target in objects:
                        if kind == 'iri' and parser.INST_RE.match(target):
                            edges.add((iri, parser.decode_rel_type(name), target))
            records[iri] = {'labels': sorted(labels), 'properties': properties}
            statement_hashes[iri] = raw_sha(statement.encode())
    return records, edges, statement_hashes

def derive_source_delta(source_root, records, edges, own_parser):
    observation_packet = json.loads((PACKET / 'actual_all38_original_own_cover_observations.json').read_text())
    observations = observation_packet['observations']
    for archive, pin in observation_packet['archives'].items():
        path = source_root / archive
        assert path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256']
    cr_records = {iri: row for iri, row in records.items() if 'CR' in row['labels']}
    ids = [row['properties']['tdocNumber'] for row in cr_records.values()]
    assert len(ids) == len(set(ids)) == 19974
    spec_iris = {}
    for iri, row in records.items():
        if 'Spec' in row['labels']:
            spec_iris.setdefault(row['properties'].get('specNumber'), []).append(iri)
    generator_ast = ast.parse((HERE / 'original_JSONLD_generator_INDEX.py').read_text())
    function = next(node for node in generator_ast.body if isinstance(node, ast.FunctionDef) and node.name == 'spec_uri')
    generator_namespace = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), '<indexed spec_uri only>', 'exec'), generator_namespace)
    spec_uri = generator_namespace['spec_uri']
    canonical_spec_iris = {number: [iri for iri in iris
                                   if records[iri]['properties'].get('specRelease') is None]
                           for number, iris in spec_iris.items()}
    byid = {row['properties']['tdocNumber']: iri for iri, row in cr_records.items()}
    source_ids = {row['tdocNumber'] for row in observations}
    prior = json.loads((PACKET / 'actual_frozen_universe_tail_receipt.json').read_text())
    bound = prior['tail_bound']
    tail_ids = {ident for ident in ids if ident >= bound}
    assert source_ids == tail_ids and len(tail_ids) == 38
    source_role_edges, source_pins = set(), []
    role_field_n = 0
    for row in observations:
        ident = row['tdocNumber']
        iri = byid[ident]
        assert row['frozen_subject'] == iri
        archive = source_root / row['archive']
        with ZipFile(archive) as package:
            member = package.read(row['member'])
        assert raw_sha(member) == row['member_sha256']
        with ZipFile(BytesIO(member)) as document:
            xml, styles = document.read('word/document.xml'), document.read('word/styles.xml')
        assert raw_sha(xml) == row['document_xml_sha256']
        assert raw_sha(styles) == row['styles_xml_sha256']
        parsed = own_parser.parse_parts(xml, styles, ident)
        role_field_n += len(parsed['fields'])
        for field in parsed['fields']:
            for spec in field['specs']:
                assert len(canonical_spec_iris.get(spec, [])) == 1, 'Ambiguous/missing canonical hub identity'
                hub = canonical_spec_iris[spec][0]
                assert records[hub]['properties'].get('id') in {None, spec_uri(spec)}
                source_role_edges.add((iri, RELATIONS[field['role']], hub))
        source_pins.append({k: row[k] for k in ['tdocNumber', 'archive', 'member', 'member_sha256',
                                                'document_xml_sha256', 'styles_xml_sha256']})
    tail_iris = {byid[ident] for ident in tail_ids}
    old_role_edges = {edge for edge in edges if edge[0] in tail_iris and edge[1] in RELATIONS.values()}
    added, removed = source_role_edges - old_role_edges, old_role_edges - source_role_edges
    assert len(old_role_edges) == 46 and len(source_role_edges) == 48 and role_field_n == 114
    assert len(added) == 2 and not removed, 'Only verified additive repair is authorized'
    for _, _, target in added:
        props = records[target]['properties']
        assert props.get('id') == spec_uri(props['specNumber']), 'New edge needs original canonical hub identity'
    enriched_edges = edges | added
    # The authored query matches ALL Spec nodes with the target number, not
    # merely the hub. Existing relationships to release-specific targets must
    # remain visible in the independent original-query calculation as well.
    targets = set(spec_iris['38.473'])

    def selected(edge_set):
        rows = [(cr_records[s]['properties']['tdocNumber'], cr_records[s]['properties'].get('summaryOfChange'))
                for s, rel, t in edge_set if s in cr_records and t in targets and rel in RELATIONS.values()]
        rows.sort(key=lambda row: row[0], reverse=True)
        return rows[:10]

    source_prefix = sorted([cr_records[s]['properties']['tdocNumber'] for s, _, t in source_role_edges if t in targets], reverse=True)[:10]
    enriched_rows = selected(enriched_edges)
    assert len(source_prefix) == 10 and [r[0] for r in enriched_rows] == source_prefix
    assert all(ident >= bound for ident in source_prefix)
    assert all(ident < bound for ident in ids if ident not in tail_ids)
    assert len({row[0] for row in enriched_rows}) == 10, 'No selected role/path multiplicity'
    proof = {
        'base_nodes': len(records), 'base_edges': len(edges), 'enriched_nodes': len(records),
        'enriched_edges': len(enriched_edges), 'CR_universe_n': len(ids), 'unique_CR_ids_n': len(set(ids)),
        'precommitted_lexical_bound': bound, 'complete_potential_entrant_tail_n': len(tail_ids),
        'all_other_frozen_CR_ids_strictly_below_bound': True, 'own_role_fields_reopened_n': role_field_n,
        'old_tail_all_role_edges_n': len(old_role_edges), 'source_tail_all_role_edges_n': len(source_role_edges),
        'actual_added_edges': [list(x) for x in sorted(added)], 'actual_removed_edges': [],
        'raw_source_archive_pins': observation_packet['archives'], 'raw_source_member_pins': source_pins,
        'canonical_target_rule': 'Original indexed schema declares the abstract hub the stable target of release-blind document references. Select the unique base Spec with matching specNumber and no specRelease, generic for all roles/all specs. Existing nonnull id must equal indexed JSONLD spec_uri; a pre-existing id-absent unique hub is preserved rather than replaced. New edge targets must have the canonical indexed JSONLD id.',
        'canonical_target_opposing_implementation': 'The older indexed native linker matched specNumber without a release guard. This separate repair follows indexed schema/JSONLD identity, not a claim to execute that older linker unchanged. Current worktree has a release guard but is not relabeled original INDEX.',
        'canonical_targets_for_all_source_specs': {spec: {'canonical_hub_iri': canonical_spec_iris[spec][0],
                                                        'existing_hub_id': records[canonical_spec_iris[spec][0]]['properties'].get('id'),
                                                        'all_number_matching_Spec_IRIs': sorted(spec_iris[spec])}
            for spec in sorted({records[t]['properties']['specNumber'] for _, _, t in source_role_edges})},
        'all_existing_target_number_relationship_rows_n': sum(s in cr_records and t in targets and rel in RELATIONS.values()
                                                              for s, rel, t in edges),
        'all_enriched_target_number_relationship_rows_n': sum(s in cr_records and t in targets and rel in RELATIONS.values()
                                                              for s, rel, t in enriched_edges),
        'all_target_number_matching_Specs_n': len(targets),
        'original_full_return_column_names': ['c.tdocNumber', 'c.summaryOfChange'],
        'base_original_query_independent_rows': selected(edges),
        'enriched_original_query_independent_rows': enriched_rows,
        'source_first10_identity': source_prefix, 'source_prefix_equals_enriched_exact10': True,
        'summary_policy': 'Exact original frozen value, including NULL. Source-summary completeness is not certified.',
        'scope_limit': 'Complete prefix proof over all 19,974 frozen CR identities, not unobserved CRs outside the frozen population.',
    }
    assert len(records) == 87980 and len(edges) == 481498 and len(enriched_edges) == 481500
    return added, proof

def quoted(name):
    return '"' + name.replace('"', '""') + '"'

def table_hash(con, name):
    columns = [row[1] for row in con.execute('PRAGMA table_info(' + quoted(name) + ')')]
    h = hashlib.sha256()
    for row in con.execute('SELECT * FROM ' + quoted(name) + ' ORDER BY ' + ','.join(quoted(x) for x in columns)):
        h.update((canonical(row) + '\n').encode())
    return h.hexdigest()

def readonly(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro&immutable=1', uri=True)

def prepare_sqlite(args):
    # Root-only after inspecting the full-TTL stage. Source is never writable.
    full = args.ttl_stage
    manifest = json.loads((full / 'manifest.json').read_text())
    for name, digest in manifest['artifacts'].items():
        assert sha(full / name) == digest, name
    proof = json.loads((full / 'source_delta_and_complete_prefix_proof.json').read_text())
    assert sha(args.base_db) == BASE_DB_SHA, 'Original frozen source DB pin mismatch'
    assert args.base_db.stat().st_size == 248152064
    assert not args.output.exists(), 'Output directory must be new'
    args.output.mkdir(parents=True)
    copy_path = args.output / 'RAN3-source-enriched-full.sqlite'
    shutil.copy2(args.base_db, copy_path)
    assert sha(copy_path) == BASE_DB_SHA
    source = readonly(args.base_db)
    clone = sqlite3.connect(copy_path)
    clone.execute('PRAGMA journal_mode=DELETE')
    clone.execute('PRAGMA synchronous=FULL')
    changes = []
    try:
        source_tables = dict(source.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
        clone_tables = dict(clone.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
        assert source_tables == clone_tables
        assert source.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        assert source.execute('SELECT count(*) FROM node').fetchone()[0] == proof['base_nodes']
        assert source.execute('SELECT count(*) FROM edge').fetchone()[0] == proof['base_edges']
        assert source.execute('SELECT count(*) FROM CR').fetchone()[0] == proof['CR_universe_n']
        baseline_rows = [list(row) for row in source.execute(SQL)]
        assert baseline_rows == proof['base_original_query_independent_rows']
        clone.execute('BEGIN IMMEDIATE')
        for s, rel, t in proof['actual_added_edges']:
            left = source.execute('SELECT node_id FROM _node_record WHERE source_iri=?', (s,)).fetchall()
            right = source.execute('SELECT node_id FROM _node_record WHERE source_iri=?', (t,)).fetchall()
            assert len(left) == len(right) == 1
            src, dst = left[0][0], right[0][0]
            assert not source.execute('SELECT 1 FROM edge WHERE src_id=? AND rel_type=? AND dst_id=?', (src, rel, dst)).fetchall()
            cursor = clone.execute('INSERT INTO edge(src_id,rel_type,dst_id) VALUES(?,?,?)', (src, rel, dst))
            edge_id = cursor.lastrowid
            clone.execute('INSERT INTO ' + quoted('rel_' + rel) + '(edge_id,src_id,dst_id) VALUES(?,?,?)', (edge_id, src, dst))
            changes.append([edge_id, src, rel, dst])
        clone.commit()
        assert clone.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        assert clone.execute('SELECT count(*) FROM edge').fetchone()[0] == proof['enriched_edges']
        rows = [list(row) for row in clone.execute(SQL)]
        assert rows == proof['enriched_original_query_independent_rows']
        # Complete record/table equality, not selected-row-only checks. Every
        # unchanged table and every old row of changed tables is compared.
        changed_tables = {'edge'} | {'rel_' + edge[2] for edge in changes}
        table_receipts = {}
        extra_edge_ids = {row[0] for row in changes}
        for table in sorted(source_tables):
            if table not in changed_tables:
                old, new = table_hash(source, table), table_hash(clone, table)
                assert old == new, table
                table_receipts[table] = {'unchanged': True, 'complete_row_sha256': old}
            else:
                columns = [row[1] for row in source.execute('PRAGMA table_info(' + quoted(table) + ')')]
                order = ','.join(quoted(c) for c in columns)
                old_rows = source.execute('SELECT * FROM ' + quoted(table) + ' ORDER BY ' + order)
                new_rows = clone.execute('SELECT * FROM ' + quoted(table) + ' WHERE edge_id NOT IN (' +
                                         ','.join('?' for _ in extra_edge_ids) + ') ORDER BY ' + order, tuple(sorted(extra_edge_ids)))
                h = hashlib.sha256()
                count = 0
                for old, new in zip(old_rows, new_rows, strict=True):
                    assert old == new, table
                    h.update((canonical(old) + '\n').encode())
                    count += 1
                table_receipts[table] = {'every_original_row_unchanged': True, 'old_rows': count,
                                        'complete_original_row_sha256': h.hexdigest()}
        assert dict(clone.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")) == source_tables
    finally:
        source.close()
        clone.close()
    assert sha(args.base_db) == BASE_DB_SHA
    save(args.output / 'enriched_independent_original_two_column_rows.json', rows)
    save(args.output / 'actual_all_table_preservation_receipt.json', table_receipts)
    (args.output / 'original_query_independent.sql').write_text(SQL + '\n')
    save(args.output / 'sqlite_clone_receipt.json', {
        'status': 'ACTUAL_SEPARATE_SQLITE_CLONE_ONLY_TWO_ADDITIVE_EDGES_AND_ORIGINAL_TWO_COLUMN_SQL_PASS',
        'immutable_base_path': str(args.base_db), 'immutable_base_sha256_before_and_after': BASE_DB_SHA,
        'separate_DB': {'path': copy_path.name, 'sha256': sha(copy_path), 'bytes': copy_path.stat().st_size},
        'source_full_TTL_manifest_sha256': sha(full / 'manifest.json'),
        'added_edge_rows': changes, 'all_original_tables_schemas_and_rows_preserved': True,
        'question_admissions': 0, 'expert_validation_n': 0, 'native_API_calls': 0,
        'public_or_operational_mutations': 0, 'SQL_scope': 'Original LIMIT10 only, original union roles, both original return columns.'})
    save(args.output / 'manifest.json', {'artifacts': {p.name: sha(p) for p in args.output.iterdir() if p.is_file()},
                                       'kind': 'Separate source-enriched full SQLite clone, not original frozen DB'})
    print(canonical({'status': 'SEPARATE_SQLITE_FULL_CLONE_PASS', 'added_edges_n': len(changes),
                     'original_query_rows': len(rows), 'manifest_sha256': sha(args.output / 'manifest.json')}))

def complete_base_proof(base):
    assert sha(base) == BASE_TTL_SHA, 'Immutable public baseline pin mismatch'
    lexer = load_module(BUNDLE / 'runtime/load_released_kg.py', 'portable_public_TTL_lexer')
    own = load_module(BUNDLE / 'runtime/source_affected_role_parser.py', 'portable_own_source_parser')
    records, edges, statement_hashes = read_full_base(base, lexer)
    universe = json.loads((PACKET / 'all19974_frozen_CR_identity_universe.json').read_text())
    actual = {iri: row for iri,row in records.items() if 'CR' in row['labels']}
    assert set(actual) == {row['subject'] for row in universe}
    number = {iri:row['properties'].get('specNumber') for iri,row in records.items() if 'Spec' in row['labels']}
    all_old_roles = {}
    for source,rel,target in edges:
        for role,relation in RELATIONS.items():
            if rel == relation:all_old_roles.setdefault(source,[]).append((PREDICATES[role],target,number[target]))
    for expected in universe:
        iri = expected['subject']; row = actual[iri]
        assert row['labels'] == expected['labels']
        assert row['properties']['tdocNumber'] == expected['tdocNumber']
        old = sorted((e['predicate'],e['target'],e['target_specNumber']) for e in expected['affected_edges'])
        got = sorted(all_old_roles.get(iri,[]))
        assert got == old
    added, proof = derive_source_delta(BUNDLE, records, edges, own)
    expected_proof = json.loads((BUNDLE / 'proof/source_delta_and_complete_prefix_proof.json').read_text())
    assert canonical(proof) == canonical(expected_proof), 'All source fields/whole universe/prefix/delta proof differs'
    definition = json.loads((BUNDLE / 'contract/definition.json').read_text())
    target_number = re.search(r"specNumber: '([^']+)'", definition['original_query']).group(1)
    target_iris = {iri for iri,row in records.items() if 'Spec' in row['labels'] and row['properties'].get('specNumber') == target_number}
    rows = [[records[source]['properties']['tdocNumber'],records[source]['properties'].get('summaryOfChange')]
            for source,relation,target in edges | added if source in actual and target in target_iris and relation in RELATIONS.values()]
    rows.sort(key=lambda row:row[0], reverse=True)
    native = json.loads((BUNDLE / 'proof/actual_native_original_two_column_capture.json').read_text())
    assert rows == native['whole_matching_pool']['rows']
    assert rows[:10] == native['selected']['rows']
    assert definition['original_query'] == native['selected']['literal_query']
    return records, edges, added, statement_hashes, lexer, proof


def materialize_ttl(base, output):
    assert not output.exists(), 'New output directory required'
    records, edges, added, original_statement_hashes, lexer, proof = complete_base_proof(base)
    output.mkdir(parents=True)
    destination = output / 'RAN3-source-enriched-full.ttl'
    subject_insertions = {}
    for source,relation,target in added:
        role = next(role for role,name in RELATIONS.items() if name == relation)
        subject_insertions.setdefault(source,[]).append((PREDICATES[role],target))
    changed = []
    with base.open(encoding='utf-8',newline='') as src, destination.open('x',encoding='utf-8',newline='') as dst:
        for statement in lexer.StatementReader(src):
            parsed = lexer.parse_statement(statement)
            if parsed is not None and parsed[0] in subject_insertions:
                iri = parsed[0]; stop = len(statement.rstrip())-1
                assert statement[stop] == '.'
                insertion = ''.join(f';\n    spectra:{pred} <{target}> ' for pred,target in sorted(subject_insertions[iri]))
                updated = statement[:stop] + insertion + statement[stop:]
                changed.append(iri);statement=updated
            dst.write(statement)
    assert sha(destination) == FULL_TTL_SHA
    new_records,new_edges,new_statement_hashes = read_full_base(destination,lexer)
    assert new_records == records and new_edges == edges | added
    assert set(changed) == {iri for iri in original_statement_hashes if original_statement_hashes[iri] != new_statement_hashes[iri]}
    assert sha(base) == BASE_TTL_SHA
    save(output / 'source_delta_and_complete_prefix_proof.json',proof)
    save(output / 'enriched_independent_original_two_column_rows.json',proof['enriched_original_query_independent_rows'])
    (output / 'original_query_independent.sql').write_text(SQL+'\n')
    save(output / 'full_clone_receipt.json',{'status':'REPLAY_PASS','base_TTL_sha256':BASE_TTL_SHA,'full_TTL_sha256':FULL_TTL_SHA,
        'nodes':len(records),'edges':len(new_edges),'added_edges':len(added),'unchanged_original_nodes_properties_edges':True,
        'both_original_return_columns_equal_saved_native_full354_and_selected10':True,'original_560_admissions':0,'native_API_calls':0})
    save(output / 'manifest.json',{'artifacts':{x.name:sha(x) for x in output.iterdir() if x.is_file()},'original_560_admissions':0})
    print(canonical({'status':'FULL_TTL_REPLAY_PASS','nodes':len(records),'edges':len(new_edges),'sha256':sha(destination)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode',required=True)
    ttl = sub.add_parser('ttl');ttl.add_argument('--base-ttl',type=Path,required=True);ttl.add_argument('--output',type=Path,required=True)
    sql = sub.add_parser('sqlite');sql.add_argument('--base-db',type=Path,required=True);sql.add_argument('--ttl-stage',type=Path,required=True);sql.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.mode == 'ttl':materialize_ttl(args.base_ttl,args.output)
    else:prepare_sqlite(args)


if __name__ == '__main__':main()
