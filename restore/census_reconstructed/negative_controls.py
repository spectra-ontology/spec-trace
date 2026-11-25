#!/usr/bin/env python3
"""Exercise census gate failures using disposable copies of the selected tree."""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import tempfile
import zipfile
import census_tree_gate as gate


def run(args):
    fixture = gate.read(args.fixture)
    rows = fixture['files']
    native = next(r for r in rows if not r['converted'])
    converted = next(r for r in rows if r['converted'] and 'clause' in r['requiredFullAuditReaders'])
    records = []
    args.scratch.mkdir(parents=True, exist_ok=True)
    for name in ['missing_native', 'extra_path', 'changed_native', 'changed_reader_with_rebound_output', 'malformed_xml_with_rebound_output', 'tampered_conversion_binding', 'missing_full_audit']:
        with tempfile.TemporaryDirectory(prefix=name+'-', dir=args.scratch) as temp:
            root = Path(temp)
            for row in rows + fixture['archives']:
                target = gate.safe(root, row['path'])
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(gate.safe(args.root, row['path']), target)
            proof = gate.read(args.proof)
            candidate = gate.safe(root, converted['path'])
            if name == 'missing_native':
                gate.safe(root, native['path']).unlink()
            elif name == 'extra_path':
                (gate.safe(root, fixture['scopeRoots'][0]) / 'unexpected.bin').write_bytes(b'extra')
            elif name == 'changed_native':
                with gate.safe(root, native['path']).open('ab') as stream:
                    stream.write(b'changed')
            elif name in ['changed_reader_with_rebound_output', 'malformed_xml_with_rebound_output']:
                with zipfile.ZipFile(candidate) as archive:
                    entries = [(item, archive.read(item)) for item in archive.infolist()]
                with zipfile.ZipFile(candidate, 'w') as archive:
                    altered = False
                    for info, data in entries:
                        if info.filename == 'word/document.xml':
                            if name == 'changed_reader_with_rebound_output':
                                if b'Clauses affected' not in data:
                                    raise ValueError('Negative-control target label was not found')
                                data = data.replace(b'Clauses affected', b'Unsupported label')
                            else:
                                data = b'<broken'
                            altered = True
                        archive.writestr(info, data)
                    assert altered
                for row in proof['conversions']:
                    if row['path'] == converted['path']:
                        row['outputSha256'] = gate.digest(candidate)
                        row['outputSha1'] = gate.digest(candidate, 'sha1')
            elif name == 'tampered_conversion_binding':
                proof['conversions'][0]['sourceSha256'] = '0' * 64
            gate.write(root / 'proof.json', proof)
            result = gate.verify_inputs(root, args.fixture, root/'proof.json', args.code, args.native_module)
            errors = sorted({row['error'] for row in result['failures']})
            if name == 'missing_full_audit':
                cert_args = argparse.Namespace(root=root, fixture=args.fixture, proof=root/'proof.json', code=args.code,
                    native_module=args.native_module, audit_directory=None, out=root/'certification.json')
                cert = gate.certify(cert_args)
                observed = result['selectedInputGatePassed'] and not cert['selectedReconstructionWithFullAuditPassed']
                errors = ['full_audit_required']
            else:
                expected = {'missing_native':'file_missing', 'extra_path':'file_unexpected', 'changed_native':'unconverted_bytes',
                    'changed_reader_with_rebound_output':'scientific_reader_digest', 'malformed_xml_with_rebound_output':'strict_xml',
                    'tampered_conversion_binding':'conversion_binding'}[name]
                observed = not result['selectedInputGatePassed'] and expected in errors
            records.append({'control':name, 'rejectedAsExpected':observed, 'observedErrors':errors})
    # A comparison may omit historical SHA1; an auditor read must retain actual SHA1.
    replacement = gate.safe(args.root, converted['path']).resolve()
    if gate.digest(replacement, 'sha1') == converted['sha1']:
        raise ValueError('The SHA1 control requires a byte-different reconstructed file')
    gate._AUDIT_REPLACEMENTS = {replacement: replacement}
    gate._AUDIT_FORM_READER = lambda _: {'path': str(replacement), 'sha1': converted['sha1']}
    try:
        gate.replaced_form_reader(str(replacement))
        rejected = False
    except ValueError as error:
        rejected = 'actual reconstructed SHA1' in str(error)
    records.append({'control':'historical_sha1_substitution', 'rejectedAsExpected':rejected,
                    'observedErrors':['actual_sha1_required'] if rejected else []})
    receipt = {'schema':gate.SCHEMA, 'helperSha256':gate.digest(gate.__file__), 'testHelperSha256':gate.digest(__file__),
        'fixtureSha256':gate.digest(args.fixture), 'conversionProofSha256':gate.digest(args.proof),
        'sourceTextIncluded':False, 'originalInputsMutated':False, 'passed':all(r['rejectedAsExpected'] for r in records),
        'controls':records}
    gate.write(args.out, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['root','fixture','proof','code','native-module','scratch','out']:
        parser.add_argument('--'+name,type=Path,required=True)
    result = run(parser.parse_args())
    print({'passed':result['passed'],'controls':len(result['controls'])})
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
