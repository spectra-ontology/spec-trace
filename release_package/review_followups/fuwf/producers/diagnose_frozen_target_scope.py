#!/usr/bin/env python3
"""Distinguish missing frozen section nodes from absent CR-to-section links."""
import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
from urllib.parse import unquote


def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--refinement',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(exist_ok=False)
    fixed=json.loads((a.refinement/'cr-binding/results.json').read_text())
    literal=json.loads((a.refinement/'cr-literal-lists/results.json').read_text())
    rows={r['identity']:r for r in fixed['cases']}
    wanted=defaultdict(set)
    for c in literal['cases']:
        if 'comparison' in c:wanted[rows[c['identity']]['wg']].update(c['comparison']['source_set'])
    helper=Path('release_package/tests/reproduce_scenario_counts.py')
    spec=importlib.util.spec_from_file_location('fuwf_frozen_target_reader',helper)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    protocol={'producer_sha256':digest(Path(__file__)), 'helper_sha256':digest(helper),
        'input_sha256':digest(a.refinement/'cr-literal-lists/results.json'),
        'rule':'For every parsed source set on the unchanged fixed50, enumerate exact declared identities defined as spectra:Section in the pinned same-WG TTL. Missing subject definitions are snapshot scope omissions; existing definitions with no CR targets are link omissions. This does not identify the historical pipeline cause.',
        'frozen':fixed['frozen'],'model_calls':0,'expert_reviews':0,'graph_mutation':False}
    (a.output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    seen=defaultdict(dict)
    for wg,pin in fixed['frozen'].items():
        path=Path(pin['path']);assert digest(path)==pin['sha256']
        for subject,types,block in m.blocks(path):
            if 'spectra:Section' not in types:continue
            key=unquote(subject.rsplit('/',1)[-1].strip('>'))
            if key in wanted[wg]:seen[wg][key]={'subject':subject,'types':sorted(types)}
        assert digest(path)==pin['sha256']
        print('defined_section_scan',wg,len(seen[wg]),flush=True)
    out=[]
    for c in literal['cases']:
        if 'comparison' not in c:continue
        wg=rows[c['identity']]['wg'];declared=c['comparison']['source_set']
        defined=[s for s in declared if s in seen[wg]]
        absent=[s for s in declared if s not in seen[wg]]
        actual=c['comparison']['graph_set']
        out.append({'identity':c['identity'],'current_tdoc':c['current_tdoc'],'wg':wg,
            'cover_status':c['status'],'declared_targets':declared,'frozen_CR_targets':actual,
            'declared_defined_in_same_WG_frozen_TTL':defined,
            'declared_undefined_in_same_WG_frozen_TTL':absent,
            'declared_defined_but_missing_CR_link':sorted(set(defined)-set(actual))})
    result={'parsed_case_n':len(out),'cases':out,'defined_sections':dict(seen),
        'frozen_inputs_unchanged':True,'model_calls':0,'expert_reviews':0,
        'limits':'Exact subject-definition check at a pinned snapshot; undefined targets are not claims that original clauses do not exist. Historical generation/import causes are unverified.'}
    (a.output/'results.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
