#!/usr/bin/env python3
"""Apply the same complete literal grammar to all retained graph-first covers."""
import argparse
from collections import Counter, defaultdict
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
    p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(exist_ok=False)
    grammar_path=Path(__file__).with_name('complete_cr_literal_lists.py')
    spec=importlib.util.spec_from_file_location('fuwf_literal_grammar',grammar_path)
    grammar=importlib.util.module_from_spec(spec);spec.loader.exec_module(grammar)
    previous=json.loads((a.base/'wg-cr-extension/results.json').read_text())
    sample=json.loads((a.base/'source-audit/sampling.json').read_text())
    fixed={r['sample_identity']:r['graph'] for r in sample['cases']
           if r['relation']=='MODIFIES_SECTION' and r['direction']=='graph_first'}
    protocol={'selected_n':50,'identities':list(fixed),
        'producer_sha256':digest(Path(__file__)),'grammar_sha256':digest(grammar_path),
        'input_results_sha256':digest(a.base/'wg-cr-extension/results.json'),
        'rule':'Same complete literal grammar on every saved native cover; same member/archive frame, union by explicit spec/release, conflicting or nonliteral covers unresolved, no silent discard or new sources. No LibreOffice extension for this direction.',
        'replacement_n':0,'model_calls':0,'expert_reviews':0,'graph_mutation':False}
    (a.output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    rows=[]
    for c in previous['cases']:
        row=dict(c);row['previous_status']=c['status'];row['status']='unresolved'
        covers=[];unknown=False;pairs=defaultdict(set)
        for old in c['covers']:
            cover=dict(old);cover.pop('keys',None);cover.pop('clauses',None)
            fields=cover.get('fields',[]);specs=cover.get('specs',[]);releases=cover.get('releases',[])
            clauses=grammar.literals(fields[0]['text']) if len(fields)==1 else None
            if len(specs)!=1 or len(releases)!=1 or not clauses:
                cover['status']='unresolved';unknown=True
            else:
                cover.update(status='complete_native_cover',clauses=clauses,
                    keys=[specs[0]+'-'+releases[0]+'-'+v for v in clauses])
                pairs[(specs[0],releases[0])].add(tuple(clauses))
            covers.append(cover)
        row['covers']=covers
        if not covers or unknown or any(len(v)>1 for v in pairs.values()):
            row.pop('comparison',None)
            row['reason']='unreadable_nonliteral_missing_or_conflicting_cover_retained'
        else:
            expected=sorted({k for v in covers for k in v['keys']})
            actual=sorted({unquote(v.rsplit('/',1)[-1]) for v in fixed[c['identity']]['targets']['MODIFIES_SECTION']})
            row['comparison']={'source_set':expected,'graph_set':actual,
                'source_only':sorted(set(expected)-set(actual)),
                'graph_only':sorted(set(actual)-set(expected)), 'exact_equal':expected==actual}
            row['status']='native_cover_set_match' if expected==actual else 'native_cover_set_difference'
            row.pop('reason',None)
        rows.append(row)
    drift=[str(p) for p,h in previous['input_before_sha256'].items() if digest(Path(p))!=h]
    assert not drift,drift
    result={'selected_n':len(rows),'counts':dict(Counter(r['status'] for r in rows)),
        'previous_counts':previous['counts'],'cases':rows,'original_source_pins_unchanged':True,
        'source_pins':previous['input_before_sha256'],'model_calls':0,'expert_reviews':0,
        'graph_mutation':False,'limits':previous['limits']}
    (a.output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'counts':result['counts']}),flush=True)


if __name__=='__main__':main()
