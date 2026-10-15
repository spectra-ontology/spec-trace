"""Fresh whole-body source inputs; bounded streaming output, no model/native calls.

All342 retained Word report document.xml bodies and every XML text paragraph in
the four retained PPTX packages are supplied without selecting eligible CRs or
dates. Raw tracked runs, empty paragraphs, tabs and line breaks are preserved.
Legacy DOC access derivatives remain explicitly identified, not re-converted.
"""
from io import BytesIO
import json
import os
from pathlib import Path
import resource
import zipfile
from lxml import etree
from prepare_RAN4_calendar58_authored_raw_retrieval_inputs_v1 import HERE,B,ROOT,CAL,W,M,A,pin,read,save,canon,sha,raw_text,member_bytes,arrangements_sources

OUT=HERE/'calendar58_authored_full_raw_retrieval_inputs_v2'
SHARD_BYTES=64*1024**2

def store_binary(data,stem):
    records=[]
    for n,start in enumerate(range(0,len(data),SHARD_BYTES)):
        p=OUT/'original_package_bytes'/f'{stem}_{n:03d}.bin';p.write_bytes(data[start:start+SHARD_BYTES])
        records.append({'relative_path':str(p.relative_to(OUT)),'sha256':sha(data[start:start+SHARD_BYTES]),'bytes':p.stat().st_size})
    return {'sha256':sha(data),'bytes':len(data),'ordered_bin_shards':records}

def chunks(paragraphs):
    values=[];start=0;chars=0
    for i,p in enumerate(paragraphs):
        literal=raw_text(p)
        if values and(chars+len(literal)>6000 or len(values)>=128):
            yield start,values
            start=i;values=[];chars=0
        values.append(literal);chars+=len(literal)
    if values:yield start,values

def main():
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    assert not OUT.exists();OUT.mkdir();(OUT/'original_package_bytes').mkdir()
    source_path=CAL/'all_original_report_raw_frontmatter_event_member_inputs.jsonl'
    sources=read(source_path);assert len(sources)==342
    raw_path=OUT/'all342_report_whole_body_and4_whole_PPTX_authored_raw_inputs.jsonl'
    verified=set();inventories=[];raw_n=0;paragraph_n=0;chars_n=0
    with raw_path.open('w')as out:
        for i,s in enumerate(sources):
            data=member_bytes(s,verified)
            original=Path(s['original_source_file_pin']['path'])
            if original.suffix.lower()=='.zip':
                with zipfile.ZipFile(original)as z:original_member=z.read(s['archive_member'])
            else:original_member=original.read_bytes()
            assert sha(original_member)==s['original_member_sha256']
            original_pack=store_binary(original_member,f'report_{i:03d}_original_member')
            derivative=store_binary(data,f'report_{i:03d}_access_derivative')if 'legacy_conversion'in s else None
            with zipfile.ZipFile(BytesIO(data))as z:xml=z.read('word/document.xml')
            assert sha(xml)==s['document_XML_sha256']
            root=etree.fromstring(xml);body=root.find(W+'body');assert body is not None
            ps=list(body.iter(W+'p'));assert len(ps)==s['all_document_raw_paragraphs_n']
            first=[{'all_document_raw_paragraph_zero_based':j,'literal_authored_text_with_tabs_and_breaks':raw_text(p),
                'lxml_UTF8_serialized_paragraph_XML_sha256':sha(etree.tostring(p,encoding='utf-8'))}for j,p in enumerate(ps[:120])]
            assert first==s['first120_all_document_raw_paragraphs']
            count=0;start_row=raw_n
            for start,literals in chunks(ps):
                r={'source_row':s['original_source_relative_path']+':'+s['archive_member']+f':body_p{start}_{start+len(literals)-1}',
                    'fields':{'source':'Retained original RAN4 report entire Word document body','filename':s['archive_member'],
                        'origin':s['source_access_path']+('; pinned DOC access derivative'if derivative else''),
                        'paragraph_texts_in_document_order':literals},
                    'source_cell_coordinates':{'original_source_relative_path':s['original_source_relative_path'],
                        'original_source_sha256':s['original_source_file_pin']['sha256'],'member_sha256':s['original_member_sha256'],
                        'member_CRC32':s['original_member_CRC32'],'document_XML_sha256':s['document_XML_sha256'],
                        'paragraph_range_zero_based':[start,start+len(literals)-1],
                        'paragraph_axis':'All w:p descendants of actual w:body, including nested table/SDT paragraphs in XML document order',
                        'raw_projection':'Every raw w:t/m:t, Word tab/br/cr including tracked runs; no final-state, own-role, date or approval interpretation'}}
                if derivative:r['source_cell_coordinates']['legacy_access_derivative_DOCX_sha256']=s['legacy_conversion']['output_DOCX_pin']['sha256']
                out.write(canon(r)+'\n');raw_n+=1;count+=len(literals);chars_n+=sum(map(len,literals))
            assert count==len(ps);paragraph_n+=count
            inventories.append({'kind':'whole_Word_body','original_source_pin':s['original_source_file_pin'],'member':s['archive_member'],
                'original_member_bytes':original_pack,'access_derivative_bytes':derivative,'legacy_conversion_provenance':s.get('legacy_conversion'),
                'full_document_XML_sha256':sha(xml),'all_body_paragraphs_n':count,'raw_row_range_zero_based':[start_row,raw_n-1],
                'fresh_all_body_paragraphs_projected':True,'access_derivative_reconversion_performed':False})
            del root,body,ps,xml,data,original_member
            if(i+1)%16==0:print(canon({'whole_reports':i+1,'paragraphs':paragraph_n,'raw_chunks':raw_n,'text_characters':chars_n}),flush=True)
        arrangements,locator_pins=arrangements_sources()
        for i,s in enumerate(arrangements):
            original=Path(s['archive_pin']['path']);assert pin(original)==s['archive_pin']
            with zipfile.ZipFile(original)as z:
                info=z.getinfo(s['member']);data=z.read(info)
            if 'member_sha256'in s:assert sha(data)==s['member_sha256']and info.CRC==s['member_CRC32']
            pack=store_binary(data,f'arrangements_{i:02d}_original_member');start_row=raw_n;parts=[]
            with zipfile.ZipFile(BytesIO(data))as z:
                for name in sorted(z.namelist()):
                    if not name.lower().endswith('.xml'):continue
                    xml=z.read(name);tree=etree.fromstring(xml)
                    ps=[p for p in tree.iter()if p.tag in {A+'p',W+'p'}]
                    count=0
                    for start,literals in chunks(ps):
                        r={'source_row':str(original.relative_to(ROOT))+':'+s['member']+':'+name+f':p{start}_{start+len(literals)-1}',
                            'fields':{'source':'Original RAN4 arrangements entire PPTX XML paragraph text','filename':s['member'],
                                'origin':name,'paragraph_texts_in_part_order':literals},
                            'source_cell_coordinates':{'original_source_relative_path':str(original.relative_to(ROOT)),
                                'original_source_sha256':s['archive_pin']['sha256'],'member_sha256':sha(data),'member_CRC32':info.CRC,
                                'part_path':name,'part_XML_sha256':sha(xml),'paragraph_range_zero_based':[start,start+len(literals)-1],
                                'paragraph_axis':'Every DrawingML a:p/Word w:p in actual XML part order; all XML parts including slides, notes, masters and layouts',
                                'raw_projection':'Raw a:t/w:t/m:t plus literal tabs/breaks and empty paragraphs; no approval/date normalization'}}
                        out.write(canon(r)+'\n');raw_n+=1;count+=len(literals);chars_n+=sum(map(len,literals))
                    parts.append({'part_path':name,'XML_sha256':sha(xml),'paragraphs_n':count});paragraph_n+=count
                    if name=='ppt/slides/slide1.xml':assert[raw_text(p)for p in ps]==s['all_raw_slide_paragraphs']
            inventories.append({'kind':'whole_PPTX_package','original_source_pin':s['archive_pin'],'member':s['member'],
                'original_member_bytes':pack,'raw_row_range_zero_based':[start_row,raw_n-1],'all_XML_part_inventory':parts,
                'all_package_bytes_preserved':True,'whole_binary_package_interpretation_claimed':False})
    shards=[]
    with raw_path.open('rb')as src:
        n=0
        while block:=src.read(SHARD_BYTES):
            p=OUT/f'authored_raw_inputs_shard_{n:03d}.bin';p.write_bytes(block)
            shards.append({'relative_path':p.name,'sha256':sha(block),'bytes':len(block)});n+=1
    assert len(inventories)==346 and paragraph_n>=6755948
    save(OUT/'whole_authored_raw_inventory.json',{'status':'all342_whole_Word_bodies_and4_whole_PPTX_XML_text_freshly_projected',
        'raw_inputs_pin':pin(raw_path),'raw_inputs_ordered_bin_shards':shards,'source342_inventory_pin':pin(source_path),
        'original_Word_body_observations_n':342,'whole_PPTX_packages_n':4,'legacy_DOC_access_derivatives_n':23,
        'raw_rows_n':raw_n,'actual_raw_paragraphs_n':paragraph_n,'actual_raw_text_characters_n':chars_n,'records':inventories,
        'raw_selection_used_gold_query_or_model_results':False,'parsed_ISO_or_canonical_labels_supplied':False,
        'all_original_package_member_bytes_preserved':True,'all_Word_document_body_paragraphs_projected':True,
        'every_PPTX_XML_part_listed':True,'full_binary_object_semantics_or_OCR_established':False,
        'raw_tracked_runs_are_not_a_final_visible_state_interpretation':True,'legacy_reconversion_performed':False,
        'human_author_review_completed':False,'expert_validation_n':0,'native_API_public_calls_n':0,'helper_pin':pin(Path(__file__))})
    print(canon({'inventory':pin(OUT/'whole_authored_raw_inventory.json'),'raw_rows_n':raw_n,'raw_bytes':raw_path.stat().st_size}),flush=True)

if __name__=='__main__':main()
