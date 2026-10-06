#!/usr/bin/env python3
"""rebuild_contract_splits.py: rebuild and check the contract-exact identifier lists.

Four identifier lists in this directory are evaluation subsets of
SpectraCQ-Core, the 560 items of ../answer_contract.jsonl. This script
rebuilds them from three files one level up and compares each rebuilt list
byte for byte with the shipped one:

  ../answer_contract.jsonl             contract flags and contract_disposition
  ../contract_demand_provenance.jsonl  one verdict per returned column, each
                                       with the method that made it
  ../core_answer_gold.jsonl            the scored answer column of each item

Besides these and the four shipped lists it reads nothing: no database, no
network, no third-party package.

The lists are defined by the released annotations. A Core item passes the
column-identity condition when no contract flag is set and every column marked
`required` is its scored answer column. Recorded annotations can miss requested
counts, recipients or ranking. Passing this condition therefore does not
establish that the complete natural-language information need is graded.

  contract_exact_asked_208.txt         passes the recorded annotation condition
  contract_exact_script_fixed_133.txt  passes that condition with every
                                       model-mediated column verdict marked
                                       required and model-matched phrases
                                       excluded; default of the Core scorer
  contract_exact_241.txt               historical: contract_disposition is 1
  contract_exact_rule_only_149.txt     historical: no model-mediated column or
                                       phrase verdict within the 241

These filenames and identifier lists are retained for score reproducibility.
The 241 condition bounds the number of required annotations, not the identity
of the scored column. In 33 items its one required column is another column;
17 of those are among the 149. Even after that correction, the annotations
are not independent semantic validation. See audit_demand_annotations.py and
../contract_annotation_diagnostics.json for source-grounded limitations.

Usage:
  python3 rebuild_contract_splits.py           # verify against the shipped lists
  python3 rebuild_contract_splits.py --check   # the same
  python3 rebuild_contract_splits.py --write   # rebuild and rewrite the four lists
"""
import json
import pathlib
import sys
from collections import Counter

BASE = pathlib.Path(__file__).resolve().parent
CQ = BASE.parent
CONTRACT = CQ / 'answer_contract.jsonl'
PROVENANCE = CQ / 'contract_demand_provenance.jsonl'
GOLD = CQ / 'core_answer_gold.jsonl'

# The contract flags that are set when a question demands two or more columns.
DEMAND_FLAGS = {'question_names_extra_columns', 'mapping_answer'}
ASKED, FIXED = 'contract_exact_asked_208', 'contract_exact_script_fixed_133'
DISP1, RULE_ONLY = 'contract_exact_241', 'contract_exact_rule_only_149'
LISTS = (DISP1, RULE_ONLY, ASKED, FIXED)


def read_jsonl(path):
    """Return the _header object and the item rows of a JSON Lines file."""
    with path.open(encoding='utf-8') as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    if not rows or '_header' not in rows[0]:
        raise SystemExit(f'{path.name}: the first line is not a _header object')
    return rows[0]['_header'], rows[1:]


def by_language_model(method):
    """True when a verdict was made by a language model."""
    return method == 'language_model' or method.startswith('language_model:')


def keyed(rows, name, problems):
    """Index rows by identifier, counting repeated identifiers as a problem."""
    out, repeated = {}, 0
    for row in rows:
        repeated += row['id'] in out
        out.setdefault(row['id'], row)
    if repeated:
        problems.append(f'{name}: {repeated} repeated identifier(s)')
    return out


def build(problems):
    """Rebuild the four lists; append any disagreement between the input files to problems."""
    _, contract_rows = read_jsonl(CONTRACT)
    prov_header, prov_rows = read_jsonl(PROVENANCE)
    _, gold_rows = read_jsonl(GOLD)
    contract = keyed(contract_rows, CONTRACT.name, problems)
    provenance = keyed([r for r in prov_rows if r.get('core')], PROVENANCE.name, problems)
    gold = keyed(gold_rows, GOLD.name, problems)
    if not set(contract) == set(provenance) == set(gold):
        problems.append('the three files do not list the same Core items')
    by_model_columns = sum(by_language_model(c['method']) for r in prov_rows for c in r['columns'])
    declared = prov_header.get('language_model', {}).get('columns')
    if by_model_columns != declared:
        problems.append(f'{PROVENANCE.name}: {by_model_columns} column verdict(s) by a language model, '
                        f'header says {declared}')
    lists = {name: [] for name in LISTS}
    counts, bad = Counter(), Counter()
    for cid in sorted(set(contract) & set(provenance) & set(gold)):
        item, prov = contract[cid], provenance[cid]
        answer = gold[cid]['answer_column']
        flags = set(item.get('contract_flags') or [])
        columns = prov['columns']
        names = [c['column'] for c in columns]
        required = {c['column'] for c in columns if c['verdict'] == 'required'}
        by_model = {c['column'] for c in columns if by_language_model(c['method'])}
        undecided = {c['column'] for c in columns if c['verdict'] == 'undecidable'}
        phrases = prov.get('phrases') or []
        bad['answer_columns[0] is not the scored answer column'] += item['answer_columns'][:1] != [answer]
        bad['the scored answer column is not returned exactly once'] += names.count(answer) != 1
        bad['column indexes are not 0, 1, 2, ...'] += [c['index'] for c in columns] != list(range(len(columns)))
        bad['a returned column name repeats'] += len(set(names)) != len(names)
        bad['a column-demand flag disagrees with the required verdicts'] += bool(flags & DEMAND_FLAGS) != (len(required) >= 2)
        bad['contract_disposition 1 disagrees with the contract flags'] += (item['contract_disposition'] == 1) != (not flags)
        bad['a phrase verdict was not made by a language model'] += not all(by_language_model(p['method']) for p in phrases)
        rule_only = not by_model and not phrases
        if item['contract_disposition'] == 1:
            lists[DISP1].append(cid)
            if rule_only:
                lists[RULE_ONLY].append(cid)
        if flags:
            continue
        bad['an undecidable verdict falls on another column'] += bool(undecided - {answer})
        if required <= {answer}:
            lists[ASKED].append(cid)
            counts['demand the scored column' if required else 'demand no column'] += 1
            if by_model <= {answer} and not phrases:
                lists[FIXED].append(cid)
        else:
            counts['one demanded column is not the scored one'] += 1
            counts['of them in the rule-only list'] += rule_only
    problems.extend(f'{n} Core item(s): {what}' for what, n in sorted(bad.items()) if n)
    return lists, counts


def render(ids):
    """The shipped on-disk form: one identifier per line, trailing newline."""
    return ('\n'.join(ids) + '\n').encode('utf-8')


def main(argv):
    args = argv[1:]
    if len(args) > 1 or any(a not in ('--check', '--write') for a in args):
        print('expected at most one of --check and --write; got: ' + ' '.join(args), file=sys.stderr)
        print('\n'.join(__doc__.strip().splitlines()[-3:]), file=sys.stderr)
        return 2
    missing = [p.name for p in (CONTRACT, PROVENANCE, GOLD) if not p.is_file()]
    if missing:
        print('missing input file(s) one level up: ' + ', '.join(missing), file=sys.stderr)
        return 1
    problems = []
    lists, counts = build(problems)
    mismatches = []
    for name in LISTS:
        path = BASE / f'{name}.txt'
        rebuilt = render(lists[name])
        shipped = path.read_bytes() if path.is_file() else b''
        old = shipped.decode('utf-8').split('\n')[:-1] if shipped else []
        ok = rebuilt == shipped
        print(f'{name + ".txt":37s} rebuilt {len(lists[name]):3d}  shipped {len(old):3d}  {"[ok]" if ok else "[MISMATCH]"}')
        if not ok:
            only_new, only_old = len(set(lists[name]) - set(old)), len(set(old) - set(lists[name]))
            mismatches.append(f'{name}.txt: ' + (
                f'{only_new} identifier(s) only in the rebuilt list, {only_old} only in the shipped one'
                if only_new or only_old else 'same identifiers, different bytes (order or line format)'))
    n241, n149 = len(lists[DISP1]), len(lists[RULE_ONLY])
    print(f"in {counts['one demanded column is not the scored one']} of the {n241} the one demanded column "
          f"is not the scored answer column; {counts['of them in the rule-only list']} of those are among the {n149}")
    print(f"of the {len(lists[ASKED])}, {counts['demand the scored column']} demand exactly the scored answer "
          f"column and {counts['demand no column']} demand no column")
    print(f'{len(set(lists[RULE_ONLY]) & set(lists[FIXED]))} of the {n149} are among the {len(lists[FIXED])}')
    if '--write' in args:
        if problems:
            print('nothing written: the input files disagree (see problems)')
        else:
            for name in LISTS:
                (BASE / f'{name}.txt').write_bytes(render(lists[name]))
            print(f'wrote {len(LISTS)} list(s) under {BASE.name}/')
    print()
    if problems or mismatches:
        print('problems:')
        for p in problems + mismatches:
            print(f'  - {p}')
        return 1
    print('problems: none; every shipped list is reproduced byte for byte')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
