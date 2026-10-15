"""Independently read the authentic report and all raw paragraphs before API use."""
from pathlib import Path
from io import BytesIO
import datetime
import hashlib
import json
import sqlite3
import xml.etree.ElementTree as ET
import zipfile

B = Path(__file__).resolve().parent.parent
REG = B / 'RAN1/source_variant_OpenRouter_registration/source6_UL_formal'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            h.update(block)
    return h.hexdigest()

def load(path):
    return json.loads(path.read_text())

def main():
    out = B / 'root_evidence/UL_source6_root_fresh_whole_report_prefreeze.json'
    assert not out.exists()
    auth = load(REG / 'raw_source_archive_authentication.json')
    archive = Path(auth['archive']['path'])
    assert sha(archive) == auth['archive']['sha256']
    with zipfile.ZipFile(archive) as package:
        member = package.read(auth['member'])
    assert hashlib.sha256(member).hexdigest() == auth['member_sha256']
    assert member == Path(auth['retained_DOCX']['path']).read_bytes()
    with zipfile.ZipFile(BytesIO(member)) as package:
        xml = package.read('word/document.xml')
    assert hashlib.sha256(xml).hexdigest() == auth['document_XML_sha256']
    paragraphs = list(ET.fromstring(xml).iter(W + 'p'))
    raw = REG / 'whole_original_report_unfiltered_paragraph_inputs.jsonl'
    rows = [json.loads(line) for line in raw.read_text().splitlines()]
    cursor = 0
    for row in rows:
        assert set(row) == {'fields', 'source_row', 'source_cell_coordinates'}
        coords = row['source_cell_coordinates']
        start, end = coords['paragraph_range_zero_based']
        assert start == cursor
        selected = paragraphs[start:end + 1]
        assert coords['document_XML_sha256'] == auth['document_XML_sha256']
        assert coords['original_member_sha256'] == auth['member_sha256']
        assert coords['paragraph_ElementTree_utf8_XML_sha256'] == [
            hashlib.sha256(ET.tostring(p, encoding='utf-8')).hexdigest() for p in selected]
        assert row['fields']['paragraphs'] == [
            {'paragraph_zero_based': start + i,
             'literal_text_all_w_t_and_m_t': ''.join(e.text or '' for e in p.iter()
                                                     if e.tag in {W + 't', M + 't'})}
            for i, p in enumerate(selected)]
        cursor = end + 1
    assert cursor == len(paragraphs) == auth['all_paragraphs_n'] == 6017
    assert len(rows) == auth['raw_chunks_n'] == 251
    config = load(REG / 'source_config.json')
    manifest = load(Path(config['sql_manifest_path']))
    db = Path(config['sql_db_path'])
    before = sha(db)
    assert before == manifest['db']['sha256']
    conn = sqlite3.connect(db.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    try:
        ddl = ';\n'.join(r[0] for r in conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT GLOB '_*' ORDER BY name")) + ';\n'
        assert ddl == load(Path(config['sql_schema_path']))['ddl']
        table_n = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT GLOB '_*'").fetchone()[0]
    finally:
        conn.close()
    assert sha(db) == before
    result = {'status': 'PASS_ROOT_FRESH_ORIGINAL_ARCHIVE_ALL6017_PARAGRAPHS_AND_PHYSICAL_DDL',
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'original_archive_sha256': sha(archive), 'member_sha256': auth['member_sha256'],
              'document_XML_sha256': auth['document_XML_sha256'],
              'raw_input_sha256': sha(raw), 'all_paragraphs_n': cursor, 'all_raw_chunks_n': len(rows),
              'all_paragraph_text_and_serialized_XML_hashes_compared': True,
              'complete_value_free_SQL_DDL_table_n': table_n, 'SQL_before_after_sha256': before,
              'new_model_API_calls': 0, 'new_native_calls': 0,
              'limitations': 'Complete raw paragraph projection only; not rendered final-visible Word, paraphrase evaluation, normative adoption or whole-corpus completeness.'}
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
