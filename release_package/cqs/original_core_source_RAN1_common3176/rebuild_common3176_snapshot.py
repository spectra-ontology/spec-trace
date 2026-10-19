#!/usr/bin/env python3
"""Reconstruct separate files from pinned bases, with no native or API actions."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import resource
import shutil
import sqlite3
import sys

sys.dont_write_bytecode=True
PROPERTY='sourceRecordWindowText'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def ident(s):return '"'+s.replace('"','""')+'"'
def ro(p):
    c=sqlite3.connect(p.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.execute('PRAGMA query_only=ON');return c
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--base-ttl',type=Path,required=True);p.add_argument('--base-sql',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--full-public-facts',action='store_true');a=p.parse_args();b=a.bundle.resolve();m=json.loads((b/'manifest.json').read_text())
    for x,n in [(a.base_ttl,'base_RDF'),(a.base_sql,'base_SQL')]:assert x.is_file() and x.stat().st_size==m[n]['bytes'] and sha(x)==m[n]['sha256']
    assert sqlite3.sqlite_version==m['expected_enriched_SQL']['recorded_sqlite_version'], 'Exact SQLite byte replay requires the pinned engine version.'
    out=a.out.resolve();assert not out.exists() and not out.is_relative_to(b),'Fresh output outside immutable package required.';out.mkdir(parents=True)
    source=ro(a.base_sql);bindings=json.loads((b/'whole_snapshot/all3176_exact_node_IRI_property_bindings.json').read_text())
    assert source.execute('SELECT count(*) FROM Agreement').fetchone()[0]==21058
    assert not source.execute('SELECT 1 FROM node_property WHERE key=? LIMIT 1',(PROPERTY,)).fetchone()
    for x in bindings:
        actual=source.execute('SELECT a.node_id,n.source_iri,n.labels_json FROM Agreement a JOIN _node_record n ON n.node_id=a.node_id WHERE a.resolutionId=?',(x['resolutionId'],)).fetchall()
        assert len(actual)==1 and actual[0][:2]==(x['node_id'],x['source_iri']) and json.loads(actual[0][2])==x['labels']
    ttl=out/'RAN1_source_record_text.ttl';db=out/'RAN1_source_record_text.sqlite'
    shutil.copyfile(a.base_ttl,ttl)
    with ttl.open('ab') as f:f.write(b'\n');f.write((b/'whole_snapshot/generic_property_additions.ttl').read_bytes())
    assert sha(ttl)==m['expected_enriched_RDF']['sha256'] and ttl.stat().st_size==m['expected_enriched_RDF']['bytes']
    shutil.copyfile(a.base_sql,db);clone=sqlite3.connect(db);clone.execute('PRAGMA foreign_keys=ON');clone.execute('BEGIN IMMEDIATE')
    for label in ['Agreement','Resolution']:clone.execute('ALTER TABLE '+ident(label)+' ADD COLUMN '+ident(PROPERTY)+' ANY')
    for x in bindings:
        text,node=x[PROPERTY],x['node_id'];clone.execute('INSERT INTO node_property(node_id,key,native_type,value_json) VALUES(?,?,?,?)',(node,PROPERTY,'string',json.dumps(text,ensure_ascii=False,separators=(',',':'))));clone.execute('UPDATE _node_record SET properties_json=json_set(properties_json,?,?) WHERE node_id=?',('$.sourceRecordWindowText',text,node))
        for label in x['labels']:assert clone.execute('UPDATE '+ident(label)+' SET '+ident(PROPERTY)+'=? WHERE node_id=?',(text,node)).rowcount==1
    clone.commit();assert clone.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    clone.execute('ATTACH DATABASE ? AS original',(a.base_sql.resolve().as_uri()+'?mode=ro&immutable=1',))
    tables=[x[0] for x in source.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    for table in tables:
        cols=[x[1] for x in source.execute('PRAGMA table_info('+ident(table)+')')]
        original_projection=','.join(ident(x)+',typeof('+ident(x)+')' for x in cols)
        new_projection=original_projection;suffix=''
        if table=='_node_record':new_projection=','.join("json_remove(properties_json,'$.sourceRecordWindowText'),typeof(properties_json)" if x=='properties_json' else ident(x)+',typeof('+ident(x)+')' for x in cols)
        elif table=='node_property':suffix=" WHERE key<>'sourceRecordWindowText'"
        left='SELECT '+original_projection+' FROM original.'+ident(table);right='SELECT '+new_projection+' FROM main.'+ident(table)+suffix
        for first,second in [(left,right),(right,left)]:assert clone.execute('SELECT 1 FROM ('+first+' EXCEPT '+second+') LIMIT 1').fetchone() is None,table
        assert clone.execute('SELECT count(*) FROM '+ident(table)).fetchone()[0]==source.execute('SELECT count(*) FROM '+ident(table)).fetchone()[0]+(3176 if table=='node_property' else 0)
    assert clone.execute('SELECT count(*) FROM Agreement WHERE sourceRecordWindowText IS NULL').fetchone()[0]==17882
    clone.close();assert sha(db)==m['expected_enriched_SQL']['sha256'] and db.stat().st_size==m['expected_enriched_SQL']['bytes']
    full=False
    if a.full_public_facts:
        available=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
        assert available>=26*1024**3,'Whole parse requires26GiB available and8GiB process cap.'
        resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
        if hasattr(__import__('os'),'sched_setaffinity'):
            import os
            os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
        spec=importlib.util.spec_from_file_location('pinned_full_public_lexer',b/'recipe/load_released_kg.py');loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
        with contextlib.redirect_stdout(io.StringIO()):nodes,edges,stats=loader.parse_ttl(ttl)
        assert len(nodes)==165418 and len(edges)==848228 and not stats['prop_conflicts']
        patches={x['node_id']:x[PROPERTY] for x in bindings};keys={};props=0
        for node,iri,labels,properties in source.execute('SELECT node_id,source_iri,labels_json,properties_json FROM _node_record'):
            match=loader.INST_RE.fullmatch(iri);assert match and match.group('wg')=='RAN1';key=(match.group('cls'),match.group('nid'));keys[node]=key;expected=json.loads(properties);props+=len(expected)
            if node in patches:expected[PROPERTY]=patches[node]
            assert nodes[key]['labels']==set(json.loads(labels)) and json.dumps(nodes[key]['props'],sort_keys=True,ensure_ascii=False)==json.dumps(expected,sort_keys=True,ensure_ascii=False)
        assert len(keys)==len(set(keys.values()))==len(nodes)
        n=0
        for src,kind,dst in source.execute('SELECT src_id,rel_type,dst_id FROM edge'):assert (keys[src],kind,keys[dst]) in edges;n+=1
        assert n==len(edges)
        full={'nodes':len(nodes),'edges':len(edges),'all_original_typed_properties':props,'new_strings':3176,'process_address_space_cap_bytes':8*1024**3,'initial_host_available_bytes':available}
    source.close();assert sha(a.base_sql)==m['base_SQL']['sha256'] and sha(a.base_ttl)==m['base_RDF']['sha256']
    receipt={'status':'PASS','base_unchanged':True,'RDF_sha256':sha(ttl),'SQL_sha256':sha(db),'original_SQL_tables_checked_both_directions':len(tables),'full_public_facts':full,'native_calls':0,'API_calls':0}
    (out/'rebuild_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
