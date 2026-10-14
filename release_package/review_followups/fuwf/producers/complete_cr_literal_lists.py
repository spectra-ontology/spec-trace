#!/usr/bin/env python3
"""Compare fully consumed explicit clause lists on the same fixed CR members.

Accept literal alphanumeric clause components, conjunctions, and explicit new
markers. Do not infer numbering for placeholders or expand ranges. This is a
retrospective reader refinement, separate from the original sampling protocol.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def literals(text):
    value = re.sub(r'^\s*new\s+', '', text, flags=re.I)
    value = re.sub(r'\s*\(new\)', '', value, flags=re.I)
    value = re.sub(r'\s+and\s+', ',', value, flags=re.I)
    value = value.rstrip(',; \n\t')
    parts = [p.strip() for p in re.split(r'[,;\n]', value)]
    numeric = r'\d+[A-Za-z]?'
    valid = re.compile(r'(?:'+numeric+r'|[A-Z])(?:\.'+numeric+r')*')
    if not parts or any(not valid.fullmatch(p) for p in parts):
        return None
    return sorted(set(parts))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--refinement', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); a.output.mkdir(exist_ok=False)
    paths = [a.refinement/'cr-binding/results.json',
             a.refinement/'legacy-doc-fallback-corrected/results.json']
    fixed, converted = [json.loads(p.read_text()) for p in paths]
    protocol = {
        'selected_n': 50, 'identities': [r['identity'] for r in fixed['cases']],
        'producer_sha256': sha(Path(__file__)),
        'input_sha256': {str(p): sha(p) for p in paths},
        'rule': 'Every fixed cover receives the same complete literal-list grammar: decimal components may carry one letter; uppercase annex component; comma/semicolon/newline/and separators; terminal punctuation ignored; leading New or (new) annotations only. No inferred numbering, ranges, x/aaa placeholders, unconsumed prose, release substitution, or graph-driven choices.',
        'selection': 'Same original50 archive/member identities and ranks; retrospective reader refinement, not a new or representative source sample.',
        'legacy_rule': 'Only decoder-confirmed current headers admitted; conflicting converted headers remain unresolved despite native antiword binding.',
        'replacement_n': 0, 'model_calls': 0, 'expert_reviews': 0,
        'graph_mutation': False}
    (a.output/'protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n')
    legacy = {r['identity']:r for r in converted['cases']}
    rows = []
    for r in fixed['cases']:
        c = legacy.get(r['identity'], r)
        row = {'identity':r['identity'], 'current_tdoc':r['current_tdoc'],
               'original_binding_status':r['binding_status'],
               'archive':r['archive'], 'archive_sha256':r['archive_sha256'],
               'member':r['member'], 'member_sha256':r['member_sha256'],
               'original_corrected_status':r['status'], 'decoder_status':c['status'],
               'status':'unresolved', 'decoder':r['decoder']}
        if 'converted_header_conflicts' in c.get('reason',''):
            row['reason'] = c['reason']; rows.append(row); continue
        if r['decoder'] == 'antiword':
            spec, release = c.get('spec'), c.get('release')
            fields = c.get('fields',[])
            text = fields[0]['value']['text'] if len(fields)==1 else None
            row['decoder']='isolated_LibreOffice_FODT'
            row['decoded_fodt_sha256']=c.get('decoded_fodt_sha256')
        else:
            spec = r['specs'][0] if len(r['specs'])==1 else None
            release = r['releases'][0] if len(r['releases'])==1 else None
            fields = r['fields']
            text = fields[0]['text'] if len(fields)==1 else None
        row.update(spec=spec, release=release, field_text=text, field_locators=fields)
        parts = literals(text) if text else None
        if not parts or not spec or not release or len(r['graph_matches'])!=1:
            row['reason']='nonliteral_placeholder_or_missing_unique_cover_fields'
        else:
            rel='Rel-'+re.search(r'\d+',release).group()
            expected=sorted({spec+'-'+rel+'-'+v for v in parts})
            actual=sorted({unquote(v.rsplit('/',1)[-1]) for v in r['graph_matches'][0]['targets']['MODIFIES_SECTION']})
            row['literal_clauses']=parts
            row['comparison']={'source_set':expected,'graph_set':actual,
                'source_only':sorted(set(expected)-set(actual)),
                'graph_only':sorted(set(actual)-set(expected)), 'exact_equal':expected==actual}
            row['status']='native_cover_set_match' if expected==actual else 'native_cover_set_difference'
        rows.append(row)
    assert len(rows)==50
    result={'selected_n':len(rows), 'counts':dict(Counter(r['status'] for r in rows)),
        'prior_corrected_counts':fixed['counts'],
        'prior_decoder_counts':converted['same50_extended_counts'],
        'cases':rows,'expert_reviews':0,'model_calls':0,'graph_mutation':False,
        'limits':'Machine cover declarations only; original sampling eligibility remains affected by the historical filename binding. No population completeness, expert interpretation, normative incorporation, or corrected frozen release is claimed.'}
    (a.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'counts':result['counts']}),flush=True)


if __name__=='__main__':
    main()
