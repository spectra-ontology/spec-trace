#!/usr/bin/env python3
"""Offline full fixture replay. Does not rerender XLSX/CFB or call native/API."""
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys


def pin(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return dict(bytes=p.stat().st_size, sha256=h.hexdigest())


def verify(directory):
    directory = Path(directory).resolve()
    manifest = json.loads((directory / 'manifest.json').read_text())
    assert manifest['id'] == 'RAN5_P1_CQ6-3'
    for name, expected in manifest['files'].items():
        p = (directory / name).resolve()
        assert p.is_relative_to(directory)
        assert pin(p) == expected, name
    definition = json.loads((directory / 'prospective_definition.json').read_text())
    assert definition['repair_sha256'] == manifest['repair_sha256']
    assert definition['question_en'] == 'Compare the total TDoc count against the CR count (CR proportion).'
    books = json.loads((directory / 'original35_workbook_source_pins.json').read_text())
    assert sorted(b['meeting'] for b in books['selected_files']) == list(range(76, 111))
    chosen = {b['workbook_sha256'] for b in books['selected_files']}
    assert len(chosen) == 35
    seen = set(); seven = set(); cr = set(); roles = collections.Counter()
    h = hashlib.sha256(); size = 0; rows = 0
    with gzip.open(directory / manifest['fixture']['file'], 'rb') as f:
        for line in f:
            rows += 1; h.update(line); size += len(line)
            row = json.loads(line); rid = row['own_ID']
            assert re.fullmatch(r'R5-\d{6,7}', rid) and rid not in seen
            seen.add(rid)
            if re.fullmatch(r'R5-\d{7}', rid): seven.add(rid)
            types = set()
            assert row['original35_rows']
            for src in row['original35_rows']:
                assert src['workbook_sha256'] in chosen
                assert str(src['raw_ID_literal']).strip().upper() == rid
                assert src['type_literal'] not in ('', 'None', 'null')
                assert re.fullmatch(r'[0-9a-f]{64}', src['raw_row_SHA256'])
                assert src['sheet_member'].startswith('xl/worksheets/')
                assert int(src['row']) > 0 and src['raw_jsonl_line_1based'] > 0
                types.add(src['type_literal'].strip())
            rs = {'CR' if t in {'CR', 'draftCR', 'pCR'} else 'LS' if t in {'LS in', 'LS out', 'LSin', 'LSout'} else 'OTHER_TDOC' for t in types}
            assert rs == {row['source_role']}
            roles[row['source_role']] += 1
            if row['source_role'] == 'CR': cr.add(rid)
    assert rows == manifest['fixture']['rows_n']
    assert size == manifest['fixture']['uncompressed_bytes']
    assert h.hexdigest() == manifest['fixture']['uncompressed_sha256']
    defective = json.loads((directory / 'four_seven_digit_source_records_schema_defect.json').read_text())
    assert seven == {r['own_ID'] for r in defective['source_records']}
    opposing = json.loads((directory / 'all63_CR_only_nodes_exact_source_provenance.json').read_text())
    assert len(opposing) == 63 and len({r['node_id'] for r in opposing}) == 63
    overlaps = [r for r in opposing if r['own_ID'] in seen]
    assert len(overlaps) == 5 and all(r['source_role'] != 'CR' for r in overlaps)
    observed = dict(total=len(seen), crs=len(cr))
    certificate = json.loads((directory / 'actual_whole_Type_field_SQL_certificate.json').read_text())
    assert observed == certificate['actual_SQL_result'] == certificate['independent_whole_source_identifier_Type_python_result']
    return dict(status='PASS_PORTABLE_FULL_FIXTURE_REPLAY_ONLY', repair_sha256=manifest['repair_sha256'],
        observed=observed, roles=dict(roles), fixture_rows=rows, seven_digit_defects_n=len(seven),
        opposing_CR_only_nodes_n=len(opposing), original_XML_native_API_executed=False,
        original_XLSX_source_truth_independently_reextracted_here=False)


if __name__ == '__main__':
    print(json.dumps(verify(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent), ensure_ascii=False))
