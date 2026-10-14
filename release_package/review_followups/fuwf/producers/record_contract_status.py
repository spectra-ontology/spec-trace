#!/usr/bin/env python3
"""Record a read-only cross-session contract review without claiming admission."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.source
    load = lambda name: json.loads((root / name).read_text())
    audit = load('audit_result.json')
    native = load('mechanical/native_top_k_report.json')
    independent = load('mechanical/latest_correction_independent_report.json')
    controls = load('correction_candidate/scorer_controls.json')
    assert audit['public_commit'] == native['commit'] == independent['commit']
    for name, expected in audit['evidence_sha256'].items():
        assert sha(root / name) == expected, name
    for name, expected in independent['reviewed_file_sha256'].items():
        assert sha(root / 'correction_candidate' / name) == expected, name
    cases = {item['id']: item for item in native['items']
             if item['excluded_cutoff_tie_n'] > 0}
    assert len(cases) == audit['cutoff_counterexamples_n'] == 8
    assert len(native['items']) == audit['proposed_sibling_contracts_n'] == 10
    witnesses = []
    for item in audit['cutoff_counterexamples']:
        source = cases[item['id']]
        assert item['pool_n'] == source['full_pool_n']
        assert item['cutoff'] == source['cutoff_value']
        assert item['excluded_cutoff_ties_n'] == source['excluded_cutoff_tie_n']
        alternate = source['same_frequency_boundary_alternative']
        assert alternate['replacement_native_row'][source['ranking_column']] == source['cutoff_value']
        assert not alternate['score_under_published_contract']['exact']
        assert not item['published_score']['exact']
        assert item['published_score']['cardinality_valid']
        assert item['published_score']['f1'] == alternate['score_under_published_contract']['f1']
        assert source['terminal_limit_removed_only']
        witnesses.append({
            'id': item['id'], 'candidate_pool_n': item['pool_n'],
            'cutoff_value': item['cutoff'],
            'excluded_same_value_candidates_n': item['excluded_cutoff_ties_n'],
            'published_exact_for_valid_alternative': item['published_score']['exact'],
            'published_F1_for_valid_alternative': item['published_score']['f1'],
            'replacement_native_row': alternate['replacement_native_row'],
            'ranking_column': source['ranking_column']})
    checks = [check for task in controls for check in task['controls']]
    assert len(checks) == audit['proposed_control_n'] == 67
    assert all(check['expected_exact'] == check['score']['exact'] for check in checks)
    assert independent['summary']['actual_replayed_controls_n'] == 67
    assert independent['summary']['actual_excluded_cutoff_alternatives_accepted_n'] == 8
    assert independent['summary']['all_controls_match_stored_scores_and_expectations']
    assert not audit['proposals_admitted'] and not audit['proposals_published']
    assert not audit['official_scores_modified'] and audit['new_model_calls'] == 0
    names = ['REPORT.md', 'audit_result.json', 'mechanical/native_top_k_report.json',
             'mechanical/latest_correction_independent_report.json',
             'correction_candidate/candidate_contracts.jsonl',
             'correction_candidate/scorer_controls.json']
    pins = {str(root / name): sha(root / name) for name in names}
    report = {
        'status': 'RECORDED_KNOWN_PUBLIC_CONTRACT_DEFECTS',
        'public_commit': audit['public_commit'],
        'source_session_artifacts_sha256': pins,
        'contracts_in_public_supplement': 371,
        'confirmed_cutoff_tie_counterexamples': witnesses,
        'cutoff_tie_counterexamples_n': 8,
        'local_proposal_contracts_n': 10,
        'local_proposal_controls_n': 67,
        'local_proposals_admitted': False,
        'local_proposals_published': False,
        'official_scores_modified': False,
        'expert_reviews': 0,
        'scope': ('The fUWF task read and cross-checked the other session\'s pinned reports, '
                  'witness metadata and control records. It did not rerun its database queries, '
                  'admit the proposals, change its files, certify all371 semantics, '
                  'or change official benchmark scores.'),
        'new_model_calls_by_this_read': 0,
        'new_DB_queries_by_this_read': 0,
        'supported_reply': ('Public contracts and retained outputs improve auditability; '
                            '371 must not be described as semantically resolved contracts. '
                            'Eight cutoff-tie scoring defects are known; local proposals '
                            'have not been incorporated into the pinned public release.')}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    assert all(sha(Path(path)) == expected for path, expected in pins.items())
    print(json.dumps({'status': report['status'], 'known_counterexamples': 8,
                      'retained_controls_read': 67, 'other_session_files_modified': 0}))


if __name__ == '__main__':
    main()
