"""Independently rescore all stored native rows and construct paired contrasts.

Uses the previously released standard-library scorer, including the original
meeting identity rule. No model calls, database calls, or generated-query edits.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE / 'frozen' if (HERE / 'frozen' / 'schedule.json').is_file() else HERE

def load(p):
    return json.loads(p.read_text())

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def summarize_pairs(pairs):
    differences = [pair['exactDifference'] for pair in pairs]
    return {
        'pairs': len(pairs),
        'pairedQuestionSlots': sum(pair['n'] for pair in pairs),
        'pairsImproved': sum(delta > 0 for delta in differences),
        'pairsTied': sum(delta == 0 for delta in differences),
        'pairsDeclined': sum(delta < 0 for delta in differences),
        'netExactDifference': sum(differences),
    }


def summarize_contrast_scopes(contrasts):
    by_kind = collections.defaultdict(list)
    for contrast in contrasts:
        if contrast['suite'] == 'all':
            by_kind[contrast['kind']].append(contrast)
    return {
        kind: {
            'allPlanned': summarize_pairs(pairs),
            'primaryCompleteInput': summarize_pairs(
                [pair for pair in pairs if pair['completeInputPair']]),
            'outputAssemblyConformantSensitivity': summarize_pairs(
                [pair for pair in pairs if pair['eligibleControlledContrast']]),
        }
        for kind, pairs in by_kind.items()
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    lock = load(SPEC / 'protocol_lock.json')
    for name, expected in lock['files'].items():
        assert sha(SPEC / name) == expected, 'Frozen protocol/input changed: '+name
    if (HERE / 'SHA256SUMS').is_file():
        for line in (HERE / 'SHA256SUMS').read_text().splitlines():
            expected, name = line.split('  ', 1)
            target = (HERE / name).resolve()
            assert target.is_relative_to(HERE.resolve())
            assert sha(target) == expected, 'Study checksum differs: '+name
    base = HERE.parent / 'matched_domains'
    if not base.is_dir():
        root = next(p for p in HERE.parents if (p / 'CLAUDE.md').is_file())
        base = root / 'logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/release_preparation/vldb_release/studies/matched_domains'
    spec = importlib.util.spec_from_file_location('released_standard_scorer', base / 'rescore.py')
    scorer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scorer)
    gold = load(base / 'gold/selected_items.json')
    by_packet = {scorer.packet_id(i): i for i in gold}
    assert len(by_packet) == 50
    kept = set(load(base / 'evidence/meeting_identity_source.json')['rules']['keptElectronicSpellings'])
    exposure = {r['runId']: r for r in load(HERE / 'input_exposure_audit.json')['runs']}
    deviations = {r['runId']: r for r in load(HERE / 'first_write_deviations.json')['runs']}
    schedule = load(SPEC / 'schedule.json')
    assert len(schedule) == len(exposure) == 32
    summaries, rows_by_run = {}, {}
    for run in schedule:
        rid = run['runId']
        directory = HERE / 'submissions' / rid
        commitment = load(directory / 'commitment.json')
        assert sha(directory / 'response.raw') == commitment['rawSha256']
        missing = commitment['status'] == 'invalid_first_submission' or rid in deviations
        order = load(SPEC / 'cohort_manifest.json')['packetOrder']
        if missing:
            if rid in deviations:
                d = deviations[rid]
                assert sha(HERE / d['firstWritePath']) == d['firstWriteSha256']
                assert d['firstWriteJsonValid'] is False
                try:
                    load(HERE / d['firstWritePath'])
                except json.JSONDecodeError:
                    pass
                else:
                    raise AssertionError('Recovered first batch was expected to be malformed')
            else:
                assert load(directory / 'response.raw') == {'queries': []}
            assert not (HERE / 'execution' / rid).exists()
            queries = [{'id': pid, 'query': None} for pid in order]
            executions = []
            for pid in order:
                item = by_packet[pid]
                zero = scorer.score(item['gold'], None)
                executions.append(dict({k: item[k] for k in ['id','wg','family','suite']},
                    packetId=pid, query=None, rows=None, error='MISSING_FIRST_QUERY', blocked=False,
                    scores=zero, identityScores=zero, status='unanswered_not_executed'))
        else:
            assert commitment['status'] == 'complete'
            qpath = directory / commitment['queryFile']
            assert sha(qpath) == commitment['querySha256']
            queries = scorer.jsonl(qpath)
            executions = load(HERE / 'execution' / rid / 'scoring_only' / (run['language'] + '_' + run['repetition'] + '.json'))
        assert [q['id'] for q in queries] == [r['packetId'] for r in executions] == order
        strict = 0
        for query, row in zip(queries, executions):
            item = by_packet[row['packetId']]
            assert row['query'] == query['query']
            assert all(row[k] == item[k] for k in ['id', 'wg', 'family', 'suite'])
            assert scorer.score(item['gold'], row['rows']) == row['scores']
            expected = scorer.score(scorer.identity_rows(item, item['gold'], kept), scorer.identity_rows(item, row['rows'], kept))
            assert expected == row['identityScores']
            strict += int(row['rows'] is not None and scorer.raw_set(item['gold']) == scorer.raw_set(row['rows']))
        s = {suite: scorer.summarize([r['identityScores'] for r in executions if suite == 'all' or r['suite'] == suite]) for suite in ['all', 'main', 'extension']}
        recorded = {suite: scorer.summarize([r['scores'] for r in executions if suite == 'all' or r['suite'] == suite]) for suite in ['all', 'main', 'extension']}
        if not missing:
            stored = load(HERE / 'execution' / rid / 'summary.json')['runs'][run['language'] + '_' + run['repetition']]
            assert s == stored['identity']
            assert all(recorded[k] == stored[k] for k in recorded)
        summaries[rid] = dict(run, identity=s, recorded=recorded, strictRawExact=strict,
            nativeQueriesExecuted=0 if missing else 50, missingFirstQueries=50 if missing else 0,
            blocked=sum(r['blocked'] for r in executions), executionErrors=0 if missing else sum(r['error'] is not None for r in executions),
            completeInput=exposure[rid]['allItemsAndSchemaLinesObserved'],
            outputAssemblyViolation=rid in deviations,
            distinctQueryTexts=len(set(q['query'] for q in queries)) if not missing else 0,
            families={f: scorer.summarize([r['identityScores'] for r in executions if r['family'] == f]) for f in sorted({r['family'] for r in executions})})
        rows_by_run[rid] = executions
    contrasts = []
    def contrast(left, right, kind):
        a, b = rows_by_run[left], rows_by_run[right]
        left_run, right_run = summaries[left], summaries[right]
        complete_input = left_run['completeInput'] and right_run['completeInput']
        valid_assembly = not (left_run['outputAssemblyViolation'] or right_run['outputAssemblyViolation'])
        for suite in ['all', 'main', 'extension']:
            pairs = [(x, y) for x, y in zip(a, b) if suite == 'all' or x['suite'] == suite]
            gains = sum(not x['identityScores']['exact'] and y['identityScores']['exact'] for x, y in pairs)
            losses = sum(x['identityScores']['exact'] and not y['identityScores']['exact'] for x, y in pairs)
            contrasts.append({'kind': kind, 'left': left, 'right': right, 'suite': suite, 'n': len(pairs),
                'completeInputPair': complete_input,
                'eligibleControlledContrast': complete_input and valid_assembly,
                'exactGains': gains, 'exactLosses': losses, 'exactDifference': gains-losses,
                'macroF1Difference': sum(y['identityScores']['f1']-x['identityScores']['f1'] for x, y in pairs)/len(pairs)})
    for model in load(SPEC / 'protocol.json')['requestedModels']:
        for repetition in ['A', 'B']:
            for lang in ['sql', 'cypher']:
                contrast(f'{model}__schema_only__{lang}_{repetition}', f'{model}__schema_domains__{lang}_{repetition}', 'categorical_domains_minus_schema')
            for condition in ['schema_only', 'schema_domains']:
                contrast(f'{model}__{condition}__sql_{repetition}', f'{model}__{condition}__cypher_{repetition}', 'cypher_minus_sql')
    result = {'sessions': 32, 'plannedQueries': 1600,
        'nativeQueries': sum(s['nativeQueriesExecuted'] for s in summaries.values()),
        'missingFirstQueries': sum(s['missingFirstQueries'] for s in summaries.values()), 'distinctQuestions': 50,
        'dependencies': {name: sha(base / name) for name in ['rescore.py', 'gold/selected_items.json', 'evidence/meeting_identity_source.json']},
        'completeInputSessions': sum(s['completeInput'] for s in summaries.values()),
        'inputDeviationSessions': [k for k,v in summaries.items() if not v['completeInput']],
        'outputAssemblyDeviationSessions': list(deviations),
        'samplingInterpretation': 'Descriptive fixed35main/15extension cohort; repeated sessions add no independent questions.',
        'runs': summaries, 'pairedContrasts': contrasts,
        'pairedContrastScopes': summarize_contrast_scopes(contrasts)}
    output = HERE / 'analysis.json'
    if args.check:
        assert load(output) == result, 'Stored analysis differs from row-level recomputation'
    else:
        output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['sessions', 'nativeQueries', 'distinctQuestions', 'completeInputSessions', 'inputDeviationSessions']}))
    for model in load(SPEC / 'protocol.json')['requestedModels']:
        cells = []
        for lang in ['sql', 'cypher']:
            for condition in ['schema_only', 'schema_domains']:
                vals = [summaries[f'{model}__{condition}__{lang}_{r}'] for r in ['A','B']]
                cells.append('/'.join(str(v['identity']['all']['exact'])+('dagger' if not v['completeInput'] else '') for v in vals))
        print(model, cells)

if __name__ == '__main__':
    main()
