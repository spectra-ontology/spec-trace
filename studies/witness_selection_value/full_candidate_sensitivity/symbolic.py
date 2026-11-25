"""Independent raw-relation interpreter for the frozen, known SQL operations.

Importing this module performs no evaluation. The runner authorizes execution.
This module neither imports the SQL builder nor consumes archived query outputs.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass
import json


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def normalized(rows):
    return frozenset(tuple(None if value is None else str(value) for value in row)
                     for row in rows)


def ordered(rows):
    # JSON ordering handles NULL without comparing None to a string.
    return sorted((list(row) for row in rows), key=canonical)


@dataclass(frozen=True)
class Outcome:
    """Exact rowset, or admitted bare-aggregate rowset family.

    The family describes SQLite's documented choice, not a probability on codes.
    Detection and the equality partition must be invariant over all choices.
    """
    allowed: frozenset

    @classmethod
    def exact(cls, rows):
        return cls(frozenset((normalized(rows),)))

    def contains(self, rows):
        return normalized(rows) in self.allowed

    def to_json(self):
        return sorted((ordered(rows) for rows in self.allowed), key=canonical)

    def bucket(self):
        buckets = {min(len(rows), 2) for rows in self.allowed}
        if len(buckets) != 1:
            raise ValueError("Non-invariant admitted row cardinality")
        return next(iter(buckets))


def invariant_equal(one, two):
    possibilities = {a == b for a in one.allowed for b in two.allowed}
    if len(possibilities) != 1:
        raise ValueError("Ambiguous rowset equality over admitted bare-code choices")
    return next(iter(possibilities))


def signature(outcomes, names, branches):
    """Partition actual complete rowsets; no row-count surrogate for detection."""
    representatives, partition = [], []
    for name in names:
        for index, previous in enumerate(representatives):
            if invariant_equal(outcomes[name], outcomes[previous]):
                partition.append(index)
                break
        else:
            partition.append(len(representatives))
            representatives.append(name)
    detected = {name: int(not invariant_equal(outcomes['reference'], outcomes[name]))
                for name in names if name != 'reference'}
    value = {'names': names, 'partition': partition,
             'row_cardinality_buckets': [outcomes[name].bucket() for name in names],
             'branches': branches}
    return value, detected


class RawInterpreter:
    def __init__(self, relations):
        self.r = relations
        self.members, self.links = relations['members'], relations['links']
        self.by_typed, self.by_projected = {}, {}
        self._last_key = self._last_value = None

    def pack_indexes(self, pack):
        if pack not in self.by_typed:
            typed, projected = defaultdict(set), defaultdict(set)
            for document in self.members[pack]:
                for spec, release, clause in self.links[document]:
                    typed[spec, release, clause].add(document)
                    projected[spec, clause].add(document)
            self.by_typed[pack], self.by_projected[pack] = typed, projected
        return self.by_typed[pack], self.by_projected[pack]

    def histogram(self, documents):
        result = Counter()
        for document in documents:
            # COUNT(DISTINCT target) within each code ignores raw row repetition.
            result.update(self.r['doc_codes'][document].keys())
        return result

    def evaluate(self, family, anchor):
        # Adjacent strata often reuse one family/anchor. Cache only the last one.
        key = family, canonical(anchor)
        if key == self._last_key:
            return self._last_value
        result = self._evaluate(family, anchor)
        self._last_key, self._last_value = key, result
        return result

    def _evaluate(self, family, anchor):
        outcome, branches = {}, {'family': family}
        exact = Outcome.exact
        if family == 'pack_disposition_counts':
            kind, cohort = anchor
            distinct, raw = defaultdict(set), Counter()
            if kind == 'pack':
                for document in self.members[cohort]:
                    multiplicity = self.r['multiplicity'][cohort, document]
                    for code, count in self.r['doc_codes'][document].items():
                        distinct[code].add(document)
                        raw[code] += multiplicity * count
            elif kind == 'meeting':
                for document, code in self.r['meeting_records'][cohort]:
                    distinct[code].add(document)
                    raw[code] += 1
            else:
                raise ValueError(('Unknown cohort kind', kind))
            outcome['reference'] = exact((code, len(documents))
                                         for code, documents in distinct.items())
            outcome['count_star'] = exact(raw.items())
            documents = set().union(*distinct.values()) if distinct else set()
            if distinct:
                choices = frozenset(normalized([(code, len(documents))]) for code in distinct)
            else:
                choices = frozenset((normalized([(None, 0)]),))
            outcome['omit_group_by'] = Outcome(choices)
            branches.update(cohort_kind=kind, code_groups=min(len(distinct), 2),
                            bare_code='arbitrary_input_code' if len(distinct) > 1
                            else 'single_code' if distinct else 'null_empty_aggregate')
        elif family in ('shared_clauses', 'exclusive_clauses'):
            _, first, second = anchor
            left, right = self.links[first], self.links[second]
            projected_right = {(value[0], value[2]) for value in right}
            shared = family == 'shared_clauses'
            outcome['reference'] = exact(left & right if shared else left - right)
            outcome.update(first_only=exact(left), second_only=exact(right),
                           union=exact(left | right), intersection=exact(left & right),
                           reverse_difference=exact(right - left))
            blind = {value for value in left
                     if (((value[0], value[2]) in projected_right) == shared)}
            outcome['release_blind_membership'] = exact(blind)
            branches['set_operation'] = 'intersection' if shared else 'difference'
        elif family in ('both_clause_documents', 'conjunction_disposition_counts'):
            pack, one, two = anchor
            one, two = tuple(one), tuple(two)
            typed, projected = self.pack_indexes(pack)
            first, second = typed[one], typed[two]
            both, either = first & second, first | second
            if family == 'both_clause_documents':
                display = lambda documents: ((d.replace('tdoc:', ''),) for d in documents)
                broad = projected[one[0], one[2]] & projected[two[0], two[2]]
                outcome.update(reference=exact(display(both)), first_only=exact(display(first)),
                               second_only=exact(display(second)), **{'or': exact(display(either))},
                               release_blind_membership=exact(display(broad)))
            else:
                outcome.update(reference=exact(self.histogram(both).items()),
                               or_before_grouping=exact(self.histogram(either).items()),
                               omit_section_filter=exact(self.histogram(self.members[pack]).items()))
            branches.update(typed_selected_empty=not bool(both))
        elif family == 'largest_clause_footprint':
            pack = anchor[0]
            counts = {document: len(self.links[document]) for document in self.members[pack]}
            if not counts:
                raise ValueError('Unexpected empty pack in frozen universe')
            maximum = max(counts.values())
            winners = {d: n for d, n in counts.items() if n == maximum}
            collapsed = {d: len({(s[0], s[2]) for s in self.links[d]}) for d in counts}
            low_maximum = max(collapsed.values())
            display = lambda items: ((d.replace('tdoc:', ''), n) for d, n in items)
            outcome.update(reference=exact(display(winners.items())),
                           all_positive=exact(display((d, n) for d, n in counts.items() if n > 0)),
                           # Original SQL is ORDER BY raw cr, then LIMIT 1.
                           limit_one=exact(display([(min(winners), maximum)])),
                           release_collapsed_count=exact(display((d, n) for d, n in collapsed.items()
                                                                 if n == low_maximum)))
            branches.update(maximum_zero=maximum == 0, maximum_tie=len(winners) > 1)
        elif family == 'members_without_clause_records':
            pack = anchor[0]
            display = lambda documents: ((d.replace('tdoc:', ''),) for d in documents)
            absent = {d for d in self.members[pack] if not self.links[d]}
            outcome.update(reference=exact(display(absent)),
                           exists=exact(display(self.members[pack] - absent)),
                           all_members=exact(display(self.members[pack])))
            branches['absence'] = 'all' if absent == self.members[pack] else 'some' if absent else 'none'
        else:
            raise ValueError(('Unknown family', family))
        return outcome, branches
