#!/usr/bin/env python3
"""Independently check U003 raw records and its native report span; emit no source prose."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import xml.etree.ElementTree as ET
import zipfile


def sha(path, compressed=False):
    h = hashlib.sha256()
    opener = gzip.open if compressed else open
    with opener(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--release', type=Path, required=True)
    ap.add_argument('--analysis', type=Path, required=True)
    ap.add_argument('--database', type=Path, required=True)
    ap.add_argument('--source-root', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    release, analysis = args.release.resolve(), args.analysis.resolve()
    questions = release / 'studies/practitioner_questions/question_analysis.json'
    q = json.loads(questions.read_text())
    decomposition = json.loads((analysis / 'decomposition.json').read_text())
    execution = json.loads((analysis / 'execution.json').read_text())
    protocol = json.loads((analysis / 'protocol.json').read_text())
    amendment = json.loads((analysis / 'implementation_amendment.json').read_text())
    selected = [u for u in q['units'] if u['first_judgment']['type'] in ('mixed', 'process_trace')]
    expected_ids = ['U003', 'U004', 'U015', 'U021', 'U023']
    require([u['unit_id'] for u in selected] == expected_ids, 'selected population changed')
    require([u['unit_id'] for u in decomposition['rows']] == expected_ids, 'decomposition population changed')
    comparisons = []
    for original, projected in zip(selected, decomposition['rows']):
        fields = ['unit_id', 'question_paraphrase_en', 'first_judgment', 'second_judgment']
        require(all(original[k] == projected[k] for k in fields), 'paraphrase/classifier projection changed')
        comparisons.append({'unit_id': original['unit_id'], 'all_preserved_fields_equal': True,
                            'first_mapping': original['first_judgment']['familyMapping'],
                            'second_mapping': original['second_judgment']['familyMapping']})
    require(selected == execution['units'], 'execution units changed')
    require(sha(questions) == protocol['input_sha256'] == execution['question_analysis_sha256'], 'question hash mismatch')
    require(sha(analysis / 'protocol.json') == execution['protocol_sha256'], 'protocol hash mismatch')
    require(sha(analysis / 'inspect_trace.py') == execution['checker_sha256'] == amendment['new_code_sha256'], 'checker hash mismatch')
    require(sha(analysis / 'failed_scope_setup/inspect_trace.py') == amendment['original_code_sha256'], 'original checker hash mismatch')
    require(sha(analysis / 'failed_scope_setup/execution.json') == amendment['original_output_sha256'], 'original execution hash mismatch')

    before = sha(args.database)
    packed = release / 'sqlite/RAN5.sqlite.gz'
    require(sha(packed, compressed=True) == before, 'database differs from released decompressed bytes')
    con = sqlite3.connect(args.database.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA query_only=ON')
    started = time.monotonic()
    con.set_progress_handler(lambda: int(time.monotonic() - started > 60), 10000)
    def rows(sql, params=()):
        return [dict(row) for row in con.execute(sql, params)]
    # Separate raw-table reads avoid importing or repeating the author's combined join.
    documents = rows('SELECT * FROM document WHERE number=?', ('R5-253194',))
    require(len(documents) == 1, 'anchor document is not unique')
    doc = documents[0]
    require([doc[k] for k in ['cr_number', 'spec', 'target_release']] == ['5008', '38.523-1', 'Rel-19'], 'CR identity mismatch')
    dispositions = rows('SELECT * FROM disposition WHERE target=?', (doc['id'],))
    require(len(dispositions) == 1, 'unexpected additional dispositions')
    disp = dispositions[0]
    require([disp[k] for k in ['code', 'scope', 'evidence_status']] == ['agreed', 'whole_target', 'source_verified'], 'disposition mismatch')
    resolutions = rows('SELECT * FROM resolution WHERE id=?', (disp['resolution_id'],))
    require(len(resolutions) == 1 and resolutions[0]['meeting_id'] == 'tdoc:meeting/RAN5_107', 'meeting mismatch')
    packs_by_direction = {}
    for table in ['pack_member', 'cr_in_pack']:
        links = rows('SELECT * FROM ' + table + ' WHERE cr=?', (doc['id'],))
        pack_rows = [rows('SELECT * FROM cr_pack WHERE id=?', (link['pack_id'],)) for link in links]
        packs_by_direction[table] = {'links': links, 'packs': pack_rows}
        require(len(pack_rows) == 1 and len(pack_rows[0]) == 1, 'unexpected pack cardinality')
        require([pack_rows[0][0][k] for k in ['pack_number', 'tsg_meeting']] == ['RP-251118', 'RAN#108'], 'pack mismatch')
    sections_by_direction = {}
    for table in ['cr_modifies_section', 'section_modified_by']:
        links = rows('SELECT * FROM ' + table + ' WHERE cr=?', (doc['id'],))
        section_rows = [rows('SELECT * FROM section WHERE id=?', (link['section_id'],)) for link in links]
        sections_by_direction[table] = {'links': links, 'sections': section_rows}
        require(len(section_rows) == 1 and len(section_rows[0]) == 1, 'unexpected section cardinality')
        require([section_rows[0][0][k] for k in ['spec', 'release', 'clause']] == ['38.523-1', 'Rel-19', '11.4.1'], 'typed clause mismatch')
    domains = {name: [r[0] for r in con.execute('SELECT DISTINCT ' + name + ' FROM disposition ORDER BY ' + name)]
               for name in ['scope', 'evidence_status']}
    con.close()
    require(sha(args.database) == before, 'database changed')

    record = json.loads((analysis / 'source_record.json').read_text())
    require(record['@id'] == disp['id'] and record['evidencePath'] == disp['evidence_path'], 'source binding identity mismatch')
    native = args.source_root / disp['evidence_path']
    expected_source_hash = 'f0c43bb326aa1fe315b9ef78fa7e806ca7d143edea3135b55ea24eac31d8d5a9'
    require(sha(native) == expected_source_hash == disp['evidence_sha256'], 'native source hash mismatch')
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    with zipfile.ZipFile(native) as archive:
        root = ET.fromstring(archive.read('word/document.xml'))
    def blocks(node):
        for child in node:
            if child.tag in (w + 'p', w + 'tbl'):
                yield child
            elif child.tag in (w + 'sdt', w + 'sdtContent', w + 'customXml'):
                yield from blocks(child)
    def text(node):
        if node.tag in (w + 'del', w + 'moveFrom'):
            return ''
        if node.tag == w + 't':
            return node.text or ''
        if node.tag == w + 'tab':
            return '\t'
        if node.tag in (w + 'br', w + 'cr'):
            return '\n'
        return ''.join(text(child) for child in node)
    body_blocks = list(blocks(root.find(w + 'body')))
    span = [text(block).strip() for block in body_blocks[8629:8633]]
    quote_hash = hashlib.sha256('\n'.join(span).encode()).hexdigest()
    require(quote_hash == 'a9a6173d9b3baff0181a2216e32dc8911442b3a422893a7ba44012d711ee1062', 'independent quote hash mismatch')
    require(span[0].startswith('R5-253194\t'), 'entry header mismatch')
    require('CR-5008' in span[1] and '38.523-1' in span[1] and '(Rel-19)' in span[1], 'entry metadata mismatch')
    decision = ' '.join(span[3].split())
    require(decision == 'Decision: The document was agreed.', 'direct target-entry decision mismatch')
    require(text(body_blocks[8633]).strip().startswith('R5-252599'), 'following entry boundary mismatch')
    restored = json.loads((analysis / 'source_restored.jsonld').read_text())['@graph']
    require(len(restored) == 1 and hashlib.sha256(restored[0]['evidenceQuote'].encode()).hexdigest() == quote_hash,
            'restored passage differs from independently read native bytes')
    workflow = json.loads((release / 'studies/practitioner_questions/workflow_example.json').read_text())
    require(workflow['unit_id'] == 'U004' and len(workflow['gold_rows']) == 28, 'existing U004 illustration changed')
    report = {
        'scope': 'Independent raw-record and native-span audit; existing labels preserved; no model calls or engineering-answer measurement.',
        'checker_sha256': sha(Path(__file__)), 'question_analysis_sha256': sha(questions),
        'unit_projection': comparisons, 'artifact_hash_chain_equal': True,
        'public_database': {'compressed_sha256': sha(packed), 'decompressed_sha256': before, 'unchanged': True},
        'runtime': {'sqlite': sqlite3.sqlite_version, 'mode': 'ro immutable query_only', 'cap_seconds': 60},
        'raw_records': {'document': documents, 'disposition': dispositions, 'resolution': resolutions,
                        'packs_by_direction': packs_by_direction, 'sections_by_direction': sections_by_direction},
        'predicate_domains': domains,
        'native_check': {'source_path': disp['evidence_path'], 'source_sha256': expected_source_hash,
                         'locator': 'word/document.xml accepted body blocks [8629,8633)',
                         'quote_sha256': quote_hash, 'entry_target_and_cr_metadata_match': True,
                         'direct_target_entry_agreed_predicate_verified': True,
                         'next_entry_boundary_verified': True, 'restored_quote_matches': True,
                         'method': 'Independent stdlib zipfile/ElementTree parser; producer parsing/classification modules unused; source prose omitted.'},
        'u004_existing_illustration': {'gold_rows': 28, 'scope': 'Existing artifact checked; its RAN4 SQL was not rerun in this U003 audit.'},
        'official_portal': {'scope': 'Existing root receipt reviewed; this audit makes no independent live portal observation.'}
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'units': expected_ids, 'u003_document_count': 1, 'native_quote_sha256': quote_hash, 'checks': 'passed'}))


if __name__ == '__main__':
    main()
