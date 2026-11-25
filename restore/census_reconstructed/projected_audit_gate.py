#!/usr/bin/env python3
"""Compare every original audit field against public withheld-value projections.

The original comparison predicate remains unchanged. Each withheld string or
list is checked against its published SHA256 and length/count before replacing
that leaf by the released marker. Inline path markers also check exact visible
prefixes/suffixes. Raw execution receipts and private original comparisons are
preserved separately; the comparison package has explicit provenance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import census_tree_gate as gate

INLINE = re.compile(r'<withheld sha256=([0-9a-f]{64}) chars=(\d+)>')
DOCUMENT_EXTENSION = re.compile(r'\.(?:docx?|docm|zip|pdf|xlsx?|xlsm|pptx?|ppsx?|rtf|msg|rar|odt|vsd)$', re.I)
PROJECTION_SOURCE_SHA256 = '711aa6c1911ef36091becfc8cadd1fbc15c397fb17534946fffb92307bf26380'


def sha_text(value):
    return hashlib.sha256(value.encode('utf-8', 'surrogatepass')).hexdigest()


def project_like_reference(expected, actual, counts):
    if isinstance(expected, dict) and expected.get('withheld') is True:
        if 'sha256' not in expected:
            raise ValueError('Withheld audit value requires a published content digest')
        if 'chars' in expected and isinstance(actual, str):
            if len(actual) != expected['chars'] or sha_text(actual) != expected['sha256']:
                raise ValueError('Withheld string differs')
            counts['withheldStrings'] = counts.get('withheldStrings', 0) + 1
        elif 'count' in expected and isinstance(actual, list):
            encoded = json.dumps(actual, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
            if len(actual) != expected['count'] or sha_text(encoded) != expected['sha256']:
                raise ValueError('Withheld list differs')
            counts['withheldLists'] = counts.get('withheldLists', 0) + 1
        else:
            raise ValueError('Withheld marker type differs')
        return expected
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(expected) != set(actual):
            raise ValueError('Audit dictionary keys differ')
        return {key:project_like_reference(expected[key],actual[key],counts) for key in expected}
    if isinstance(expected, list):
        if not isinstance(actual,list) or len(expected) != len(actual):
            raise ValueError('Audit list length differs')
        return [project_like_reference(left,right,counts) for left,right in zip(expected,actual)]
    if isinstance(expected, str) and INLINE.search(expected):
        if not isinstance(actual,str):
            raise ValueError('Inline marker requires a string')
        expected_offset = actual_offset = 0
        for match in INLINE.finditer(expected):
            prefix = expected[expected_offset:match.start()]
            if not actual.startswith(prefix,actual_offset):
                raise ValueError('Visible path prefix differs')
            actual_offset += len(prefix)
            size = int(match[2])
            text = actual[actual_offset:actual_offset+size]
            if len(text) != size or sha_text(text) != match[1]:
                raise ValueError('Withheld inline text differs')
            actual_offset += size
            expected_offset = match.end()
            # The published name rule hashes the entire filename (including
            # extension), then appends its extension as a visible type label.
            extension = DOCUMENT_EXTENSION.search(text)
            if extension and expected.startswith(extension.group(), expected_offset):
                expected_offset += len(extension.group())
                counts['displayExtensionsVerified'] = counts.get('displayExtensionsVerified',0)+1
            counts['inlineStrings'] = counts.get('inlineStrings',0)+1
        if actual[actual_offset:] != expected[expected_offset:]:
            raise ValueError('Visible path suffix differs')
        return expected
    if expected != actual:
        raise ValueError('Visible audit value differs')
    return actual


def fields(runner, kind, document):
    if kind == 'pack':
        return {'total':runner.counts_only(document['total']),
                'byWg':runner.counts_only({row['wg']:row for row in document['byWg']})}
    return {'wg':runner.counts_only(document['wg']), 'corpus':document['corpus'], 'bodyText':document['bodyText']}


def compare_and_certify(args):
    source = args.execution_directory.resolve()
    destination = args.comparison_directory.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Comparison package must be new or empty')
    source_receipt = gate.read(source/'replay_receipt.json')
    condition = gate.read(source/'audit_condition.json')
    if set(source_receipt['audits']) != {'pack','clause'}:
        raise ValueError('Both complete original audit executions are required')
    runner = gate.load(args.code/'restore_census_artifact.py','projected_original_runner')
    results = {}
    for kind in ['pack','clause']:
        executed = source_receipt['audits'][kind]
        output = source/f'{kind}_audit.json'
        if gate.digest(output) != executed['outputSha256'] or gate.digest(args.code/f'audit_{kind}_links.py') != executed['auditorSha256']:
            raise ValueError('Executed original auditor/output identity differs')
        rel = 'pack_link_audit.json' if kind == 'pack' else 'final/reconciliation/clause_link_audit_rerun.json'
        public = gate.read(args.reference/rel)
        actual_fields = fields(runner,kind,gate.read(output))
        expected_fields = fields(runner,kind,public)
        counts = {}
        projected = project_like_reference(expected_fields,actual_fields,counts)
        comparison = {key:runner.differences(expected_fields[key],projected[key],'/'+key) for key in expected_fields}
        if any(comparison.values()):
            raise ValueError('Original comparison predicate failed after verified public projection')
        result = {**executed,'referenceSha256':gate.digest(args.reference/rel),'comparison':comparison,
            'allComparedFieldsMatch':True,'projectionVerification':counts,
            'comparisonPredicate':'Pinned original differences/counts_only; every withheld leaf verified by SHA256 and length/count'}
        if args.original_reference:
            original = gate.read(args.original_reference/rel)
            original_fields = fields(runner,kind,original)
            original_comparison = {key:runner.differences(original_fields[key],actual_fields[key],'/'+key) for key in original_fields}
            if any(original_comparison.values()):
                raise ValueError('Original private full-reference comparison failed')
            result['originalUnprojectedReferenceSha256'] = gate.digest(args.original_reference/rel)
            result['originalUnprojectedComparison'] = original_comparison
            result['originalUnprojectedComparisonPassed'] = True
        results[kind] = result
    destination.mkdir(parents=True,exist_ok=True)
    for name in ['audit_condition.json','replacement_reads.jsonl','input_gate.json','pack_audit.json','clause_audit.json']:
        shutil.copyfile(source/name,destination/name)
    receipt = {**source_receipt,'audits':results,'comparisonHelperSha256':gate.digest(__file__),
        'publishedProjectionSourceSha256':PROJECTION_SOURCE_SHA256,
        'originalExecutionReceiptSha256':gate.digest(source/'replay_receipt.json'),
        'rawExecutionReceiptPreserved':True,'allOriginalComparedFieldsRetained':True,
        'freshAuditExecutionPerformedDuringRecomparison':False}
    gate.write(destination/'replay_receipt.json',receipt)
    args.audit_directory = destination
    result = gate.certify(args)
    if not result['selectedReconstructionWithFullAuditPassed']:
        raise ValueError('Bound input/full-audit certification failed')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['compare','run'])
    for name in ['root','fixture','proof','code','native-module','reference','comparison-directory','out']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--execution-directory',type=Path)
    parser.add_argument('--original-reference',type=Path)
    for name in ['original-root','stage','artifact']:
        parser.add_argument('--'+name,type=Path)
    args=parser.parse_args()
    if args.command=='run':
        if any(getattr(args,key) is None for key in ['original_root','stage','artifact','execution_directory']):
            parser.error('run requires original-root, stage, artifact and execution-directory')
        certification_out = args.out
        args.out = args.execution_directory
        try:
            gate.run_audit(args)
        except SystemExit as error:
            # Preserve the original raw/public comparison failure. The fresh
            # full executions must exist and match their recorded hashes below.
            if error.code != 1:
                raise
        args.out = certification_out
    elif args.execution_directory is None:
        parser.error('compare requires execution-directory')
    result=compare_and_certify(args)
    print({'selectedReconstructionWithFullAuditPassed':result['selectedReconstructionWithFullAuditPassed'],
           'fullCorpusReconstructionCertified':result['fullCorpusReconstructionCertified']})


if __name__=='__main__':
    main()
