#!/usr/bin/env python3
"""Read-only full checks of public SQL registries, labels and edge tables."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import sqlite3
import time

import build_frozen_sqlite as codec
import add_loader_identity as identity


def verify(db,manifest,graph_schema):
    db=Path(db);manifest=Path(manifest);pin=json.loads(manifest.read_text())
    if codec.sha(db)!=pin['db_sha256'] or codec.sha(pin['source']['path'])!=pin['source']['sha256']:
        raise ValueError('SQL/frozen source hash mismatch')
    started=time.monotonic();sql_schema=pin['schema']
    actual_properties={label:set(fields)-{'node_id'} for label,fields in sql_schema['label_tables'].items()}
    expected_properties={label:{field['name'] for field in fields}
                         for label,fields in graph_schema['label_properties'].items()}
    if actual_properties!=expected_properties or set(actual_properties)!=set(graph_schema['labels']):
        raise ValueError('SQL/graph label-property information differs')
    expected_triples={(r['from_label'],r['relationship'],r['to_label']) for r in graph_schema['relationship_triples']}
    if {tuple(r) for r in sql_schema['directed_relationships']}!=expected_triples:
        raise ValueError('SQL/graph directed relationship patterns differ')
    con=sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
    con.execute('PRAGMA cache_size=-32768');con.execute('PRAGMA temp_store=FILE')
    public_hash=hashlib.sha256();nodes=properties=labels=0
    for node_id,iri,labels_json,properties_json in con.execute('SELECT * FROM _node_record ORDER BY node_id'):
        original_labels=json.loads(labels_json);original_properties=json.loads(properties_json)
        public_labels=json.loads(con.execute('SELECT labels FROM node WHERE node_id=?',(node_id,)).fetchone()[0])
        explicit_labels=[r[0] for r in con.execute('SELECT label FROM node_label WHERE node_id=? ORDER BY label',(node_id,))]
        if public_labels!=original_labels or explicit_labels!=original_labels:
            raise ValueError('public multilabel registry differs from parsed source')
        public_properties={}
        for key,kind,value_json in con.execute('SELECT key,native_type,value_json FROM node_property WHERE node_id=?',(node_id,)):
            value=json.loads(value_json)
            if kind!=codec.native_type(value):
                raise ValueError('native property type registry mismatch')
            public_properties[key]=value;properties+=1
        if codec.canonical(public_properties)!=codec.canonical(original_properties):
            raise ValueError('public property registry differs from parsed source')
        public_hash.update((codec.canonical([iri,public_labels,public_properties])+'\n').encode())
        nodes+=1;labels+=len(public_labels)
    if public_hash.hexdigest()!=pin['complete_native_record_sha256'] or nodes!=pin['nodes']:
        raise ValueError('public complete record hash differs from complete native source record hash')
    relations=0;table_hashes={}
    for rel_type,count in sorted(pin['relationship_counts'].items()):
        generic=hashlib.sha256();special=hashlib.sha256();ng=ns=0
        for row in con.execute('SELECT edge_id,src_id,dst_id FROM edge WHERE rel_type=? ORDER BY edge_id',(rel_type,)):
            generic.update((codec.canonical(row)+'\n').encode());ng+=1
        for row in con.execute('SELECT edge_id,src_id,dst_id FROM '+codec.quoted('rel_'+rel_type)+' ORDER BY edge_id'):
            special.update((codec.canonical(row)+'\n').encode());ns+=1
        if ng!=count or ns!=count or generic.digest()!=special.digest():
            raise ValueError('typed relationship table is not an exact identity-preserving edge encoding')
        relations+=ns;table_hashes[rel_type]=generic.hexdigest()
    identity_result=None
    if pin.get('auxiliary_loader_identity'):
        overlay=pin['auxiliary_loader_identity'];loader=Path(overlay['shipped_loader_path'])
        if codec.sha(loader)!=overlay['shipped_loader_sha256']:
            raise ValueError('actual loader identity mapping code changed')
        parser=codec.parser_module(loader);ih=hashlib.sha256();identity_count=0
        for node_id,source_iri,iri in con.execute('''SELECT r.node_id,r.source_iri,i.iri FROM _node_record r
                   JOIN node_identity i USING(node_id) ORDER BY r.node_id'''):
            if iri!=identity.expected_iri(source_iri,parser):
                raise ValueError('auxiliary SQL/Neo4j loader identity differs')
            ih.update((codec.canonical([node_id,iri])+'\n').encode());identity_count+=1
        if identity_count!=nodes or ih.hexdigest()!=overlay['identity_records_sha256']:
            raise ValueError('auxiliary identity incomplete or identity hash differs')
        identity_result={'status':'PASS','nodes_checked':identity_count,'identity_records_sha256':ih.hexdigest(),
                         'shipped_loader_sha256':overlay['shipped_loader_sha256']}
    con.close()
    if relations!=pin['relationships'] or codec.sha(db)!=pin['db_sha256']:
        raise ValueError('relationship inventory or frozen DB changed during verification')
    return {'status':'PASS','db_sha256':pin['db_sha256'],'manifest_sha256':codec.sha(manifest),
            'source_sha256':pin['source']['sha256'],'nodes_checked':nodes,'labels_checked':labels,
            'property_native_types_checked':properties,'relationship_identity_rows_checked':relations,
            'public_complete_native_record_sha256':public_hash.hexdigest(),
            'all_typed_relationship_table_sha256':table_hashes,
            'auxiliary_loader_identity':identity_result,
            'valuefree_schema_label_property_patterns_exact':True,
            'elapsed_seconds':round(time.monotonic()-started,3)}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--directory',required=True,type=Path);ap.add_argument('--graph-schema',required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args();schema=json.loads(args.graph_schema.read_text())
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    if hasattr(os,'sched_getaffinity'):
        os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    results={wg:verify(args.directory/(wg+'.sqlite'),args.directory/(wg+'.manifest.json'),group)
             for wg,group in schema['working_groups'].items()}
    report={'status':'PASS','scope':'Complete public SQL node/label/property/edge encoding equals pinned shipped frozen graph projection; not causal representation fairness.',
            'verifier_sha256':codec.sha(__file__),'frozen_graph_schema_sha256':codec.sha(args.graph_schema),
            'working_groups':results,'model_calls':0,'expert_review_n':0}
    with args.output.open('x') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({wg:{k:r[k] for k in ('status','nodes_checked','relationship_identity_rows_checked','elapsed_seconds')}
                      for wg,r in results.items()}),flush=True)


if __name__=='__main__':main()
