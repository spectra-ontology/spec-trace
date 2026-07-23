#!/usr/bin/env python3
"""score.py — deterministic scorer for the SpectraCQ baseline campaign.

Gold = benchmark.jsonl gold_primary_values (a canonicalised set produced by
re-executing each CQ's Cypher against the live graph; no LLM). For every logged
result row we compute set-overlap metrics of the model's predicted answer set
against that gold set:

  * exact_match   strict set equality on canonicalised values (BIRD-style
                  execution accuracy for kg_grounded; set-exactness otherwise)
  * precision / recall / f1   on normalised values (whitespace-collapsed,
                  case-folded) so a correct id that differs only in casing/space
                  is not punished; reported as macro means over CQs

For kg_grounded we additionally report the pipeline health rates that a
Text2Cypher benchmark needs: produced-a-query, executed-without-error, and
execution accuracy (== exact_match). Aggregates: per (condition, model) overall
and per (condition, model, wg). No network, no LLM — pure re-scoring of logs, so
it is safe to re-run anytime.

Usage:  python3 score.py                 # score everything under results/
        python3 score.py --json scores.json
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import bench_common as bc

BASE = bc.BASE
RESULTS = BASE / 'results'
BENCH = bc.ROOT / 'release_package/cqs/spectra_cq_v2.0/benchmark.jsonl'


def norm(v):
    """Normalised comparison key: canon -> collapse whitespace -> casefold."""
    return ' '.join(bc.canon(v).split()).casefold()


def load_gold():
    gold = {}
    with open(BENCH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            gold[r['id']] = {
                'wg': r['wg'], 'phase': r['phase'],
                'values': {norm(v) for v in (r['gold_primary_values'] or [])},
            }
    return gold


def score_row(pred_values, gold_values):
    """Set metrics for one CQ. Returns dict of exact/precision/recall/f1."""
    pred = {norm(v) for v in (pred_values or [])}
    gold = set(gold_values)
    inter = pred & gold
    # empty gold shouldn't occur (degenerate held out); guard anyway
    if not gold:
        exact = 1.0 if not pred else 0.0
        return {'exact': exact, 'precision': exact, 'recall': exact, 'f1': exact,
                'pred_n': len(pred), 'gold_n': 0, 'inter_n': len(inter)}
    precision = len(inter) / len(pred) if pred else 0.0
    recall = len(inter) / len(gold)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    exact = 1.0 if pred == gold else 0.0
    return {'exact': exact, 'precision': precision, 'recall': recall, 'f1': f1,
            'pred_n': len(pred), 'gold_n': len(gold), 'inter_n': len(inter)}


def iter_result_files():
    if not RESULTS.exists():
        return
    for cond_dir in sorted(RESULTS.iterdir()):
        if not cond_dir.is_dir() or cond_dir.name.startswith('_'):
            continue
        for model_dir in sorted(cond_dir.iterdir()):
            if not model_dir.is_dir():
                continue
            f = model_dir / 'all.jsonl'
            if f.exists():
                yield cond_dir.name, model_dir.name, f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', default=str(RESULTS / 'scores.json'),
                    help='where to write the aggregated scores json')
    args = ap.parse_args()

    gold = load_gold()
    if not gold:
        print('no gold loaded — is benchmark.jsonl present?')
        return 2

    # accumulator[(cond, model)] and [(cond, model, wg)] -> list of per-CQ metrics
    agg = defaultdict(lambda: defaultdict(list))       # key -> metric -> [values]
    health = defaultdict(lambda: defaultdict(int))     # kg pipeline counters
    seen_ids = defaultdict(set)                         # (cond,model) -> ids (dedupe)
    n_rows = n_dup = n_nogold = n_err = 0

    for cond, model, path in iter_result_files():
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:  # noqa: BLE001
                    continue
                n_rows += 1
                cid = row.get('id')
                key = (cond, model)
                if cid in seen_ids[key]:          # resumable logs may double-write
                    n_dup += 1
                    continue
                seen_ids[key].add(cid)
                g = gold.get(cid)
                if g is None:
                    n_nogold += 1
                    continue
                if row.get('error'):
                    n_err += 1
                m = score_row(row.get('predicted_values'), g['values'])
                for metric in ('exact', 'precision', 'recall', 'f1'):
                    agg[key][metric].append(m[metric])
                    agg[(cond, model, g['wg'])][metric].append(m[metric])
                if cond == 'kg_grounded':
                    health[key]['total'] += 1
                    if row.get('cypher'):
                        health[key]['produced_query'] += 1
                    if row.get('exec_status') == 'OK':
                        health[key]['executed_ok'] += 1
                    if row.get('exec_status') == 'REJECTED_WRITE':
                        health[key]['rejected_write'] += 1

    def summarize(key):
        d = agg[key]
        n = len(d['f1'])
        if not n:
            return None
        out = {metric: round(sum(vals) / len(vals), 4) for metric, vals in d.items()}
        out['n'] = n
        return out

    overall = {}
    for (cond, model) in sorted(k for k in agg if len(k) == 2):
        s = summarize((cond, model))
        if s is None:
            continue
        entry = {'overall': s, 'by_wg': {}}
        for wg in ['RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5']:
            ws = summarize((cond, model, wg))
            if ws:
                entry['by_wg'][wg] = ws
        if cond == 'kg_grounded':
            h = health[(cond, model)]
            t = h['total'] or 1
            entry['pipeline'] = {
                'total': h['total'],
                'produced_query_rate': round(h['produced_query'] / t, 4),
                'executed_ok_rate': round(h['executed_ok'] / t, 4),
                'rejected_write': h['rejected_write'],
                'execution_accuracy': s['exact'],  # exact set match == exec accuracy
            }
        overall.setdefault(cond, {})[model] = entry

    Path(args.json).write_text(json.dumps({
        'gold_cqs': len(gold),
        'rows_scored': n_rows, 'duplicates_skipped': n_dup,
        'rows_without_gold': n_nogold, 'rows_with_call_error': n_err,
        'scores': overall,
    }, indent=2, ensure_ascii=False))

    # ---- console summary table
    print(f'gold CQs: {len(gold)} | rows: {n_rows} | dup: {n_dup} | '
          f'no-gold: {n_nogold} | call-errors: {n_err}')
    print(f'-> {args.json}\n')
    hdr = f'{"condition":12s} {"model":18s} {"n":>4s} {"F1":>7s} {"P":>7s} {"R":>7s} {"exact":>7s}'
    for cond in ['closed_book', 'rag', 'kg_grounded']:
        if cond not in overall:
            continue
        print(hdr)
        print('-' * len(hdr))
        for model in sorted(overall[cond]):
            s = overall[cond][model]['overall']
            print(f'{cond:12s} {model:18s} {s["n"]:4d} {s["f1"]:7.3f} '
                  f'{s["precision"]:7.3f} {s["recall"]:7.3f} {s["exact"]:7.3f}')
            if cond == 'kg_grounded':
                p = overall[cond][model]['pipeline']
                print(f'{"":12s} {"":18s}  -> produced={p["produced_query_rate"]:.3f} '
                      f'exec_ok={p["executed_ok_rate"]:.3f} '
                      f'exec_acc={p["execution_accuracy"]:.3f}')
        print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
