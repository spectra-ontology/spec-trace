#!/usr/bin/env python3
"""Offline SQL/Cypher answer-column comparison on the whole released Core key.

Use retained predictions for one shared model and the current repaired Core
answer-column key. Query failures and missing items score zero; no item is
selected by either arm's success. This does not execute queries or reconstruct
the historical 325-item comparison. No network, model or database access occurs.

The optional paired item bootstrap uses common Random(0) draws, 10,000
resamples and the same rounded endpoints as analyse_contract_subsets.py.
"""
import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

import analyse_contract_subsets as subsets
import bench_common as bc
import score_core as sc
from score import score_row

MODEL = 'claude-opus-4.8'
CQ = bc.ROOT / 'release_package/cqs/spectra_cq_v2.0'
SQL_LOG = bc.BASE / f'relational/runs/sql_grounded/{MODEL}/all.jsonl.gz'
CYPHER_LOG = bc.BASE / f'results/kg_grounded/{MODEL}/all.jsonl.gz'
METRICS = ('exact', 'precision', 'recall', 'f1')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_name(path):
    try:
        return path.resolve().relative_to(bc.ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def load_core(cq_dir):
    """Check unique, nonempty Core labels before using the existing scorer key."""
    rows = [json.loads(line) for line in (cq_dir / 'core_answer_gold.jsonl').read_text().splitlines()
            if line.strip()]
    rows = [row for row in rows if '_header' not in row]
    ids = [row['id'] for row in rows]
    require(len(ids) == len(set(ids)), 'Core key contains duplicate ids')
    require(bool(ids), 'Core key is empty')
    key = sc.load_key(cq_dir, 'repaired')
    require(set(key) == set(ids), 'Core loader changed membership')
    require(all(row['values'] for row in key.values()), 'Core key has an empty gold answer')
    metadata = {row['id']: {'wg': row['wg'], 'answer_column': row['answer_column'],
                          'scope_repaired': 'repaired_cypher' in row}
                for row in rows}
    return key, metadata


def read_run(path, condition, model=MODEL):
    """Read every logged row; retain the first record for a repeated ID."""
    opener = gzip.open if path.suffix == '.gz' else open
    first, counts = {}, Counter()
    with opener(path, 'rt') as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            require(isinstance(row, dict), f'{path.name}:{line_no}: expected an object')
            cid = row.get('id')
            require(isinstance(cid, str) and bool(cid), f'{path.name}:{line_no}: missing id')
            require(row.get('condition') == condition, f'{cid}: unexpected condition')
            require(row.get('model_slug') == model, f'{cid}: unexpected model')
            require(row.get('predicted_values') is None or isinstance(row['predicted_values'], list),
                    f'{cid}: predicted_values must be a list or null')
            counts[cid] += 1
            if cid not in first:
                first[cid] = row
    return first, counts


def successful(row):
    require(not (row.get('exec_status') == 'OK' and row.get('error')),
            f'{row["id"]}: query OK conflicts with a model-call error')
    return row.get('exec_status') == 'OK' and not row.get('error')


def score_arm(ids, key, records, record_counts):
    """Score every declared ID, with explicit zero rows for missing/failed runs."""
    scored = {}
    for cid in ids:
        row = records.get(cid)
        if row is None:
            scored[cid] = dict.fromkeys(METRICS, 0.0)
        elif successful(row):
            scored[cid] = score_row(row.get('predicted_values'), key[cid]['values'])
        else:
            require(not row.get('predicted_values'), f'{cid}: failed query has nonempty predictions')
            scored[cid] = dict.fromkeys(METRICS, 0.0)
    present = [records[cid] for cid in ids if cid in records]
    statuses = Counter(str(row.get('exec_status') or 'UNRECORDED') for row in present)
    duplicates = sorted(cid for cid in ids if record_counts.get(cid, 0) > 1)
    summary = {
        'n_denominator': len(ids), 'n_scored_including_zero': len(scored),
        'n_attempted': len(present), 'n_missing': len(ids) - len(present),
        'n_query_ok': sum(successful(row) for row in present),
        'n_query_error': statuses['ERROR'],
        'n_other_failed_or_unrecorded': sum(not successful(row) and row.get('exec_status') != 'ERROR'
                                          for row in present),
        'n_model_call_errors': sum(bool(row.get('error')) for row in present),
        'query_status_counts': dict(sorted(statuses.items())),
        'n_duplicate_ids': len(duplicates),
        'n_duplicate_records': sum(record_counts[cid] - 1 for cid in duplicates),
        'duplicate_ids': duplicates,
        'model_slug_counts': dict(sorted(Counter(row.get('model_slug') for row in present).items())),
        'model_id_counts': dict(sorted(Counter(str(row.get('model_id')) for row in present).items())),
        'metrics': {metric: round(sum(scored[cid][metric] for cid in ids) / len(ids), 6)
                    for metric in METRICS},
        'exact_matches': sum(scored[cid]['exact'] == 1 for cid in ids),
        'source_log': {'n_records': sum(record_counts.values()), 'n_unique_ids': len(records),
                       'n_outside_core': len(set(records) - set(ids)),
                       'n_duplicate_ids': sum(n > 1 for n in record_counts.values()),
                       'n_duplicate_records': sum(n - 1 for n in record_counts.values())}}
    return scored, summary


def paired_interval(sql_f1, cypher_f1, n_boot=10000, seed=0, engine='auto', batch_size=128):
    """Two fixed arms share item draws; there is no text-run selection here."""
    raw = subsets.paired_bootstrap(
        {'answer_column': {'sql': sql_f1}}, {'cypher': cypher_f1},
        n_boot, seed, engine, batch_size)
    result = raw['scores']['answer_column']
    ci = result['fixed']['model_minus_text_ci95']['sql']
    require(result['fixed'] == result['reselected'], 'single fixed comparator was reselected differently')
    return {
        'n_boot': n_boot, 'seed': seed, 'generator': raw['generator'], 'engine': raw['engine'],
        'unit': 'Core item; the same draws are used for both fixed arms',
        'endpoint_rule': raw['endpoint_rule'], 'clear_rule': raw['clear_rule'],
        'sql_f1_ci95': result['model_f1_ci95']['sql'],
        'cypher_f1_ci95': result['fixed']['text_bar_ci95'],
        'sql_minus_cypher_f1_ci95': ci,
        'sql_above_cypher': ci[0] > 0, 'sql_below_cypher': ci[1] < 0,
        'family_wise_correction': False, 'schema_template_cluster_adjustment': False}


def status_group(sql, cypher):
    def status(row):
        return 'missing' if row is None else ('ok' if successful(row) else 'failed')
    return f'sql_{status(sql)}__cypher_{status(cypher)}'


def analyse(ci=False, n_boot=10000, seed=0, engine='auto', batch_size=128,
            cq_dir=CQ, sql_log=SQL_LOG, cypher_log=CYPHER_LOG):
    key, metadata = load_core(cq_dir)
    ids = sorted(key)
    sql, sql_counts = read_run(sql_log, 'sql_grounded')
    cypher, cypher_counts = read_run(cypher_log, 'kg_grounded')
    sql_scores, sql_summary = score_arm(ids, key, sql, sql_counts)
    cypher_scores, cypher_summary = score_arm(ids, key, cypher, cypher_counts)
    groups = {}
    for name in sorted({status_group(sql.get(cid), cypher.get(cid)) for cid in ids}):
        members = [cid for cid in ids if status_group(sql.get(cid), cypher.get(cid)) == name]
        groups[name] = {'n': len(members), 'ids': members,
                        'sql_f1': round(sum(sql_scores[cid]['f1'] for cid in members) / len(members), 6),
                        'cypher_f1': round(sum(cypher_scores[cid]['f1'] for cid in members) / len(members), 6),
                        'use': 'descriptive status decomposition; not a selected headline cohort'}
    paths = [cq_dir / 'core_answer_gold.jsonl', sql_log, cypher_log,
             Path(__file__), bc.BASE / 'score_core.py', bc.BASE / 'score.py',
             bc.BASE / 'bench_common.py', bc.BASE / 'analyse_contract_subsets.py',
             bc.BASE / 'score_full_record.py', bc.BASE / 'query_features.py',
             bc.BASE / 'sql_schema_cards.json', bc.BASE / 'schema_cards.json',
             bc.BASE / 'build_relational_db.py']
    out = {
        'population': 'all released SpectraCQ-Core ids; no success-conditioned filtering',
        'n': len(ids), 'ids': ids, 'model': MODEL, 'gold': 'current repaired Core answer-column key',
        'scope_repaired_n': sum(row['scope_repaired'] for row in metadata.values()),
        'definition': {'normalization': 'bench_common.canon; collapse whitespace; casefold',
                       'answer_column': 'declared Core answer column, using retained predicted_values',
                       'f1': 'macro mean of per-item normalized unordered value-set F1',
                       'exact': 'normalized unordered value-set equality',
                       'duplicates_and_order': 'ignored within an answer set',
                       'missing_and_failed': 'explicit zero on every metric, included in the full denominator',
                       'duplicate_records': 'first record for each ID',
                       'n_scored': 'all fixed IDs, including explicit zero rows; query OK is counted separately',
                       'historical_metrics': 'stored primary_metrics/full_metrics in SQL logs are not used'},
        'arms': {'sql': sql_summary, 'cypher': cypher_summary},
        'sql_minus_cypher': {metric: round(sum(sql_scores[cid][metric] - cypher_scores[cid][metric]
                                              for cid in ids) / len(ids), 6) for metric in METRICS},
        'query_status_decomposition': groups,
        'items': [{'id': cid, **metadata[cid],
                   'sql': {metric: sql_scores[cid][metric] for metric in METRICS},
                   'cypher': {metric: cypher_scores[cid][metric] for metric in METRICS},
                   'sql_exec_status': sql.get(cid, {}).get('exec_status'),
                   'cypher_exec_status': cypher.get(cid, {}).get('exec_status')}
                  for cid in ids],
        'input_sha256': {relative_name(path): sha256(path) for path in sorted(set(paths))},
        'provenance_only_inputs': ['paper/baseline/sql_schema_cards.json',
                                   'paper/baseline/schema_cards.json', 'paper/baseline/build_relational_db.py'],
        'limits': [
            'This re-scores retained predictions; no new query, model or database execution occurs.',
            'The current repaired Core key does not establish that every original question requirement is graded.',
            'The recorded SQL database byte snapshot is not retained; hashing the loader and schema cards does not reconstruct it.',
            'The historical 325-item ID list and the reported 290 count are not reconstructed by this full-Core analysis.',
            'Only one shared model is compared. Query languages, prompts and recorded runs differ; this is not a controlled causal test of graph-engine benefit.',
            'Answer-column scoring does not grade other fields, full records, ranking or multiplicity.',
            'The CI resamples items without schema/template cluster or multiple-comparison adjustment.']}
    if ci:
        out['bootstrap'] = paired_interval([sql_scores[cid]['f1'] for cid in ids],
                                          [cypher_scores[cid]['f1'] for cid in ids],
                                          n_boot, seed, engine, batch_size)
    return out


def check_output(target, inputs):
    target = target.resolve()
    require(target not in {path.resolve() for path in inputs},
            'output must not overwrite a scoring source or input')
    require(not target.is_relative_to((bc.ROOT / 'release_package').resolve()),
            'write analysis results outside release datasets')


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--ci', action='store_true', help='add paired SQL-minus-Cypher item-bootstrap intervals')
    parser.add_argument('--n-boot', type=int, default=10000)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--bootstrap-engine', choices=('auto', 'numpy', 'python'), default='auto')
    parser.add_argument('--batch-size', type=int, default=128)
    parser.add_argument('--json', type=Path, help='write a neutral analysis result, leaving all sources unchanged')
    args = parser.parse_args()
    out = analyse(args.ci, args.n_boot, args.seed, args.bootstrap_engine, args.batch_size)
    if args.json:
        check_output(args.json, [bc.ROOT / name for name in out['input_sha256']])
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    sql, cypher = out['arms']['sql'], out['arms']['cypher']
    print(f'Core n={out["n"]} model={MODEL}; SQL F1={sql["metrics"]["f1"]:.6f} '
          f'exact={sql["metrics"]["exact"]:.6f}; Cypher F1={cypher["metrics"]["f1"]:.6f} '
          f'exact={cypher["metrics"]["exact"]:.6f}')
    print(f'SQL query OK={sql["n_query_ok"]} error={sql["n_query_error"]} missing={sql["n_missing"]}; '
          f'Cypher query OK={cypher["n_query_ok"]} error={cypher["n_query_error"]} missing={cypher["n_missing"]}')
    if args.ci:
        print(f'SQL minus Cypher F1={out["sql_minus_cypher"]["f1"]:.6f}; '
              f'paired CI95={out["bootstrap"]["sql_minus_cypher_f1_ci95"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
