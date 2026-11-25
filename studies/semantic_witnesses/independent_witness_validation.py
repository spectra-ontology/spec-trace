"""Reconstruct every eligibility pool and gold from raw rows, without builder imports."""
import argparse
import collections
import gzip
import hashlib
import itertools
import json
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--study', type=Path, default=HERE / 'semantic_coverage')
parser.add_argument('--release', type=Path, default=Path('logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/release_preparation/vldb_release'))
parser.add_argument('--database-directory', type=Path, default=Path('/tmp/vldb-operator-study-databases'))
parser.add_argument('--output', type=Path, default=HERE / 'independent_witness_validation.json')
args = parser.parse_args()
STUDY = args.study
MEAS = STUDY / 'measurement'
loads = lambda p: json.loads(p.read_text())
canon = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
sha = lambda x: hashlib.sha256(x).hexdigest()
norm = lambda rows: sorted({tuple(str(x) if x is not None else '' for x in row) for row in rows})
protocol = loads(STUDY / 'protocol.json')
frozen = loads(MEAS / 'selection_and_gold.json')
stored = {x['id']: x for x in loads(MEAS / 'execution.json')['items']}
supplement = loads(STUDY / 'supplementary_omitted_controls.json') if (STUDY / 'supplementary_omitted_controls.json').exists() else {'items': []}
checks = []
started = time.monotonic()


def check(name, ok, **detail):
    checks.append({'check': name, 'ok': bool(ok), **detail})


for wg in protocol['working_groups']:
    path = args.database_directory / (wg + '.sqlite')
    if not path.exists():
        path = args.release / 'sqlite' / (wg + '.sqlite')
    if not path.exists():
        args.database_directory.mkdir(parents=True, exist_ok=True)
        path = args.database_directory / (wg + '.sqlite')
        with gzip.open(args.release / 'sqlite' / (wg + '.sqlite.gz'), 'rb') as source, path.open('xb') as target:
            while chunk := source.read(1024 * 1024):
                target.write(chunk)
    check(wg + ':database_pin', sha(path.read_bytes()) == next(p['database_sha256'] for p in frozen['inputs'] if p['wg'] == wg))
    con = sqlite3.connect(f'file:{path.resolve()}?mode=ro&immutable=1', uri=True)
    con.execute('PRAGMA query_only=ON')
    section = {i: (sp, rel, cl) for i, sp, rel, cl in con.execute('SELECT id,spec,release,clause FROM section')}
    links = collections.defaultdict(set)
    for d, s in con.execute('SELECT cr,section_id FROM cr_modifies_section'):
        links[d].add(section[s])
    members = collections.defaultdict(set)
    for d, p in con.execute('SELECT cr,pack_id FROM cr_in_pack'):
        members[p].add(d)
    res = dict(con.execute('SELECT id,meeting_id FROM resolution'))
    codes = collections.defaultdict(list)
    meeting_pairs = collections.defaultdict(list)
    for rid, doc, code in con.execute("SELECT resolution_id,target,code FROM disposition WHERE scope='whole_target' AND evidence_status='source_verified'"):
        codes[doc].append(code)
        if rid in res:
            meeting_pairs[res[rid]].append((doc, code))
    pools = collections.defaultdict(set)

    def add(key, identity):
        pools[key].add(canon(identity))

    def histogram(docs):
        groups = collections.defaultdict(set)
        for d in docs:
            for code in codes[d]:
                groups[code].add(d)
        return {c: len(ds) for c, ds in groups.items()}

    def reduce_release(values):
        return {(s, c) for s, r, c in values}

    for cohort, cohorts in [('pack', {p: [(d, c) for d in ds for c in codes[d]] for p, ds in members.items()}),
                            ('meeting', meeting_pairs)]:
        for name, pairs in cohorts.items():
            groups = collections.defaultdict(set)
            raw = collections.Counter()
            for d, c in pairs:
                groups[c].add(d)
                raw[c] += 1
            multi = len(groups) > 1
            duplicates = any(raw[c] > len(ds) for c, ds in groups.items())
            anchor = ['pack' if cohort == 'pack' else 'meeting', name]
            for suffix, yes in [('multicode', multi), ('duplicates', duplicates), ('multicode_duplicates', multi and duplicates)]:
                if yes:
                    add(cohort + '_' + suffix, anchor)
    for pack, docs in members.items():
        sizes = {d: len(links[d]) for d in docs}
        if any(sizes.values()) and 0 in sizes.values():
            add('absence', [pack])
        if len({n for n in sizes.values() if n > 0}) >= 2:
            add('maximum_variation', [pack])
            max_full = max(sizes.values())
            winners = {d for d, n in sizes.items() if n == max_full}
            if len(winners) >= 2:
                add('maximum_ties', [pack])
            collapsed = {d: len(reduce_release(links[d])) for d in docs}
            max_collapsed = max(collapsed.values())
            collapsed_winners = {d for d, n in collapsed.items() if n == max_collapsed}
            changed = {(d, max_full) for d in winners} != {(d, max_collapsed) for d in collapsed_winners}
            if changed:
                add('maximum_release_count', [pack])
                if len(winners) >= 2:
                    add('maximum_ties_release', [pack])
            if winners != collapsed_winners:
                add('maximum_release_winner', [pack])
        inv = collections.defaultdict(set)
        for d in docs:
            for s in links[d]:
                inv[s].add(d)
        doc_pairs = set()
        for ds in inv.values():
            doc_pairs.update(itertools.combinations(sorted(ds), 2))
        for a, b in doc_pairs:
            a_sections, b_sections = links[a], links[b]
            if not (a_sections & b_sections and a_sections - b_sections and b_sections - a_sections):
                continue
            add('intersection', [pack, a, b])
            if any((s, c) in reduce_release(b_sections) for s, r, c in a_sections - b_sections):
                add('intersection_release', [pack, a, b])
            for left, right in [(a, b), (b, a)]:
                add('difference', [pack, left, right])
                if any((s, c) in reduce_release(links[right]) for s, r, c in links[left] - links[right]):
                    add('difference_release', [pack, left, right])
        sec_pairs = set()
        for d in docs:
            sec_pairs.update(itertools.combinations(sorted(links[d]), 2))
        inv_blind = collections.defaultdict(set)
        for s, ds in inv.items():
            inv_blind[(s[0], s[2])].update(ds)
        for a, b in sec_pairs:
            da, db = inv[a], inv[b]
            both = da & db
            if not (both and da - db and db - da):
                continue
            anchor = [pack, list(a), list(b)]
            add('conjunction', anchor)
            blind_both = inv_blind[(a[0], a[2])] & inv_blind[(b[0], b[2])]
            if blind_both - both:
                add('conjunction_release', anchor)
            h = histogram(both)
            if h and h != histogram(da | db):
                add('composition', anchor)
    for cell in (x for x in frozen['cells'] if x['wg'] == wg):
        key = cell['stratum']
        raw = gzip.decompress((MEAS / cell['pool']).read_bytes())
        pool_rows = [json.loads(line) for line in raw.splitlines()]
        actual = {canon(x['candidate']) for x in pool_rows}
        check(wg + ':' + key + ':entire_eligible_pool', actual == pools[key] and len(pool_rows) == len(actual) == cell['eligible_candidates'], measured=len(actual), independent=len(pools[key]))
        check(wg + ':' + key + ':pool_hash', sha(raw) == cell['pool_uncompressed_sha256'] and sha((MEAS / cell['pool']).read_bytes()) == cell['pool_sha256'])
        if actual:
            selected = min((sha(canon([protocol['study'], wg, key, json.loads(a)]).encode()), a) for a in actual)
            check(wg + ':' + key + ':selection', selected[0] == cell['selection_sha256'] and selected[1] == canon(cell['selected']['candidate']))
    for item in (i for i in frozen['items'] if i['wg'] == wg):
        family, anchor = item['family'], item['anchor']
        if family == 'pack_disposition_counts':
            if anchor[0] == 'pack':
                h = histogram(members[anchor[1]])
            else:
                groups = collections.defaultdict(set)
                for d, c in meeting_pairs[anchor[1]]:
                    groups[c].add(d)
                h = {c: len(ds) for c, ds in groups.items()}
            gold = norm(h.items())
        elif family in ['shared_clauses', 'exclusive_clauses']:
            a, b = links[anchor[1]], links[anchor[2]]
            gold = norm(a & b if family == 'shared_clauses' else a - b)
        elif family in ['both_clause_documents', 'conjunction_disposition_counts']:
            a, b = tuple(anchor[1]), tuple(anchor[2])
            ds = {d for d in members[anchor[0]] if a in links[d] and b in links[d]}
            gold = norm(histogram(ds).items()) if family == 'conjunction_disposition_counts' else norm([(d.removeprefix('tdoc:'),) for d in ds])
        elif family == 'largest_clause_footprint':
            sizes = {d: len(links[d]) for d in members[anchor[0]]}
            highest = max(sizes.values())
            gold = norm([(d.removeprefix('tdoc:'), n) for d, n in sizes.items() if n == highest])
        elif family == 'members_without_clause_records':
            gold = norm([(d.removeprefix('tdoc:'),) for d in members[anchor[0]] if not links[d]])
        else:
            raise ValueError(family)
        check(item['id'] + ':independent_gold', gold == norm(item['gold']))
        executed_names = {x['name'] for x in stored[item['id']]['mutations']}
        omitted = set(item['mutations']) - executed_names
        expected_omitted = {'intersection'} if family == 'shared_clauses' else ({'first_only', 'second_only'} if family == 'exclusive_clauses' else set())
        check(item['id'] + ':control_accounting', omitted == expected_omitted, defined_not_executed=sorted(omitted))
        for name, sql in [('reference', item['reference_sql']), *item['mutations'].items()]:
            if name in omitted:
                continue
            rows = norm(con.execute(sql).fetchall())
            expected = stored[item['id']]['reference'] if name == 'reference' else next(x for x in stored[item['id']]['mutations'] if x['name'] == name)
            check(item['id'] + ':' + name + ':actual_replay', rows == norm(expected['rows']) and expected['status'] == 'ok')
        for extra in (x for x in supplement['items'] if x['id'] == item['id']):
            check(item['id'] + ':' + extra['name'] + ':supplement_binding', extra['sql'] == item['mutations'][extra['name']] and extra['name'] in omitted)
            rows = norm(con.execute(extra['sql']).fetchall())
            check(item['id'] + ':' + extra['name'] + ':actual_supplement_replay', rows == norm(extra['rows']) and rows != gold and extra['status'] == 'ok')
    con.close()
result = {'scope': 'Independent full raw-row eligibility pool reconstruction, hash-min selection, all66 Python-set golds,254 original SQL executions and12 supplementary defined controls. Imports neither builder nor its gold functions. No model responses.',
          'python_version': sys.version, 'sqlite_version': sqlite3.sqlite_version,
          'implementation_sha256': sha(Path(__file__).read_bytes()),
          'selection_sha256': sha((MEAS / 'selection_and_gold.json').read_bytes()),
          'elapsed_seconds': time.monotonic() - started,
          'passed': sum(x['ok'] for x in checks), 'failed': sum(not x['ok'] for x in checks), 'checks': checks}
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'checks'}))
for failure in (c for c in checks if not c['ok']):
    print(json.dumps(failure))
raise SystemExit(bool(result['failed']))
