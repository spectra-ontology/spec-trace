"""Replay retained actual-population errors without model or database calls."""
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def verify(bundle):
    b = Path(bundle).resolve()
    sys.path.insert(0, str(b))
    import original_scorer
    tasks = {r['id']: r for r in map(json.loads, (b / 'tasks.jsonl').read_text().splitlines())}
    golds = {r['id']: r for r in map(json.loads, (b / 'reference_gold.jsonl').read_text().splitlines())}
    cases = json.loads((b / 'saved_actual_controls.json').read_text())
    assert {r['id'] for r in cases} == set(tasks)
    replayed = []
    for case in cases:
        task = tasks[case['id']]
        gold = golds[case['id']]
        assert case['repair_sha256'] == task['repair_sha256']
        for x in case['controls']:
            d = original_scorer.score(task, gold['records'], x['predictions'], diagnostic=True, order_groups=gold['order_groups'])
            v = original_scorer.score(dict(task, validation_status='validated'), gold['records'], x['predictions'], diagnostic=False, order_groups=gold['order_groups'])
            plain = lambda y: {k: z for k, z in y.items() if k != 'diagnostic_only'}
            assert plain(d) == plain(v) == plain(x['saved_score']), (case['id'], x['name'])
            assert d['exact'] is x['expected_exact'], (case['id'], x['name'])
            assert x['synthetic_source_free_fixture'] is False
            replayed.append({'id': case['id'], 'name': x['name'], 'pass': True})
    assert len(replayed) == 138
    return {'status': 'PASS', 'additional_saved_controls_n': len(replayed),
            'actual_population_control_replays_n': len(replayed), 'separate_synthetic_control_replays_n': 0,
            'diagnostic_and_validated_modes_equal': True, 'database_queries_n': 0, 'API_calls_n': 0,
            'checks': replayed,
            'limits': 'Actual source-population mutation replay only; retained historical synthetic checks are not counted here. Nonblind AI development verification, zero human or expert reviews.'}
