#!/usr/bin/env python3
"""Compare complete derived paths with the released text-free frontier.

The original verify-derived command separately checks every historical byte.
This check supplies exact set coverage, including unexpected paths, for the
local base tree used by the explicit selected-replacement audit condition.
"""
import argparse
import collections
import gzip
import json
from pathlib import Path
import census_tree_gate as gate


def check(args):
    frontier_receipt = gate.read(args.frontier_receipt)
    if gate.digest(args.frontier) != frontier_receipt['frontierSha256']:
        raise ValueError('Frontier checksum differs')
    expected = set()
    with gzip.open(args.frontier, 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            expected.add((row['path'], row['kind']))
    # The published frontier is partitioned at the five <WG>/derived roots.
    roots = sorted({str(Path(*Path(path).parts[:Path(path).parts.index('derived')+1])) for path, _ in expected})
    actual = set()
    for root in roots:
        for path in gate.safe(args.root, root).rglob('*'):
            relative = path.relative_to(args.root).as_posix()
            kind = 'symlink' if path.is_symlink() else 'file' if path.is_file() else 'directory' if path.is_dir() else 'other'
            actual.add((relative, kind))
    byte_receipt = gate.read(args.byte_receipt)
    byte_passed = byte_receipt.get('frontierSha256') == frontier_receipt['frontierSha256'] and not byte_receipt.get('failures')
    expected_counts = collections.Counter(kind for _, kind in expected)
    byte_passed = byte_passed and byte_receipt.get('counts') == {'directories': expected_counts['directory'], 'files': expected_counts['file']}
    receipt = {'schema':gate.SCHEMA, 'condition':'Original local derived base before explicit selected archive read replacements',
        'frontierSha256':gate.digest(args.frontier), 'originalFullByteReceiptSha256':gate.digest(args.byte_receipt),
        'helperSha256':gate.digest(__file__), 'expectedCounts':dict(expected_counts), 'actualCounts':dict(collections.Counter(kind for _,kind in actual)),
        'missing':[{'path':p,'kind':k} for p,k in sorted(expected-actual)],
        'unexpected':[{'path':p,'kind':k} for p,k in sorted(actual-expected)],
        'completePathSetMatched':expected==actual, 'allOriginalHistoricalBytesMatched':byte_passed,
        'wholeCorpusFreshlyReconstructed':False, 'sourceTextIncluded':False}
    receipt['passed'] = receipt['completePathSetMatched'] and byte_passed
    gate.write(args.out, receipt)
    return receipt


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['root','frontier','frontier-receipt','byte-receipt','out']:
        parser.add_argument('--'+name,type=Path,required=True)
    result=check(parser.parse_args())
    print({k:v for k,v in result.items() if k not in ['missing','unexpected']})
    if not result['passed']:
        raise SystemExit(1)
