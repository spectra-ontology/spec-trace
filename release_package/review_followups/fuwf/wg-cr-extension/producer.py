#!/usr/bin/env python3
"""Read original WG contribution ZIPs for the SAME 50 graph-first CR cases.

This independently broadens the original-document frame, without replacing
sampled records or using graph answers to select a document/release. Conflicting
cover revisions and any ambiguous cover keep the entire case unresolved.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.parse
import zipfile


def module(path,name):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def write(path,value):
    with path.open('x') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--scripts',type=Path,required=True)
    a=p.parse_args()
    reader=module(a.scripts/'source_audit.py','reader')
    native=module(a.scripts/'native_cr_audit.py','native')
    sample=json.loads((a.base/'source-audit/sampling.json').read_text())
    cases=[c for c in sample['cases'] if c['relation']=='MODIFIES_SECTION' and c['direction']=='graph_first']
    outdir=a.base/'wg-cr-extension'
    outdir.mkdir(exist_ok=False)
    write(outdir/'protocol.json',{'sample_n':len(cases),'identities':[c['sample_identity'] for c in cases],
          'frame':'All exact-TDoc-named original WG ZIPs across Rel15–19; all original DOC/DOCX members with an explicit CHANGE REQUEST marker and Clauses affected field.',
          'selection':'No matching against graph targets to select covers, versions, or clauses.',
          'comparison':'Union of all unambiguous native cover fields across spec/release pairs; conflicting fields for the same spec/release retain the entire case unresolved.',
          'replacement_n':0,'expert_reviews':0,'model_calls':0,
          'reader_sha256':reader.digest(a.scripts/'source_audit.py'),'native_reader_sha256':reader.digest(a.scripts/'native_cr_audit.py'),
          'producer_sha256':reader.digest(Path(__file__))})
    antiword=a.base/'legacy-reader/extracted/usr/bin/antiword'
    env=dict(os.environ,ANTIWORDHOME=str((a.base/'legacy-reader/extracted/usr/share/antiword').resolve()))
    rows,pins=[],{}
    for case in cases:
        graph=case['graph'];tdoc=graph['tdoc'];wg=case['wg']
        sourcebase=Path(f'data/corpus/tsg/RAN/formal/change-requests/{wg}/source')
        archives=sorted(sourcebase.glob(f'Rel-*/wg_docs/{tdoc}.zip'))
        result={'identity':case['sample_identity'],'wg':wg,'tdoc':tdoc,'archives_n':len(archives),
                'covers':[],'status':'unresolved'}
        unknown=[]
        for archive in archives:
            pins.setdefault(str(archive),reader.digest(archive))
            with zipfile.ZipFile(archive) as z:
                for name in z.namelist():
                    if not name.lower().endswith(('.doc','.docx')) or Path(name).name.startswith('~$'):
                        continue
                    data=z.read(name)
                    doc={'archive':str(archive),'archive_sha256':pins[str(archive)],'member':name,
                         'member_sha256':hashlib.sha256(data).hexdigest()}
                    try:
                        if data.startswith(b'PK'):
                            units=reader.paragraphs(data)
                            text='\n'.join(u['text'] for u in units)
                            fields,spec,release=reader.cr_fields(units)
                            specs,releases=([spec] if spec else []),([release] if release else [])
                            doc['decoder']='native_OOXML'
                        else:
                            proc=subprocess.run([str(antiword.resolve()),'-t','-w','0','-m','UTF-8.txt','-'],
                                input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=30)
                            if proc.returncode:
                                raise ValueError('antiword exit '+str(proc.returncode))
                            text=proc.stdout.decode('utf-8')
                            fields,specs,releases=native.binary_fields(text)
                            doc.update(decoder='antiword',decoded_text_sha256=hashlib.sha256(proc.stdout).hexdigest())
                        if not re.search(r'\bCHANGE\s+REQUEST\b',text,re.I) or not fields:
                            continue
                        doc.update(fields=fields,specs=specs,releases=releases)
                        result['covers'].append(doc)
                        if len(fields)!=1 or len(specs)!=1 or len(releases)!=1:
                            doc.update(status='unresolved',reason='unbound_or_nonunique_cover_fields')
                            unknown.append(doc['reason']);continue
                        clauses,simple=reader.clause_tokens(fields[0]['text'])
                        if not simple or not clauses:
                            doc.update(status='unresolved',reason='empty_or_complex_clause_list')
                            unknown.append(doc['reason']);continue
                        doc.update(status='complete_native_cover',clauses=clauses,keys=[specs[0]+'-'+releases[0]+'-'+c for c in clauses])
                    except Exception as error:
                        doc.update(status='unresolved',reason=type(error).__name__+': '+str(error))
                        result['covers'].append(doc);unknown.append(doc['reason'])
        if not archives or not result['covers']:
            result['reason']='no_original_WG_archive_or_explicit_CR_cover'
        elif unknown:
            result['reason']='at_least_one_native_cover_or_member_unresolved; no_silent_discard'
        else:
            pairs=collections.defaultdict(set)
            for doc in result['covers']:
                pairs[(doc['specs'][0],doc['releases'][0])].add(tuple(doc['clauses']))
            if any(len(values)>1 for values in pairs.values()):
                result['reason']='conflicting_original_cover_revisions_for_same_spec_release'
            else:
                expected=sorted({k for d in result['covers'] for k in d['keys']})
                actual=sorted({urllib.parse.unquote(t.rsplit('/',1)[-1]) for t in graph['targets']['MODIFIES_SECTION']})
                result['comparison']={'source_set':expected,'graph_set':actual,'source_only':sorted(set(expected)-set(actual)),
                                      'graph_only':sorted(set(actual)-set(expected)),'exact_equal':expected==actual}
                result['status']='native_cover_set_match' if expected==actual else 'native_cover_set_difference'
        rows.append(result)
    drift=[path for path,h in pins.items() if reader.digest(path)!=h]
    counts=dict(collections.Counter(r['status'] for r in rows))
    write(outdir/'results.json',{'selected_n':len(rows),'counts':counts,'cases':rows,'input_before_sha256':pins,
           'input_drift_paths':drift,'validity':'INVALID_INPUT_DRIFT' if drift else 'INPUTS_UNCHANGED','model_calls':0,'expert_reviews':0,
           'limits':['Original WG covers can precede final TSG covers or frozen release; differences are not automatically false edges.',
                     'Antiword may omit Word objects/revisions; this is a machine field audit, not an expert judgment.',
                     'This expanded source frame retains the same graph-first50; not a corpus precision/completeness estimate.']})
    print(json.dumps({'selected':len(rows),'counts':counts,'drift':drift}))
    if drift:raise ValueError('Source drift')


if __name__=='__main__':
    main()
