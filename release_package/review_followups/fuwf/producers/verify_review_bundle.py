#!/usr/bin/env python3
"""Verify packaged hashes, fixed identities and scores without models or raw corpus."""
import collections
import csv
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    def load(name):
        return json.loads((root / name).read_text())
    for name, expected in load('SHA256.json').items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
    sample, audit = load('source-audit/sampling.json'), load('source-audit/results.json')
    assert sample['selected_n'] == len(sample['cases']) == audit['selected_n'] == 491
    assert sample['requested_n'] == audit['requested_n'] == 500
    wg = load('wg-cr-extension/results.json')
    fixed = {x['sample_identity'] for x in sample['cases']
             if x['relation'] == 'MODIFIES_SECTION' and x['direction'] == 'graph_first'}
    assert {x['identity'] for x in wg['cases']} == fixed and len(fixed) == 50
    assert dict(collections.Counter(x['status'] for x in wg['cases'])) == wg['counts']
    slice_ = load('source-verified-cr-slice.json')
    assert len(slice_['cases']) == 26
    assert all(x['comparison']['exact_equal'] for x in slice_['cases'])
    for ledger in ('source_dispositions_unapplied.json', 'wg_cr_dispositions_unapplied.json'):
        d = load(ledger)
        assert not d.get('applied_to_frozen_release', False) and not d.get('applied_to_production', False)
    pool, manifest, gold, analysis = [load(n) for n in ('routing_pool.json', 'matched/manifest.json', 'matched/gold.json', 'matched/analysis.json')]
    assert pool['records'] == manifest['records'] and len(pool['records']) == 47
    assert sum(len(r['recipients']) for r in pool['records']) == 62
    fields = ('row_id', 'tdoc_number', 'raw_to')
    answer_set = lambda rows: {tuple(x[k] for k in fields) for x in rows}
    summaries = {}
    for arm in manifest['arms']:
        scores, errors, exact, nonempty, nonempty_exact = [], 0, 0, [], 0
        for task in manifest['tasks']:
            derived = [{k: r[k] for k in fields} for r in pool['records']
                       if r['source_wg'] == task['source_wg'] and task['recipient'] in r['recipients']]
            assert derived == gold[task['id']]
            base = root / 'matched/calls' / (task['id'] + '__' + arm)
            result, reservation = [json.loads((base / n).read_text()) for n in ('result.json', 'reservation.json')]
            assert reservation['scientific_attempt'] == 1 and result['tools_used'] == []
            assert hashlib.sha256((base / 'prompt.txt').read_bytes()).hexdigest() == result['prompt_sha256']
            expected, actual = answer_set(derived), answer_set(result['records'])
            score = 2 * len(expected & actual) / (len(expected) + len(actual)) if expected or actual else 1.
            correct = expected == actual
            if result['error']:
                errors += 1
                score, correct = 0., False
            scores.append(score)
            exact += correct
            if expected:
                nonempty.append(score)
                nonempty_exact += correct
        d = analysis['arms'][arm]
        assert errors == d['errors'] and exact == d['exact_matches']
        assert abs(sum(scores) / len(scores) - d['mean_record_f1']) < 1e-12
        assert len(nonempty) == d['nonempty_tasks'] == 15
        assert abs(sum(nonempty) / len(nonempty) - d['nonempty_record_f1']) < 1e-12
        summaries[arm] = {'n': len(scores), 'errors': errors, 'exact': exact, 'f1': sum(scores)/len(scores)}
    assert len(list((root / 'matched/calls').iterdir())) == 75
    primary, independent = load('semantic_review_primary.json'), load('semantic_review_independent.json')
    assert len(primary['cases']) == len(independent['cases']) == 19
    assert sum(x['original_available'] for x in independent['cases']) == 7
    assert primary['expert_review_n'] == independent['domain_expert_review_count'] == 0
    with (root / 'verified-routing-slice/records.csv').open(newline='') as f:
        assert len(list(csv.DictReader(f))) == 47
    with (root / 'verified-routing-slice/addressed_recipients.csv').open(newline='') as f:
        assert len(list(csv.DictReader(f))) == 62
    print(json.dumps({'status': 'PASS', 'hashes_checked': len(load('SHA256.json')),
                      'fixed_source_cases': 491, 'graph_first_CR_cases': 50,
                      'source_checked_CR_records': 26, 'routing_records': 47,
                      'routing_memberships': 62, 'reserved_calls': 75, 'scores': summaries,
                      'expert_reviews': 0, 'raw_source_authentication_reperformed': False}, indent=2))


if __name__ == '__main__':
    main()
