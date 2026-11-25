#!/usr/bin/env python3
"""Independent candidate, Python gold/mutant and SQLite replay verification.

Imports neither measure.py nor the original task builder or gold functions.
Only the specified output file is written; databases are opened read only.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import re
import sqlite3
import sys
import time


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def norm(rows):
    return sorted({tuple(None if c is None else str(c) for c in r) for r in rows})


def rows_json(rows):
    return [list(r) for r in rows]


def load_raw(con):
    members, multiplicity, links = defaultdict(set), Counter(), defaultdict(set)
    for doc, pack in con.execute('SELECT cr,pack_id FROM cr_in_pack'):
        members[pack].add(doc)
        multiplicity[pack, doc] += 1
    sections = {i: (s, r, c) for i, s, r, c in con.execute('SELECT id,spec,release,clause FROM section')}
    for doc, section in con.execute('SELECT cr,section_id FROM cr_modifies_section'):
        links[doc].add(sections[section])
    meetings = dict(con.execute('SELECT id,meeting_id FROM resolution'))
    outcomes = [(doc, code, meetings[res]) for doc, code, res in con.execute(
        "SELECT target,code,resolution_id FROM disposition WHERE evidence_status='source_verified' AND scope='whole_target'")]
    by_doc = defaultdict(list)
    for doc, code, meeting in outcomes:
        by_doc[doc].append((code, meeting))
    return dict(members=members, multiplicity=multiplicity, links=links,
                outcomes=outcomes, by_doc=by_doc)


class Fingerprints:
    def __init__(self, salt, wg):
        self.salt, self.wg = salt, wg
        self.counts, self.sums, self.xors, self.best = Counter(), defaultdict(int), defaultdict(int), {}

    def add(self, stratum, candidate):
        # Count plus two cryptographic commutative fingerprints validate the
        # entire candidate multiset independently of file enumeration order.
        key = canon(candidate)
        number = int(hashlib.sha256(key.encode()).hexdigest(), 16)
        self.counts[stratum] += 1
        self.sums[stratum] = (self.sums[stratum] + number) % (1 << 256)
        self.xors[stratum] ^= number
        rank = (hashlib.sha256(canon([self.salt, self.wg, stratum, candidate]).encode()).hexdigest(), key)
        if stratum not in self.best or rank < self.best[stratum][0]:
            self.best[stratum] = (rank, json.loads(key))


def reconstruct_candidates(data, salt, wg):
    pool = Fingerprints(salt, wg)
    members, links = data['members'], data['links']
    meetings = {meeting for _, _, meeting in data['outcomes']}
    for kind, cohorts in [('pack', members), ('meeting', meetings)]:
        for cohort in cohorts:
            for suffix in ('multicode', 'duplicates', 'multicode_duplicates'):
                pool.add(kind + '_' + suffix, [kind, cohort])
    for pack, docs in members.items():
        sharing = defaultdict(set)
        for doc in docs:
            for section in links[doc]:
                sharing[section].add(doc)
        pairs = set()
        for peers in sharing.values():
            pairs.update(itertools.combinations(sorted(peers), 2))
        for first, second in pairs:
            for s in ('intersection', 'intersection_release'):
                pool.add(s, [pack, first, second])
            for one, two in ((first, second), (second, first)):
                for s in ('difference', 'difference_release'):
                    pool.add(s, [pack, one, two])
        section_pairs = set()
        for doc in docs:
            section_pairs.update(itertools.combinations(sorted(links[doc]), 2))
        for first, second in section_pairs:
            for s in ('conjunction', 'conjunction_release', 'composition'):
                pool.add(s, [pack, first, second])
        for s in ('maximum_variation', 'maximum_ties', 'maximum_release_count',
                  'maximum_release_winner', 'maximum_ties_release', 'absence'):
            pool.add(s, [pack])
    return pool


def selected_documents(data, anchor, condition='both', release=True):
    pack, one, two = anchor
    one, two = tuple(one), tuple(two)
    result = set()
    for doc in data['members'][pack]:
        if release:
            a, b = one in data['links'][doc], two in data['links'][doc]
        else:
            short = {(s[0], s[2]) for s in data['links'][doc]}
            a, b = (one[0], one[2]) in short, (two[0], two[2]) in short
        keep = {'both': a and b, 'or': a or b, 'first_only': a, 'second_only': b}[condition]
        if keep:
            result.add(doc)
    return result


def grouped(data, docs=None, meeting=None, raw=False, pack=None):
    values = defaultdict(set)
    counts = Counter()
    for doc, code, meet in data['outcomes']:
        if (docs is None or doc in docs) and (meeting is None or meet == meeting):
            values[code].add(doc)
            counts[code] += data['multiplicity'][pack, doc] if pack is not None else 1
    return norm(counts.items() if raw else ((code, len(ds)) for code, ds in values.items()))


def expect(data, family, anchor, name='reference'):
    members, links = data['members'], data['links']
    if family == 'pack_disposition_counts':
        kind, cohort = anchor
        if name == 'omit_group_by':
            # SQLite intentionally leaves the ungrouped code column arbitrary.
            # Validate its relational constraints separately, then replay the
            # full SQL to check its exact snapshot-specific stored rowset.
            pairs = [(d, c) for d, c, m in data['outcomes']
                     if (d in members[cohort] if kind == 'pack' else m == cohort)]
            return {'arbitraryCode': {c for _, c in pairs}, 'count': str(len({d for d, _ in pairs}))}
        return grouped(data, docs=members[cohort] if kind == 'pack' else None,
                       meeting=cohort if kind == 'meeting' else None,
                       raw=name == 'count_star', pack=cohort if kind == 'pack' else None)
    if family in ('shared_clauses', 'exclusive_clauses'):
        _, one, two = anchor
        left, right = links[one], links[two]
        short_right = {(s[0], s[2]) for s in right}
        if name == 'reference':
            out = left & right if family == 'shared_clauses' else left - right
        elif name == 'union':
            out = left | right
        elif name == 'first_only':
            out = left
        elif name == 'second_only':
            out = right
        elif name == 'intersection':
            out = left & right
        elif name == 'reverse_difference':
            out = right - left
        elif name == 'release_blind_membership':
            out = {s for s in left if ((s[0], s[2]) in short_right) == (family == 'shared_clauses')}
        else:
            raise ValueError(name)
        return norm(out)
    if family in ('both_clause_documents', 'conjunction_disposition_counts'):
        if name == 'omit_section_filter':
            docs = members[anchor[0]]
        else:
            condition = {'or_before_grouping': 'or', 'reference': 'both',
                         'release_blind_membership': 'both'}.get(name, name)
            docs = selected_documents(data, anchor, condition, release=name != 'release_blind_membership')
        if family == 'both_clause_documents':
            return norm((doc.removeprefix('tdoc:'),) for doc in docs)
        return grouped(data, docs=docs)
    if family == 'largest_clause_footprint':
        counts = {doc: len(links[doc]) for doc in members[anchor[0]]}
        if name == 'release_collapsed_count':
            counts = {doc: len({(s[0], s[2]) for s in links[doc]}) for doc in counts}
        high = max(counts.values())
        docs = {d for d, n in counts.items() if n > 0} if name == 'all_positive' else {d for d, n in counts.items() if n == high}
        if name == 'limit_one':
            docs = {min(docs)}
        return norm((d.removeprefix('tdoc:'), counts[d]) for d in docs)
    if family == 'members_without_clause_records':
        docs = members[anchor[0]]
        if name != 'all_members':
            docs = {d for d in docs if bool(links[d]) == (name == 'exists')}
        return norm((d.removeprefix('tdoc:'),) for d in docs)
    raise ValueError(family)


def execute(con, sql):
    started = time.monotonic()
    con.set_progress_handler(lambda: time.monotonic() - started >= 60, 10000)
    try:
        return {'status': 'ok', 'rows': norm(con.execute(sql).fetchall())}
    except sqlite3.Error as exc:
        return {'status': 'timeout' if 'interrupted' in str(exc) else 'error', 'error': str(exc)}
    finally:
        con.set_progress_handler(None, 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--experiment', type=Path, required=True)
    ap.add_argument('--release', type=Path, required=True)
    ap.add_argument('--database-directory', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    begun = time.monotonic()
    checks = []

    def check(name, ok, **detail):
        checks.append({'name': name, 'ok': bool(ok), **detail})
        if not ok:
            raise AssertionError((name, detail))

    exp, release = args.experiment, args.release
    plan = json.loads((exp / 'protocol.json').read_text())
    stage1 = json.loads((exp / 'protocol_freeze.json').read_text())
    stage2 = json.loads((exp / 'measurement/selection_freeze.json').read_text())
    final = json.loads((exp / 'measurement/freeze.json').read_text())
    selection = json.loads((exp / 'measurement/selection.json').read_text())
    execution = json.loads((exp / 'measurement/execution.json').read_text())
    summary = json.loads((exp / 'measurement/summary.json').read_text())
    check('implementation_pin', digest(exp / 'measure.py') == plan['implementation_sha256'] == stage1['implementation_sha256'])
    check('protocol_pin', digest(exp / 'protocol.json') == stage1['protocol_sha256'] == stage2['protocol_sha256'] == final['protocol_sha256'])
    check('stage2_pre_execution_declaration', stage2['reference_executions_so_far'] == stage2['control_executions_so_far'] == 0)
    for name, expected in stage2['files'].items():
        check('selection_freeze:' + name, digest(exp / 'measurement' / name) == expected)
    for name, expected in final['files'].items():
        check('final_freeze:' + name, digest(exp / 'measurement' / name) == expected)
    original_study = release / 'studies/semantic_witnesses'
    for name, expected in plan['input_sha256'].items():
        check('original_input:' + name, digest(original_study / name) == expected)
    original = json.loads((original_study / 'measurement/selection_and_gold.json').read_text())
    old_tasks = {r['id']: r for r in original['items']}
    old_cells = {(r['wg'], r['stratum']): r for r in original['cells']}
    planned = {d['id']: set(d['mutations']) for d in plan['design']['original_strata']}
    cells = {(r['wg'], r['stratum']): r for r in selection['cells']}
    check('all95_cells', set(cells) == set(old_cells) and len(cells) == 95)
    unavailable = [r for r in cells.values() if r['comparison_status'] != 'paired']
    check('original29_unavailable_retained', len(unavailable) == 29 and all(
        r['original_status'] == 'unavailable' for r in unavailable))
    arms = execution['arms']
    arm_names = ['witness', 'hash_without_final_witness_predicates']
    by_arm = {a: {r['id']: r for r in arms[a]} for a in arm_names}
    check('same66_task_ids', len(by_arm['witness']) == 66 and set(by_arm['witness']) == set(by_arm[arm_names[1]]))
    for arm in arm_names:
        staged = {r['id']: r for r in selection['prepared_arms'][arm]}
        check(arm + ':all_staged_tasks_executed', set(staged) == set(by_arm[arm]))
        for identity, task in by_arm[arm].items():
            before = staged[identity]
            check(arm + ':' + identity + ':pre_execution_task_binding', all(
                task[k] == before[k] for k in ('id', 'wg', 'stratum', 'family', 'anchor', 'question',
                                               'fields', 'reference_sql', 'selection_sha256')) and
                  norm(task['gold']) == norm(before['independently_derived_gold']))
            check(arm + ':' + identity + ':pre_execution_control_binding',
                  sorted(c['name'] for c in task['controls']) == before['planned_control_names'] and
                  all(c['sql'] == before['mutations'][c['name']] for c in task['controls']))
    skeleton = lambda sql: re.sub(r"'(?:[^']|'')*'", '<literal>', sql)
    for identity, first in by_arm['witness'].items():
        second = by_arm[arm_names[1]][identity]
        check(identity + ':same_task_contract', all(first[k] == second[k] for k in ('wg', 'stratum', 'family', 'fields')))
        check(identity + ':original_witness_anchor', first['anchor'] == old_tasks[identity]['anchor'])
        one = {c['name']: c for c in first['controls']}
        two = {c['name']: c for c in second['controls']}
        check(identity + ':same_control_names', set(one) == set(two))
        check(identity + ':same_reference_skeleton', skeleton(first['reference_sql']) == skeleton(second['reference_sql']))
        for name in one:
            check(identity + ':' + name + ':matched_operator', skeleton(one[name]['sql']) == skeleton(two[name]['sql']) and
                  one[name]['required'] == two[name]['required'] == (name in planned[first['stratum']]))
    totals = {a: Counter() for a in arm_names}
    pairs, independent_baselines, outputs = Counter(), [], []
    for pin in plan['database_pins']:
        wg = pin['wg']
        database = args.database_directory / (wg + '.sqlite')
        source = release / 'sqlite' / (wg + '.sqlite')
        # The released semantic-witness checker expands only compressed
        # databases; RAN1 is already plain and is read from the release itself.
        if not database.exists() and source.is_file():
            database = source
        if not source.exists():
            source = source.with_suffix('.sqlite.gz')
        check(wg + ':database_pin', digest(database) == pin['database_sha256'] and digest(source) == pin['source_sha256'])
        con = sqlite3.connect('file:' + str(database.resolve()) + '?mode=ro&immutable=1', uri=True)
        con.execute('PRAGMA query_only=ON')
        data = load_raw(con)
        expected_pool = reconstruct_candidates(data, plan['selection']['study_salt'], wg)
        stored_pool = Fingerprints(plan['selection']['study_salt'], wg)
        with gzip.open(exp / 'measurement' / ('candidate_universe_' + wg + '.jsonl.gz'), 'rt') as stream:
            for line in stream:
                row = json.loads(line)
                stored_pool.add(row['stratum'], row['candidate'])
        for (_, stratum), cell in ((k, v) for k, v in cells.items() if k[0] == wg):
            n = expected_pool.counts[stratum]
            check(wg + ':' + stratum + ':entire_pre_consider_candidate_multiset',
                  n == stored_pool.counts[stratum] == cell['pre_predicate_candidates'] == old_cells[wg, stratum]['candidate_universe_count'] and
                  expected_pool.sums[stratum] == stored_pool.sums[stratum] and expected_pool.xors[stratum] == stored_pool.xors[stratum])
            if cell['comparison_status'] == 'paired':
                (rank, _), anchor = expected_pool.best[stratum]
                check(wg + ':' + stratum + ':same_hash_minimum', anchor == cell['baseline_anchor'] and rank == cell['baseline_selection_sha256'])
                independent_baselines.append({'wg': wg, 'stratum': stratum, 'candidateCount': n, 'anchor': anchor, 'selectionSha256': rank})
        for arm in arm_names:
            for task in (r for r in arms[arm] if r['wg'] == wg):
                identity, family, anchor = task['id'], task['family'], task['anchor']
                gold = expect(data, family, anchor)
                check(arm + ':' + identity + ':independent_python_gold', gold == norm(task['gold']))
                ref = execute(con, task['reference_sql'])
                check(arm + ':' + identity + ':fresh_reference_SQL', ref['status'] == task['reference']['status'] == 'ok' and
                      ref['rows'] == gold == norm(task['reference']['rows']))
                totals[arm]['references'] += 1
                wrong, equivalences = set(), defaultdict(list)
                equivalences[canon(rows_json(gold))].append('reference')
                for control in task['controls']:
                    name = control['name']
                    actual = execute(con, control['sql'])
                    stored = control['execution']
                    check(arm + ':' + identity + ':' + name + ':fresh_SQL', actual['status'] == stored['status'] and
                          (actual['status'] != 'ok' or actual['rows'] == norm(stored['rows'])))
                    expected = expect(data, family, anchor, name)
                    if isinstance(expected, dict):
                        out = actual['rows']
                        admissible = expected['arbitraryCode'] or {None}
                        py_equal = len(out) == 1 and out[0][0] in admissible and out[0][1] == expected['count']
                        totals[arm]['arbitrary_group_code_constraints'] += 1
                    else:
                        py_equal = actual['status'] == 'ok' and actual['rows'] == expected
                        totals[arm]['mutant_full_python_rowsets'] += 1
                    check(arm + ':' + identity + ':' + name + ':independent_mutant_semantics', py_equal)
                    discriminating = actual['status'] == 'ok' and actual['rows'] != gold
                    check(arm + ':' + identity + ':' + name + ':boundary', discriminating == control['discriminating'])
                    totals[arm]['controls'] += 1
                    totals[arm]['discriminating'] += discriminating
                    totals[arm]['required'] += control['required']
                    totals[arm]['required_discriminating'] += discriminating and control['required']
                    if discriminating:
                        wrong.add(canon(rows_json(actual['rows'])))
                    if actual['status'] == 'ok':
                        equivalences[canon(rows_json(actual['rows']))].append(name)
                    outputs.append({'arm': arm, 'task': identity, 'control': name, 'status': actual['status'],
                                    'discriminating': discriminating, 'rowsSha256': hashlib.sha256(canon(rows_json(actual.get('rows', []))).encode()).hexdigest()})
                frozen_classes = {canon(c['rows']): sorted(c['queries']) for c in task['output_equivalence_classes']}
                actual_classes = {key: sorted(value) for key, value in equivalences.items()}
                check(arm + ':' + identity + ':all_output_equivalence_classes', frozen_classes == actual_classes and len(wrong) == task['wrong_output_classes'])
                totals[arm]['wrong_output_classes'] += len(wrong)
        con.close()
        check(wg + ':database_unchanged', digest(database) == pin['database_sha256'] and digest(source) == pin['source_sha256'])
        print(json.dumps({'checked': wg, 'counts': {a: dict(v) for a, v in totals.items()}}), flush=True)
    for arm in arm_names:
        s = summary['arms'][arm]
        t = totals[arm]
        check(arm + ':fixed_denominators', t['references'] == 66 and t['controls'] == 200 and t['required'] == 113)
        check(arm + ':summary', t['discriminating'] == s['discriminating_controls'] and
              t['required_discriminating'] == s['required_discriminating'] and t['wrong_output_classes'] == s['wrong_output_classes'])
    for identity, witness in by_arm['witness'].items():
        baseline = by_arm[arm_names[1]][identity]
        by_control = {r['name']: r for r in baseline['controls']}
        for control in witness['controls']:
            pairs[f"witness_{int(control['discriminating'])}_baseline_{int(by_control[control['name']]['discriminating'])}"] += 1
    check('paired_matrix_summary', dict(pairs) == summary['paired_control_patterns'])
    result = {'status': 'pass', 'checkerSha256': digest(Path(__file__)), 'protocolSha256': digest(exp / 'protocol.json'),
              'implementationSha256': digest(exp / 'measure.py'), 'python': sys.version, 'sqlite': sqlite3.sqlite_version,
              'elapsedSeconds': time.monotonic() - begun, 'scope': 'No builder imports. Entire pre-consider candidate multiset and hash-min reconstructed from raw relations; independent Python reference and mutant semantics, plus all132 reference and400 control SQL executions. Ungrouped SQLite arbitrary code is checked relationally and replayed exactly, rather than assigned a false deterministic Python gold.',
              'totals': {a: dict(v) for a, v in totals.items()}, 'pairedPatterns': dict(pairs),
              'candidateBaselines': independent_baselines, 'outputs': outputs, 'checks': checks,
              'checksPassed': sum(r['ok'] for r in checks), 'checksFailed': sum(not r['ok'] for r in checks)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('checks', 'outputs', 'candidateBaselines')}))


if __name__ == '__main__':
    main()
