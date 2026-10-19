#!/usr/bin/env python3
"""Offline original ZIP/XML + whole captured population proof; no native/API."""
import argparse
import collections
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
WORD = re.compile(r'\bcome\s*back\b', re.I)
KEYS = ('id', 'question_en', 'original_query', 'reference_query', 'required_fields', 'collection',
        'cardinality_policy', 'repair_class', 'original_question_preserved')
IDENTITY = '59abc20c9f7da50b8bf77b9238169a5a70e0d064f28347a7154ec882a8204abc'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return {'bytes': Path(path).stat().st_size, 'sha256': h.hexdigest()}


def load(path):
    return json.loads(Path(path).read_text())


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def norm(value):
    return re.sub(r'\s+', ' ', value).strip()


def raw_text(element):
    # Final ordinary Word text only. No equation/drawing rendering claim.
    if element.tag in {W + 'del', W + 'moveFrom', W + 'drawing', W + 'pict', W + 'object'}:
        return ''
    if element.tag == W + 't':
        return element.text or ''
    if element.tag == W + 'tab':
        return '\t'
    if element.tag in {W + 'br', W + 'cr'}:
        return '\n'
    return ''.join(raw_text(child) for child in element)


def iter_blocks(container):
    for child in container:
        if child.tag in {W + 'p', W + 'tbl'}:
            yield child
        elif child.tag in {W + 'sdt', W + 'sdtContent', W + 'customXml'}:
            yield from iter_blocks(child)


def paragraphs(root):
    out = []

    def visit(container, coordinate):
        for bi, block in enumerate(iter_blocks(container)):
            here = f'{coordinate}/b{bi}'
            if block.tag == W + 'p':
                out.append({'coordinate': here, 'text': raw_text(block), 'element': block})
            else:
                for ri, row in enumerate(block.findall(W + 'tr')):
                    for ci, cell in enumerate(row.findall(W + 'tc')):
                        visit(cell, f'{here}/r{ri}/c{ci}')
    body = root.find(W + 'body')
    assert body is not None
    visit(body, 'body')
    return out


def verify(directory, source_root=None):
    directory = Path(directory).resolve()
    manifest = load(directory / 'manifest.json')
    assert manifest['id'] == 'RAN2_P2_CQ2-3' and manifest['repair_sha256'] == IDENTITY
    for name, expected in manifest['files'].items():
        path = (directory / name).resolve()
        assert path.is_relative_to(directory), name
        assert pin(path) == expected, f'embedded_file_pin:{name}'
    for name, expected in manifest['lossless_compressed_files'].items():
        h, size = hashlib.sha256(), 0
        with gzip.open(directory / name, 'rb') as f:
            for block in iter(lambda: f.read(1048576), b''):
                h.update(block)
                size += len(block)
        assert {'bytes': size, 'sha256': h.hexdigest()} == expected['uncompressed'], name

    def rows(name):
        with gzip.open(directory / name, 'rt') as f:
            return [json.loads(line) for line in f if line.strip()]

    definition = load(directory / 'prospective_definition.json')
    kernel = module('comeback_portable_typed_values', directory / 'typed_values.py')
    assert sha(kernel.json_exact({k: definition[k] for k in KEYS}).encode()) == IDENTITY
    assert definition['repair_sha256'] == IDENTITY
    criteria = load(directory / 'criteria.json')
    review = load(directory / 'independent_child_seven_unit_review.json')
    schema = module('comeback_portable_review_schema', directory / 'review_schema.py')
    schema.check_pass(review, definition['question_en'], criteria['semantic_units'],
                      criteria_sha=pin(directory / 'criteria.json')['sha256'], identity_key='repair_sha256', identity_sha=IDENTITY)
    assert definition['required_fields'] == [{'name': 'resolutionId', 'type': 'string', 'nullable': False,
        'source_column_or_expression': 'a.resolutionId; distinct original Agreement record identity'}]
    assert definition['collection'] == {'kind': 'set'}
    assert definition['cardinality_policy'] == {'mode': 'exact', 'value': 10}
    archives = load(directory / 'original_six_archive_portable_locators.json')
    assert len(archives) == 6 and len({a['meeting'] for a in archives}) == 6
    source_paragraphs, source_raw_all_p, xml_pins = {}, 0, {}
    for item in archives:
        path = directory / item['archive_file']
        if source_root is not None:
            path = Path(source_root) / item['original_archive_relative_to_source_root']
            assert pin(path) == item['original_archive_pin']
            assert pin(Path(source_root) / item['retained_report_relative_to_source_root']) == item['retained_report_pin']
        with zipfile.ZipFile(path) as z:
            actual = []
            for member in z.infolist():
                if member.is_dir():
                    continue
                data = z.read(member)
                actual.append({'name': member.filename, 'bytes': len(data), 'CRC32': f'{member.CRC:08x}', 'sha256': sha(data)})
            assert actual == item['all_member_inventory']
            document = z.read(item['exact_report_member']['name'])
        assert sha(document) == item['retained_report_pin']['sha256']
        with zipfile.ZipFile(io.BytesIO(document)) as z:
            xml = z.read('word/document.xml')
            info = z.getinfo('word/document.xml')
        assert {'bytes': len(xml), 'CRC32': f'{info.CRC:08x}', 'sha256': sha(xml)} == item['word_document_XML']
        tree = ET.fromstring(xml)
        pars = paragraphs(tree)
        assert len(pars) == item['protected_body_table_paragraphs_n']
        source_paragraphs[item['meeting']] = pars
        source_raw_all_p += len(list(tree.iter(W + 'p')))
        xml_pins[item['meeting']] = sha(xml)
    captured = rows('whole_frozen3413_neutral_rank_inputs.jsonl.gz')
    diagnostics = rows('whole3413_source_alignment_diagnostics.jsonl.gz')
    candidates = rows('whole5050_source_candidate_observations_not_membership.jsonl.gz')
    panels = rows('whole483_six_report_unfiltered_source_panels.jsonl.gz')
    occurrences = rows('all177_source_occurrence_boundary_audit.jsonl.gz')
    assert len(captured) == len({r['resolutionId'] for r in captured}) == 3413
    assert len(diagnostics) == len({r['resolutionId'] for r in diagnostics}) == 3413
    assert len(candidates) == len({r['source_iri'] for r in candidates}) == 5050
    assert len(panels) == len({r['source_iri'] for r in panels}) == 483
    assert len(occurrences) == 177
    by_id = {r['resolutionId']: r for r in diagnostics}
    by_source = {r['source_iri']: r for r in panels}
    for row in captured:
        d = by_id[row['resolutionId']]
        assert (d['node_id'], d['meeting'], d['meetingNumberInt'], d['recorded_sequence']) == (
            row['node_id'], row['canonicalMeetingNumber'], row['meetingNumberInt'], row['sequence'])
    for panel in panels:
        pars = source_paragraphs[panel['meeting']]
        assert xml_pins[panel['meeting']] == panel['word_document_XML_sha256']
        for witness in panel['whole_candidate_source_body'] + panel['source_prior'] + panel['source_following']:
            assert pars[witness['index']]['coordinate'] == witness['coordinate']
    latest = [r for r in captured if r['meetingNumberInt'] >= 129]
    assert len(latest) == 272
    latest_source_flags = []
    for row in latest:
        diag = by_id[row['resolutionId']]
        assert len(diag['source_candidate_iris']) == 1
        panel = by_source[diag['source_candidate_iris'][0]]
        assert row['resolutionId'] in panel['aligned_original_resolutionIds']
        c = panel['source_candidate']
        pars = source_paragraphs[panel['meeting']]
        source_text = '\n'.join(p['text'] for p in pars[c['marker_document_order_paragraph_index']:c['content_end_document_order_paragraph_index_exclusive']])
        assert bool(WORD.search(source_text)) == bool(WORD.search(row['content']))
        if WORD.search(source_text):
            latest_source_flags.append(row['resolutionId'])
    lexical = [r for r in captured if WORD.search(r['content'])]
    assert len(lexical) == 60
    lexical.sort(key=lambda r: (-r['meetingNumberInt'], r['sequence']))
    selected = lexical[:10]
    selected_ids = {r['resolutionId'] for r in selected}
    assert len(selected_ids) == len(latest_source_flags) == 10
    assert selected_ids == set(latest_source_flags)
    cutoff = (selected[-1]['meetingNumberInt'], selected[-1]['sequence'])
    tied = [r for r in lexical if (r['meetingNumberInt'], r['sequence']) == cutoff]
    assert len(tied) == 1
    assert all(r['meetingNumberInt'] < 129 for r in captured if r not in latest)
    manual = load(directory / 'manual10_source_roles.json')['cases']
    assert {r['original_resolutionId'] for r in manual} == selected_ids
    assert sum(r['conditional_flag_retained_not_condition_satisfied'] for r in manual) == 4
    quote_n = 0
    for row in manual:
        panel = by_source[row['source_iri']]
        pars = source_paragraphs[panel['meeting']]
        for quote in row['source_quote_paragraphs']:
            source = pars[quote['index']]
            assert source['coordinate'] == quote['coordinate']
            assert norm(source['text']) == norm(quote['final_text'])
            assert not list(source['element'].iter(W + 'del'))
            assert not list(source['element'].iter(W + 'strike'))
            quote_n += 1
    boundary = load(directory / 'whole272_cutoff_and_order_roles.json')
    assert boundary['current_parse_sequence_mismatch_n_among10'] == 6
    assert boundary['source_population_warning']['unbound_generic_pattern_candidates_six_reports_n'] == 3
    assert boundary['source_population_warning']['Agreement_style_pattern_occurrences_outside_generic_spans_n'] == 93
    assert sum(1 for r in occurrences if r['existing_candidate_containers']) == 14
    return {
        'status': 'PASS_PORTABLE_ORIGINAL_ARCHIVE_XML_AND_WHOLE_CAPTURED_POPULATION_EVIDENCE',
        'repair_sha256': IDENTITY, 'files_checked_n': len(manifest['files']),
        'original_archives_n': 6, 'all_raw_XML_w_p': source_raw_all_p,
        'body_table_paragraphs': sum(map(len, source_paragraphs.values())),
        'captured_original_records': 3413, 'unfiltered_latest_source_dependencies': 272,
        'word_predicate_records': len(lexical), 'effective_flags': len(selected_ids), 'cutoff_group_size': len(tied),
        'raw_XML_quote_witnesses_n': quote_n, 'conditional_reopeners': 4, 'sequence_disagreements_preserved': 6,
        'source_root_reopened': source_root is not None,
        'native_SQL_or_API_executed': False, 'current_protected_renderer_executed': False,
        'semantic_truth_or_physical_population_completeness_proved_by_verifier': False,
        'verification_fixture_is_model_input': False,
    }


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('directory', nargs='?', type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument('--source-root', type=Path)
    args = ap.parse_args()
    print(json.dumps(verify(args.directory, args.source_root), ensure_ascii=False))
