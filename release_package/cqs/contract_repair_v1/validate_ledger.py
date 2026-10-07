#!/usr/bin/env python3
"""Validate the directly audited ledger contracts and retained-output diagnostics.

Gold self-comparison is a scorer/schema smoke check, never a model result.
Legacy replay values were serialized by paper/baseline/bench_common.py:canon;
their original types cannot be recovered. Optional replay scores therefore use
a separately labelled canonical-string view of the named output contract.
They are conditional compatibility diagnostics of old retained query replays,
not fresh predictions, a result on repaired questions, or expert gold validation.
No model, database, network, source rewriting or score-based selection occurs.
"""
import argparse
from collections import Counter
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import score_contract as sc


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def check_anchors(item, contract):
    for field in contract['required_fields']:
        anchor = field['source_anchor']
        if isinstance(anchor, dict):
            sc.require(anchor['question'] == item['question'], 'field anchor question differs from ledger original')
            sc.require(anchor['query'] == item['reference_query'], 'field anchor query differs from ledger original')
            if 'returned_column' in anchor:
                sc.require(anchor['returned_column'] == field['name'], 'field anchor returned column differs')
    for constraint in contract['constraints']:
        anchor = constraint['source_anchor']
        if isinstance(anchor, dict):
            sc.require(anchor['question'] == item['question'], 'constraint anchor question differs')
            sc.require(anchor['query'] == item['reference_query'], 'constraint anchor query differs')


def legacy_diagnostics(selected, replay_dir):
    # Reuse the historical serializer with attribution; do not reinterpret its
    # canonical strings as proof of the original field's numeric/string type.
    legacy_path = REPO / 'paper/baseline/bench_common.py'
    spec = importlib.util.spec_from_file_location('legacy_bench_common_for_canon', legacy_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    models = sorted(path.name for path in (REPO / 'paper/baseline/results/kg_grounded').iterdir() if path.is_dir())
    expected = {(model, item_id) for model in models for item_id in selected}
    replay_rows, replay_hashes = {}, {}
    for wg in sorted({item['wg'] for item in selected.values()}):
        path = replay_dir / (wg + '.jsonl.gz')
        replay_hashes[str(path.relative_to(REPO))] = sha256(path)
        wanted = {(model, item_id) for model, item_id in expected if selected[item_id]['wg'] == wg}
        with gzip.open(path, 'rt') as stream:
            for line in stream:
                record = json.loads(line)
                if '_header' in record:
                    continue
                key = record.get('model'), record.get('id')
                if key in wanted:
                    sc.require(key not in replay_rows, 'duplicate selected retained replay')
                    replay_rows[key] = record
                    wanted.remove(key)
                    if not wanted:
                        break
    cases = []
    for model, item_id in sorted(expected):
        item = selected[item_id]
        source_contract = item['typed_contract']
        if not source_contract['required_fields']:
            continue
        view = copy.deepcopy(source_contract)
        for field in view['required_fields']:
            field['type'] = 'string'
            field.pop('nullable', None)
        view['status'] = 'unresolved'
        view['unresolved_reasons'].append('legacy_canonical_transport_erased_original_field_types')
        gold = [{name: module.canon(value) for name, value in row.items()}
                for row in item['original_gold']['rows']]
        replay = replay_rows.get((model, item_id))
        if replay is None or replay['status'] != 'OK':
            prediction = []
            status = 'missing' if replay is None else replay['status']
        else:
            columns = replay['columns']
            sc.require(len(set(columns)) == len(columns), 'duplicate retained replay columns')
            sc.require(all(len(row) == len(columns) for row in replay['rows']), 'retained replay width differs')
            prediction = [dict(zip(columns, row)) for row in replay['rows']]
            status = replay['status']
        try:
            result = sc.score_contract(view, gold, prediction)
            cases.append({'model': model, 'item_id': item_id, 'replay_status': status,
                          'row_capped': None if replay is None else replay['row_capped'],
                          'missing_required_columns': [field['name'] for field in view['required_fields']
                                                       if replay is None or field['name'] not in replay['columns']],
                          'diagnostic': result})
        except ValueError as error:
            cases.append({'model': model, 'item_id': item_id, 'replay_status': status,
                          'diagnostic_not_computed': str(error)})
    return {'view': 'legacy_canonical_strings_with_named_roles',
            'measurement_claim': 'retained-query-output compatibility only; not new model performance',
            'original_types_recoverable': False,
            'models': models, 'expected_cases': len(expected), 'retained_cases_found': len(replay_rows),
            'serializer_source': str(legacy_path.relative_to(REPO)), 'serializer_sha256': sha256(legacy_path),
            'replay_sha256': replay_hashes, 'cases': cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, default=HERE / 'contract_ledger.jsonl')
    parser.add_argument('--out', type=Path, default=HERE / 'validation_ledger.json')
    parser.add_argument('--legacy-replays', action='store_true')
    args = parser.parse_args()
    import jsonschema
    schema = json.loads((HERE / 'contract_schema.json').read_text())
    jsonschema.Draft7Validator.check_schema(schema)
    validator = jsonschema.Draft7Validator(schema)
    ledger_bytes = args.ledger.read_bytes()
    ledger = [json.loads(line) for line in ledger_bytes.decode().splitlines() if line.strip()]
    items = [item for item in ledger if '_header' not in item]
    sc.require(len({item['id'] for item in items}) == len(items), 'duplicate ledger IDs')
    selected = {item['id']: item for item in items if item.get('selected_for_direct_source_audit')}
    checks = []
    for item_id, item in sorted(selected.items()):
        contract = item['typed_contract']
        try:
            validator.validate(contract)
            sc.validate_contract(contract)
            sc.require(contract['item_id'] == item_id, 'contract item ID differs')
            check_anchors(item, contract)
            check = {'item_id': item_id, 'status': 'PASS', 'schema_and_source_anchors': 'PASS',
                     'gold_rows': len(item['original_gold']['rows']),
                     'required_fields': [field['name'] for field in contract['required_fields']]}
            try:
                absent = [field['name'] for field in contract['required_fields']
                          if field['name'] not in item['original_gold']['columns']]
                sc.require(not absent, 'requested field absent from original returned columns: ' + ', '.join(absent))
                gold = item['original_gold']['rows']
                result = sc.score_contract(contract, gold, gold)
                sc.require(result['output_exact'] == 1 and result['partial_named_cells']['f1'] == 1,
                           'valid supplied gold does not self-match')
                check.update(gold_applicability='PASS', gold_self_comparison_smoke_check=result)
            except ValueError as error:
                # A source-grounded contract may explicitly require a field or
                # type that old gold does not contain. Preserve the blocker;
                # do not coerce it into a typed gold or a zero model score.
                check.update(gold_applicability='BLOCKED', gold_applicability_reason=str(error))
            checks.append(check)
        except (ValueError, jsonschema.ValidationError) as error:
            checks.append({'item_id': item_id, 'status': 'FAIL', 'error': str(error)})
    report = {'schema_validation': 'Draft7 meta-schema and selected item validation',
              'measurement_scope': 'author-side contract/schema/source-anchor and supplied-gold smoke checks',
              'semantic_validation': False, 'fresh_models_or_database_runs': False,
              'source_sha256': {**{path.name: sha256(path) for path in
                                (HERE / 'contract_schema.json', HERE / 'score_contract.py', Path(__file__))},
                                args.ledger.name: hashlib.sha256(ledger_bytes).hexdigest()},
              'ledger_items': len(items), 'selected_items': len(selected),
              'automatic_only_items_not_scored': len(items) - len(selected),
              'checks': checks, 'status_counts': dict(Counter(check['status'] for check in checks)),
              'gold_applicability_counts': dict(Counter(check.get('gold_applicability', 'not_checked') for check in checks)),
              'limitations': ['Gold self-matching is not a model score or a validation of gold meaning.',
                              'Unresolved scope, extent, source fidelity and role interpretation remain indeterminate.',
                              'Legacy queries were generated for original questions and old contracts, not these sidecars.',
                              'Released gold can also contain canonical strings. Typed fields cannot be certified by parsing those strings.',
                              'Requested count-unit repairs can require gold fields absent from the original reference query.']}
    if args.legacy_replays:
        report['legacy_retained_output_diagnostics'] = legacy_diagnostics(selected, REPO / 'paper/baseline/results/_full_record')
    args.out.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'selected_items': len(selected), 'status_counts': report['status_counts'],
                      'gold_applicability_counts': report['gold_applicability_counts'],
                      'automatic_only_items_not_scored': report['automatic_only_items_not_scored'],
                      'output': str(args.out)}, sort_keys=True))
    if any(check['status'] == 'FAIL' for check in checks):
        sys.exit(1)


if __name__ == '__main__':
    main()
