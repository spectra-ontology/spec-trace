#!/usr/bin/env python3
"""Follow every explicitly agreed/endorsed citation in the fixed AI-read cases.

This is a bounded source-link demonstrator, not a semantic accuracy estimate.
No absent CR is inferred and no duplicate is silently chosen.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import zipfile


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--reader', type=Path, required=True)
    a = p.parse_args()
    spec = importlib.util.spec_from_file_location('reader', a.reader)
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    semantic = json.loads((a.base/'semantic_review_primary.json').read_text())
    pack = json.loads((a.base/'semantic_review_blind_pack.json').read_text())
    ix = {c['case_id']:c for c in pack['cases']}
    agreed = [(c, role) for c in semantic['cases'] for role in c['roles']
              if role['role'].startswith(('explicit_agreement', 'explicit_endorsement'))]
    ids = {role['tdoc'] for c,role in agreed}
    sources = []
    for wg in reader.WGS:
        sources.extend(s for s in reader.cr_candidates(wg) if s['tdoc'] in ids)
    rows, original_pins = [], {}
    for case, role in agreed:
        docs = [s for s in sources if s['tdoc'] == role['tdoc']]
        result = {'case_id':case['case_id'], 'tdoc':role['tdoc'], 'reported_role':role['role'],
                  'report_sources': [o['source'] for o in ix[case['case_id']]['occurrences']],
                  'original_CR_candidates_n':len(docs), 'candidates':[], 'status':'unresolved'}
        for source in docs:
            path = Path(source['source_path'])
            original_pins.setdefault(str(path), reader.digest(path))
            with zipfile.ZipFile(path) as z:
                data = z.read(source['member'])
            out = {'archive':str(path),'archive_sha256':original_pins[str(path)],'member':source['member'],
                   'member_sha256':hashlib.sha256(data).hexdigest()}
            result['candidates'].append(out)
            if not data.startswith(b'PK'):
                out['status']='legacy_original_requires_native_reader'
                continue
            units = reader.paragraphs(data)
            fields,number,release = reader.cr_fields(units)
            out.update(fields=fields, spec_number=number, release=release)
            if len(fields) != 1 or not number or not release:
                out['status']='ambiguous_native_fields'
                continue
            tokens,simple = reader.clause_tokens(fields[0]['text'])
            out['clauses']=tokens
            out['status']='original_cover_fields_read' if simple and tokens else 'complex_clause_syntax'
        if len(docs) == 1:
            result['status'] = result['candidates'][0]['status']
        else:
            result['reason']='absent_or_duplicate_original_CR_documents; no substitution'
        rows.append(result)
    drift = [p for p,h in original_pins.items() if reader.digest(p)!=h]
    out={'selected_positive_citation_n':len(agreed),'distinct_citation_n':len(ids),'cases':rows,
         'producer_sha256':sha(Path(__file__)),'reader_sha256':sha(a.reader),'drift_paths':drift,
         'model_calls':0,'expert_reviews':0,
         'limits':['Report wording can agree only part of a contribution; full-document approval is not inferred.',
                   'A trace to the CR cover does not prove subsequent incorporation into a published specification.',
                   'Not a random sample or global process-relationship reliability statistic.']}
    with (a.base/'decision_to_CR_demonstrator.json').open('x') as f:
        json.dump(out,f,ensure_ascii=False,indent=2)
    print(json.dumps({'traced':len(rows),'states':[r['status'] for r in rows],'drift':drift}))


if __name__ == '__main__':
    main()
