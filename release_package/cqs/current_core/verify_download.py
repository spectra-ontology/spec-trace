#!/usr/bin/env python3
"""Fetch a pinned public review archive anonymously and replay its saved proofs.

This script never uses local repository data, credentials, models or databases.
The retained 371-item parent supplies index dependencies only; its previously
verified historical experiment is not silently replayed from a partial archive.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request

PREFIX = 'release_package/cqs/current_core/'
FILES = ('manifest.json', 'archive_inventory.json', 'review_evidence.tar.gz')
MAX_DOWNLOAD = 2 * 1024 ** 3
MAX_EXPANDED = 8 * 1024 ** 3


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(part)
    return digest.hexdigest()


def safe_relative(name):
    if not isinstance(name, str) or not name or '\\' in name or '\x00' in name:
        raise ValueError('Invalid archive member path')
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '.' in name.split('/') or str(path) != name:
        raise ValueError('Unsafe or noncanonical archive member path')
    return path


def fetch(commit, name, downloads):
    url = 'https://raw.githubusercontent.com/spectra-ontology/spec-trace/' + commit + '/' + PREFIX + name
    target = downloads / name
    request = urllib.request.Request(url, headers={'User-Agent': 'SPECTRA-anonymous-proof-replay'})
    # An explicit new opener has no account/credential/cookie handlers.
    opener = urllib.request.build_opener()
    for attempt in range(3):
        partial = target.with_name(target.name + '.partial')
        try:
            total = 0
            digest = hashlib.sha256()
            with opener.open(request, timeout=60) as response, partial.open('wb') as stream:
                if response.status != 200:
                    raise ValueError('Anonymous public download did not return HTTP 200')
                final_url = response.geturl()
                if not final_url.startswith('https://raw.githubusercontent.com/'):
                    raise ValueError('Unexpected public-download redirect')
                for chunk in iter(lambda: response.read(1024 * 1024), b''):
                    total += len(chunk)
                    if total > MAX_DOWNLOAD:
                        raise ValueError('Public file exceeds the fixed download cap')
                    digest.update(chunk)
                    stream.write(chunk)
            partial.replace(target)
            return {'path': PREFIX + name, 'url': url, 'http_status': 200,
                    'sha256': digest.hexdigest(), 'bytes': total,
                    'transport_attempts': attempt + 1, 'authorization_header_used': False}
        except Exception:
            partial.unlink(missing_ok=True)
            if attempt == 2:
                raise
            time.sleep(1)


def artifact_pin(manifest, key, expected_name):
    entry = manifest.get(key)
    if isinstance(entry, dict):
        name = entry.get('file', entry.get('path'))
        digest = entry.get('sha256')
        size = entry.get('bytes')
    else:
        name = manifest.get(key + '_file')
        digest = manifest.get(key + '_sha256')
        size = manifest.get(key + '_bytes')
    # The wrapper may also carry a conventional exact membership mapping.
    if name is None and isinstance(manifest.get('files'), dict):
        name = expected_name
        value = manifest['files'].get(expected_name)
        if isinstance(value, str):
            digest = value
        elif isinstance(value, dict):
            digest, size = value.get('sha256'), value.get('bytes')
    if name not in (expected_name, PREFIX + expected_name) or not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
        raise ValueError('Missing or malformed exact public ' + key + ' pin')
    return digest, size


def inventory_files(inventory):
    files = inventory.get('files')
    if not isinstance(files, dict) or not files:
        raise ValueError('Inventory must contain a nonempty exact file mapping')
    normalized = {}
    for name, value in files.items():
        safe_relative(name)
        if isinstance(value, str):
            digest, size = value, None
        elif isinstance(value, dict):
            digest, size = value.get('sha256'), value.get('bytes')
        else:
            raise ValueError('Malformed inventory record')
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError('Invalid inventory digest')
        if size is not None and (not isinstance(size, int) or isinstance(size, bool) or size < 0):
            raise ValueError('Invalid inventory file size')
        normalized[name] = (digest, size)
    return normalized


def extract_verified(archive_path, expected, checkout, layout=None):
    archive_expected=expected
    aliases={}
    if layout and ('archive_files' in layout or 'duplicate_files' in layout):
        archive_expected=inventory_files({'files':layout.get('archive_files')})
        aliases=layout.get('duplicate_files')
        if not isinstance(aliases,dict) or set(archive_expected)&set(aliases) or set(archive_expected)|set(aliases)!=set(expected):
            raise ValueError('Content deduplication does not preserve exact inventory membership')
        for name,value in archive_expected.items():
            if value!=expected[name]:
                raise ValueError('Canonical archive content differs from the full inventory')
        for name,canonical in aliases.items():
            safe_relative(name);safe_relative(canonical)
            if canonical not in archive_expected or expected[name]!=archive_expected[canonical]:
                raise ValueError('Duplicate content does not point to an identical verified regular member')
    seen = set()
    total = 0
    with tarfile.open(archive_path, 'r:gz') as archive:
        for member in archive:
            path = safe_relative(member.name)
            if member.name in seen or not member.isfile() or member.name not in archive_expected:
                raise ValueError('Duplicate, nonregular or unmanifested archive member')
            seen.add(member.name)
            total += member.size
            if member.size < 0 or total > MAX_EXPANDED:
                raise ValueError('Archive exceeds the fixed expanded-size cap')
            wanted_sha, wanted_size = archive_expected[member.name]
            if wanted_size is not None and member.size != wanted_size:
                raise ValueError('Archived size differs from exact inventory')
            destination = checkout.joinpath(*path.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.resolve().is_relative_to(checkout.resolve()):
                raise ValueError('Archive destination escapes the fresh checkout')
            source = archive.extractfile(member)
            digest = hashlib.sha256()
            count = 0
            with destination.open('xb') as stream:
                for part in iter(lambda: source.read(1024 * 1024), b''):
                    count += len(part)
                    digest.update(part)
                    stream.write(part)
            if count != member.size or digest.hexdigest() != wanted_sha:
                raise ValueError('Archived bytes differ from exact inventory: ' + member.name)
    if seen != set(archive_expected):
        raise ValueError('Archive is missing manifested files')
    for name,canonical in sorted(aliases.items()):
        destination=checkout.joinpath(*safe_relative(name).parts)
        source=checkout.joinpath(*safe_relative(canonical).parts)
        destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.exists() or not destination.resolve().is_relative_to(checkout.resolve()):
            raise ValueError('Duplicate materialization would replace an existing file or escape the fresh checkout')
        shutil.copyfile(source,destination)
        digest,size=expected[name]
        total+=destination.stat().st_size
        if total>MAX_EXPANDED or sha(destination)!=digest or (size is not None and destination.stat().st_size!=size):
            raise ValueError('Materialized duplicate differs from exact inventory')
    return {'file_n': len(expected), 'archive_regular_member_n':len(seen),
            'byte_identical_files_materialized':len(aliases), 'expanded_bytes': total,
            'links_allowed': False, 'duplicate_members_allowed': False,
            'exact_inventory_membership_verified': True}


def run_offline(checkout, reports):
    # Commands execute from the extracted checkout; absolute paths preserve
    # the caller's chosen output directory when it was supplied relatively.
    checkout = checkout.resolve()
    reports = reports.resolve()
    base = checkout / 'release_package/cqs'
    parent = base / 'original_core_repair'
    py = [sys.executable, '-B', '-S']
    checks = []
    def run(name, arguments):
        command = py + [str(value) for value in arguments]
        started = time.monotonic()
        completed = subprocess.run(command, cwd=checkout, capture_output=True, text=True, timeout=1200)
        record = {'name': name, 'command': command, 'exit_code': completed.returncode,
                  'elapsed_seconds': time.monotonic() - started,
                  'stdout': completed.stdout, 'stderr': completed.stderr,
                  'status': 'PASS' if completed.returncode == 0 else 'FAIL'}
        checks.append(record)
        (reports / (name + '.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'offline_check': name, 'status': record['status']}), flush=True)
        if completed.returncode:
            raise ValueError('Offline proof replay failed: ' + name)
    top = base / 'original_core_topk_replacements'
    run('topk_replacements', [top/'verify_replacements.py', '--bundle', top, '--parent', parent,
                              '--out', reports/'topk_proof.json'])
    for stem in ('followup', 'source', 'natural'):
        bundle = base / ('original_core_' + stem + '_repairs')
        evidence = base / ('original_core_' + stem + '_evaluation')
        run(stem + '_contracts', [bundle/'verify_additions.py', '--bundle', bundle, '--parent', parent])
        run(stem + '_model_replay', [evidence/'runtime/verify_additional_evaluation.py',
                                    '--evidence', evidence, '--bundle', bundle, '--parent', parent,
                                    '--out', reports/(stem + '_model_proof.json')])
    final = base / 'original_core_final_repairs'
    run('final_three_contracts', [final/'verify_additions.py', '--bundle', final, '--parent', parent])
    final_evidence = base/'original_core_final_evaluation'
    run('final_three_model_replay', [final_evidence/'runtime/verify_additional_evaluation.py', '--evidence', final_evidence, '--bundle', final, '--parent', parent, '--out', reports/'final_three_model_proof.json'])
    top_evidence = base/'original_core_topk_evaluation'
    run('topk_current_model_replay', [top_evidence/'runtime/verify_topk_evaluation.py', '--evidence', top_evidence, '--bundle', top, '--parent', parent, '--out', reports/'topk_model_proof.json'])
    run('sql378_compact_replay', [base/'original_core_sql_interface_evaluation/verify_archive.py'])
    run('source_access23', [base/'source_access_diagnostic/verify_saved.py'])
    run('current_original400_index', [base/'current_core/verify_index.py'])
    # Inspect the actual prepared forms, without turning preparation into a
    # claim that a human/domain expert has answered any question.
    kit = base/'current_core/expert_review'
    kit_manifest = json.loads((kit/'manifest.json').read_text())
    for name, expected in kit_manifest['files'].items():
        safe_relative(name)
        if sha(kit/name) != expected:
            raise ValueError('Prepared human-review kit differs from its manifest')
    read_rows = lambda path: [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    originals = {row['id']:row for row in read_rows(parent/'provenance/original_benchmark.jsonl')}
    questions = read_rows(kit/'source_first_questions.jsonl')
    forms = read_rows(kit/'blank_answer_forms.jsonl')
    if len(questions) != 560 or len(forms) != 560 or len({row['id'] for row in questions}) != 560:
        raise ValueError('Prepared human-review inputs omit or duplicate original IDs')
    for question, form in zip(questions, forms):
        if (set(question) != {'id','question_en','wg'} or question['id'] != form['id']
                or question['question_en'] != form['question_en']
                or question['question_en'] != originals[question['id']]['question_en']
                or form['answer_from_source'] is not None
                or form['review_completion_status'] != 'not_started'
                or form['reference_gold_seen_before_source_answer'] is not False):
            raise ValueError('Prepared human-review form is populated or differs from original input')
    record = {'name':'prepared560_human_review_inputs', 'status':'PASS',
              'prepared_question_n':560,'blank_form_n':560,'completed_human_or_expert_n':0,
              'raw_source_population_availability_certified':False}
    checks.append(record)
    (reports/'prepared560_human_review_inputs.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'offline_check':record['name'],'status':'PASS'}),flush=True)
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--out-dir', required=True, type=Path)
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--skip-offline', action='store_true', help='Download-only diagnostic; cannot report complete verification')
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}', args.commit):
        parser.error('--commit must be a full 40-character exact Git commit')
    if args.manifest_sha256 and not re.fullmatch('[0-9a-f]{64}', args.manifest_sha256):
        parser.error('--manifest-sha256 must be an exact lowercase SHA256')
    args.out_dir.mkdir(parents=True, exist_ok=False)
    downloads = args.out_dir/'downloads'; downloads.mkdir()
    checkout = args.out_dir/'checkout'; checkout.mkdir()
    reports = args.out_dir/'proofs'; reports.mkdir()
    started = time.time()
    report = {'status': 'RUNNING', 'commit': args.commit, 'started_unix': started,
              'anonymous_public_download': True, 'authorization_header_used': False,
              'local_source_reuse': False, 'new_model_calls': 0, 'new_database_executions': 0,
              'historical371_full_model_replay_repeated': False}
    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            receipts = list(pool.map(lambda name: fetch(args.commit, name, downloads), FILES))
        report['downloads'] = receipts
        report['download_bytes'] = sum(row['bytes'] for row in receipts)
        actual_manifest = sha(downloads/'manifest.json')
        report['manifest_sha256'] = actual_manifest
        if args.manifest_sha256 and actual_manifest != args.manifest_sha256:
            raise ValueError('Anonymous manifest differs from the separately supplied exact pin')
        manifest = json.loads((downloads/'manifest.json').read_text())
        for key, name in [('archive', 'review_evidence.tar.gz'), ('inventory', 'archive_inventory.json')]:
            digest, size = artifact_pin(manifest, key, name)
            if sha(downloads/name) != digest or (size is not None and (downloads/name).stat().st_size != size):
                raise ValueError('Anonymous downloaded ' + key + ' differs from its pinned manifest')
        layout=json.loads((downloads/'archive_inventory.json').read_text())
        expected = inventory_files(layout)
        report['archive_verification'] = extract_verified(downloads/'review_evidence.tar.gz', expected, checkout, layout)
        if args.skip_offline:
            report['status'] = 'DOWNLOAD_ONLY'
            report['offline_proof_replay_complete'] = False
        else:
            report['offline_checks'] = run_offline(checkout, reports)
            report['offline_proof_replay_complete'] = True
            report['status'] = 'PASS'
    except Exception as error:
        report['status'] = 'FAIL'
        report['error_type'] = type(error).__name__
        report['error'] = str(error)
        raise
    finally:
        report['finished_unix'] = time.time()
        report['elapsed_seconds'] = report['finished_unix'] - started
        (args.out_dir/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps({key: report.get(key) for key in ('status', 'commit', 'manifest_sha256', 'elapsed_seconds')}), flush=True)


if __name__ == '__main__':
    main()
