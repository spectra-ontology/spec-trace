#!/usr/bin/env python3
"""Prepare one original-question repair using the entire shared ownership source."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PREP = HERE.parents[1]
ORIG = PREP / 'original_repair'
sys.path.insert(0, str(ORIG))
import build
import review_schema


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destination = HERE / 'RAN4_owner_candidate'
    destination.mkdir(exist_ok=True)
    source = HERE / 'ownership_common_source'
    mapping = json.loads((source / 'primary_to_specs.json').read_text())
    owners = mapping['R4']
    known = set().union(*(set(numbers) for numbers in mapping.values()))
    manifest = json.loads((source / 'manifest.json').read_text())
    for row in manifest['files']:
        assert sha(source / row['path']) == row['sha256']
    database = HERE.parent / 'relational/RAN4.sqlite'
    before = sha(database)
    connection = sqlite3.connect(f'file:{database.resolve()}?mode=ro&immutable=1', uri=True)
    connection.execute('PRAGMA query_only=ON')
    connection.set_progress_handler(lambda: 0, 10000)
    count_query = '''SELECT s.specNumber,count(e.src_id) AS edgeCount,
                            count(DISTINCT e.src_id) AS crCount
                     FROM Spec s LEFT JOIN rel_MODIFIES e ON e.dst_id=s.node_id
                     WHERE s.specRelease IS NULL GROUP BY s.specNumber'''
    actual = connection.execute(count_query).fetchall()
    assert all(edge == cr for _, edge, cr in actual)
    counts = {number: count for number, _, count in actual}
    pool = sorted([{'specNumber': number, 'crCount': counts.get(number, 0)}
                   for number in owners], key=lambda row: (-row['crCount'], row['specNumber']))
    unknown = [{'specNumber': number, 'crCount': count} for number, count in counts.items()
               if number not in known]
    boundary = pool[9]['crCount']
    assert max((row['crCount'] for row in unknown), default=0) < boundary
    assert connection.execute('SELECT count(*) FROM rel_MODIFIES e JOIN Spec s ON e.dst_id=s.node_id WHERE s.specRelease IS NOT NULL').fetchone()[0] == 0
    connection.close()
    assert sha(database) == before
    evidence = {'status': 'RECORDED_FROZEN_SOURCE', 'source_manifest_sha256': sha(source / 'manifest.json'),
                'complete_shared_source_sha256': sha(source / 'shared_source.txt'),
                'source_snapshot': '2026-01-22', 'source_responsibility_role': 'Responsible Primary; code R4',
                'sql_database_sha256_before': before, 'sql_database_sha256_after': sha(database),
                'sql_query': count_query, 'all_hub_counts': actual, 'full_owned_pool': pool,
                'owned_pool_n': len(pool), 'positive_owned_n': sum(row['crCount'] > 0 for row in pool),
                'zero_owned_n': sum(row['crCount'] == 0 for row in pool),
                'graph_absent_owned_n': sum(number not in counts for number in owners),
                'unclassified_frozen_specs': unknown, 'unclassified_max_count': max(row['crCount'] for row in unknown),
                'requested_k': 10, 'boundary_count': boundary, 'boundary_tie_n': sum(row['crCount'] == boundary for row in pool),
                'next_count': pool[10]['crCount'], 'edge_vs_distinct_cr_pool_equal': True,
                'all_MODIFIES_targets_are_unversioned_hubs': True,
                'scope': 'Complete frozen graph-relative ranking pool; shared official ownership snapshot, not completeness of real CR archives or current-date responsibility',
                'new_native_calls': 0, 'new_model_calls': 0, 'expert_validation_n': 0}
    witness_path = destination / 'source_pool_witness.json'
    witness_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
    original = next(json.loads(line) for line in (HERE / 'RAN3_RAN4.jsonl').read_text().splitlines()
                    if json.loads(line)['id'] == 'RAN4_P3_CQ5-4')
    query = ('UNWIND ' + json.dumps(owners, separators=(',', ':')) + ' AS specNumber '
             'OPTIONAL MATCH (hub:Spec {specNumber:specNumber}) WHERE hub.specRelease IS NULL '
             'OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(hub) '
             'RETURN specNumber, count(DISTINCT cr) AS crCount ORDER BY crCount DESC')
    definition = {'id': original['id'], 'question_en': original['original_question'],
                  'original_query': original['original_query'], 'reference_query': query,
                  'required_fields': [{'name': 'specNumber', 'type': 'string', 'nullable': False,
                                       'source_column_or_expression': 'specNumber'}],
                  'collection': {'kind': 'top_k_boundary_ties', 'value': 10,
                                 'source_order_keys': [{'source_column': 'crCount', 'direction': 'desc'}],
                                 'tie_policy': 'any_subset_at_boundary', 'within_tie_order': 'any',
                                 'require_rank_order': False},
                  'cardinality_policy': {'mode': 'top_k', 'value': 10, 'tie_policy': 'any_subset_at_boundary'},
                  'repair_class': 'query_and_scorer', 'original_question_preserved': True}
    digest = build.digest(definition)
    criteria_sha = sha(ORIG / 'criteria.json')
    units = json.loads((ORIG / 'criteria.json').read_text())['semantic_units']
    findings = [
        'The original asks to list specification identities. specNumber is required; the count is ranking metadata and sectionCount is an unasked former auxiliary field.',
        f'The entire shared official inventory source selects Responsible Primary R4: {len(owners)} spec numbers. UNWIND preserves all of them, including graph-absent/zero-count entries; the old 38.1 prefix and Section-presence restriction are removed. The 20 unclassified frozen numbers have at most5 CRs, below the actual top10 cutoff1428, so their unresolved ownership cannot alter the requested top10. The snapshot does not assert present-date ownership or completeness of real CR archives.',
        'Keep the original MODIFIES relationship toward unversioned logical Spec hubs. This counts recorded CR submissions targeting a specification, not approval, normative incorporation or causal impact. No release-specific section lookup is needed to identify a specification.',
        'Count distinct actual CR entities per logical specNumber. The full frozen pool directly proves original edge counts and distinct CR counts coincide, with no duplicate CR/spec contribution; no data-driven change of the ranking unit occurs.',
        f'The original explicitly asks ten. The uncapped reference returns all{len(pool)} source-owned identities including160 zeros and148 graph-absent identities. The scorer requires ten distinct eligible identities, all above the boundary and any needed equal-boundary subset. No positive-only/capped output is used as the full pool.',
        'Top10 specifies selection by descending CR count, not mandatory display order. Equal-boundary alternatives and arbitrary answer display order are accepted; wrong eligible selections, missing higher ranks and duplicate identities are rejected.',
        'Ownership is an additional documented source input absent from the frozen graph. The identical complete shared_source.txt must be supplied to every method in a separately frozen future evaluation, including follow-up retrieval. No graph property, prior model prediction, expert judgment or current performance claim is added.'
    ]
    review = {'id': original['id'], 'status': 'pass', 'repair_sha256': digest,
              'criteria_sha256': criteria_sha, 'original_question_sha256': original['original_question_sha256'],
              'reviewer_kind': 'Primary AI original-question-derived review with full common ownership source; not human/expert validation',
              'human_author_review_completed': False, 'expert_validation_n': 0,
              'semantic_evidence': [{'unit': unit, 'status': 'pass', 'original_quote': definition['question_en'],
                                     'query_clauses': [query], 'finding': finding} for unit, finding in zip(units, findings)]}
    review_schema.check_pass(review, definition['question_en'], units, criteria_sha=criteria_sha,
                             identity_key='repair_sha256', identity_sha=digest)
    proposal = dict(definition, repair_sha256=digest, criteria_sha256=criteria_sha,
                    original_question_sha256=original['original_question_sha256'],
                    original_query_sha256=original['original_query_sha256'],
                    reference_query_sha256=hashlib.sha256(query.encode()).hexdigest(), primary_review=review,
                    source_witness_path=str(witness_path), source_witness_sha256=sha(witness_path),
                    common_source_manifest_sha256=sha(source / 'manifest.json'),
                    common_source_sha256=sha(source / 'shared_source.txt'),
                    model_evaluation_requires='Identical whole shared ownership source in every arm before prediction; separate cohort',
                    admitted=False, new_native_calls=0, new_model_calls=0)
    out = destination / 'proposals.jsonl'
    out.write_text(json.dumps(proposal, ensure_ascii=False, sort_keys=True) + '\n')
    print(json.dumps({'status': 'PREPARED_NOT_ADMITTED', 'id': original['id'], 'repair_sha256': digest,
                      'proposals_sha256': sha(out), 'owned_n': len(pool), 'zero_n': evidence['zero_owned_n'],
                      'boundary': boundary, 'unknown_n': len(unknown), 'unknown_max': evidence['unclassified_max_count']}))


if __name__ == '__main__':
    main()
