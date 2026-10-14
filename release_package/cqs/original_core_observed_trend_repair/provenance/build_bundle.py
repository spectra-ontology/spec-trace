#!/usr/bin/env python3
"""Build a small, disjoint two-item bundle after both reviews and native gates."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
RECHECK = BASE.parents[1]
sys.path.insert(0, str(RECHECK))
import build_additions


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    proof = json.loads((BASE / 'native_capture_check.json').read_text())
    if proof['status'] != 'NATIVE_FULL_SOURCE_AND_SCORER_PASS':
        raise ValueError('complete source/native/scorer proof unavailable')
    extra = [(BASE.parent / 'trend_scope_source_probe.json', 'source_evidence/trend_scope_source_probe.json'),
             (BASE.parent / 'prepare_observed_agenda_trends.py', 'source_evidence/prepare_observed_agenda_trends.py')]
    for name in ('proposals.jsonl', 'definition_only.jsonl', 'root_secondary_reviews.jsonl',
                 'root_independent_count_reconstruction.jsonl', 'native_capture_check.json',
                 'check_native.py', 'capture.py'):
        extra.append((BASE / name, 'source_evidence/' + name))
    for item in proof['items']:
        identifier = item['id']
        extra.append((BASE / (identifier + '_source_witness.json'), 'source_evidence/' + identifier + '_source_witness.json'))
        for receipt in item['native_receipts']:
            if receipt['id'].endswith('_FULL_MEMBERSHIP'):
                for key in ('receipt_file', 'rows_file'):
                    source = BASE / receipt[key]
                    extra.append((source, 'diagnostic_outputs/' + receipt['id'] + '/' + source.name))
    specification = {'groups': [{'proposals': str(BASE / 'proposals.jsonl'),
        'secondary': str(BASE / 'root_secondary_reviews.jsonl'), 'native_base': str(BASE / 'native')}],
        'prior_additional_cohorts': [],
        'additional_provenance': [{'source': str(source), 'relative': relative} for source, relative in extra]}
    write_json(BASE / 'build_inputs.json', specification)
    destination = BASE / 'bundle'
    build_additions.main(BASE / 'build_inputs.json', destination)
    shutil.copy2(BASE / 'verify_observed_trend.py', destination / 'verify_observed_trend.py')
    shutil.copy2(BASE / 'build_bundle.py', destination / 'provenance/build_bundle.py')
    tasks = [json.loads(line) for line in (destination / 'tasks.jsonl').read_text().splitlines()]
    by_id = {row['id']: row for row in proof['items']}
    for task in tasks:
        identifier = task['id']
        diagnostic = next(row for row in by_id[identifier]['native_receipts'] if row['id'].endswith('_FULL_MEMBERSHIP'))
        task['completeness_witness'] = {
            'kind': 'Complete source Meeting population and exact agenda Resolution-node association count',
            'source_tuple_file': 'source_evidence/trend_scope_source_probe.json',
            'source_tuple_sha256': sha(destination / 'source_evidence/trend_scope_source_probe.json'),
            'source_witness_file': 'source_evidence/' + identifier + '_source_witness.json',
            'source_witness_sha256': sha(destination / ('source_evidence/' + identifier + '_source_witness.json')),
            'membership_diagnostic': {
                'receipt_file': 'diagnostic_outputs/' + diagnostic['id'] + '/' + Path(diagnostic['receipt_file']).name,
                'receipt_sha256': diagnostic['receipt_sha256'],
                'rows_file': 'diagnostic_outputs/' + diagnostic['id'] + '/' + Path(diagnostic['rows_file']).name,
                'rows_sha256': diagnostic['rows_sha256']},
            'scope': 'All graph-recorded Meeting nodes, exact agenda numbers and MADE_AT associations in each designated frozen WG fixture; not full raw archive or calendar activity.'}
        task.update(admitted=True, native_execution_completed=True, scorer_controls_completed=True)
    kernel = build_additions.implementation.original_scorer.typed.get_kernel()
    (destination / 'tasks.jsonl').write_text(''.join(kernel.json_exact(row) + '\n' for row in tasks))
    (destination / 'README.md').write_text(
        '# Exact agenda Resolution-count trends\n\n'
        'This disjoint two-item repair bundle retains the original English questions for RAN3_P2_CQ6-1 '
        'and RAN4_P2_CQ6-1. Each has two separate, nonblind AI semantic judgments under the unchanged '
        'seven-unit criteria, full exact-query native output, an independent source-tuple count rebuild, '
        'and strict requested-field scoring controls. There is no human author or independent expert validation.\n\n'
        'Each answer contains the source Meeting identity and the number of distinct observed Resolution '
        'nodes associated with the exact agenda number and that Meeting through MADE_AT. All 58 source '
        'Meeting nodes are retained, including graph-observed zero counts. The source meetingNumberInt '
        'ordinal determines order; equal ordinals allow any order and keep base/bis identities distinct. '
        'This establishes graph-relative observations, not real-world inactivity, complete archive coverage, '
        'calendar dates, a strict base/bis chronology, or invariant agenda descriptions over meetings.\n\n'
        'Reference outputs contain 116 rows; the separate full-membership diagnostics contain another 116. '
        'The scorer replays 20 standard controls and 10 additional controls, including graph-zero omission, '
        'duplicate meetings, invented positive counts, permitted ordinal ties, and prohibited cross-ordinal swaps.\n\n'
        'The manifest and disposition ledger compare these two IDs with the preserved 371-item parent. '
        'Their parent-relative union of 373 is only this package verification scope. It does not report '
        'the current public union; the separately maintained current index combines all admitted cohorts. '
        'The original 402-item public snapshot and all preceding model outputs are unchanged. '
        'This repair bundle contains no new benchmark predictions.\n\n'
        'Run `python3 -B -S verify_observed_trend.py --bundle . --parent ../original_core_repair`. '
        'This offline check verifies manifest membership, original-question and repair hashes, both AI '
        'reviews, read-only capture provenance and graph guards, full source/node counts, diagnostic '
        'Resolution membership, gold projections, ordinal tie groups, and all 30 scoring controls.\n')
    manifest = json.loads((destination / 'manifest.json').read_text())
    manifest.update(diagnostic_native_rows=116, total_native_rows_including_diagnostics=232,
        additional_scorer_controls=10, total_actual_scorer_controls=30,
        accounting_scope='Parent-relative 371 + these 2; current public union belongs to the separate current index.',
        source_interpretation='Exact agenda number, full graph Meeting population, Resolution node count and source ordinal only.')
    manifest['files'] = {str(path.relative_to(destination)): sha(path) for path in destination.rglob('*')
                         if path.is_file() and path != destination / 'manifest.json'}
    write_json(destination / 'manifest.json', manifest)
    print(json.dumps({'status': 'BUNDLE_CREATED_REQUIRE_STANDALONE_REPLAY', 'bundle': str(destination),
        'manifest_sha256': sha(destination / 'manifest.json'), 'admitted_n': 2,
        'native_rows': 116, 'diagnostic_rows': 116, 'total_controls': 30}))


if __name__ == '__main__':
    main()
