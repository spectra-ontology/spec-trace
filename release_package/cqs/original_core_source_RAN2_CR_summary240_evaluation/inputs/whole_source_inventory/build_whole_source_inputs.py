#!/usr/bin/env python3
"""Build raw meeting-source inputs from a physical, unfiltered inventory.

Reads original archives and authenticated existing conversion outputs. It does
not read task definitions, reference answers, native databases, or model output.
No converter, network, model, or container is invoked. Existing inputs are never
written. Each invocation requires a new output directory.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import posixpath
import time
import xml.etree.ElementTree as ET
import zipfile


PROJECT_ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
S = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR = 'http://schemas.openxmlformats.org/package/2006/relationships'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(2**20), b''):
            h.update(chunk)
    return h.hexdigest()


def resolve(path):
    p = Path(path)
    if p.is_absolute():
        # Existing receipts are historical records containing absolute paths.
        p.relative_to(PROJECT_ROOT)
        return p
    p = (PROJECT_ROOT / p).resolve()
    p.relative_to(PROJECT_ROOT)
    return p


def rel(path):
    return str(Path(path).resolve().relative_to(PROJECT_ROOT))


def pin(path):
    p = resolve(path)
    return {'path': rel(p), 'sha256': file_sha(p), 'bytes': p.stat().st_size}


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def write_line(f, value):
    f.write(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n')


def check_pin(expected):
    actual = pin(expected['path'])
    if actual['sha256'] != expected['sha256']:
        raise ValueError('Existing source pin mismatch: ' + actual['path'])
    if 'bytes' in expected and actual['bytes'] != expected['bytes']:
        raise ValueError('Existing source size mismatch: ' + actual['path'])
    return actual


def load_conversion_map(specs):
    """Project only conversion provenance, never ledger content/answer fields."""
    mapping, inputs = {}, []
    for spec in specs:
        source = resolve(spec['receipt'])
        receipt = json.loads(source.read_text())
        receipt_pin = pin(source)
        inputs.append(receipt_pin)
        kind = spec['format']
        entries = []
        if kind == 'RAN3_members':
            for x in receipt['members']:
                if x.get('decode_status') == 'strict_decoded_XML_read':
                    entries.append((x['original_member_sha256'],
                                    {'path': x['input_path'], 'sha256': x['input_sha256']},
                                    {'path': x['decoded_output_path'], 'sha256': x['decoded_output_sha256']}))
        elif kind == 'RAN2_single':
            if receipt['exit_code'] != 0:
                continue
            entries.append((receipt['primary_member']['sha256'], receipt['isolated_copy_pin'], receipt['output_DOCX_pin']))
        elif kind == 'RAN2_recovery_ledger':
            ledger_pin = receipt['output_pin']
            inputs.append(check_pin(ledger_pin))
            for line in resolve(ledger_pin['path']).open():
                if not line.strip():
                    continue
                row = json.loads(line)
                for x in row.get('member_reviews', []):
                    if x.get('state') == 'derived_DOCX_header_read' and x.get('derived_DOCX_pin'):
                        entries.append((x['original_member_sha256'], x['private_original_member_pin'], x['derived_DOCX_pin']))
        elif kind == 'RAN3_conversion_ledger':
            ledger_pin = {'path': receipt['ledger_path'], 'sha256': receipt['ledger_sha256']}
            inputs.append(check_pin(ledger_pin))
            for line in resolve(ledger_pin['path']).open():
                if not line.strip():
                    continue
                x = json.loads(line)
                if x.get('decode_status') == 'strict_decoded_XML_read':
                    entries.append((x['original_member_sha256'],
                                    {'path': x['local_input_path'], 'sha256': x['local_input_sha256']},
                                    {'path': x['decoded_output_path'], 'sha256': x['decoded_output_sha256']}))
        else:
            raise ValueError('Unknown conversion receipt schema: ' + kind)
        for original_sha, input_pin, output_pin in entries:
            if original_sha != input_pin['sha256']:
                raise ValueError('Receipt does not bind exact original member')
            mapping.setdefault(original_sha, []).append({
                'receipt': receipt_pin, 'original_input': input_pin, 'decoded_output': output_pin})
    return mapping, inputs


def paragraph_text(paragraph, symbol_map):
    text, symbols = [], []
    for x in paragraph.iter():
        if x.tag in (f'{{{W}}}t', f'{{{W}}}delText', f'{{{M}}}t', f'{{{W}}}instrText', f'{{{W}}}delInstrText'):
            text.append(x.text or '')
        elif x.tag == f'{{{W}}}tab':
            text.append('\t')
        elif x.tag in (f'{{{W}}}br', f'{{{W}}}cr'):
            text.append('\n')
        elif x.tag == f'{{{W}}}sym':
            font, char = x.get(f'{{{W}}}font', ''), x.get(f'{{{W}}}char', '')
            key = font + ':' + char.upper()
            glyph = symbol_map.get(key)
            symbols.append({'font': font, 'char': char, 'generic_unicode_glyph': glyph})
            text.append(glyph if glyph is not None else '[w:sym font=' + font + ' char=' + char + ']')
    result = {'literal_text_all_tracked_states': ''.join(text)}
    if symbols:
        result['literal_symbol_elements'] = symbols
    return result


class Builder:
    def __init__(self, config, out):
        self.config, self.out = config, out
        self.raw = (out / 'raw_source_records.jsonl').open('w')
        self.inventory = (out / 'physical_source_inventory.jsonl').open('w')
        self.results = (out / 'source_access_results.jsonl').open('w')
        self.counts, self.formats, self.statuses = Counter(), Counter(), Counter()
        self.input_pins, self.reused = [], []
        self.conversions, self.conversion_input_pins = load_conversion_map(config.get('existing_conversion_receipts', []))

    def record(self, fields, coordinates):
        self.counts['raw_records_n'] += 1
        write_line(self.raw, {'source_row': self.counts['raw_records_n'], 'fields': fields, 'source_cell_coordinates': coordinates})

    def result(self, source, status, **extra):
        self.statuses[status] += 1
        write_line(self.results, {'source': source, 'status': status, **extra})

    def word(self, data, source, original_sha, conversion=None):
        data_sha = digest(data)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if 'word/document.xml' not in z.namelist():
                raise ValueError('DOCX has no word/document.xml')
            total, parts = 0, []
            for name in sorted(n for n in z.namelist() if n.startswith('word/') and n.endswith('.xml')):
                xml = z.read(name)
                xml_sha = digest(xml)
                tree = ET.fromstring(xml)
                ps = list(tree.iter(f'{{{W}}}p'))
                if not ps:
                    continue
                parts.append({'part': name, 'sha256': xml_sha, 'paragraphs_n': len(ps)})
                for start in range(0, len(ps), self.config['paragraphs_per_record']):
                    group = ps[start:start + self.config['paragraphs_per_record']]
                    text = [{'paragraph_zero_based': start + i, **paragraph_text(p, self.config['symbol_mapping'])} for i, p in enumerate(group)]
                    fields = {'source': 'Original meeting source', 'filename': Path(source[-1]['name']).name,
                              'origin': self.config['meeting_source_relative_dir'], 'meetingNumber': self.config['meeting'],
                              'source_location': source, 'document_text_state': 'Literal XML text including tracked insertions/deletions, fields and math; not a selected final-visible answer projection',
                              'paragraphs': text}
                    coordinates = {'physical_member_sha256': original_sha, 'OOXML_part': name,
                                   'OOXML_part_sha256': xml_sha, 'coordinate_domain': 'Existing converted DOCX XML' if conversion else 'Original DOCX XML',
                                   'paragraphs': [{'paragraph_zero_based': start+i, 'parsed_paragraph_XML_sha256': digest(ET.tostring(p))} for i, p in enumerate(group)]}
                    if conversion:
                        coordinates['existing_converted_DOCX_sha256'] = data_sha
                        coordinates['conversion_receipt_sha256'] = conversion['receipt']['sha256']
                    self.record(fields, coordinates)
                total += len(ps)
            self.counts['word_documents_text_read_n'] += 1
            self.counts['word_paragraphs_n'] += total
            self.result(source, 'existing_authenticated_DOC_conversion_text_read' if conversion else 'original_DOCX_text_read',
                        physical_member_sha256=original_sha, text_paragraphs_n=total, parts=parts)

    def workbook(self, data, source, original_sha):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
                strings = [''.join(x.itertext()) if not list(x.iter(f'{{{S}}}t')) else ''.join(t.text or '' for t in x.iter(f'{{{S}}}t')) for x in tree]
            names = {}
            if 'xl/workbook.xml' in z.namelist() and 'xl/_rels/workbook.xml.rels' in z.namelist():
                links = {x.get('Id'): x.get('Target') for x in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
                for sh in ET.fromstring(z.read('xl/workbook.xml')).iter(f'{{{S}}}sheet'):
                    target = links.get(sh.get(f'{{{R}}}id'), '')
                    part = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
                    names[part] = {'name': sh.get('name'), 'state': sh.get('state', 'visible')}
            sheets = []
            for name in sorted(n for n in z.namelist() if n.startswith('xl/worksheets/') and n.endswith('.xml')):
                xml = z.read(name)
                xml_sha = digest(xml)
                tree = ET.fromstring(xml)
                rows = list(tree.iter(f'{{{S}}}row'))
                for row in rows:
                    cells = []
                    for cell in row.findall(f'{{{S}}}c'):
                        typ = cell.get('t', '')
                        value = cell.find(f'{{{S}}}v')
                        value = '' if value is None else (value.text or '')
                        if typ == 's':
                            value = strings[int(value)] if value else ''
                        elif typ == 'inlineStr':
                            value = ''.join(x.text or '' for x in cell.iter(f'{{{S}}}t'))
                        item = {'coordinate': cell.get('r'), 'type': typ, 'literal_value': value}
                        formula = cell.find(f'{{{S}}}f')
                        if formula is not None:
                            item['literal_formula'] = formula.text or ''
                            item['formula_attributes'] = dict(formula.attrib)
                        cells.append(item)
                    self.record({'source': 'Original meeting source workbook', 'filename': Path(source[-1]['name']).name,
                                 'origin': self.config['meeting_source_relative_dir'], 'meetingNumber': self.config['meeting'],
                                 'source_location': source, 'worksheet': names.get(name, {}), 'row_1based': row.get('r'), 'cells': cells},
                                {'physical_member_sha256': original_sha, 'OOXML_part': name, 'OOXML_part_sha256': xml_sha,
                                 'parsed_row_XML_sha256': digest(ET.tostring(row)), 'coordinate_domain': 'Original workbook XML'})
                sheets.append({'part': name, 'sha256': xml_sha, 'sparse_XML_rows_n': len(rows), **names.get(name, {})})
                self.counts['workbook_sparse_XML_rows_n'] += len(rows)
            self.counts['workbooks_text_read_n'] += 1
            self.result(source, 'original_XLSX_all_worksheets_text_read', physical_member_sha256=original_sha, worksheets=sheets)

    def visit(self, data, source, outer=False):
        sha = digest(data)
        suffix = Path(source[-1]['name']).suffix.lower()
        inv = {'source': source, 'sha256': sha, 'bytes': len(data), 'filename_suffix': suffix, 'outer_physical_file': outer}
        write_line(self.inventory, inv)
        self.counts['physical_inventory_entries_n'] += 1
        self.formats[suffix or '(no suffix)'] += 1
        try:
            # OLE DOCs can contain an embedded theme ZIP, which zipfile detects.
            # That does not make the outer binary document an OOXML package.
            is_ole = data.startswith(bytes.fromhex('D0CF11E0A1B11AE1'))
            if not is_ole and zipfile.is_zipfile(io.BytesIO(data)):
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    names = z.namelist()
                    if 'word/document.xml' in names:
                        self.word(data, source, sha)
                    elif 'xl/workbook.xml' in names:
                        self.workbook(data, source, sha)
                    elif '[Content_Types].xml' in names:
                        # Preserve all bytes by pin; no unsupported Office view is fabricated.
                        self.result(source, 'unsupported_Office_package_text_view', physical_member_sha256=sha, package_parts_n=len(names))
                    else:
                        members = [x for x in z.infolist() if not x.is_dir()]
                        self.counts['container_archives_n'] += 1
                        self.result(source, 'archive_inventory_traversed', physical_member_sha256=sha, member_files_n=len(members))
                        for item in members:
                            child_source = source + [{'name': item.filename, 'container_sha256': sha}]
                            try:
                                child = z.read(item)
                            except Exception as e:
                                self.result(child_source, 'archive_member_read_failed', error=type(e).__name__ + ': ' + str(e))
                                continue
                            self.visit(child, child_source)
                return
            if suffix == '.doc':
                candidates = self.conversions.get(sha, [])
                for conversion in candidates:
                    try:
                        original = check_pin(conversion['original_input'])
                        decoded = check_pin(conversion['decoded_output'])
                        if original['sha256'] != sha:
                            raise ValueError('Conversion original bytes differ from the current physical member')
                        data2 = resolve(decoded['path']).read_bytes()
                        if not zipfile.is_zipfile(io.BytesIO(data2)):
                            raise ValueError('Existing conversion is not DOCX')
                        self.word(data2, source, sha, conversion)
                        self.reused.append({'physical_source': source, 'original_member_sha256': sha,
                                            'receipt': conversion['receipt'], 'original_input': original, 'decoded_output': decoded})
                        return
                    except Exception as e:
                        self.result(source, 'existing_conversion_reuse_failed', physical_member_sha256=sha, receipt=conversion['receipt'], error=type(e).__name__ + ': ' + str(e))
                self.result(source, 'unsupported_binary_DOC_without_verified_existing_text_view', physical_member_sha256=sha, existing_candidate_n=len(candidates))
                return
            if suffix in self.config['literal_text_file_suffixes']:
                text = data.decode('utf-8-sig')
                self.record({'source': 'Original meeting source text file', 'filename': Path(source[-1]['name']).name,
                             'origin': self.config['meeting_source_relative_dir'], 'meetingNumber': self.config['meeting'],
                             'source_location': source, 'literal_text': text},
                            {'physical_member_sha256': sha, 'coordinate_domain': 'Original UTF-8 text file'})
                self.result(source, 'original_UTF8_text_read', physical_member_sha256=sha)
                return
            self.result(source, 'unsupported_source_format_text_view', physical_member_sha256=sha)
        except Exception as e:
            self.result(source, 'text_access_failed', physical_member_sha256=sha, error=type(e).__name__ + ': ' + str(e))

    def run(self, config_path):
        start = time.monotonic()
        physical_root = resolve(self.config['meeting_source_relative_dir'])
        physical_files = sorted(p for sub in self.config['included_physical_subdirectories'] for p in (physical_root/sub).rglob('*') if p.is_file())
        for i, path in enumerate(physical_files):
            before = pin(path)
            self.input_pins.append(before)
            self.visit(path.read_bytes(), [{'name': rel(path)}], outer=True)
            if pin(path) != before:
                raise ValueError('Original physical input changed during read: ' + rel(path))
            if (i+1) % 100 == 0:
                print(json.dumps({'meeting': self.config['meeting'], 'physical_files_read_n': i+1, 'total_physical_files_n': len(physical_files), 'raw_records_n': self.counts['raw_records_n']}), flush=True)
        for handle in (self.raw, self.inventory, self.results):
            handle.close()
        dump(self.out/'existing_conversion_reuse.json', self.reused)
        outputs = {name: pin(self.out/name) for name in ('raw_source_records.jsonl', 'physical_source_inventory.jsonl', 'source_access_results.jsonl', 'existing_conversion_reuse.json')}
        manifest = {'kind': 'Whole physical meeting source universe with explicit text availability',
                    'created_utc': datetime.now(timezone.utc).isoformat(), 'meeting': self.config['meeting'],
                    'builder': pin(Path(__file__)), 'configuration': pin(config_path),
                    'common_source_context_policy': pin(self.config['common_source_context_policy']),
                    'existing_generic_symbol_interpretation_receipt': pin(self.config['symbol_mapping_existing_source_receipt']),
                    'source_selection': 'Every physical file below the configured Docs and Report directories, every ordinary nested archive member, every readable whole DOCX text part, every XLSX worksheet and sparse XML row. No type, status, TDoc or answer-based selection.',
                    'original_outer_physical_files_n': len(physical_files), 'original_outer_physical_file_pins': self.input_pins,
                    'existing_conversion_receipt_and_ledger_pins': self.conversion_input_pins,
                    'counts': dict(self.counts), 'filename_suffix_inventory_counts': dict(self.formats), 'source_access_status_counts': dict(self.statuses),
                    'verified_existing_conversion_reuses_n': len(self.reused), 'outputs': outputs,
                    'query_gold_definition_or_model_output_read_by_builder': False,
                    'external_API_calls_n': 0, 'native_calls_n': 0, 'new_conversions_n': 0,
                    'central_registry_or_public_writes_n': 0, 'input_writes_n': 0,
                    'all_outer_physical_input_pins_unchanged_during_read': True,
                    'whole_physical_inventory_complete': True,
                    'whole_text_available': not any(n for status,n in self.statuses.items() if status.startswith(('unsupported_', 'text_access_failed', 'archive_member_read_failed'))),
                    'limitations': [
                        'Physical inventory coverage and text availability are separate. Unsupported formats and failed reads remain pinned and explicit.',
                        'Existing DOC conversions are access derivatives, not original binary XML. Their original input and current physical member SHA256 must match.',
                        'Whole text includes tracked insertions/deletions and field instruction text; it is not the final-visible renderer used to judge the reference source cells.',
                        'Images, drawing-only content, embedded objects, macros, formatting and unsupported Office package types have no new visual/text conversion.',
                        'Only the listed existing conversion ledgers are searched. No claim is made that every conversion elsewhere on disk has been discovered.',
                        'No lexical SQLite has been cloned or changed by this builder, and no model context has been supplied or evaluated.'],
                    'elapsed_seconds': round(time.monotonic()-start,3)}
        dump(self.out/'manifest.json', manifest)
        plan = {'raw_records': rel(self.out/'raw_source_records.jsonl'), 'expected_n': self.counts['raw_records_n'],
                'wg': self.config['wg'], 'base_lexical_corpus': self.config['base_lexical_corpus'],
                'collection': self.config['collection'], 'common_source_context_policy': self.config['common_source_context_policy'],
                'augmentation_not_executed': True}
        dump(self.out/'corpus_augmentation_plan.json', plan)
        print(json.dumps({'status': 'RAW_SOURCE_INPUTS_BUILT', 'meeting': self.config['meeting'], 'raw_records_n': self.counts['raw_records_n'],
                          'whole_text_available': manifest['whole_text_available'], 'manifest': rel(self.out/'manifest.json'), 'manifest_sha256': file_sha(self.out/'manifest.json')}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    config_path, out = resolve(args.config), resolve(args.out)
    if out.exists():
        raise ValueError('Refuse to overwrite an existing output directory')
    out.relative_to(Path(__file__).resolve().parent)
    config = json.loads(config_path.read_text())
    if config['paragraphs_per_record'] != 24:
        raise ValueError('Preserve the existing raw-source builder paragraph chunk policy')
    out.mkdir(parents=True)
    Builder(config, out).run(config_path)


if __name__ == '__main__':
    main()
