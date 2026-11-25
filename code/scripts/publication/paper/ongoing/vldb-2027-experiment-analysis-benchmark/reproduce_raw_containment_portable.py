"""Recompute raw-source containment using explicit restored input paths."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time


def rows(path):
    with Path(path).open() as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 << 20), b''):
            value.update(block)
    return value.hexdigest()


def emit(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def checked_index(value):
    wg, separator, path = value.partition('=')
    if not separator or wg not in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
        raise argparse.ArgumentTypeError('Expected --index RAN1=/path/to/restored.sqlite3')
    return wg, Path(path).resolve(strict=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--module-dir', type=Path, required=True)
    ap.add_argument('--common-dir', type=Path, required=True)
    ap.add_argument('--items', type=Path, required=True, action='append')
    ap.add_argument('--index', type=checked_index, required=True, action='append')
    ap.add_argument('--plenary', type=Path, required=True)
    ap.add_argument('--reference-items', type=Path, required=True)
    ap.add_argument('--reference-orders', type=Path, required=True)
    ap.add_argument('--wg', nargs='+', choices=('RAN1','RAN2','RAN3','RAN4','RAN5'))
    ap.add_argument('--expected-items', type=int, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    start = time.monotonic()
    args.out.mkdir(parents=True, exist_ok=False)
    sys.path[:0] = [str(args.module_dir.resolve()), str(args.common_dir.resolve())]
    import measure_text_route_ceiling as text
    import measure_raw_source_route as raw
    indexes = dict(args.index)
    if len(indexes) != len(args.index):
        raise ValueError('Repeated working-group index')
    items = [item for path in args.items for item in rows(path)
             if args.wg is None or item['wg'] in args.wg]
    if len(items) != args.expected_items or len({i['id'] for i in items}) != len(items):
        raise ValueError('Item count or identity differs from the requested scope')
    if set(item['wg'] for item in items) - set(indexes):
        raise ValueError('A required working-group index is absent')
    refs = {item['id']: item for item in rows(args.reference_items)}
    orders = {item['id']: item for item in rows(args.reference_orders)}

    def connect(wg):
        con = sqlite3.connect(indexes[wg].as_uri() + '?mode=ro', uri=True)
        con.execute('PRAGMA cache_size=-65536')
        return con

    text.connect_index = connect
    plenary = raw.PlenarySource(args.plenary.resolve(strict=True))
    sources = {}
    results = []
    try:
        with (args.out/'items.jsonl').open('x') as item_stream, (args.out/'orders.jsonl').open('x') as order_stream:
            for item in items:
                text.guard_memory()
                if item['wg'] not in sources:
                    sources[item['wg']] = raw.WgSource(item['wg'])
                record, order = raw.measure_item(item, sources[item['wg']], plenary)
                expected = {key: value for key, value in refs[item['id']].items()
                            if key not in ('seconds', 'indexStamp')}
                same_record = record == expected
                same_order = order == orders[item['id']]
                results.append({'id': item['id'], 'all_record_fields_equal': same_record,
                                'all_order_fields_equal': same_order})
                item_stream.write(json.dumps(record, ensure_ascii=False) + '\n')
                order_stream.write(json.dumps(order, ensure_ascii=False) + '\n')
                item_stream.flush()
                order_stream.flush()
                if len(results) % 10 == 0 or not (same_record and same_order):
                    print(json.dumps({'items_completed':len(results), 'of':len(items),
                                      'record_equal':same_record,'order_equal':same_order}), flush=True)
                if not (same_record and same_order):
                    raise ValueError('Containment or route order differs: ' + item['id'])
    finally:
        for source in sources.values():
            source.con.close()
        plenary.con.close()
        receipt = {'items': len(results), 'expected_items': args.expected_items,
                   'all_record_fields_equal': len(results) == len(items) and all(r['all_record_fields_equal'] for r in results),
                   'all_order_fields_equal': len(results) == len(items) and all(r['all_order_fields_equal'] for r in results),
                   'python': sys.version, 'sqlite_version': sqlite3.sqlite_version,
                   'wrapper_sha256': digest(Path(__file__)),
                   'original_modules_sha256': {Path(module.__file__).name: digest(Path(module.__file__))
                                               for module in (raw,text)},
                   'reference_sha256': {path.name:digest(path) for path in (args.reference_items,args.reference_orders)},
                   'excluded_comparison_fields': ['seconds','indexStamp'],
                   'seconds': time.monotonic()-start, 'checks': results,
                   'scope':'Original raw-source measurement on explicit restored indexes; every scientific record field and stored route-order field compared.'}
        emit(args.out/'receipt.json',receipt)
    print(json.dumps({key:receipt[key] for key in ('items','all_record_fields_equal','all_order_fields_equal','seconds')}))


if __name__ == '__main__':
    main()
