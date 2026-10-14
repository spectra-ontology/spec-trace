#!/usr/bin/env python3
"""Construct an information-matched pool from every fixed source-first LS case.

Normalize only fully consumed, explicit recipient fields. Unknown names and
malformed aliases remain excluded with their original fixed identities.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROLE = re.compile(r'\b(?:3GPP\s+)?(?:TSG\s+(?:WG\s+)?)?(RAN|SA|CT)\s*(?:WG\s*)?([1-9]\d*)?\b', re.I)


def normalize_recipients(raw):
    values = []
    for match in ROLE.finditer(raw):
        values.append(match.group(1).upper() + (match.group(2) or ''))
    remainder = ROLE.sub('', raw)
    remainder = re.sub(r'\band\b|[,.;/\s&+]', '', remainder, flags=re.I)
    return sorted(set(values)), not remainder, remainder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sampling', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    raw = args.sampling.read_bytes()
    sampling = json.loads(raw)
    selected = [r for r in sampling['cases'] if r['relation'] == 'SENT_TO' and r['direction'] == 'source_first']
    records, exclusions = [], []
    for case in selected:
        source = case['source']
        recipients, complete, remainder = normalize_recipients(source['to'])
        if not complete:
            exclusions.append({'identity': case['sample_identity'], 'source_wg': case['wg'],
                               'raw_to': source['to'], 'reason': 'unconsumed_recipient_text',
                               'unconsumed_text': remainder, 'explicit_tokens_only': recipients})
            continue
        records.append({'row_id': hashlib.sha256(case['sample_identity'].encode()).hexdigest()[:16],
                        'source_wg': case['wg'], 'tdoc_number': source['tdoc'], 'raw_to': source['to'],
                        'recipients': recipients, 'source_identity': case['sample_identity'],
                        'source_path': source['source_path'], 'source_sha256': source['source_read_sha256'],
                        'sheet': source['sheet'], 'row': source['row']})
    out = {'sampling_path': str(args.sampling.resolve()),
           'sampling_sha256': hashlib.sha256(raw).hexdigest(),
           'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'normalization': 'Explicit RAN/SA/CT tokens, optional 3GPP/TSG/WG wrappers, numeric WG or bare TSG; only delimiter residue permitted.',
           'original_selected_n': len(selected), 'admitted_n': len(records),
           'exclusions': exclusions, 'replacement_n': 0,
           'machine_source_field_normalization': True, 'human_expert_validation_n': 0,
           'finite_scope': 'Explicit addressed-recipient facts in these selected records only; no population or full-corpus claims.',
           'records': records}
    with args.output.open('x') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'selected': len(selected), 'admitted': len(records), 'excluded': len(exclusions)}))


if __name__ == '__main__':
    main()
