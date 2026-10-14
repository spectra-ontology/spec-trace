#!/usr/bin/env python3
"""Build a whole-inventory fact source shared across future four-arm requests.

No question, answer, reference query, review, score or model output is read.
This is an additional source interface, not an edit of the frozen graph/schema.
"""
import collections
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
SOURCE = ROOT / 'data/inventory/RAN/List_of_Specifications_20260122.xlsx'
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def exact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def main():
    if hasattr(os, 'sched_getaffinity'):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    before_sha = sha(SOURCE)
    before_stat = {'size': SOURCE.stat().st_size, 'mtime_ns': SOURCE.stat().st_mtime_ns}
    with zipfile.ZipFile(SOURCE) as z:
        shared = []
        for _, e in ET.iterparse(z.open('xl/sharedStrings.xml'), events=['end']):
            if e.tag == NS + 'si':
                shared.append(''.join(t.text or '' for t in e.iter(NS + 't')))
                e.clear()
        header = None
        records = {}
        rows_read = 0
        for _, row in ET.iterparse(z.open('xl/worksheets/sheet1.xml'), events=['end']):
            if row.tag != NS + 'row':
                continue
            rows_read += 1
            cells = {}
            for cell in row:
                v = cell.find(NS + 'v')
                if v is None:
                    continue
                col = ''.join(c for c in cell.attrib['r'] if c.isalpha())
                cells[col] = shared[int(v.text)] if cell.attrib.get('t') == 's' else v.text
            if header is None:
                header = cells
                columns = {name: col for col, name in header.items()}
                assert columns['Responsible Primary'] == 'J' and columns['Spec number'] == 'A'
            else:
                r = {header[col]: value for col, value in cells.items()}
                number = r.get('Spec number', '')
                primary = r.get('Responsible Primary', '').strip()
                key = (number, primary)
                fact = records.setdefault(key, {'specNumber': number, 'responsiblePrimaryCode': primary,
                                                'isTS_source_values': set(), 'source_row_numbers': [],
                                                'source_first_link': r.get('Link')})
                fact['isTS_source_values'].add(r.get('Is TS'))
                fact['source_row_numbers'].append(int(row.attrib['r']))
            row.clear()
        member_sha = {name: hashlib.sha256(z.read(name)).hexdigest() for name in ['xl/sharedStrings.xml', 'xl/worksheets/sheet1.xml']}
    ordered = []
    groups = collections.defaultdict(set)
    for key, r in sorted(records.items()):
        r['isTS_source_values'] = sorted(r['isTS_source_values'], key=lambda v: (v is None, str(v)))
        ordered.append(r)
        groups[r['responsiblePrimaryCode']].add(r['specNumber'])
    groups = {code: sorted(numbers) for code, numbers in sorted(groups.items())}
    (HERE / 'full_inventory.jsonl').write_text(''.join(exact(r) + '\n' for r in ordered))
    (HERE / 'primary_to_specs.json').write_text(exact(groups) + '\n')
    header_text = 'Supplemental preserved 3GPP specification responsibility inventory, snapshot 2026-01-22. Each exact Responsible Primary code maps to specification numbers. R1..R5 mean RAN1..RAN5; RP means RAN plenary. Empty code is unassigned in this source. Do not infer ownership from number prefix, Responsible Secondary, graph filename or missing lookup. Historical version rows are deduplicated by exact number and primary code; multiple primary codes, if any, are retained. This is source data, not benchmark answers or accepted/applied CR evidence. No present-date ownership is asserted.\n'
    shared_text = header_text + exact(groups) + '\n'
    (HERE / 'shared_source.txt').write_text(shared_text)
    docs = []
    # Search corpus chunks are a standalone optional view of exactly the same
    # source. The recommended four-arm interface supplies the complete shared
    # source verbatim; no arm can lose responsibility information to retrieval.
    for code, numbers in groups.items():
        chunks = []
        pending = []
        for number in numbers:
            if pending and len(exact(pending + [number])) > 2500:
                chunks.append(pending)
                pending = []
            pending.append(number)
        if pending:
            chunks.append(pending)
        alias = ('RAN' + code[1:] if code.startswith('R') and code[1:].isdigit() else code)
        for index, part in enumerate(chunks):
            text = f'Official specification ownership responsibility inventory. Responsible Primary={code or "unassigned"}; working-group alias={alias or "unassigned"}. Exact specification numbers: ' + ', '.join(part)
            docs.append({'id': f'official-spec-primary-{code or "unassigned"}-{index:03d}',
                         'text': text, 'metadata': {'source_snapshot': '2026-01-22', 'source_sha256': before_sha,
                                                   'primary_code': code, 'complete_group_parts': len(chunks),
                                                   'part_index': index, 'group_spec_number_n': len(numbers),
                                                   'purpose': 'Whole source fact view, never per-question answer selection'}})
    (HERE / 'search_documents.jsonl').write_text(''.join(exact(r) + '\n' for r in docs))
    interface = {'kind': 'Separately frozen additional source interface; existing model experiments unchanged',
                 'recommended_policy': 'Append the identical complete UTF-8 shared_source.txt to every A/B/C/D serialized model request, at the same source-data role, including D follow-up calls. Do not select rows from task/gold/query/review/output or cap ownership facts. C/D native retrieved context budgets remain separately reported. Record source bytes/hash and total input/context lengths for every arm.',
                 'graph_SQL_conservation': 'No ResponsiblePrimary property or relationship is added to frozen Neo4j/SQLite. A/B use the identical provided source catalog to formulate exact source membership predicates. The source catalog is an extra evidence input and must not be misrepresented as a value-free schema or native-graph knowledge.',
                 'search_view': 'search_documents.jsonl is an optional portable whole-source retrieval index view. It is not a substitute for complete common source exposure in the recommended four-arm experiment, and no new retrieval has been run here.',
                 'schema': {'fact_key': ['specNumber', 'responsiblePrimaryCode'], 'fields': {'specNumber': 'string', 'responsiblePrimaryCode': 'string; empty=unassigned', 'isTS_source_values': 'array of original spreadsheet raw values, including null if missing', 'source_row_numbers': 'array of original 1-based worksheet row numbers', 'source_first_link': 'string|null'}, 'source_role': 'Responsible Primary only; secondary is not substituted', 'multi_owner_policy': 'Preserve exact source facts; do not force uniqueness or current-date interpretation'},
                 'method_exposure': {arm: {'file': 'shared_source.txt', 'sha256': sha(HERE / 'shared_source.txt'), 'complete': True, 'not_yet_model_executed': True} for arm in ['A_Text2Cypher', 'B_Text2SQL', 'C_single_retrieval', 'D_iterative_retrieval']},
                 'source_snapshot': '2026-01-22', 'full_worksheet_rows_including_header': rows_read,
                 'distinct_spec_number_n': len({r['specNumber'] for r in ordered}),
                 'distinct_spec_primary_facts_n': len(ordered), 'primary_codes': list(groups),
                 'per_primary_spec_number_n': {code: len(numbers) for code, numbers in groups.items()},
                 'shared_text_bytes': len(shared_text.encode()), 'shared_text_characters': len(shared_text),
                 'search_documents_n': len(docs), 'new_model_calls': 0,
                 'original_source': {'path': str(SOURCE), 'sha256': before_sha, 'members_sha256': member_sha, 'header': header},
                 'forbidden_inputs_read': {'questions': False, 'gold': False, 'reference_queries': False, 'semantic_reviews': False, 'scores': False, 'model_outputs': False},
                 'limits': ['Supplemental source context must be pinned before any new predictions. No existing model scores are inherited.', 'The source inventory alone does not establish section edition/counting unit, recency, approval meeting, causal influence or applied normative changes.']}
    after_sha = sha(SOURCE)
    after_stat = {'size': SOURCE.stat().st_size, 'mtime_ns': SOURCE.stat().st_mtime_ns}
    assert before_sha == after_sha and before_stat == after_stat and rows_read == 89071
    interface['source_before_after'] = {'before_sha256': before_sha, 'after_sha256': after_sha, 'before_stat': before_stat, 'after_stat': after_stat, 'unchanged': True}
    (HERE / 'interface.json').write_text(json.dumps(interface, ensure_ascii=False, indent=2) + '\n')
    files = []
    for name in ['prepare.py', 'full_inventory.jsonl', 'primary_to_specs.json', 'shared_source.txt', 'search_documents.jsonl', 'interface.json']:
        p = HERE / name
        files.append({'path': name, 'sha256': sha(p), 'bytes': p.stat().st_size})
    (HERE / 'manifest.json').write_text(json.dumps({'files': files, 'new_model_calls': 0, 'shared_all_arms_policy': 'interface.json'}, indent=2) + '\n')
    print(json.dumps({k: interface[k] for k in ['full_worksheet_rows_including_header', 'distinct_spec_number_n', 'distinct_spec_primary_facts_n', 'shared_text_characters', 'shared_text_bytes', 'search_documents_n', 'per_primary_spec_number_n']}))
    print('manifest_sha256=' + sha(HERE / 'manifest.json'))

if __name__ == '__main__':
    main()
