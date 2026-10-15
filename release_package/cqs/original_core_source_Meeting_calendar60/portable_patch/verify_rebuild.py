"""Verify actual source windows and optionally rebuild separate calendar stores."""
import argparse
from collections import Counter
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import sqlite3
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
FIELDS=['sourceReportedStartDate','sourceReportedEndDate']
MONTHS={n:i+1 for i,n in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'])}
M='(?:'+'|'.join(MONTHS)+')';DAY=r'\d{1,2}(?:st|nd|rd|th|h)?'
DM=re.compile(r'(?P<d1>'+DAY+r')\s*(?P<m1>'+M+r')?\s*[-–]\s*(?P<d2>'+DAY+r')\s*(?P<m2>'+M+r')\s*,?\s*(?P<year>20\d{2})')
MD=re.compile(r'(?P<m1>'+M+r')\s*(?P<d1>'+DAY+r')\s*[-–]\s*(?:(?P<m2>'+M+r')\s*)?(?P<d2>'+DAY+r')\s*,?\s*(?P<year>20\d{2})')


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()


def read(path):return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def quote(n):return '"'+n.replace('"','""')+'"'
def text(p):
    if p.tag in [W+'t','{http://schemas.openxmlformats.org/officeDocument/2006/math}t']:return p.text or ''
    if p.tag==W+'tab':return '\t'
    if p.tag in [W+'br',W+'cr']:return '\n'
    return ''.join(text(c) for c in p)
def compact(v):return ''.join(v.split())
def period(v):
    hits=[m for rx in [DM,MD] for m in rx.finditer(v)];assert len(hits)==1
    d=hits[0].groupdict();y=int(d['year'])
    start=datetime.date(y,MONTHS[d['m1'] or d['m2']],int(re.match(r'\d+',d['d1'])[0]))
    end=datetime.date(y,MONTHS[d['m2'] or d['m1']],int(re.match(r'\d+',d['d2'])[0]));assert start<=end
    return start.isoformat(),end.isoformat()


def source(manifest):
    for p in manifest['files']:
        path=HERE/p['path'];assert path.is_file() and path.stat().st_size==p['bytes'] and sha(path)==p['sha256'],p['path']
    sources=read(HERE/'source/all192_own_report_source_identity_and_period_ledger.jsonl')
    ledger=read(HERE/'source/all60_source_reported_Meeting_period_ledger.jsonl')
    raw=read(HERE/'source/all192_authored_raw_frontmatter_inputs.jsonl')
    fragments=json.loads((HERE/'source/all192_frontmatter_fragment_provenance.json').read_text())['records']
    assert len(sources)==len(raw)==len(fragments)==192 and len(ledger)==60
    source_by_key={(s['source_archive']['path'],s['member']):s for s in sources}
    raw_by_row={r['source_row']:r for r in raw};actual={}
    for f in fragments:
        key=(f['original_source_archive_pin']['path'],f['original_member']);s=source_by_key[key];r=raw_by_row[f['raw_source_row']]
        assert f['original_source_archive_pin']==s['source_archive'] and f['original_member_sha256']==s['member_sha256']
        assert f['original_full_document_XML_sha256']==s['document_XML_sha256']
        assert len(f['eight_authored_ET_utf8_paragraph_fragments'])==8
        vals=[]
        for i,pin in enumerate(f['eight_authored_ET_utf8_paragraph_fragments']):
            p=HERE/pin['path'];assert sha(p)==pin['sha256']==r['source_cell_coordinates']['paragraph_ElementTree_utf8_XML_sha256'][i]
            assert pin['paragraph_zero_based']==i
            vals.append(text(ET.fromstring(p.read_bytes())))
        assert vals==[p['literal_authored_text_with_tabs_and_breaks'] for p in r['fields']['paragraphs']]
        ti,di=s['title_all_document_paragraph_index'],s['date_all_document_paragraph_index']
        assert 0<=ti<8 and di==ti+1 and di<8
        assert compact(vals[ti])==compact(s['title_literal']) and compact(vals[di])==compact(s['period']['literal'])
        dates=period(vals[di]);assert dates==(s['period']['start'],s['period']['end'])
        actual[key]=dates
    for l in ledger:
        assert l['all_matched_source_reports']
        for s in l['all_matched_source_reports']:
            key=(s['source_archive']['path'],s['member']);assert source_by_key[key]==s
            assert actual[key]==tuple(l[k] for k in FIELDS)
    mappings=json.loads((HERE/'patch/all60_existing_Meeting_property_delta_mapping.json').read_text())['all60_Meeting_property_deltas']
    assert len(mappings)==60 and len({r['node_id'] for r in mappings})==60
    by_node={r['frozen_Meeting']['node_id']:r for r in ledger}
    for r in mappings:
        assert r['added_properties']=={k:by_node[r['node_id']][k] for k in FIELDS}
        assert not set(FIELDS)&set(r['original_properties'])
    assert len((HERE/'patch/source_reported_Meeting_period_additions.nt').read_text().splitlines())==120
    return mappings


def rebuild(manifest,mappings,args):
    assert args.base_sql and args.base_ttl and args.rebuild_dir
    assert sha(args.base_sql)==manifest['baseline_SQL']['sha256']
    assert sha(args.base_ttl)==manifest['baseline_TTL']['sha256']
    assert not args.rebuild_dir.exists();args.rebuild_dir.mkdir()
    sql_path=args.rebuild_dir/'RAN1.sqlite';shutil.copy2(args.base_sql,sql_path)
    c=sqlite3.connect(sql_path);c.row_factory=sqlite3.Row
    c.execute('ATTACH DATABASE ? AS baseline',(str(args.base_sql),))
    tables=[r[0] for r in c.execute("SELECT name FROM baseline.sqlite_master WHERE type='table' ORDER BY name")];assert len(tables)==89
    cols={t:[r[1] for r in c.execute('PRAGMA baseline.table_info('+quote(t)+')')] for t in tables}
    with c:
        for k in FIELDS:c.execute('ALTER TABLE Meeting ADD COLUMN '+quote(k)+' ANY')
        for r in mappings:
            old=c.execute('SELECT properties_json,source_iri FROM _node_record WHERE node_id=?',(r['node_id'],)).fetchone()
            assert old and json.loads(old['properties_json'])==r['original_properties'] and old['source_iri']==r['source_iri']
            assert not c.execute('SELECT1 FROM node_property WHERE node_id=? AND key IN (?,?)'.replace('SELECT1','SELECT 1'),(r['node_id'],*FIELDS)).fetchone()
            c.execute('UPDATE Meeting SET sourceReportedStartDate=?,sourceReportedEndDate=? WHERE node_id=?',(*[r['added_properties'][k] for k in FIELDS],r['node_id']))
            c.execute('UPDATE _node_record SET properties_json=? WHERE node_id=?',(canon({**r['original_properties'],**r['added_properties']}),r['node_id']))
            c.executemany('INSERT INTO node_property VALUES(?,?,?,?)',[(r['node_id'],k,'string',canon(v)) for k,v in r['added_properties'].items()])
    changed={r['node_id']:r['added_properties'] for r in mappings};preserved={}
    for t in tables:
        names=','.join(quote(k) for k in cols[t])
        if t=='_node_record':
            count=0
            for row in c.execute('SELECT a.node_id,a.source_iri,a.labels_json,a.properties_json,b.source_iri,b.labels_json,b.properties_json FROM main._node_record a JOIN baseline._node_record b USING(node_id)'):
                nid,iri,labels,new,oldiri,oldlabels,old=row;assert iri==oldiri and labels==oldlabels
                assert json.loads(new)=={**json.loads(old),**changed[nid]} if nid in changed else new==old
                count+=1
            assert count==165418
        else:
            suffix=" WHERE key NOT IN ('sourceReportedStartDate','sourceReportedEndDate')" if t=='node_property' else ''
            for left,right in [('baseline','main'),('main','baseline')]:
                a=suffix if left=='main' else '';b=suffix if right=='main' else ''
                assert c.execute('SELECT count(*) FROM (SELECT '+names+' FROM '+left+'.'+quote(t)+a+' EXCEPT SELECT '+names+' FROM '+right+'.'+quote(t)+b+')').fetchone()[0]==0,t
        preserved[t]=True
    assert c.execute('SELECT count(*) FROM node').fetchone()[0]==165418
    assert c.execute('SELECT count(*) FROM edge').fetchone()[0]==848228
    assert c.execute('SELECT count(*) FROM node_property').fetchone()[0]==1194916
    rows=[dict(r) for r in c.execute("SELECT cr.tdocNumber AS tdocNumber,MAX(m.sourceReportedEndDate) AS meetingPeriodEndDate FROM CR cr JOIN rel_PRESENTED_AT e ON e.src_id=cr.node_id JOIN Meeting m ON m.node_id=e.dst_id WHERE cr.node_id IN (SELECT x.src_id FROM rel_MODIFIES x JOIN Spec s ON s.node_id=x.dst_id WHERE s.specNumber='38.213') GROUP BY cr.node_id,cr.tdocNumber ORDER BY meetingPeriodEndDate DESC,tdocNumber ASC")]
    expected=read(HERE/'evidence/actual_query_native_full3041_records.jsonl');assert rows==expected and len(rows)==3041
    c.close()
    ttl_path=args.rebuild_dir/'RAN1-source-reported-Meeting-periods-body.ttl'
    with ttl_path.open('wb') as out,args.base_ttl.open('rb') as src:
        shutil.copyfileobj(src,out);out.write((HERE/'patch/source_reported_Meeting_period_additions.ttl').read_bytes())
    assert sha(ttl_path)=='d5b6da096c81927989f0823b75420c6199572de9b25b189fb95c8827b089cbc3'
    assert sha(args.base_sql)==manifest['baseline_SQL']['sha256'] and sha(args.base_ttl)==manifest['baseline_TTL']['sha256']
    receipt={'status':'pass','all89_original_SQL_table_preservation':preserved,'native_full3041_rebuilt_SQL_all_fields_equal':True,
        'rebuilt_SQL_sha256':sha(sql_path),'rebuilt_TTL_sha256':sha(ttl_path),'baseline_bytes_unchanged':True,
        'new_nodes_n':0,'new_relationships_n':0,'added_properties_n':120,'native_API_calls_n':0}
    (args.rebuild_dir/'rebuild_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base-sql',type=Path);p.add_argument('--base-ttl',type=Path);p.add_argument('--rebuild-dir',type=Path);args=p.parse_args()
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    manifest=json.loads((HERE/'manifest.json').read_text());mappings=source(manifest)
    result={'status':'pass','all192_actual_authored_XML_windows_n':192,'raw_paragraphs_n':1536,'all60_added_period_source_support':True,
        'original_report_body_equality_established':False,'model_native_calls_n':0}
    if args.base_sql or args.base_ttl or args.rebuild_dir:result['rebuild']=rebuild(manifest,mappings,args)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))


if __name__=='__main__':main()
