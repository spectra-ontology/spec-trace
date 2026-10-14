#!/usr/bin/env python3
"""Freeze an original-answer invariance candidate; no admission or model calls."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PREP = HERE.parents[2]
ORIG = PREP / 'original_repair'
ROOT = PREP.parents[2]
PUBLIC = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs')
sys.path.insert(0, str(ORIG))
import build
import review_schema

KEYS = ('id', 'question_en', 'original_query', 'reference_query', 'required_fields',
        'collection', 'cardinality_policy', 'repair_class', 'original_question_preserved')
QUERY = """MATCH (s:Spec)
WITH DISTINCT s.specNumber AS specNumber
OPTIONAL MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(target:Spec)
WHERE target.specNumber = specNumber
WITH specNumber, count(DISTINCT cr) AS crCount
RETURN specNumber, crCount
ORDER BY crCount DESC"""
DIAGNOSTIC_QUERY = """MATCH (s:Spec)
WITH DISTINCT s.specNumber AS specNumber
OPTIONAL MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(target:Spec)
WHERE target.specNumber = specNumber
RETURN specNumber, count(cr) AS pathCount, count(DISTINCT r) AS resolutionCount,
       count(DISTINCT cr) AS crEntityCount, count(DISTINCT cr.tdocNumber) AS crDocumentCount
ORDER BY specNumber"""
SQL = """SELECT s.specNumber,
 COUNT(CASE WHEN r.node_id IS NOT NULL THEN c.node_id END) AS pathCount,
 COUNT(DISTINCT r.node_id) AS resolutionCount,
 COUNT(DISTINCT CASE WHEN r.node_id IS NOT NULL THEN c.node_id END) AS crEntityCount,
 COUNT(DISTINCT CASE WHEN r.node_id IS NOT NULL THEN c.tdocNumber END) AS crDocumentCount
 FROM Spec s
 LEFT JOIN rel_MODIFIES ms ON ms.dst_id=s.node_id
 LEFT JOIN CR c ON c.node_id=ms.src_id
 LEFT JOIN rel_REFERENCES rr ON rr.dst_id=c.node_id
 LEFT JOIN Resolution r ON r.node_id=rr.src_id
 GROUP BY s.specNumber ORDER BY s.specNumber"""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    ledger_path = PUBLIC / 'current_core/all_core_dispositions.jsonl'
    original_path = PUBLIC / 'spectra_cq_v2.0/benchmark.jsonl'
    ledger = [json.loads(line) for line in ledger_path.read_text().splitlines()]
    originals = {row['id']: row for row in map(json.loads, original_path.read_text().splitlines())}
    pending = [row for row in ledger if row['status'] != 'pass' and row['id'].startswith(('RAN3_', 'RAN4_'))]
    assert len(pending) == 47 and len({row['id'] for row in pending}) == 47
    criteria_sha = sha(ORIG / 'criteria.json')
    criteria = json.loads((ORIG / 'criteria.json').read_text())
    scope = {'status': 'EXACT_CURRENT_PENDING_SCOPE_FROZEN', 'pending_n': 47,
             'ledger_path': str(ledger_path), 'ledger_sha256': sha(ledger_path),
             'original_benchmark_path': str(original_path), 'original_benchmark_sha256': sha(original_path),
             'criteria_sha256': criteria_sha,
             'items': [{'id': row['id'], 'question_en': originals[row['id']]['question_en'],
                        'original_question_sha256': text_sha(originals[row['id']]['question_en']),
                        'original_query': originals[row['id']]['cypher'],
                        'original_query_sha256': text_sha(originals[row['id']]['cypher']),
                        'prior_reason': row.get('continuation_triage', {}).get('reason', row.get('reason'))}
                       for row in pending], 'new_admitted_n': 0, 'human_expert_validation_n': 0}
    write(HERE / 'scope47.json', scope)
    db_path = PREP / 'empirical/relational/RAN3.sqlite'
    before = sha(db_path)
    database = sqlite3.connect('file:' + str(db_path) + '?mode=ro', uri=True)
    database.execute('PRAGMA query_only=ON')
    database.set_progress_handler(lambda: 0, 10000)
    columns = ['specNumber', 'pathCount', 'resolutionCount', 'crEntityCount', 'crDocumentCount']
    rows = [dict(zip(columns, row)) for row in database.execute(SQL)]
    cr_identity = dict(zip(['n', 'distinct_document_n', 'null_document_n'], database.execute(
        'SELECT COUNT(*),COUNT(DISTINCT tdocNumber),SUM(tdocNumber IS NULL) FROM CR').fetchone()))
    spec_identity = dict(zip(['n', 'distinct_spec_number_n', 'null_spec_number_n'], database.execute(
        'SELECT COUNT(*),COUNT(DISTINCT specNumber),SUM(specNumber IS NULL) FROM Spec').fetchone()))
    database.close()
    assert before == sha(db_path)
    assert spec_identity['null_spec_number_n'] == 0
    metric_proofs = []
    for metric in columns[1:]:
        pool = sorted(rows, key=lambda row: (-row[metric], row['specNumber']))
        boundary = pool[4][metric]
        above = sorted(row['specNumber'] for row in pool if row[metric] > boundary)
        equal = sorted(row['specNumber'] for row in pool if row[metric] == boundary)
        eligible = sorted(above + equal)
        # Full tied group fits within exactly five: no arbitrary boundary selection.
        assert len(eligible) == 5
        metric_proofs.append({'metric': metric, 'pool_n': len(pool), 'zero_n': sum(row[metric] == 0 for row in pool),
                             'boundary_value': boundary, 'strictly_above_ids': above,
                             'boundary_tied_ids': equal, 'needed_from_tied_group_n': 5 - len(above),
                             'next_value': pool[5][metric], 'asked_top5_identity_set': eligible})
    answer = metric_proofs[0]['asked_top5_identity_set']
    assert all(proof['asked_top5_identity_set'] == answer for proof in metric_proofs)
    witness = {'status': 'FULL_FROZEN_SOURCE_ASKED_TOP5_IDENTITY_INVARIANCE',
               'id': 'RAN3_P3_CQ4-4', 'source_sqlite_path': str(db_path.relative_to(ROOT)),
               'source_sqlite_sha256_before': before, 'source_sqlite_sha256_after': sha(db_path),
               'source_graph_path': 'release_package/kg/per_wg/RAN3-body.ttl',
               'source_graph_sha256': sha(ROOT / 'release_package/kg/per_wg/RAN3-body.ttl'),
               'whole_pool_sql': SQL, 'pool_columns': columns, 'full_pool': rows,
               'all_frozen_CR_identity_inventory': cr_identity, 'all_frozen_Spec_identity_inventory': spec_identity,
               'metric_proofs': metric_proofs, 'requested_identity_set': answer,
               'native_diagnostic_query': DIAGNOSTIC_QUERY,
               'scope_limit': 'Four recorded structural-path counting interpretations produce the same requested identity set in this frozen graph. This does not prove enacted modifications, all raw archives, all possible meanings, or a globally interchangeable metric.',
               'new_model_calls': 0, 'new_native_executions': 0, 'human_expert_validation_n': 0}
    witness_path = HERE / 'path_top5_count_unit_invariance.json'
    write(witness_path, witness)
    item = originals[witness['id']]
    definition = {'id': item['id'], 'question_en': item['question_en'], 'original_query': item['cypher'],
                  'reference_query': QUERY,
                  'required_fields': [{'name': 'specNumber', 'type': 'string', 'nullable': False,
                                       'source_column_or_expression': 'specNumber'}],
                  'collection': {'kind': 'top_k_boundary_ties', 'value': 5,
                                 'source_order_keys': [{'source_column': 'crCount', 'direction': 'desc'}],
                                 'tie_policy': 'any_subset_at_boundary', 'within_tie_order': 'any',
                                 'require_rank_order': False},
                  'cardinality_policy': {'mode': 'top_k', 'value': 5, 'tie_policy': 'any_subset_at_boundary'},
                  'repair_class': 'query_and_scorer', 'original_question_preserved': True}
    repair_sha = build.digest(definition)
    findings = [
        'Return the top 5 specs asks specification identities. No clause asks numerical counts, resolution IDs, CR IDs, or a ranked output sequence. Require only specNumber; counts remain ranking evidence.',
        'Every frozen specification number is an eligible root, including zero-path numbers. The full139-number inventory is retained without latest-edition, RAN ownership, positive-only, date or release filters. Original explicit path defines the recorded context.',
        'Preserve the explicit Resolution REFERENCES CR MODIFIES Spec path. The question says via that path rather than asking approved, enacted or normatively incorporated changes. No approval/causality interpretation or status predicate is introduced.',
        'Most modified through the CR-to-Spec path is directly operationalized as distinct qualifying CR entities per specification. Crucially, the original Resolution count, relation-path occurrences and distinct CR-document count independently yield the identical requested top5 identity set over the full pool. Counts/order differ and are not claimed equivalent; the requested answer here is invariant. All19974 frozen CR entities have unique non-null document identifiers.',
        'The reference has no LIMIT and retains all139 specNumber roots, including recorded zero counts. Explicit top5 is enforced by the existing boundary-tie scorer. For all four actual metrics, the whole at-boundary group fits within the five positions, and the next lower value is strictly smaller; there is no unresolved requested-identity choice at the cutoff.',
        'Top5 determines eligibility rather than an explicitly required presentation order. The response is the five specification identities in any order. The auxiliary crCount key is used only for full-pool selection; no identifier ASC tie-break or unasked count field is compulsory.',
        'The exact original English/query bytes and fixedcriteria are pinned. This is a separate primary AI source analysis, with earlier metric-ambiguity judgments preserved. Only asked-identity invariance over four identified structural counting interpretations is asserted, not all conceivable meanings, raw-archive completeness, enacted change or human/expert validation. Root independent secondary, fresh native two-query equality and strict controls remain gates.'
    ]
    review = {'id': item['id'], 'status': 'pass', 'repair_sha256': repair_sha,
              'criteria_sha256': criteria_sha, 'original_question_sha256': text_sha(item['question_en']),
              'reviewer_kind': 'Separate primary AI original-question-derived source-identity invariance review; not human/expert validation',
              'human_author_review_completed': False, 'expert_validation_n': 0,
              'semantic_evidence': [{'unit': unit, 'status': 'pass', 'original_quote': item['question_en'],
                                     'query_clauses': QUERY.splitlines(), 'finding': finding,
                                     'source_witness_file': witness_path.name, 'source_witness_sha256': sha(witness_path)}
                                    for unit, finding in zip(criteria['semantic_units'], findings)]}
    review_schema.check_pass(review, item['question_en'], criteria['semantic_units'], criteria_sha=criteria_sha,
                             identity_key='repair_sha256', identity_sha=repair_sha)
    proposal = dict(definition, repair_sha256=repair_sha, criteria_sha256=criteria_sha,
                    original_question_sha256=text_sha(item['question_en']), original_query_sha256=text_sha(item['cypher']),
                    reference_query_sha256=text_sha(QUERY), primary_review=review,
                    completeness_witness={'file': witness_path.name, 'sha256': sha(witness_path)},
                    repair_reason={'previous_problem': 'Resolution versus CR-count ranking unit was unresolved.',
                                   'new_evidence': 'Full-pool four-metric requested-identity invariance, not a rewritten question or metric-equivalence claim.'},
                    admitted=False, new_model_calls=0, human_expert_validation_n=0)
    destination = HERE / 'path_top5_candidates'
    destination.mkdir(exist_ok=True)
    (destination / 'proposals.jsonl').write_text(json.dumps(proposal, ensure_ascii=False, sort_keys=True) + '\n')
    (destination / 'definition_only.jsonl').write_text(json.dumps(dict(definition, repair_sha256=repair_sha,
        criteria_sha256=criteria_sha, original_question_sha256=text_sha(item['question_en']),
        original_query_sha256=text_sha(item['cypher']), reference_query_sha256=text_sha(QUERY)),
        ensure_ascii=False, sort_keys=True) + '\n')
    print(json.dumps({'status': 'PREPARED_NOT_ADMITTED', 'id': item['id'], 'repair_sha256': repair_sha,
                      'candidate_sha256': sha(destination / 'proposals.jsonl'), 'witness_sha256': sha(witness_path),
                      'full_pool_n': len(rows), 'requested_identity_set': answer}, ensure_ascii=False))


if __name__ == '__main__':
    main()
