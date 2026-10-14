#!/usr/bin/env python3
"""Reopen original reports for unchanged cases; distinguish body and ZIP identity."""
from collections import Counter, defaultdict
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

import source_audit as old


W = old.W


def digest(path):
    return old.digest(path)


def relative(path):
    return str(path.resolve().relative_to(old.ROOT))


def meeting_number(value):
    text = re.sub(r'^TSGR[1-5]_+', '', value, flags=re.I)
    match = re.match(r'^(\d+)(?:[-_ ]?(bis|b))?(?=[_\-\s]|$)', text, re.I)
    return (int(match[1]), bool(match[2])) if match else None


def visible_paragraph_pin(rows):
    # All paragraphs/cells, in order, with only the existing whitespace rule.
    data = [old.norm(row['text']) for row in rows]
    return hashlib.sha256(json.dumps(data, ensure_ascii=False).encode()).hexdigest()


def heading_candidates(data):
    with zipfile.ZipFile(io.BytesIO(data)) as zipped:
        body = ET.fromstring(zipped.read('word/document.xml')).find(W + 'body')
        styles = ET.fromstring(zipped.read('word/styles.xml')) if 'word/styles.xml' in zipped.namelist() else None
    definitions = {}
    if styles is not None:
        for style in styles.findall(W + 'style'):
            name = style.find(W + 'name')
            parent = style.find(W + 'basedOn')
            outline = style.find('./' + W + 'pPr/' + W + 'outlineLvl')
            definitions[style.get(W + 'styleId')] = {
                'name': name.get(W + 'val', '') if name is not None else '',
                'parent': parent.get(W + 'val') if parent is not None else None,
                'outline': outline.get(W + 'val') if outline is not None else None}
    def heading_style(style_id, visited=None):
        visited = set() if visited is None else visited
        if not style_id or style_id in visited:
            return False
        visited.add(style_id)
        info = definitions.get(style_id, {})
        if re.fullmatch(r'heading\s*\d+', info.get('name', ''), re.I) or re.fullmatch(r'Heading\d+', style_id, re.I):
            return True
        if info.get('outline') is not None and int(info['outline']) < 9:
            return True
        return heading_style(info.get('parent'), visited)
    rows, para_n = [], 0
    for body_index, element in enumerate(body):
        if element.tag != W + 'p':
            continue
        locator = {'body_index': body_index, 'paragraph_index': para_n}
        para_n += 1
        style = element.find('./' + W + 'pPr/' + W + 'pStyle')
        style_id = style.get(W + 'val') if style is not None else None
        outline = element.find('./' + W + 'pPr/' + W + 'outlineLvl')
        is_heading = heading_style(style_id) or (outline is not None and int(outline.get(W + 'val')) < 9)
        if not is_heading:
            continue
        # Preserve native tabs/breaks. Do not generate automatic list numbering.
        pieces = []
        for part in element.iter():
            if part.tag == W + 't':
                pieces.append(part.text or '')
            elif part.tag == W + 'tab':
                pieces.append('\t')
            elif part.tag in [W + 'br', W + 'cr']:
                pieces.append('\n')
        text = ''.join(pieces)
        match = re.match(r'^\s*(\d+(?:\.\d+){0,6})\.?\s+\S', text)
        # A heading with unreconstructed automatic numbering clears the scope;
        # never skip it to inherit a more convenient numbered ancestor.
        rows.append({'locator': locator, 'native_heading_text': text,
                     'style': style_id, 'explicit_agenda_candidate': match[1] if match else None})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base, output = args.base, args.output
    output.mkdir(exist_ok=False)
    sample_path, prior_path = base / 'source-audit/sampling.json', base / 'source-audit/results.json'
    sample, prior = json.loads(sample_path.read_text()), json.loads(prior_path.read_text())
    relations = ['REFERENCES', 'MADE_AT', 'RESOLUTION_BELONGS_TO']
    fixed = [case for case in sample['cases'] if case['relation'] in relations]
    previous = {(case['sample_identity'], case['relation'], case['direction']): case for case in prior['cases']}
    reports = {}
    for case in fixed:
        if case['direction'] == 'source_first':
            reports[case['source']['source_path']] = case['wg']
        for occurrence in previous[(case['sample_identity'], case['relation'], case['direction'])]['result'].get('source_occurrences', []):
            reports[occurrence['source']['path']] = case['wg']
    inventory = {}
    for path, wg in sorted(reports.items()):
        label = old.report_meeting(Path(path), wg)
        key = meeting_number(label)
        root = old.ROOT / f'data/corpus/tsg/RAN/formal/meetings/{wg}/source'
        files = [file for folder in sorted(root.iterdir())
                 if folder.is_dir() and key is not None and meeting_number(folder.name) == key
                 for file in sorted((folder / 'Report').rglob('*'))
                 if file.is_file() and file.suffix.lower() in ['.docx', '.zip']]
        inventory[path] = {'wg': wg, 'unchanged_meeting_label': label,
                           'candidate_original_files': [relative(file) for file in files]}
    protocol = {
        'classification': 'NEW_MEASUREMENT_ON_FIXED_CASES_AND_READER_FORMAT_CORRECTION',
        'sampling_sha256': digest(sample_path), 'previous_results_sha256': digest(prior_path),
        'producer_sha256': digest(Path(__file__)), 'fixed_cases_n': len(fixed),
        'source_frame': ('Native direct DOCX files and DOCX ZIP members in every same-WG '
                         'meeting-number/bis folder, including city/electronic suffixes. '
                         'All candidates are inventoried before comparison. Meeting labels '
                         'used in frozen comparisons remain unchanged.'),
        'admission': ('Exact retained/native DOCX bytes, exact main-document XML, or equality '
                      'of every ordered visible-body paragraph/cell after the existing whitespace '
                      'normalization. Body equivalence does not imply whole-package equivalence.'),
        'agenda': ('Recognize native heading styles including basedOn/outlineLvl and native tab '
                   'separators. Require an explicit literal heading number. Automatic numbering '
                   'is not reconstructed and clears the nearest-heading scope. Heading evidence '
                   'is structural provenance, not expert adjudication.'),
        'original_content_matching': 'No new substring/approximate graph binding; old fixed complete-span and identity constraints retained.',
        'model_calls': 0, 'database_calls': 0, 'expert_reviews': 0}
    (output / 'protocol.json').write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + '\n')
    (output / 'inventory_before_comparison.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n')
    pins, authentication, native_data = {}, {}, {}
    for path, definition in inventory.items():
        retained_path = old.ROOT / path
        pins[path] = digest(retained_path)
        retained = retained_path.read_bytes()
        retained_rows = old.paragraphs(retained)
        expected = visible_paragraph_pin(retained_rows)
        with zipfile.ZipFile(io.BytesIO(retained)) as zipped:
            retained_xml_sha = hashlib.sha256(zipped.read('word/document.xml')).hexdigest()
        matches, errors, attempted_n = [], [], 0
        for original in definition['candidate_original_files']:
            original_path = old.ROOT / original
            pins.setdefault(original, digest(original_path))
            if original_path.suffix.lower() == '.zip':
                try:
                    with zipfile.ZipFile(original_path) as zipped:
                        payloads = [(name, zipped.read(name)) for name in zipped.namelist() if name.lower().endswith('.docx')]
                except (OSError, zipfile.BadZipFile) as exc:
                    errors.append({'file': original, 'error': type(exc).__name__})
                    continue
            else:
                payloads = [(None, original_path.read_bytes())]
            for member, data in payloads:
                attempted_n += 1
                try:
                    rows = old.paragraphs(data)
                    paragraph_pin = visible_paragraph_pin(rows)
                    with zipfile.ZipFile(io.BytesIO(data)) as zipped:
                        xml_sha = hashlib.sha256(zipped.read('word/document.xml')).hexdigest()
                    if paragraph_pin != expected:
                        continue
                    exact_bytes = hashlib.sha256(data).hexdigest() == pins[path]
                    mode = 'exact_native_DOCX_bytes' if exact_bytes else 'exact_native_main_document_XML' if xml_sha == retained_xml_sha else 'all_ordered_visible_body_paragraphs_equal_after_whitespace_normalization'
                    match = {'original_file': original, 'original_file_sha256': pins[original],
                             'member': member, 'native_DOCX_sha256': hashlib.sha256(data).hexdigest(),
                             'native_main_document_XML_sha256': xml_sha,
                             'complete_ordered_visible_body_sha256': paragraph_pin,
                             'visible_paragraphs_n': len(rows), 'authentication_scope': mode,
                             'byte_identical_to_retained_DOCX': exact_bytes,
                             'native_headings': heading_candidates(data)}
                    matches.append(match)
                    # Retain only paragraph locators, not every report's text.
                    # Whole-body equality has already fixed their ordered mapping.
                    native_data[(path, len(matches)-1)] = [row['locator'] for row in rows]
                except (OSError, zipfile.BadZipFile, ET.ParseError, KeyError) as exc:
                    errors.append({'file': original, 'member': member, 'error': type(exc).__name__})
        authentication[path] = {'retained_sha256': pins[path], 'retained_visible_body_sha256': expected,
                                'original_DOCX_members_checked_n': attempted_n,
                                'native_matches': matches, 'errors': errors,
                                'native_status': 'original_visible_body_authenticated' if matches else 'unresolved_original_body_authentication'}
        print('original_report_body_checked', definition['wg'], definition['unchanged_meeting_label'], len(matches), flush=True)
    rows, changed = [], []
    for case in fixed:
        key = (case['sample_identity'], case['relation'], case['direction'])
        before = previous[key]['result']
        graph_matches = case['graph_matches'] if case['direction'] == 'source_first' else [case['graph']]
        result = {'status': 'unresolved', 'previous_status': before['status'],
                  'fixed_identity': case['sample_identity'], 'relation': case['relation'],
                  'direction': case['direction'], 'wg': case['wg'],
                  'graph_identity_n': len(graph_matches), 'occurrences': []}
        occurrences = before.get('source_occurrences', [])
        for occurrence in occurrences:
            source = occurrence['source']['path']
            old_retained_rows = old.paragraphs((old.ROOT / source).read_bytes())
            index = {json.dumps(row['locator'], sort_keys=True): i for i, row in enumerate(old_retained_rows)}
            begin = index[json.dumps(occurrence['quotes'][0]['locator'], sort_keys=True)]
            mapped = []
            for native_index, candidate in enumerate(authentication[source]['native_matches']):
                native_rows = native_data[(source, native_index)]
                source_start = native_rows[begin]
                headings = [h for h in candidate['native_headings'] if h['locator']['body_index'] <= source_start['body_index']]
                nearest = headings[-1] if headings else None
                mapped.append({'native_match_index': native_index, 'native_start_locator': source_start,
                               'nearest_native_heading': nearest})
            result['occurrences'].append({'retained_source': source,
                'meeting_label': occurrence['source']['meeting_label'],
                'original_complete_paragraph_span_equal': occurrence['full_original_paragraph_span_equal'],
                'citation_ids': occurrence['source_reference_ids'], 'native_mappings': mapped})
        if not occurrences:
            result['reason'] = before.get('reason', 'complete_graph_content_not_located')
        elif len(graph_matches) != 1:
            result['reason'] = 'graph_identity_absent_or_nonunique'
        elif not all(row['native_mappings'] for row in result['occurrences']):
            result['reason'] = 'original_body_authentication_unresolved'
        elif not all(row['original_complete_paragraph_span_equal'] for row in result['occurrences']):
            result['reason'] = 'source_occurrence_is_partial_original_paragraph_span'
        else:
            relation = case['relation']
            if relation == 'REFERENCES':
                sets = {tuple(row['citation_ids']) for row in result['occurrences']}
                if len(sets) == 1:
                    source_set = list(next(iter(sets)))
                    graph_set = [old.target_tail(value) for value in graph_matches[0]['targets'][relation]]
                    comparison = old.set_difference(source_set, graph_set)
                    result['comparison'] = comparison
                    result['status'] = 'citation_token_set_match' if comparison['exact_set_equal'] else 'citation_token_set_mismatch'
                else:
                    result['reason'] = 'different_original_occurrences_carry_different_citations'
            elif relation == 'MADE_AT':
                source_set = sorted({row['meeting_label'].casefold() for row in result['occurrences']})
                graph_set = sorted({old.target_tail(value).removeprefix('meeting/' + case['wg'] + '_').casefold() for value in graph_matches[0]['targets'][relation]})
                result['comparison'] = old.set_difference(source_set, graph_set)
                if len(source_set) > 1 or len(graph_set) > 1:
                    result['reason'] = 'multiple_meeting_identity_or_repeated_source_content_requires_adjudication'
                else:
                    result['status'] = 'provenance_set_match' if result['comparison']['exact_set_equal'] else 'provenance_set_mismatch'
            else:
                candidates = [mapping['nearest_native_heading']['explicit_agenda_candidate']
                              if mapping['nearest_native_heading'] is not None else None
                              for occurrence in result['occurrences'] for mapping in occurrence['native_mappings']]
                if None in candidates or not candidates:
                    result['reason'] = 'nearest_native_heading_has_no_explicit_literal_number'
                else:
                    graph_set = [old.target_tail(value).removeprefix('agenda/').split('-', 1)[-1] for value in graph_matches[0]['targets'][relation]]
                    result['comparison'] = old.set_difference(candidates, graph_set)
                    result['status'] = 'heading_candidate_set_match' if result['comparison']['exact_set_equal'] else 'heading_candidate_set_mismatch'
        if result['status'] != before['status']:
            changed.append({'identity': case['sample_identity'], 'relation': case['relation'],
                            'direction': case['direction'], 'before': before['status'],
                            'after': result['status']})
        rows.append(result)
    drift = [path for path, pin in pins.items() if digest(old.ROOT / path) != pin]
    summary = defaultdict(Counter)
    for row in rows:
        summary[row['relation'] + '/' + row['direction']][row['status']] += 1
    # Large native heading inventories stay in local producer output; exported
    # cases contain only selected locators and their nearest heading evidence.
    for entry in authentication.values():
        for match in entry['native_matches']:
            match.pop('native_headings')
    report = {'status': 'PASS' if not drift else 'INPUT_DRIFT',
              'protocol_sha256': digest(output / 'protocol.json'),
              'sampling_sha256': protocol['sampling_sha256'],
              'fixed_report_case_n': len(rows), 'requested_full_audit_n': 500,
              'original_full_selected_n': 491, 'original_missing_slots_n': 9,
              'counts': {key: dict(value) for key, value in summary.items()},
              'changed_cases': changed, 'cases': rows, 'report_authentication': authentication,
              'inspected_source_sha256': pins, 'input_drift_paths': drift,
              'unresolved_graph_content_and_identity_constraints_unchanged': True,
              'expert_reviews': 0, 'model_calls': 0, 'database_calls': 0,
              'limits': ['Full-body equality authenticates only the defined visible paragraph/cell extraction.',
                         'Source paragraph graph absence can reflect aggregation and is not inferred to be an erroneous missing edge.',
                         'Citation matches do not establish endorsement; heading candidates are not expert semantic judgments.',
                         'Meeting suffixes and graph identities were not rewritten; automatic numbering remains unexpanded.',
                         'These fixed cases cannot establish whole-corpus accuracy or completeness.']}
    (output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'fixed_cases': len(rows),
                      'reports_checked': len(authentication), 'input_pins': len(pins),
                      'counts': report['counts'], 'changed_cases': len(changed)}, indent=2), flush=True)
    assert not drift


if __name__ == '__main__':
    main()
