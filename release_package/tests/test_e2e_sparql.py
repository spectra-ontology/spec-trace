#!/usr/bin/env python3
"""Reproduce the end-to-end SPARQL example.

Loads ontology/spectra.ttl + examples/end_to_end/data.ttl, runs the
example's own query (examples/end_to_end/query.sparql), and verifies the
expected row (R1-2599998 / RAN1#121). This is the standalone counterpart
of the E2E check in verify_release.py, which runs the same query.

The full-corpus SpectraCQ translations under queries/sparql/ target the
released RAN1-body.ttl, not this 47-triple synthetic example, so they are
exercised by the parity harness rather than here.

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

    with open(ROOT / 'examples' / 'end_to_end' / 'query.sparql') as f:
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
