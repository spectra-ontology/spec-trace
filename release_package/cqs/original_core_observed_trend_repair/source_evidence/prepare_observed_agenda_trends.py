"""Two original graph-observed count-trend candidates; no admission/model/native calls."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ORIG = HERE.parents[2] / 'original_repair'
PUB = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs')
sys.path.insert(0, str(ORIG))
import build
import review_schema


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def text_sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def main():
    out = HERE / 'observed_agenda_trend_candidates'
    out.mkdir(exist_ok=True)
    criteria = json.loads((ORIG / 'criteria.json').read_text())
    criteria_sha = sha(ORIG / 'criteria.json')
    original = {r['id']: r for r in (json.loads(line) for line in (PUB / 'spectra_cq_v2.0/benchmark.jsonl').read_text().splitlines())}
    probe_path = HERE / 'trend_scope_source_probe.json'
    probe = json.loads(probe_path.read_text())
    records = []
    for wg, id_, agenda in [('RAN3', 'RAN3_P2_CQ6-1', '8.1'), ('RAN4', 'RAN4_P2_CQ6-1', '6.6.3')]:
        item = original[id_]
        query = f"""MATCH (m:Meeting)
OPTIONAL MATCH (r:Resolution)-[:MADE_AT]->(m)
WHERE EXISTS {{ MATCH (r)-[:RESOLUTION_BELONGS_TO]->(:AgendaItem {{agendaNumber: '{agenda}'}}) }}
WITH m, count(DISTINCT r) AS resolutionCount
RETURN m.canonicalMeetingNumber AS meetingNumber, m.meetingNumberInt AS meetingOrdinal, resolutionCount
ORDER BY meetingOrdinal ASC"""
        source = probe[wg]
        meetings = source['whole_meetings']
        counts = source['counts_by_exactAgenda_resolution_MADE_AT']
        assert len(meetings) == len(counts) == 58
        assert {m['canonicalMeetingNumber'] for m in meetings} == {r['canonicalMeetingNumber'] for r in counts}
        assert all(m['meetingNumberInt'] is not None for m in meetings)
        direct = {m['canonicalMeetingNumber']: set() for m in meetings}
        for row in source['resolution_agenda_MADE_AT_pairs']:
            assert row['agendaNumber'] == agenda
            direct[row['canonicalMeetingNumber']].add(row['resolutionNode'])
        assert all(len(direct[row['canonicalMeetingNumber']]) == row['resolutionCount'] for row in counts)
        definition = {'id': id_, 'question_en': item['question_en'], 'original_query': item['cypher'],
                      'reference_query': query,
                      'required_fields': [
                          {'name': 'meetingNumber', 'type': 'string', 'nullable': False, 'source_column_or_expression': 'meetingNumber'},
                          {'name': 'resolutionCount', 'type': 'integer', 'nullable': False, 'source_column_or_expression': 'resolutionCount'}],
                      'collection': {'kind': 'native_ordered_ties', 'source_order_keys': [{'source_column': 'meetingOrdinal', 'direction': 'asc'}], 'tie_policy': 'any_order_within_equal_keys'},
                      'cardinality_policy': {'mode': 'all'}, 'repair_class': 'query_and_scorer', 'original_question_preserved': True}
        digest = build.digest(definition)
        findings = [
            f'The original asks a resolution-count trend for agenda item{agenda}; each requested observation is a meeting identity and its resolution count. Require only meetingNumber and integer resolutionCount. meetingOrdinal is an auxiliary ordering coordinate, not an extra required answer field.',
            f'Fixed criteria explicitly preserve originalWG/phase and graph-relative source context. All58 Meeting nodes of the designated{wg} fixture form the recorded observation universe; this is not a chosen external date interval, all meetings ever held, or a claim of complete real-world meeting coverage.',
            f'The literal agendaNumber={agenda} is the original selector. Use actual Resolution.RESOLUTION_BELONGS_TO and Resolution.MADE_AT edges, not an inferred Agenda.meetingNumber suffix. Do not include descendants or require constant topic descriptions. The original asks the numbered agenda item, while changing descriptions are retained as a limitation rather than an invented topic filter.',
            'The unit is a distinct qualifying Resolution entity at a source-recorded Meeting. OPTIONAL MATCH and COUNT(DISTINCT r) include exactly one count per Meeting without join-product inflation; EXISTS tests agenda membership without multiplying by multiple agenda edges. Captured full source relation tuples independently reconstruct every count.',
            'Every58 captured Meeting is included. A zero means no qualifying Resolution edge observed in this frozen fixture, not proof of an inactive meeting or complete real-world zero. No hidden LIMIT or positive-only filter is retained; all source-known meetings and zeros remain in the answer.',
            'Over time is represented on the source Meeting.meetingNumberInt ordinal axis that the original query used. All source ordinals are nonnull. Base/bis meetings may share the ordinal; no calendar date or sub-order is inferred. Keep count observations in ascending source ordinal and allow any order within equal keys, with canonical meeting identities preserving separate observations.',
            'Exact original English, original query and fixed criteria are pinned. No source completeness outside the supplied WG fixture, causal topic-activity interpretation, new date anchor or reviewer-authored scope choice is claimed. Earlier pending diagnostics remain preserved; this followup reassesses whether a pure recorded count needs world-inactivity or stable-topic assumptions. Root secondary may reject the coarse ordinal/source-observation interpretation; native/scorer/model gates are still incomplete.'
        ]
        review = {'id': id_, 'status': 'pass', 'repair_sha256': digest, 'criteria_sha256': criteria_sha,
                  'original_question_sha256': text_sha(item['question_en']),
                  'reviewer': 'Separate primary AI original-question/graph-context source review /root/dqqc_final_perspective',
                  'blind_review': False, 'human_expert_validation_n': 0,
                  'semantic_evidence': [{'unit': unit, 'status': 'pass', 'original_quote': item['question_en'],
                                         'query_clauses': query.splitlines(), 'finding': finding,
                                         'source_witness_path': str(probe_path), 'source_witness_sha256': sha(probe_path)}
                                        for unit, finding in zip(criteria['semantic_units'], findings)]}
        review_schema.check_pass(review, item['question_en'], criteria['semantic_units'], criteria_sha=criteria_sha,
                                 identity_key='repair_sha256', identity_sha=digest)
        witness = {'id': id_, 'working_group': wg, 'agendaNumber': agenda,
                   'source_sqlite_sha256': source['sqlite_sha256'], 'whole_meeting_n': 58,
                   'all_native_semantic_counts_independently_reconstructed': True,
                   'zero_observation_n': sum(row['resolutionCount'] == 0 for row in counts),
                   'resolution_count_sum': sum(row['resolutionCount'] for row in counts),
                   'all_source_count_records': counts,
                   'source_probe': {'path': str(probe_path), 'sha256': sha(probe_path)},
                   'scope': 'Graph-recorded association counts and source ordinal; no real-world inactivity or complete raw-archive chronology certified.'}
        witness_path = out / (id_ + '_source_witness.json')
        witness_path.write_text(json.dumps(witness, ensure_ascii=False, indent=2) + '\n')
        records.append({**definition, 'repair_sha256': digest, 'criteria_sha256': criteria_sha,
                        'original_question_sha256': text_sha(item['question_en']), 'original_query_sha256': text_sha(item['cypher']),
                        'reference_query_sha256': text_sha(query), 'primary_review': review,
                        'source_witness': {'path': str(witness_path), 'sha256': sha(witness_path)},
                        'source_context': {'graph_source_sha256': sha(Path('/home/sihyeon/workspace/spectra/release_package/kg/per_wg') / (wg + '-body.ttl')),
                                           'original_fixture': wg, 'time_axis': 'source meeting ordinal, not exact calendar chronology'},
                        'repair_reason': 'Original observed Resolution-count series: all source Meetings, exact numbered agenda, actual MADE_AT, DISTINCT Resolution, no hidden cap or query-time source scope invention.',
                        'admitted': False, 'native_execution_completed': False, 'scorer_controls_completed': False,
                        'new_model_calls': 0, 'human_expert_validation_n': 0})
    path = out / 'proposals.jsonl'
    path.write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in records))
    (out / 'definition_only.jsonl').write_text(''.join(json.dumps({key: r[key] for key in ['id', 'question_en', 'original_query', 'reference_query', 'required_fields', 'collection', 'cardinality_policy', 'repair_class', 'original_question_preserved']}, ensure_ascii=False, sort_keys=True) + '\n' for r in records))
    print(json.dumps({'path': str(path), 'sha256': sha(path), 'candidate_n': len(records),
                      'ids': [r['id'] for r in records], 'native_or_admission_completed': False}, indent=2))


if __name__ == '__main__':
    main()
