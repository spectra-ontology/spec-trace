#!/usr/bin/env python3
"""Independently reopen every matched report and the changed native headings."""
import argparse
from collections import Counter
import ctypes
import gc
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'.git').exists())


def hash_bytes(data):return hashlib.sha256(data).hexdigest()


def body(data):
    with zipfile.ZipFile(io.BytesIO(data)) as zipped:
        xml=zipped.read('word/document.xml')
    return ET.fromstring(xml).find(W+'body'),xml


def text(element, separators=False):
    parts=[]
    for child in element.iter():
        if child.tag==W+'t':parts.append(child.text or '')
        elif separators and child.tag==W+'tab':parts.append('\t')
        elif separators and child.tag in [W+'br',W+'cr']:parts.append('\n')
    return ''.join(parts)


def visible_rows(native_body):
    rows=[]
    for element in native_body:
        if element.tag==W+'p':rows.append(text(element))
        elif element.tag==W+'tbl':
            for row in element.findall(W+'tr'):
                for cell in row.findall(W+'tc'):
                    rows.extend(text(p) for p in cell.findall('.//'+W+'p'))
    return [re.sub(r'\s+',' ',row).strip() for row in rows]


def fingerprint(data):
    native_body,xml=body(data)
    rows=visible_rows(native_body)
    return hash_bytes(xml),hash_bytes(json.dumps(rows,ensure_ascii=False).encode()),len(rows)


def release_memory():
    gc.collect()
    # Return large XML allocation arenas to the guarded process budget.
    try:ctypes.CDLL(None).malloc_trim(0)
    except AttributeError:pass


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();data=json.loads(args.results.read_text())
    checked=[];scopes=Counter()
    for retained,proof in data['report_authentication'].items():
        if not proof['native_matches']:continue
        raw=(ROOT/retained).read_bytes();assert hash_bytes(raw)==proof['retained_sha256']
        original_xml_pin,original_body_pin,paragraph_n=fingerprint(raw)
        assert original_body_pin==proof['retained_visible_body_sha256']
        release_memory()
        for match in proof['native_matches']:
            path=ROOT/match['original_file'];source=path.read_bytes()
            assert hash_bytes(source)==match['original_file_sha256']
            if match['member'] is not None:
                with zipfile.ZipFile(io.BytesIO(source)) as zipped:source=zipped.read(match['member'])
            assert hash_bytes(source)==match['native_DOCX_sha256']
            if source==raw:
                native_xml_pin,native_body_pin,native_n=original_xml_pin,original_body_pin,paragraph_n
            else:
                native_xml_pin,native_body_pin,native_n=fingerprint(source)
            assert native_body_pin==original_body_pin
            assert native_xml_pin==match['native_main_document_XML_sha256']
            mode=match['authentication_scope']
            assert (source==raw)==match['byte_identical_to_retained_DOCX']
            if mode=='exact_native_DOCX_bytes':assert source==raw
            if mode=='exact_native_main_document_XML':assert native_xml_pin==original_xml_pin
            assert native_n==match['visible_paragraphs_n']
            checked.append({'retained':retained,'original_file':match['original_file'],
                            'member':match['member'],'scope':mode})
            scopes[mode]+=1
        del raw,source
        release_memory()
    changed={(row['identity'],row['relation'],row['direction']) for row in data['changed_cases']}
    excerpts=[]
    for case in data['cases']:
        if case['relation']!='RESOLUTION_BELONGS_TO' or (case['fixed_identity'],case['relation'],case['direction']) not in changed:continue
        for occurrence in case['occurrences']:
            for mapping in occurrence['native_mappings']:
                heading=mapping['nearest_native_heading']
                if heading is None:continue
                match=data['report_authentication'][occurrence['retained_source']]['native_matches'][mapping['native_match_index']]
                source=(ROOT/match['original_file']).read_bytes()
                if match['member'] is not None:
                    with zipfile.ZipFile(io.BytesIO(source)) as zipped:source=zipped.read(match['member'])
                native_body,_=body(source)
                paragraph=native_body[heading['locator']['body_index']]
                assert paragraph.tag==W+'p'
                assert text(paragraph,True)==heading['native_heading_text']
                style=paragraph.find('./'+W+'pPr/'+W+'pStyle')
                assert (style.get(W+'val') if style is not None else None)==heading['style']
                index=mapping['native_start_locator']['body_index']
                span=text(native_body[index])
                excerpt={'identity':case['fixed_identity'],'direction':case['direction'],
                         'status':case['status'],'native_heading':heading,
                         'native_source_paragraph_or_cell_container':span,
                         'comparison':case.get('comparison'),
                         'source':{'file':match['original_file'],'member':match['member']}}
                excerpts.append(excerpt)
                del native_body,paragraph,source
                release_memory()
    result={'status':'PASS','producer_sha256':hash_bytes(Path(__file__).read_bytes()),
            'input_results_sha256':hash_bytes(args.results.read_bytes()),
            'original_native_report_matches_reopened':len(checked),
            'retained_reports_reopened':len({row['retained'] for row in checked}),
            'authentication_scope_counts':dict(scopes),'checks':checked,
            'changed_agenda_native_excerpts':excerpts,
            'expert_reviews':0,'operational_DB_calls':0,'model_calls':0,
            'limits':'Independent native-byte/body and literal-heading checks, not expert semantic adjudication or full-corpus validation.'}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['checks','changed_agenda_native_excerpts']},indent=2))


if __name__=='__main__':main()
