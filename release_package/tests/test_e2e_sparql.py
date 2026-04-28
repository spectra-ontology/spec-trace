#!/usr/bin/env python3
"""Reproduce the end-to-end SPARQL example.

Loads ontology/spectra.ttl + examples/end_to_end/data.ttl, runs
queries/sparql/MULTI_HOP_traceability.rq, and verifies the expected row
(R1-2599998 / RAN1#121).

Exit 0 on success; non-zero on any deviation.
"""
import sys
from pathlib import Path

import rdflib

ROOT = Path(__file__).resolve().parents[1]


def main():
    g = rdflib.Graph()
    g.parse(ROOT / 'ontology' / 'spectra.ttl', format='turtle')
    initial = len(g)
    g.parse(ROOT / 'examples' / 'end_to_end' / 'data.ttl', format='turtle')
    print(f'Loaded ontology: {initial} triples')
    print(f'Loaded data:     {len(g) - initial} additional triples')
    print(f'Total:           {len(g)} triples')

    with open(ROOT / 'queries' / 'sparql' / 'MULTI_HOP_traceability.rq') as f:
        q = f.read()
    rows = list(g.query(q))
    print(f'\nQuery rows: {len(rows)}')
    for r in rows:
        print(f'  {dict(r.asdict())}')

    expected = {'R1-2599998', 'RAN1#121'}
    actual_tdocs = {str(r['tdocNumber']) for r in rows}
    actual_meetings = {str(r['meetingNumber']) for r in rows}

    if 'R1-2599998' not in actual_tdocs:
        print('FAIL: expected tdocNumber R1-2599998 not found')
        sys.exit(1)
    if 'RAN1#121' not in actual_meetings:
        print('FAIL: expected meetingNumber RAN1#121 not found')
        sys.exit(1)
    print('\nPASS')


if __name__ == '__main__':
    main()
