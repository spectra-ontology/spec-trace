#!/usr/bin/env python3
"""Independently reread complete report XML and six formal source blocks.

Spec: unchanged RAN1_P2_CQ1-2; no admission from source hashes alone.
Ontology: proposed formalSourceContentWithTables with literal qualifiers.
Cycle: overnight audit before 2026-10-15 10:00 KST.
배경: Check whole-document provenance and formal/provisional separation.
사용: python3 audit_UL_source_integrity.py
LLM 호출: 없음; direct source verification only.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

BASE = Path(__file__).resolve().parent
ROOT = next(p for p in BASE.parents if (p / 'CLAUDE.md').exists())
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def text(node):
    bits = []
    for item in node.iter():
        if item.tag == W + 't':
            bits.append(item.text or '')
        elif item.tag in {W + 'tab', W + 'br', W + 'cr'}:
            bits.append(' ')
    return ''.join(bits).strip()


def main():
    whole_path = BASE / 'RAN1/RAN1_100_whole_ordered_report_source.json'
    whole = json.loads(whole_path.read_text())
    source = ROOT / whole['source']['path']
    assert sha(source.read_bytes()) == whole['source']['sha256']
    with zipfile.ZipFile(source) as archive:
        raw = archive.read('word/document.xml')
    assert sha(raw) == whole['document_xml_sha256']
    tree = ET.fromstring(raw)
    body = list(tree.find(W + 'body'))
    paragraphs = list(tree.iter(W + 'p'))
    index = {id(p): i for i, p in enumerate(paragraphs)}
    assert len(paragraphs) == whole['paragraph_n'] == 6017
    actual = [i for i, node in enumerate(body) if node.tag in {W + 'p', W + 'tbl'}]
    assert actual == [record['body_child_index'] for record in whole['records']]
    for record in whole['records']:
        node = body[record['body_child_index']]
        assert sha(ET.tostring(node, encoding='utf-8')) == record['xml_sha256']
        assert text(node) == record['text']
        assert [index[id(p)] for p in node.iter(W + 'p')] == record['paragraph_indices']
        if record['kind'] == 'table':
            rows = [[text(cell) for cell in row.findall(W + 'tc')] for row in node.findall(W + 'tr')]
            assert rows == record['table_rows']
            rendered = '\n'.join(' | '.join(row) for row in rows)
        else:
            rendered = text(node)
        assert rendered == record['rendered_text']
    mapping_path = BASE / 'RAN1/UL_switching_formal_ontology_mapping_v2.json'
    mapping = json.loads(mapping_path.read_text())
    blocks_path = ROOT / mapping['source_blocks']['path']
    assert sha(blocks_path.read_bytes()) == mapping['source_blocks']['sha256']
    blocks = json.loads(blocks_path.read_text())
    assert blocks['document_xml_sha256'] == sha(raw)
    assert len(mapping['fills']) == len(blocks['formal_agreement_groups']) == 6
    by_index = {record['body_child_index']: record for record in whole['records']}
    results = []
    for fill, group in zip(mapping['fills'], blocks['formal_agreement_groups']):
        assert fill['resolutionId'] == group['resolutionId']
        assert re.fullmatch(r'Agreements?\s*:', text(body[group['marker']['body_child_index']]))
        for record in [group['marker'], *group['content_records'], group['end_boundary']['record']]:
            assert record == by_index[record['body_child_index']]
        rendered = '\n'.join(record['rendered_text'] for record in group['content_records'])
        assert rendered == group['formalSourceContentWithTables'] == fill['new_properties']['formalSourceContentWithTables']
        assert fill['content_records'] == group['content_records']
        flags = {}
        for record in group['content_records']:
            for node in body[record['body_child_index']].iter():
                if node.tag in {W + 'del', W + 'moveFrom', W + 'drawing', W + 'object', W + 'instrText', M + 'oMath'}:
                    flags[node.tag] = flags.get(node.tag, 0) + 1
        assert not flags, ('Unrendered source content', fill['resolutionId'], flags)
        results.append({'resolutionId': fill['resolutionId'],
                        'content_sha256': sha(rendered.encode()),
                        'source_marker_paragraphs': group['marker']['paragraph_indices'],
                        'source_content_record_n': len(group['content_records']),
                        'source_table_n': sum(r['kind'] == 'table' for r in group['content_records']),
                        'unrendered_source_constructs': flags})
    assert mapping['fills'][3]['new_properties']['formalSourceContentWithTables'] == text(paragraphs[456])
    assert blocks['separate_optional_working_assumption'][0]['marker']['paragraph_indices'] == [457]
    assert not blocks['formal_group4_depends_on_neighboring_working_assumption']
    assert 'Note: 2Tx carrier 2' in mapping['fills'][2]['new_properties']['formalSourceContentWithTables']
    assert 'Case 1 | 1 Tx' in mapping['fills'][4]['new_properties']['formalSourceContentWithTables']
    assert 'FFS:' in mapping['fills'][5]['new_properties']['formalSourceContentWithTables']
    patch = ROOT / mapping['patch']['path']
    assert sha(patch.read_bytes()) == mapping['patch']['sha256']
    report = {'checked_utc': datetime.now(timezone.utc).isoformat(),
              'status': 'whole_raw_report_and_six_formal_blocks_verified',
              'source': whole['source'], 'document_xml_sha256': sha(raw),
              'mapping_sha256': sha(mapping_path.read_bytes()),
              'whole_source_sha256': sha(whole_path.read_bytes()),
              'whole_raw_body_records_n': len(whole['records']), 'whole_paragraph_n': len(paragraphs),
              'formal_group_n': 6, 'new_property_values_n': 6, 'groups': results,
              'standalone_working_assumption_required': False,
              'initial_root_read_adapter_failure': 'A prior SQL inspection omitted importing json; corrected read-only adapter, original DB unchanged.',
              'new_model_api_calls': 0, 'question_admissions': 0,
              'limit': 'Retained final-report XML verified; no original archive authentication or whole-report semantic mapping certification. Prose/table source values do not validate paraphrase equivalence.'}
    (BASE / 'root_evidence/UL_source_integrity.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'raw_records': len(whole['records']), 'formal_groups': 6}))


if __name__ == '__main__':
    main()
