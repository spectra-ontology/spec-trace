"""Verify included source projections, with optional original-source replay."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import xml.etree.ElementTree as ET
import zipfile

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def projected_original_rows(path, specs, fields):
    with zipfile.ZipFile(path) as archive:
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            with archive.open('xl/sharedStrings.xml') as stream:
                for _, element in ET.iterparse(stream, events=('end',)):
                    if element.tag == NS + 'si':
                        strings.append(''.join(t.text or '' for t in element.iter(NS + 't')))
                        element.clear()
        header, total, rows = None, 0, []
        with archive.open('xl/worksheets/sheet1.xml') as stream:
            for _, element in ET.iterparse(stream, events=('end',)):
                if element.tag != NS + 'row':
                    continue
                total += 1
                n = int(element.attrib['r'])
                values, coords = {}, {}
                for cell in element.findall(NS + 'c'):
                    address = cell.attrib['r']
                    col = re.match('[A-Z]+', address).group()
                    value = cell.find(NS + 'v')
                    text = value.text if value is not None else ''
                    if cell.attrib.get('t') == 's':
                        text = strings[int(text)] if text else ''
                    elif cell.attrib.get('t') == 'inlineStr':
                        text = ''.join(t.text or '' for t in cell.iter(NS + 't'))
                    values[col], coords[col] = text, address
                if header is None:
                    header = values
                else:
                    data = {name: values.get(col, '') for col, name in header.items()}
                    if data.get('Spec number') in specs:
                        addresses = {name: coords.get(col) for col, name in header.items()}
                        rows.append({'source_row': n, 'fields': {k: data[k] for k in fields},
                                     'source_cells': {k: addresses[k] for k in fields}})
                element.clear()
        return total, rows


def verify(base, source_root=None):
    manifest = json.loads((base / 'manifest.json').read_text())
    for entry in manifest['files']:
        path = base / entry['path']
        assert path.is_file() and path.stat().st_size == entry['bytes']
        assert sha(path) == entry['sha256'], entry['path']
    scope = json.loads((base / 'scope_and_provenance.json').read_text())
    summary = json.loads((base / 'pair_and_release_axis_witness.json').read_text())
    graph = json.loads((base / 'graph_typed_witness.json').read_text())
    specs = set(scope['metadata_scope19'])
    fields = scope['source_projection_fields']
    with gzip.open(base / 'original_source_projection.jsonl.gz', 'rt') as f:
        projected = [json.loads(line) for line in f]
    assert len(projected) == 40091
    assert len({r['source_row'] for r in projected}) == len(projected)
    assert all(r['fields']['Spec number'] in specs for r in projected)
    assert all(r['fields']['Spec number'].startswith('38.5') and
               not r['fields']['Spec number'].startswith('38.591') for r in projected)
    columns = {'Spec number': 'A', 'CR number': 'B', 'Revision': 'C', 'WG Tdoc': 'K',
               'Release': 'M', 'WG-level status': 'F', 'TSG-level status': 'H',
               'Version-current': 'N', 'Version-new': 'O', 'TSG Tdoc': 'Q',
               'Meeting TSG-level': 'G', 'Meeting WG-level': 'E'}
    pairs, approved, status_counts = Counter(), Counter(), Counter()
    for row in projected:
        assert set(row['fields']) == set(fields) == set(columns)
        assert row['source_cells'] == {k: v + str(row['source_row']) for k, v in columns.items()}
        f = row['fields']
        assert all(isinstance(v, str) for v in f.values())
        pair = f['Release'], f['Spec number']
        pairs[pair] += 1
        status_counts[f['TSG-level status']] += 1
        positive = (f['TSG-level status'] == 'approved' and
                    re.fullmatch(r'\d+\.\d+\.\d+', f['Version-new']) is not None and
                    f['Release'] == 'Rel-' + f['Version-new'].split('.')[0] and
                    f['Version-new'] != f['Version-current'])
        assert positive is row['recorded_approved_numeric_consistent_created_version']
        if positive:
            approved[pair] += 1
    assert len(pairs) == 69 and len(approved) == 66 and sum(approved.values()) == 22466
    assert dict(status_counts) == summary['TSG_status_counts']
    assert [{'release': p[0], 'spec': p[1], 'source_rows': pairs[p],
             'approved_created_version_source_rows': approved[p]} for p in sorted(pairs)] == summary['pairs']
    assert [list(p) for p in sorted(set(pairs) - set(approved))] == summary['three_recorded_pairs_without_approved_created_version']
    axes = {r['releaseName'] for r in graph['release_axis']}
    graph_pairs = {(r['releaseName'], r['specNumber']) for r in graph['requested_pairs']}
    assert graph_pairs == set(pairs) and len(axes) == 11
    native = [json.loads(line) for line in (base / 'actual_native_projected_records.jsonl').read_text().splitlines()]
    assert len(native) == len({r['releaseName'] for r in native}) == 11
    assert {r['releaseName'] for r in native} == axes
    assert {(r['releaseName'], s) for r in native for s in r['specNumbers']} == set(pairs)
    assert sum(not r['specNumbers'] for r in native) == 6
    checks = {'included_projection_full_row_and_cell_checks': 'PASS',
              'included_projection_pair_recount': 69, 'different_approved_created_version_pairs': 66,
              'included_typed_graph_witness_and_native_axis_check': 'PASS',
              'release_axis': 11, 'empty_release_rows': 6,
              'original_CRDB_XML_full_replay': 'NOT_RUN',
              'original_local_SQLite_full_replay': 'NOT_RUN',
              'native_database_execution': 'NOT_RUN', 'domain_expert_evaluation_n': 0}
    if source_root:
        source_root = Path(source_root)
        original = source_root / scope['original_CRDB']['source_path']
        assert original.stat().st_size == scope['original_CRDB']['bytes']
        assert sha(original) == scope['original_CRDB']['sha256']
        count, extracted = projected_original_rows(original, specs, fields)
        assert count == 588415
        expected = [{k: row[k] for k in ('source_row', 'fields', 'source_cells')} for row in projected]
        assert extracted == expected
        checks['original_CRDB_XML_full_replay'] = 'PASS_588415_rows_40091_retained_exact'
        db = source_root / scope['local_relational_snapshot']['source_path']
        assert db.stat().st_size == scope['local_relational_snapshot']['bytes']
        assert sha(db) == scope['local_relational_snapshot']['sha256']
        connection = sqlite3.connect('file:' + str(db.resolve()) + '?mode=ro&immutable=1', uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA query_only=ON')
        actual_axes = [dict(r) for r in connection.execute(graph['release_axis_SQL'])]
        actual_pairs = [dict(r) for r in connection.execute(graph['requested_pairs_SQL'])]
        connection.close()
        assert actual_axes == graph['release_axis']
        assert actual_pairs == graph['requested_pairs']
        checks['original_local_SQLite_full_replay'] = 'PASS_full_Release_and_CR_relation_population'
    return {'status': 'PASS', 'checks': checks,
            'limits': manifest['verification_limits']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path)
    arguments = parser.parse_args()
    print(json.dumps(verify(Path(__file__).resolve().parent, arguments.source_root), ensure_ascii=False))
