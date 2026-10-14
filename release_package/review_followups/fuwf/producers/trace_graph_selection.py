#!/usr/bin/env python3
"""Locate actual frozen TDoc records for every positive cited demonstrator ID."""
import argparse
import importlib.util
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--reader',type=Path,required=True)
    a=p.parse_args()
    sp=importlib.util.spec_from_file_location('reader',a.reader)
    r=importlib.util.module_from_spec(sp)
    sp.loader.exec_module(r)
    native=r.reader()
    ids=set(json.loads((a.base/'decision_trace_ids.json').read_text())['ids'])
    cases,hits,pins=[],{},{}
    for wg in ['RAN1','RAN2','RAN4']:
        ttl=Path(f'release_package/kg/per_wg/{wg}-body.ttl')
        pins[wg]=r.digest(ttl)
        assert pins[wg]==r.FROZEN[wg]
        selected={i for i in ids if i.startswith('R'+wg[-1]+'-')}
        for subject,types,text in native.blocks(ttl):
            if 'spectra:Tdoc' not in types:
                continue
            tid=native.literal(text,'spectra:tdocNumber')
            if tid in selected:
                hits.setdefault(tid,[]).append(r.graph_record(native,subject,types,text))
        assert r.digest(ttl)==pins[wg]
    held=[]
    for tid in sorted(ids):
        records=hits.get(tid,[])
        if len(records)!=1:
            held.append({'tdoc':tid,'actual_graph_identity_n':len(records),'status':'unresolved_graph_absent_or_nonunique'})
            continue
        rec=records[0]
        cases.append({'wg':'RAN'+tid[1],'relation':'MODIFIES_SECTION','direction':'graph_first',
                      'sample_identity':rec['subject'],'graph':rec})
    out={'selection':'All explicitly positive citations from the fixed native semantic excerpts; explanatory demonstrator, not the 50-case random audit.',
         'requested_citation_n':len(ids),'cases':cases,'held':held,'frozen_sha256':pins,'producer_sha256':r.digest(Path(__file__))}
    with (a.base/'decision_trace_actual_graph.json').open('x') as f:
        json.dump(out,f,ensure_ascii=False,indent=2)
    print(json.dumps({'requested':len(ids),'actual_unique_graph_records':len(cases),'held':held}))


if __name__=='__main__':
    main()
