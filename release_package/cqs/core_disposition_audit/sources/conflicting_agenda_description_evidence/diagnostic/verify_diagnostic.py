"""Replay a bounded original-agenda conflict; no answer policy is selected."""
import argparse
import copy
import encodings.ascii
import encodings.cp437
from decimal import Decimal
from fractions import Fraction
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

if sys.flags.optimize:
    raise RuntimeError('Optimized execution is not supported')
sys.dont_write_bytecode = True


def no_symlink(path):
    path = Path(os.path.abspath(os.fspath(path)))
    for part in (path, *path.parents):
        if part.is_symlink():
            raise RuntimeError('Symlink boundary rejected')


no_symlink(__file__)
PACKAGE_ROOT = Path(__file__).resolve().parent
EXPECTED_INVENTORY_SHA256 = '0e971bc1b77b6d046dfc74ddf47ffe5a1807f1f26ae2513792bfcc528f3ce7a8'
ID = 'RAN1_P2_CQ1-1'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
NS = {'w': W[1:-1]}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(name):
    path = PACKAGE_ROOT / name
    no_symlink(path)
    require(path.is_relative_to(PACKAGE_ROOT) and path.is_file(), 'Invalid included file')
    return path.read_bytes()


def load(name):
    return json.loads(read(name))


def tx(element):
    return ''.join(node.text or '' for node in element.iter(W + 't'))


def norm(text):
    return re.sub(r'\s+', ' ', text).strip()


def sty(element):
    found = element.find('w:pPr/w:pStyle', NS)
    return found.get(W + 'val') if found is not None else None


def main():
    for path in PACKAGE_ROOT.rglob('*'):
        no_symlink(path)
        require(path.is_file() or path.is_dir(), 'Nonregular entry rejected')
    inventory_bytes = read('immutable_inventory.json')
    require(sha(inventory_bytes) == EXPECTED_INVENTORY_SHA256, 'Immutable inventory changed')
    inventory = json.loads(inventory_bytes)
    expected = set(inventory) | {'immutable_inventory.json', 'verify_diagnostic.py', 'manifest.json'}
    actual = {path.relative_to(PACKAGE_ROOT).as_posix() for path in PACKAGE_ROOT.rglob('*') if path.is_file()}
    require(actual == expected, 'Closed file inventory mismatch')
    for name, expected_pin in inventory.items():
        require(set(expected_pin) == {'sha256', 'bytes'} and type(expected_pin['bytes']) is int, 'Invalid pin shape')
        value = read(name)
        require(len(value) == expected_pin['bytes'] and sha(value) == expected_pin['sha256'], 'Included payload changed: ' + name)
    manifest = load('manifest.json')
    require(set(manifest) == {'id', 'artifact_type', 'classification', 'classification_is_conditional', 'expert_validation_n', 'original_core_increment', 'admitted', 'inventory_sha256', 'verifier_sha256', 'files', 'limitations'}, 'Manifest keys changed')
    require(manifest['id'] == ID and manifest['artifact_type'] == 'bounded_original_agenda_conflict_diagnostic', 'Manifest identity changed')
    require(manifest['classification'] == 'clarification_required' and manifest['classification_is_conditional'] is True and manifest['admitted'] is False, 'Classification changed')
    require(type(manifest['expert_validation_n']) is int and manifest['expert_validation_n'] == 0, 'Expert attribution changed')
    require(type(manifest['original_core_increment']) is int and manifest['original_core_increment'] == 0, 'Admission count changed')
    require(manifest['inventory_sha256'] == EXPECTED_INVENTORY_SHA256 and manifest['verifier_sha256'] == sha(read('verify_diagnostic.py')), 'Metadata integrity changed')
    require(manifest['files'] == inventory, 'Payload inventory metadata changed')
    require(manifest['limitations'] == load('scope_and_limits.json'), 'Limitations changed')

    # All subsequent artifact reads must stay within this copied package.
    opened = []
    def audit(event, args):
        if event in {'subprocess.Popen', 'os.system', 'sqlite3.connect'} or event.startswith('socket.'):
            raise RuntimeError('Network, database, or child execution is forbidden')
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0]))
            if not path.is_absolute():
                path = Path.cwd() / path
            no_symlink(path)
            require(path.resolve().is_relative_to(PACKAGE_ROOT), 'Artifact read outside package rejected')
            mode = args[1]
            require(mode is None or not any(value in str(mode) for value in ('w', 'a', '+', 'x')), 'Writes forbidden')
            opened.append(path.resolve().relative_to(PACKAGE_ROOT).as_posix())
    sys.addaudithook(audit)

    row_bytes = read('original_registered_row.jsonl').rstrip(b'\n')
    require(sha(row_bytes) == 'bbc16e6ffa1b0e6fff799c21ffef16773ace1a25e7cb20d9c26e549c31fc9b69', 'Original row changed')
    row = json.loads(row_bytes)
    require(sha(row['question_en'].encode()) == '29d6629959b816091b5d768ead18d93c2e63f2c7ac36853dcaeb62fff5c7394d', 'Question changed')
    require(sha(row['cypher'].encode()) == 'd0a1887020c90fb57a49528e2b336931001f6a8af796884e22792b2afba1aeaa', 'Authored query changed')
    source = load('compact_source_and_conditional_scope_witnesses.json')
    with zipfile.ZipFile(io.BytesIO(read('original_report.zip'))) as archive:
        info = archive.getinfo(source['source']['member']['name'])
        member = archive.read(info)
    require(info.CRC == source['source']['member']['zip_crc32'] and sha(member) == source['source']['member']['sha256'], 'Original member changed')
    with zipfile.ZipFile(io.BytesIO(member)) as document:
        xml, styles = document.read('word/document.xml'), document.read('word/styles.xml')
    require(sha(xml) == source['source']['document_XML']['sha256'] and sha(styles) == source['source']['styles_XML']['sha256'], 'Original XML changed')
    paragraphs = list(ET.fromstring(xml).iter(W + 'p'))
    require(len(paragraphs) == 10603, 'Paragraph universe changed')
    headings = load('actual_four_original_TOC_and_own_heading_bindings.json')['pairs']
    for item in headings:
        toc, own = paragraphs[item['TOC_p0']], paragraphs[item['heading_p0']]
        require(tx(toc) == item['TOC_text'] and tx(own) == item['heading_text'], 'TOC/heading changed')
        require(item['TOC_anchor'] in [node.get(W + 'anchor') for node in toc.iter(W + 'hyperlink')], 'TOC anchor changed')
        require(item['TOC_anchor'] in [node.get(W + 'name') for node in own.iter(W + 'bookmarkStart')], 'Own heading bookmark changed')
    for number, scope in source['source_scope_boundaries'].items():
        start = scope['start_p0']
        end = next(index for index in range(start + 1, len(paragraphs)) if sty(paragraphs[index]) in {'Heading1', 'Heading2'})
        labels = [index for index in range(start, end) if tx(paragraphs[index]).strip() == 'Agreement']
        require(end == scope['end_p0_exclusive'] and labels == scope['labels'], 'Own Agreement boundary changed')
    numeric = source['captured_numeric_records']
    require(len(numeric) == 11 and len({item['resolutionId'] for item in numeric}) == 11, 'Numeric identity population changed')
    require(len({(item['agendaNumber'], item['sequence']) for item in numeric}) == 11, 'Cutoff/order keys changed')
    for witness, record in zip(source['numeric_source_witnesses'], numeric):
        own = paragraphs[witness['source_heading_p0']]
        first_index = next(index for index in range(witness['source_heading_p0'] + 1, 1087) if tx(paragraphs[index]).strip())
        first = paragraphs[first_index]
        require(first_index == witness['source_first_body_p0'] and tx(first) == witness['source_first_paragraph_text'], 'First-body witness changed')
        require(sha(ET.tostring(own)) == witness['source_heading_xml_sha256'] and sha(ET.tostring(first)) == witness['source_first_paragraph_xml_sha256'], 'Raw witness XML changed')
        require(norm(tx(first))[:45] == norm(record['content'])[:45], 'Source-to-frozen first-body prefix changed')
    captured_named = source['captured_named_agenda_IDs']
    require(len(captured_named) == len(set(captured_named)) == 55, 'Conditional named population changed')
    require(not ({item['resolutionId'] for item in numeric} & set(captured_named)), 'Conditional scopes no longer disjoint')
    # These are captured frozen identities, not freshly queried rows or full55 content certification.
    native = [json.loads(line) for line in read('saved_original_native_rows.jsonl').splitlines() if line.strip()]
    sql3 = [[item['resolutionId'], item['content'], item['agendaNumber']] for item in numeric]
    require(native == sql3 and all(type(value) is str for record in native for value in record), 'Stored native33/SQL values changed')
    native_receipt = load('saved_original_native_receipt.json')
    execution = native_receipt['execution']
    require(execution['rows_file_sha256'] == sha(read('saved_original_native_rows.jsonl')), 'Native row pin changed')
    require(native_receipt['reference_query_utf8_sha256'] == sha(row['cypher'].encode()), 'Native query differs')
    require(execution['status'] == 'OK' and execution['row_count_retained'] == 11 and execution['rollback_completed'] and execution['execution_summary_complete'], 'Historical native execution flags invalid')

    criteria = load('canonical/criteria.json')
    definition = load('definition.json')
    gold = load('reference_gold.json')['records']
    require(definition['question_en'] == row['question_en'] and definition['original_query'] == definition['reference_query'] == row['cypher'], 'Conditional definition changed original bytes')
    spec = importlib.util.spec_from_file_location('included_canonical_scorer', PACKAGE_ROOT / 'canonical/scorer.py')
    scorer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scorer)
    keys = ('id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved')
    require(sha(scorer.get_kernel().json_exact({key: definition[key] for key in keys}).encode()) == definition['repair_sha256'] == 'c10e383fcd0c9df48911755d42478df1c96d5f2a836a79c29b9446c394a14ade', 'Nine-key repair binding changed')
    require(gold == [{'resolutionId': record[0]} for record in native], 'Conditional gold differs')
    controls = load('actual_unchanged_canonical_scorer_controls.json')
    for control in controls['checks']:
        result = scorer.score(definition, gold, control['predicted_records'], diagnostic=True)
        require(result == control['actual'] and result['exact'] is control['expected_exact'], 'Conditional scorer result differs')
    require(controls['control_n'] == len(controls['checks']) == 90, 'Control denominator changed')
    review = load('primary_exact_seven_unit_classification_review.json')
    require([unit['unit'] for unit in review['semantic_evidence']] == criteria['semantic_units'], 'Seven-unit coverage changed')
    require(review['status'] == 'clarification_required' and review['classification_is_conditional'] is True and review['expert_validation_n'] == 0, 'Final classification changed')
    final = load('final_local_decision.json')
    require(final['recommended_classification'] == 'clarification_required' and final['classification_is_conditional'] is True, 'Final decision changed')
    require(load('conditional_numeric_candidate_NOT_ADMITTED.json')['meaning_adoption_requires_explicit_ID_first_correction_policy'] is True, 'Conditional scope gate changed')
    tr = load('existing_three_TR_candidates.json')['cases']
    require(len(tr) == 3 and all(case['classification_is_conditional'] is True and case['admission'] is False for case in tr), 'Existing conditional comparison changed')
    require(all(unit['original_quote'] == row['question_en'] for unit in review['semantic_evidence']), 'Original seven-unit question binding changed')
    print(json.dumps({'status':'PASS_BOUNDED_CONDITIONAL_CLARIFICATION_REPLAY','id':ID,'classification':'clarification_required','original_core_increment':0,'source_own_numeric_labels':11,'captured_named_agenda_IDs':55,'saved_original_native_rows':11,'native_typed_values_compared':33,'conditional_scorer_controls':90,'classification_units':7,'fresh_SQL_queries':0,'fresh_native_executions':0,'API_calls':0,'expert_validation_n':0,'artifact_reads_outside_package':0,'limitations':manifest['limitations']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
