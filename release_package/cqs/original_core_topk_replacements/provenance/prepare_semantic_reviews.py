#!/usr/bin/env python3
"""Record separately derived semantic judgments for existing top-k replacements."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PREP = HERE.parents[1]
ROOT = HERE.parents[4]
ORIG = PREP / 'original_repair'
GX = ROOT / 'logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/gxmb-verification'
PUBLIC = ROOT.parent / 'spectra-public/spec-trace/release_package/cqs'
BASE = HERE / 'topk_replacements'
sys.path[:0] = [str(ORIG), str(PREP)]
import build
import review_schema


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


FINDINGS = {
 'RAN1_P1_CQ3-3': [
  'The requested answers are company identities. "Top 10 by TDoc count" specifies the selection metric, without separately asking to report counts or document IDs.',
  'Only contributions RELATED_TO the explicitly named NR_unlic-Core work item count. Keep the original SUBMITTED_BY direction and work-item predicate; no extra release or time filter.',
  'SUBMITTED_BY binds contributing company and RELATED_TO binds the named work item. The question asks contribution volume, not approval, adoption or causal success.',
  'One qualifying TDoc contribution is the count unit. The independent full SQL projection reproduces every company/count and COUNT(t) equals COUNT(DISTINCT t.node_id) for all groups, so this frozen graph has no path-count inflation.',
 ],
 'RAN1_P1_CQ3-6': [
  '"Top 10 Work Items" requests work-item identities. Contribution count determines their selection, not an additional reported answer field.',
  'Preserve the explicit companyName Nokia and original submission/work-item membership. No guessed technical-area ontology or company alias expansion is introduced.',
  'The parenthetical technical-area meaning is operationally anchored by the explicit Work Items and contribution count; RELATED_TO is not changed into a causal or ownership relation.',
  'Count qualifying Nokia TDoc nodes per workItemCode. The separate full SQL projection and DISTINCT-node counterfactual match all captured groups exactly.',
 ],
 'RAN1_P2_CQ4-3': [
  'Which companies handled the most FL summaries asks company identities selected by FL volume. The query-only count is a ranking witness, not a separately requested answer.',
  'Keep all frozen FL summaries, their original MODERATED_BY companies and no unstated meeting or release restriction.',
  'summaryType FL and MODERATED_BY provide the explicit summary handling role. Do not claim technical leadership causally measured beyond this documented role.',
  'Each qualifying summary TDoc is counted once for its company. COUNT(t) and DISTINCT-node counts are identical across every captured group in the separate SQL audit.',
 ],
 'RAN1_P4_CQ2-4': [
  'The question explicitly asks both ten CR identities and which specs each affects. Require cr.tdocNumber and the nested set affectedSpecs; do not require the unasked numeric ranking count.',
  'Every frozen CR remains eligible, including zero affected-spec CRs through OPTIONAL MATCH. No new primary-spec subtraction or release filter is added.',
  'The three original AFFECTS roles retain the frozen ontology role of the source Other specs affected field. They are declared cross-spec reach, not proof of normative enactment or independent causality.',
  'Count distinct logical specNumber values per CR, matching the requested affected-spec set. The independent SQL union of the three source relations reproduces all CR/count pairs; duplicate categories naming a spec do not inflate reach.',
 ],
 'RAN1_P5_CQ5-3': [
  'The requested output is five TR identities. Titles and numeric reference counts are supporting context, not asked output fields.',
  'Start from every TechnicalReport and OPTIONAL incoming REFERENCES_TR sources, including reports with zero references. No unasked work-item, release or time filter.',
  'Most-referenced means incoming REFERENCES_TR toward each target report. Preserve source-to-target direction; foundational studies is motivation rather than a measured novelty or causal outcome.',
  'Count distinct source trNumber identities referencing each target trNumber. The frozen SQL reconstruction matches the full target/count pool, avoiding node- or edition-duplication of logical reports.',
 ],
 'RAN2_P2_CQ1-8': [
  'The requested objects are agenda-item instances. agendaNumber together with meetingNumber identifies those instances across meetings; counts determine top-ten selection but are not separately requested.',
  'The original all-meeting population remains. The original UNKNOWN sentinel exclusion adds no hidden positive candidate loss: the complete frozen SQL agenda pool has no UNKNOWN agenda with a resolution; zero-count agendas cannot reach the positive cutoff.',
  'RESOLUTION_BELONGS_TO links resolutions to their agenda items. Hot-topic ranking is volume over this explicit relation, not scientific importance or causality.',
  'Count Resolution nodes per agendaNumber/meetingNumber. A separate full SQL projection equals native counts, and DISTINCT-node counts match every group, so same textual identities do not produce path-count inflation here.',
 ],
 'RAN2_P3_CQ1-15': [
  'Top 5 sections by table count requests Section identities. The sectionId preserves spec, edition and clause context; table counts are ranking evidence only.',
  'No spec or release is named, so keep the original all-Section source scope. The uncapped native covers every positive-table group; the independent OPTIONAL full-Section source pool includes zeros and proves none can reach the positive boundary.',
  'CONTAINS_TABLE uses Section as owner and TSTable as contained object. Do not replace it with title parsing or infer tables from textual mentions.',
  'Count contained TSTable nodes per Section identity. The separate SQL full pool agrees with native output and DISTINCT-node counts, proving no relation multiplicity inflation in this snapshot.',
 ],
 'RAN2_P3_CQ1-16': [
  'Top 5 sections by figure count requests Section identities, not separately reported figure count or captions. Keep sectionId as the requested clause identity.',
  'The original graph-wide Section scope is unchanged. The separate OPTIONAL full-Section witness includes zero-figure sections and confirms their scores are below the positive boundary.',
  'CONTAINS_FIGURE points from Section to TSFigure and supplies the explicit contained-object role. No guessed text or caption predicate is introduced.',
  'Count contained TSFigure nodes per Section identity. Separate SQL full-pool reconstruction and DISTINCT-node counts agree for every positive group.',
 ],
 'RAN2_P3_CQ2-8': [
  'The requested five most-referenced sections are identified by sectionId. Titles and refCount are auxiliary context, not required answer fields.',
  'The phrase within spec 38.331 and internal hubs restricts both source and target sections to the same original Spec node. Preserve this declared scope rather than mixing different specifications or silently choosing a latest edition.',
  'REFERENCES_SECTION is directed source Section to target Section. Rank the target by incoming internal references; do not rank the outgoing source.',
  'Count eligible internal reference relationships. Independent SQL count(*) equals DISTINCT reference-edge count for every target, excluding join multiplicity through belongs-to paths.',
 ],
 'RAN5_P1_CQ1-4': [
  'Which five meetings requests meeting identities. canonicalMeetingNumber distinguishes physical/e-meetings; TDoc count is a selection key, not an unasked required number.',
  'Start from every frozen Meeting and OPTIONAL PRESENTED_AT TDoc, retaining zero-document meetings. No timeframe or release restriction is invented.',
  'PRESENTED_AT supplies the explicit document-hosting relation toward Meeting. Activity ranking is this volume, not technical influence or adoption.',
  'Count DISTINCT Tdoc nodes for each canonical meeting identity. Independent SQL reconstructs every full-pool meeting/count pair exactly and all requested identities are non-null.',
 ],
}


def main():
    BASE.mkdir(exist_ok=True)
    criteria_sha = sha(ORIG / 'criteria.json')
    units = json.loads((ORIG / 'criteria.json').read_text())['semantic_units']
    originals = {x['id']: x for x in map(json.loads, (PUBLIC / 'spectra_cq_v2.0/benchmark.jsonl').read_text().splitlines())}
    published = {x['id']: x for x in map(json.loads, (PUBLIC / 'original_core_repair/tasks.jsonl').read_text().splitlines())}
    candidates = [json.loads(line) for line in (GX / 'correction_candidate/candidate_contracts.jsonl').read_text().splitlines()]
    audit_path = BASE / 'source_native_audit.json'
    audits = {x['id']: x for x in json.loads(audit_path.read_text())['items']}
    definition_keys = ['id', 'question_en', 'original_query', 'reference_query', 'required_fields', 'collection',
                       'cardinality_policy', 'repair_class', 'original_question_preserved']
    records = []
    for candidate in candidates:
        identifier = candidate['id']
        definition = {key: candidate[key] for key in definition_keys}
        identity = build.digest(definition)
        original = originals[identifier]
        assert identity == candidate['repair_sha256']
        assert definition['question_en'] == original['question_en'] and definition['original_query'] == original['cypher']
        assert definition['required_fields'] == published[identifier]['required_fields']
        assert definition['collection']['kind'] == 'top_k_boundary_ties'
        assert definition['collection']['require_rank_order'] is False
        audit = audits[identifier]
        assert audit['independent_sql_all_pool_exact'] and audit['count_multiplicity_difference_n'] == 0
        assert audit['null_requested_identity_n'] == 0 and audit['retained_n'] >= audit['explicit_k']
        k = definition['cardinality_policy']['value']
        findings = FINDINGS[identifier] + [
          f'The English explicitly asks {k} answers. The retained uncapped query contains no terminal LIMIT, and all {audit["retained_n"]} captured rows are kept. The separate SQL projection verifies the full positive or zero-inclusive pool. Zero-inclusive witnesses, where needed, prove omitted zeros cannot reach the positive boundary {audit["positive_boundary_value"]}. Accept all higher-scored members and any needed equal-boundary subset; fewer, extra, duplicate or lower-ranked answers cannot be exact.',
          'The original question asks for a top-k selection rather than mandating output sequence or lexical tie-break. Descending numeric keys establish eligibility only. source_order_keys omit auxiliary lexical IDs/names, require_rank_order is false, and any eligible boundary subset and display order is permitted.',
          'This separate AI review uses the original English, exact query, field roles and an independent frozen-source SQL projection. The native receipt is preserved under the recorded __uncapped alias with exact query/row hashes and published graph source guards. It neither certifies complete archive extraction nor supplies a human/expert review or new model performance. Previously saved predictions may only be re-scored as a separately labelled diagnostic.'
        ]
        review = {'id': identifier, 'status': 'pass', 'repair_sha256': identity,
                  'criteria_sha256': criteria_sha,
                  'original_question_sha256': hashlib.sha256(original['question_en'].encode()).hexdigest(),
                  'reviewer_kind': 'New primary AI original-question-derived replacement review; not human/expert validation or blind review',
                  'human_author_review_completed': False, 'expert_validation_n': 0,
                  'semantic_evidence': [{'unit': unit, 'status': 'pass', 'original_quote': original['question_en'],
                                         'query_clauses': definition['reference_query'].splitlines(), 'finding': finding}
                                        for unit, finding in zip(units, findings)]}
        review_schema.check_pass(review, original['question_en'], units, criteria_sha=criteria_sha,
                                 identity_key='repair_sha256', identity_sha=identity)
        record = dict(definition, repair_sha256=identity, criteria_sha256=criteria_sha,
                      original_question_sha256=review['original_question_sha256'],
                      original_query_sha256=hashlib.sha256(original['cypher'].encode()).hexdigest(),
                      reference_query_sha256=hashlib.sha256(definition['reference_query'].encode()).hexdigest(),
                      primary_review=review, replaces_public371_repair_sha256=published[identifier]['repair_sha256'],
                      new_unique_core_id=False, admitted=False, source_native_audit=audit,
                      source_native_audit_sha256=sha(audit_path),
                      repair_reason='Replace capped within-pool ties with uncapped boundary-subset selection; preserve original English and requested field definitions. No old AI semantic pass is inherited.')
        records.append(record)
    assert len(records) == len(FINDINGS) == 10
    out = BASE / 'candidates.jsonl'
    out.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in records))
    report = {'status': 'PREPARED_NOT_ADMITTED', 'primary_separate_AI_pass_n': 10, 'unique_added_id_n': 0,
              'source_native_audit_sha256': sha(audit_path), 'candidates_sha256': sha(out),
              'criteria_sha256': criteria_sha, 'new_neo4j_calls': 0, 'new_model_calls': 0,
              'required_before_admission': 'Exact-definition separate second semantic review and independent replacement-package verifier. Preserve prior contracts and scientific results.'}
    (BASE / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
