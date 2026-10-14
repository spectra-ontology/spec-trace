#!/usr/bin/env python3
"""Reopen native fixed CR members and available downloaded liaison workbooks.

Independent of the CR producer and production parsers. Workbook copies are
not assumed byte-identical: complete TDoc/To/Type cells are compared explicitly.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile
import xml.etree.ElementTree as ET
import openpyxl

ROOT = Path.cwd()
B = ROOT/'logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/reviews/fUWF-follow-up'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def paragraph(el):
    return ''.join(t.text or '' for t in el.findall('.//'+W+'t'))


def original_value(body, loc):
    el = body[loc['body_index']]
    if 'row_index' in loc:
        el = el.findall(W+'tr')[loc['row_index']].findall(W+'tc')[loc['cell_index']]
        el = el.findall('.//'+W+'p')[loc['cell_paragraph_index']]
    return paragraph(el)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); a.output.mkdir(exist_ok=False)
    raw = json.loads((B/'source-audit/sampling.json').read_text())
    new = json.loads((B/'refinement/cr-binding/results.json').read_text())
    fixed = {c['sample_identity']:c for c in raw['cases']
             if c['relation']=='MODIFIES_SECTION' and c['direction']=='source_first'}
    assert len(fixed)==len(new['cases'])==50
    assert set(fixed)=={r['identity'] for r in new['cases']}
    pins={}; checked=[]; anti=B/'legacy-reader/extracted/usr/bin/antiword'
    env=dict(os.environ,ANTIWORDHOME=str((anti.parent.parent/'share/antiword').resolve()))
    for r in new['cases']:
        before=fixed[r['identity']]; s=before['source']; path=ROOT/s['source_path']
        assert r['selection_rank']==before['selection_rank'] and r['member']==s['member']
        pins.setdefault(str(path),sha(path)); assert pins[str(path)]==r['archive_sha256']
        with zipfile.ZipFile(path) as z: data=z.read(s['member'])
        assert hashlib.sha256(data).hexdigest()==r['member_sha256']
        if data.startswith(b'PK'):
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                body=ET.fromstring(z.read('word/document.xml')).find(W+'body')
            lines=[paragraph(el) for el in body.iter(W+'p')]
            for witness in r['header_witnesses']:
                assert original_value(body,witness['locator'])==witness['text']
            for field in r['fields']:
                actual=original_value(body,field['locator'])
                assert actual==field['text'] or field['text'] in actual
            if r['specs']: assert r['specs'][0] in lines
            if r['releases']: assert any(re.fullmatch(r'Rel(?:ease)?[- ]?'+r['releases'][0][4:],t.strip(),re.I) for t in lines)
        else:
            proc=subprocess.run([str(anti.resolve()),'-t','-w','0','-m','UTF-8.txt','-'],
                input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=30,check=True)
            assert hashlib.sha256(proc.stdout).hexdigest()==r['decoded_text_sha256']
            lines=proc.stdout.decode('utf-8').splitlines()
            for witness in r['header_witnesses']:
                assert lines[witness['locator']['decoder_line']-1]==witness['text']
        head=[]
        for line in lines:
            if re.search(r'\bCHANGE\s+REQUEST\b',line,re.I):break
            if not re.search(r'\b(?:was|revision|revised|rev\s+of|endorsed|from)\b|ex-',line,re.I):head.append(line)
        ids=set(re.findall(r'R[1-5]-\d{6,7}(?!\d)','\n'.join(head),re.I))
        assert {v.upper() for v in ids}=={r['current_tdoc']}
        assert re.search(r'R[1-5]-\d{6,7}(?!\d)',r['member'],re.I).group().upper()==r['current_tdoc']
        if r.get('comparison'):
            parts=sorted(set(v.strip() for v in re.split(r'[,;\n]',r['fields'][0]['text']) if v.strip()))
            assert all(re.fullmatch(r'(?:[A-Za-z]\.)?\d+(?:\.\d+)*|[A-Za-z](?:\.\d+)*',v) for v in parts)
            assert sorted(r['specs'][0]+'-'+r['releases'][0]+'-'+v for v in parts)==r['comparison']['source_set']
            assert hashlib.sha256(r['graph_matches'][0]['frozen_block'].encode()).hexdigest()==r['graph_matches'][0]['block_sha256']
            assert r['comparison']['exact_equal']==(r['comparison']['source_set']==r['comparison']['graph_set'])
        checked.append({'identity':r['identity'],'tdoc':r['current_tdoc'],'member_sha256':r['member_sha256']})
    # Match all available downloaded native workbooks by exact basename; do not
    # choose a favorable snapshot. Conflicting/missing documents stay unknown.
    ls=[c for c in raw['cases'] if c['relation']=='SENT_TO' and c['direction']=='source_first']
    inventory=defaultdict(list)
    for i in range(1,6):
        for path in (ROOT/f'data/corpus/tsg/RAN/formal/meetings/RAN{i}/source').glob('*/Docs/*.xlsx'):
            inventory[(f'RAN{i}',path.name.casefold())].append(path)
    requested=defaultdict(set)
    for c in ls:
        for path in inventory[(c['wg'],Path(c['source']['source_path']).name.casefold())]:
            requested[path].add(c['source']['tdoc'])
    workbook_rows={}
    for path,tdocs in requested.items():
        pins.setdefault(str(path),sha(path)); book=openpyxl.load_workbook(path,read_only=True,data_only=True)
        hits=defaultdict(list)
        for sheet in book:
            iterator=sheet.iter_rows(values_only=True)
            try: headers=next(iterator)
            except StopIteration:continue
            columns={str(v).strip():i for i,v in enumerate(headers) if v is not None}
            if not {'TDoc','To','Type'}<=set(columns):continue
            for number,row in enumerate(iterator,2):
                tid=str(row[columns['TDoc']] or '').strip()
                if tid in tdocs:
                    hits[tid].append({'source_path':str(path.relative_to(ROOT)),'source_sha256':pins[str(path)],
                        'sheet':sheet.title,'row':number,'tdoc':tid,'To':str(row[columns['To']] or ''),
                        'Type':str(row[columns['Type']] or '')})
        book.close();workbook_rows[path]=hits
    alignment=[]
    for c in ls:
        s=c['source']; matches=[]
        paths=inventory[(c['wg'],Path(s['source_path']).name.casefold())]
        for path in paths:matches+=workbook_rows[path].get(s['tdoc'],[])
        row={'identity':c['sample_identity'],'tdoc':s['tdoc'],'retained_path':s['source_path'],
             'retained_sha256':s['source_read_sha256'],'retained_row':s['row'],
             'retained_To':s['to'],'retained_Type':s['type'],'downloaded_candidates_n':len(paths),'original_rows':matches}
        if not matches:row['status']='unresolved_no_original_basename_or_TDoc_match'
        elif all(v['To']==s['to'] and v['Type']==s['type'] for v in matches):
            row['status']='original_TDoc_To_Type_fields_agree'
        else:row['status']='original_fields_differ_or_conflict'
        alignment.append(row)
    drift=[path for path,h in pins.items() if sha(Path(path))!=h]
    assert not drift
    result={'status':'PASS','fixed_CR_native_reopened_n':len(checked),
        'current_CR_header_IDs_checked_n':len(checked),'CR_counts':dict(Counter(r['status'] for r in new['cases'])),
        'CR_binding_changed_n':sum(r['binding_changed'] for r in new['cases']),
        'CR_cases':checked,'LS_fixed_n':len(ls),'LS_original_alignment_counts':dict(Counter(r['status'] for r in alignment)),
        'LS_cases':alignment,'native_input_pins':pins,'input_drift_paths':drift,'expert_reviews':0,
        'scope':'Native CR header/field/bytes reopened; saved frozen blocks hash-checked, not a new full Turtle scan. Original downloaded XLSX fields compared across all exact-basename candidates; differing workbook bytes are not called byte-identical.'}
    with (a.output/'results.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:result[k] for k in ['status','fixed_CR_native_reopened_n','CR_counts','LS_original_alignment_counts']}),flush=True)


if __name__=='__main__':main()
