#!/usr/bin/env python3
"""Replay the frozen 298-pair scope intervention in a fresh scratch directory."""
from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import time

sys.dont_write_bytecode = True
BUNDLE = Path(__file__).resolve().parent
PAYLOAD = BUNDLE / 'payload'
CODE_RELATIVE = 'code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def result_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True, help='Public release checkout root')
    parser.add_argument('--output', type=Path, required=True, help='New scratch directory; must not exist')
    args = parser.parse_args()
    release, output = args.release.resolve(), args.output.resolve()
    require(sys.version.startswith('3.10.12') and sqlite3.sqlite_version == '3.37.2',
            'Use the pinned Python 3.10.12 / SQLite 3.37.2 runtime.')
    require(not output.exists(), '--output must be a new scratch directory.')
    manifest = read_json(PAYLOAD / 'edit_manifest.json')
    pin = read_json(PAYLOAD / 'pre_execution_pin.json')
    source = PAYLOAD / 'scope_intervention.py'
    require(sha(source) == pin['scriptSha256'], 'Frozen source hash mismatch.')
    require(sha(PAYLOAD / 'edit_manifest.json') == pin['editManifestSha256'], 'Frozen manifest hash mismatch.')
    require(sha(PAYLOAD / 'protocol.md') == pin['protocolSha256'], 'Frozen protocol hash mismatch.')
    expected_path = PAYLOAD / 'expected_paired_results.jsonl'
    expected_sha = 'd6c143ff25af289281bc17a4ce5f22b621eeef57242ed3d2a0fb148afa9255f9'
    require(sha(expected_path) == expected_sha, 'Frozen expected result hash mismatch.')
    code = release / CODE_RELATIVE
    input_paths = {}
    for name, digest in manifest['inputSha256'].items():
        if name == 'classifier':
            path = release / 'responses/final/supplement_cycle/query_writers/miss_clusters_ten_runs.json'
        elif name.startswith('code/'):
            path = code / name[5:]
        else:
            path = release / name
        require(path.is_file() and sha(path) == digest, 'Release input hash mismatch: ' + str(path))
        input_paths[name] = path
    for wg, meta in manifest['databases'].items():
        compressed = release / 'sqlite' / f'{wg}.sqlite.gz'
        require(compressed.is_file() and sha(compressed) == meta['compressedSha256'],
                'Compressed database hash mismatch: ' + wg)
        input_paths['compressedDatabase:' + wg] = compressed
    before = {name: sha(path) for name, path in input_paths.items()}
    output.mkdir(parents=True)
    for name in ['edit_manifest.json', 'pre_execution_pin.json', 'protocol.md']:
        shutil.copyfile(PAYLOAD / name, output / name)
    (output / 'sqlite').mkdir()
    for wg, meta in manifest['databases'].items():
        target = output / meta['path']
        with gzip.open(release / 'sqlite' / f'{wg}.sqlite.gz', 'rb') as handle, target.open('xb') as out:
            shutil.copyfileobj(handle, out)
        require(sha(target) == meta['sha256'], 'Decompressed database hash mismatch: ' + wg)
        target.chmod(0o444)
    # Keep the original functions and imports; supply explicit roots for this CLI.
    # No repository discovery, CLI main block, or preparation mutation is evaluated.
    tree = ast.parse(source.read_text())
    selected = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef))]
    namespace = {'__file__': str(source), '__name__': 'frozen_scope_replay', 'HERE': output,
                 'ROOT': release, 'PACKAGE': release, 'CODE': code}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), 'exec'), namespace)
    started = time.monotonic()
    namespace['run']('full')
    actual_list = result_rows(output / 'paired_results.jsonl')
    expected_list = result_rows(expected_path)
    actual = {entry['case']: entry for entry in actual_list}
    expected = {entry['case']: entry for entry in expected_list}
    require(len(actual_list) == len(actual) == len(expected_list) == len(expected) == 298,
            'Replay is incomplete or has duplicate cases.')
    require(set(actual) == set(expected), 'Replay case identities differ.')
    differences = []
    for case in sorted(expected):
        for key in ['gold', 'goldSet', 'questionSha256']:
            if actual[case][key] != expected[case][key]:
                differences.append({'case': case, 'field': key})
        for arm in ['original', 'fixed']:
            for key in ['set', 'status', 'error', 'score', 'sqlSha256', 'rowCountBefore2000Limit']:
                if actual[case][arm][key] != expected[case][arm][key]:
                    differences.append({'case': case, 'arm': arm, 'field': key})
    after = {name: sha(path) for name, path in input_paths.items()}
    receipt = {'wrapperSha256': sha(__file__), 'frozenSourceSha256': sha(source),
        'manifestSha256': sha(PAYLOAD / 'edit_manifest.json'), 'protocolSha256': sha(PAYLOAD / 'protocol.md'),
        'release': str(release), 'output': str(output), 'python': sys.version,
        'sqlite': sqlite3.sqlite_version, 'cases': len(actual), 'pairedQueries': 2 * len(actual),
        'expectedResultSha256': expected_sha, 'freshResultSha256': sha(output / 'paired_results.jsonl'),
        'comparison': 'Complete normalized row sets, gold, question/query hashes, status, errors, scores and row counts; elapsed times and physical row order may vary.',
        'differences': differences, 'all298PairedOutputsMatch': not differences,
        'releaseInputsUnchanged': before == after, 'inputSha256Before': before, 'inputSha256After': after,
        'elapsedSeconds': time.monotonic() - started,
        'requiresAgentsFile': False,
        'releaseAncestorsContainAgentsFile': any((p / 'AGENTS.md').exists() for p in [release, *release.parents])}
    (output / 'portable_replay_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    require(not differences, 'Fresh replay differs from the frozen output; inspect portable_replay_receipt.json.')
    require(before == after, 'Release input changed during replay.')
    print(json.dumps({'cases': len(actual), 'all298PairedOutputsMatch': True,
                      'releaseInputsUnchanged': True, 'receipt': str(output / 'portable_replay_receipt.json')}), flush=True)


if __name__ == '__main__':
    main()
