"""Opus Text-to-Cypher 실행 A–J 가 다섯 scope 계열에서 scope 열을 거르는 방식을 나눠 센다 (모델 호출 없음).

measure_scope_predicate.py 가 센 "scope 열을 참조하지 않는 질의" 의 나머지를 다음으로 나눈다.
1. 저장값(관계형 사본의 whole_target, 그래프 resolutionScope 의 document_disposition)을 글자 그대로 담은 질의
2. scope 참조 둘레(앞 200자, 뒤 260자)에 부정 연산(NOT · none · size(...) = 0)과 부분을 뜻하는 낱말(part 등)이 함께 있는 질의.
   scope 식에 별칭을 붙인 질의(... resolutionScope ... AS rs)는 그 별칭이 쓰인 자리의 둘레도 같은 방식으로 본다.
3. 그 밖

사용: python3 classify_opus_scope_filters.py <chain_eval 폴더> <items jsonl...> --out <json>
"""
import argparse
import collections
import glob
import hashlib
import json
import pathlib
import re

ap = argparse.ArgumentParser()
ap.add_argument('chain_eval')
ap.add_argument('items', nargs='+')
ap.add_argument('--out', required=True)
a = ap.parse_args()

items = {i['id']: i for p in a.items for i in map(json.loads, open(p))}
FAM = {'clause_history', 'disposition_pack', 'full_chain', 'pack_origin', 'revision_chain'}
REF = re.compile(r'(?i)(resolution_?scope|\b\w+\.scope\b)')
STORED = ('whole_target', 'document_disposition')
NEG = re.compile(r'(?i)\bNOT\b|\bnone\s*\(|size\s*\([^\n]{0,400}\)\s*=\s*0')
PART = re.compile(r'(?i)part|proposal|subset|portion|section|clause')
ALIAS = re.compile(r"(?i)(?:resolution_?scope|\b\w+\.scope\b)(?:\s*,\s*'[^']*')?[\s)]*\bAS\s+(\w+)")

count = collections.Counter()
other = []
for f in sorted(glob.glob(f'{a.chain_eval}/RAN*_text2cypher_claude_subagent_run[A-J].jsonl')):
    for r in map(json.loads, open(f)):
        if r['family'] not in FAM or r['id'] not in items:
            continue
        if r.get('questionSha256') != hashlib.sha256(items[r['id']]['question'].encode()).hexdigest():
            continue
        q = r['attempts'][0].get('cypher') or ''
        count['queries'] += 1
        named = [v for v in STORED if v in q]
        count['namingStoredValue'] += bool(named)
        refs = [m for m in REF.finditer(q)]
        if not refs:
            count['noScopeReference'] += 1
            continue
        count['scopeReferenced'] += 1
        spans = [(m.start(), m.end()) for m in refs]
        for name in {m.group(1) for m in ALIAS.finditer(q)}:
            spans += [(m.start(), m.end()) for m in re.finditer(rf'\b{re.escape(name)}\b', q)]
        windows = [q[max(0, s - 200):e + 260] for s, e in spans]
        if any(NEG.search(w) and PART.search(w) for w in windows):
            count['excludingPartLikeSpellings'] += 1
        else:
            count['other'] += 1
            if len(other) < 5:
                other.append({'file': pathlib.Path(f).name, 'id': r['id'], 'window': re.sub(r'\s+', ' ', windows[0])})
res = {**{k: count[k] for k in ('queries', 'noScopeReference', 'scopeReferenced', 'namingStoredValue',
                                'excludingPartLikeSpellings', 'other')},
       'storedValues': list(STORED), 'otherSamples': other}
json.dump(res, open(a.out, 'w'), indent=1)
print({k: v for k, v in res.items() if k != 'otherSamples'})
