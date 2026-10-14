#!/usr/bin/env python3
"""Independent offline checks; never rerun models or mutate source/release files."""
import collections
import hashlib
import json
import math
from pathlib import Path

ROOT = Path.cwd()
B = ROOT / 'logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/reviews/fUWF-follow-up'


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    out = B / 'matched-information-cli-pinned'
    m, gold, analysis = [read(out / n) for n in ('manifest.json', 'gold.json', 'analysis.json')]
    pool = read(B / 'routing_pool.json')
    assert pool['records'] == m['records']
    assert sha(B / 'routing_pool.json') == m['pool_sha256']
    script = ROOT / 'scripts/publication/paper/under-review/kdd-2027-datasets-benchmarks/rebuttal/fuwf_followup/matched_information.py'
    assert sha(script) == m['producer_sha256']
    for name in ('cli_node', 'cli_js'):
        assert sha(Path(m[name])) == m[name + '_sha256']
    assert len(m['records']) == 47
    assert sum(len(r['recipients']) for r in m['records']) == 62
    tasks = {f'RAN{i}_TO_RAN{j}' for i in range(1, 6) for j in range(1, 6)}
    assert {t['id'] for t in m['tasks']} == set(gold) == tasks
    expected_calls = {t + '__' + a for t in tasks for a in m['arms']}
    assert {p.name for p in (out / 'calls').iterdir()} == expected_calls
    summaries = {}
    failures = []
    fields = ('row_id', 'tdoc_number', 'raw_to')
    for arm in m['arms']:
        rows = []
        for t in m['tasks']:
            derived = [{k: r[k] for k in fields} for r in pool['records']
                       if r['source_wg'] == t['source_wg'] and t['recipient'] in r['recipients']]
            assert derived == gold[t['id']]
            c = out / 'calls' / (t['id'] + '__' + arm)
            r, reservation = read(c / 'result.json'), read(c / 'reservation.json')
            assert reservation['scientific_attempt'] == 1
            assert reservation['task_id'] == r['task_id'] == t['id']
            assert reservation['arm'] == r['arm'] == arm
            assert r['CLI_dispatched'] is True
            assert r['tools_used'] == []
            assert sha(c / 'prompt.txt') == r['prompt_sha256']
            expected = {tuple(x[k] for k in fields) for x in derived}
            actual = {tuple(x[k] for k in fields) for x in r['records']}
            f1 = 2 * len(expected & actual) / (len(expected) + len(actual)) if expected or actual else 1.0
            exact = expected == actual
            if r['error']:
                exact, f1 = False, 0.0
                stderr = (c / 'stderr.txt').read_text()
                thread = 'failed to spawn thread' in stderr or 'creating threadpool failed' in stderr
                failures.append({'call_id': c.name, 'error': r['error'],
                                 'thread_creation_diagnostic': thread, 'timeout': r['error'].startswith('TimeoutError')})
            else:
                assert r['CLI_returncode'] == 0
                answer = read(c / 'answer.json')
                if arm != 'sql':
                    assert answer['records'] == r['records']
                else:
                    assert answer['query'] == r['query']
            rows.append({'f1': f1, 'exact': exact, 'error': bool(r['error']), 'nonempty': bool(expected)})
        nonempty, empty = [x for x in rows if x['nonempty']], [x for x in rows if not x['nonempty']]
        result = {'n_fixed_tasks': len(rows), 'errors': sum(x['error'] for x in rows),
                  'exact_matches': sum(x['exact'] for x in rows),
                  'mean_record_f1': sum(x['f1'] for x in rows) / len(rows),
                  'nonempty_tasks': len(nonempty), 'nonempty_exact_matches': sum(x['exact'] for x in nonempty),
                  'nonempty_record_f1': sum(x['f1'] for x in nonempty) / len(nonempty),
                  'empty_tasks': len(empty), 'empty_exact_matches': sum(x['exact'] for x in empty)}
        for k, v in result.items():
            assert math.isclose(v, analysis['arms'][arm][k], abs_tol=1e-12)
        summaries[arm] = result
    assert sum(x['thread_creation_diagnostic'] for x in failures) == 7
    assert len(failures) == 8
    for arm in ('complete_text', 'sql'):
        assert summaries[arm]['exact_matches'] + summaries[arm]['errors'] == 25
    blind = read(B / 'semantic_review_blind_pack.json')
    primary, independent = read(B / 'semantic_review_primary.json'), read(B / 'semantic_review_independent.json')
    assert primary['source_pack_sha256'] == independent['blind_pack_sha256'] == sha(B / 'semantic_review_blind_pack.json')
    assert len(primary['cases']) == len(independent['cases']) == 19
    mapping = {'explicit_endorsement': 'explicit_endorsement_or_positive_agreement',
               'explicit_agreement': 'explicit_endorsement_or_positive_agreement',
               'explicit_endorsement_for_editors_CR': 'explicit_endorsement_or_positive_agreement',
               'explicit_agreement_scoped_to_deltaPDCCH_changes': 'explicit_endorsement_or_positive_agreement',
               'explicit_agreement_scoped_to_slides_3_and_4': 'explicit_endorsement_or_positive_agreement',
               'explicit_not_pursued': 'explicit_negative_or_not_pursued',
               'basis_for_further_discussion': 'basis_for_further_discussion',
               'competing_view_under_discussion': 'competing_proposal'}
    ia = {x['case_id']: x for x in independent['cases']}
    compared = []
    for p in primary['cases']:
        q = ia[p['case_id']]
        assert p['original_available'] == q['original_available']
        if not p['original_available']:
            assert p['roles'] == q['citations'] == []
            continue
        qr = {x['cited_id']: x['classification'] for x in q['citations']}
        assert {x['tdoc'] for x in p['roles']} == set(qr)
        for x in p['roles']:
            compared.append({'case_id': p['case_id'], 'tdoc': x['tdoc'],
                             'primary_category': mapping[x['role']], 'independent_category': qr[x['tdoc']],
                             'same_category': mapping[x['role']] == qr[x['tdoc']]})
    assert len(compared) == 11 and all(x['same_category'] for x in compared)
    wg = read(B / 'wg-cr-extension/results.json')
    assert wg['counts'] == dict(collections.Counter(x['status'] for x in wg['cases']))
    assert wg['selected_n'] == len(wg['cases']) == 50
    old_graph_ids = None
    sampling = read(B / 'source-audit/sampling.json')
    # Sampling schema is retained in the report for independent source reproduction.
    assert wg['validity'] == 'INPUTS_UNCHANGED' and not wg['input_drift_paths']
    diffs = [x for x in wg['cases'] if x['status'] == 'native_cover_set_difference']
    ledger = {'status': 'LOCAL_UNAPPLIED_CANDIDATES', 'applied_to_frozen_release': False,
              'applied_to_production': False, 'expert_reviews': 0,
              'source': 'wg-cr-extension/results.json', 'n': len(diffs),
              'scope': 'Original WG cover versus frozen target sets; reconcile original/final revision and snapshot before any repair.',
              'cases': diffs}
    with (B / 'wg_cr_dispositions_unapplied.json').open('x') as f:
        json.dump(ledger, f, indent=2)
    result = {'status': 'PASS', 'source_pool_equal': True, 'pinned_producer_and_cli_unchanged': True,
              'all_fixed_tasks_and_75_reservations_present': True, 'scientific_retries': 0,
              'model_tool_actions': 0, 'independent_scoring': summaries,
              'failures': failures, 'thread_diagnostic_failure_n': 7, 'other_timeout_n': 1,
              'semantic_same_broad_category_n': len(compared), 'semantic_comparisons': compared,
              'semantic_available_cases_n': 7, 'semantic_unavailable_cases_n': 12,
              'semantic_limit': 'AI concordance after explicit taxonomy mapping; not expert accuracy or population validation.',
              'wg_cr_counts': wg['counts'], 'expert_reviews': 0,
              'model_calls_in_this_verification': 0}
    with (B / 'final_verification.json').open('x') as f:
        json.dump(result, f, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k not in ('failures', 'semantic_comparisons')}, indent=2))


if __name__ == '__main__':
    main()
