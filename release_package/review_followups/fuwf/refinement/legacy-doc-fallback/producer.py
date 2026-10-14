#!/usr/bin/env python3
"""Read the SAME legacy DOC covers with an isolated LibreOffice XML decoder.

Only cover fields are compared. Conversion output is a separately pinned reader
artifact, never claimed byte-identical to native input or human verification.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path.cwd()
B=ROOT/'logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/reviews/fUWF-follow-up'
TEXT='{urn:oasis:names:tc:opendocument:xmlns:text:1.0}'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p,x):
    with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(exist_ok=False)
    inp=a.output/'inputs';out=a.output/'decoded';inp.mkdir();out.mkdir()
    original=json.loads((B/'refinement/cr-binding/results.json').read_text())
    selected=[r for r in original['cases'] if r['decoder']=='antiword']
    profile=(a.output/'isolated-libreoffice-profile').resolve().as_uri()
    save(a.output/'protocol.json',{'selected_n':len(selected),'identities':[r['identity'] for r in selected],
        'producer_sha256':sha(Path(__file__)),'input_results_sha256':sha(B/'refinement/cr-binding/results.json'),
        'libreoffice_binary_sha256':sha(Path('/usr/lib/libreoffice/program/soffice.bin')),
        'version':subprocess.run(['/usr/bin/libreoffice','--version'],capture_output=True,text=True,check=True,timeout=30).stdout.strip(),
        'native_input':'Exact original DOC ZIP members from the same50 fixed source-first CR cases.',
        'decoder':'Isolated private UserInstallation; headless conversion to Flat OpenDocument XML, only native cover fields interpreted.',
        'rule':'A unique cover spec/release/current header ID and one complete simple Clauses affected list; all ambiguity retained, no expansion or favorable source selection.',
        'replacement_n':0,'model_calls':0,'expert_reviews':0})
    rows=[]
    for n,r in enumerate(selected):
        result={'identity':r['identity'],'current_tdoc':r['current_tdoc'],'old_status':r['status'],
                'archive':r['archive'],'archive_sha256':r['archive_sha256'],'member':r['member'],
                'member_sha256':r['member_sha256'],'status':'unresolved'}
        path=Path(r['archive']);assert sha(path)==r['archive_sha256']
        with zipfile.ZipFile(path) as z:data=z.read(r['member'])
        assert hashlib.sha256(data).hexdigest()==r['member_sha256']
        doc=inp/(str(n)+'.doc');doc.write_bytes(data)
        try:
            run=subprocess.run(['/usr/bin/libreoffice','-env:UserInstallation='+profile,
                '--headless','--nologo','--nodefault','--nofirststartwizard','--convert-to',
                'fodt:OpenDocument Text Flat XML','--outdir',str(out.resolve()),str(doc.resolve())],
                capture_output=True,text=True,timeout=90)
            result.update(decoder_exit_code=run.returncode,decoder_stdout=run.stdout,
                          decoder_stderr=run.stderr)
            decoded=out/(str(n)+'.fodt')
            if run.returncode or not decoded.exists():raise ValueError('decoder_exit_or_missing_output')
            xml=ET.fromstring(decoded.read_bytes())
            units=[{'index':i,'text':''.join(el.itertext()).strip()} for i,el in enumerate(xml.iter())
                   if el.tag in [TEXT+'p',TEXT+'h']]
            save(out/(str(n)+'.paragraphs.json'),units)
            result.update(decoded_fodt_sha256=sha(decoded),decoded_paragraphs_path=str((out/(str(n)+'.paragraphs.json')).relative_to(ROOT)))
            head=[]
            for u in units:
                if re.search(r'\bCHANGE\s+REQUEST\b',u['text'],re.I):break
                if not re.search(r'\b(?:was|revision|revised|rev\s+of|endorsed|from)\b|ex-',u['text'],re.I):head.append(u['text'])
            ids=set(re.findall(r'R[1-5]-\d{6,7}(?!\d)','\n'.join(head),re.I))
            if {s.upper() for s in ids}!={r['current_tdoc']}:raise ValueError('converted_header_conflicts_with_native_binding')
            spec=next((u['text'] for u in units if re.fullmatch(r'\d{2}\.\d{3}(?:-\d+)?',u['text'])),None)
            release=next((u['text'] for u in units if re.fullmatch(r'Rel(?:ease)?[- ]?\d+',u['text'],re.I)),None)
            fields=[]
            for i,u in enumerate(units):
                if re.search(r'clauses?\s+affected',u['text'],re.I):
                    value=re.split(r'clauses?\s+affected\s*[:：]?',u['text'],flags=re.I)[-1].strip()
                    fields.append({'label':u,'value':{'index':u['index'],'text':value} if value else units[i+1]})
            result.update(spec=spec,release=release,fields=fields)
            if not spec or not release or len(fields)!=1:raise ValueError('cover_fields_nonunique_or_unavailable')
            parts=sorted(set(v.strip() for v in re.split(r'[,;\n]',fields[0]['value']['text']) if v.strip()))
            if not parts or not all(re.fullmatch(r'(?:[A-Za-z]\.)?\d+(?:\.\d+)*|[A-Za-z](?:\.\d+)*',v) for v in parts):
                raise ValueError('complex_clause_list_no_expansion')
            rel='Rel-'+re.search(r'\d+',release).group()
            expected=sorted({spec+'-'+rel+'-'+v for v in parts})
            assert len(r['graph_matches'])==1
            from urllib.parse import unquote
            actual=sorted({unquote(v.rsplit('/',1)[-1]) for v in r['graph_matches'][0]['targets']['MODIFIES_SECTION']})
            result['comparison']={'source_set':expected,'graph_set':actual,'exact_equal':expected==actual}
            result['status']='native_cover_set_match' if expected==actual else 'native_cover_set_difference'
        except Exception as e:result['reason']=type(e).__name__+': '+str(e)
        assert sha(path)==r['archive_sha256'];rows.append(result)
    replacement={r['identity']:r for r in rows}
    all_counts=Counter(replacement.get(r['identity'],r)['status'] for r in original['cases'])
    save(a.output/'results.json',{'selected_legacy_n':len(rows),'legacy_counts':dict(Counter(r['status'] for r in rows)),
        'same50_extended_counts':dict(all_counts),'cases':rows,'native_inputs_unchanged':True,
        'limits':'Additional decoder interpretation; still machine cover-field validation, not expert validation. Original25/8/17 and both decoder versions retained.',
        'model_calls':0,'expert_reviews':0})
    print(json.dumps({'legacy_counts':dict(Counter(r['status'] for r in rows)),'same50_extended_counts':dict(all_counts)}),flush=True)


if __name__=='__main__':main()
