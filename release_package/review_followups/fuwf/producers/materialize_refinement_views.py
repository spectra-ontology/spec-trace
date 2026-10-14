#!/usr/bin/env python3
"""Export complete parsed cover declarations and all discrepancies, unapplied."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--refinement',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False)
    src=a.refinement/'cr-literal-lists-complete/results.json'
    d=json.loads(src.read_text());scope=json.loads((a.refinement/'frozen-target-scope/results.json').read_text())
    scopes={r['identity']:r for r in scope['cases']}
    records=[];memberships=[];ledger=[]
    for c in d['cases']:
        if 'comparison' not in c:continue
        records.append({'tdoc':c['current_tdoc'],'specification':c['spec'],'release':c['release'],
            'raw_clauses_affected':c['field_text'],'clauses':';'.join(c['literal_clauses']),
            'frozen_alignment':c['status'],'archive':c['archive'],'member':c['member'],
            'archive_sha256':c['archive_sha256'],'member_sha256':c['member_sha256'],
            'decoder':c['decoder'],'source_identity':c['identity']})
        for clause in c['literal_clauses']:
            memberships.append({'tdoc':c['current_tdoc'],'specification':c['spec'],
                'release':c['release'],'declared_clause':clause,'source_identity':c['identity']})
        if c['status']=='native_cover_set_difference':
            s=scopes[c['identity']]
            if c['comparison']['graph_set']:
                kind='different_release_target'
            elif s['declared_defined_but_missing_CR_link']:
                kind='missing_link_to_defined_section'
            else:
                kind='declared_section_outside_frozen_definition_scope'
            ledger.append({'identity':c['identity'],'tdoc':c['current_tdoc'],
                'observed_discrepancy_kind':kind,'native_fields':c['field_locators'],
                'native_release':c['release'],'comparison':c['comparison'],
                'frozen_definition_scope':s,
                'historical_pipeline_cause':'Not established by snapshot inspection.',
                'proposal':'Keep explicit native cover declaration in separate source-derived view; do not invent or relabel frozen Section nodes.',
                'applied_to_frozen_release':False,'applied_to_production':False})
    for name,rows in [('records.csv',records),('declared_clauses.csv',memberships)]:
        with (a.output/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    manifest={'fixed_selected_n':50,'parsed_record_n':len(records),'declared_membership_n':len(memberships),
        'frozen_alignment_counts':d['counts'],'unresolved_cases':[c for c in d['cases'] if 'comparison' not in c],
        'selection':'Every completely parsed member in the unchanged fixed50, including all15differences; no post-match positive-only selection.',
        'input_results_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
        'producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'files_sha256':{n:hashlib.sha256((a.output/n).read_bytes()).hexdigest() for n in ['records.csv','declared_clauses.csv']},
        'version_boundary':'New source-derived declaration CSVs, distinct from unchanged frozen KG, earlier8-record correction proposal, and earlier26-match graph-first subset.',
        'semantics':'A native cover declares an affected clause; this does not imply adopted changes, normative final numbering, a defined frozen Section node, or causal influence.',
        'sampling_limit':'Historical filename ID rule affected source-frame eligibility; parsed members cannot estimate population completeness.',
        'expert_reviews':0,'model_calls':0,'applied_to_frozen_release':False,'applied_to_production':False}
    save(a.output/'manifest.json',manifest)
    from collections import Counter
    save(a.output/'discrepancies_unapplied.json',{'case_n':len(ledger),
        'observed_kind_counts':dict(Counter(c['observed_discrepancy_kind'] for c in ledger)),
        'cases':ledger,'applied_to_frozen_release':False,'applied_to_production':False})
    print(json.dumps({'records':len(records),'memberships':len(memberships),'differences':len(ledger)}))


if __name__=='__main__':main()
