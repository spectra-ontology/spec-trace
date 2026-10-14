"""Freeze a natural breadcrumb candidate from the unchanged original question."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PREP = HERE.parents[2]
ROOT = PREP.parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(PREP))
sys.path.insert(0, str(PREP / 'original_repair'))
import build
import review_schema


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def main():
    output = HERE / 'candidates.jsonl'
    assert not output.exists()
    source = next(row for row in map(json.loads, (HERE.parent / 'RAN1_RAN2.jsonl').open())
                  if row['id'] == 'RAN1_P3_CQ003')
    witness_path = HERE.parent / 'RAN1_RAN2_natural_edition_witness.json'
    source_witness = json.loads(witness_path.read_text())
    item = next(row for row in source_witness['items'] if row['id'] == source['id'])
    assert item['full_natural_records_invariant'] and item['structured_editions_n'] == 5
    assert len({row['record_sha256'] for row in item['edition_results']}) == 1
    benchmark = Path(source['evidence']['input_pins']['original_benchmark']['path'])
    assert sha(benchmark) == source['evidence']['input_pins']['original_benchmark']['sha256']
    original = next(row for row in map(json.loads, benchmark.open()) if row['id'] == source['id'])
    question, old_query = original['question_en'], original['cypher']
    assert question == source['original_question'] and old_query == source['original_query']
    criteria_path = PREP / 'original_repair' / 'criteria.json'
    criteria, criteria_sha = json.loads(criteria_path.read_text()), sha(criteria_path)
    clauses = [
        "MATCH (target:Section {sectionNumber:'5.1.3.2'})-[:BELONGS_TO_SPEC]->(:Spec {specNumber:'38.214'})",
        "WITH DISTINCT target",
        "MATCH p=(target)-[:PARENT_SECTION*0..]->(root:Section)",
        "WHERE NOT EXISTS { MATCH (root)-[:PARENT_SECTION]->(:Section) }",
        "RETURN DISTINCT [n IN reverse(nodes(p)) | n.sectionNumber] AS breadcrumb",
    ]
    definition = {
        'id': source['id'], 'question_en': question, 'original_query': old_query,
        'reference_query': ' '.join(clauses),
        'required_fields': [{'name': 'breadcrumb', 'type': 'json', 'nullable': False,
            'source_column_or_expression': 'breadcrumb',
            'json_schema': {'type': 'array', 'items': {'type': 'string'}},
            'nested_array_semantics': {'$': 'sequence'}}],
        'collection': {'kind': 'set'}, 'cardinality_policy': {'mode': 'exact', 'value': 1},
        'repair_class': 'query_and_scorer', 'original_question_preserved': True,
    }
    repair_sha = build.digest(definition)
    witness = {'path': str(witness_path.relative_to(ROOT)), 'sha256': sha(witness_path),
        'item_id': source['id'], 'all_matching_structured_editions': 5,
        'all_matching_spec_nodes': 6, 'unversioned_hub_incoming_editions': 5,
        'number_and_title_path_equal_in_all_five_editions': True,
        'actual_unique_parent_and_cycle_checks': True}
    findings = [
        "The original asks a breadcrumb locating one naturally named Section in its TS hierarchy. Give root-to-target ordered section identifiers as one string-array breadcrumb; do not require release-qualified loader IDs. Old query titles are contextual rather than an additional requested field in this minimal locating-path contract. The stronger witness also compares every title and finds the full labelled paths identical. This field-role judgment remains subject to independent review.",
        "Use every actual Section5.1.3.2 belonging to Spec38.214 in the original frozen RAN1 graph, without choosing a release or latest version. Complete source scan finds five structured roots Rel15–19, one each, and identical number-and-title paths. A sixth unversioned Spec has five incoming IN_RELEASE_OF edges and no direct Sections; it is a version hub, not a missing empty edition. The shared natural projection is independent of matching edition; DISTINCT removes duplicate natural answers without averaging or selecting an edition.",
        "BELONGS_TO_SPEC anchors the Section to its TS. Outgoing PARENT_SECTION follows child to direct parent. In every edition the actual complete chain is5.1.3.2→5.1.3→5.1→5; every visited node has at most one parent and no cycle. The no-parent predicate selects the top-level Section; reverse(nodes(p)) gives the breadcrumb. Remove the old depth10 cap and impose no unasked topic/time/release filter.",
        "No numeric aggregate is requested. One ordered natural path is the answer unit. WITH DISTINCT target prevents duplicated anchoring routes from duplicating traversal; RETURN DISTINCT deduplicates identical whole natural paths across editions. Individual ancestor entries are neither deduplicated nor position-reordered. Actual unique-parent/no-cycle checks show no hidden multiplication of alternate paths.",
        "The full source scan covers all six matching Spec nodes and five matching Section roots. Every complete ascent has three parent edges and contains the target plus all ancestors. The new query has neither LIMIT nor depth cap and returns every distinct natural path. Exact1 follows actual equality of all five full paths; fresh native receipt and source guard remain required for admission. This proves the frozen matching graph extent, not all physical editions or expert validation.",
        "A breadcrumb is ordered root-to-target. reverse(nodes(p)) gives this hierarchy order and nested_array_semantics {'$':'sequence'} rejects reversed or shuffled paths. No lexical sort, level approximation, arbitrary tie-break or outer-record order is added. Target appears last.",
        "No unbound edition/default/latest or external author intent is introduced: all frozen matching structured editions have the same complete labelled breadcrumb. Preserve original English/Korean graph hierarchy context; later changed phase queries are not original scope authority. This is an AI primary judgment, not a model result or human/expert review. Separate AI secondary, exact-query native capture and strict requested-field/sequence scorer checks are still required before admission.",
    ]
    review = {'id': source['id'], 'status': 'pass', 'repair_sha256': repair_sha,
        'criteria_sha256': criteria_sha, 'original_question_sha256': text_sha(question),
        'reviewer_kind': 'AI source-first primary semantic review',
        'human_author_review_completed': False, 'expert_validation_n': 0,
        'semantic_evidence': [{'unit': unit, 'status': 'pass', 'original_quote': question,
            'finding': finding, 'query_clauses': clauses, 'source_evidence': witness}
            for unit, finding in zip(criteria['semantic_units'], findings)]}
    review_schema.check_pass(review, question, criteria['semantic_units'], criteria_sha=criteria_sha,
                             identity_key='repair_sha256', identity_sha=repair_sha)
    record = {**definition, 'repair_sha256': repair_sha, 'criteria_sha256': criteria_sha,
        'original_question_sha256': text_sha(question), 'original_query_sha256': text_sha(old_query),
        'reference_query_sha256': text_sha(definition['reference_query']), 'primary_review': review,
        'repair_reason': {'old_pending_reason': source['existing_unresolved_reason'],
            'repair': 'Remove unstated latest release and cutoffs. Traverse every matching natural hierarchy, then deduplicate invariant ordered Section-number paths. Do not require unasked version identity/title fields.',
            'finding_class': 'definition and query repair with new source measurement'},
        'completeness_witness': witness,
        'source_graph': source_witness['db_evidence']['RAN1']['graph_source'],
        'original_benchmark': {'path': str(benchmark), 'sha256': sha(benchmark)},
        'original_korean_source': source['original_korean_source'],
        'admitted': False, 'new_admitted_n': 0, 'new_model_calls': 0,
        'native_reference_query_capture_completed': False,
        'integration_gates': ['Separate AI secondary semantic review exact definition SHA',
            'Fresh exact-query native receipt on guarded original frozen RAN1 graph',
            'Nested sequence/required field/type/value/cardinality strict scorer controls']}
    output.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
    print(json.dumps({'candidate_sha256': sha(output), 'repair_sha256': repair_sha,
        'question_sha256': text_sha(question), 'ref_query_sha256': text_sha(definition['reference_query']),
        'new_admitted_n': 0}))


if __name__ == '__main__':
    main()
