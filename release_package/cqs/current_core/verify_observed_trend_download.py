#!/usr/bin/env python3
"""Fetch the Core404 supplement and its byte-preserved Core402 dependency anonymously.

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
FILES = ('observed_trend_manifest.json', 'observed_trend_inventory.json', 'observed_trend.tar.gz',
         'latest_additions_manifest.json', 'latest_additions_inventory.json', 'latest_additions.tar.gz')
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


def verify_downloads(downloads, output):
    wrapper = json.loads((downloads/'observed_trend_manifest.json').read_text())
    dependency = wrapper['preserved_402_dependency']
    for name, pin in dependency['files'].items():
        if sha(downloads/name) != pin['sha256'] or (downloads/name).stat().st_size != pin['bytes']:
            raise ValueError('Preserved Core402 dependency differs: ' + name)
    for key, name in [('archive','observed_trend.tar.gz'), ('inventory','observed_trend_inventory.json')]:
        digest, size = artifact_pin(wrapper,key,name)
        if sha(downloads/name) != digest or (downloads/name).stat().st_size != size:
            raise ValueError('Core404 supplement differs: ' + name)
    prior = json.loads((downloads/'latest_additions_manifest.json').read_text())
    if prior['current_repaired_n'] != 402 or prior['pending_n'] != 158:
        raise ValueError('Dependency does not retain the Core402 scope')
    base = output/'preserved402'; base.mkdir()
    layout = json.loads((downloads/'latest_additions_inventory.json').read_text())
    old_extract = extract_verified(downloads/'latest_additions.tar.gz', inventory_files(layout), base, layout)
    old_index = base/'release_package/cqs/current_core/index_manifest.json'
    if sha(old_index) != prior['index_manifest_sha256']:
        raise ValueError('Retained Core402 index differs from its wrapper')
    reports = output/'proofs'; reports.mkdir()
    checks = []
    def run(name, arguments, checkout):
        command = [sys.executable,'-B','-S']+[str(value) for value in arguments]
        result = subprocess.run(command,cwd=checkout,capture_output=True,text=True,timeout=1200)
        proof = {'name':name,'status':'PASS' if result.returncode == 0 else 'FAIL',
                 'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
        (reports/(name+'.json')).write_text(json.dumps(proof,indent=2)+'\n')
        checks.append(proof)
        if result.returncode:
            raise ValueError('Offline check failed: ' + name)
    run('preserved402_index',[base/'release_package/cqs/current_core/verify_index.py'],base)
    overlay = output/'supplement'; overlay.mkdir()
    layout = json.loads((downloads/'observed_trend_inventory.json').read_text())
    new_extract = extract_verified(downloads/'observed_trend.tar.gz',inventory_files(layout),overlay,layout)
    permitted = {'README.md','current_tasks.jsonl','all_core_dispositions.jsonl','index_manifest.json',
                 'verify_index.py','verify_observed_trend_download.py','expert_review/manifest.json',
                 'expert_review/source_first_questions.jsonl','expert_review/blank_answer_forms.jsonl',
                 'expert_review/README.md'}
    checkout = output/'checkout'; shutil.copytree(base,checkout)
    for source in overlay.rglob('*'):
        if not source.is_file():
            continue
        relative = source.relative_to(overlay)
        name = str(relative)
        if name.startswith('release_package/cqs/current_core/'):
            if name[len('release_package/cqs/current_core/'):] not in permitted:
                raise ValueError('Supplement overwrites an undeclared historical path')
        elif not name.startswith('release_package/cqs/original_core_observed_trend_repair/'):
            raise ValueError('Supplement adds an undeclared cohort')
        target = checkout/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    cqs = checkout/'release_package/cqs'
    current = cqs/'current_core'
    index = json.loads((current/'index_manifest.json').read_text())
    if (sha(current/'index_manifest.json') != wrapper['index_manifest_sha256']
            or index['repaired_n'] != 404 or index['pending_n'] != 156
            or index['repair_classes'] != {'scorer_only':115,'query_and_scorer':289}):
        raise ValueError('Current404 scope, classes or index pin differs')
    bundle = cqs/'original_core_observed_trend_repair'
    run('observed_trend_contract',[bundle/'verify_observed_trend.py','--bundle',bundle,
                                   '--parent',cqs/'original_core_repair'],checkout)
    run('current404_index',[current/'verify_index.py'],checkout)
    kit = current/'expert_review'
    manifest = json.loads((kit/'manifest.json').read_text())
    for name,digest in manifest['files'].items():
        if sha(kit/name) != digest:
            raise ValueError('Prepared human-review input pin differs')
    read = lambda path: [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    questions, forms = read(kit/'source_first_questions.jsonl'),read(kit/'blank_answer_forms.jsonl')
    originals = {row['id']:row for row in read(cqs/'original_core_repair/provenance/original_benchmark.jsonl')}
    if (len(questions) != 560 or len(forms) != 560 or len({row['id'] for row in questions}) != 560
            or manifest['current_index_manifest_sha256'] != wrapper['index_manifest_sha256']
            or manifest['human_reviews_completed'] != 0 or manifest['expert_reviews_completed'] != 0):
        raise ValueError('Prepared review scope or completion differs')
    for question,form in zip(questions,forms):
        if (set(question) != {'id','question_en','wg'} or question['id'] != form['id']
                or question['question_en'] != form['question_en']
                or question['question_en'] != originals[question['id']]['question_en']
                or form['answer_from_source'] is not None
                or form['review_completion_status'] != 'not_started'
                or form['reference_gold_seen_before_source_answer'] is not False):
            raise ValueError('Prepared form has changed original input or an answer')
    checks.append({'name':'prepared560_human_review_inputs','status':'PASS','completed_human_or_expert_n':0})
    return {'status':'PASS','preserved402_inventory':old_extract,'supplement_inventory':new_extract,
            'offline_checks':checks,'current_repaired_n':404,'pending_n':156,
            'older_model_experiments_replayed':False,'new_model_calls':0,'new_database_executions':0,
            'completed_human_or_expert_reviews':0,
            'scope':'Preserved402 index dependencies, disjoint two-item repair, current404 index and blank560 forms. New model evidence remains separate.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit',required=True)
    parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--out-dir',required=True,type=Path)
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',args.commit) or not re.fullmatch('[0-9a-f]{64}',args.manifest_sha256):
        parser.error('Exact commit and manifest SHA256 required')
    args.out_dir.mkdir(parents=True,exist_ok=False)
    downloads = args.out_dir/'downloads'; downloads.mkdir()
    report = {'status':'RUNNING','commit':args.commit,'anonymous_public_download':True,
              'authorization_header_used':False,'local_source_reuse':False,'new_model_calls':0,
              'new_database_executions':0,'started_unix':time.time()}
    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            report['downloads'] = list(pool.map(lambda name:fetch(args.commit,name,downloads),FILES))
        actual = sha(downloads/'observed_trend_manifest.json')
        if actual != args.manifest_sha256:
            raise ValueError('Downloaded manifest differs from separately supplied exact pin')
        report['manifest_sha256'] = actual
        report.update(verify_downloads(downloads,args.out_dir))
        report['offline_proof_replay_complete'] = True
    except Exception as error:
        report.update(status='FAIL',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        report['finished_unix'] = time.time()
        (args.out_dir/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({key:report.get(key) for key in ('status','commit','manifest_sha256')}),flush=True)


if __name__ == '__main__':
    main()
