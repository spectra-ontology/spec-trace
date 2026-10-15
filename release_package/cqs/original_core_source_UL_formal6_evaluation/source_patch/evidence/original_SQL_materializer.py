#!/usr/bin/env python3
"""Encode six formal source values in an independent SQL snapshot copy.

Spec: unchanged RAN1_P2_CQ1-2; source enrichment is counted separately.
Ontology: new Agreement/Resolution formalSourceContentWithTables string.
Cycle: overnight audit before 2026-10-15 10:00 KST.
배경: Preserve every old property while comparing an independent encoding.
사용: python3 build_UL_source_sql.py after native restoration succeeds.
LLM 호출: 없음; no expert validation or model performance is inferred.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

BASE = Path(__file__).resolve().parent
WORK = BASE / 'source_enriched/RAN1_UL_formal_v2'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def main():
    mapping_path = BASE / 'RAN1/UL_switching_formal_ontology_mapping_v2.json'
    mapping = json.loads(mapping_path.read_text())
    native_manifest_path = WORK / 'native_import_manifest.json'
    native_manifest = json.loads(native_manifest_path.read_text())
    assert native_manifest['status'] == 'restored_inventory_match'
    assert native_manifest['mapping']['sha256'] == sha(mapping_path)
    snapshot = Path(native_manifest['snapshot']['path'])
    assert sha(snapshot) == native_manifest['snapshot']['sha256']
    original = BASE.parent / 'relational/RAN1.sqlite'
    original_manifest = json.loads(original.with_suffix('.manifest.json').read_text())
    original_sha = sha(original)
    assert original_sha == original_manifest['db_sha256']
    original_stat = (original.stat().st_size, original.stat().st_mtime_ns)
    output_dir = WORK / 'relational'
    output_dir.mkdir(exist_ok=True)
    output = output_dir / 'RAN1.sqlite'
    assert not output.exists(), 'Refuse replacing an earlier source SQL copy'
    shutil.copy2(original, output)
    assert sha(output) == original_sha
    connection = sqlite3.connect(output)
    added = []
    try:
        before = {'nodes': connection.execute('SELECT COUNT(*) FROM node').fetchone()[0],
                  'relationships': connection.execute('SELECT COUNT(*) FROM edge').fetchone()[0]}
        with connection:
            for label in ['Agreement', 'Resolution']:
                columns = {row[1] for row in connection.execute('PRAGMA table_info(' + label + ')')}
                assert 'formalSourceContentWithTables' not in columns
                connection.execute('ALTER TABLE ' + label + ' ADD COLUMN formalSourceContentWithTables ANY')
            for fill in mapping['fills']:
                record = connection.execute('SELECT node_id,labels_json,properties_json FROM _node_record WHERE source_iri=?',
                                            [fill['source_iri']]).fetchall()
                assert len(record) == 1
                node_id, labels_json, old_json = record[0]
                labels = json.loads(labels_json)
                assert set(labels) == {'Agreement', 'Resolution'}
                old = json.loads(old_json)
                assert old['resolutionId'] == fill['resolutionId']
                assert 'formalSourceContentWithTables' not in old
                value = fill['new_properties']['formalSourceContentWithTables']
                new = dict(old, formalSourceContentWithTables=value)
                assert {key: new[key] for key in old} == old
                assert connection.execute('SELECT value_json FROM node_property WHERE node_id=? AND key=?',
                                          [node_id, 'formalSourceContentWithTables']).fetchone() is None
                connection.execute('UPDATE _node_record SET properties_json=? WHERE node_id=?', [canonical(new), node_id])
                connection.execute('INSERT INTO node_property VALUES(?,?,?,?)',
                                   [node_id, 'formalSourceContentWithTables', 'string', canonical(value)])
                for label in labels:
                    connection.execute('UPDATE ' + label + ' SET formalSourceContentWithTables=? WHERE node_id=?', [value, node_id])
                    observed = connection.execute('SELECT content,formalSourceContentWithTables FROM ' + label + ' WHERE node_id=?',
                                                  [node_id]).fetchone()
                    assert observed == (old['content'], value)
                added.append({'node_id': node_id, 'resolutionId': fill['resolutionId'],
                              'old_content_sha256': hashlib.sha256(old['content'].encode()).hexdigest(),
                              'new_property_sha256': hashlib.sha256(value.encode()).hexdigest(),
                              'original_properties_preserved': True})
        after = {'nodes': connection.execute('SELECT COUNT(*) FROM node').fetchone()[0],
                 'relationships': connection.execute('SELECT COUNT(*) FROM edge').fetchone()[0]}
        assert before == after == {'nodes': native_manifest['expected_nodes'],
                                   'relationships': native_manifest['expected_relationships']}
        connection.row_factory = sqlite3.Row
        sql = """SELECT DISTINCT a.formalSourceContentWithTables AS content FROM Agreement a
                 JOIN rel_RESOLUTION_BELONGS_TO ra ON ra.src_id=a.node_id
                 JOIN AgendaItem ai ON ai.node_id=ra.dst_id
                 JOIN rel_MADE_AT am ON am.src_id=a.node_id
                 JOIN Meeting m ON m.node_id=am.dst_id
                 WHERE ai.agendaNumber='5.1' AND m.meetingNumber='RAN1#100'"""
        records = [dict(row) for row in connection.execute(sql)]
        assert len(records) == 6 and all(row['content'] for row in records)
        assert {row['content'] for row in records} == {fill['new_properties']['formalSourceContentWithTables'] for fill in mapping['fills']}
    finally:
        connection.close()
    assert sha(original) == original_sha
    assert (original.stat().st_size, original.stat().st_mtime_ns) == original_stat
    records_path = output_dir / 'formal_source_six_records.jsonl'
    records_path.write_text(''.join(canonical(row) + '\n' for row in records))
    report = {'checked_utc': datetime.now(timezone.utc).isoformat(),
              'status': 'separate_source_SQL_six_values_verified',
              'base': {'path': str(original), 'sha256': original_sha, 'bytes_and_mtime_unchanged': True},
              'db': {'path': str(output), 'sha256': sha(output), 'bytes': output.stat().st_size},
              'snapshot_sha256': native_manifest['snapshot']['sha256'],
              'mapping_sha256': sha(mapping_path), 'builder_sha256': sha(Path(__file__)),
              'inventory_before': before, 'inventory_after': after,
              'added_property_values_n': 6, 'added_properties': added,
              'original_property_values_updated_n': 0, 'question_admissions': 0,
              'full_formal_records': {'sql': sql, 'path': str(records_path), 'sha256': sha(records_path), 'rows': 6},
              'new_model_api_calls': 0,
              'limit': 'Independent source encoding, no original question semantic admission, paraphrase equivalence or new model performance.'}
    (output_dir / 'RAN1.manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'formal_source_rows': len(records), 'base_unchanged': True}))


if __name__ == '__main__':
    main()
