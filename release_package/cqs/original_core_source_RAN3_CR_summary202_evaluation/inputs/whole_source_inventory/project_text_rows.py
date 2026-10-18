#!/usr/bin/env python3
"""Stream a question-independent text projection of the whole physical inputs.

Workbook rows with neither a nonempty literal value nor a formula element have
no authored text to retrieve. Keep every other record, preserving all JSON
values except the globally renumbered source_row. Original physical inputs,
full raw rows and coordinates remain immutable external pinned inputs.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time


ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())


def canonical(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def relative(p):
    return str(p.resolve().relative_to(ROOT))


def pin(p):
    return {'path': relative(p), 'sha256': sha(p), 'bytes': p.stat().st_size}


def dump(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def keep_record(record):
    fields = record['fields']
    if 'cells' not in fields:
        return True
    return any(c.get('literal_value', '') != '' or 'literal_formula' in c for c in fields['cells'])


def add_range(ranges, value):
    if ranges and ranges[-1][1] + 1 == value:
        ranges[-1][1] = value
    else:
        ranges.append([value, value])


def run(original_manifest, out):
    original = json.loads(original_manifest.read_text())
    original_pin = original['outputs']['raw_source_records.jsonl']
    raw = ROOT / original_pin['path']
    before_stat = raw.stat()
    out.relative_to(Path(__file__).resolve().parent)
    if out.exists():
        raise ValueError('Refuse to overwrite an existing projection')
    out.mkdir(parents=True)
    start = time.monotonic()
    counters, groups = Counter(), {}
    whole_hash, kept_value_hash, dropped_hash = hashlib.sha256(), hashlib.sha256(), hashlib.sha256()
    target = out / 'raw_source_records.jsonl'
    with raw.open('rb') as source, target.open('w') as dest:
        for line in source:
            whole_hash.update(line)
            row = json.loads(line)
            counters['original_raw_records_n'] += 1
            assert row['source_row'] == counters['original_raw_records_n']
            assert set(row) == {'source_row', 'fields', 'source_cell_coordinates'}
            if keep_record(row):
                counters['raw_records_n'] += 1
                if 'cells' in row['fields']:
                    counters['retained_authored_workbook_rows_n'] += 1
                else:
                    counters['retained_nonworkbook_records_n'] += 1
                kept_value_hash.update((canonical({'fields': row['fields'], 'source_cell_coordinates': row['source_cell_coordinates']}) + '\n').encode())
                row['source_row'] = counters['raw_records_n']
                dest.write(canonical(row) + '\n')
            else:
                counters['excluded_empty_workbook_rows_n'] += 1
                dropped_hash.update(line)
                fields, coords = row['fields'], row['source_cell_coordinates']
                key = canonical({'source_location': fields['source_location'], 'OOXML_part': coords['OOXML_part'],
                                 'OOXML_part_sha256': coords['OOXML_part_sha256'], 'worksheet': fields['worksheet']})
                if key not in groups:
                    groups[key] = {'source': json.loads(key), 'excluded_empty_workbook_rows_n': 0,
                                   'original_source_row_ranges_inclusive': [], 'worksheet_row_1based_ranges_inclusive': []}
                group = groups[key]
                group['excluded_empty_workbook_rows_n'] += 1
                add_range(group['original_source_row_ranges_inclusive'], row['source_row'])
                add_range(group['worksheet_row_1based_ranges_inclusive'], int(fields['row_1based']))
            if counters['original_raw_records_n'] % 200000 == 0:
                print(canonical({'meeting': original['meeting'], **dict(counters)}), flush=True)
    assert whole_hash.hexdigest() == original_pin['sha256']
    assert counters['original_raw_records_n'] == original['counts']['raw_records_n']
    after_stat = raw.stat()
    assert before_stat.st_size == after_stat.st_size == original_pin['bytes']
    assert before_stat.st_mtime_ns == after_stat.st_mtime_ns
    # Reparse the materialized result and bind the unchanged non-index values.
    check_hash = hashlib.sha256()
    n = 0
    with target.open() as f:
        for line in f:
            row = json.loads(line)
            n += 1
            assert row['source_row'] == n and keep_record(row)
            check_hash.update((canonical({'fields': row['fields'], 'source_cell_coordinates': row['source_cell_coordinates']}) + '\n').encode())
    assert n == counters['raw_records_n'] and check_hash.hexdigest() == kept_value_hash.hexdigest()
    rejection = {'kind': 'Excluded workbook rows without authored text or formula',
                 'predicate': "Workbook row is retained iff any cell literal_value != '' or a literal_formula key exists. Whitespace literal values and shared-formula elements remain retained.",
                 'original_full_raw': original_pin, 'coordinate_recovery': 'All original fields, exact cell coordinates and parsed-row XML hashes remain in original_full_raw at the listed original source_row indices.',
                 'excluded_original_lines_concatenated_sha256': dropped_hash.hexdigest(),
                 'excluded_empty_workbook_rows_n': counters['excluded_empty_workbook_rows_n'],
                 'groups': list(groups.values())}
    dump(out/'excluded_empty_workbook_row_coordinates.json', rejection)
    outputs = {p.name: pin(p) for p in (target, out/'excluded_empty_workbook_row_coordinates.json')}
    manifest = {'kind': 'Whole-source text projection excluding text-free workbook formatting rows',
                'created_utc': datetime.now(timezone.utc).isoformat(), 'meeting': original['meeting'],
                'builder': pin(Path(__file__)), 'original_physical_source_manifest': pin(original_manifest),
                'original_full_raw': original_pin, 'original_raw_stream_sha256_verified': True,
                'original_full_raw_bytes_and_mtime_unchanged': True, 'counts': dict(counters), 'outputs': outputs,
                'selection_policy': rejection['predicate'],
                'nonworkbook_record_JSON_values_preserved_except_source_row': True,
                'retained_workbook_record_JSON_values_preserved_except_source_row': True,
                'kept_fields_and_coordinates_canonical_stream_sha256': kept_value_hash.hexdigest(),
                'output_reparsed_fields_and_coordinates_equal_source_projection': True,
                'source_selection_used_question_gold_summary_values_type_status_or_model_results': False,
                'whole_physical_inventory_and_text_unavailability': 'Unchanged; retained in original_physical_source_manifest. This projection does not convert or add missing binary text.',
                'common_source_context_policy': original['common_source_context_policy'],
                'external_API_calls_n': 0, 'native_calls_n': 0, 'new_conversions_n': 0,
                'central_registry_or_public_writes_n': 0, 'elapsed_seconds': round(time.monotonic()-start,3)}
    dump(out/'manifest.json', manifest)
    original_plan = json.loads((original_manifest.parent/'corpus_augmentation_plan.json').read_text())
    plan = {**original_plan, 'raw_records': relative(target), 'expected_n': counters['raw_records_n'],
            'original_whole_physical_manifest': relative(original_manifest),
            'raw_text_projection_manifest': relative(out/'manifest.json'), 'augmentation_not_executed': True}
    dump(out/'corpus_augmentation_plan.json', plan)
    print(canonical({'status': 'TEXT_PROJECTION_READY', 'meeting': original['meeting'], **dict(counters),
                     'raw': outputs['raw_source_records.jsonl'], 'manifest': pin(out/'manifest.json')}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--original-manifest', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    run(args.original_manifest.resolve(), args.out.resolve())
