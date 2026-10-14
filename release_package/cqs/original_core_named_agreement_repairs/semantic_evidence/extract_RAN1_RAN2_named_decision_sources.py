#!/usr/bin/env python3
"""Question-identifier-only full retained report scan; no answer/reference inputs.

Every retained DOCX report is read in full. Paragraph windows are source evidence,
not a causal annotation or proof that the archive itself is complete.
"""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path('/home/sihyeon/workspace/spectra')
HERE = Path(__file__).resolve().parent
W = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
TARGETS = {'RAN1': ['R1-2001110'], 'RAN2': ['R2-2500064', 'R2-2508373']}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    sources = []
    all_hits = []
    for wg, identifiers in TARGETS.items():
        directory = ROOT / 'ontology/input/tsg/RAN/formal/meetings' / wg / 'Final_Report'
        for path in sorted(directory.glob('*.docx')):
            body = path.read_bytes()
            with zipfile.ZipFile(path) as archive:
                xml = archive.read('word/document.xml')
            tree = ET.fromstring(xml)
            nodes = tree.findall('.//w:p', W)
            paragraphs = []
            for index, node in enumerate(nodes):
                style = node.find('./w:pPr/w:pStyle', W)
                paragraphs.append({'paragraph_zero_based': index,
                    'style': style.attrib.get('{' + W['w'] + '}val', '') if style is not None else '',
                    'literal_text': ''.join(t.text or '' for t in node.findall('.//w:t', W))})
            source = {'path': str(path.relative_to(ROOT)), 'sha256': sha(body),
                      'document_xml_sha256': sha(xml), 'whole_document_paragraph_n': len(paragraphs),
                      'source_bytes_unchanged': sha(path.read_bytes()) == sha(body)}
            if not source['source_bytes_unchanged']:
                raise ValueError('Source changed')
            sources.append(source)
            heading_path = []
            for i, paragraph in enumerate(paragraphs):
                style = paragraph['style']
                if style.startswith('Heading') and style[7:].isdigit():
                    level = int(style[7:])
                    heading_path = [h for h in heading_path if h['level'] < level]
                    heading_path.append({'level': level, **paragraph})
                for identifier in identifiers:
                    if identifier in paragraph['literal_text']:
                        all_hits.append({'wg': wg, 'question_identifier': identifier,
                            'source': source, 'heading_path': list(heading_path),
                            'hit_paragraph_zero_based': i,
                            'literal_window': paragraphs[max(0, i - 4):min(len(paragraphs), i + 14)]})
    report = {'status': 'FULL_RETAINED_REPORT_IDENTIFIER_SCAN_COMPLETE',
        'source_inputs': 'Only original question TDoc identifiers and full retained DOCX bytes. No graph, query, gold or model output is used by this extraction.',
        'target_identifiers': TARGETS, 'source_reports_n': len(sources), 'sources': sources,
        'hits_n': len(all_hits), 'hits': all_hits,
        'scope_limits': ['Literal occurrence and nearby decision text are not automatically evidence of led-to causality.',
                         'Completeness applies to retained reports actually read, not all historical reports or normative adoption.',
                         'Heading paths use actual DOCX styles; ToC and narrative hits remain separately visible.'],
        'new_model_calls': 0, 'new_native_executions': 0, 'admitted_repairs': 0}
    out = HERE / 'RAN1_RAN2_named_decision_sources.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'source_reports_n': len(sources),
                      'hits_n': len(all_hits), 'report_sha256': sha(out.read_bytes())}), flush=True)


if __name__ == '__main__':
    main()
