#!/usr/bin/env python3
"""Re-read bounded native sources; retain only the single documentary trace."""
import hashlib, importlib.util, io, json, pathlib, re, urllib.error, urllib.request, zipfile

BASE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('native_reader', BASE/'producer.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
ROOT = reader.ROOT

def sha(data): return hashlib.sha256(data).hexdigest()
def pin(path): return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path.read_bytes()), 'bytes': path.stat().st_size}
def quote(rows, i, radius=2): return rows[max(0,i-radius):i+radius+1]

def main():
    inspection_path=BASE/'inspection.json'
    prior=json.loads(inspection_path.read_text())
    crpath=ROOT/prior['CR']['provenance']['local_path']
    crrows,crmeta=reader.native_doc(crpath.read_bytes(), {'local_path':str(crpath.relative_to(ROOT)),'official_url':prior['CR']['provenance']['official_url']})
    tracked=[r for r in crrows if r['inserted_text'] or r['deleted_text']]
    if len(tracked)!=1: raise ValueError('Predeclared single-tracked-paragraph example changed')
    proposed=tracked[0]
    pins=[pin(crpath),pin(inspection_path)]
    result={'reader_sha256':sha(pathlib.Path(__file__).read_bytes()),'initial_producer_sha256':prior['producer_sha256'],'normalization':'Only whitespace runs are collapsed. No word/parameter rewriting or fuzzy matching. Locators are zero based in word/document.xml. Paragraph_index counts only top-level body paragraphs.','CR':{'provenance':crmeta,'proposed_tracked_paragraph':proposed,'proposal_context':quote(crrows,proposed['index']),'cover_rows':[r for r in crrows if r['locator'].get('table_index')==0 and r['locator'].get('row_index')==3 or r['locator'].get('table_index')==2 and r['locator'].get('row_index') in [1,11,13,17]]},'normative_versions':{},'limitations':['This is a deliberately investigated single example, not a random-sample accuracy measurement.','Normative text appearance plus explicit native change-history CR linkage establishes documentary incorporation of this sentence; it does not establish causal motivation, every intermediate approval step, or graph-wide semantic accuracy.','The RP pack binary .doc cover is retained and hashed but not decoded by this reader. Local cr_list.csv is treated as unverified derivative metadata, not as independent original approval evidence.']}
    for version in ['h30','h40']:
        path=ROOT/prior['normative_versions'][version]['provenance']['local_path']
        pins.append(pin(path))
        rows,meta=reader.native_doc(path.read_bytes(),dict(prior['normative_versions'][version]['provenance']))
        if meta['archive_sha256']!=prior['normative_versions'][version]['provenance']['archive_sha256']: raise ValueError('Normative input drift')
        exact=[r for r in rows if reader.norm(r['final_text'])==reader.norm(proposed['final_text'])]
        heading=[r for r in rows if r['style']=='Heading1' and re.match(r'^18\s',r['final_text'])]
        if len(heading)!=1: raise ValueError('Ambiguous native clause 18 heading')
        start=heading[0]['index']
        end=next((r['index'] for r in rows[start+1:] if r['style']=='Heading1'),len(rows))
        section=rows[start:end]
        history=[r for r in rows if reader.norm(r['final_text'])=='0388' and 'table_index' in r['locator']]
        history_rows=[]
        for r in history:
            history_rows.extend(x for x in rows if x['locator'].get('table_index')==r['locator']['table_index'] and x['locator'].get('row_index')==r['locator']['row_index'])
        preceding=crrows[proposed['index']-1]
        following=crrows[proposed['index']+1]
        neighbors={}
        for label,c in [('preceding_CR_paragraph',preceding),('following_CR_paragraph',following)]:
            matches=[r for r in section if reader.norm(r['final_text'])==reader.norm(c['final_text'])]
            neighbors[label]={'CR_locator':c['locator'],'native_matches':matches,'normative_context':[quote(rows,m['index'],1) for m in matches]}
        result['normative_versions'][version]={'provenance':meta,'version_front_matter':rows[0],'clause18_heading':heading[0],'clause18_end_exclusive_index':end,'exact_proposed_paragraph_count_whole_document':len(exact),'exact_proposed_paragraph_count_clause18':sum(start<=r['index']<end for r in exact),'normalized_proposed_sentence_substring_count_whole_document':reader.norm(' '.join(r['final_text'] for r in rows)).count(reader.norm(proposed['final_text'])),'exact_proposal_matches':exact,'exact_proposal_context':[quote(rows,m['index']) for m in exact],'neighbor_correspondence':neighbors,'CR0388_change_history_row':history_rows}
        del rows,section
    reportpath=ROOT/'data/corpus/tsg/RAN/formal/meetings/RAN1/source/TSGR1_110b-e/Report/Final_Minutes_report_RAN1#110b-e_v100.zip'
    pins.append(pin(reportpath))
    reportrows,reportmeta=reader.native_doc(reportpath.read_bytes(),{'local_path':str(reportpath.relative_to(ROOT)),'official_url':'https://www.3gpp.org/ftp/tsg_ran/WG1_RL1/TSGR1_110b-e/Report/Final_Minutes_report_RAN1%23110b-e_v100.zip'})
    agreements=[r for r in reportrows if 'Final CR is agreed in R1-2210700' in r['final_text']]
    result['original_meeting_report']={'provenance':reportmeta,'exact_agreement_matches':agreements,'agreement_context':[quote(reportrows,m['index'],2) for m in agreements]}
    del reportrows
    packpath=ROOT/'data/corpus/tsg/RAN/formal/change-requests/RAN1/source/Rel-17/TSG/RP-222864.zip'
    pins.append(pin(packpath))
    packdata=packpath.read_bytes()
    member='38213_CR0388_(Rel-17)_R1-2210700.docx'
    with zipfile.ZipFile(io.BytesIO(packdata)) as z:
        native=z.read(member)
        cover=z.read('RP-222864_cover.doc')
    with zipfile.ZipFile(crpath) as z: standalone=z.read(crmeta['native_member'])
    result['RP222864_original_pack']={'local_archive_pin':pins[-1],'CR_native_member':member,'CR_native_member_sha256':sha(native),'CR_native_member_bytes':len(native),'native_CR_member_byteidentical_to_WG_CR':native==standalone,'binary_cover_member':'RP-222864_cover.doc','binary_cover_sha256':sha(cover),'binary_cover_bytes':len(cover),'binary_cover_read_status':'Not decoded; no claim from its content.','external_verification_attempts':[]}
    urls=['https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_98e/Docs/RP-222864.zip','https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_98/Docs/RP-222864.zip','https://portal.3gpp.org/ngppapp/DownloadTDoc.aspx?contributionUid=RP-222864']
    for url in urls:
        attempt={'url':url}
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Python source-documentary-audit'}),timeout=25) as response:
                remote=response.read(10*1024*1024+1)
                if len(remote)>10*1024*1024: raise ValueError('Bounded source size exceeded')
                attempt.update(http_status=response.status,final_url=response.url,remote_bytes=len(remote),remote_sha256=sha(remote),byteidentical_to_local=remote==packdata,is_zip=zipfile.is_zipfile(io.BytesIO(remote)))
            if remote==packdata:
                target=BASE/'RP-222864.official.zip'
                with target.open('xb') as f:f.write(remote)
                attempt['download_path']=str(target.relative_to(ROOT))
        except Exception as e: attempt['error']=type(e).__name__+':'+str(e)
        result['RP222864_original_pack']['external_verification_attempts'].append(attempt)
        if attempt.get('byteidentical_to_local'): break
    meta=ROOT/'data/corpus/tsg/RAN/formal/change-requests/RAN1/source/Rel-17/metadata/cr_list.csv'
    lines=[{'line_number':i,'text':line} for i,line in enumerate(meta.read_text().splitlines(),1) if 'R1-2210700,' in line]
    result['non_primary_derivative_metadata']={'pin':pin(meta),'matching_rows':lines,'not_used_for_primary_incorporation_claim':True}
    after=[pin(ROOT/p['path']) for p in pins]
    result['input_pins_before']=pins
    result['input_pins_after']=after
    result['all_pinned_inputs_unchanged']=pins==after
    if pins!=after: raise ValueError('Pinned local input drift')
    target=BASE/'verified-trace.json'
    with target.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'artifact':str(target.relative_to(ROOT)),'input_pins_unchanged':result['all_pinned_inputs_unchanged'],'versions':{v:{k:x[k] for k in ['exact_proposed_paragraph_count_whole_document','exact_proposed_paragraph_count_clause18','normalized_proposed_sentence_substring_count_whole_document']} for v,x in result['normative_versions'].items()},'report_agreement_count':len(agreements),'RP_native_CR_byteidentical':native==standalone,'RP_external':result['RP222864_original_pack']['external_verification_attempts']},ensure_ascii=False),flush=True)

if __name__=='__main__': main()
