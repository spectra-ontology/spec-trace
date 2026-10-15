"""Authenticate five source tables and optionally rebuild an additive snapshot.

Python standard library only. No servers, model calls, or baseline writes.
"""
import argparse, hashlib, json, shutil, sqlite3, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def quote(v):return '"'+v.replace('"','""')+'"'
def read(p):return json.loads(Path(p).read_text())
def visible(e):
    if e.tag==W+'t':return e.text or ''
    if e.tag==W+'tab':return '\t'
    if e.tag in (W+'br',W+'cr'):return '\n'
    return ''.join(visible(x) for x in e)

def verify_source(package,m):
    for f in m['files']:
        p=(package/f['path']).resolve()
        assert p.is_relative_to(package.resolve()) and p.is_file()
        assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],f['path']
    documents=read(package/'source/portable_document_sources.json')
    mapping=read(package/'patch/source5_node_edge_mapping.json')
    docs={}
    for d in documents:
        dp=package/d['DOCX_path'];ap=package/d['ZIP_path']
        assert sha(dp)==d['DOCX_sha256'] and sha(ap)==d['ZIP_sha256']
        with zipfile.ZipFile(ap) as z:
            assert z.testzip() is None;assert z.read(d['member'])==dp.read_bytes()
        with zipfile.ZipFile(dp) as z:
            assert z.testzip() is None;raw=z.read('word/document.xml');styles=z.read('word/styles.xml')
        root=ET.fromstring(raw)
        docs[d['DOCX_sha256']]=(raw,styles,root,list(root.find(W+'body')),list(root.iter(W+'p')),list(root.iter(W+'tbl')))
    omml=0
    for r in mapping['new_tables']:
        p=r['properties'];u=r['source_receipt']
        raw,styles,root,body,paras,tables=docs[p['sourceDOCXSha256']]
        assert hashlib.sha256(raw).hexdigest()==p['sourceDocumentXMLSha256']
        assert hashlib.sha256(styles).hexdigest()==p['sourceStylesXMLSha256']
        cp=paras[p['sourceCaptionAllParagraphIndex']];tp=tables[p['sourceTableAllTableIndex']]
        assert cp is body[p['sourceCaptionBodyBlockIndex']]
        assert tp is body[p['sourceTableBodyBlockIndex']] and tp.tag==W+'tbl'
        assert cp.find(W+'pPr/'+W+'pStyle') is None
        assert ET.tostring(cp,encoding='unicode')==p['sourceCaptionXML']
        assert ET.tostring(tp,encoding='unicode')==p['sourceTableXML']
        assert hashlib.sha256(ET.tostring(cp,encoding='utf-8')).hexdigest()==p['sourceCaptionXMLSha256']
        assert hashlib.sha256(ET.tostring(tp,encoding='utf-8')).hexdigest()==p['sourceTableXMLSha256']
        assert ''.join(e.text or '' for e in cp.iter(W+'t'))==p['sourceCaptionWTextProjection']
        assert p['tableNumber']==u['caption_number']
        assert p['tableId']==u['source_number']+'-'+u['source_release']+'-T'+u['caption_number']
        j=p['sourceCaptionBodyBlockIndex']+1
        while body[j].tag==W+'p' and not visible(body[j]).strip():j+=1
        assert body[j] is tp
        hp=body[p['sourceHeadingBodyBlockIndex']]
        assert visible(hp)==p['sourceHeadingLiteralWithTabs']
        assert hashlib.sha256(ET.tostring(hp,encoding='utf-8')).hexdigest()==p['sourceHeadingXMLSha256']
        assert r['section_anchor']['sectionId']==u['frozen_Section_anchor']['sectionId']
        assert r['Spec_anchor']['specNumber']==p['sourceSpecNumber']==u['source_number']
        assert r['Spec_anchor']['specRelease']==p['sourceRelease']==u['source_release']
        assert r['Spec_anchor']['specVersion']==p['sourceVersion']==u['source_version']
        for h in u['source_receipt']['source_header_witnesses']:
            hp=paras[h['all_document_paragraph_index']]
            assert ''.join(e.text or '' for e in hp.iter(W+'t'))==h['literal']
            assert h['literal'].startswith('3GPP TS '+p['sourceSpecNumber']+' V'+p['sourceVersion'])
        atoms=[dict(tag=e.tag,text=e.text or '',attributes=dict(e.attrib)) for e in cp.iter() if e.tag in (W+'t',M+'t')]
        assert atoms==json.loads(p['sourceCaptionTypedTextAtomsJSON'])
        maths=[ET.tostring(e,encoding='unicode') for e in cp.iter(M+'oMath')]
        assert maths==json.loads(p['sourceCaptionOMMLJSON']) and len(maths)==p['sourceCaptionOMMLCount']
        omml+=len(maths)
        assert r['labels']==['TSTable'] and len(r['relationships'])==2
        assert {e['rel_type'] for e in r['relationships']}=={'CONTAINS_TABLE','TABLE_IN_SECTION'}
    assert len(documents)==2 and len(mapping['new_tables'])==5 and omml==8
    return mapping,dict(authentic_actual_Word_tables_n=5,original_ZIP_DOCX_pairs_n=2,caption_OMML_objects_n=8,whole_physical_extraction_completeness_claimed=False)

def rebuild(package,m,mapping,base_sql,base_ttl,out):
    assert not out.exists() and sha(base_sql)==m['baseline']['SQLite']['sha256']
    assert sha(base_ttl)==m['baseline']['RDF']['sha256']
    out.mkdir(parents=True);dbpath=out/'RAN1.sqlite';ttlpath=out/'RAN1-source5-body.ttl'
    shutil.copy2(base_sql,dbpath)
    c=sqlite3.connect(dbpath.as_uri()+'?mode=rw',uri=True);c.row_factory=sqlite3.Row
    c.execute('PRAGMA cache_size=-8192');c.execute('PRAGMA temp_store=FILE');c.execute('PRAGMA threads=1')
    tables=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    columns={t:[r[1] for r in c.execute('PRAGMA table_info('+quote(t)+')')] for t in tables}
    maxn=c.execute('SELECT max(node_id) FROM node').fetchone()[0]
    maxe=c.execute('SELECT max(edge_id) FROM edge').fetchone()[0]
    assert len(tables)==89 and maxn==165418 and maxe==848228
    rows=mapping['new_tables'];added=sorted(set(rows[0]['properties'])-set(columns['TSTable']))
    assert len(added)==28
    with c:
        for k in added:c.execute('ALTER TABLE TSTable ADD COLUMN '+quote(k)+' ANY')
        allcols=[r[1] for r in c.execute('PRAGMA table_info(TSTable)')]
        for r in rows:
            a=r['section_anchor'];stored=c.execute('SELECT source_iri,labels_json,properties_json FROM _node_record WHERE node_id=?',(a['node_id'],)).fetchone()
            assert dict(stored)=={k:a[k] for k in ['source_iri','labels_json','properties_json']}
            assert not c.execute('SELECT 1 FROM TSTable WHERE tableId=?',(r['properties']['tableId'],)).fetchone()
            nid,p=r['node_id'],r['properties'];labs=canon(r['labels'])
            c.execute('INSERT INTO _node_record VALUES(?,?,?,?)',(nid,r['source_iri'],labs,canon(p)))
            c.execute('INSERT INTO node VALUES(?,?)',(nid,labs));c.execute('INSERT INTO node_label VALUES(?,?)',(nid,'TSTable'))
            c.execute('INSERT INTO node_identity VALUES(?,?)',(nid,r['loader_iri']))
            c.executemany('INSERT INTO node_property VALUES(?,?,?,?)',[(nid,k,'integer' if type(v) is int else 'string',canon(v)) for k,v in p.items()])
            c.execute('INSERT INTO TSTable VALUES('+','.join('?' for _ in allcols)+')',[nid if k=='node_id' else p.get(k) for k in allcols])
            for e in r['relationships']:
                c.execute('INSERT INTO edge VALUES(?,?,?,?)',(e['edge_id'],e['src_id'],e['rel_type'],e['dst_id']))
                c.execute('INSERT INTO '+quote('rel_'+e['rel_type'])+' VALUES(?,?,?)',(e['edge_id'],e['src_id'],e['dst_id']))
    c.execute('ATTACH DATABASE ? AS frozen',(base_sql.as_uri()+'?mode=ro&immutable=1',))
    preserved={}
    for t in tables:
        fields=','.join(quote(k) for k in columns[t]);restrict=' WHERE node_id<='+str(maxn) if 'node_id' in columns[t] else (' WHERE edge_id<='+str(maxe) if 'edge_id' in columns[t] else '')
        old='SELECT '+fields+' FROM frozen.'+quote(t);new='SELECT '+fields+' FROM main.'+quote(t)+restrict
        missing=c.execute('SELECT count(*) FROM ('+old+' EXCEPT '+new+')').fetchone()[0]
        extra=c.execute('SELECT count(*) FROM ('+new+' EXCEPT '+old+')').fetchone()[0]
        oldn=c.execute('SELECT count(*) FROM frozen.'+quote(t)).fetchone()[0];newn=c.execute('SELECT count(*) FROM main.'+quote(t)+restrict).fetchone()[0]
        assert missing==extra==0 and oldn==newn,t
        preserved[t]=dict(original_columns=columns[t],old_rows=oldn,new_original_domain_rows=newn,old_minus_new=missing,new_minus_old=extra)
    for k in added:assert c.execute('SELECT count(*) FROM TSTable WHERE node_id<=? AND '+quote(k)+' IS NOT NULL',(maxn,)).fetchone()[0]==0
    expected_edges={(e['edge_id'],e['src_id'],e['rel_type'],e['dst_id']) for r in rows for e in r['relationships']}
    assert {tuple(x) for x in c.execute('SELECT edge_id,src_id,rel_type,dst_id FROM edge WHERE edge_id>?',(maxe,))}==expected_edges
    for r in rows:
        nid=r['node_id'];stored=c.execute('SELECT * FROM _node_record WHERE node_id=?',(nid,)).fetchone()
        assert json.loads(stored['properties_json'])==r['properties']
        actual={x['key']:json.loads(x['value_json']) for x in c.execute('SELECT * FROM node_property WHERE node_id=?',(nid,))}
        assert actual==r['properties']
        actual=dict(c.execute('SELECT * FROM TSTable WHERE node_id=?',(nid,)).fetchone())
        assert actual==dict(node_id=nid,**r['properties'])
    assert c.execute('SELECT count(*) FROM node').fetchone()[0]==165423
    assert c.execute('SELECT count(*) FROM edge').fetchone()[0]==848238
    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok';c.close()
    with ttlpath.open('wb') as dst,base_ttl.open('rb') as src:shutil.copyfileobj(src,dst);dst.write((package/'patch/source5_additions.ttl').read_bytes())
    assert sha(ttlpath)==m['expected_rebuilt_RDF_sha256']
    assert sha(base_sql)==m['baseline']['SQLite']['sha256'] and sha(base_ttl)==m['baseline']['RDF']['sha256']
    result=dict(status='PASS_FRESH_ISOLATED_ADDITIVE_REBUILD',old89_all_columns_bidirectional_EXCEPT=preserved,new_nodes_n=5,new_directed_edges_n=10,SQL_sha256=sha(dbpath),RDF_sha256=sha(ttlpath),baseline_unchanged=True,native_execution_n=0,model_API_calls_n=0)
    (out/'rebuild_receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

def main():
    a=argparse.ArgumentParser();a.add_argument('--package',type=Path,required=True);a.add_argument('--base-sql',type=Path);a.add_argument('--base-ttl',type=Path);a.add_argument('--out-dir',type=Path);ns=a.parse_args()
    p=ns.package.resolve();m=read(p/'manifest.json');mapping,source=verify_source(p,m)
    result=dict(status='PASS',source_verification=source,source_variant_only=True,frozen_original_gold_changed=False,native_execution_n=0,model_API_calls_n=0)
    if any([ns.base_sql,ns.base_ttl,ns.out_dir]):
        assert all([ns.base_sql,ns.base_ttl,ns.out_dir]);result['isolated_rebuild']=rebuild(p,m,mapping,ns.base_sql.resolve(),ns.base_ttl.resolve(),ns.out_dir.resolve())
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
