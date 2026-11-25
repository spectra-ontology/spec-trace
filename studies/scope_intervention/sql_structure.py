#!/usr/bin/env python3
"""Describe every admitted main/extension reference SQL without executing queries."""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / 'AGENTS.md').exists())
PACKAGE = ROOT / 'logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/release_preparation/vldb_release'
SOURCE = PACKAGE / 'code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_relational_equivalence.py'
spec = importlib.util.spec_from_file_location('released_relational', SOURCE)
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)
TOKEN = re.compile(r"--[^\n]*|/\*.*?\*/|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|[A-Za-z_][A-Za-z_0-9]*|[()]|\S", re.S)


def shape(sql):
    tokens = [t.upper() for t in TOKEN.findall(sql) if not t.startswith(('--', '/*', "'", '"'))]
    cte_definitions = 0
    if tokens and tokens[0] == 'WITH':
        cursor = 2 if tokens[1] == 'RECURSIVE' else 1
        while True:
            cte_definitions += 1
            cursor += 1
            if tokens[cursor] == '(':
                depth = 1
                cursor += 1
                while depth:
                    depth += (tokens[cursor] == '(') - (tokens[cursor] == ')')
                    cursor += 1
            assert tokens[cursor:cursor + 2] == ['AS', '(']
            cursor += 2
            depth = 1
            while depth:
                depth += (tokens[cursor] == '(') - (tokens[cursor] == ')')
                cursor += 1
            if tokens[cursor] != ',':
                break
            cursor += 1
    scopes = [None]
    blocks = []
    max_depth = 0
    for token in tokens:
        if token == '(':
            scopes.append(None)
        elif token == ')':
            assert len(scopes) > 1
            scopes.pop()
        elif token == 'SELECT':
            depth = 1 + sum(block is not None for block in scopes[:-1])
            max_depth = max(max_depth, depth)
            block = {'joins': 0, 'selectNesting': depth}
            blocks.append(block)
            scopes[-1] = block
        elif token == 'JOIN':
            block = next(block for block in reversed(scopes) if block is not None)
            block['joins'] += 1
    assert len(scopes) == 1
    pairs = collections.Counter(zip(tokens, tokens[1:]))
    counts = collections.Counter(tokens)
    return {'joinKeywords': counts['JOIN'], 'selectBlocks': len(blocks),
            'maxJoinsPerSelectBlock': max((b['joins'] for b in blocks), default=0),
            'maxSelectNesting': max_depth, 'with': counts['WITH'], 'cteDefinitions': cte_definitions,
            'recursiveWith': pairs[('WITH', 'RECURSIVE')], 'exists': counts['EXISTS'],
            'notExists': pairs[('NOT', 'EXISTS')], 'except': counts['EXCEPT'],
            'intersect': counts['INTERSECT'], 'union': counts['UNION'],
            'groupBy': pairs[('GROUP', 'BY')], 'having': counts['HAVING'],
            'orderBy': pairs[('ORDER', 'BY')], 'limit': counts['LIMIT'],
            'aggregateCalls': sum(pairs[(name, '(')] for name in ['COUNT', 'SUM', 'MIN', 'MAX', 'AVG', 'TOTAL', 'GROUP_CONCAT']),
            'windowOver': counts['OVER'], 'selectBlockDetails': blocks}


def main():
    all_rows = []
    files = {}
    for workload, folder in [('main', 'benchmark/items_final'), ('extension', 'benchmark/headroom')]:
        for wg_group in ['core', 'ran5']:
            relative = f'{folder}/gate/{wg_group}/chain_items_admitted.jsonl'
            path = PACKAGE / relative
            files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
            for line in path.read_text().splitlines():
                item = json.loads(line)
                query = {**reference.SQL, **reference.CLAUSE_SET_SQL}[item['family']]
                for variant, names in reference.VARIANTS.items():
                    sql = query.format(**names)
                    all_rows.append({'workload': workload, 'id': item['id'], 'wg': item['wg'],
                        'family': item['family'], 'variant': variant,
                        'sql': sql, 'sqlSha256': hashlib.sha256(sql.encode()).hexdigest(), 'shape': shape(sql)})
    assert sum(row['workload'] == 'main' for row in all_rows) == 667 * 2
    assert sum(row['workload'] == 'extension' for row in all_rows) == 297 * 2
    output = HERE / 'sql_structure_items.jsonl'
    output.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in all_rows))
    summaries = {}
    metrics = [k for k in all_rows[0]['shape'] if k != 'selectBlockDetails']
    for workload in ['main', 'extension']:
        entries = [row for row in all_rows if row['workload'] == workload and row['variant'] == 'cr_side']
        families = {}
        for family in sorted({row['family'] for row in entries}):
            group = [row for row in entries if row['family'] == family]
            unique = {json.dumps(row['shape'], sort_keys=True) for row in group}
            assert len(unique) == 1
            families[family] = {'items': len(group), 'shape': group[0]['shape']}
        summaries[workload] = {'items': len(entries), 'families': families,
            'histograms': {metric: dict(sorted(collections.Counter(row['shape'][metric] for row in entries).items())) for metric in metrics}}
    report = {'method': 'Lexical SQL tokens outside strings/comments; JOIN keyword counts and SELECT-block containment, not optimizer plans or graph hops.',
              'referenceCodeSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'inputSha256': files,
              'variantsHaveEqualShapes': all(all_rows[i]['shape'] == all_rows[i+1]['shape'] for i in range(0, len(all_rows), 2)),
              'workloads': summaries, 'itemOutputSha256': hashlib.sha256(output.read_bytes()).hexdigest()}
    (HERE / 'sql_structure_summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summaries, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
