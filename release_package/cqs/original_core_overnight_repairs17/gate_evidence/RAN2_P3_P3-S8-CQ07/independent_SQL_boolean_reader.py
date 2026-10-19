#!/usr/bin/env python3
"""Execute an independent read-only SQL query and compare every native field.

Spec: Exact canonical original-question repair, no model performance measurement.
Ontology: Pinned frozen SQL mirror and full rollback-only native capture.
Cycle: Overnight local audit before 2026-10-15 10:00 KST.
배경: Compare uncapped complete records using independently authored SQL.
사용: python3 audit_frozen_required_records_against_native_v3_declared_JSON.py --definition FILE --capture DIR --sql FILE --stem NAME
LLM 호출: None; direct development verification, expert validation0.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, "/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/original_core_repair")
import typed_values

BASE = Path(__file__).resolve().parents[3]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--definition', type=Path, required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--sql', type=Path, required=True)
    parser.add_argument('--stem', required=True)
    args = parser.parse_args()
    args.definition = args.definition.resolve()
    args.capture = args.capture.resolve()
    args.sql = args.sql.resolve()
    assert '/' not in args.stem and '..' not in args.stem
    definition = json.loads(args.definition.read_text())
    wg = definition['id'].split('_')[0]
    db = BASE.parent/'relational'/f'{wg}.sqlite'
    db_before = sha(db)
    manifest_path = BASE.parent/'relational'/f'{wg}.manifest.json'
    manifest = json.loads(manifest_path.read_text())
    assert db_before == manifest['db_sha256']
    sql = args.sql.read_text()
    conn = sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1', uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA query_only=ON')
    independent = [dict(row) for row in conn.execute(sql)]
    conn.close()
    fields = definition["required_fields"]
    for row in independent:
        for field in fields:
            if field["type"] == "json" and isinstance(row[field["name"]], str):
                row[field["name"]] = json.loads(row[field["name"]])
            if field["type"] == "boolean":
                value = row[field["name"]]
                assert type(value) is int and value in (0, 1), "SQLite Boolean must be exact integer0/1"
                row[field["name"]] = bool(value)
    def typed_record(row):
        assert set(row) == {f["name"] for f in fields}
        return tuple(typed_values.typed_token(row[f["name"]], typed_values.field_schema(f), f.get("nested_array_semantics", {})) for f in fields)
    query_sha = hashlib.sha256(definition['reference_query'].encode()).hexdigest()
    receipt_path = args.capture/'reference_outputs'/definition['id']/(query_sha+'.json')
    receipt = json.loads(receipt_path.read_text())
    assert receipt['query'] == definition['reference_query'] and receipt['status'] == 'OK'
    assert receipt['full_rows_available'] and not receipt['truncated'] and receipt['rollback_completed']
    assert receipt['execution_summary_complete']
    assert receipt['plan_query_type'] == receipt['execution_query_type'] == 'r'
    native_rows = receipt_path.with_suffix('.jsonl')
    assert sha(native_rows) == receipt['rows_sha256']
    native = [dict(zip(receipt['columns'], json.loads(line))) for line in native_rows.open()]
    assert all(set(row) == set(receipt['columns']) for row in native+independent)
    assert Counter(map(typed_record, native)) == Counter(map(typed_record, independent)), definition['id']
    assert len(native) == len(independent) == receipt['rows_retained']
    assert sha(db) == db_before
    run_path = args.capture/f'execution_{wg}.json'
    run = json.loads(run_path.read_text())
    assert run['inventory_unchanged'] and run['source_before'] == run['source_after']
    assert run['source_before']['source']['sha256'] == manifest['source']['sha256']
    records_path = BASE/'root_evidence/independent_sql_recheck_records'/f"{definition['id']}.jsonl"
    assert not records_path.exists(), 'Preserve previous complete records'
    records_path.write_text(''.join(canonical(row)+'\n' for row in independent))
    case = {'id': definition['id'], 'status': 'full_native_SQL_multiset_equal', 'sql': sql, 'parameters': [],
            'columns': receipt['columns'], 'rows': len(independent), 'all_return_fields_compared': True,
            'uncapped_SQL': True, 'independent_records': str(records_path.relative_to(BASE)),
            'independent_records_sha256': sha(records_path),
            'native_receipt': str(receipt_path), 'native_receipt_sha256': sha(receipt_path),
            'native_rows': str(native_rows), 'native_rows_sha256': sha(native_rows),
            'db': str(db), 'db_sha256': db_before, 'relational_manifest': str(manifest_path),
            'relational_manifest_sha256': sha(manifest_path), 'snapshot_sha256': manifest['source']['sha256'],
            'SQL_query_pin': {'path': str(args.sql.resolve()), 'sha256': sha(args.sql)},
            'reader_pin': {'path': str(Path(__file__).resolve()), 'sha256': sha(Path(__file__))}}
    case['full_record_comparison_policy'] = 'Declared typed fields and nested array semantics'
    case['declared_field_definitions'] = fields
    case['typed_kernel_pin'] = {'path': str(Path(typed_values.__file__).resolve()), 'sha256': sha(Path(typed_values.__file__))}
    report = {'id': definition['id'], 'independent_native_sql_fullpool_equal': True,
              'rows': len(independent), 'source_sql': sql, 'parameters': [], 'root_independent_SQL_case': case,
              'checked_utc': datetime.now(timezone.utc).isoformat(), 'new_model_API_calls': 0, 'expert_validation_n': 0}
    path = BASE/'root_evidence'/f'{args.stem}.json'
    assert not path.exists(), 'Preserve previous complete evidence'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'id': definition['id'], 'rows': len(independent), 'all_return_fields_compared': True,
                      'root_agreement_sha256': sha(path)}))


if __name__ == '__main__':
    main()
