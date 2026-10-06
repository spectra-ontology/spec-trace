#!/usr/bin/env python3
"""score_core.py - score the recorded runs on SpectraCQ-Core and annotation-selected subsets.

score.py scores the released key: the first returned column of all 624 items.
The paper's Core and subset numbers use a different key, V2 in the
gold-remediation table: each of the 560 Core items is scored on its declared
answer column. That key ships as

  release_package/cqs/spectra_cq_v2.0/core_answer_gold.jsonl

one line per Core item with its answer column and the gold value set of that
column. For 553 items the set comes from the released reference query's rows.
For the 7 items whose reference query pins a literal value list the question
does not state, it comes from the same query with that list removed
(`repaired_cypher` in the file); `--gold released` scores those 7 on the
released query's rows instead (V1 in the same table).

Sets (--set):
  contract_exact_script_fixed_133 (default)
                                the 133 of the 208 below in which every column
                                verdict made by a language model falls on the
                                scored answer column and no phrase verdict is
                                recorded. Membership is stable under changes
                                to those judgments, conditional on the stored
                                rule verdicts and demand-column universe
  contract_exact_asked_208      the 208 items selected by the recorded demand
                                verdicts (contract_demand_provenance.jsonl):
                                no contract flag is set, and every column with
                                a required verdict is the scored answer column
  contract_exact_241            superseded: the 241 items with
                                contract_disposition 1, which bounds how many
                                returned columns a question demands, not which
  contract_exact_rule_only_149  superseded: the 149 of the 241 with no column
                                or phrase verdict made by a language model
  core                          all 560 Core items
Each set but core is a list under release_package/cqs/spectra_cq_v2.0/splits/.
The historical filenames are retained. Membership does not establish that
every field, count, attribute or ordering requirement in the question is
graded; see that directory's README.md and the annotation diagnostic sidecar.

Every arm is scored over the whole set: an item a run never answered scores
zero. When a log repeats an id, the first record counts. No network, no LLM.

Usage:  gunzip -k results/*/*/all.jsonl.gz     # optional: .gz logs are read directly
        python3 score_core.py                   # contract_exact_script_fixed_133, V2 gold
        python3 score_core.py --set contract_exact_asked_208
        python3 score_core.py --set core --json core_scores.json
"""
import argparse
import gzip
import json
from pathlib import Path

import bench_common as bc
from score import norm, score_row

BASE = bc.BASE
CQ = bc.ROOT / 'release_package/cqs/spectra_cq_v2.0'
METRICS = ('exact', 'precision', 'recall', 'f1')


def load_key(cq_dir, gold):
    key = {}
    with open(cq_dir / 'core_answer_gold.jsonl') as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if '_header' in r:
                continue
            values = r['gold_values']
            if gold == 'released' and 'gold_values_released_query' in r:
                values = r['gold_values_released_query']
            key[r['id']] = {'wg': r['wg'], 'values': {norm(v) for v in values}}
    return key


def load_set(cq_dir, name, key):
    if name == 'core':
        return sorted(key)
    ids = (cq_dir / 'splits' / f'{name}.txt').read_text().split()
    outside = [i for i in ids if i not in key]
    if outside:
        raise SystemExit(f'{len(outside)} ids of {name} are not Core items, e.g. {outside[0]}')
    return ids


def read_predictions(path):
    opener = gzip.open if path.suffix == '.gz' else open
    pred = {}
    with opener(path, 'rt') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            cid = row.get('id')
            if cid is not None and cid not in pred:
                pred[cid] = row.get('predicted_values')
    return pred


def iter_runs(results):
    for cond_dir in sorted(p for p in results.iterdir() if p.is_dir() and not p.name.startswith('_')):
        for model_dir in sorted(p for p in cond_dir.iterdir() if p.is_dir()):
            for name in ('all.jsonl', 'all.jsonl.gz'):
                if (model_dir / name).exists():
                    yield cond_dir.name, model_dir.name, model_dir / name
                    break


def mean(rows, metric):
    return sum(r[metric] for r in rows) / len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--set', default='contract_exact_script_fixed_133', help='split file name under splits/, or core')
    ap.add_argument('--gold', choices=('repaired', 'released'), default='repaired')
    ap.add_argument('--results', default=str(BASE / 'results'))
    ap.add_argument('--cq-dir', default=str(CQ))
    ap.add_argument('--json', help='write the scores to this path')
    a = ap.parse_args()

    cq_dir = Path(a.cq_dir)
    key = load_key(cq_dir, a.gold)
    ids = load_set(cq_dir, a.set, key)
    runs, pooled = {}, {}
    for cond, model, path in iter_runs(Path(a.results)):
        pred = read_predictions(path)
        rows = [score_row(pred[i], key[i]['values']) if i in pred else dict.fromkeys(METRICS, 0.0)
                for i in ids]
        runs.setdefault(cond, {})[model] = {
            'n': len(ids), 'n_attempted': sum(i in pred for i in ids),
            **{m: round(mean(rows, m), 6) for m in METRICS}}
        pooled.setdefault(cond, []).extend(rows)

    out = {'set': a.set, 'gold': a.gold, 'n': len(ids),
           'pooled_by_condition': {c: {'n_runs': len(runs[c]), **{m: round(mean(r, m), 6) for m in METRICS}}
                                   for c, r in pooled.items()},
           'runs': runs}
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1) + '\n')

    print(f'set={a.set} gold={a.gold} n={len(ids)}')
    print(f"{'condition':<14} {'model':<18} {'attempted':>9} {'exact':>7} {'f1':>7}")
    for cond in runs:
        for model, s in runs[cond].items():
            print(f"{cond:<14} {model:<18} {s['n_attempted']:>9} {s['exact']:>7.4f} {s['f1']:>7.4f}")
        p = out['pooled_by_condition'][cond]
        print(f"{cond:<14} {'(pooled)':<18} {'':>9} {p['exact']:>7.4f} {p['f1']:>7.4f}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
