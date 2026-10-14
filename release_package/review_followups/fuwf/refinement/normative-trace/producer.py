#!/usr/bin/env python3
"""Bounded independent OOXML inspection of one CR and two normative versions."""
from pathlib import Path
import hashlib, io, json, re, urllib.request, zipfile
import xml.etree.ElementTree as ET

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'.git').exists())
BASE = Path(__file__).resolve().parent
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'

def sha(data): return hashlib.sha256(data).hexdigest()
def norm(text): return re.sub(r'\s+', ' ', text).strip()

def text_tree(node, mode):
    if node.tag == W+'del' and mode == 'final': return ''
    if node.tag == W+'ins' and mode == 'before': return ''
    if node.tag in {W+'t', W+'delText', M+'t'}: return node.text or ''
    if node.tag == W+'tab': return '\t'
    if node.tag in {W+'br', W+'cr'}: return '\n'
    return ''.join(text_tree(child, mode) for child in node)

def native_doc(archive_data, source):
    with zipfile.ZipFile(io.BytesIO(archive_data)) as z:
        members = [n for n in z.namelist() if n.lower().endswith('.docx')]
        if len(members) != 1: raise ValueError('Nonunique native DOCX member')
        member = members[0]; data = z.read(member)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        body = ET.fromstring(z.read('word/document.xml')).find(W+'body')
    rows=[]; table_n=0; para_n=0
    for bi, element in enumerate(body):
        if element.tag == W+'p':
            elems=[(element,{'body_index':bi,'paragraph_index':para_n})]; para_n+=1
        elif element.tag == W+'tbl':
            elems=[]
            for ri,row in enumerate(element.findall(W+'tr')):
                for ci,cell in enumerate(row.findall(W+'tc')):
                    for pi,p in enumerate(cell.findall('.//'+W+'p')):
                        elems.append((p,{'body_index':bi,'table_index':table_n,'row_index':ri,'cell_index':ci,'cell_paragraph_index':pi}))
            table_n+=1
        else: continue
        for p,loc in elems:
            style=p.find('./'+W+'pPr/'+W+'pStyle')
            rows.append({'index':len(rows),'locator':loc,'style':style.get(W+'val') if style is not None else None,'final_text':text_tree(p,'final'),'before_text':text_tree(p,'before'),'inserted_text':[text_tree(x,'all') for x in p.findall('.//'+W+'ins')],'deleted_text':[text_tree(x,'all') for x in p.findall('.//'+W+'del')]})
    return rows,dict(source,archive_sha256=sha(archive_data),native_member=member,native_docx_sha256=sha(data))

def download(version):
    url=f'https://www.3gpp.org/ftp/Specs/archive/38_series/38.213/38213-{version}.zip'
    request=urllib.request.Request(url,headers={'User-Agent':'Python source-documentary-audit'})
    with urllib.request.urlopen(request,timeout=60) as response:
        data=response.read(50*1024*1024+1)
        if len(data)>50*1024*1024: raise ValueError('Bounded source size exceeded')
        meta={'official_url':url,'final_url':response.url,'http_status':response.status,'download_bytes':len(data)}
    path=BASE/f'38213-{version}.official.zip'
    with path.open('xb') as f: f.write(data)
    meta['local_path']=str(path.relative_to(ROOT))
    return native_doc(data,meta)

def main():
    crpath=ROOT/'data/corpus/tsg/RAN/formal/change-requests/RAN1/source/Rel-17/wg_docs/R1-2210700.zip'
    cr,crmeta=native_doc(crpath.read_bytes(),{'local_path':str(crpath.relative_to(ROOT)),'official_url':'https://www.3gpp.org/ftp/tsg_ran/WG1_RL1/TSGR1_110b-e/Docs/R1-2210700.zip'})
    candidates=[r for r in cr if r['inserted_text'] or r['deleted_text']]
    print('CR_NATIVE',json.dumps(crmeta),flush=True)
    print('CR_ROWS',json.dumps(cr,ensure_ascii=False),flush=True)
    result={'producer_sha256':sha(Path(__file__).read_bytes()),'CR':{'provenance':crmeta,'paragraphs':cr,'tracked_paragraph_n':len(candidates)},'normative_versions':{},'limits':['Tracked proposed text and corresponding normative text do not by themselves prove causal adoption.','Only original native OOXML is parsed; no production parser, database or model calls.']}
    for version in ['h30','h40']:
        print('READ_OFFICIAL',version,flush=True)
        try:
            rows,meta=download(version)
            headings=[r for r in rows if re.match(r'^\s*18(?:[ .\t]|$)',r['final_text']) or ('heading' in str(r['style']).lower() and re.search(r'(positioning|position)',r['final_text'],re.I))]
            history=[]
            for i,r in enumerate(rows):
                if re.fullmatch(r'0?388',norm(r['final_text'])) or '2210700' in r['final_text']:
                    loc=r['locator']
                    if 'table_index' in loc:
                        history.extend(x for x in rows if x['locator'].get('table_index')==loc['table_index'] and x['locator'].get('row_index')==loc['row_index'])
                    else: history.extend(rows[max(0,i-3):i+4])
            matches=[]
            for c in candidates:
                if len(norm(c['final_text']))<20: continue
                final=[r for r in rows if norm(r['final_text'])==norm(c['final_text'])]
                before=[r for r in rows if norm(r['final_text'])==norm(c['before_text'])] if norm(c['before_text']) else []
                if final or before:
                    matches.append({'CR_paragraph':c,'final_proposal_exact_matches':final,'before_revision_exact_matches':before})
            result['normative_versions'][version]={'provenance':meta,'front_matter':rows[:25],'heading18_candidates':headings,'CR388_change_history_rows':history,'tracked_paragraph_exact_matches':matches}
            print('NORMATIVE_MATCHES',version,json.dumps({'provenance':meta,'match_n':len(matches),'headings':headings,'CR388history':history},ensure_ascii=False),flush=True)
        except Exception as e:
            result['normative_versions'][version]={'status':'unavailable','error':type(e).__name__+':'+str(e)}
            print('READ_ERROR',version,type(e).__name__,str(e),flush=True)
    with (BASE/'inspection.json').open('x',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2); f.write('\n')

if __name__=='__main__': main()
