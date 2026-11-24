"""스키마만 받은 질의 작성 에이전트(Claude Opus 실행 A–J, Codex)가 scope 열을 어떻게 다루는지 세고, 다섯 scope 계열의 정답 수와 함께 적는다 (모델 호출 없음).

세는 것:
1. 다섯 계열(clause_history · disposition_pack · full_chain · pack_origin · revision_chain)의 질의 수와 정답 수
2. 저장값 whole_target 을 글자 그대로 담은 질의 수
3. scope 열을 전혀 참조하지 않는 질의 수
4. 세션(작업반 × 실행)별 정답 수, 그리고 절반 미만인 세션과 그 세션이 쓴 scope 조건 한 개

사용: python3 measure_scope_predicate.py <chain_eval 폴더> <items jsonl...> --score-module <score_chain_eval.py> --out <json>
"""
import argparse
import collections
import glob
import hashlib
import json
import pathlib
import re
import sys

ap = argparse.ArgumentParser()
ap.add_argument('chain_eval')
ap.add_argument('items', nargs='+')
ap.add_argument('--score-module', required=True)
ap.add_argument('--out', required=True)
a = ap.parse_args()
sys.path.insert(0, str(pathlib.Path(a.score_module).resolve().parent))
from score_chain_eval import score  # noqa: E402

items = {i['id']: i for p in a.items for i in map(json.loads, open(p))}
FAM = {'clause_history', 'disposition_pack', 'full_chain', 'pack_origin', 'revision_chain'}
REF = re.compile(r'(?i)(resolution_?scope|\b\w+\.scope\b)')
CONF = {'opus_text2cypher': 'RAN*_text2cypher_claude_subagent_run[A-J].jsonl',
        'opus_text2sql': 'text2sql/RAN*_text2sql_run[A-J].jsonl',
        'codex_cypher_schema': 'codex/chain_cy_RAN*_codex.jsonl',
        'codex_sql_schema': 'codex/chain_sql_RAN*_codex.jsonl'}


def query_of(record):
    x = record['attempts']
    if isinstance(x, list):
        return (x[0].get('cypher') or x[0].get('sql') or '') if x else ''
    m = re.search(r"'(?:cypher|sql)': \"(.*?)\", 'rowCount'", x, re.S) or re.search(r"'(?:cypher|sql)': '(.*?)', 'rowCount'", x, re.S)
    return m.group(1) if m else x


res = {}
for name, pat in CONF.items():
    total = exact = stored = unref = 0
    sessions = []
    for f in sorted(glob.glob(f'{a.chain_eval}/{pat}')):
        n = e = 0
        sample = None
        for r in map(json.loads, open(f)):
            if r['family'] not in FAM or r['id'] not in items:
                continue
            item = items[r['id']]
            if r.get('questionSha256') != hashlib.sha256(item['question'].encode()).hexdigest():
                continue
            q = query_of(r)
            n += 1
            e += score(item['gold'], r.get('rows'))['exact']
            stored += 'whole_target' in q
            refs = [m.start() for m in REF.finditer(q)]
            unref += not refs
            if refs and sample is None and r['family'] == 'disposition_pack':
                sample = q[refs[0]:refs[0] + 260]
        total += n
        exact += e
        sessions.append({'file': pathlib.Path(f).name, 'queries': n, 'exact': e, 'scopePredicateSample': sample})
    res[name] = {'queries': total, 'exact': exact, 'containWholeTarget': stored, 'noScopeReference': unref,
                 'sessions': len(sessions), 'sessionsBelowHalf': [s for s in sessions if s['exact'] < 0.5 * s['queries']]}
json.dump(res, open(a.out, 'w'), indent=1)
for k, v in res.items():
    print(k, {x: y for x, y in v.items() if x != 'sessionsBelowHalf'}, [(s['file'], s['exact'], s['queries']) for s in v['sessionsBelowHalf']])
