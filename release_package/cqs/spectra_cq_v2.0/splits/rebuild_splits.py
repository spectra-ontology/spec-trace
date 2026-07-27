#!/usr/bin/env python3
"""rebuild_splits.py -- re-derive the shipped SpectraCQ v2.0 split identifier lists.

The release ships four canonical partitions of the 624 scored competency
questions:

  standard_60_20_20      60/20/20 train/dev/test, stratified on (WG x track).
  template_disjoint      no literal-erased query template and no verbatim
                         question string crosses a split, so a solver cannot
                         memorise a shape in train and replay it in test.
  cross_wg_heldout_ran5  test = the whole of RAN5; RAN1..RAN4 split 75/25 into
                         train/dev, so transfer to an unseen Working Group is
                         measured rather than assumed.
  challenge_subset.txt   every question satisfying at least four of the five
                         per-row difficulty conditions.

This script rebuilds all of them from two files that ship inside the same
release directory -- ../benchmark.jsonl and ./track_assignment.json -- and then
compares the regenerated lists byte for byte against the shipped .txt files.
Nothing else is read: no database, no network, no third-party package.

Membership is a deterministic function of the question identifier. Every
ordering decision goes through sha256(SALT + cq_id); the split sizes come from
largest-remainder arithmetic rather than from sampling; no random-number
generator is involved. There is therefore no Python-version, dict-order, or
platform dependence, and a rebuild reproduces the shipped files byte for byte.

Usage:
  python3 rebuild_splits.py           # verify against the shipped lists
  python3 rebuild_splits.py --write   # regenerate and rewrite the .txt files
"""
import hashlib
import json
import pathlib
import re
import sys
from collections import Counter

BASE = pathlib.Path(__file__).resolve().parent
BENCH = BASE.parent / 'benchmark.jsonl'
TRACKS = BASE / 'track_assignment.json'

SEED = 624
SALT = f'spectra_cq_v2.0/seed-{SEED}/'
SPLIT_NAMES = ('train', 'dev', 'test')
RATIOS = (0.6, 0.2, 0.2)
WGS = ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5')
TRACK_NAMES = ('lookup', 'aggregation', 'relational', 'multihop')
HELD_OUT_WG = 'RAN5'
CHALLENGE_THRESHOLD = 4


def hkey(cq_id):
    """Stable per-item sort key: salted SHA-256 hex digest of the id."""
    return hashlib.sha256((SALT + cq_id).encode()).hexdigest()


# ------------------------------------------------------- structural derivations
def template(cypher):
    """Literal-erased query shape: quote bodies and numerals normalised."""
    t = re.sub(r"'(?:[^'\\]|\\.)*'", "'S'", cypher)
    t = re.sub(r'"(?:[^"\\]|\\.)*"', '"S"', t)
    t = re.sub(r'\b\d+(?:\.\d+)?\b', '0', t)
    return re.sub(r'\s+', ' ', t).strip()


def hops(cypher):
    """Number of relationship patterns the query traverses."""
    return len(re.findall(r'-\s*\[[^\]]*\]\s*-', cypher))


ANY_LIMIT = re.compile(r'\bLIMIT\b', re.I)
# The corpus's time axis: the monotone meeting ordinal used for recency
# ordering, its string forms, and the plenary ordinal.
TIME_FIELDS = r'(?:meetingNumberInt|canonicalMeetingNumber|meetingNumber|tsgMeeting)'
# Inter-group surface: liaison statements and their routing edges cross WG
# boundaries by construction, and a CR pack's tsgMeeting leaves the WG for the
# plenary.
CROSS_WG = re.compile(r':WorkingGroup|ORIGINATED_FROM|SENT_TO|CC_TO|:LS\b|tsgMeeting')


def order_by_clause(cypher):
    m = re.search(r'\bORDER\s+BY\b(.*?)(?:\bLIMIT\b|\bSKIP\b|$)', cypher, re.I | re.S)
    return m.group(1) if m else ''


def is_temporal(cypher):
    """Answer depends on the meeting time axis: ordered by it, compared against
    it, or reduced over it."""
    if re.search(TIME_FIELDS, order_by_clause(cypher)):
        return True
    if re.search(TIME_FIELDS + r'\s*(?:<=|>=|<|>)', cypher):
        return True
    return bool(re.search(r'\b(?:max|min)\s*\(\s*\w+\.' + TIME_FIELDS, cypher, re.I))


def is_cross_wg(cypher):
    return bool(CROSS_WG.search(cypher))


def load_items():
    """The per-row facts the four splits are functions of."""
    rows = [json.loads(l) for l in BENCH.read_text().splitlines() if l.strip()]
    ta = json.loads(TRACKS.read_text())
    items = {}
    for r in rows:
        cy = r['cypher']
        vals = [str(v) for v in (r['gold_primary_values'] or [])]
        items[r['id']] = {
            'id': r['id'], 'wg': r['wg'], 'track': ta[r['id']],
            'template': template(cy), 'hops': hops(cy),
            'question': r['question_en'],
            'n_gold_columns': len(r['gold_columns']),
            'gold_cardinality': len({v for v in vals}),
            'has_limit': bool(ANY_LIMIT.search(cy)),
            'temporal': is_temporal(cy), 'cross_wg': is_cross_wg(cy),
        }
    return items


# ------------------------------------------------------------- allocation maths
def largest_remainder(n, ratios):
    """Integer quotas summing exactly to n, ties broken by split order."""
    exact = [n * r for r in ratios]
    base = [int(x) for x in exact]
    order = sorted(range(len(ratios)), key=lambda i: (-(exact[i] - base[i]), i))
    for i in order[:n - sum(base)]:
        base[i] += 1
    return base


def stratified(ids_by_cell, ratios, names=SPLIT_NAMES):
    """Two-level entitlement allocation over hash-ordered ids.

    Items are visited stratum by stratum (strata in fixed lexical order, items
    inside a stratum in hash order) and each item goes to the split whose
    entitlement is furthest unmet, summed over two levels:

      deficit(s) = [r_s * (global_seen + 1) - global_n_s]
                 + [r_s * (cell_seen + 1)   - cell_n_s]

    The stratum term holds each cell's composition near the target ratios; the
    global term stops the per-cell rounding residues from all landing on the
    same split. Both terms are counts of items owed, so no weighting constant
    is introduced.
    """
    assign = {}
    gn = {s: 0 for s in names}
    gseen = 0
    for cell in sorted(ids_by_cell):
        cn = {s: 0 for s in names}
        cseen = 0
        for i in sorted(ids_by_cell[cell], key=lambda x: (hkey(x), x)):
            gseen += 1
            cseen += 1
            best = None
            for si, s in enumerate(names):
                r = ratios[si]
                d = (r * gseen - gn[s]) + (r * cseen - cn[s])
                if best is None or d > best[0] + 1e-12:
                    best = (d, si, s)
            s = best[2]
            assign[i] = s
            gn[s] += 1
            cn[s] += 1
    return assign


class Union:
    def __init__(self, keys):
        self.p = {k: k for k in keys}

    def find(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def join(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def leak_groups(items):
    """Grouping unit for the disjoint split: connected components of
    same-template and same-question-string. Duplicate-question pairs are not
    always template mates, so grouping on templates alone would leave a verbatim
    question in train and in test; the union closes that hole and is a strict
    superset of template disjointness."""
    u = Union(items)
    for key in ('template', 'question'):
        buckets = {}
        for i, it in items.items():
            buckets.setdefault(it[key], []).append(i)
        for ids in buckets.values():
            for other in ids[1:]:
                u.join(ids[0], other)
    groups = {}
    for i in items:
        groups.setdefault(u.find(i), []).append(i)
    return {g: sorted(v) for g, v in groups.items()}


def marginal_greedy(groups, items, targets, keys=('track', 'wg')):
    """Assign whole groups to splits, always to the split whose marginals are
    furthest below where they should be.

      deficit(s, k) = target_size(s) * corpus_share(k) - current_count(s, k)
      score(s)      = sum over the group's items of deficit on each key

    Because the per-track deficits of a split sum to its size deficit, the same
    rule drives the split sizes to their targets without a separate size weight.
    Ties break by split order; groups are visited largest first, then by hash
    key.
    """
    n = len(items)
    share = {k: {v: c / n for v, c in Counter(it[k] for it in items.values()).items()}
             for k in keys}
    count = {s: {k: Counter() for k in keys} for s in SPLIT_NAMES}
    assign = {}
    order = sorted(groups.items(), key=lambda kv: (-len(kv[1]), hkey(kv[1][0])))
    for _, ids in order:
        best = None
        for si, s in enumerate(SPLIT_NAMES):
            score = sum(targets[s] * share[k][items[i][k]] - count[s][k][items[i][k]]
                        for i in ids for k in keys)
            if best is None or score > best[0] + 1e-12:
                best = (score, si, s)
        s = best[2]
        for i in ids:
            assign[i] = s
            for k in keys:
                count[s][k][items[i][k]] += 1
    return assign


# ------------------------------------------------------------------- challenge
# Five per-row difficulty conditions, each a predicate over the released row.
# Their conjunction admits two questions, which is too few to score a model on,
# so the published subset is every question satisfying at least four of them.
CONDITIONS = (
    ('c1_depth_ge_3_hops', lambda it: it['hops'] >= 3),
    ('c2_no_limit_anywhere', lambda it: not it['has_limit']),
    ('c3_full_tuple_ge_2_columns', lambda it: it['n_gold_columns'] >= 2),
    ('c4_gold_cardinality_ge_2', lambda it: it['gold_cardinality'] >= 2),
    ('c5_cross_wg_or_temporal', lambda it: it['cross_wg'] or it['temporal']),
)


def challenge_subset(items):
    conds = dict(CONDITIONS)
    return [i for i in sorted(items)
            if sum(1 for n in conds if conds[n](items[i])) >= CHALLENGE_THRESHOLD]


# ---------------------------------------------------------------------- splits
def build(items):
    """The four splits, as {relative .txt path: sorted identifier list}."""
    targets = dict(zip(SPLIT_NAMES, largest_remainder(len(items), RATIOS)))

    cells = {}
    for i, it in items.items():
        cells.setdefault((it['wg'], it['track']), []).append(i)
    standard = stratified(cells, RATIOS)

    tdisjoint = marginal_greedy(leak_groups(items), items, targets)

    trainable = {}
    for i, it in items.items():
        if it['wg'] != HELD_OUT_WG:
            trainable.setdefault((it['wg'], it['track']), []).append(i)
    crosswg = stratified(trainable, (0.75, 0.25), ('train', 'dev'))
    for i, it in items.items():
        if it['wg'] == HELD_OUT_WG:
            crosswg[i] = 'test'

    out = {}
    for name, assign in (('standard_60_20_20', standard),
                         ('template_disjoint', tdisjoint),
                         ('cross_wg_heldout_ran5', crosswg)):
        for s in SPLIT_NAMES:
            out[f'{name}/{s}.txt'] = sorted(i for i, v in assign.items() if v == s)
    out['challenge_subset.txt'] = challenge_subset(items)
    return out


def render(ids):
    """The shipped on-disk form: one identifier per line, trailing newline."""
    return ('\n'.join(ids) + '\n').encode()


def main(argv):
    write = '--write' in argv[1:]
    unknown = [a for a in argv[1:] if a != '--write']
    if unknown:
        print(f'unknown argument(s): {unknown}', file=sys.stderr)
        print('\n'.join(__doc__.strip().splitlines()[-3:]), file=sys.stderr)
        return 2

    problems = []
    for p in (BENCH, TRACKS):
        if not p.exists():
            problems.append(f'missing input: {p}')
    if problems:
        for p in problems:
            print(p)
        return 1

    items = load_items()
    if len(items) != SEED:
        problems.append(f'expected {SEED} rows in benchmark.jsonl, read {len(items)}')
    unknown_track = sorted({it['track'] for it in items.values()} - set(TRACK_NAMES))
    if unknown_track:
        problems.append(f'track_assignment.json holds unknown tracks {unknown_track}')
    unknown_wg = sorted({it['wg'] for it in items.values()} - set(WGS))
    if unknown_wg:
        problems.append(f'benchmark.jsonl holds unknown working groups {unknown_wg}')

    parts = build(items)
    for rel in sorted(parts):
        ids = parts[rel]
        blob = render(ids)
        path = BASE / rel
        shipped = path.read_bytes() if path.exists() else b''
        shipped_ids = shipped.decode().split('\n')[:-1] if shipped else []
        ok = blob == shipped
        print(f'{rel:37s} rebuilt {len(ids):3d}  shipped {len(shipped_ids):3d}  '
              f'{"[ok]" if ok else "[MISMATCH]"}')
        if not ok:
            only_new = sorted(set(ids) - set(shipped_ids))
            only_old = sorted(set(shipped_ids) - set(ids))
            problems.append(
                f'{rel}: {len(only_new)} identifier(s) only in the rebuild '
                f'{only_new[:5]}, {len(only_old)} only in the shipped list '
                f'{only_old[:5]}'
                + ('' if (only_new or only_old) else '; same members, byte layout differs'))
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)

    if write:
        print(f'wrote {len(parts)} list(s) under {BASE.name}/')
    print()
    if problems:
        print('problems:')
        for p in problems:
            print(f'  - {p}')
        return 1
    print('problems: none -- every shipped list is reproduced byte for byte')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
