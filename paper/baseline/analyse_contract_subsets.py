#!/usr/bin/env python3
"""Offline reanalysis of annotation-selected Core subsets and scoring sensitivity.

Read the released keys, demand annotations, run logs and retained full-record
replays. No model calls, graph connection, query execution or input writes occur.
Annotation membership is not an expert validation of the question's meaning.

The optional CI uses the recorded paired item-bootstrap protocol: Random(0),
10,000 resamples, common item draws for every model/metric/text run, and best of
the original 18 text runs reselected within each resample. Text is scored on the
Core answer column throughout. Rebuilt retrieval runs have no retained item
outputs here and are not substituted for those 18 runs.
"""
import argparse
import hashlib
import itertools
import json
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path

import bench_common as bc
import query_features as qf
import score_core as sc
import score_full_record as sf
from score import norm, score_row

CQ = bc.ROOT / 'release_package/cqs/spectra_cq_v2.0'
RECORD_TYPES = {'tuple_set', 'mapping'}
DEMAND_FLAGS = {'question_names_extra_columns', 'mapping_answer'}
RULES = ('S', 'P', 'C')
SCORERS = ('answer_column', *(f'full_record_{r}' for r in RULES),
           *(f'declared_type_{r}' for r in RULES))
TEXT_CONDITIONS = ('closed_book', 'rag')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_jsonl(path):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    headers = [r['_header'] for r in rows if '_header' in r]
    body = [r for r in rows if '_header' not in r]
    require(len({r['id'] for r in body}) == len(body), f'duplicate ids: {path}')
    return (headers[0] if headers else {}), {r['id']: r for r in body}


def is_lm(method):
    return method == 'language_model' or method.startswith('language_model:')


def derive_subsets(core, contracts, provenance):
    """Reproduce column-identity selection, conditional on the stored demand list.

    D is the set of stored required columns; S is the scored answer column.
    No natural-language demand inference is performed by this function.
    """
    require(set(core) == set(contracts) == {i for i, p in provenance.items() if p['core']},
            'Core, contract and provenance ids disagree')
    lower, recorded, upper, rule_only = [], [], [], []
    for cid in sorted(core):
        contract, prov = contracts[cid], provenance[cid]
        columns = prov['columns']
        names = [c['column'] for c in columns]
        require([c['index'] for c in columns] == list(range(len(columns)))
                and len(names) == len(set(names)), f'invalid column identities: {cid}')
        scored = {core[cid]['answer_column']}
        require(contract['answer_columns'][0] in scored and scored <= set(names),
                f'answer-column key/contract mismatch: {cid}')
        flags = set(contract['contract_flags'])
        other_flags = bool(flags - DEMAND_FLAGS)
        demanded = {c['column'] for c in columns if c['verdict'] == 'required'}
        rule_demand = {c['column'] for c in columns
                       if c['verdict'] == 'required' and not is_lm(c['method'])}
        lm_columns = {c['column'] for c in columns if is_lm(c['method'])}
        phrases = bool(prov.get('phrases'))
        if not other_flags and demanded <= scored:
            recorded.append(cid)
            if not lm_columns and not phrases:
                rule_only.append(cid)
        if not other_flags and not phrases and (rule_demand | lm_columns) <= scored:
            lower.append(cid)
        if not other_flags and rule_demand <= scored:
            upper.append(cid)
    require(set(rule_only) <= set(lower) <= set(recorded) <= set(upper),
            'annotation subset nesting failed')
    later = [r for r in provenance.values()
             if any(c['index'] >= 1 and c['verdict'] == 'required' for c in r['columns'])]
    first_verdict = Counter(r['columns'][0]['verdict'] for r in later)
    return {'annotation_lower_133': lower, 'annotation_recorded_208': recorded,
            'annotation_rule_only_132': rule_only}, {
        'lower_n': len(lower), 'recorded_n': len(recorded), 'upper_n': len(upper),
        'rule_only_n': len(rule_only), 'upper_ids': upper,
        'bound_scope': 'stored column universe, rule verdicts and other flags fixed; language-model column/phrase judgments varied',
        'semantic_validation': False,
        'later_required_column_all_released': {
            'n': len(later), 'first_column_verdicts': dict(sorted(first_verdict.items())),
            'definition': 'at least one column after index 0 has a recorded required verdict; '
                          'does not assert that the scored first column is wrong'},
        'record_typed_in_lower': sum(contracts[i]['answer_type'] in RECORD_TYPES for i in lower),
        'record_typed_in_recorded': sum(contracts[i]['answer_type'] in RECORD_TYPES for i in recorded)}


def row_p(row):
    return tuple(norm(v) for v in row)


def matching_permutations(pred_row, gold_row):
    """Column permutations making one normalized row equal; duplicates retained."""
    available = {}
    for j, value in enumerate(pred_row):
        available.setdefault(value, []).append(j)

    def visit(position, used, perm):
        if position == len(gold_row):
            yield tuple(perm)
            return
        for j in available.get(gold_row[position], ()):
            if j not in used:
                yield from visit(position + 1, used | {j}, perm + [j])
    yield from visit(0, set(), [])


def score_records(rows, ncol, gold_p, gold_ncol):
    """S: value bag per row; P: positions; C: one gold-oracle column permutation.

    C applies one permutation to *all* rows of a model/item, never a different
    permutation for each row. Candidate permutations need only include those
    matching some row; every permutation with positive overlap is therefore
    considered. All three rules ignore outer row order and duplicate rows.
    """
    require(all(len(row) == ncol for row in rows), 'replay row/column width mismatch')
    pred_p = {row_p(row) for row in rows}
    pred_s = {tuple(sorted(row)) for row in pred_p}
    gold_s = {tuple(sorted(row)) for row in gold_p}
    out = {'S': sf.score_sets(pred_s, gold_s), 'P': sf.score_sets(pred_p, gold_p)}
    out['C'] = dict(out['P'])
    if ncol == gold_ncol and ncol >= 2 and pred_p and gold_p and out['P']['exact'] != 1:
        best = len(pred_p & gold_p)
        by_bag = {}
        for row in gold_p:
            by_bag.setdefault(tuple(sorted(row)), []).append(row)
        seen = set()
        done = False
        for pred_row in sorted(pred_p):
            for gold_row in sorted(by_bag.get(tuple(sorted(pred_row)), ())):
                for perm in matching_permutations(pred_row, gold_row):
                    if perm in seen:
                        continue
                    seen.add(perm)
                    candidate = {tuple(row[j] for j in perm) for row in pred_p}
                    intersection = len(candidate & gold_p)
                    if intersection > best:
                        best = intersection
                        out['C'] = sf.score_sets(candidate, gold_p)
                    if best == min(len(pred_p), len(gold_p)):
                        done = True
                        break
                if done:
                    break
            if done:
                break
    collapse = len(pred_s) != len(pred_p) or len(gold_s) != len(gold_p)
    require(out['P']['f1'] <= out['C']['f1'] + 1e-12, 'P <= C invariant failed')
    require(collapse or out['C']['f1'] <= out['S']['f1'] + 1e-12,
            'C <= S invariant failed on a non-collapsing pair')
    return out, collapse


def ranks(values):
    """Descending average ranks, including ties."""
    ordered = sorted(values, key=lambda m: (-values[m], m))
    out = {}
    k = 0
    while k < len(ordered):
        end = k + 1
        while end < len(ordered) and values[ordered[end]] == values[ordered[k]]:
            end += 1
        rank = (k + 1 + end) / 2
        for m in ordered[k:end]:
            out[m] = rank
        k = end
    return out


def rank_agreement(values, reference):
    r, s = ranks(values), ranks(reference)
    models = sorted(values)
    mean_r = sum(r.values()) / len(r)
    mean_s = sum(s.values()) / len(s)
    numerator = sum((r[m] - mean_r) * (s[m] - mean_s) for m in models)
    denominator = math.sqrt(sum((r[m] - mean_r) ** 2 for m in models)
                            * sum((s[m] - mean_s) ** 2 for m in models))
    concordant = discordant = ties_r = ties_s = 0
    for a, b in itertools.combinations(models, 2):
        x, y = r[a] - r[b], s[a] - s[b]
        if x == y == 0:
            continue
        if x == 0:
            ties_r += 1
        elif y == 0:
            ties_s += 1
        elif x * y > 0:
            concordant += 1
        else:
            discordant += 1
    tau_denom = math.sqrt((concordant + discordant + ties_r)
                         * (concordant + discordant + ties_s))
    return {'spearman': round(numerator / denominator, 6) if denominator else None,
            'kendall_tau_b': round((concordant - discordant) / tau_denom, 6) if tau_denom else None,
            'models_changing_rank': sum(r[m] != s[m] for m in models),
            'ranks': r, 'core_ranks': s}


def interval(values):
    ordered = sorted(float(v) for v in values)
    n = len(ordered)
    return [round(ordered[int(.025 * n)], 6), round(ordered[int(.975 * n) - 1], 6)]


def paired_bootstrap(graph, text, n_boot=10000, seed=0, engine='auto', batch_size=128):
    """Shared Random(seed) item draws; fixed and resample-reselected text bars.

    Endpoints are rounded to six decimals before strict exclusion of zero, as
    in the recorded protocol. Intervals are individual comparisons, with no
    family-wise correction or cluster-dependence adjustment.
    """
    require(n_boot >= 40 and batch_size >= 1, 'need >=40 draws and a positive batch size')
    labels = [(scorer, model) for scorer in sorted(graph) for model in sorted(graph[scorer])]
    text_labels = sorted(text)
    vectors = [graph[s][m] for s, m in labels] + [text[k] for k in text_labels]
    n = len(vectors[0])
    require(n > 0 and all(len(v) == n for v in vectors), 'bootstrap input lengths disagree')
    np = None
    if engine in ('auto', 'numpy'):
        try:
            import numpy as np
        except ImportError:
            if engine == 'numpy':
                raise
    actual_engine = 'numpy' if np is not None else 'python'
    rng = random.Random(seed)
    boots = [[] for _ in vectors]
    if np is not None:
        matrix = np.asarray(vectors, dtype=float)
    for start in range(0, n_boot, batch_size):
        count = min(batch_size, n_boot - start)
        draws = [[rng.randrange(n) for _ in range(n)] for _ in range(count)]
        if np is not None:
            idx = np.asarray(draws, dtype=np.int32)
            # One vector at a time bounds the temporary array by batch_size*n.
            for k, row in enumerate(matrix):
                boots[k].extend(row[idx].mean(axis=1).tolist())
        else:
            for k, row in enumerate(vectors):
                boots[k].extend(sum(row[j] for j in draw) / n for draw in draws)
    text_boots = boots[len(labels):]
    text_means = [sum(text[k]) / n for k in text_labels]
    fixed_index = max(range(len(text_labels)), key=lambda k: text_means[k])
    comparators = {'fixed': text_boots[fixed_index],
                   'reselected': [max(values) for values in zip(*text_boots)]}
    by_scorer = {}
    for scorer in sorted(graph):
        model_boots = {m: boots[labels.index((scorer, m))] for m in sorted(graph[scorer])}
        pooled = [sum(values) / len(model_boots) for values in zip(*model_boots.values())]
        pairs = {}
        for a, b in itertools.combinations(sorted(model_boots), 2):
            pairs[f'{a} - {b}'] = interval(x - y for x, y in zip(model_boots[a], model_boots[b]))
        result = {'model_f1_ci95': {m: interval(v) for m, v in model_boots.items()},
                  'pooled_f1_ci95': interval(pooled), 'model_pair_difference_ci95': pairs,
                  'model_pairs_separated': sum(lo > 0 or hi < 0 for lo, hi in pairs.values())}
        for name, comparator in comparators.items():
            model_ci = {m: interval(x - y for x, y in zip(values, comparator))
                        for m, values in model_boots.items()}
            result[name] = {
                'model_minus_text_ci95': model_ci,
                'pooled_minus_text_ci95': interval(x - y for x, y in zip(pooled, comparator)),
                'models_clear': sum(lo > 0 for lo, _ in model_ci.values()),
                'models_below': sum(hi < 0 for _, hi in model_ci.values()),
                'minimum_lower_bound': min(lo for lo, _ in model_ci.values()),
                'text_bar_ci95': interval(comparator)}
        by_scorer[scorer] = result
    return {'n_boot': n_boot, 'seed': seed, 'generator': 'random.Random.randrange',
            'engine': actual_engine, 'endpoint_rule': 'sorted[ floor(.025*B) ], sorted[ floor(.975*B)-1 ]; round 6',
            'clear_rule': 'rounded lower > 0; below iff rounded upper < 0',
            'unit': 'item; common draw across models, scorers and text arms',
            'fixed_text_run': text_labels[fixed_index], 'scores': by_scorer}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(paths):
    return {str(p.relative_to(bc.ROOT)): sha256(p) for p in sorted(set(paths))}


def load_ids(path, core):
    """Read a pre-fixed external selection without inferring or changing it."""
    raw = path.read_bytes()
    ids = raw.decode('utf-8').split()
    require(bool(ids), 'external ID file is empty')
    require(len(ids) == len(set(ids)), 'external ID file contains duplicate ids')
    unknown = sorted(set(ids) - set(core))
    require(not unknown, f'external ID file has unknown/non-Core ids: {unknown[:5]}')
    return sorted(ids), {'filename': path.name, 'sha256': hashlib.sha256(raw).hexdigest(),
                         'n': len(ids), 'item_order': 'sorted id',
                         'selection_scope': 'supplied membership; this tool does not validate its semantic labels'}


def extreme_mean(values, lower, upper, maximize=False):
    """Exact extreme over lower <= selected <= upper, by sorted prefix search.

    For each possible selected-set size, the smallest/largest optional values
    minimize/maximize its numerator. Searching all prefix sizes therefore gives
    the global extreme, without assuming that the selected set is the upper set.
    This is sensitivity analysis; it does not choose the headline population.
    """
    optional = sorted(set(upper) - set(lower), key=lambda i: (values[i], i), reverse=maximize)
    total, n = sum(values[i] for i in lower), len(lower)
    require(n > 0 and set(lower) <= set(upper), 'invalid nonempty bound sets')
    best_value, best_k = total / n, 0
    for k, cid in enumerate(optional, 1):
        total += values[cid]
        value = total / (n + k)
        better = value > best_value if maximize else value < best_value
        if better:
            best_value, best_k = value, k
    return best_value, sorted(list(lower) + optional[:best_k])


def annotation_mean_bounds(data):
    lower = data['subsets']['annotation_lower_133']
    upper = data['selection']['upper_ids']
    arms = data['graph']['answer_column']
    models = sorted(arms)
    pooled = {i: sum(arms[m][i] for m in models) / len(models) for i in upper}
    low, _ = extreme_mean(pooled, lower, upper)
    high, _ = extreme_mean(pooled, lower, upper, maximize=True)
    text_max = max(extreme_mean(v, lower, upper, maximize=True)[0] for v in data['text'].values())
    pair_minima, pooled_minima = {}, {}
    for run, text in data['text'].items():
        pooled_minima[run] = extreme_mean({i: pooled[i] - text[i] for i in upper}, lower, upper)[0]
        for model in models:
            difference = {i: arms[model][i] - text[i] for i in upper}
            value, _ = extreme_mean(difference, lower, upper)
            pair_minima[f'{model} - {run}'] = value
    return {'scope': 'answer-column means over every set between the annotation-derived lower and upper; stored rule verdicts and column universe fixed',
            'not_a_semantic_validity_bound': True, 'n_range': [len(lower), len(upper)],
            'free_items': len(upper) - len(lower),
            'pooled_f1_range': [round(low, 6), round(high, 6)],
            'best_original_text_f1_max': round(text_max, 6),
            'model_text_pairs': len(pair_minima),
            'model_text_pairs_positive_in_every_set': sum(v > 0 for v in pair_minima.values()),
            'worst_model_minus_text_mean': round(min(pair_minima.values()), 6),
            'worst_pooled_minus_text_mean': round(min(pooled_minima.values()), 6)}


def load_inputs():
    paths = [Path(__file__), Path(qf.__file__), Path(sc.__file__), Path(sf.__file__),
             bc.BASE / 'score.py', Path(bc.__file__), CQ / 'core_answer_gold.jsonl',
             CQ / 'answer_contract.jsonl', CQ / 'contract_demand_provenance.jsonl',
             CQ / 'benchmark.jsonl', CQ / 'splits/track_assignment.json',
             CQ / 'splits/contract_exact_script_fixed_133.txt',
             CQ / 'splits/contract_exact_asked_208.txt',
             CQ / 'splits/contract_exact_rule_only_149.txt',
             bc.ROOT / 'release_package/ontology/spectra.ttl']
    run_files = [(c, m, p) for c, m, p in sc.iter_runs(bc.BASE / 'results')
                 if c in ('kg_grounded', *TEXT_CONDITIONS)]
    paths.extend(p for _, _, p in run_files)
    paths.extend(CQ / 'gold' / f'{wg}_gold.json' for wg in sf.WGS)
    paths.extend(sf.REPLAY / f'{wg}.jsonl.gz' for wg in sf.WGS)
    before = manifest(paths)
    core = sf.read_core(CQ)
    _, contracts = read_jsonl(CQ / 'answer_contract.jsonl')
    _, provenance = read_jsonl(CQ / 'contract_demand_provenance.jsonl')
    _, benchmark = read_jsonl(CQ / 'benchmark.jsonl')
    subsets, selection = derive_subsets(core, contracts, provenance)
    for public_name, name in [('contract_exact_script_fixed_133', 'annotation_lower_133'),
                              ('contract_exact_asked_208', 'annotation_recorded_208')]:
        require(set((CQ / 'splits' / f'{public_name}.txt').read_text().split()) == set(subsets[name]),
                f'derived membership differs from shipped {public_name}')
    old_rule = set((CQ / 'splits/contract_exact_rule_only_149.txt').read_text().split())
    require(set(subsets['annotation_rule_only_132']) == old_rule & set(subsets['annotation_lower_133']),
            'rule-only intersection differs from stored old split')
    logs = sf.read_logs(sf.RUNS)
    models = sorted(logs)
    _, replay, refs = sf.read_replay(sf.REPLAY)
    expected = {(m, i) for m, recs in logs.items() for i, r in recs.items() if r.get('cypher')}
    require(set(replay) == expected, 'full-record replay query coverage differs from logs')
    require(all(sf.query_hash(logs[m][i]['cypher']) == r['query_sha256']
                for (m, i), r in replay.items()), 'full-record replay query hash differs from log')
    key = sc.load_key(CQ, 'repaired')
    require(set(key) == set(core), 'answer-column key ids differ from Core')
    gold_p, gold_width = {}, {}
    for wg in sf.WGS:
        for entry in json.loads((CQ / 'gold' / f'{wg}_gold.json').read_text())['gold']:
            cid = f"{entry['wg']}_P{entry['phase']}_{entry['id']}"
            require(all(list(row) == entry['columns'] for row in entry['rows']),
                    f'gold dictionary key order differs from columns: {cid}')
            gold_p[cid] = {row_p(row.values()) for row in entry['rows']}
            gold_width[cid] = len(entry['columns'])
    repaired = []
    for cid, row in core.items():
        if row.get('repaired_cypher'):
            ref = refs.get(('repaired_query', cid))
            require(ref is not None and ref['status'] == 'OK' and not ref['row_capped']
                    and ref['query_sha256'] == sf.query_hash(row['repaired_cypher']),
                    f'no usable repaired reference replay: {cid}')
            require(all(len(r) == len(ref['columns']) for r in ref['rows']),
                    f'repaired gold width mismatch: {cid}')
            gold_p[cid] = {row_p(r) for r in ref['rows']}
            gold_width[cid] = len(ref['columns'])
            repaired.append(cid)
    require(set(core) <= set(gold_p), 'full-record gold does not cover Core')
    graph = {s: {m: {} for m in models} for s in SCORERS}
    exact = {s: {m: {} for m in models} for s in SCORERS}
    diagnostics = Counter()
    differences = {'S_vs_P': [], 'S_vs_C': [], 'C_vs_P': []}
    for model in models:
        for cid in sorted(core):
            diagnostics['core_model_item_pairs'] += 1
            ac = score_row(logs[model][cid].get('predicted_values'), key[cid]['values']) \
                if cid in logs[model] else dict.fromkeys(sf.METRICS, 0.0)
            r = replay.get((model, cid))
            if r is not None and r['status'] == 'OK':
                diagnostics['executed_pairs'] += 1
                full, collapse = score_records(r['rows'], len(r['columns']), gold_p[cid], gold_width[cid])
                diagnostics['row_bag_collapse_pairs'] += collapse
                diagnostics['same_width_pairs'] += len(r['columns']) == gold_width[cid]
                diagnostics['multi_column_same_width_pairs'] += len(r['columns']) == gold_width[cid] >= 2
                diagnostics['noncollapsing_C_ne_S_observed'] += not collapse and full['C']['f1'] != full['S']['f1']
                for label, a, b in [('S_vs_P', 'S', 'P'), ('S_vs_C', 'S', 'C'), ('C_vs_P', 'C', 'P')]:
                    if full[a]['f1'] != full[b]['f1']:
                        differences[label].append({'model': model, 'id': cid})
            else:
                full = {rule: dict.fromkeys(sf.METRICS, 0.0) for rule in RULES}
            graph['answer_column'][model][cid], exact['answer_column'][model][cid] = ac['f1'], ac['exact']
            for rule in RULES:
                f = full[rule]
                typed = f if contracts[cid]['answer_type'] in RECORD_TYPES else ac
                graph[f'full_record_{rule}'][model][cid] = f['f1']
                exact[f'full_record_{rule}'][model][cid] = f['exact']
                graph[f'declared_type_{rule}'][model][cid] = typed['f1']
                exact[f'declared_type_{rule}'][model][cid] = typed['exact']
    text = {}
    for condition, model, path in run_files:
        if condition in TEXT_CONDITIONS:
            predictions = sc.read_predictions(path)
            text[f'{condition}/{model}'] = {
                cid: score_row(predictions[cid], key[cid]['values'])['f1'] if cid in predictions else 0.0
                for cid in core}
    require(set(text) == {f'{condition}/{m}' for condition in TEXT_CONDITIONS for m in models},
            'expected one original text arm per condition and graph model')
    diagnostics['retained_query_replays'] = len(replay)
    diagnostics['repaired_reference_items'] = len(repaired)
    diagnostics['original_text_arms'] = len(text)
    diagnostics['graph_models'] = len(models)
    track = json.loads((CQ / 'splits/track_assignment.json').read_text())
    require(set(core) <= set(track), 'track assignment does not cover Core')
    return {'core': core, 'contract': contracts, 'benchmark': benchmark, 'subsets': subsets,
            'selection': selection, 'graph': graph, 'exact': exact, 'text': text, 'track': track,
            'diagnostics': dict(diagnostics), 'scoring_differences': differences,
            'paths': paths, 'manifest': before}


def populations(data, scope):
    core = sorted(data['core'])
    out = {'Core_560': core}
    if scope in ('headline', 'all', 'tracks', 'groups', 'composition'):
        out.update(data['subsets'])
    if scope in ('typed', 'all'):
        out['declared_record_141'] = [i for i in core if data['contract'][i]['answer_type'] in RECORD_TYPES]
        for answer_type in sorted(RECORD_TYPES):
            out[f'declared_{answer_type}'] = [i for i in core if data['contract'][i]['answer_type'] == answer_type]
    if scope in ('tracks', 'all'):
        for name in ('annotation_lower_133', 'annotation_recorded_208'):
            for track in ('lookup', 'aggregation', 'relational', 'multihop'):
                out[f'{name}/track/{track}'] = [i for i in out[name] if data['track'][i] == track]
    if scope in ('groups', 'all'):
        for name in ('annotation_lower_133', 'annotation_recorded_208'):
            for wg in sf.WGS:
                out[f'{name}/group/{wg}'] = [i for i in out[name] if data['core'][i]['wg'] == wg]
    composition = {}
    if scope in ('composition', 'all'):
        process = {'Resolution', 'Agreement', 'Conclusion', 'WorkingAssumption', 'LS', 'Meeting', 'AgendaItem'}
        partial = {'submittedby', 'references', 'modifiessection'}
        def canonical(value):
            return value.replace('_', '').lower()
        features = {}
        for cid in data['subsets']['annotation_lower_133']:
            released = data['benchmark'][cid]['cypher']
            repaired = data['core'][cid].get('repaired_cypher', released)
            triples = qf.parse_patterns(released)
            relations = {canonical(r) for r in qf.rel_types(repaired)}
            features[cid] = {'pattern_edges_ge_2': len(triples) >= 2,
                             'pattern_edges_ge_3': len(triples) >= 3,
                             'process_record': bool(qf.node_labels(released) & process),
                             'partial_relation_yes': bool(relations & partial),
                             'partial_relation_no': not bool(relations & partial),
                             'CR_clause_link': 'modifiessection' in {canonical(r) for r in qf.rel_types(released)}}
        for feature in ('pattern_edges_ge_2', 'pattern_edges_ge_3', 'process_record',
                        'partial_relation_yes', 'partial_relation_no'):
            out[f'annotation_lower_133/composition/{feature}'] = [i for i in sorted(features) if features[i][feature]]
        ontology = (bc.ROOT / 'release_package/ontology/spectra.ttl').read_text()
        composition = {'scope': 'annotation_lower_133', 'CR_clause_link_items': sum(f['CR_clause_link'] for f in features.values()),
                       'ontology_object_properties': len(re.findall(r'^spectra:([A-Za-z0-9_]+) a owl:ObjectProperty\b', ontology, re.M)),
                       'query_source': 'released query for pattern edges/process/CR link; repaired-if-present for partial relations',
                       'feature_method': 'regex surface features; not an execution or semantic validator'}
    return out, composition


def point_summary(data, ids, reference):
    n = len(ids)
    text = {k: sum(v[i] for i in ids) / n for k, v in data['text'].items()}
    best = max(sorted(text), key=text.get)
    graph = {}
    for scorer, arms in data['graph'].items():
        raw = {m: sum(values[i] for i in ids) / n for m, values in arms.items()}
        rounded = {m: round(v, 6) for m, v in raw.items()}
        # The recorded full-record rank tables used six-decimal model means.
        rank_values = rounded if scorer.startswith('full_record_') else raw
        rank_ref = reference[scorer]
        graph[scorer] = {
            'model_f1': rounded,
            'model_exact': {m: round(sum(data['exact'][scorer][m][i] for i in ids) / n, 6) for m in arms},
            'pooled_f1': round(sum(raw.values()) / len(raw), 6),
            'pooled_exact': round(sum(data['exact'][scorer][m][i] for m in arms for i in ids) / (n * len(arms)), 6),
            'pooled_from_rounded_model_means': round(sum(rounded.values()) / len(raw), 6),
            'minimum_model_f1': round(min(raw.values()), 6), 'maximum_model_f1': round(max(raw.values()), 6),
            'models_point_above_best_text': sum(v > text[best] for v in raw.values()),
            'minimum_point_gap_to_best_text': round(min(raw.values()) - text[best], 6),
            'minimum_point_gap_from_rounded_means': round(min(rounded.values()) - round(text[best], 6), 6),
            'rank_agreement_with_same_scorer_Core': rank_agreement(rank_values, rank_ref)}
    conditions = {condition: round(sum(v for k, v in text.items() if k.startswith(condition + '/')) /
                                   sum(k.startswith(condition + '/') for k in text), 6)
                  for condition in TEXT_CONDITIONS}
    return {'n': n, 'record_typed_items': sum(data['contract'][i]['answer_type'] in RECORD_TYPES for i in ids),
            'ids': ids, 'best_original_text': {'run': best, 'answer_column_f1': round(text[best], 6)},
            'original_text_model_f1': {k: round(v, 6) for k, v in text.items()},
            'original_text_condition_mean_f1': conditions, 'scores': graph}


def analyse(scope='headline', ci=False, n_boot=10000, seed=0, engine='auto', batch_size=128, ids_path=None):
    data = load_inputs()
    external = None
    if ids_path is not None:
        ids, external = load_ids(ids_path, data['core'])
        pops, composition, scope = {'external_subset': ids}, {}, 'external_subset'
    else:
        pops, composition = populations(data, scope)
    core = sorted(data['core'])
    reference = {}
    for scorer, arms in data['graph'].items():
        means = {m: sum(v[i] for i in core) / len(core) for m, v in arms.items()}
        reference[scorer] = {m: round(v, 6) for m, v in means.items()} if scorer.startswith('full_record_') else means
    results = {}
    for name, ids in pops.items():
        require(bool(ids), f'population is empty: {name}')
        print(f'analysing {name}: n={len(ids)}' + (' (paired CI)' if ci else ''), file=sys.stderr, flush=True)
        result = point_summary(data, ids, reference)
        if ci:
            graph = {s: {m: [v[i] for i in ids] for m, v in arms.items()} for s, arms in data['graph'].items()}
            text = {k: [v[i] for i in ids] for k, v in data['text'].items()}
            result['bootstrap'] = paired_bootstrap(graph, text, n_boot, seed, engine, batch_size)
        results[name] = result
    require(manifest(data['paths']) == data['manifest'], 'an input or scoring source changed during analysis')
    require(external is None or sha256(ids_path) == external['sha256'], 'external ID file changed during analysis')
    return {'schema': 'spectra-contract-subsets-v1', 'scope': scope, 'offline_only': True,
            'input_sha256': data['manifest'], 'selection': data['selection'],
            'external_subset_input': external,
            'annotation_mean_bounds': annotation_mean_bounds(data),
            'integrity': data['diagnostics'], 'scoring_differences': data['scoring_differences'],
            'composition': composition, 'populations': results,
            'metric_definitions': {
                'answer_column': 'normalized value-set F1 against the declared Core answer-column key',
                'full_record_S': 'set of rows; each row is the sorted tuple of normalized values, ignoring column roles',
                'full_record_P': 'set of normalized row tuples in RETURN column positions; no column-name matching',
                'full_record_C': 'gold-oracle maximum set overlap with one common column permutation per model/item; C=P if widths differ',
                'declared_type_S/P/C': 'full_record rule for declared tuple_set/mapping items; answer_column for all other declared types',
                'text': 'answer-column scoring of the original closed_book/rag logs; not rebuilt retrieval',
                'pooled': 'unweighted average across model/item pairs; pooled_from_rounded_model_means also reports rounded-model aggregation',
                'point_gap': 'minimum_point_gap_to_best_text uses unrounded means; minimum_point_gap_from_rounded_means subtracts six-decimal means',
                'rank': 'same scorer versus Core; full_record model means rounded to six decimals before ranking; average ties'},
            'limits': [
                'Stored demand annotations are not independent expert validation; membership does not guarantee every requested field/value is scored.',
                'All row-set rules ignore row ranking, order, ties and duplicate-row multiplicity. Nested values retain the existing normalization.',
                'C uses the gold as an alignment oracle and is a sensitivity measure, not a deployable prediction method.',
                'C=S and matching clear-model counts, if observed, are dataset findings rather than universal correctness invariants.',
                'CI resamples items, assumes that unit is appropriate, and applies no cluster-dependence or family-wise correction.',
                'Best-text reselection is over the original 18 arms; no retained per-item rebuilt retrieval outputs are available here.',
                'Missing predictions and failed/missing query replays score zero over the whole selected population.']}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--scope', choices=('headline', 'typed', 'tracks', 'groups', 'composition', 'all'), default='headline')
    ap.add_argument('--ci', action='store_true', help='add paired item intervals and fixed/reselected original-text comparisons')
    ap.add_argument('--n-boot', type=int, default=10000)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--bootstrap-engine', choices=('auto', 'numpy', 'python'), default='auto')
    ap.add_argument('--batch-size', type=int, default=128, help='bound resample working memory')
    ap.add_argument('--ids', type=Path, help='analyze only these pre-fixed Core ids, sorted internally; overrides --scope; empty/duplicate/unknown ids rejected')
    ap.add_argument('--json', type=Path, help='write a neutral analysis artifact (input files remain unchanged)')
    a = ap.parse_args()
    require(not a.json or not a.ids or a.json.resolve() != a.ids.resolve(), 'output must not overwrite the external ID input')
    out = analyse(a.scope, a.ci, a.n_boot, a.seed, a.bootstrap_engine, a.batch_size, a.ids)
    if a.json:
        target = a.json.resolve()
        require(target not in {(bc.ROOT / name).resolve() for name in out['input_sha256']},
                'output must not overwrite a scoring source or input file')
        require(not target.is_relative_to((bc.ROOT / 'release_package').resolve()),
                'write analysis results outside the release datasets')
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    for name, result in out['populations'].items():
        scorer = 'full_record_S' if name.startswith('declared_') else 'answer_column'
        score = result['scores'][scorer]['pooled_f1']
        best = result['best_original_text']['answer_column_f1']
        tail = ''
        if a.ci:
            comparison = result['bootstrap']['scores'][scorer]['reselected']
            tail = f" clear={comparison['models_clear']} below={comparison['models_below']}"
        print(f'{name}: n={result["n"]} {scorer}={score:.6f} best_original_text={best:.6f}{tail}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
