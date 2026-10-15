"""Verify all source windows and optionally rebuild separate immutable stores.

Portable source verification checks raw XML/literal correspondence and complete
own-period date alternatives. Root's fresh original-file proof and both exact
semantic judgments remain separately pinned; this script is not expert review.
"""
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
MATH='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
FIELDS=['sourceReportedStartDate','sourceReportedEndDate']
MONTHS={n.lower():i+1 for i,n in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'])}
MONTHS.update({n[:3]:v for n,v in list(MONTHS.items())});MONTHS['sept']=9
M=r'(?:'+'|'.join(sorted(MONTHS,key=len,reverse=True))+r')\.?'
D=r'\d{1,2}(?:st|nd|rd|th)?'
DM=re.compile(r'(?P<d1>'+D+r')\s*(?P<m1>'+M+r')?\s*(?:[-–]|to)\s*(?P<d2>'+D+r')\s*(?:of\s+)?(?P<m2>'+M+r')\s*,?\s*(?P<y>20\d{2})',re.I)
MD=re.compile(r'(?P<m1>'+M+r')\s*(?P<d1>'+D+r')\s*(?:[-–]|to)\s*(?:(?P<m2>'+M+r')\s*)?(?P<d2>'+D+r')\s*,?\s*(?P<y>20\d{2})',re.I)
NUM=re.compile(r'(\d{1,2})/(\d{1,2})/(20\d{2})\s*(?:to|[-–])\s*(\d{1,2})/(\d{1,2})/(20\d{2})')


def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def read(path):return [json.loads(l)for l in path.read_text().splitlines()if l.strip()]
def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def quote(n):return '"'+n.replace('"','""')+'"'
def text(p):
    parts=[]
    for e in p.iter():
        if e.tag in {W+'t',MATH+'t',A+'t'}:parts.append(e.text or '')
        elif e.tag==W+'tab':parts.append('\t')
        elif e.tag in {W+'br',W+'cr',A+'br'}:parts.append('\n')
    return ''.join(parts)


def periods(literal):
    literal=' '.join(literal.split());out=set()
    numeric=list(NUM.finditer(literal))
    if numeric:
        assert len(numeric)==1
        a,b,y,c,d,z=map(int,numeric[0].groups())
        for m1,d1,m2,d2 in [(b,a,d,c),(a,b,c,d)]:
            try:
                start,end=datetime.date(y,m1,d1),datetime.date(z,m2,d2)
                if start<=end:out.add((start.isoformat(),end.isoformat()))
            except ValueError:pass
    else:
        hits=[m for rx in [DM,MD]for m in rx.finditer(literal)]
        assert len({(m.span(),m.group())for m in hits})==1,literal
        m=hits[0];d=m.groupdict();y=int(d['y'])
        m1=(d['m1']or d['m2']).lower().rstrip('.');m2=(d['m2']or d['m1']).lower().rstrip('.')
        start=datetime.date(y,MONTHS[m1],int(re.match(r'\d+',d['d1'])[0]))
        end=datetime.date(y,MONTHS[m2],int(re.match(r'\d+',d['d2'])[0]));assert start<=end
        out.add((start.isoformat(),end.isoformat()))
    assert out,literal
    return out


def source(manifest):
    for item in manifest['files']:
        p=HERE/item['path'];assert p.is_file()and p.stat().st_size==item['bytes']and sha(p)==item['sha256'],item['path']
    inventory=json.loads((HERE/'source/raw_source_inventory.json').read_text())
    raw=read(HERE/'source/all342_report_first120_and4_authored_arrangements_raw_inputs.jsonl')
    ledger=read(HERE/'source/all58_source_reported_Meeting_period_ledger.jsonl')
    assert len(raw)==346 and len(ledger)==58 and len(inventory['records'])==346
    rawbyrow={r['source_row']:r for r in raw};rawbykey={};slide_periods={}
    for i,record in enumerate(inventory['records']):
        p=HERE/record['window_relative_path'];assert sha(p)==record['window_pin']['sha256']
        root=ET.parse(p).getroot();elements=list(root)if i<342 else list(root.iter(A+'p'))
        values=[text(e)for e in elements]
        row=rawbyrow[record['source_row']]
        assert values==[r['literal_authored_text_with_tabs_and_breaks']for r in row['fields']['paragraphs']]
        assert len(elements)==record['paragraphs_n']
        if i<342:rawbykey[(record['original_source_pin']['path'],record['member'])]=values
        else:
            own=[re.search(r'Meeting\s*#\s*(\d+)\s*((?:-?\s*(?:bis|e))*)',v,re.I)for v in values]
            own=[m for m in own if m];assert len(own)==1
            suffix=re.sub(r'[\s-]','',own[0][2]).lower()
            key='RAN4#'+own[0][1]+('bis'if'bis'in suffix else'')
            candidates=[periods(v)for v in values if NUM.search(v)or DM.search(v)or MD.search(v)]
            assert len(candidates)==1 and len(candidates[0])==1
            slide_periods[key]=candidates[0]
    assert len(slide_periods)==4
    checks=0
    by_node={}
    for item in ledger:
        alternatives=None
        for s in item['all_identity_matched_source_report_witnesses']:
            values=rawbykey[(s['original_source_file_pin']['path'],s['archive_member'])]
            ti=s['actual_title_paragraph']['all_document_raw_paragraph_zero_based']
            di=s['actual_immediately_following_period_paragraph']['all_document_raw_paragraph_zero_based']
            assert di==ti+1 and 0<=ti<di<len(values)
            assert values[ti]==s['actual_title_paragraph']['literal_authored_text_with_tabs_and_breaks']
            assert values[di]==s['actual_immediately_following_period_paragraph']['literal_authored_text_with_tabs_and_breaks']
            current=periods(values[di]);alternatives=current if alternatives is None else alternatives&current
            checks+=1
        key=item['own_canonical_Meeting']
        if key in slide_periods:alternatives &=slide_periods[key]
        expected=tuple(item[k]for k in FIELDS)
        assert alternatives=={expected},(key,alternatives,expected)
        by_node[item['original_frozen_Meeting']['node_id']]=item
    assert checks==321
    mappings=json.loads((HERE/'patch/all58_existing_Meeting_property_delta_mapping.json').read_text())['all58_Meeting_property_deltas']
    assert len(mappings)==58==len({r['node_id']for r in mappings})
    for r in mappings:
        assert r['added_properties']=={k:by_node[r['node_id']][k]for k in FIELDS}
        assert not set(FIELDS)&set(r['original_properties'])
    assert len((HERE/'patch/source_reported_Meeting_period_additions.nt').read_text().splitlines())==116
    return mappings


def rebuild(manifest,mappings,args):
    assert args.base_sql and args.base_ttl and args.rebuild_dir
    assert sha(args.base_sql)==manifest['baseline_SQL']['sha256']
    assert sha(args.base_ttl)==manifest['baseline_TTL']['sha256']
    assert not args.rebuild_dir.exists();args.rebuild_dir.mkdir()
    sql_path=args.rebuild_dir/'RAN4.sqlite';shutil.copy2(args.base_sql,sql_path)
    c=sqlite3.connect(sql_path);c.row_factory=sqlite3.Row
    c.execute('ATTACH DATABASE ? AS baseline',(str(args.base_sql),))
    tables=[r[0] for r in c.execute("SELECT name FROM baseline.sqlite_master WHERE type='table' ORDER BY name")];assert len(tables)==80
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
            assert count==342161
        else:
            suffix=" WHERE key NOT IN ('sourceReportedStartDate','sourceReportedEndDate')" if t=='node_property' else ''
            for left,right in [('baseline','main'),('main','baseline')]:
                a=suffix if left=='main' else '';b=suffix if right=='main' else ''
                assert c.execute('SELECT count(*) FROM (SELECT '+names+' FROM '+left+'.'+quote(t)+a+' EXCEPT SELECT '+names+' FROM '+right+'.'+quote(t)+b+')').fetchone()[0]==0,t
        preserved[t]=True
    assert c.execute('SELECT count(*) FROM node').fetchone()[0]==342161
    assert c.execute('SELECT count(*) FROM edge').fetchone()[0]==1592845
    assert c.execute('SELECT count(*) FROM node_property').fetchone()[0]==2281406
    rows=[dict(r) for r in c.execute("SELECT cr.tdocNumber AS tdocNumber,MAX(m.sourceReportedEndDate) AS meetingPeriodEndDate FROM CR cr JOIN rel_PRESENTED_AT e ON e.src_id=cr.node_id JOIN Meeting m ON m.node_id=e.dst_id WHERE cr.node_id IN (SELECT x.src_id FROM rel_MODIFIES x JOIN Spec s ON s.node_id=x.dst_id WHERE s.specNumber='38.133') GROUP BY cr.node_id,cr.tdocNumber ORDER BY meetingPeriodEndDate DESC,tdocNumber ASC")]
    expected=read(HERE/'evidence/actual_query_native_full16017_records.jsonl');assert rows==expected and len(rows)==16017
    c.close()
    ttl_path=args.rebuild_dir/'RAN4-source-reported-Meeting-periods-body.ttl'
    with ttl_path.open('wb') as out,args.base_ttl.open('rb') as src:
        shutil.copyfileobj(src,out);out.write((HERE/'patch/source_reported_Meeting_period_additions.ttl').read_bytes())
    assert sha(ttl_path)=='1af748f08f74f1393d15c63e14590b0bccf7459b95e6102b10aa383905bc295e'
    assert sha(args.base_sql)==manifest['baseline_SQL']['sha256'] and sha(args.base_ttl)==manifest['baseline_TTL']['sha256']
    receipt={'status':'pass','all80_original_SQL_table_preservation':preserved,'native_full16017_rebuilt_SQL_all_fields_equal':True,
        'rebuilt_SQL_sha256':sha(sql_path),'rebuilt_TTL_sha256':sha(ttl_path),'baseline_bytes_unchanged':True,
        'new_nodes_n':0,'new_relationships_n':0,'added_properties_n':116,'native_API_calls_n':0}
    (args.rebuild_dir/'rebuild_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt



def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base-sql',type=Path);ap.add_argument('--base-ttl',type=Path);ap.add_argument('--rebuild-dir',type=Path)
    args=ap.parse_args();os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    manifest=json.loads((HERE/'manifest.json').read_text());mappings=source(manifest)
    result={'status':'pass','all342_actual_authored_report_windows':True,'four_actual_authored_calendar_slides':True,
        'all321_own_title_adjacent_periods_checked':True,'all58_added_periods_derived_from_unambiguous_intersections':True,
        'original_report_body_equality_established':False,'model_native_calls_n':0}
    if args.base_sql or args.base_ttl or args.rebuild_dir:result['rebuild']=rebuild(manifest,mappings,args)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))


if __name__=='__main__':main()
