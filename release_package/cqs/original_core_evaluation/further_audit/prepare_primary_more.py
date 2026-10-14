#!/usr/bin/env python3
"""Separate followup proposals; never extend the frozen 350-model cohort."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ORIG = BASE.parent
SOURCE = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/spectra_cq_v2.0/benchmark.jsonl')
CRITERIA = 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
UNITS = ['requested answer roles and fields', 'population and source context',
         'filters and relationship meaning', 'counting unit and join multiplicity',
         'cardinality and completeness', 'ordering and ties when requested',
         'unverified additional inputs or external interpretation']


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def field(name):
    return {'name': name, 'type': 'string', 'nullable': False, 'source_column_or_expression': name}


def task(identifier, query, fields, evidence, *, k=None, rank_column=None):
    original = originals[identifier]
    collection = {'kind': 'set'}
    cardinality = {'mode': 'all', 'extent': evidence[4]}
    if k:
        collection = {'kind': 'top_k_boundary_ties', 'value': k,
                      'source_order_keys': [{'source_column': rank_column, 'direction': 'desc'}],
                      'tie_policy': 'any_subset_at_boundary', 'within_tie_order': 'any',
                      'require_rank_order': False}
        cardinality = {'mode': 'top_k', 'value': k, 'tie_policy': 'any_subset_at_boundary'}
    definition = {'id': identifier, 'question_en': original['question_en'],
                  'original_query': original['cypher'], 'reference_query': query,
                  'required_fields': fields, 'collection': collection,
                  'cardinality_policy': cardinality, 'repair_class': 'query_and_scorer',
                  'original_question_preserved': True}
    repair_hash = sha(json.dumps(definition, ensure_ascii=False, sort_keys=True, separators=(',', ':')))
    record = dict(definition, repair_sha256=repair_hash, criteria_sha256=CRITERIA,
                  original_question_sha256=sha(original['question_en']),
                  original_query_sha256=sha(original['cypher']), reference_query_sha256=sha(query))
    record['primary_review'] = {'id': identifier, 'status': 'pass', 'repair_sha256': repair_hash,
                               'criteria_sha256': CRITERIA,
                               'original_question_sha256': record['original_question_sha256'],
                               'reviewer_kind': 'Primary AI original-question semantic review; separate followup proposal',
                               'semantic_evidence': [{'unit': unit, 'status': 'pass',
                                                      'original_quote': original['question_en'],
                                                      'query_clauses': query.splitlines(), 'finding': finding}
                                                     for unit, finding in zip(UNITS, evidence)],
                               'human_author_review_completed': False, 'expert_validation_n': 0}
    record['repair_reason'] = {'prior_problem': old_problems[identifier],
                              'repair': evidence[2] + ' ' + evidence[3],
                              'cohort_status': 'Separate further expansion. Never add to the frozen350 empirical cohort or reuse its scores.',
                              'not_admitted_reason': 'Fresh exact-query full native evidence, independent second semantic review, complete-pool/identity checks and actual scorer controls are not yet obtained.'}
    return record


originals = {item['id']: item for item in [json.loads(line) for line in SOURCE.read_text().splitlines()]}
old_problems = {}
records = []
scope_basis = ('The benchmark is executed on a frozen, multi-edition graph. Only the explicitly named specNumber and section/table identity restrict this lookup; the English contains no release/latest predicate. Removing the hidden latest selection rather than adding a new edition restriction retains every matching source instance. Native identity fields retain their edition distinctions. This is a source-relative lookup interpretation, not proof that one current normative edition represents all versions.')
lookups = [
    ('RAN5_P3_CQ1-2', '38.533', '5', 'HAS_SUB_SECTION', 'Section', 'sectionId'),
    ('RAN5_P3_CQ1-12', '38.523-1', '7', 'HAS_SUB_SECTION', 'Section', 'sectionId'),
    ('RAN5_P3_CQ1-5', '38.521-1', '6.2.3', 'CONTAINS_TABLE', 'TSTable', 'tableId'),
    ('RAN5_P3_CQ1-6', '38.509', '5.3.4.1', 'CONTAINS_FIGURE', 'TSFigure', 'figureId'),
    ('RAN5_P3_CQ2-1', '38.521-1', '6.5D.3.3.5', 'REFERENCES_SECTION', 'Section', 'sectionId'),
]
for identifier, spec, section, relationship, label, output_field in lookups:
    query = (f"MATCH (p:Section {{sectionNumber:'{section}'}})-[:BELONGS_TO_SPEC]->(:Spec {{specNumber:'{spec}'}})\n"
             f"MATCH (p)-[:{relationship}]->(item:{label})\n"
             f"RETURN DISTINCT item.{output_field} AS {output_field}")
    old_problems[identifier] = 'Original query silently selects one latest edition and imposes a final row cap absent from the original English.'
    evidence = [
        f'The original asks for matching {label} identities. Require only {output_field}; titles, captions, release labels and sorting diagnostics are not separately requested answer fields.',
        scope_basis + ' Actual source inventory edition_inventory_RAN5.json contains23 matching Spec nodes across the four named specNumbers, including release-bearing instances and unversioned hubs.',
        f'Preserve the original direct {relationship} relation and exact named specNumber={spec}, sectionNumber={section}; remove the hidden release-rank/latest selection and arbitrary row cap. No recursive traversal, additional document role or new version qualifier is introduced.',
        f'DISTINCT item.{output_field} returns the complete requested identity set, not duplicate membership paths. Different release-bearing identities remain distinct source items.',
        'Every source node matching the named spec/clause and original direct relation is included; no unasked edition-selection rule or numeric cap. Fresh full native output and identity/type checks remain necessary.',
        'The original asks a list, with no explicit answer order. A set accepts any order; old lexical presentation order does not become an additional requirement.',
        'Frozen source inventory and original question/query predicates ground the graph-relative lookup. No new company alias, WG owner, approval flag or expert decision is added. Independent secondary review must specifically consider this unqualified-source scope interpretation; this is not an independently validated normative edition answer.'
    ]
    records.append(task(identifier, query, [field(output_field)], evidence))

for identifier in ['RAN3_P2_CQ1-8', 'RAN4_P2_CQ1-8']:
    query = ('MATCH (ai:AgendaItem)\nOPTIONAL MATCH (r:Resolution)-[:RESOLUTION_BELONGS_TO]->(ai)\n'
             'WITH ai, count(DISTINCT r) AS resolutionCount\n'
             'RETURN coalesce(ai.id, ai.iri) AS agendaId, resolutionCount\nORDER BY resolutionCount DESC')
    old_problems[identifier] = 'Repeated agenda numbers from different meetings merge distinct entities; id-null grouping also merges nodes; fixedLIMIT10 hides boundary ties and the eligible pool.'
    evidence = [
        'Explicit top10 asks which agenda items, identified by agendaId. Resolution count determines rank and is not separately requested as an answer field.',
        'Every frozen AgendaItem node is eligible; include zero-count and missing-business-id nodes. WITH ai preserves the entity instead of conflating reusable agendaNumber/id-null values.',
        'The preserved Resolution RESOLUTION_BELONGS_TO AgendaItem path means recorded agenda association. No mandatory MADE_AT, meeting prefix, content-classifier or approval restriction is added.',
        'count(DISTINCT r) counts actual Resolution nodes per actual agenda node; repeated paths cannot multiply a resolution and anonymous agenda items cannot merge into a fake group.',
        'The original explicitly says10; capture the entire uncapped pool, selectmin(10,pool-size), include every strictly higher rank and any needed subset of the boundary tie. Fresh identity uniqueness/full-output gates required.',
        'Top10 specifies rank-based membership, not a required answer sequence. require_rank_order=false, with boundary freedom but rejection of lower-rank substitutions.',
        'Frozen loader uses a unique deterministic /inst/_/{cls}/{nid} iri when id is absent. This is a source-node identity codec, not an invented business identifier or external fact. Paired SQL exposes the same node_identity codec. Fresh actual native output and a second independent review remain required.'
    ]
    records.append(task(identifier, query, [field('agendaId')], evidence, k=10, rank_column='resolutionCount'))

identifier = 'RAN4_P1_CQ3-1'
query = ('MATCH (ai:AgendaItem)\nOPTIONAL MATCH (t:Tdoc)-[:BELONGS_TO]->(ai)\n'
         'WITH ai, count(DISTINCT t) AS tdocCount\n'
         'RETURN coalesce(ai.id, ai.iri) AS agendaId, tdocCount')
old_problems[identifier] = 'Repeated agendaNumber groups collapse different meetings, hiddenLIMIT10 truncates the distribution, and positive-only joining excludes zero-count agenda items.'
evidence = [
    'A distribution across agenda items requires each agenda identity and its integer TDoc count. Both agendaId and tdocCount are required; agenda description and meeting labels are not extra required values.',
    'All frozen AgendaItem nodes are the distribution population, since no meeting or positive-document restriction appears in the English. Zero-count items remain part of the graph-relative distribution.',
    'Preserve the original Tdoc BELONGS_TO AgendaItem association; start from AgendaItem and OPTIONAL that relation. No meeting113 restriction from a later Korean CQ is imported.',
    'Group by ai actual entity, count distinct Tdoc nodes, and expose recorded id or the deterministic loader iri. Repeated agenda numbers and anonymous nodes cannot collapse or inflate counts.',
    'Return every eligible agenda item including count0, without the unasked10 cap. Fresh complete output must verify unique nonnull identity and integer count for every item.',
    'Distribution asks all per-item counts and no explicit sequence. Score a set, not an unrequested descending order.',
    'The same explicit loader identity codec is available in Neo4j and SQL. This source-relative count does not claim that the archive captured every real meeting document; it requires a separate second semantic judgment and fresh native capture before admission.'
]
distribution_fields = [field('agendaId'), {'name': 'tdocCount', 'type': 'integer', 'nullable': False, 'source_column_or_expression': 'tdocCount'}]
records.append(task(identifier, query, distribution_fields, evidence))

for identifier, k, spec in [('RAN3_P3_CQ2-4', 10, None), ('RAN4_P3_CQ2-3', 10, None), ('RAN3_P3_CQ2-8', 5, '38.423')]:
    if spec:
        query = ("MATCH (b:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber:'38.423'})\nWITH DISTINCT b, sp\n"
                 'OPTIONAL MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp), (a)-[ref:REFERENCES_SECTION]->(b)\n'
                 'WITH b, count(DISTINCT ref) AS referenceCount\n'
                 'RETURN coalesce(b.sectionId,b.iri) AS sectionId, referenceCount\nORDER BY referenceCount DESC')
        population = 'The original explicitly names38.423 internal reference hubs. Preserve the original shared Spec-node context for source and target Sections, across every matching Spec instance; every eligible target remains in the pool even when its internal incoming count is0.'
    else:
        query = ('MATCH (b:Section)\nOPTIONAL MATCH (:Section)-[ref:REFERENCES_SECTION]->(b)\n'
                 'WITH b, count(DISTINCT ref) AS referenceCount\n'
                 'RETURN coalesce(b.sectionId,b.iri) AS sectionId, referenceCount\nORDER BY referenceCount DESC')
        population = 'Every frozen Section node is eligible for the original overall most-referenced ranking, including zero-count and anonymous source entities. No spec, release or working-group ownership filter is added.'
    old_problems[identifier] = 'FixedLIMIT hides ranking/tie population; distinct-source/native-edge count equivalence needed explicit source grounding rather than silently changing the unit.'
    evidence = [
        'The original explicitly asks top'+str(k)+' Section identities. Require sectionId only; title and numeric rank diagnostics are auxiliary, not separately demanded answers.',
        population,
        'Preserve incoming directed REFERENCES_SECTION as the reference relation. For the internal-spec query preserve the original same-spec-node membership rather than adding external references or latest-edition selection.',
        'Count distinct reference relationships per target Section entity. The shipped loader stores a set of(source,relationship-type,target), so one source-to-target REFERENCES_SECTION pair is not duplicated: the original count(source) equals edge occurrence count on this relation. DISTINCT ref additionally prevents membership joins duplicating an edge.',
        'Explicit k is preserved, but full uncapped eligible pool is captured; selected answers include all higher-count entities and any needed subset tied at the cutoff. Fresh exact-query output must verify identity uniqueness and complete pool.',
        'No answer-sequence order is explicitly requested, so require_rank_order=false. Only descending referenceCount governs selection; lexical Section ordering is not a required tie breaker.',
        'Source-unit equivalence follows from actual frozen loader relation-set construction, not expert approval or a successful model answer. coalesce(sectionId,iri) is an auxiliary source-node identity fallback, exposed equally in SQL. This remains a separately reviewed/executed followup proposal.'
    ]
    records.append(task(identifier, query, [field('sectionId')], evidence, k=k, rank_column='referenceCount'))

identifier = 'RAN4_P3_CQ2-5'
query = ('MATCH (a:Section)-[ref:REFERENCES_SECTION]->(b:Section),\n'
         '(a)-[:BELONGS_TO_SPEC]->(sa:Spec), (b)-[:BELONGS_TO_SPEC]->(sb:Spec)\n'
         'WHERE sa.specNumber <> sb.specNumber\n'
         'RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(DISTINCT ref) AS referenceCount\n'
         'ORDER BY referenceCount DESC')
old_problems[identifier] = 'Capped ranking pool and membership-join count(*) can inflate a reference edge; original top10 has unspecified boundary ties.'
evidence = [
    'Top10 cross-spec reference pairs requires the directed fromSpec/toSpec identities. A referenceCount/title is not an additional required answer field.',
    'Existing directed cross-spec pairs are eligible: a recorded Section reference whose endpoints belong to unequal specNumbers. Unreferenced arbitrary spec Cartesian pairs are not section-reference pairs.',
    'Preserve REFERENCES_SECTION, both BELONGS_TO_SPEC roles and the original unequal specNumber test. No new release, owner, document type or causal dependency classifier.',
    'count(DISTINCT ref) counts each directed Section reference once per directed specNumber pair, preventing a membership join from multiplying an edge; source and target directions are distinct answer roles.',
    'Explicit10 and complete uncapped pair-frequency pool are preserved; allow any boundary-tied subset while retaining all higher-ranked pairs. Native full-pool and typed-pair uniqueness evidence remain pending.',
    'No output sequence is requested; selected pairs can appear in any order, with no invented lexical tie break.',
    'Pair definition and recorded relation unit come from original English, original query roles and the frozen loader relation set. No independent expert, normative dependency, adoption or model-performance conclusion is asserted.'
]
records.append(task(identifier, query, [field('fromSpec'), field('toSpec')], evidence, k=10, rank_column='referenceCount'))

identifier = 'RAN4_P5_CQ5-3'
query = ('MATCH (tr:TechnicalReport)\nWITH DISTINCT tr.trNumber AS trNumber\n'
         'OPTIONAL MATCH (:TechnicalReport)-[ref:REFERENCES_TR]->(target:TechnicalReport)\n'
         'WHERE target.trNumber = trNumber\nRETURN trNumber, count(DISTINCT ref) AS referenceCount\nORDER BY referenceCount DESC')
old_problems[identifier] = 'OriginalLIMIT5 hides the full boundary-tie pool; unasked TR title/count must not become answer fields; edge/source equivalence was not grounded.'
evidence = [
    'The original asks which five TRs; trNumber identifies each conceptual report. Neither TR title nor reference count is separately requested as a required answer value.',
    'Every frozen TechnicalReport number is eligible, including reports with0 incoming recorded TR references. Group equal report numbers across source nodes instead of returning duplicate conceptual report identities.',
    'Count incoming directed REFERENCES_TR links from TechnicalReport nodes, matching the original relation and most-cited-studies context. No source-TDoc citation role or normative-TS-creation claim is introduced.',
    'Count distinct directed reference edges per target trNumber. The frozen loader deduplicates(source,type,target) relations; edge frequency, rather than joined path multiplicity, is the recorded citation unit.',
    'The original explicitly specifies5; capture the full uncapped pool including zeros, admit min(5,pool-size) distinct report numbers with all higher ranks and any boundary-tied subset.',
    'Most-referenced specifies membership by count, not a mandatory final sequence or lexical TR-number tie breaker; require_rank_order=false.',
    'Only recorded report identity/reference roles are used. Exact current-query native output and a second independent semantic judgment must verify this number-level aggregation before admission; no expert or new model-performance evidence is claimed.'
]
records.append(task(identifier, query, [field('trNumber')], evidence, k=5, rank_column='referenceCount'))

identifier = 'RAN4_P2_CQ2-4'
query = ('MATCH (s:Spec)\nWITH DISTINCT s.specNumber AS specNumber\n'
         'OPTIONAL MATCH (:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(target:Spec)\n'
         'WHERE target.specNumber = specNumber\nRETURN specNumber, count(DISTINCT t) AS tdocCount\nORDER BY tdocCount DESC')
old_problems[identifier] = 'Mandatory Resolution MADE_AT is unasked, positive-only ranking omits eligible zero Specs, andLIMIT10 omits full boundary ties.'
evidence = [
    'Top10 Specs by resolution-linked TDocs asks which Spec numbers. Require specNumber only; no linked TDoc ID, Resolution ID or count is separately demanded in the answer.',
    'All recorded specNumbers are eligible because the question says top10 Specs by a metric, not only Specs with a positive linked-document count. Group edition/base nodes by the same specification number.',
    'Preserve Resolution REFERENCES Tdoc MODIFIES Spec; remove mandatory MADE_AT absent from the English. This relation is a documentary link, not proof of approval or actual normative change.',
    'count(DISTINCT t) counts linked TDoc nodes per specNumber, never Resolution count or duplicate reference paths. OPTIONAL gives0 for Specs with no matching linked document.',
    'Keep explicit10 and capture the entire uncapped spec-number ranking pool; selected answers must retain all strictly higher ranks and any cutoff-tied subset.',
    'No answer order is explicitly required; rank governs valid membership only and no lexical Spec tie break is imposed.',
    'No additional RAN4 ownership classifier, approval predicate, meeting-selection rule or expert validation is introduced. The exact native population and independent second semantic review are still prerequisites, separate from these primary judgments.'
]
records.append(task(identifier, query, [field('specNumber')], evidence, k=10, rank_column='tdocCount'))

identifier = 'RAN3_P2_CQ4-2'
query = ("MATCH (s:Summary)-[:MODERATED_BY]->(:Company {companyName:'ZTE'}),\n"
         '(s)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem)\n'
         'RETURN DISTINCT coalesce(ai.id,ai.iri) AS agendaId')
old_problems[identifier] = 'Mandatory MADE_AT discards moderator-role records without a meeting link; reusable agendaNumber merges different items; hiddenLIMIT15 truncates the requested list.'
evidence = [
    'The original asks for agenda items, so agendaId is the required identity. A meeting identifier, Summary id or moderation count is not separately requested as an answer value.',
    'Eligible items are actual AgendaItem nodes linked to a Summary explicitly MODERATED_BY the recorded ZTE Company. No particular meeting/date or latest instance is named; preserve every qualifying item.',
    'MODERATED_BY supplies the moderator role; RESOLUTION_BELONGS_TO assigns that Summary to the agenda item. Remove mandatory MADE_AT because it is not the requested role path and may be absent. Do not infer moderation from mere TDoc submission.',
    'Return DISTINCT actual agenda identity; multiple Summary instances do not duplicate an item and reused agenda numbers do not merge items from different meetings.',
    'Every qualifying item is returned without the old15 cap. Fresh full output must verify source identity/role coverage, and distinct nonnull agenda identities before admission.',
    'The question asks a list and no specific temporal or lexical order; set scoring is sufficient.',
    'Recorded exact Company nameZTE is preserved without inventing a corporation/affiliate alias rule. The frozen loader identity fallback is a source-node key, not an extra business attribute. This tests recorded moderator roles and does not constitute independent expert confirmation of each underlying meeting record.'
]
records.append(task(identifier, query, [field('agendaId')], evidence))

followup = [json.loads(line) for line in (ORIG / 'followup_repairs_RAN5.jsonl').read_text().splitlines()]
records.extend(followup)
output = BASE / 'primary_RAN3_RAN4_RAN5.jsonl'
output.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in records))
print(json.dumps({'separate_further_proposals': len(records), 'output': str(output),
                  'original_question_bytes_changed': 0, 'admitted_by_this_script': 0,
                  'native_executions_by_this_script': 0, 'expert_validation_n': 0}))
