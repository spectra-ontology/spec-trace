"""Fresh root replay of every raw input against original members/derivatives.

Uses stdlib XML and independent contiguous paragraph comparison. This verifies
raw XML text, not rendered final state, OCR, binary objects or legacy conversion.
"""
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / 'RAN3_RAN4/calendar58_authored_full_raw_retrieval_inputs_v2'
OUT = HERE / 'RAN4_root_fresh_whole342_and4_raw_replay_v1'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024**2), b''):
            digest.update(block)
    return digest.hexdigest()

def h(data):
    return hashlib.sha256(data).hexdigest()

def literal(paragraph):
    text = []
    for element in paragraph.iter():
        if element.tag in (W+'t', A+'t', M+'t'):
            text.append(element.text or '')
        elif element.tag == W+'tab':
            text.append('\t')
        elif element.tag in (W+'br', W+'cr', A+'br'):
            text.append('\n')
    return ''.join(text)

def shards_bytes(pin):
    blocks = []
    for item in pin['ordered_bin_shards']:
        path = RAW / item['relative_path']
        assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256']
        blocks.append(path.read_bytes())
    data = b''.join(blocks)
    assert len(data) == pin['bytes'] and h(data) == pin['sha256']
    return data

def main():
    resource.setrlimit(resource.RLIMIT_AS, (2*1024**3, 2*1024**3))
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    assert not OUT.exists()
    OUT.mkdir()
    manifest_path = RAW / 'whole_authored_raw_inventory.json'
    assert sha(manifest_path) == '32cf569b1ecf873ead073045f2f51231c3429122a83c27828e0f954d6cf0b1e0'
    manifest = json.loads(manifest_path.read_text())
    raw_path = Path(manifest['raw_inputs_pin']['path'])
    assert sha(raw_path) == manifest['raw_inputs_pin']['sha256']
    combined = hashlib.sha256()
    for item in manifest['raw_inputs_ordered_bin_shards']:
        path = RAW / item['relative_path']
        assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256']
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(4*1024**2), b''):
                combined.update(block)
    assert combined.hexdigest() == sha(raw_path)
    row_number = paragraph_count = character_count = legacy_count = 0
    source_paths = set()
    seen_rows = set()
    def consume(stream, paragraphs, field, XML_sha, expected_source_sha, expected_member_sha, part=None):
        nonlocal row_number, paragraph_count, character_count
        index = 0
        for expected in paragraphs:
            if index == 0:
                row = json.loads(next(stream)); values = row['fields'][field]
                assert values and row['source_row'] not in seen_rows
                seen_rows.add(row['source_row'])
                coordinate = row['source_cell_coordinates']
                start, end = coordinate['paragraph_range_zero_based']
                assert start == paragraph_count_local[0] and end-start+1 == len(values)
                assert coordinate['original_source_sha256'] == expected_source_sha
                assert coordinate['member_sha256'] == expected_member_sha
                assert coordinate['document_XML_sha256' if part is None else 'part_XML_sha256'] == XML_sha
                if part is not None:
                    assert coordinate['part_path'] == part
                row_number += 1
            value = literal(expected)
            assert value == values[index]
            character_count += len(value)
            paragraph_count += 1
            paragraph_count_local[0] += 1
            index += 1
            if index == len(values):
                index = 0
        assert index == 0
    with raw_path.open() as stream:
        for number, record in enumerate(manifest['records']):
            source_pin = record['original_source_pin']; path = Path(source_pin['path'])
            assert path.stat().st_size == source_pin['bytes'] and sha(path) == source_pin['sha256']
            source_paths.add(str(path))
            if path.suffix.lower() == '.zip':
                with zipfile.ZipFile(path) as archive:
                    info = archive.getinfo(record['member']); original = archive.read(info)
            else:
                original = path.read_bytes()
            assert original == shards_bytes(record['original_member_bytes'])
            begin = row_number
            assert begin == record['raw_row_range_zero_based'][0]
            if record['kind'] == 'whole_Word_body':
                derivative = record['access_derivative_bytes']
                data = original
                if derivative:
                    legacy_count += 1
                    data = shards_bytes(derivative)
                    old = record['legacy_conversion_provenance']['output_DOCX_pin']
                    assert data == Path(old['path']).read_bytes() and h(data) == old['sha256']
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    XML = archive.read('word/document.xml')
                assert h(XML) == record['full_document_XML_sha256']
                body = ET.fromstring(XML).find(W+'body'); assert body is not None
                paragraph_count_local = [0]
                consume(stream, body.iter(W+'p'), 'paragraph_texts_in_document_order', h(XML), source_pin['sha256'], h(original))
                assert paragraph_count_local[0] == record['all_body_paragraphs_n']
                del body, XML, data
            else:
                with zipfile.ZipFile(io.BytesIO(original)) as archive:
                    names = sorted(name for name in archive.namelist() if name.lower().endswith('.xml'))
                    assert names == [part['part_path'] for part in record['all_XML_part_inventory']]
                    for part in record['all_XML_part_inventory']:
                        XML = archive.read(part['part_path']); assert h(XML) == part['XML_sha256']
                        root = ET.fromstring(XML)
                        paragraph_count_local = [0]
                        consume(stream, (e for e in root.iter() if e.tag in (A+'p', W+'p')), 'paragraph_texts_in_part_order', h(XML), source_pin['sha256'], h(original), part['part_path'])
                        assert paragraph_count_local[0] == part['paragraphs_n']
                        del XML, root
            assert row_number-1 == record['raw_row_range_zero_based'][1]
            del original
            if (number+1) % 32 == 0:
                print(json.dumps({'sources_verified': number+1, 'paragraphs_verified': paragraph_count}), flush=True)
        assert not stream.readline()
    assert row_number == manifest['raw_rows_n'] == 61730
    assert paragraph_count == manifest['actual_raw_paragraphs_n'] == 6757634
    assert character_count == manifest['actual_raw_text_characters_n'] == 267922412
    assert legacy_count == 23 and len(manifest['records']) == 346
    proof = {'status': 'ROOT_FRESH_ALL342_WHOLE_BODY_AND4_WHOLE_PPTX_RAW_XML_TEXT_PASS',
        'UTC': datetime.now(timezone.utc).isoformat(), 'manifest_sha256': sha(manifest_path),
        'raw_inputs_sha256': sha(raw_path), 'raw_shards_exact_reconstruction': True,
        'whole_Word_bodies_n': 342, 'whole_PPTX_packages_n': 4,
        'legacy_pinned_derivatives_n': legacy_count, 'original_files_n': len(source_paths),
        'raw_rows_n': row_number, 'all_paragraphs_n': paragraph_count,
        'all_raw_characters_n': character_count, 'script_sha256': sha(Path(__file__)),
        'comparison_implementation': 'Independent stdlib XML traversal; all consecutive paragraphs and every original member/shard byte compared.',
        'legacy_reconversion_performed': False, 'rendered_final_state_OCR_or_binary_objects_established': False,
        'human_author_review_completed': False, 'expert_validation_n': 0,
        'new_model_calls_n': 0, 'new_native_calls_n': 0}
    path = OUT / 'receipt.json'; path.write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps({'status': proof['status'], 'receipt_sha256': sha(path)}), flush=True)

if __name__ == '__main__':
    main()
