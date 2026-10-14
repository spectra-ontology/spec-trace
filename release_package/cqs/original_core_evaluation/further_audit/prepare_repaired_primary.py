"""New pinned candidates after independent objections; preserve prior proposals."""
import copy
import hashlib
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
ORIG = BASE.parent
sys.path.insert(0, str(ORIG))
import build
import review_schema

units = json.loads((ORIG / 'criteria.json').read_text())['semantic_units']
criteria_sha = hashlib.sha256((ORIG / 'criteria.json').read_bytes()).hexdigest()
keys = ('id', 'question_en', 'original_query', 'reference_query', 'required_fields', 'collection',
        'cardinality_policy', 'repair_class', 'original_question_preserved')
prior = {r['id']: r for r in map(json.loads, (BASE / 'unresolved_repairs_RAN1_RAN2.jsonl').read_text().splitlines())}
originals = {r['id']: r for r in map(json.loads, Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/spectra_cq_v2.0/benchmark.jsonl').read_text().splitlines())}
reviews = {r['id']: r for r in map(json.loads, (BASE / 'secondary_RAN1_RAN2.jsonl').read_text().splitlines())}


def field(name, nullable=False, type_name='string'):
    return {'name': name, 'type': type_name, 'nullable': nullable, 'source_column_or_expression': name}


def candidate(identifier, query, fields, findings, *, k=None, source_context=None):
    original = originals[identifier]
    collection = {'kind': 'set'}
    cardinality = {'mode': 'all'}
    if k:
        column = 'crCount' if identifier == 'RAN1_P3_CQ036' else 'impactCount'
        collection = {'kind': 'top_k_boundary_ties', 'value': k,
                      'source_order_keys': [{'source_column': column, 'direction': 'desc'}],
                      'tie_policy': 'any_subset_at_boundary', 'within_tie_order': 'any',
                      'require_rank_order': False}
        cardinality = {'mode': 'top_k', 'value': k, 'tie_policy': 'any_subset_at_boundary'}
    definition = {'id': identifier, 'question_en': original['question_en'], 'original_query': original['cypher'],
                  'reference_query': query, 'required_fields': fields, 'collection': collection,
                  'cardinality_policy': cardinality, 'repair_class': 'query_and_scorer', 'original_question_preserved': True}
    sha = build.digest(definition)
    evidence = [{'unit': unit, 'status': 'pass', 'original_quote': original['question_en'],
                 'query_clauses': query.splitlines(), 'finding': finding} for unit, finding in zip(units, findings)]
    review = {'id': identifier, 'status': 'pass', 'repair_sha256': sha, 'criteria_sha256': criteria_sha,
              'original_question_sha256': hashlib.sha256(original['question_en'].encode()).hexdigest(),
              'reviewer_kind': 'Primary AI original-question semantic inspection /root/dqqc_final_perspective',
              'semantic_evidence': evidence, 'source_context': source_context or copy.deepcopy(prior[identifier]['primary_review']['source_context']),
              'review_scope': 'New proposal after source inspection; separate exact-hash secondary/native/scorer gates remain uncompleted',
              'human_author_review_completed': False, 'expert_validation_n': 0}
    review_schema.check_pass(review, original['question_en'], units, criteria_sha=criteria_sha,
                             identity_key='repair_sha256', identity_sha=sha)
    result = dict(definition, repair_sha256=sha, criteria_sha256=criteria_sha,
                  original_question_sha256=review['original_question_sha256'],
                  original_query_sha256=hashlib.sha256(original['cypher'].encode()).hexdigest(),
                  reference_query_sha256=hashlib.sha256(query.encode()).hexdigest(), primary_review=review,
                  validation_status='pending', human_author_review_completed=False, expert_validation_n=0,
                  model_calls=0, reference_evidence_status='New/reused exact-query complete native output and second semantic review/scorer controls required; not admitted')
    result['repair_reason'] = {'new_proposal_preserves_previous_versions': True,
                              'prior_proposal_repair_sha256': prior.get(identifier, {}).get('repair_sha256'),
                              'prior_secondary_status': reviews.get(identifier, {}).get('status', 'not_yet_reviewed'),
                              'repair': findings[0] + ' ' + findings[2] + ' ' + findings[3],
                              'native_execution_by_this_reviewer': False,
                              'cohort_status': 'Separate further expansion; no changes to frozen350/runtime/current50 candidates'}
    return result


records = []
records.append(candidate('RAN2_P4_CQ4-4',
    "MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company)\nWHERE comp.companyName CONTAINS 'Samsung'\nWITH c\nMATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec)\nRETURN DISTINCT s.specNumber AS spec",
    [field('spec', nullable=True)], [
        'The question requests a set of other specification identities, so only spec is required. No vendor label, category label, title or numerical impact count is separately asked.',
        'Use the preserved original-query Samsung submitter predicate CONTAINS, rather than selecting only the exact canonical Company Samsung. This keeps separately recorded Samsung-named submitters that the original source context included; it does not claim a verified external corporate-family ontology.',
        'Preserve CR SUBMITTED_BY Company and all three declared OtherSpecs AFFECTS roles. The AFFECTS fields are source form declarations, so do not subtract targets sharing a number with MODIFIES: actual source overlaps exist and such subtraction was an unsupported new choice.',
        'RETURN DISTINCT specNumber forms the requested union over all qualifying CRs, categories and repeated target editions. No occurrence count or duplicate specification answer is required.',
        'List supplies no k, meeting, edition or positive-document condition beyond the preserved submission and declaration roles. There is no LIMIT or mandatory meeting join, so capture the full declaration-target union before scoring.',
        'The question supplies no presentation order. A set accepts any order and does not make the old ORDER BY spec a mandatory answer sequence.',
        'The interpretation is a source-relative lookup of declared OtherSpecs for the original recorded submitter predicate, not proof of realized downstream effects or externally validated Samsung ownership. English/query bytes and source roles are pinned; fresh exact-hash secondary and native evidence remain required.'
    ]))

records.append(candidate('RAN2_P4_CQ2-4',
    'MATCH (c:CR)\nOPTIONAL MATCH (c)-[impact:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->()\nWITH c, count(DISTINCT impact) AS impactCount\nRETURN c.tdocNumber AS tdocNumber, impactCount\nORDER BY impactCount DESC',
    [field('tdocNumber')], [
        'The explicit top10 asks CR identities ranked by the recorded cross-spec impact metric. tdocNumber is the required answer; the count supplies rank evidence rather than an independently requested output field.',
        'All frozen CR entities are eligible for the ranking, including zero declared-impact links. Direct RAN2 source audit found34622 CR nodes with unique nonnull tdocNumber; no meeting, vendor, release or topic restriction is added.',
        'Retain the original AFFECTS_CORE_SPEC/TEST_SPEC/OM_SPEC declared association roles and every original target. Remove the prior proposed MODIFIES subtraction, which could change actual declaration populations. No extra target label or actual-effect classifier is introduced.',
        'Preserve the original_query count(r) association unit: count distinct actual impact relationships, not distinct specNumber and not primary-target-excluded specs. On the direct single-hop relation this is the same as the original relationship count; DISTINCT protects against repeated query paths without collapsing distinct role-specific declarations. This is a recorded-declaration metric, not a new distinct-spec metric.',
        'Capture the whole uncapped CR pool with OPTIONAL links giving count0. The explicit10 selects min(10,pool size), retaining every higher rank and any needed subset tied at the boundary. Exact full native pool and scorer negative controls are still uncompleted.',
        'Top10 constrains membership, without an explicit output sequence or lexical TDoc tie breaker. Only impactCount DESC supplies ranking; any tied subset at the boundary and any final answer order are accepted.',
        'The frozen original reference query establishes the impact association-count context. This revision makes no external causal assertion or new subtraction/deduplication definition; it does not turn historical scores into new model evidence. Separate second review may still reject this source-context interpretation, and no admission is claimed.'
    ], k=10))

resolution_context = copy.deepcopy(prior['RAN2_P2_CQ1-5']['primary_review']['source_context'])
resolution_audit = BASE / 'resolution_identity_RAN2.json'
ra = json.loads(resolution_audit.read_text())
assert ra['missing_resolutionId_n'] == 0 and not ra['duplicate_resolutionId_counts']
resolution_context.update({'resolution_identity_audit_path': str(resolution_audit.relative_to(BASE.parents[4])),
                           'resolution_identity_audit_sha256': hashlib.sha256(resolution_audit.read_bytes()).hexdigest()})
records.append(candidate('RAN2_P2_CQ1-5', prior['RAN2_P2_CQ1-5']['reference_query'],
    [field('resolutionId')], [
        'List the resolutions requests Resolution identities. Require resolutionId only; the native query still returns content as auxiliary information, but an identity answer is not rejected for omitting an unasked content attribute.',
        'The original related-to-Rel18 source context is Resolution REFERENCES Tdoc TARGET_RELEASE Release(Rel-18), exactly preserved. Full frozen RAN2 source scan found3773 Resolution entities with no missing or duplicate resolutionId, so identity-only projection remains discriminative in this snapshot.',
        'Preserve the fixed Rel-18 and documentary relation path. Remove the original mandatory MADE_AT and LIMIT10 because meeting membership and top-k are not requested. Relatedness does not imply approval, causal adoption or substantive resolution completion.',
        'DISTINCT resolution projection removes duplicated paths through multiple release-targeted TDocs. The required identity projection identifies each actual Resolution once; auxiliary textual content is not part of required scoring.',
        'List has no numerical cap or temporal restriction. Capture all qualifying Resolution identities; the native projection may include text, but strict requested-field comparison uses the whole identity set. Fresh full exact-query receipt remains necessary.',
        'No answer order or recency is requested. A set accepts any order and does not require old meeting/sequence values in the answer.',
        'No missing release or date input is chosen. Required fields are derived from the original identity-list request, without treating available rationale/content as mandatory or claiming human/expert validation. Actual source-null absence is observed in this frozen graph, not a universal schema guarantee.'
    ], source_context=resolution_context))

structure_path = BASE / 'RAN1_structure_audit.json'
structure = json.loads(structure_path.read_text())
numbers = ['38.201', '38.202', '38.211', '38.212', '38.213', '38.214', '38.215', '38.291']
assert sorted(structure['section_owning_spec_populations']) == sorted(numbers)
context = {'wg': 'RAN1', 'graph_source_sha256': structure['source_sha256'],
           'read_only_full_structure_audit_path': str(structure_path.relative_to(BASE.parents[4])),
           'read_only_full_structure_audit_sha256': hashlib.sha256(structure_path.read_bytes()).hexdigest(),
           'current_phase_metadata_used_as_original_scope_authority': False,
           'original_context_basis': 'Original reference query explicitly enumerates the same eight numbers; full frozen source shows exactly these eight Section-owning TS numbers',
           'parser_sha256': structure['parser_sha256']}
records.append(candidate('RAN1_P3_CQ036',
    "MATCH (sp:Spec)\nWHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291']\nWITH DISTINCT sp.specNumber AS ts\nOPTIONAL MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:ts})\nWITH ts, count(DISTINCT cr) AS crCount\nOPTIONAL MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:ts})\nRETURN ts, crCount, count(DISTINCT sec) AS sectionCount\nORDER BY crCount DESC",
    [field('ts'), field('crCount', type_name='integer'), field('sectionCount', type_name='integer')], [
        'Compare top5 TSs by CR count against their section counts explicitly requires each TS identity, its integer CR count and its integer Section count. All three named fields are required; no title, release or complexity score is added.',
        'The original source query explicitly limits its phase3 comparison to eight TS numbers. Preserve exactly that list, not a newly chosen whitelist. Direct frozen-source inspection independently shows these are exactly the eight Section-owning TS numbers in RAN1. Base/release nodes with the same number are one TS identity; no latest-edition restriction is imported.',
        'Preserve CR MODIFIES Spec and Section BELONGS_TO_SPEC for the same TS number. Optional joins include eligible zero-count cases rather than requiring both a CR and a Section. No company, meeting, release or title filter is added.',
        'Count DISTINCT CR entities per TS before joining Sections, then DISTINCT Section entities per TS across the same source edition population used by the original query. This avoids multiple Spec/path edges and CR-by-Section multiplication; it does not change the denominator to a selected latest edition.',
        'The original explicitly requests top5. Remove the early LIMIT5 to capture all eight eligible TS records with their counts; the top_k_boundary_ties contract selects min(5,pool size), all greater CR counts and any needed boundary-tied subset. Full exact-query native evidence and strict wrong-count controls remain required.',
        'By CR count supplies the rank criterion, not an explicit output order or arbitrary TS lexical tie breaker. Use crCount DESC as the only ranking key, allow any tied boundary subset and any final answer ordering.',
        'The parenthetical comparison motivates two recorded counts; it is not a validated implementation-complexity metric or measured correlation/causal result. The eight-number scope is preserved from the frozen original query and independently matches the source phase3 TS population, without relying on updated phase metadata or expert approval.'
    ], k=5, source_context=context))

output = BASE / 'additional_proposals_RAN1_RAN2.jsonl'
output.write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in records))
print(json.dumps({'path': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                  'rows': len(records), 'repair_hashes': {r['id']: r['repair_sha256'] for r in records}}, ensure_ascii=False))
