#!/usr/bin/env python3
"""Add and verify the same auxiliary identity used by the shipped Neo4j loader.

This is a provenance-visible encoding supplement, not a new source-authored
property. The source IRI containing RANx differs from the loader IRI containing
the literal underscore group. Original node/property/edge records remain intact.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

import build_frozen_sqlite as codec


def expected_iri(source_iri,parser):
    match=parser.INST_RE.match(source_iri)
    if not match:
        raise ValueError('source node identity outside shipped loader syntax')
    return 'https://w3id.org/spectra/inst/_/'+match.group('cls')+'/'+match.group('nid')


def add(db,manifest_path,loader):
    db,manifest_path,loader=map(Path,(db,manifest_path,loader))
    manifest=json.loads(manifest_path.read_text())
    if manifest.get('auxiliary_loader_identity') or codec.sha(db)!=manifest['db_sha256']:
        raise ValueError('overlay already present or source database changed')
    parser=codec.parser_module(loader)
    con=sqlite3.connect(db)
    con.execute('PRAGMA cache_size=-32768');con.execute('PRAGMA temp_store=FILE')
    if con.execute('SELECT count(*) FROM node_property WHERE key=?',('iri',)).fetchone()[0]:
        raise ValueError('original iri collision requires explicit _orig_iri mapping; do not guess')
    before_sha=manifest['db_sha256'];original_record_hash=manifest['complete_native_record_sha256']
    before_inventory=(con.execute('SELECT count(*) FROM node').fetchone()[0],
                      con.execute('SELECT count(*) FROM edge').fetchone()[0])
    identity_hash=hashlib.sha256();count=0
    with con:
        con.execute('CREATE TABLE node_identity(node_id INTEGER PRIMARY KEY,iri TEXT NOT NULL UNIQUE) STRICT')
        for node_id,source_iri in con.execute('SELECT node_id,source_iri FROM _node_record ORDER BY node_id'):
            iri=expected_iri(source_iri,parser)
            con.execute('INSERT INTO node_identity VALUES(?,?)',(node_id,iri))
            identity_hash.update((codec.canonical([node_id,iri])+'\n').encode());count+=1
    reread_hash=hashlib.sha256();checked=0
    for node_id,source_iri,actual in con.execute('''SELECT r.node_id,r.source_iri,i.iri FROM _node_record r
               JOIN node_identity i USING(node_id) ORDER BY r.node_id'''):
        if actual!=expected_iri(source_iri,parser):
            raise ValueError('public auxiliary identity differs from actual shipped loader expression')
        reread_hash.update((codec.canonical([node_id,actual])+'\n').encode());checked+=1
    after_inventory=(con.execute('SELECT count(*) FROM node').fetchone()[0],
                     con.execute('SELECT count(*) FROM edge').fetchone()[0])
    if checked!=count or count!=before_inventory[0] or after_inventory!=before_inventory or reread_hash.digest()!=identity_hash.digest():
        raise ValueError('auxiliary identity incomplete or native source inventory changed')
    if con.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
        raise ValueError('SQL integrity failure after identity overlay')
    con.close()
    overlay={'status':'all_node_exact_loader_identity_PASS','sourceauthored_record_hash_unchanged':original_record_hash,
             'sourceauthored_record_and_edge_preserved':True,'source_iri_equals_loader_iri':False,
             'actual_loader_expression':'https://w3id.org/spectra/inst/_/{cls}/{nid}; cls,nid from shipped INST_RE key',
             'shipped_loader_path':str(loader.resolve()),'shipped_loader_sha256':codec.sha(loader),
             'overlay_script_sha256':codec.sha(__file__),'db_sha256_before_identity_overlay':before_sha,
             'nodes_checked':count,'identity_records_sha256':identity_hash.hexdigest(),
             'independently_reread_identity_records_sha256':reread_hash.hexdigest(),
             'original_source_iri_property_collisions':0,
             'meaning':'Loader-only stable entity identity, jointly accessible in SQL and Neo4j. No new source-authored fact or real-world completeness claim.'}
    manifest['auxiliary_loader_identity']=overlay
    manifest['schema']['node_identity']={'node_id':'integer shared with every label table','iri':'string, exact Neo4j loader-only iri'}
    manifest['schema']['auxiliary_identity_codec']='Join node_identity USING(node_id) to access the same loader-only iri as Neo4j. Source IRI containing RANx is not the loader iri; the latter uses /inst/_/{cls}/{nid}. This is stable entity identity, not a source-authored property. Business identifier fields remain their original values.'
    manifest['db_sha256']=codec.sha(db);manifest['db_bytes']=db.stat().st_size
    temporary=manifest_path.with_suffix('.pending')
    temporary.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');temporary.replace(manifest_path)
    return overlay


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--directory',required=True,type=Path);ap.add_argument('--loader',required=True,type=Path)
    args=ap.parse_args()
    print(json.dumps({wg:add(args.directory/(wg+'.sqlite'),args.directory/(wg+'.manifest.json'),args.loader)
                      for wg in ['RAN1','RAN2','RAN3','RAN4','RAN5']},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
