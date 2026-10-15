"""Verify exact whole authored inputs and optionally rebuild the separate property patch.

Original342 report member packages (23 legacyDOC access derivatives identified)
and4 PPTX packages are re-read, with every Word-body paragraph and every PPTX XML
paragraph compared to supplied raw chunks. Raw text projection is explicit;
OCR, binary objects and final-visible interpretation are not claimed.
"""
from io import BytesIO
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import tempfile
import xml.etree.ElementTree as ET
import zipfile

HERE=Path(__file__).resolve().parent
FULL=HERE/'source/full_authored_raw_v2'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def text(p):
    result=[]
    for e in p.iter():
        if e.tag in{W+'t',M+'t',A+'t'}:result.append(e.text or'')
        elif e.tag==W+'tab':result.append('\t')
        elif e.tag in{W+'br',W+'cr',A+'br'}:result.append('\n')
    return ''.join(result)

def package(spec):
    data=[]
    for s in spec['ordered_bin_shards']:
        p=FULL/s['relative_path'];assert p.stat().st_size==s['bytes']and sha(p)==s['sha256'];data.append(p.read_bytes())
    data=b''.join(data);assert len(data)==spec['bytes']and hashlib.sha256(data).hexdigest()==spec['sha256'];return data

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def source(manifest):
    for r in manifest['files']:
        p=HERE/r['path'];assert p.stat().st_size==r['bytes']and sha(p)==r['sha256'],r['path']
    inventory=json.loads((FULL/'whole_authored_raw_inventory.json').read_text())
    assert len(inventory['records'])==346 and inventory['raw_rows_n']==61730
    ledger=[json.loads(l)for l in(HERE/'source/all58_source_reported_Meeting_period_ledger.jsonl').read_text().splitlines()]
    wanted={}
    for item in ledger:
        for s in item['all_identity_matched_source_report_witnesses']:
            key=(s['original_source_file_pin']['path'],s['archive_member'])
            for role in['actual_title_paragraph','actual_immediately_following_period_paragraph']:
                p=s[role];wanted.setdefault(key,{})[p['all_document_raw_paragraph_zero_based']]=p['literal_authored_text_with_tabs_and_breaks']
    supported=set();paragraphs_n=0;rows_n=0;report_n=0;pptx_n=0
    with tempfile.TemporaryDirectory(prefix='spectra-source58-whole-read-')as directory:
        raw=Path(directory)/'raw.jsonl'
        h=hashlib.sha256()
        with raw.open('wb')as out:
            for s in inventory['raw_inputs_ordered_bin_shards']:
                p=FULL/s['relative_path'];assert p.stat().st_size==s['bytes']and sha(p)==s['sha256']
                with p.open('rb')as stream:
                    for b in iter(lambda:stream.read(1048576),b''):h.update(b);out.write(b)
        assert h.hexdigest()==inventory['raw_inputs_pin']['sha256']and raw.stat().st_size==inventory['raw_inputs_pin']['bytes']
        with raw.open()as stream:
            def compare(ps,first,last,filename,xmlsha):
                nonlocal paragraphs_n,rows_n
                cursor=0
                for ordinal in range(first,last+1):
                    r=json.loads(next(stream));assert set(r)=={'source_row','fields','source_cell_coordinates'}
                    c=r['source_cell_coordinates'];start,end=c['paragraph_range_zero_based']
                    values=r['fields'].get('paragraph_texts_in_document_order',r['fields'].get('paragraph_texts_in_part_order'))
                    assert r['fields']['filename']==filename and start==cursor and end-start+1==len(values)
                    assert(c.get('document_XML_sha256')or c.get('part_XML_sha256'))==xmlsha
                    assert values==[text(p)for p in ps[start:end+1]]
                    cursor=end+1;paragraphs_n+=len(values);rows_n+=1
                assert cursor==len(ps)
            for record in inventory['records']:
                data=package(record['original_member_bytes'])
                start,end=record['raw_row_range_zero_based'];assert start==rows_n
                if record['kind']=='whole_Word_body':
                    if record['access_derivative_bytes']is not None:data=package(record['access_derivative_bytes'])
                    with zipfile.ZipFile(BytesIO(data))as z:xml=z.read('word/document.xml')
                    assert hashlib.sha256(xml).hexdigest()==record['full_document_XML_sha256']
                    root=ET.fromstring(xml);ps=list(root.find(W+'body').iter(W+'p'))
                    assert len(ps)==record['all_body_paragraphs_n']
                    compare(ps,start,end,record['member'],record['full_document_XML_sha256']);report_n+=1
                    key=(record['original_source_pin']['path'],record['member'])
                    for index,literal in wanted.get(key,{}).items():
                        assert text(ps[index])==literal;supported.add((key,index))
                    del root,ps,xml,data
                else:
                    assert record['kind']=='whole_PPTX_package';pptx_n+=1
                    with zipfile.ZipFile(BytesIO(data))as z:
                        names=sorted(n for n in z.namelist()if n.lower().endswith('.xml'))
                        assert names==[p['part_path']for p in record['all_XML_part_inventory']]
                        for part in record['all_XML_part_inventory']:
                            xml=z.read(part['part_path']);assert hashlib.sha256(xml).hexdigest()==part['XML_sha256']
                            ps=[p for p in ET.fromstring(xml).iter()if p.tag in{A+'p',W+'p'}]
                            assert len(ps)==part['paragraphs_n']
                            cursor=0
                            while cursor<len(ps):
                                r=json.loads(next(stream));c=r['source_cell_coordinates'];a,b=c['paragraph_range_zero_based']
                                assert a==cursor and c['part_path']==part['part_path']and c['part_XML_sha256']==part['XML_sha256']
                                values=r['fields']['paragraph_texts_in_part_order'];assert b-a+1==len(values)
                                assert values==[text(p)for p in ps[a:b+1]]
                                rows_n+=1;paragraphs_n+=len(values);cursor=b+1
                    assert rows_n==end+1
            assert stream.read()==''
    assert(report_n,pptx_n,rows_n,paragraphs_n)==(342,4,inventory['raw_rows_n'],inventory['actual_raw_paragraphs_n'])
    assert supported=={(key,index)for key,values in wanted.items()for index in values}
    mappings=json.loads((HERE/'patch/all58_existing_Meeting_property_delta_mapping.json').read_text())['all58_Meeting_property_deltas']
    by_node={r['original_frozen_Meeting']['node_id']:r for r in ledger}
    assert len(by_node)==len(mappings)==58
    for r in mappings:
        assert r['added_properties']=={k:by_node[r['node_id']][k]for k in['sourceReportedStartDate','sourceReportedEndDate']}
        assert not set(r['added_properties'])&set(r['original_properties'])
    return mappings,{'status':'pass','whole342_Word_bodies_exact_raw_projection':True,'whole4_PPTX_packages_and_all_XML_paragraphs_exact':True,
        'raw_rows_n':rows_n,'actual_paragraphs_n':paragraphs_n,'all321_own_title_adjacent_period_witnesses_supported':True,
        'source_period_interpretation_evidence':'Two exactsource reviews and rootfresh342 proof pinned separately; all58 date mappings preserved',
        'OCR_or_embedded_binary_object_semantics_established':False,'human_author_review_completed':False,'expert_validation_n':0,'native_API_calls_n':0}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--base-sql',type=Path);ap.add_argument('--base-ttl',type=Path);ap.add_argument('--rebuild-dir',type=Path)
    args=ap.parse_args();os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    manifest=json.loads((HERE/'manifest.json').read_text());mappings,result=source(manifest)
    if args.base_sql or args.base_ttl or args.rebuild_dir:
        prop=module(HERE/'source58_property_rebuild.py','source58_unchanged_property_rebuild');result['rebuild']=prop.rebuild(manifest,mappings,args)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()
