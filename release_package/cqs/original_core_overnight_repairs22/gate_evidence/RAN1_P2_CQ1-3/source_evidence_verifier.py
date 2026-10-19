"""Replay raw source/typed projection evidence, independently of native/scorer gold."""
import argparse
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import zipfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def rows(path):
    data = path.read_bytes()
    if path.suffix == '.gz':
        data = gzip.decompress(data)
    return [json.loads(line) for line in data.decode().splitlines()]


def validate_boundary(records, frozen):
    assert len(records) == 64 and len({x['resolutionId'] for x in records}) == 64
    assert {x['resolutionId'] for x in records} == {x['resolutionId'] for x in frozen}
    expected_sequence = {x['resolutionId']: x['sequence'] for x in frozen}
    assert all(x['sequence'] == expected_sequence[x['resolutionId']] for x in records)
    ordered = sorted(records, key=lambda x: (x['sequence'], x['resolutionId']))
    active = [x for x in ordered if x['label_active'] and not x['explicit_withdrawal_literal']]
    selected = [x['resolutionId'] for x in active[:15]]
    assert selected == [x['resolutionId'] for x in ordered[:15]]
    assert selected == [x['resolutionId'] for x in frozen[:15]]
    assert len(active) == 63
    assert [x['resolutionId'] for x in records if x['explicit_withdrawal_literal']] == ['CON-121-9.8.1-003']
    return selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path)
    args = parser.parse_args()
    manifest = json.loads((HERE/'manifest.json').read_text())
    expected = {x['path'] for x in manifest['files']} | {'manifest.json'}
    actual = {str(x.relative_to(HERE)) for x in HERE.rglob('*') if x.is_file()}
    assert actual == expected, (actual-expected, expected-actual)
    assert not any('__pycache__' in x or x.endswith(('.pyc', '.pyo')) for x in actual)
    for pin in manifest['files']:
        data = (HERE/pin['path']).read_bytes()
        assert len(data) == pin['bytes'] and sha(data) == pin['sha256'], pin['path']
    original = json.loads((HERE/'context/original_benchmark_record.json').read_text())
    definition = json.loads((HERE/'context/prospective_definition_NOT_ADMITTED.json').read_text())
    assert sha(original['question_en'].encode()) == manifest['original_question_sha256']
    assert definition['question_en'] == original['question_en']
    assert definition['original_query'] == definition['reference_query'] == original['cypher']
    assert definition['repair_class'] == 'scorer_only'
    assert definition['required_fields'] == [{'name':'resolutionId','type':'string','nullable':False,'source_column_or_expression':'c.resolutionId'}]
    assert definition['collection'] == {'kind':'set'}
    assert definition['cardinality_policy'] == {'mode':'exact','value':15}
    assert sha(json.dumps(definition,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()) == manifest['scope_and_provenance']['repair_sha256']
    raw = load_module('source_marker_reader', HERE/'raw_source.py')
    conclusions = load_module('source_Conclusion_reader', HERE/'Conclusion_source.py')
    data = (HERE/'source/report.docx').read_bytes()
    assert sha(data) == manifest['original_report']['member_sha256']
    audit = conclusions.audit_conclusions(data, raw)
    assert audit['document_XML_sha256'] == manifest['original_report']['document_XML_sha256']
    assert audit['styles_XML_sha256'] == manifest['original_report']['styles_XML_sha256']
    source = rows(HERE/'source/all64_raw_Conclusion_records.jsonl.gz')
    candidates = rows(HERE/'source/all_label_candidates.jsonl')
    assert audit['records'] == source and audit['candidates'] == candidates
    assert len(candidates) == 64 and all(x['strict_own_pattern'] for x in candidates)
    frozen = rows(HERE/'frozen/all64_query_operands.jsonl')
    assert len(frozen) == 64
    assert frozen == sorted(frozen,key=lambda x:(x['sequence'],x['resolutionId']))
    selected = validate_boundary(source, frozen)
    selected_records = rows(HERE/'source_selected_records.jsonl')
    assert selected_records == [{'resolutionId': x} for x in selected]
    controls = []
    for kind in ['drop_record','duplicate_record','selected_label_inactive','selected_withdrawn','selected_sequence_change']:
        bad = json.loads(json.dumps(source))
        if kind == 'drop_record':
            bad.pop(0)
        elif kind == 'duplicate_record':
            bad[-1] = bad[0]
        elif kind == 'selected_label_inactive':
            next(x for x in bad if x['resolutionId'] == selected[0])['label_active'] = False
        elif kind == 'selected_withdrawn':
            next(x for x in bad if x['resolutionId'] == selected[0])['explicit_withdrawal_literal'] = True
        else:
            next(x for x in bad if x['resolutionId'] == selected[0])['sequence'] = 999
        try:
            validate_boundary(bad, frozen)
        except AssertionError:
            controls.append({'control':kind,'outcome':'REJECTED'})
        else:
            raise AssertionError(('negative accepted',kind))
    full_original = None
    if args.source_root:
        pin = manifest['original_report']
        archive = args.source_root/pin['archive_path']
        assert sha(archive.read_bytes()) == pin['archive_sha256']
        with zipfile.ZipFile(archive) as z:
            assert z.read(pin['member']) == data
        dbpin = manifest['frozen_source']
        dbpath = args.source_root/dbpin['path']
        assert sha(dbpath.read_bytes()) == dbpin['sha256']
        db = sqlite3.connect(dbpath.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
        db.execute('PRAGMA query_only=ON'); db.row_factory = sqlite3.Row
        actual_rows = [dict(x) for x in db.execute(dbpin['SQL'])]
        db.close()
        assert actual_rows == frozen
        full_original = {'original_archive_and_member_reopened':True,'frozen_SQLite_rehashed_and_all64_rows_recounted':True}
    print(json.dumps({'status':'PASS','kind':'Source-only conditional original15 identity evidence; semantic/native/scorer admission remains separate','id':manifest['id'],'raw_candidates':len(candidates),'source_records':len(source),'source_active':63,'selected_records':len(selected),'negative_controls':controls,'optional_original_replay':full_original,'expert_validation_n':0,'native_calls':0,'model_calls':0},ensure_ascii=False))


if __name__ == '__main__':
    main()
