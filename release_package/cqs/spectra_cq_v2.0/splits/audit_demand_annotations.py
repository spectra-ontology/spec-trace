#!/usr/bin/env python3
"""Inspect the released demand annotations without changing questions or scoring keys.

This is an offline diagnostic, not a semantic-validity classifier. It enumerates
unscored returned columns and syntactic ORDER BY/LIMIT signals over every Core
item, checks the definition of the release-wide later-column demand count, and
records three source-grounded examples of requested information omitted by the
answer-column score. Neither these examples nor the syntactic signals establish
an error prevalence or constitute independent practitioner validation.

Run from any directory:
  python3 audit_demand_annotations.py --check
  python3 audit_demand_annotations.py --json OUTPUT.json
Without arguments, print the complete JSON diagnostic to standard output.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


CQ = Path(__file__).resolve().parent.parent
RECORDED = CQ / 'contract_annotation_diagnostics.json'
INPUTS = (
    'benchmark.jsonl', 'core_answer_gold.jsonl', 'answer_contract.jsonl',
    'contract_demand_provenance.jsonl',
    'splits/contract_exact_script_fixed_133.txt',
    'splits/contract_exact_asked_208.txt',
)
ILLUSTRATIONS = {
    'RAN2_P2_CQ1-10': {
        'requested_information': 'resolution counts by type',
        'omitted_columns': ['cnt'],
        'limitation': 'The gold set contains types, not their resolution counts.',
    },
    'RAN4_P1_CQ4-2': {
        'requested_information': 'liaison-statement direction and recipients',
        'omitted_columns': ['sentTo'],
        'limitation': 'The gold set contains direction, not recipient groups.',
    },
    'RAN5_P2_CQ3-3': {
        'requested_information': 'ranked main contributors to each specification',
        'omitted_columns': ['company', 'tdoc_count'],
        'limitation': 'The gold set contains specification numbers, not contributors, '
                      'contribution counts, or their ranking.',
    },
}


def read_items(name):
    rows = [json.loads(line) for line in (CQ / name).read_text(encoding='utf-8').splitlines()
            if line.strip()]
    items = [row for row in rows if '_header' not in row]
    keyed = {row['id']: row for row in items}
    if len(keyed) != len(items):
        raise ValueError(f'{name}: duplicate identifiers')
    return keyed


def identifiers(name):
    rows = (CQ / name).read_text(encoding='utf-8').splitlines()
    if len(rows) != len(set(rows)) or rows != sorted(rows):
        raise ValueError(f'{name}: identifiers are repeated or unsorted')
    return set(rows)


def clause_present(query, clause):
    # Ignore quoted string values and backtick identifiers. This only detects
    # syntax anywhere in the query; it does not infer the final answer contract.
    stripped = re.sub(r"'(?:\\.|''|[^'])*'|\"(?:\\.|\"\"|[^\"])*\"|`[^`]*`", ' ', query)
    return bool(re.search(r'\b' + clause + r'\b', stripped, re.IGNORECASE))


def diagnostic():
    benchmark = read_items('benchmark.jsonl')
    gold = read_items('core_answer_gold.jsonl')
    contract = read_items('answer_contract.jsonl')
    provenance = read_items('contract_demand_provenance.jsonl')
    fixed = identifiers('splits/contract_exact_script_fixed_133.txt')
    asked = identifiers('splits/contract_exact_asked_208.txt')
    core = set(gold)
    if set(benchmark) != set(provenance):
        raise ValueError('benchmark and provenance identifiers differ')
    if core != set(contract) or not fixed <= asked <= core <= set(benchmark):
        raise ValueError('Core keys or annotation-derived subset nesting differ')

    later_required = sorted(cid for cid, row in provenance.items()
                            if any(c['index'] > 0 and c['verdict'] == 'required'
                                   for c in row['columns']))
    first_verdicts = Counter()
    for cid in later_required:
        first = [c for c in provenance[cid]['columns'] if c['index'] == 0]
        if len(first) != 1:
            raise ValueError(f'{cid}: expected one first returned column')
        first_verdicts[first[0]['verdict']] += 1

    items = []
    for cid in sorted(core):
        item, key, ann = benchmark[cid], gold[cid], provenance[cid]
        answer = key['answer_column']
        columns = item['gold_columns']
        if answer not in columns or contract[cid]['answer_columns'][:1] != [answer]:
            raise ValueError(f'{cid}: scored answer column does not match returned columns')
        by_column = {c['column']: c for c in ann['columns']}
        if set(by_column) != set(columns):
            raise ValueError(f'{cid}: returned columns and provenance differ')
        items.append({
            'id': cid,
            'answer_column': answer,
            'unscored_returned_columns': [c for c in columns if c != answer],
            'annotation_required_beyond_scored_column': sorted(
                c['column'] for c in ann['columns']
                if c['verdict'] == 'required' and c['column'] != answer),
            'reference_has_order_by': clause_present(item['cypher'], r'ORDER\s+BY'),
            'reference_has_limit': clause_present(item['cypher'], 'LIMIT'),
            'recorded_ordering_required': contract[cid]['ordering_required'],
            'in_script_fixed_subset': cid in fixed,
            'in_recorded_annotation_subset': cid in asked,
        })

    cohorts = {}
    for name, ids in [('core', core), ('script_fixed', fixed), ('recorded_annotations', asked)]:
        selected = [row for row in items if row['id'] in ids]
        cohorts[name] = {
            'n': len(selected),
            'items_with_unscored_returned_columns': sum(bool(r['unscored_returned_columns']) for r in selected),
            'items_with_required_annotation_beyond_scored_column': sum(
                bool(r['annotation_required_beyond_scored_column']) for r in selected),
            'items_with_order_by_syntax': sum(r['reference_has_order_by'] for r in selected),
            'items_with_limit_syntax': sum(r['reference_has_limit'] for r in selected),
            'interpretation': 'Syntactic and annotation counts, not numbers of semantically invalid questions.',
        }

    examples = []
    for cid, observation in ILLUSTRATIONS.items():
        item, key, ann = benchmark[cid], gold[cid], provenance[cid]
        by_column = {c['column']: c for c in ann['columns']}
        omitted = observation['omitted_columns']
        if not all(c in item['gold_columns'] and c != key['answer_column']
                   and by_column[c]['verdict'] == 'not_required' for c in omitted):
            raise ValueError(f'{cid}: the recorded illustrative discrepancy has changed')
        if cid not in fixed or cid not in asked:
            raise ValueError(f'{cid}: the recorded illustrative subset membership has changed')
        examples.append({
            'id': cid, 'question': item['question_en'],
            'reference_query': item['cypher'],
            'answer_type': contract[cid]['answer_type'],
            'answer_column': key['answer_column'],
            'gold_values': key['gold_values'],
            **observation,
            'omitted_column_annotations': [by_column[c] for c in omitted],
            'in_script_fixed_subset': True,
            'in_recorded_annotation_subset': True,
        })

    return {
        'method': 'Offline source inspection and enumeration of released annotations and query syntax.',
        'model_calls': 0,
        'inputs': {name: {'sha256': hashlib.sha256((CQ / name).read_bytes()).hexdigest()}
                   for name in INPUTS},
        'scope': {
            'released_items': len(benchmark), 'core_items': len(core),
            'independent_expert_validation': False,
            'semantic_error_prevalence_estimated': False,
            'dataset_or_scoring_key_changed': False,
            'answer_column_score': 'unordered set comparison; other columns, ranks, and duplicates are not graded',
            'examples': 'Source-grounded illustrative discrepancies, not an independent practitioner audit.',
        },
        'later_required_annotation': {
            'definition': 'A returned column with index greater than zero has verdict required, over all released items.',
            'n': len(later_required), 'ids': later_required,
            'first_returned_column_verdicts': dict(sorted(first_verdicts.items())),
            'interpretation': 'This count does not mean that the first returned column, or the declared Core answer column, is unasked.',
        },
        'cohorts': cohorts,
        'illustrative_discrepancies': examples,
        'core_item_signals': items,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true', help='compare with the shipped diagnostic JSON')
    group.add_argument('--json', type=Path, help='write the diagnostic JSON to this path')
    args = parser.parse_args()
    try:
        result = diagnostic()
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.check:
            if not RECORDED.is_file() or RECORDED.read_text(encoding='utf-8') != rendered:
                raise ValueError('the shipped diagnostic is missing or differs; inspect the inputs before regenerating')
            print(f"PASS: {result['scope']['released_items']} released items, "
                  f"{result['scope']['core_items']} Core items, "
                  f"{len(result['illustrative_discrepancies'])} illustrative discrepancies; "
                  'shipped diagnostic reproduced exactly')
        elif args.json:
            args.json.write_text(rendered, encoding='utf-8')
            print(f'wrote {args.json}')
        else:
            print(rendered, end='')
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'diagnostic failed: {error}\n')


if __name__ == '__main__':
    main()
