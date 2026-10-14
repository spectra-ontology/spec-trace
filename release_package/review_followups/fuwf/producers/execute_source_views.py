#!/usr/bin/env python3
"""Replay prespecified SQL and SPARQL queries on the two fixed source slices.

Requires Python 3.10+ and rdflib 7.6.0. No model, network or operational DB
access. Gold rows come directly from CSV/JSON, before either representation is
built. This verifies an export and its queries, not source truth or utility.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import rdflib
from rdflib import Graph, Literal, Namespace, URIRef


V = Namespace('urn:fuwf:source-view:')
INPUTS = {
    'cr': 'refinement/source-derived-cr-declarations/records.csv',
    'clauses': 'refinement/source-derived-cr-declarations/declared_clauses.csv',
    'cr_manifest': 'refinement/source-derived-cr-declarations/manifest.json',
    'differences': 'refinement/source-derived-cr-declarations/discrepancies_unapplied.json',
    'ls': 'verified-routing-slice/records.csv',
    'recipients': 'verified-routing-slice/addressed_recipients.csv',
    'ls_manifest': 'verified-routing-slice/manifest.json',
}
SCHEMA = '''
CREATE TABLE cr (source_identity TEXT PRIMARY KEY, tdoc TEXT NOT NULL,
 specification TEXT NOT NULL, release TEXT NOT NULL, archive TEXT NOT NULL,
 member TEXT NOT NULL, archive_sha256 TEXT NOT NULL, member_sha256 TEXT NOT NULL);
CREATE TABLE declared_clause (source_identity TEXT NOT NULL REFERENCES cr,
 declared_clause TEXT NOT NULL, PRIMARY KEY(source_identity,declared_clause));
CREATE TABLE discrepancy (source_identity TEXT PRIMARY KEY REFERENCES cr,
 kind TEXT NOT NULL, native_field_locators TEXT NOT NULL);
CREATE TABLE cr_unresolved (source_identity TEXT PRIMARY KEY, tdoc TEXT NOT NULL,
 reason TEXT NOT NULL);
CREATE TABLE liaison (row_id TEXT PRIMARY KEY, observed_wg TEXT NOT NULL,
 tdoc TEXT NOT NULL, raw_to TEXT NOT NULL, source_path TEXT NOT NULL,
 source_sha256 TEXT NOT NULL, sheet TEXT NOT NULL, source_row TEXT NOT NULL);
CREATE TABLE recipient (row_id TEXT NOT NULL REFERENCES liaison,
 addressed_recipient TEXT NOT NULL, PRIMARY KEY(row_id,addressed_recipient));
CREATE TABLE ls_excluded (source_identity TEXT PRIMARY KEY, observed_wg TEXT NOT NULL,
 raw_to TEXT NOT NULL, reason TEXT NOT NULL);
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


def csv_rows(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def normalize(rows):
    values = [tuple(str(value) for value in row) for row in rows]
    assert len(values) == len(set(values)), 'Duplicate output rows'
    return [list(row) for row in sorted(values)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compare', type=Path)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False, parents=True)
    paths = {key: args.root/value for key, value in INPUTS.items()}
    pins = {INPUTS[key]: sha(path) for key, path in paths.items()}
    records, clauses = csv_rows(paths['cr']), csv_rows(paths['clauses'])
    liaisons, recipients = csv_rows(paths['ls']), csv_rows(paths['recipients'])
    cm, lm = json.loads(paths['cr_manifest'].read_text()), json.loads(paths['ls_manifest'].read_text())
    differences = json.loads(paths['differences'].read_text())['cases']
    unresolved, excluded = cm['unresolved_cases'], lm['excluded']
    assert len(records)==45 and len(clauses)==112 and len(liaisons)==47 and len(recipients)==62
    assert len(differences)==15 and len(unresolved)==5 and len(excluded)==3
    cr_by_id = {row['source_identity']:row for row in records}
    ls_by_id = {row['row_id']:row for row in liaisons}
    assert len(cr_by_id)==45 and len(ls_by_id)==47
    assert {row['source_identity'] for row in clauses}==set(cr_by_id)
    assert {row['row_id'] for row in recipients}==set(ls_by_id)
    for row in clauses:
        record=cr_by_id[row['source_identity']]
        assert all(row[key]==record[key] for key in ['tdoc','specification','release'])
    ls_fields=['row_id','observed_wg','tdoc','raw_to','source_path','source_sha256','sheet','source_row']
    cr_fields=['source_identity','tdoc','specification','release','archive','member','archive_sha256','member_sha256']
    ls_tuple=lambda row: (row['row_id'],row['source_wg'],row['tdoc_number'],row['raw_to'],row['source_path'],row['source_sha256'],row['sheet'],row['row'])
    cr_tuple=lambda row: tuple(row[key] for key in cr_fields)
    queries=[]
    def add(name, fields, sql, sparql, gold):
        queries.append({'name':name,'fields':fields,'sql':sql,
                        'sparql':'PREFIX v: <urn:fuwf:source-view:>\n'+sparql,
                        'expected':normalize(gold)})
    # Fix all 25 pairs, including zero-result pairs, before engine execution.
    ls_select='SELECT '+','.join('l.'+field for field in ls_fields)+' FROM liaison l JOIN recipient r ON l.row_id=r.row_id'
    ls_pattern=' '.join('v:'+field+' ?'+field+';' for field in ls_fields).rstrip(';')+'.'
    for observed in ['RAN1','RAN2','RAN3','RAN4','RAN5']:
        for addressed in ['RAN1','RAN2','RAN3','RAN4','RAN5']:
            gold=[ls_tuple(ls_by_id[row['row_id']]) for row in recipients
                  if row['addressed_recipient']==addressed and ls_by_id[row['row_id']]['source_wg']==observed]
            add('liaison_'+observed+'_addressed_'+addressed,ls_fields,
                ls_select+" WHERE l.observed_wg='"+observed+"' AND r.addressed_recipient='"+addressed+"'",
                'SELECT '+' '.join('?'+field for field in ls_fields)+' WHERE { ?record '+ls_pattern+
                ' ?record v:addressed_recipient '+Literal(addressed).n3()+'. FILTER (?observed_wg = '+Literal(observed).n3()+') }',gold)
    cr_select='SELECT '+','.join('c.'+field for field in cr_fields)+' FROM cr c'
    cr_pattern=' '.join('v:'+field+' ?'+field+';' for field in cr_fields).rstrip(';')+'.'
    for release in ['Rel-15','Rel-16','Rel-17','Rel-18','Rel-19']:
        add('cr_declared_release_'+release,cr_fields,
            cr_select+" WHERE c.release='"+release+"'",
            'SELECT '+' '.join('?'+field for field in cr_fields)+' WHERE { ?record '+cr_pattern+' FILTER (?release = '+Literal(release).n3()+') }',
            [cr_tuple(row) for row in records if row['release']==release])
    add('all_declared_clause_memberships',cr_fields+['declared_clause'],
        'SELECT '+','.join('c.'+f for f in cr_fields)+',d.declared_clause FROM cr c JOIN declared_clause d ON c.source_identity=d.source_identity',
        'SELECT '+' '.join('?'+f for f in cr_fields+['declared_clause'])+' WHERE { ?record '+cr_pattern+' ?record v:declared_clause ?declared_clause. }',
        [cr_tuple(cr_by_id[row['source_identity']])+(row['declared_clause'],) for row in clauses])
    difference_fields=cr_fields+['kind','native_field_locators']
    diff_sql='SELECT '+','.join('c.'+f for f in cr_fields)+',d.kind,d.native_field_locators FROM cr c JOIN discrepancy d ON c.source_identity=d.source_identity'
    diff_sparql='SELECT '+' '.join('?'+f for f in difference_fields)+' WHERE { ?record '+cr_pattern+' ?record v:kind ?kind; v:native_field_locators ?native_field_locators. '
    difference_tuple=lambda row: cr_tuple(cr_by_id[row['identity']])+(row['observed_discrepancy_kind'],json.dumps(row['native_fields'],ensure_ascii=False,sort_keys=True))
    add('all_cr_discrepancies',difference_fields,diff_sql,diff_sparql+'}',[difference_tuple(row) for row in differences])
    for kind in ['declared_section_outside_frozen_definition_scope','missing_link_to_defined_section','different_release_target']:
        add('cr_discrepancy_'+kind,difference_fields,diff_sql+" WHERE d.kind='"+kind+"'",
            diff_sparql+'FILTER (?kind = '+Literal(kind).n3()+') }',
            [difference_tuple(row) for row in differences if row['observed_discrepancy_kind']==kind])
    add('all_cr_unresolved',['source_identity','tdoc','reason'],
        'SELECT source_identity,tdoc,reason FROM cr_unresolved',
        'SELECT ?source_identity ?tdoc ?reason WHERE { ?record v:record_type "cr_unresolved"; v:source_identity ?source_identity; v:tdoc ?tdoc; v:reason ?reason. }',
        [(row['identity'],row['current_tdoc'],row['reason']) for row in unresolved])
    add('all_liaison_exclusions',['source_identity','observed_wg','raw_to','reason'],
        'SELECT source_identity,observed_wg,raw_to,reason FROM ls_excluded',
        'SELECT ?source_identity ?observed_wg ?raw_to ?reason WHERE { ?record v:record_type "ls_excluded"; v:source_identity ?source_identity; v:observed_wg ?observed_wg; v:raw_to ?raw_to; v:reason ?reason. }',
        [(row['identity'],row['source_wg'],row['raw_to'],row['reason']) for row in excluded])
    assert len(queries)==37
    # Protocol/gold exist before SQL and RDF construction or execution.
    protocol={'classification':'NEW_LOCAL_EXECUTABLE_DERIVATIVE_AND_FIXED_QUERY_REPLAY',
        'input_sha256':pins,'queries_n':len(queries),'selection':'All fixed slices and all 25 observed/addressed RAN WG pairs; no outcome-based replacement.',
        'gold':'Direct CSV/JSON filters and joins, computed before either representation is built.',
        'semantics':'Observed WG is the file location, not sender; addressed recipient is not causal influence. Declared clause is a cover literal, not an adopted change or a frozen Section node.',
        'scope':'Export/query correctness on these slices; no model accuracy, population completeness or practitioner utility evaluation.',
        'operational_database_calls':0,'model_calls':0,'expert_reviews':0,'production_or_frozen_release_modified':False}
    dump(args.output/'protocol.json',protocol)
    dump(args.output/'queries_and_gold.json',queries)
    (args.output/'schema.sql').write_text(SCHEMA)
    db=sqlite3.connect(':memory:')
    db.execute('PRAGMA foreign_keys=ON');db.executescript(SCHEMA)
    graph=Graph()
    def insert(table, record_type, rows):
        for n,row in enumerate(rows):
            values=list(row.values())
            db.execute('INSERT INTO '+table+' VALUES ('+','.join('?' for _ in values)+')',values)
            subject=URIRef(str(V)+record_type+'/'+str(n))
            graph.add((subject,V.record_type,Literal(record_type)))
            for key,value in row.items():graph.add((subject,V[key],Literal(value)))
    insert('cr','cr',[dict(zip(cr_fields,cr_tuple(row))) for row in records])
    cr_uris={row['source_identity']:URIRef(str(V)+'cr/'+str(n)) for n,row in enumerate(records)}
    for row in clauses:
        db.execute('INSERT INTO declared_clause VALUES (?,?)',(row['source_identity'],row['declared_clause']))
        graph.add((cr_uris[row['source_identity']],V.declared_clause,Literal(row['declared_clause'])))
    for row in differences:
        kind,locators=difference_tuple(row)[-2:]
        db.execute('INSERT INTO discrepancy VALUES (?,?,?)',(row['identity'],kind,locators))
        graph.add((cr_uris[row['identity']],V.kind,Literal(kind)))
        graph.add((cr_uris[row['identity']],V.native_field_locators,Literal(locators)))
    insert('cr_unresolved','cr_unresolved',[
        {'source_identity':row['identity'],'tdoc':row['current_tdoc'],'reason':row['reason']} for row in unresolved])
    insert('liaison','liaison',[dict(zip(ls_fields,ls_tuple(row))) for row in liaisons])
    ls_uris={row['row_id']:URIRef(str(V)+'liaison/'+str(n)) for n,row in enumerate(liaisons)}
    for row in recipients:
        db.execute('INSERT INTO recipient VALUES (?,?)',(row['row_id'],row['addressed_recipient']))
        graph.add((ls_uris[row['row_id']],V.addressed_recipient,Literal(row['addressed_recipient'])))
    insert('ls_excluded','ls_excluded',[
        {'source_identity':row['identity'],'observed_wg':row['source_wg'],'raw_to':row['raw_to'],'reason':row['reason']} for row in excluded])
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
    triples=''.join(sorted(' '.join(term.n3() for term in triple)+' .\n' for triple in graph))
    (args.output/'source_views.nt').write_text(triples)
    # Execute SPARQL against the serialized export, not the graph used to build it.
    imported=Graph();imported.parse(args.output/'source_views.nt',format='nt')
    assert set(imported)==set(graph)
    outputs=[]
    for query in queries:
        sql=normalize(db.execute(query['sql']).fetchall())
        sparql=normalize(imported.query(query['sparql']))
        outputs.append({'name':query['name'],'fields':query['fields'],'sql_rows':sql,
            'sparql_rows':sparql,'expected_rows':query['expected'],
            'status':'PASS' if sql==sparql==query['expected'] else 'FAIL'})
    dump(args.output/'query_results.json',outputs)
    tables={table:db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
            for table in ['cr','declared_clause','discrepancy','cr_unresolved','liaison','recipient','ls_excluded']}
    db.close()
    drift=[relative for relative,pin in pins.items() if sha(args.root/relative)!=pin]
    replay_equal=None
    if args.compare:
        previous=json.loads((args.compare/'query_results.json').read_text())
        replay_equal=previous==outputs
        assert replay_equal, 'Fresh replay differs from retained results'
        assert sha(args.compare/'source_views.nt')==sha(args.output/'source_views.nt')
    report={'status':'PASS' if not drift and all(row['status']=='PASS' for row in outputs) else 'FAIL',
        'query_pairs_n':len(outputs),'sql_executions_n':len(outputs),'sparql_executions_n':len(outputs),
        'all_three_way_exact':all(row['status']=='PASS' for row in outputs),
        'table_record_counts':tables,'rdf_triples_n':len(imported),
        'RAN2_observed_addressed_RAN3_records_n':len(next(row['sql_rows'] for row in outputs if row['name']=='liaison_RAN2_addressed_RAN3')),
        'discrepancy_kind_counts':dict(Counter(row['observed_discrepancy_kind'] for row in differences)),
        'original_denominators':{'cr_selected':50,'cr_parsed':45,'cr_unresolved':5,'liaisons_selected':50,'liaisons_admitted':47,'liaisons_excluded':3},
        'software':{'python_requirement':'3.10+','sqlite':sqlite3.sqlite_version,'rdflib':rdflib.__version__},
        'fresh_replay_equal':replay_equal,'input_drift':drift,
        'file_sha256':{name:sha(args.output/name) for name in ['protocol.json','queries_and_gold.json','schema.sql','source_views.nt','query_results.json']},
        'expert_reviews':0,'model_calls':0,'operational_database_calls':0,
        'production_or_frozen_release_modified':False,'limits':protocol['scope']}
    dump(args.output/'results.json',report)
    print(json.dumps({key:report[key] for key in ['status','query_pairs_n','table_record_counts','rdf_triples_n','fresh_replay_equal']},indent=2))
    assert report['status']=='PASS'


if __name__=='__main__':main()
