#!/usr/bin/env python3
"""Bounded WG/TSG CR content comparison, preserving native byte distinctions."""
import difflib, importlib.util, io, json, pathlib, zipfile
BASE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('excerpt_reader',BASE/'export_excerpt.py')
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
def main():
    trace=json.loads((BASE/'verified-trace.json').read_text())
    wgpath=reader.ROOT/trace['CR']['provenance']['local_path']
    rppath=reader.ROOT/trace['RP222864_original_pack']['local_archive_pin']['path']
    with zipfile.ZipFile(wgpath) as z:wg=z.read(trace['CR']['provenance']['native_member'])
    with zipfile.ZipFile(rppath) as z:rp=z.read(trace['RP222864_original_pack']['CR_native_member'])
    wgrows=reader.rows_from_native(wg);rprows=reader.rows_from_native(rp)
    a=[r['final_text'] for r in wgrows];b=[r['final_text'] for r in rprows]
    diffs=[{'op':op,'WG_rows':wgrows[i:j],'RP_rows':rprows[k:l]} for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes() if op!='equal']
    result={'WG_native_docx_sha256':reader.sha(wg),'RP_native_docx_sha256':reader.sha(rp),'WG_word_document_xml_sha256':reader.sha(reader.member_xml(wg)),'RP_word_document_xml_sha256':reader.sha(reader.member_xml(rp)),'native_docx_byteidentical':wg==rp,'native_document_xml_byteidentical':reader.member_xml(wg)==reader.member_xml(rp),'final_visible_paragraph_sequence_identical':a==b,'before_visible_paragraph_sequence_identical':[r['before_text'] for r in wgrows]==[r['before_text'] for r in rprows],'WG_paragraph_count':len(wgrows),'RP_paragraph_count':len(rprows),'final_visible_text_differences':diffs,'RP_cover_identity_rows':[r for r in rprows if r['locator'].get('table_index')==0 and r['locator'].get('row_index')==3 or r['locator'].get('table_index')==2 and r['locator'].get('row_index') in [1,17]],'RP_tracked_paragraphs':[r for r in rprows if r['inserted_runs'] or r['deleted_runs']], 'limit':'Visible main-document paragraph sequences only; formatting, comments, headers, footers, properties and author identity are not asserted equal.'}
    with (BASE/'rp-difference-check.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ['native_docx_byteidentical','native_document_xml_byteidentical','final_visible_paragraph_sequence_identical','before_visible_paragraph_sequence_identical','WG_paragraph_count','RP_paragraph_count','final_visible_text_differences']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
