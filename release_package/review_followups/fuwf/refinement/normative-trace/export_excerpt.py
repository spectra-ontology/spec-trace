#!/usr/bin/env python3
"""Inspect the native RP member and emit a small, relative-path evidence excerpt."""
import hashlib, importlib.util, io, json, pathlib, re, zipfile
import xml.etree.ElementTree as ET
BASE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('native_reader',BASE/'producer.py')
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
ROOT=reader.ROOT
def sha(data):return hashlib.sha256(data).hexdigest()
def member_xml(native):
    with zipfile.ZipFile(io.BytesIO(native)) as z:return z.read('word/document.xml')
def rows_from_native(native):
    body=ET.fromstring(member_xml(native)).find(reader.W+'body')
    rows=[];table_n=0;para_n=0
    for bi,el in enumerate(body):
        if el.tag==reader.W+'p':
            found=[(el,{'body_index':bi,'paragraph_index':para_n})];para_n+=1
        elif el.tag==reader.W+'tbl':
            found=[]
            for ri,row in enumerate(el.findall(reader.W+'tr')):
                for ci,cell in enumerate(row.findall(reader.W+'tc')):
                    for pi,p in enumerate(cell.findall('.//'+reader.W+'p')):
                        found.append((p,{'body_index':bi,'table_index':table_n,'row_index':ri,'cell_index':ci,'cell_paragraph_index':pi}))
            table_n+=1
        else:continue
        for p,loc in found:
            rows.append({'locator':loc,'final_text':reader.text_tree(p,'final'),'before_text':reader.text_tree(p,'before'),'inserted_runs':[reader.text_tree(x,'all') for x in p.findall('.//'+reader.W+'ins')],'deleted_runs':[reader.text_tree(x,'all') for x in p.findall('.//'+reader.W+'del')]})
    return rows
def main():
    trace_path=BASE/'verified-trace.json';trace=json.loads(trace_path.read_text())
    cr=trace['CR'];proposal=cr['proposed_tracked_paragraph'];text=proposal['final_text']
    excerpt='the UE does not expect to be provided pdsch-HARQ-ACK-Codebook = semi-static for multicast HARQ-ACK information.'
    if excerpt not in text:raise ValueError('Exact excerpt absent')
    pack=trace['RP222864_original_pack'];packpath=ROOT/pack['local_archive_pin']['path'];packdata=packpath.read_bytes()
    if sha(packdata)!=pack['local_archive_pin']['sha256']:raise ValueError('RP input drift')
    with zipfile.ZipFile(io.BytesIO(packdata)) as z:rp_native=z.read(pack['CR_native_member'])
    crpath=ROOT/cr['provenance']['local_path']
    with zipfile.ZipFile(crpath) as z:wg_native=z.read(cr['provenance']['native_member'])
    rp_rows=rows_from_native(rp_native)
    matches=[r for r in rp_rows if reader.norm(r['final_text'])==reader.norm(text)]
    tracked=[r for r in rp_rows if r['inserted_runs'] or r['deleted_runs']]
    rp={'official_url':pack['external_verification_attempts'][0]['url'],'archive_sha256':sha(packdata),'native_member':pack['CR_native_member'],'native_docx_sha256':sha(rp_native),'native_word_document_xml_sha256':sha(member_xml(rp_native)),'native_docx_byteidentical_to_WG_CR':rp_native==wg_native,'word_document_xml_byteidentical_to_WG_CR':member_xml(rp_native)==member_xml(wg_native),'exact_proposed_sentence_matches':matches,'tracked_paragraph_count':len(tracked),'cover_read_status':pack['binary_cover_read_status'],'input_sha256_after':sha(packpath.read_bytes())}
    with (BASE/'rp-member-verification.json').open('x',encoding='utf8') as f:json.dump(rp,f,ensure_ascii=False,indent=2);f.write('\n')
    report=trace['original_meeting_report'];agreement=report['exact_agreement_matches'][0]
    h30=trace['normative_versions']['h30'];h40=trace['normative_versions']['h40'];norm_match=h40['exact_proposal_matches'][0]
    history=h40['CR0388_change_history_row'];history_values=[r['final_text'] for r in history]
    assert len(h30['exact_proposal_matches'])==0 and len(h40['exact_proposal_matches'])==1
    result={'example_identity':'R1-2210700 / TS38.213 / Rel17 / CR0388 / base17.3.0 / clause18','selection_scope':'Fixed named follow-up to an already inspected example; this is not the randomized relation audit. No resampling and no accuracy estimate.','audit_kind':'Documentary original-source trace, not a generated SPECTRA answer, graph execution, expert semantic evaluation, or post-hoc KG accuracy measurement.','locator_convention':'All indices zero based within native word/document.xml; paragraph_index counts top-level body paragraphs, not table cell paragraphs.','normalization':'Whitespace runs only; comparison used the complete inserted paragraph, without fuzzy matching.','sources':{'meeting_report':report['provenance'],'WG_CR':cr['provenance'],'normative_before':h30['provenance'],'normative_after':h40['provenance'],'RP_pack':{'official_url':rp['official_url'],'archive_sha256':rp['archive_sha256'],'native_member':rp['native_member'],'native_docx_sha256':rp['native_docx_sha256'],'native_word_document_xml_sha256':rp['native_word_document_xml_sha256'],'native_docx_byteidentical_to_WG_CR':rp['native_docx_byteidentical_to_WG_CR'],'word_document_xml_byteidentical_to_WG_CR':rp['word_document_xml_byteidentical_to_WG_CR']}},'evidence':[{'step':'WG agreement names final CR','locator':agreement['locator'],'quote':'Final CR is agreed in R1-2210700 (38.213, v17.3.0, Rel-17, CR#0388, Cat. F).'}, {'step':'WG CR cover names target','specification_CR_baseversion_locator':{'body_index':2,'table_index':0,'row_index':3},'clauses_affected_locator':{'body_index':6,'table_index':2,'row_index':17,'cell_index':1,'cell_paragraph_index':0},'cover_target':{'specification':'38.213','CR':'0388','current_version':'17.3.0','release':'Rel-17','clauses_affected':['18']}}, {'step':'WG CR proposes insertion','locator':proposal['locator'],'exact_quote_excerpt':excerpt,'normalized_complete_paragraph_sha256':sha(reader.norm(text).encode()),'tracked_insertion_runs':len(proposal['inserted_text']),'tracked_deleted_runs':len(proposal['deleted_text']),'before_text_is_empty':proposal['before_text']=='','full_paragraph_is_inserted':''.join(proposal['inserted_text'])==text}, {'step':'Earlier normative version lacks complete inserted sentence','version':'17.3.0','clause18_heading_locator':h30['clause18_heading']['locator'],'whole_document_exact_paragraph_matches':h30['exact_proposed_paragraph_count_whole_document'],'whole_document_normalized_substring_matches':h30['normalized_proposed_sentence_substring_count_whole_document'],'unchanged_before_CR_neighbor_locators':{k:[r['locator'] for r in v['native_matches']] for k,v in h30['neighbor_correspondence'].items()}}, {'step':'Subsequent normative version contains identical complete inserted sentence','version':'17.4.0','clause18_heading_locator':h40['clause18_heading']['locator'],'exact_sentence_locator':norm_match['locator'],'exact_quote_excerpt':excerpt,'normalized_complete_paragraph_sha256':sha(reader.norm(norm_match['final_text']).encode()),'whole_document_exact_paragraph_matches':h40['exact_proposed_paragraph_count_whole_document'],'clause18_exact_paragraph_matches':h40['exact_proposed_paragraph_count_clause18'],'normative_tracked_insertions_at_match':len(norm_match['inserted_text']),'normative_tracked_deletions_at_match':len(norm_match['deleted_text'])}, {'step':'Native normative change-history explicitly corroborates CR/version','locator':{'body_index':4240,'table_index':78,'row_index':352},'fields':{'date':history_values[0],'meeting':history_values[1],'TSG_document':history_values[2],'CR':history_values[3],'revision':history_values[4],'category':history_values[5],'title':history_values[6],'new_version':history_values[7]}}, {'step':'Official TSG pack contains named CR original member','native_member':rp['native_member'],'exact_proposed_sentence_match_count':len(matches),'exact_proposed_sentence_locators':[r['locator'] for r in matches],'tracked_paragraph_count':len(tracked),'native_DOCX_byte_identity_to_WG':rp['native_docx_byteidentical_to_WG_CR'],'word_document_XML_byte_identity_to_WG':rp['word_document_xml_byteidentical_to_WG_CR'],'binary_cover_content':'Not decoded or used for an approval-content claim.'}],'input_pins_unchanged':trace['all_pinned_inputs_unchanged'] and rp['input_sha256_after']==rp['archive_sha256'],'defensible_claim':'For this named example, a WG agreement names CR0388, the original CR inserts a sentence in clause18, that sentence is absent from native v17.3.0 and present identically in native v17.4.0, and v17.4.0 native change-history explicitly records CR0388 under RP-222864 leading to 17.4.0. This demonstrates a documentary process-to-normative trace for this sentence.','limits':trace['limitations'],'guard_artifacts':['guard/result.json','guard-verification/result.json','guard-export/result.json'],'local_reader_artifacts':['producer.py','verify_trace.py','export_excerpt.py','inspection.json','verified-trace.json','rp-member-verification.json']}
    encoded=json.dumps(result,ensure_ascii=False,indent=2)
    if '/home/' in encoded or 'C:\\' in encoded:raise ValueError('Host absolute path found in excerpt')
    with (BASE/'evidence-excerpt.json').open('x',encoding='utf8') as f:f.write(encoded+'\n')
    print(json.dumps({'RP_docx_byte_identity':rp['native_docx_byteidentical_to_WG_CR'],'RP_word_document_XML_identity':rp['word_document_xml_byteidentical_to_WG_CR'],'RP_exact_sentence_match_n':len(matches),'RP_tracked_paragraph_n':len(tracked),'field_sized_excerpt_bytes':len(encoded.encode()),'RP_input_unchanged':rp['input_sha256_after']==rp['archive_sha256']}),flush=True)
if __name__=='__main__':main()
