#!/usr/bin/env python3
"""Retain exact-cover matches as a derivative slice, preserving the audit denominator."""
import hashlib
import json
from pathlib import Path

b = Path('logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/reviews/fUWF-follow-up')
p = b / 'wg-cr-extension/results.json'
d = json.loads(p.read_text())
cases = [x for x in d['cases'] if x['status'] == 'native_cover_set_match']
assert len(cases) == 26 and all(x['comparison']['exact_equal'] for x in cases)
sample = json.loads((b / 'source-audit/sampling.json').read_text())
ids = {x['sample_identity'] for x in sample['cases']
       if x['relation'] == 'MODIFIES_SECTION' and x['direction'] == 'graph_first'}
assert len(ids) == 50 and {x['identity'] for x in d['cases']} == ids
out = {'status': 'LOCAL_PREPARED_NOT_PUBLISHED', 'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'audit_results_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
       'record_n': 26, 'affected_clause_membership_n': sum(len(x['comparison']['source_set']) for x in cases),
       'original_fixed_denominator': 50, 'original_counts': d['counts'],
       'selection': 'Derivative slice of exact native-cover/frozen-target-set matches after reading all fixed cases.',
       'accuracy_estimation_claim': False, 'adoption_or_implementation_claim': False,
       'expert_reviews': 0, 'frozen_or_production_modifications': False, 'cases': cases}
with (b / 'source-verified-cr-slice.json').open('x') as f:
    json.dump(out, f, indent=2)
print(json.dumps({k: v for k, v in out.items() if k != 'cases'}))
