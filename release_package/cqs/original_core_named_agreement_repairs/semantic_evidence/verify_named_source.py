#!/usr/bin/env python3
"""Check the retained named-draft decision and its frozen native projection.

This is a programmatic source comparison, not expert assessment, a model
prediction, or evidence for every REFERENCES relation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(bundle):
    tasks = [json.loads(s) for s in (bundle/'tasks.jsonl').read_text().splitlines() if s]
    if len(tasks) != 1 or tasks[0]['id'] != 'RAN1_P2_CQ2-2':
        raise ValueError('Wrong named-decision cohort')
    task = tasks[0]
    context = task['source_context']['actual_original_decision']
    source = bundle/'source_evidence/Final_Report_RAN1-100-e.docx'
    if sha(source) != context['source']['sha256']:
        raise ValueError('Original report changed')
    with zipfile.ZipFile(source) as zipped:
        document = zipped.read('word/document.xml')
    if hashlib.sha256(document).hexdigest() != context['source']['document_xml_sha256']:
        raise ValueError('Original report document XML changed')
    ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    root = ET.fromstring(document)
    paragraphs = [''.join(t.text or '' for t in p.findall('.//w:t',ns))
                  for p in root.findall('.//w:p',ns)]
    if len(paragraphs) != context['source']['whole_document_paragraph_n']:
        raise ValueError('Whole report paragraph count differs')
    for expected in context['literal_paragraphs']:
        if paragraphs[expected['paragraph_zero_based']] != expected['literal_text']:
            raise ValueError('Named-decision literal differs')
    if paragraphs[532] != 'Agreement:' or not paragraphs[533].startswith(
            'The draft CR in R1-2001110 is agreed with a modification'):
        raise ValueError('Source does not explicitly agree the named draft')
    evidence = task['portable_native_evidence']
    receipt_path = bundle/evidence['receipt_file']
    rows_path = bundle/evidence['rows_file']
    if sha(receipt_path) != evidence['receipt_sha256'] or sha(rows_path) != evidence['rows_sha256']:
        raise ValueError('Retained native bytes differ')
    receipt = json.loads(receipt_path.read_text())
    columns = receipt['execution']['columns']
    rows = [dict(zip(columns,json.loads(s))) for s in rows_path.read_text().splitlines() if s]
    if len(rows) != 2 or {r['a.resolutionId'] for r in rows} != {'AGR-100-6.1-001'}:
        raise ValueError('Native full-row identity projection differs')
    if any(r['a.content'].splitlines()[0] != paragraphs[533] for r in rows):
        raise ValueError('Graph literal first line differs from explicit source decision')
    if task['required_fields'] != [{'name':'a.resolutionId','type':'string','nullable':False,
                                  'source_column_or_expression':'a.resolutionId'}]:
        raise ValueError('Unasked context fields became required answers')
    if task['collection'] != {'kind':'set'} or task['cardinality_policy'] != {'mode':'all'}:
        raise ValueError('Complete unordered identity projection changed')
    return {'status':'PASS','id':task['id'],'repair_sha256':task['repair_sha256'],
            'source_sha256':sha(source),'paragraphs_checked':[531,532,533,534],
            'full_native_rows':2,'unique_requested_identity_count':1,
            'expert_validation_n':0,'model_calls':0,
            'scope':'One explicit named-draft adoption decision; not general causality, normative incorporation, or full historical source completeness.'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parent.parent)
    args=parser.parse_args()
    print(json.dumps(verify(args.bundle.resolve()),ensure_ascii=False))
