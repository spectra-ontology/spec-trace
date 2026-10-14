"""Record separate AI secondary judgments from the actual preserved definitions."""
import hashlib
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
ORIG = BASE.parent
sys.path.insert(0, str(ORIG))
import build
import review_schema

CRITERIA_PATH = ORIG / 'criteria.json'
CRITERIA_SHA = hashlib.sha256(CRITERIA_PATH.read_bytes()).hexdigest()
UNITS = json.loads(CRITERIA_PATH.read_text())['semantic_units']
KEYS = ('id', 'question_en', 'original_query', 'reference_query', 'required_fields', 'collection',
        'cardinality_policy', 'repair_class', 'original_question_preserved')
INPUT_PATH = BASE / 'primary_RAN3_RAN4_RAN5.jsonl'
INPUT_SHA = hashlib.sha256(INPUT_PATH.read_bytes()).hexdigest()
original_path = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/spectra_cq_v2.0/benchmark.jsonl')
originals = {r['id']: r for r in map(json.loads, original_path.read_text().splitlines())}
input_records = [{k: v for k, v in json.loads(line).items() if k != 'primary_review'}
                 for line in INPUT_PATH.read_text().splitlines()]
results = []

for record in input_records:
    identifier = record['id']
    wg = identifier.split('_')[0]
    definition = {key: record[key] for key in KEYS}
    assert build.digest(definition) == record['repair_sha256']
    assert definition['question_en'] == originals[identifier]['question_en']
    assert definition['original_query'] == originals[identifier]['cypher']
    question = definition['question_en']
    query = definition['reference_query']
    clauses = query.splitlines()
    audit_path = BASE / ('secondary_source_audit_' + wg + '.json')
    audit = json.loads(audit_path.read_text())
    findings = []
    statuses = ['pass'] * 7
    is_lookup = identifier in audit.get('lookup_population_difference', {})
    if is_lookup:
        observed = audit['lookup_population_difference'][identifier]
        findings = [
            'The original requests the matching named subsection/table/figure or outgoing referenced Section. Its source identity is sufficient to identify the requested item; the question does not separately request title, caption, release, number or count. The contract requires only that identity.',
            f"The original supplies the exact spec/clause but no edition phrase. The preserved original_query explicitly chooses the highest release, whereas this query returns the union over all matching releases. Direct frozen-TTL inspection proves a real population change: {observed['all_release_output_count']} all-release identities versus {observed['latest_release_output_count']} latest-release identities ({observed['extra_all_release_identity_count']} additional identities). The absence of an English edition phrase does not uniquely establish the all-release interpretation against that preserved source context. Neither latest nor all is assumed correct without original benchmark scope evidence.",
            'The named spec/clause and direct containment/reference direction are preserved. However, deleting the original latest-release selection changes a source-context filter. A frozen original default-edition/all-instance contract is needed to establish that removal as meaning-preserving rather than a new scope choice.',
            'RETURN DISTINCT item identity removes repeated paths, while release-bearing source identities remain distinct. The full source inspection found no null requested identity among this lookup output. This deduplication does not settle which editions should be eligible.',
            'The proposed query has no LIMIT and includes every match under its chosen all-release scope. Completeness for the original remains unconfirmed because its edition population is unresolved; a successful full native receipt for this query would prove execution completeness only within the selected scope.',
            'List/which supplies no required output sequence or tie rule. A set is appropriate; lexical sorting and captions from the old projection are not additional requested answers.',
            'No company role or external causal interpretation is added. The unresolved input is the original benchmark edition/default lookup context. Current CQ metadata may corroborate latest-default but is not treated as frozen-history authority. Keep pending instead of selecting an interpretation to increase coverage.'
        ]
        statuses[1] = statuses[2] = statuses[4] = statuses[6] = 'pending'
    elif identifier in {'RAN3_P2_CQ1-8', 'RAN4_P2_CQ1-8'}:
        ai = audit['identity_audits']['AgendaItem']
        findings = [
            'The explicit top10 request asks which AgendaItem entities rank highest. agendaId identifies each item; resolutionCount supplies the rank rather than an independently asked output value. The required identity-only projection follows that distinction.',
            f"Every frozen AgendaItem entity is eligible, including zero-resolution items. Full source scan found {ai['population']} AgendaItems and {ai['missing_property']} missing id properties. WITH ai groups actual entities, and coalesce(id,iri) keeps anonymous nodes instead of excluding/merging them; no effective identity duplicates were found.",
            'Resolution RESOLUTION_BELONGS_TO AgendaItem is the original association and role. The source has other classes using the same predicate, but the query correctly retains the explicit Resolution label, matching the original counting role. No mandatory meeting, date, approval or text filter is imposed.',
            'count(DISTINCT r) counts one actual Resolution node per AgendaItem entity; grouping by ai prevents reused agenda numbers or multiple null IDs from collapsing distinct source items. Optional joining represents zero as count0 rather than dropping it.',
            'The original explicitly specifies10. The reference query captures the complete uncapped eligible rank pool. The top_k_boundary_ties contract requires min(10,pool size), every higher-ranked item, and exactly the remaining quota from the boundary tie; lower-ranked replacements and duplicate identities are invalid. Fresh exact-query receipt and scorer controls remain integration gates.',
            'Top10 establishes ranked membership, with no request to output the answers in sorted order. Only resolutionCount DESC governs eligibility; any boundary-tied subset and any within-answer order is allowed. No unasked agenda-number tie breaker is required.',
            'The fallback is the deterministic loader node identity /inst/_/{class}/{key}, verified in the shipped loader, not an invented source business ID or a verbatim raw WG URI. Its equal disclosure in the frozen SQL/graph schema is a necessary paired evaluation condition. This semantic pass is AI review only; no native execution or admission is claimed.'
        ]
    elif identifier == 'RAN4_P1_CQ3-1':
        ai = audit['identity_audits']['AgendaItem']
        findings = [
            'A distribution across AgendaItems requires each agenda identity and its integer TDoc count. agendaId and tdocCount are required together; no meeting label, agenda text or list of TDoc IDs is additionally requested.',
            f"The English supplies no meeting restriction or positive-count qualifier. All {ai['population']} frozen AgendaItem entities form the distribution, including zero-count nodes. The {ai['missing_property']} id-null nodes remain separately identified through loader iri; the source scan found no effective identity duplicates.",
            'Tdoc BELONGS_TO AgendaItem preserves the original documentary membership relation. Starting from AgendaItem with OPTIONAL MATCH expands a positive-only join to the full requested distribution. No meeting number is imported from a later CQ version.',
            'WITH ai and count(DISTINCT t) produce one typed integer count of actual TDoc nodes per actual agenda entity. The query avoids reusable agendaNumber grouping and null-group collapse and does not count path multiplicity.',
            'The distribution has no requested top-k. There is no LIMIT or positive-count filter, so the full captured reference must contain every agenda entity. Fresh row-count/identity/type/full-receipt checks are still required; this is not a claim that the source archive covers every real-world TDoc.',
            'The question requests a distribution, with no explicit output ordering. The set contract accepts any order of the complete per-agenda count records.',
            'This is a graph-relative workload count, not inferred causal workload or approval. The deterministic loader identity is an explicit source-node codec, not the raw source URI, and must be equally exposed in SQL and graph schemas. No external input or human/expert judgment is asserted.'
        ]
    elif identifier in {'RAN3_P3_CQ2-4', 'RAN4_P3_CQ2-3', 'RAN3_P3_CQ2-8'}:
        internal = identifier == 'RAN3_P3_CQ2-8'
        k = 5 if internal else 10
        sections = audit['identity_audits']['Section']
        findings = [
            f'The original asks which top{k} Sections are most referenced. sectionId is the answer identity. The count determines rank; neither title nor numeric count is separately requested as an answer field.',
            ('The original explicitly restricts internal references to spec38.423. Both source and target Section belong to the same matching Spec entity, preserving the original relationship roles across recorded editions. All eligible target Sections remain candidates, including zero-incoming targets.' if internal else
             f"The overall/unqualified ranking covers all {sections['population']} frozen Section entities, with no added release/spec filter. Zero-reference targets remain eligible. Direct source scan found no missing sectionId or duplicated Section identities."),
            'Incoming REFERENCES_SECTION direction is preserved. ' + ('The shared sp membership restricts the reference source and target to the same recorded spec instance rather than counting outside references.' if internal else 'There is no extra membership, company or topic filter.'),
            f"Count distinct reference edges per target Section. Full source scan found {audit['reference_unit_equivalence']['distinct_section_reference_source_target_pairs']} unique REFERENCES_SECTION source-target pairs and zero duplicated pairs; the loader stores relations in a set. Consequently one incoming edge equals one referencing source Section on this exact relation, preserving the original count(source) unit. DISTINCT ref prevents membership joins inflating an edge.",
            f'Capture the complete uncapped eligible target pool; explicit top{k} and any boundary-tied subset remain the requested selection. Higher counts must always win, and the output quota is min(k,pool size). Native complete-pool checks and actual scorer negative controls remain required before admission.',
            'The question specifies a rank criterion and k, without an answer sequence or lexical identity tie breaker. require_rank_order=False with count-based membership and any order within/between submitted answer records does not weaken ranked selection.',
            'The reference is a recorded directed Section citation, not measured normative importance. Source identities are nonnull and unique in the full source; the fallback codec does not change present identities. No external topic/edition input is selected, and no human/expert or new model performance result is claimed.'
        ]
    elif identifier in {'RAN4_P3_CQ2-5', 'RAN5_P3_CQ2-4'}:
        maximum = identifier == 'RAN5_P3_CQ2-4'
        findings = [
            'The original requests directed spec-to-spec Section-reference pairs. fromSpec and toSpec preserve the separate source and target answer roles. Frequency is a selection metric; a numeric count is not separately requested in the answer.',
            'Eligible pairs have at least one recorded directed Section reference and unequal endpoint specNumbers. Unreferenced arbitrary Cartesian Spec pairs are not Section-reference pairs. No release, company or current-version restriction is added.',
            'REFERENCES_SECTION and both BELONGS_TO_SPEC endpoint memberships reproduce the original directed cross-spec roles; sa.specNumber<>sb.specNumber removes within-spec links. This represents recorded references, not proof of causal dependency or actual change propagation.',
            'count(DISTINCT ref) counts each Section-reference edge once per directed specNumber pair. The full source confirms deduplicated directed relation pairs; membership joins cannot multiply a reference occurrence. Reversing fromSpec/toSpec is a different answer.',
            ('Most frequent has no k: group every observed pair, compute the global maximum and return all pairs tied at that maximum. The old LIMIT10 is not retained as an invented quota. On an empty pair population the result is empty.' if maximum else
             'The explicit top10 applies to the full uncapped observed-pair frequency pool. If fewer than10 pairs exist, return all of them; otherwise retain all higher frequencies and any required boundary-tied subset. No arbitrary zero-frequency pair is introduced.'),
            ('All maximum ties are required and their output order is unrestricted, matching the set/all contract.' if maximum else
             'The question gives no output sequence or pair-identifier tie-break. Boundary-tied subsets are permitted while lower-frequency selections remain invalid; require_rank_order=False is appropriate.'),
            'The graph association and original exact role/predicate pattern establish this count question without extra causal/topic interpretation. Fresh native exact-query pair uniqueness, source-number type checks and strict scorer controls are still needed; separate AI semantic pass does not assert admission or human expertise.'
        ]
    elif identifier == 'RAN4_P5_CQ5-3':
        reports = audit['identity_audits']['TechnicalReport']
        findings = [
            'The question asks which five TRs are most cited. trNumber identifies the requested report; title and numeric referenceCount are auxiliary old projection fields, not separately asked outputs.',
            f"All {reports['population']} frozen TechnicalReport identities are eligible, including zero-reference reports. Source scan found no missing or duplicate trNumber, so number-level grouping does not merge distinct report entities in this snapshot.",
            'The preserved incoming TechnicalReport REFERENCES_TR TechnicalReport relation supplies the citation role. It does not add TDoc citations, a date restriction or a TS-creation/approval claim.',
            'count(DISTINCT ref) counts incoming directed recorded TR-reference edges, never joined paths. The loader relation set deduplicates source/type/target; with one report per trNumber in this source, grouping by number preserves the original per-report unit.',
            'The query has no LIMIT and begins with every report number, so zeros and the whole top5 boundary pool remain represented. The contract selects min(5,pool size), with all higher ranks and any quota-completing boundary subset. Fresh exact-query receipt and scorer checks remain gates.',
            'Most-referenced specifies rank membership, not the order in which answers must be printed. No lexical TR-number tie break is required; only referenceCount DESC controls eligibility.',
            'No external notion of study influence, human endorsement or downstream normative outcome is inferred. Direct frozen source evidence grounds report numbers and edge units; any future source with duplicated/missing numbers would require renewed identity checks.'
        ]
    elif identifier == 'RAN4_P2_CQ2-4':
        findings = [
            'The original asks which top10 Spec identities have the greatest number of resolution-linked TDocs. specNumber is the requested answer; neither individual TDoc IDs nor the count is separately requested.',
            'All frozen specNumbers are eligible, including zero linked TDocs. Edition/base nodes with the same specNumber describe the same requested Spec-number identity; WITH DISTINCT prevents duplicate report rows. Exact source-number nonnull and pool uniqueness checks remain necessary.',
            'Resolution REFERENCES Tdoc MODIFIES Spec preserves the original documentary path. MADE_AT is absent from the English, so its mandatory join is removed. Resolution-linked does not imply approval or an enacted normative change.',
            'count(DISTINCT t) counts each actual linked TDoc once per specNumber, regardless of multiple Resolution references or Spec-edition joins. It is not Resolution count or raw path count, matching the original explicit distinct-TDoc aggregation.',
            'The query captures an uncapped pool of every specNumber and count0 where no linked TDoc exists. The top10 contract requires all higher ranks and any boundary-tied subset needed to fill min(10,pool size). Full receipt and typed uniqueness checks remain integration requirements.',
            'The question does not request an answer sequence or lexical Spec tie break. require_rank_order=False preserves rank-based membership while allowing boundary ties and arbitrary final answer order.',
            'The source relation is used as a documentary link only. No missing date, owner, topic or approval classifier is introduced. This separate AI judgment does not substitute for full native output and scorer controls or claim expert validation.'
        ]
    elif identifier == 'RAN3_P2_CQ4-2':
        observed = audit['zte_moderation_lookup']
        findings = [
            'The original asks which agenda items ZTE moderated. agendaId identifies each actual AgendaItem; an output meeting label or Summary ID is not separately requested.',
            f"All AgendaItems linked to ZTE-moderated Summary nodes in this frozen source are eligible. Full source scan found {observed['canonical_company_nodes']} exact Company ZTE, {observed['moderated_summary_nodes']} moderated Summaries and {observed['distinct_agenda_nodes']} distinct linked AgendaItems. The Company equality is the same as the preserved original_query, so no vendor-family choice is newly introduced.",
            'Summary MODERATED_BY Company(ZTE) and Summary RESOLUTION_BELONGS_TO AgendaItem preserve the original moderator-role direction. Removing MADE_AT avoids filtering items by an unasked meeting relation; no proposer/supporter role is substituted.',
            'RETURN DISTINCT coalesce(ai.id,ai.iri) records each AgendaItem once even when multiple moderated summaries point to it. Full source audit proves effective AgendaItem identities unique and keeps missing business-ID nodes with the exact loader identity codec.',
            'There is no English top-k or recency restriction. Removing LIMIT15 and the mandatory meeting join returns the whole qualifying agenda set. Fresh exact-query full native capture must establish the actual typed records before admission.',
            'List specifies no required order. The set accepts any output order and does not require the unasked meeting recency order used by the old query.',
            'Moderation is the explicit recorded MODERATED_BY role, not claimed meeting-chair authority or support. The loader identity is a deterministic node codec, not the raw source URI; paired schema disclosure remains necessary. No external interpretation or human/expert evaluation is claimed.'
        ]
    else:
        raise ValueError(identifier)
    assert len(findings) == 7
    status = 'pending' if 'pending' in statuses else 'pass'
    result = {'id': identifier, 'status': status, 'repair_sha256': record['repair_sha256'],
              'criteria_sha256': CRITERIA_SHA,
              'original_question_sha256': hashlib.sha256(question.encode()).hexdigest(),
              'reference_query_sha256': hashlib.sha256(query.encode()).hexdigest(),
              'reviewer_kind': 'Separate secondary AI semantic review /root/dqqc_final_perspective',
              'review_scope': 'Original/question/query/contract derivation with direct frozen-source checks; no new native execution, model call or admission',
              'primary_rationale_exposure': 'Preparation script and primary proposal format were visible; this is not blind review. Findings are separately derived and disagreements retained.',
              'input_file_sha256': INPUT_SHA, 'source_context': {
                  'graph_source_sha256': audit['graph_source_sha256'],
                  'direct_source_audit_path': str(audit_path.relative_to(BASE.parents[4])),
                  'direct_source_audit_sha256': hashlib.sha256(audit_path.read_bytes()).hexdigest(),
                  'parser_sha256': audit['parser_sha256'],
                  'current_phase_metadata_used_as_frozen_history_authority': False,
                  'source_loader_identity_is_raw_uri_verbatim': False},
              'semantic_evidence': [{'unit': unit, 'original_quote': question, 'query_clauses': clauses,
                                     'finding': finding, 'status': unit_status}
                                    for unit, finding, unit_status in zip(UNITS, findings, statuses)],
              'human_author_review_completed': False, 'expert_validation_n': 0,
              'validation_status': 'pending_native_and_scorer_integration' if status == 'pass' else 'pending_semantic_scope'}
    if status == 'pass':
        review_schema.check_pass(result, question, UNITS, criteria_sha=CRITERIA_SHA,
                                 identity_key='repair_sha256', identity_sha=record['repair_sha256'])
    results.append(result)
output = BASE / 'secondary_RAN3_RAN4_RAN5.jsonl'
output.write_text(''.join(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n' for record in results))
print(json.dumps({'path': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                  'rows': len(results), 'statuses': {s: sum(r['status'] == s for r in results) for s in ['pass', 'pending', 'blocked']}}, ensure_ascii=False))
