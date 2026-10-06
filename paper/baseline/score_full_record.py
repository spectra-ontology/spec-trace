#!/usr/bin/env python3
"""score_full_record.py - full-record scores of the kg_grounded runs on SpectraCQ-Core.

score_core.py scores each Core item on one column, its declared answer column.
This script scores the whole returned records instead. The run logs keep only
the first returned column of each query, so the records are obtained by
executing every recorded query again on the released graph. Two steps:

  replay --wg RANn   On a Neo4j database that holds the released body TTL of
                     one working group, execute every query a kg_grounded run
                     recorded for that group, the group's released reference
                     queries (benchmark.jsonl), and the repaired reference
                     query of each of its scope-repaired Core items. Writes
                     results/_full_record/RANn.jsonl.gz.
  score              Score the 560 Core items, or a subset of them (--set,
                     --answer-type), from the five replay files.

Load one working group at a time before its replay, for example with

  python3 release_package/tests/verify_benchmark.py --full --wg RAN1 \\
      --bolt bolt://localhost:7687 --user neo4j --password PASSWORD

which empties the database, loads release_package/kg/per_wg/RAN1-body.ttl with
the shipped loader and checks the reference answers against it. The body TTLs
are the Zenodo deposit (release_package/kg/per_wg/README.md).

Execution follows bench_common.exec_cypher, the query executor of the
harness: its write-clause guard and its transaction timeout (timeout_s, 30
seconds), in a read-access session; a query that exceeds the timeout is recorded
as TIMEOUT. Rows are kept up to the row_cap of exec_cypher (2,000), the result
cap the benchmark declares; exec_cypher itself returns every row. The recorded
runs did not apply the row cap (250 recorded executions return more than
2,000 rows), and none of their errors is a transaction timeout, so a
replayed query can time out or reach the cap where its recorded execution
did not; both are recorded per query. Each value is stored as
bench_common.canon renders it, which leaves score.norm unchanged. The
recorded runs executed on Neo4j 5.26 with the APOC
plugin, and some recorded queries call APOC procedures, so install the APOC
release that matches the server before a replay. The replay header records the
server version, the APOC version (null when APOC does not answer), the row cap,
the timeout and a digest of the executing code; each record carries its
execution time. A replay interrupted midway resumes from its partial file only
with the same settings.

Scoring. Each returned row is a record, compared as the tuple of its
normalized values sorted within the row (row_key below), so column names and
column order are ignored and a value is not tied to the column that returned
it; the predicted and gold record sets are compared, so row order and
duplicate rows are ignored. Exact is 1 when the two sets are equal; precision,
recall and F1 are those of the set overlap. The
gold records are the rows of the released reference query
(release_package/cqs/spectra_cq_v2.0/gold/RANn_gold.json). For the 7
scope-repaired items they are the rows of `repaired_cypher` in
core_answer_gold.jsonl; `--gold released` keeps the released rows for them.
Every model is averaged over all 560 items: an item without a query, or whose
query fails or times out, scores zero. The answer-column scores of score_core.py
for the same runs are printed alongside.

Three options of `score` select items and add a summary; without them the
output is the one described here. `--set NAME` averages over a subset of
Core named as in score_core.py (contract_exact_script_fixed_133,
contract_exact_asked_208 or another list under splits/) or core, the
default. `--answer-type T[,T]` keeps the items whose
answer_type in answer_contract.jsonl is one of the listed types (scalar_set,
ranked_top_k, tuple_set, mapping). `--ci` adds a 95% interval to each model's
F1 from a paired item bootstrap: 10,000 resamples of the selected items drawn
with random.Random(0), one resample shared by every model, the interval
running from the 251st to the 9,750th sorted resample mean. A model pair
counts as separated when the interval of its difference excludes zero. The
options change which items are averaged, not how an item is scored, and the
integrity check always covers all 560 Core items.

The replay is also an integrity check, reported under `integrity`: whether the
released reference queries return the gold records on the loaded graph, whether
each recorded execution error recurs or now times out, and whether the replayed first column
equals the recorded one, split by whether the 2,000-row cap was reached or the
query carries a LIMIT.

Usage:  python3 score_full_record.py replay --wg RAN1 --bolt bolt://localhost:7687 \\
            --user neo4j --password PASSWORD        # once per working group
        python3 score_full_record.py score --json full_record_scores.json
        python3 score_full_record.py score --set contract_exact_script_fixed_133 --ci
        python3 score_full_record.py score --answer-type tuple_set,mapping
"""
import argparse
import gzip
import hashlib
import inspect
import io
import json
import os
import random
import re
import time
from pathlib import Path

import bench_common as bc
import score_core as sc
from score import norm

BASE = bc.BASE
CQ = bc.ROOT / 'release_package/cqs/spectra_cq_v2.0'
RUNS = BASE / 'results/kg_grounded'
REPLAY = BASE / 'results/_full_record'
WGS = ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5')
_EXEC = inspect.signature(bc.exec_cypher).parameters
ROW_CAP = _EXEC['row_cap'].default
TIMEOUT_S = _EXEC['timeout_s'].default
METRICS = ('exact', 'precision', 'recall', 'f1')
N_BOOT, SEED = 10000, 0
WRITE_WORDS = (' create ', ' merge ', ' delete ', ' set ', ' remove ', ' drop ')


def query_hash(cypher):
    return hashlib.sha256(cypher.encode('utf-8')).hexdigest()[:16]


def read_logs(runs):
    """{model: {id: first record}} over results/kg_grounded/<model>/all.jsonl(.gz)."""
    logs = {}
    for model_dir in sorted(p for p in runs.iterdir() if p.is_dir()):
        for name in ('all.jsonl', 'all.jsonl.gz'):
            path = model_dir / name
            if not path.exists():
                continue
            opener = gzip.open if path.suffix == '.gz' else open
            recs = {}
            with opener(path, 'rt') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    r = json.loads(line)
                    recs.setdefault(r['id'], r)
            logs[model_dir.name] = recs
            break
    return logs


def read_core(cq_dir):
    """{id: core_answer_gold record} for the 560 Core items."""
    core = {}
    with open(cq_dir / 'core_answer_gold.jsonl') as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                if '_header' not in r:
                    core[r['id']] = r
    return core


def execute(session, cypher, timeout=None):
    lowered = (cypher or '').lower()
    for bad in WRITE_WORDS:
        if bad in f' {lowered} ':
            return {'status': 'REJECTED_WRITE', 'error': f'write clause {bad.strip()}',
                    'columns': [], 'rows': [], 'row_capped': False}
    try:
        with session.begin_transaction(timeout=timeout) as tx:
            result = tx.run(cypher)
            rows, capped = [], False
            for rec in result:
                if len(rows) >= ROW_CAP:
                    capped = True
                    break
                rows.append([bc.canon(v) for v in rec.data().values()])
            cols = list(result.keys()) if rows else []
        return {'status': 'OK', 'error': None, 'columns': cols, 'rows': rows, 'row_capped': capped}
    except Exception as e:  # noqa: BLE001  any driver or server error is data here
        timed_out = 'TransactionTimedOut' in (getattr(e, 'code', None) or '')
        return {'status': 'TIMEOUT' if timed_out else 'ERROR', 'error': f'{type(e).__name__}: {str(e)[:300]}',
                'columns': [], 'rows': [], 'row_capped': False}


def executor_digest():
    """SHA-256 over the code that turns a query into a replay record."""
    src = inspect.getsource(execute) + inspect.getsource(bc.canon) + repr((ROW_CAP, WRITE_WORDS))
    return hashlib.sha256(src.encode('utf-8')).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def replay(a):
    from neo4j import READ_ACCESS, GraphDatabase

    wg = a.wg
    password = a.password or os.environ.get('NEO4J_PASSWORD')
    if not password:
        raise SystemExit('give --password or set NEO4J_PASSWORD')
    logs = read_logs(Path(a.runs))
    core = read_core(Path(a.cq_dir))
    tasks = [(m, cid, r['cypher']) for m, recs in sorted(logs.items())
             for cid, r in sorted(recs.items()) if r.get('wg') == wg and r.get('cypher')]
    refs = []
    with open(Path(a.cq_dir) / 'benchmark.jsonl') as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                if r['wg'] == wg:
                    refs.append(('released_query', r['id'], r['cypher']))
    refs += [('repaired_query', cid, r['repaired_cypher']) for cid, r in sorted(core.items())
             if r['wg'] == wg and r.get('repaired_cypher')]
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    partial = out_dir / f'{wg}.jsonl.partial'
    settings = {'wg': wg, 'row_cap': ROW_CAP, 'timeout_s': a.timeout, 'executor_sha256': executor_digest()}
    done = {}
    if partial.exists():
        lines = partial.read_text().splitlines()
        if not lines or json.loads(lines[0]).get('_partial') != settings:
            raise SystemExit(f'{partial} was written with other settings; remove it to start over')
        for line in lines[1:]:
            r = json.loads(line)
            done[(r.get('model') or 'reference:' + r['reference'], r['id'])] = r

    driver = GraphDatabase.driver(a.bolt, auth=(a.user, password), notifications_min_severity='OFF')
    try:
        with driver.session(default_access_mode=READ_ACCESS) as s:
            server = s.run('CALL dbms.components() YIELD name, versions, edition '
                           'RETURN versions[0] AS v, edition AS e').single()
            nodes = s.run('MATCH (n) RETURN count(n) AS c').single()['c']
            rels = s.run('MATCH ()-[r]->() RETURN count(r) AS c').single()['c']
            try:
                apoc = s.run('RETURN apoc.version() AS v').single()['v']
            except Exception:  # noqa: BLE001  no APOC on this server
                apoc = None
            if apoc is None:
                print(f'{wg}: APOC does not answer; recorded queries that call it will fail', flush=True)
            if not nodes:
                raise SystemExit(f'the database is empty: load {wg}-body.ttl first')
            if not partial.exists():
                partial.write_text(json.dumps({'_partial': settings}) + '\n')
            with open(partial, 'a') as f:
                todo = [('reference:' + kind, cid, cy) for kind, cid, cy in refs] + tasks
                for i, (m, cid, cypher) in enumerate(todo, 1):
                    if (m, cid) in done:
                        continue
                    t0 = time.monotonic()
                    res = execute(s, cypher, a.timeout)
                    rec = {'id': cid, 'query_sha256': query_hash(cypher), **res,
                           'elapsed_s': round(time.monotonic() - t0, 1)}
                    if m.startswith('reference:'):
                        rec = {'reference': m.split(':', 1)[1]} | rec
                    else:
                        rec = {'model': m} | rec
                    f.write(json.dumps(rec, ensure_ascii=False) + '\n')
                    f.flush()
                    done[(m, cid)] = rec
                    if i % 100 == 0 or i == len(todo):
                        print(f'{wg}: {i}/{len(todo)}', flush=True)
    finally:
        driver.close()

    header = {'_header': {
        'wg': wg, 'row_cap': ROW_CAP, 'timeout_s': a.timeout, 'executor_sha256': settings['executor_sha256'],
        'graph': {'nodes': nodes, 'relationships': rels, 'server': f"{server['v']} {server['e']}",
                  'apoc': apoc},
        'body_ttl': ({'name': Path(a.ttl).name, 'bytes': Path(a.ttl).stat().st_size,
                      'sha256': sha256_file(a.ttl)} if a.ttl else None),
        'n_queries': len(tasks), 'n_reference': len(refs)}}
    lines = [header] + [done[k] for k in sorted(done)]
    buf = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=buf, mtime=0) as gz:
        for r in lines:
            gz.write((json.dumps(r, ensure_ascii=False) + '\n').encode('utf-8'))
    (out_dir / f'{wg}.jsonl.gz').write_bytes(buf.getvalue())
    partial.unlink()
    n_ok = sum(r['status'] == 'OK' for r in done.values())
    print(f'{wg}: {len(tasks)} queries, {len(refs)} reference, {n_ok} OK -> {out_dir / (wg + ".jsonl.gz")}')
    return 0


def row_key(values):
    return tuple(sorted(norm(v) for v in values))


def score_sets(pred, gold):
    if not gold:
        exact = 1.0 if not pred else 0.0
        return dict.fromkeys(METRICS, exact)
    inter = len(pred & gold)
    precision = inter / len(pred) if pred else 0.0
    recall = inter / len(gold)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {'exact': 1.0 if pred == gold else 0.0, 'precision': precision, 'recall': recall, 'f1': f1}


def read_replay(replay_dir):
    header, runs, refs = {}, {}, {}
    for wg in WGS:
        path = replay_dir / f'{wg}.jsonl.gz'
        if not path.exists():
            raise SystemExit(f'{path} is missing: run `replay --wg {wg}` first')
        with gzip.open(path, 'rt') as f:
            for line in f:
                r = json.loads(line)
                if '_header' in r:
                    header[wg] = r['_header']
                elif 'reference' in r:
                    refs[(r['reference'], r['id'])] = r
                else:
                    runs[(r['model'], r['id'])] = r
    return header, runs, refs


def mean(rows, metric):
    return sum(r[metric] for r in rows) / len(rows)


def integrity(logs, runs, ids):
    """Recorded execution status and first column against the replay, over `ids`."""
    c = dict.fromkeys(('replayed', 'recorded_error', 'recorded_error_recurs', 'recorded_error_now_timeout',
                       'recorded_error_now_ok', 'recorded_ok_now_error', 'recorded_ok_now_timeout',
                       'first_column_compared', 'first_column_equal', 'differ_row_cap_reached',
                       'differ_with_limit', 'differ_other'), 0)
    for m, recs in logs.items():
        for cid in ids:
            stored, r = recs.get(cid), runs.get((m, cid))
            if stored is None or r is None:
                continue
            c['replayed'] += 1
            if stored.get('exec_status') == 'ERROR':
                c['recorded_error'] += 1
                c['recorded_error_recurs'] += r['status'] == 'ERROR'
                c['recorded_error_now_timeout'] += r['status'] == 'TIMEOUT'
                c['recorded_error_now_ok'] += r['status'] == 'OK'
            elif stored.get('exec_status') == 'OK' and r['status'] != 'OK':
                c['recorded_ok_now_timeout' if r['status'] == 'TIMEOUT' else 'recorded_ok_now_error'] += 1
            if stored.get('exec_status') == 'OK' and r['status'] == 'OK':
                c['first_column_compared'] += 1
                first = sorted({row[0] for row in r['rows']}) if r['columns'] else []
                if set(first[:5000]) == set(stored.get('predicted_values') or []):
                    c['first_column_equal'] += 1
                elif r['row_capped']:
                    c['differ_row_cap_reached'] += 1
                elif re.search(r'\blimit\b', stored['cypher'], re.IGNORECASE):
                    c['differ_with_limit'] += 1
                else:
                    c['differ_other'] += 1
    return c



def read_contract(cq_dir):
    """{id: answer_contract record} for the 560 Core items."""
    contract = {}
    with open(cq_dir / 'answer_contract.jsonl') as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                if '_header' not in r:
                    contract[r['id']] = r
    return contract


def bootstrap(per_item, n_boot=N_BOOT, seed=SEED):
    """Paired item bootstrap. `per_item` is {scorer: {model: [item F1, ...]}}, every list in one item order;
    each resample of the items is shared by every scorer and model."""
    n = len(next(iter(next(iter(per_item.values())).values())))
    rng = random.Random(seed)
    boots = {s: {m: [] for m in d} for s, d in per_item.items()}
    for _ in range(n_boot):
        draw = [rng.randrange(n) for _ in range(n)]
        for s, d in per_item.items():
            for m, v in d.items():
                boots[s][m].append(sum(map(v.__getitem__, draw)) / n)
    lo, hi = int(0.025 * n_boot), int(0.975 * n_boot) - 1

    def interval(vals):
        vals = sorted(vals)
        return [round(vals[lo], 6), round(vals[hi], 6)]

    out = {}
    for s, b in boots.items():
        ms = sorted(b)
        ci = {m: interval(b[m]) for m in ms}
        diffs = [interval([x - y for x, y in zip(b[p], b[q])]) for i, p in enumerate(ms) for q in ms[i + 1:]]
        half = [(h - l) / 2 for l, h in ci.values()]
        out[s] = {'ci95': ci, 'model_pairs': len(diffs),
                  'model_pairs_separated': sum(l > 0 or h < 0 for l, h in diffs),
                  'half_width_min': round(min(half), 6), 'half_width_max': round(max(half), 6)}
    return {'n_boot': n_boot, 'seed': seed, 'scores': out}


def score(a):
    cq_dir = Path(a.cq_dir)
    core = read_core(cq_dir)
    ids = sorted(core)
    logs = read_logs(Path(a.runs))
    header, runs, refs = read_replay(Path(a.replay))

    stale = [k for k, r in runs.items()
             if k[1] not in logs.get(k[0], {}) or query_hash(logs[k[0]][k[1]]['cypher']) != r['query_sha256']]
    if stale:
        raise SystemExit(f'{len(stale)} replayed queries do not match the run logs, e.g. {stale[0]}')
    expected = {(m, cid) for m, recs in logs.items() for cid, r in recs.items() if r.get('cypher')}
    if set(runs) != expected:
        raise SystemExit(f'replay covers {len(runs)} queries, the logs hold {len(expected)}')

    released_gold = {}
    for wg in WGS:
        for e in json.loads((cq_dir / 'gold' / f'{wg}_gold.json').read_text())['gold']:
            released_gold[f"{e['wg']}_P{e['phase']}_{e['id']}"] = {row_key(r.values()) for r in e['rows']}
    gold = dict(released_gold)
    if a.gold == 'repaired':
        for cid, r in core.items():
            if r.get('repaired_cypher'):
                ref = refs.get(('repaired_query', cid))
                if ref is None or ref['status'] != 'OK' or ref['query_sha256'] != query_hash(r['repaired_cypher']):
                    raise SystemExit(f'no usable replay of the repaired reference query of {cid}')
                gold[cid] = {row_key(row) for row in ref['rows']}

    key = sc.load_key(cq_dir, a.gold)
    sel = sorted(sc.load_set(cq_dir, a.set, key))
    types = a.answer_type.split(',') if a.answer_type else None
    if types:
        contract = read_contract(cq_dir)
        unknown = sorted(set(types) - {r['answer_type'] for r in contract.values()})
        if unknown:
            raise SystemExit(f'unknown answer type {unknown[0]}')
        sel = [cid for cid in sel if contract[cid]['answer_type'] in types]
    if not sel:
        raise SystemExit('no item is selected')
    models, pooled = {}, {'full_record': [], 'answer_column': []}
    per_item = {'full_record': {}, 'answer_column': {}}
    for m, recs in sorted(logs.items()):
        full = []
        for cid in sel:
            r = runs.get((m, cid))
            if r is None or r['status'] != 'OK':
                full.append(dict.fromkeys(METRICS, 0.0))
            else:
                full.append(score_sets({row_key(row) for row in r['rows']}, gold[cid]))
        col = [sc.score_row(recs[cid].get('predicted_values'), key[cid]['values']) if cid in recs
               else dict.fromkeys(METRICS, 0.0) for cid in sel]
        models[m] = {'n': len(sel), 'n_executed': sum(runs.get((m, c), {}).get('status') == 'OK' for c in sel),
                     'full_record': {k: round(mean(full, k), 6) for k in METRICS},
                     'answer_column': {k: round(mean(col, k), 6) for k in METRICS}}
        pooled['full_record'] += full
        pooled['answer_column'] += col
        per_item['full_record'][m] = [r['f1'] for r in full]
        per_item['answer_column'][m] = [r['f1'] for r in col]

    ref_check = {'compared': 0, 'equal': 0, 'not_ok': [], 'differ': []}
    for cid in ids:
        ref = refs.get(('released_query', cid))
        ref_check['compared'] += 1
        if ref is None or ref['status'] != 'OK':
            ref_check['not_ok'].append(cid)
        elif {row_key(row) for row in ref['rows']} == released_gold[cid]:
            ref_check['equal'] += 1
        else:
            ref_check['differ'].append(cid)

    boot = bootstrap(per_item) if a.ci else None
    out = {'set': a.set, **({'answer_type': types} if types else {}), 'gold': a.gold, 'n': len(sel),
           'replay_headers': header,
           'pooled': {s: {k: round(mean(v, k), 6) for k in METRICS} for s, v in pooled.items()},
           'models': models, **({'bootstrap': boot} if boot else {}),
           'integrity': {'reference_rows_equal_gold_core': ref_check,
                         'core': integrity(logs, runs, ids),
                         'all_released_items': integrity(logs, runs, sorted({c for m, c in expected}))}}
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1) + '\n')

    label = 'Core' if a.set == 'core' else a.set
    if types:
        label += ' answer_type=' + ','.join(types)
    print(f'kg_grounded runs, {label} n={len(sel)}, gold={a.gold}')
    print(f"{'model':<18} {'executed':>8} {'rec.exact':>9} {'rec.f1':>7} {'col.exact':>9} {'col.f1':>7}")
    for m, s in models.items():
        fr, ac = s['full_record'], s['answer_column']
        print(f"{m:<18} {s['n_executed']:>8} {fr['exact']:>9.4f} {fr['f1']:>7.4f} {ac['exact']:>9.4f} {ac['f1']:>7.4f}")
    fr, ac = out['pooled']['full_record'], out['pooled']['answer_column']
    print(f"{'(pooled)':<18} {'':>8} {fr['exact']:>9.4f} {fr['f1']:>7.4f} {ac['exact']:>9.4f} {ac['f1']:>7.4f}")
    if boot:
        fb, cb = boot['scores']['full_record'], boot['scores']['answer_column']
        print(f"paired bootstrap over the {len(sel)} items: {boot['n_boot']} resamples, seed {boot['seed']}, "
              'one resample shared by every model')
        print(f"{'model':<18} {'rec.f1 95% interval':>20} {'col.f1 95% interval':>20}")
        for m in models:
            (fl, fh), (cl, ch) = fb['ci95'][m], cb['ci95'][m]
            print(f"{m:<18}   [{fl:.4f}, {fh:.4f}]   [{cl:.4f}, {ch:.4f}]")
        for name, b in (('full record', fb), ('answer column', cb)):
            print(f"{name}: {b['model_pairs_separated']} of {b['model_pairs']} model pairs separated (difference "
                  f"interval excludes 0); interval half-width {b['half_width_min']:.4f} to {b['half_width_max']:.4f}")
    print('released reference queries return the gold records on the loaded graph: '
          f"{ref_check['equal']}/{ref_check['compared']} Core items")
    for scope in ('core', 'all_released_items'):
        print(scope, json.dumps(out['integrity'][scope]))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    rp = sub.add_parser('replay', help='execute the recorded queries of one working group')
    rp.add_argument('--wg', required=True, choices=WGS)
    rp.add_argument('--bolt', default='bolt://localhost:7687')
    rp.add_argument('--user', default='neo4j')
    rp.add_argument('--password', help='or set NEO4J_PASSWORD')
    rp.add_argument('--ttl', help='the loaded body TTL, recorded by size and sha256')
    rp.add_argument('--out', default=str(REPLAY))
    rp.add_argument('--timeout', type=float, default=TIMEOUT_S,
                    help=f'transaction timeout in seconds (default: {TIMEOUT_S}, that of bench_common.exec_cypher)')
    sp = sub.add_parser('score', help='score the Core items from the replay files')
    sp.add_argument('--gold', choices=('repaired', 'released'), default='repaired')
    sp.add_argument('--replay', default=str(REPLAY))
    sp.add_argument('--json', help='write the scores to this path')
    sp.add_argument('--set', default='core', help='a subset named as in score_core.py, or core (default)')
    sp.add_argument('--answer-type', help='keep the items of these answer types, comma-separated')
    sp.add_argument('--ci', action='store_true',
                    help='add paired bootstrap 95%% intervals of F1 and count the model pairs they separate')
    for p in (rp, sp):
        p.add_argument('--runs', default=str(RUNS))
        p.add_argument('--cq-dir', default=str(CQ))
    a = ap.parse_args()
    return replay(a) if a.cmd == 'replay' else score(a)


if __name__ == '__main__':
    raise SystemExit(main())
