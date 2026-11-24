"""RQ6 헤드룸 분할의 저장된 응답 행을 score_chain_eval.score 로 다시 채점해 요약 파일의 정확 수와 견준다 (모델 호출 없음).

분석 스크립트(analyze_headroom.py)를 거치지 않고, 요약 파일이 가리키는 응답 파일과 채택 문항만 읽는다.
문항은 id 로 맞추고, 응답의 rows 가 없으면 0 점으로 분모에 남긴다(요약 파일의 규칙과 같다).

사용: python3 recompute_headroom_scores.py <summary_with_opus.json> <items jsonl...> --score-module <score_chain_eval.py> --out <json>
"""
import argparse
import json
import pathlib
import sys

ap = argparse.ArgumentParser()
ap.add_argument('summary')
ap.add_argument('items', nargs='+')
ap.add_argument('--score-module', required=True)
ap.add_argument('--out', required=True)
a = ap.parse_args()
sys.path.insert(0, str(pathlib.Path(a.score_module).resolve().parent))
from score_chain_eval import score  # noqa: E402

items = {i['id']: i for p in a.items for i in map(json.loads, open(p))}
summary = json.load(open(a.summary))
out = []
for m in summary['methods']:
    for r in m['runs']:
        seen, exact, unknown = set(), 0, 0
        for f in r['files']:
            for rec in map(json.loads, open(f)):
                if rec['id'] not in items:
                    unknown += 1
                    continue
                seen.add(rec['id'])
                rows = rec.get('rows')
                exact += score(items[rec['id']]['gold'], rows)['exact'] if rows is not None else 0
        stored = r['recorded']['all']['exact']
        out.append({'method': m['name'], 'run': r['run'], 'records': len(seen), 'unknownIds': unknown,
                    'recomputedExact': exact, 'summaryExact': stored, 'same': exact == stored})
json.dump({'items': len(items), 'runs': out, 'allSame': all(x['same'] for x in out)}, open(a.out, 'w'), indent=1)
for x in out:
    print(x)
print('allSame', all(x['same'] for x in out))
