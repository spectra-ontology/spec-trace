#!/usr/bin/env python3
"""Compare fully consumed original recipient fields to canonical WG IRIs."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import urllib.parse


def canonical_wg(value):
    # Decode the encoded path segment BEFORE removing the instance-local tag.
    tail = urllib.parse.unquote(value.rsplit('/', 1)[-1])
    if not tail.startswith('tdoc:wg/'):
        raise ValueError('Unexpected WorkingGroup instance identity: ' + value)
    return tail.removeprefix('tdoc:wg/')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base', type=Path, required=True)
    a = p.parse_args()
    pool = json.loads((a.base/'routing_pool.json').read_text())
    sample = json.loads((a.base/'source-audit/sampling.json').read_text())
    verification = json.loads((a.base/'pool_verification.json').read_text())
    if not verification['valid']:
        raise ValueError('Original cell verification failed')
    cases = {c['sample_identity']: c for c in sample['cases']}
    rows = []
    for record in pool['records']:
        case = cases[record['source_identity']]
        graphs = case['graph_matches']
        actual = sorted({canonical_wg(x) for graph in graphs for x in graph['targets']['SENT_TO']})
        expected = record['recipients']
        status = ('unresolved_graph_identity' if len(graphs) != 1 else
                  ('match' if expected == actual else 'mismatch'))
        rows.append({'identity': record['source_identity'], 'tdoc': record['tdoc_number'],
                     'source_wg': record['source_wg'], 'original_to': record['raw_to'],
                     'normalized_source_set': expected, 'graph_set': actual,
                     'graph_identities': len(graphs), 'status': status,
                     'source_path': record['source_path'], 'source_sha256': record['source_sha256'],
                     'sheet': record['sheet'], 'row': record['row']})
    out = {'selected_source_first_n': 50, 'fully_normalized_n': 47, 'excluded_unconsumed_n': 3,
           'counts': dict(Counter(row['status'] for row in rows)), 'cases': rows,
           'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'source_verification': 'pool_verification.json', 'expert_reviews': 0,
           'limits': ['Conditional addressed-recipient field fidelity; not sent-by attribution or population completeness.',
                      'Three absent or nonunique graph identities and three unknown recipient fields retained unresolved.',
                      'No source or frozen graph modified.']}
    with (a.base/'recipient_field_extension.json').open('x') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(out['counts']))


if __name__ == '__main__':
    main()
