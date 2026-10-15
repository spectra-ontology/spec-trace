"""Verify packaged source witnesses and optionally rebuild an isolated snapshot.

Uses Python standard library only. Inputs and the frozen benchmark are read only.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import xml.etree.ElementTree as ET
import zipfile

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def canonical(v):
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def quoted(v):
    return '"'+v.replace('"','""')+'"'

def visible(e):
    if e.tag in (W+'del',W+'moveFrom'): return ''
    if e.tag==W+'t': return e.text or ''
    if e.tag==W+'tab': return '\t'
    if e.tag in (W+'br',W+'cr'): return '\n'
    return ''.join(visible(x) for x in e)

def verify_source(package,m):
    for p in m['files']:
        f=package/p['path']; assert f.is_file() and f.stat().st_size==p['bytes'] and sha(f)==p['sha256'],p['path']
    sources=json.loads((package/'source/document_sources.json').read_text())
    units=json.loads((package/'source/source_units80.json').read_text())
    docs={}; covered=set()
    for d in sources:
        path=package/d['path']; assert sha(path)==d['member_sha256']
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            xml=z.read('word/document.xml'); styles=z.read('word/styles.xml')
        tree=ET.fromstring(xml)
        docs[(d['archive_sha256'],d['member'])]=(xml,styles,list(tree.find(W+'body')),list(tree.iter(W+'p')),list(tree.iter(W+'tbl')))
    actual=0; void=0
    for u in units:
        sm=u['source_member_pin']; key=(sm['raw_archive_pin']['sha256'],sm['member'])
        xml,styles,body,paras,tables=docs[key]
        assert hashlib.sha256(xml).hexdigest()==u['document_XML_sha256']
        assert hashlib.sha256(styles).hexdigest()==u['styles_XML_sha256']
        p=body[u['caption_raw_direct_body_child_zero_based']]
        assert p is paras[u['caption']['raw_all_w_p_zero_based']]
        assert visible(p)==u['caption']['final_visible_text']
        assert hashlib.sha256(ET.tostring(p,encoding='utf-8')).hexdigest()==u['caption']['ElementTree_serialized_XML_sha256']
        assert visible(p)=='Table '+u['tableNumber']+': '+u['tableCaption_source_literal']
        for k in ('source_owner_heading','source_next_same_level_heading'):
            h=u[k]; e=paras[h['raw_all_w_p_zero_based']]
            assert visible(e)==h['final_visible_text']
            assert hashlib.sha256(ET.tostring(e,encoding='utf-8')).hexdigest()==h['ElementTree_serialized_XML_sha256']
            assert e.find(W+'pPr/'+W+'pStyle').get(W+'val')=='Heading4'
        assert u['source_owner_heading']['raw_all_w_p_zero_based'] < u['caption']['raw_all_w_p_zero_based'] < u['source_next_same_level_heading']['raw_all_w_p_zero_based']
        for w in u['source_front_cover_identity_receipt']['associated_original_archive_cover_witnesses']:
            front=w['actual_source_front_witness']; cx,_,_,cp,_=docs[(w['archive_sha256'],front['member'])]
            assert hashlib.sha256(cx).hexdigest()==front['document_XML_sha256']
            matches=[x for x in cp if visible(x).strip()==front['first_paragraph_literal']]
            assert len(matches)==1 and hashlib.sha256(ET.tostring(matches[0],encoding='utf-8')).hexdigest()==front['paragraph_XML_sha256']
            assert front['literal_front_identity']==['TS',u['specNumber'],u['specVersion']]
            covered.add((u['specRelease'],u['specVersion']))
        if u['actual_Word_table'] is None:
            assert u['tableCaption_source_literal']=='Void'; void+=1
        else:
            t=u['actual_Word_table']; e=body[t['raw_direct_body_child_zero_based']]
            assert e.tag==W+'tbl' and e is tables[t['raw_all_w_tbl_zero_based']]
            assert hashlib.sha256(ET.tostring(e,encoding='utf-8')).hexdigest()==t['ElementTree_serialized_XML_sha256']
            j=u['caption_raw_direct_body_child_zero_based']+1
            while body[j].tag==W+'p' and not visible(body[j]).strip(): j+=1
            assert body[j] is e; actual+=1
    assert len(units)==80 and actual==62 and void==18 and len(covered)==5
    mapping=json.loads((package/'patch/new_node_edge_mapping10.json').read_text())
    by_id={u['tableId']:u for u in units}
    for r in mapping['new_tables']:
        u=by_id[r['properties']['tableId']]; assert u['actual_Word_table'] is not None
        xml,_,body,_,_=docs[(u['source_member_pin']['raw_archive_pin']['sha256'],u['source_member_pin']['member'])]
        assert r['properties']['sourceCaptionXML']==ET.tostring(body[u['caption_raw_direct_body_child_zero_based']],encoding='unicode')
        assert r['properties']['sourceTableXML']==ET.tostring(body[u['actual_Word_table']['raw_direct_body_child_zero_based']],encoding='unicode')
        assert r['properties']['sourceDocumentXMLHash']==hashlib.sha256(xml).hexdigest()
        assert r['properties']['sourceDOCXHash']==u['source_member_pin']['raw_member_sha256']
        assert r['properties']['sourceVersionLiteral']==u['specVersion']
        assert r['properties']['sourceCaptionStyleLiteral']=='ABSENT'
        assert len(r['relationships'])==2
    assert len(mapping['new_tables'])==10
    return mapping,{'source_caption_units':80,'actual_Word_tables':62,'authored_Void_caption_units':18,'source_document_members':len(sources),'retained_editions':len(covered),'new_real_Word_tables':10}

def rebuild(package,m,mapping,base_sql,base_rdf,out):
    assert not out.exists() and base_sql.resolve()!=out.resolve() and base_rdf.resolve()!=out.resolve()
    assert sha(base_sql)==m['baseline']['SQLite']['sha256'] and base_sql.stat().st_size==m['baseline']['SQLite']['bytes']
    assert sha(base_rdf)==m['baseline']['RDF']['sha256'] and base_rdf.stat().st_size==m['baseline']['RDF']['bytes']
    out.mkdir(parents=True); sql_out=out/'RAN4-source10.sqlite'; rdf_out=out/'RAN4-source10-body.ttl'
    shutil.copy2(base_sql,sql_out)
    db=sqlite3.connect(sql_out); db.row_factory=sqlite3.Row
    tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    columns={t:[r[1] for r in db.execute('PRAGMA table_info('+quoted(t)+')')] for t in tables}
    assert len(tables)==80
    max_n=db.execute('SELECT max(node_id) FROM node').fetchone()[0]
    max_e=db.execute('SELECT max(edge_id) FROM edge').fetchone()[0]
    assert max_n==342161 and max_e==1592845
    rows=mapping['new_tables']; newcols=sorted(set(rows[0]['properties'])-set(columns['TSTable']))
    assert len(newcols)==8
    with db:
        for col in newcols: db.execute('ALTER TABLE TSTable ADD COLUMN '+quoted(col)+' ANY')
        allcols=[r[1] for r in db.execute('PRAGMA table_info(TSTable)')]
        for r in rows:
            old=db.execute('SELECT * FROM _node_record WHERE node_id=?',(r['Section_anchor']['node_id'],)).fetchone()
            assert dict(old)==r['Section_anchor']
            assert not db.execute('SELECT 1 FROM TSTable WHERE tableId=?',(r['properties']['tableId'],)).fetchone()
            nid,props,labs=r['node_id'],r['properties'],canonical(r['labels'])
            db.execute('INSERT INTO _node_record VALUES(?,?,?,?)',(nid,r['source_iri'],labs,canonical(props)))
            db.execute('INSERT INTO node VALUES(?,?)',(nid,labs))
            db.execute('INSERT INTO node_label VALUES(?,?)',(nid,'TSTable'))
            db.execute('INSERT INTO node_identity VALUES(?,?)',(nid,r['loader_iri']))
            db.executemany('INSERT INTO node_property VALUES(?,?,?,?)',[(nid,k,'string',canonical(v)) for k,v in props.items()])
            db.execute('INSERT INTO TSTable VALUES('+','.join('?' for _ in allcols)+')',[nid if k=='node_id' else props.get(k) for k in allcols])
            for e in r['relationships']:
                db.execute('INSERT INTO edge VALUES(?,?,?,?)',(e['edge_id'],e['src_id'],e['rel_type'],e['dst_id']))
                db.execute('INSERT INTO '+quoted('rel_'+e['rel_type'])+' VALUES(?,?,?)',(e['edge_id'],e['src_id'],e['dst_id']))
    db.execute('ATTACH DATABASE ? AS frozen',(str(base_sql.resolve()),))
    preserved={}
    for t in tables:
        fields=','.join(quoted(k) for k in columns[t])
        restrict=' WHERE node_id<='+str(max_n) if 'node_id' in columns[t] else (' WHERE edge_id<='+str(max_e) if 'edge_id' in columns[t] else '')
        old='SELECT '+fields+' FROM frozen.'+quoted(t)
        new='SELECT '+fields+' FROM main.'+quoted(t)+restrict
        minus=db.execute('SELECT count(*) FROM ('+old+' EXCEPT '+new+')').fetchone()[0]
        plus=db.execute('SELECT count(*) FROM ('+new+' EXCEPT '+old+')').fetchone()[0]
        old_n=db.execute('SELECT count(*) FROM frozen.'+quoted(t)).fetchone()[0]
        new_n=db.execute('SELECT count(*) FROM main.'+quoted(t)+restrict).fetchone()[0]
        assert minus==plus==0 and old_n==new_n,t
        preserved[t]={'old_rows':old_n,'missing_or_changed':minus,'unexpected_old_population':plus}
    assert db.execute('SELECT count(*) FROM node').fetchone()[0]==342171
    assert db.execute('SELECT count(*) FROM edge').fetchone()[0]==1592865
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    db.close()
    delta=(package/'patch/source10_additions.ttl').read_bytes()
    with rdf_out.open('wb') as dst,base_rdf.open('rb') as src:
        shutil.copyfileobj(src,dst);dst.write(delta)
    assert sha(rdf_out)==m['expected_rebuilt_RDF_sha256']
    assert sha(base_sql)==m['baseline']['SQLite']['sha256'] and sha(base_rdf)==m['baseline']['RDF']['sha256']
    receipt={'status':'isolated_snapshot_rebuilt_with_all80_old_SQL_tables_preserved','nodes':342171,'relationships':1592865,
      'rebuilt_SQL_sha256':sha(sql_out),'rebuilt_RDF_sha256':sha(rdf_out),'old_table_preservation':preserved,
      'frozen_benchmark_changed':False,'native_execution_n':0,'model_API_calls_n':0,'expert_validation_n':0}
    (out/'rebuild_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--baseline-sql',type=Path);p.add_argument('--baseline-rdf',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args();m=json.loads((a.package/'manifest.json').read_text())
    mapping,result=verify_source(a.package,m)
    if any(x is not None for x in (a.baseline_sql,a.baseline_rdf,a.output)):
        assert all(x is not None for x in (a.baseline_sql,a.baseline_rdf,a.output)), 'Supply both baseline inputs and a new output directory'
        result['rebuild']=rebuild(a.package,m,mapping,a.baseline_sql,a.baseline_rdf,a.output)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=='__main__': main()
