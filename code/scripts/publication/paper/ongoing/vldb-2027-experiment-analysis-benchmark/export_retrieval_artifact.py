#!/usr/bin/env python3
"""Export text-free retrieval frontiers and restore indexes from checked text.

The original SQLite files are opened read-only and immutable. Frontiers contain
schema, identifiers, metadata, text digests and locators; source text stays in
the user's local corpus. A restored database preserves logical rows and FTS
configuration, rather than the original SQLite page layout.
"""
from __future__ import annotations

import argparse
import ast
import collections
import contextlib
from concurrent.futures import ThreadPoolExecutor
import difflib
import functools
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
import types
import unicodedata
from urllib.parse import quote
from urllib.parse import urlparse
import urllib.request
import zlib
import zipfile
from xml.etree import ElementTree as ET


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 << 20), b''):
            h.update(block)
    return h.hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def recipe_rows(path):
    """Read one gzip JSONL or a digest-bounded manifest of gzip parts."""
    path=Path(path)
    shared={}
    if path.suffix=='.gz':parts=[{'path':path.name}]
    else:
        manifest=json.loads(path.read_text());parts=manifest['parts'];shared=manifest.get('shared_code_sha256',{})
    for part in parts:
        current=contained(path.parent,part['path'])
        if part.get('sha256') and digest(current)!=part['sha256']:raise ValueError('Recipe part SHA differs')
        count=0
        with gzip.open(current,'rt')as handle:
            for line in handle:
                count+=1;row=json.loads(line)
                if shared and 'code_sha256'not in row:row['code_sha256']=shared
                yield row
        if part.get('rows') is not None and count!=part['rows']:raise ValueError('Recipe part row count differs')


def split_recipes(args):
    """Write deterministic recipe shards and a checked part manifest."""
    args.output.mkdir(parents=True,exist_ok=True);parts=[];stream=None;raw=None;count=0;total=0;shared=None
    def close_part():
        nonlocal stream,raw,count
        if stream is None:return
        stream.close();raw.close();path=args.output/parts[-1]['path']
        parts[-1].update(rows=count,bytes=path.stat().st_size,sha256=digest(path))
        if path.stat().st_size>=100*1024*1024:raise ValueError('Part exceeds GitHub file limit; reduce --rows-per-part')
        stream=None;raw=None;count=0
    try:
        for row in recipe_rows(args.input):
            if 'code_sha256'in row:
                if shared is None:shared=row['code_sha256']
                if row['code_sha256']!=shared:raise ValueError('Code pins vary across recipe frontier')
                row={k:v for k,v in row.items()if k!='code_sha256'}
            if stream is None:
                path=args.output/f'part-{len(parts):04d}.jsonl.gz';raw=path.open('xb')
                stream=gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6);parts.append({'path':path.name})
            stream.write(encoded(row)+b'\n');count+=1;total+=1
            if count==args.rows_per_part:close_part()
        close_part()
    finally:
        if stream is not None:stream.close();raw.close()
    result={'format':'spectra-sharded-recipes-v1','rows':total,'input_sha256':digest(args.input),'parts':parts,
            'shared_code_sha256':shared or {},
            'full_text_included':False}
    (args.output/'manifest.json').write_bytes(encoded(result)+b'\n');print(json.dumps(result))


def runtime():
    return {'executable': sys.executable, 'python': sys.version, 'sqlite': sqlite3.sqlite_version}


def readonly(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError(f'Missing input database: {path}')
    if any(Path(str(path) + suffix).exists() for suffix in ('-wal', '-journal')):
        raise ValueError('Input has a journal/WAL; provide a closed, stable snapshot')
    con = sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)
    con.execute('PRAGMA query_only=ON')
    return con


def ident(name):
    return '"' + name.replace('"', '""') + '"'


def contained(root, relative):
    root = Path(root).resolve()
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError('Locator escapes supplied root')
    return candidate


@functools.lru_cache(maxsize=24)
def read_json(path):
    return json.loads(Path(path).read_text())


@functools.lru_cache(maxsize=5)
def load_offline_phase6(repository, wg):
    """Load parser functions with the service-resolver class removed explicitly.

    The parser's class-level credential lookup is irrelevant to document parsing.
    This adapter removes only MetadataResolver from its AST before execution;
    parsing/chunking functions retain the checked source code. No credentials,
    Neo4j driver or metadata query is needed by this adapter.
    """
    path = repository / f'scripts/tsg/RAN/formal/{wg}/phase-6/tdoc-parser/parse_tdoc_lib.py'
    tree = ast.parse(path.read_text(), filename=str(path))
    removed = [n.name for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'MetadataResolver']
    if removed != ['MetadataResolver']:
        raise ValueError('Expected exactly one service MetadataResolver class')
    tree.body = [n for n in tree.body if not (isinstance(n, ast.ClassDef) and n.name == 'MetadataResolver')]
    for node in tree.body:
        if isinstance(node,ast.FunctionDef)and node.name=='parse_documents':
            node.body=[part for part in node.body if not(
                isinstance(part,ast.ImportFrom)and part.module=='tdoc_body_source_metadata')and not(
                isinstance(part,ast.Expr)and isinstance(part.value,ast.Call)and
                isinstance(part.value.func,ast.Name)and part.value.func.id=='validate_source_selection')]
    name = 'spectra_offline_phase6_' + wg
    module = types.ModuleType(name); module.__file__ = str(path); sys.modules[name] = module
    os.environ['HF_HUB_OFFLINE'] = '1'; os.environ['TRANSFORMERS_OFFLINE'] = '1'
    exec(compile(tree, str(path), 'exec'), module.__dict__)
    return module


@functools.lru_cache(maxsize=5)
def load_rechunk(repository, wg):
    path = repository / f'scripts/tsg/RAN/formal/{wg}/phase-6/tdoc-parser/07_rechunk_all.py'
    spec = importlib.util.spec_from_file_location('spectra_offline_rechunk_' + wg, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def phase6_code_files(repository, wg):
    files = [f'scripts/tsg/RAN/formal/{wg}/phase-6/tdoc-parser/{n}'
             for n in ('parse_tdoc_lib.py', '07_rechunk_all.py')]
    files += [f'scripts/common/common/{n}' for n in
              ('chunker.py', 'embedding_registry.py', 'script_markup.py', 'atomic_io.py', 'tdoc_number.py')]
    files += [str(p.relative_to(repository)) for p in sorted(
        (repository / 'scripts/tsg/RAN/formal/common').glob('*.py'))]
    return {s: digest(repository / s) for s in files}


def native_conversion_record(chain, magic=None):
    record = {'source_status': 'native_doc_conversion_recipe', 'member_chain': chain,
              'conversion': {'native_sha256': chain[-1]['sha256'],
                             'libreoffice_version': 'LibreOffice 7.3.7.2 30(Build:2)'}}
    if magic: record['conversion']['native_magic_prefix'] = magic
    return record


def zip_member_chain(archive_path, wanted_sha, max_depth=10):
    """Locate a checked DOCX byte sequence inside ZIP-only nested archives."""
    def walk(handle, chain, depth):
        with zipfile.ZipFile(handle) as archive:
            nested = []
            for member in archive.infolist():
                if member.is_dir(): continue
                try:
                    with archive.open(member) as f:
                        h = hashlib.sha256()
                        for block in iter(lambda: f.read(1 << 20), b''): h.update(block)
                    if h.hexdigest() == wanted_sha:
                        return chain + [{'name': member.filename, 'sha256': h.hexdigest(), 'bytes': member.file_size}]
                    if Path(member.filename).suffix.lower() == '.zip': nested.append((member, h.hexdigest()))
                except (OSError, RuntimeError, zipfile.BadZipFile):
                    continue
            if depth < max_depth:
                for member, sha in nested:
                    try:
                        # Nested ZIP metadata is bounded by the recorded local source size.
                        result = walk(io.BytesIO(archive.read(member)), chain + [
                            {'name': member.filename, 'sha256': sha, 'bytes': member.file_size}], depth + 1)
                        if result: return result
                    except (OSError, RuntimeError, zipfile.BadZipFile): pass
        return None
    return walk(archive_path, [], 0)


def read_zip_member(handle, name):
    """Use ZIP stdlib or the pinned local 7z executable for Deflate64."""
    try:
        with zipfile.ZipFile(handle) as archive: return archive.read(name)
    except (NotImplementedError, zipfile.BadZipFile):
        with tempfile.TemporaryDirectory(prefix='spectra-deflate64-') as temp:
            path = Path(handle) if isinstance(handle, (str, Path)) else Path(temp) / 'nested.zip'
            if not isinstance(handle, (str, Path)): path.write_bytes(handle.getvalue())
            proc = subprocess.run(['7z', 'x', '-so', '-y', '-spd', str(path), name],
                                  capture_output=True, stdin=subprocess.DEVNULL, timeout=180)
            if proc.returncode:
                # Ubuntu's p7zip build omits the RAR decoder; libarchive-c uses
                # the installed native libarchive decoder without a service.
                import libarchive
                with libarchive.file_reader(str(path)) as archive:
                    for member in archive:
                        if member.pathname == name:
                            return b''.join(member.get_blocks())
                raise ValueError('Archive member unavailable: ' + name)
            return proc.stdout


def zip_leaf_members(archive_path, max_depth=10):
    def walk(handle, chain, depth):
        try:
            with zipfile.ZipFile(handle) as archive:
                names = [m.filename for m in archive.infolist() if not m.is_dir()]
        except zipfile.BadZipFile:
            with tempfile.TemporaryDirectory(prefix='spectra-archive-list-') as temp:
                path = Path(handle) if isinstance(handle, (str, Path)) else Path(temp) / 'nested.archive'
                if not isinstance(handle, (str, Path)): path.write_bytes(handle.getvalue())
                proc = subprocess.run(['7z', 'l', '-slt', str(path)], check=True, capture_output=True, text=True)
                entries = proc.stdout.split('----------\n', 1)[-1].strip().split('\n\n')
                names = []
                for entry in entries:
                    fields = dict(line.split(' = ', 1) for line in entry.splitlines() if ' = ' in line)
                    if fields.get('Path') and fields.get('Folder') != '+' and not fields.get('Attributes', '').startswith('D'):
                        names.append(fields['Path'])
        leaves = []
        for name in names:
            content = read_zip_member(handle, name)
            member = {'name': name, 'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content)}
            if Path(name).suffix.lower() in ('.zip', '.rar', '.7z') and depth < max_depth:
                leaves += walk(io.BytesIO(content), chain + [member], depth + 1)
            else:
                leaves.append((chain + [member], content[:8].hex()))
        return leaves
    return walk(archive_path, [], 0)


def source_recipe(path, repository, by_path):
    """Resolve a derived file to an actual source file and checked member chain."""
    relative = str(path.relative_to(repository)); expected = digest(path)
    item = {'path': relative, 'sha256': expected, 'source_status': 'archive_unresolved'}
    native_path = Path(relative.replace('/derived/', '/source/', 1))
    candidates = [native_path]
    tdoc = re.search(r'(R[1-5]-\d+)', native_path.name, re.I)
    if tdoc: candidates.append(native_path.parent / (tdoc.group(1) + '.zip'))
    for parent in native_path.parents:
        if '/source/' not in str(parent): break
        candidates += [parent.with_suffix(parent.suffix + '.zip')]
    archive = None
    for candidate in candidates:
        archive = by_path.get(str(candidate))
        if archive is None:
            archive = by_path.get(str(candidate).lower())
        if archive: break
    if not archive: return item
    item.update(archive_sha256=archive['archive_sha256'], archive_paths=archive['paths'],
                official_urls=archive['official_urls'])
    actual_path = contained(repository, archive['paths'][0])
    if str(native_path).lower() in {p.lower() for p in archive['paths']}:
        native_sha = archive['archive_sha256']
        item.update(member_chain=[], direct_source_file=True)
        if native_sha == expected: item['source_status'] = 'exact_source_file'
        else:
            item.update(source_status='native_doc_conversion_recipe', conversion={
                'native_sha256': native_sha, 'native_name': actual_path.name,
                'libreoffice_version': 'LibreOffice 7.3.7.2 30(Build:2)'})
        return item
    try:
        leaves = zip_leaf_members(actual_path)
        matches = [(chain, magic) for chain, magic in leaves if chain[-1]['sha256'] == expected]
        documents = [(chain, magic) for chain, magic in leaves
                     if Path(chain[-1]['name']).suffix.lower() in ('.doc', '.docx', '.docm', '.rtf')
                     and '__MACOSX' not in Path(chain[-1]['name']).parts and not Path(chain[-1]['name']).name.startswith('._')]
        if matches: item.update(source_status='exact_archive_member', member_chain=matches[0][0])
        elif len(documents) == 1: item.update(native_conversion_record(*documents[0]))
        else:
            names = {path.name.lower(), path.stem.lower() + '.doc', path.stem.lower() + '.rtf', path.stem.lower()}
            named = [(chain, magic) for chain, magic in documents if Path(chain[-1]['name']).name.lower() in names]
            if len(named) == 1: item.update(native_conversion_record(*named[0]))
            else:
                def name_key(name):
                    value=Path(name).name
                    try:value=value.encode('cp437').decode('utf8')
                    except (UnicodeError,ValueError):pass
                    value=value.replace('¿C','–')
                    while Path(value).suffix.lower()in('.doc','.docx','.docm','.rtf'):value=Path(value).stem
                    return ''.join(c.lower()for c in unicodedata.normalize('NFKC',value)if c.isalnum())
                named=[(chain,magic)for chain,magic in documents if name_key(chain[-1]['name'])==name_key(path.name)]
                if len(named)==1:
                    item.update(native_conversion_record(*named[0]));item['source_name_rule']='unique normalized native basename; final chunk SHA required'
                else:item.update(source_status='conversion_or_source_version_requires_recipe', document_candidates=[c for c,m in documents])
    except Exception as error:
        item.update(source_status='conversion_or_source_version_requires_recipe', mapping_error=type(error).__name__+': '+str(error))
    return item


def merge_url_supplements(inventory, by_path):
    by_sha={row['archive_sha256']:row for row in by_path.values()}
    prefix=inventory.name.split('_sources',1)[0]
    for path in sorted(inventory.parent.glob(prefix+'*url_supplement.jsonl.gz')):
        with gzip.open(path,'rt')as handle:
            for line in handle:
                row=json.loads(line)
                if row['archive_sha256']in by_sha:
                    found=by_sha[row['archive_sha256']]
                    found['official_urls']=sorted(set(found['official_urls'])|set(row['official_urls']))


def repair_tdoc_recipes(args):
    """Resolve every previously recorded mapping gap and preserve all rows."""
    repository = args.repository.resolve(); by_path = {}; statuses = collections.Counter(); started = time.monotonic()
    with gzip.open(args.source_inventory, 'rt') as handle:
        for line in handle:
            row = json.loads(line)
            for path in row['paths']: by_path[path] = row; by_path[path.lower()] = row
    merge_url_supplements(args.source_inventory,by_path)
    if args.url_inventory:
        by_sha = {row['archive_sha256']:row for row in by_path.values()}
        with gzip.open(args.url_inventory, 'rt') as handle:
            for line in handle:
                row=json.loads(line)
                if row['sha256'] in by_sha:
                    found=by_sha[row['sha256']];found['official_urls']=sorted(set(found['official_urls'])|set(row['candidateUrls']))
    if args.output.exists(): raise ValueError('Output exists')
    gaps = [];supplements={}
    with gzip.open(args.input, 'rt') as inp, args.output.open('xb') as raw, gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as out:
        for line in inp:
            row=json.loads(line)
            wg=row['wg']
            if wg not in supplements:
                path=repository/f'ontology/input/tsg/RAN/formal/meetings/{wg}/tdoc_source_supplements.json'
                supplements[wg]={r['target']:r for r in json.loads(path.read_text()).get('records',[])}if path.exists()else{}
            if not row['sources'] and row['tdoc'] in supplements[wg]:
                native=supplements[wg][row['tdoc']];source=source_recipe(contained(repository,native['path']),repository,by_path)
                if Path(native['path']).suffix.lower() in ('.xlsx','.xls','.pptx'):
                    row['native_supplement']={'source_type':native['sourceIdentity']['type'],'source_suffix':Path(native['path']).suffix.lower()}
                    if native.get('nativeView') and source.get('member_chain'):
                        view=native['nativeView'];source.update(path=view['path'],sha256=view['sha256'],
                            source_status='native_doc_conversion_recipe',conversion={'native_sha256':source['member_chain'][-1]['sha256'],
                            'libreoffice_version':view['conversionLineage']['version'],'output_format':'xlsx'})
                row['sources']=[source];row['parser_pipeline']='source_supplement'
            if row['raw_source_status'] != 'all_sources_with_executable_recipe':
                row['sources']=[source_recipe(contained(repository,s['path']),repository,by_path)
                                if s['source_status'] not in ('exact_archive_member','native_doc_conversion_recipe','exact_source_file') else s for s in row['sources']]
                row['raw_source_status']='all_sources_with_executable_recipe' if row['sources'] and all(
                    s['source_status'] in ('exact_archive_member','native_doc_conversion_recipe','exact_source_file') for s in row['sources']) else 'additional_recipe_required'
            statuses[row['raw_source_status']]+=1
            for source in row['sources']: statuses[source['source_status']]+=1
            if row['raw_source_status']!='all_sources_with_executable_recipe': gaps.append(row)
            out.write(encoded(row)+b'\n')
    report={'counts':dict(statuses),'sha256':digest(args.output),'bytes':args.output.stat().st_size,'runtime':runtime(),
            'seconds':time.monotonic()-started,'scope':'Source identity and executable mapping; parser execution receipts are separate.'}
    args.report.write_bytes(encoded(report)+b'\n')
    args.report.with_suffix('.gaps.json').write_bytes(encoded(gaps)+b'\n');print(json.dumps(report))


def prepare_tdoc_recipes(args):
    """Pin the entire indexed TDOC source frontier for a WG, including gaps."""
    repository = args.repository.resolve()
    module = load_offline_phase6(repository, args.wg)
    sources, by_path = {}, {}
    with gzip.open(args.source_inventory, 'rt') as handle:
        for line in handle:
            row = json.loads(line); sources[row['archive_sha256']] = row
            for path in row['paths']: by_path[path] = row
    if args.url_inventory:
        with gzip.open(args.url_inventory, 'rt') as handle:
            for line in handle:
                row = json.loads(line)
                if row['sha256'] in sources:
                    found = sources[row['sha256']]
                    found['official_urls'] = sorted(set(found['official_urls']) | set(row['candidateUrls']))
    con = readonly(args.database)
    targets = con.execute("SELECT DISTINCT tdoc,json_extract(meta,'$.meetingId') FROM docs "
                          "WHERE collection LIKE '%_tdoc_chunks' ORDER BY tdoc").fetchall()
    con.close()
    code = phase6_code_files(repository, args.wg)
    stats, started = collections.Counter(), time.monotonic()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists(): raise ValueError('Recipe output exists')
    with args.output.open('xb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=6) as gz:
        for tdoc, meeting in targets:
            relative = f'vectordb/parsed/tdocs/{args.wg}/{meeting}/{tdoc}/chunks.json'
            parsed = read_json(str(contained(repository, relative)))
            base = repository / f'data/corpus/tsg/RAN/formal/meetings/{args.wg}/derived'
            meeting_folder = module.meeting_id_to_folder(meeting, args.wg, base_dir=base)
            folder = module.tdoc_dir_for(base / meeting_folder / 'Docs', tdoc)
            selected = module.tdoc_documents(folder) if folder else []
            # Per-view reviewed source overrides are frozen explicitly, if present.
            projection = parsed.get('metadata', {}).get('bodySourceMetadata', {}).get('cover', {})
            override = projection.get('evidence', {}).get('path')
            if override: selected = [contained(repository, override)]
            record = {'format': 'spectra-offline-tdoc-recipe-v1', 'wg': args.wg, 'tdoc': tdoc,
                      'meetingId': meeting, 'parsed_path': relative, 'metadata': parsed.get('metadata', {}),
                      'code_sha256': code, 'sources': [],
                      'expected_chunks': [{'chunkId': c['chunkId'], 'content_sha256': hashlib.sha256(c['content'].encode()).hexdigest()}
                                          for c in parsed['chunks']]}
            for path in selected:
                rel = str(path.relative_to(repository)); sha = digest(path)
                archive_relative = str(folder.relative_to(repository)).replace('/derived/', '/source/', 1) + '.zip'
                archive = by_path.get(archive_relative)
                item = {'path': rel, 'sha256': sha, 'source_status': 'archive_unresolved'}
                if archive:
                    item.update(archive_sha256=archive['archive_sha256'], archive_paths=archive['paths'],
                                official_urls=archive['official_urls'])
                    direct = [m for m in archive['members'] if m.get('sha256') == sha]
                    chain = [{'name': direct[0]['path'], 'sha256': sha, 'bytes': direct[0]['bytes']}] if direct else None
                    if not chain and any(m.get('nested_archive') for m in archive['members']):
                        chain = zip_member_chain(contained(repository, archive['paths'][0]), sha)
                    if chain:
                        item.update(source_status='exact_archive_member', member_chain=chain)
                    else:
                        names = {path.name.lower(), path.stem.lower() + '.doc', path.stem.lower()}
                        candidates = [m for m in archive['members'] if Path(m['path']).name.lower() in names]
                        item.update(source_status='conversion_or_source_version_requires_recipe', native_member_candidates=candidates)
                        natives = [m for m in candidates if Path(m['path']).suffix.lower() in ('.doc', '.rtf') and 'sha256' in m]
                        if len(natives) == 1:
                            m = natives[0]
                            item.update(native_conversion_record([{'name': m['path'], 'sha256': m['sha256'], 'bytes': m['bytes']}]))
                        else:
                            try:
                                leaves = zip_leaf_members(contained(repository, archive['paths'][0]))
                                matches = [(c, h) for c, h in leaves if c[-1]['sha256'] == sha]
                                documents = [(c, h) for c, h in leaves if Path(c[-1]['name']).suffix.lower() in ('.doc', '.docx', '.docm', '.rtf')]
                                if matches:
                                    item.update(source_status='exact_archive_member', member_chain=matches[0][0])
                                elif len(documents) == 1:
                                    item.update(native_conversion_record(*documents[0]))
                            except (OSError, RuntimeError, zipfile.BadZipFile) as error:
                                item['mapping_error'] = type(error).__name__
                record['sources'].append(item); stats[item['source_status']] += 1
            if not selected: stats['selected_source_missing'] += 1
            statuses = {s['source_status'] for s in record['sources']}
            record['raw_source_status'] = 'all_sources_with_executable_recipe' if selected and statuses <= {
                'exact_archive_member', 'native_doc_conversion_recipe'} else 'additional_recipe_required'
            stats[record['raw_source_status']] += 1; stats['tdocs'] += 1
            gz.write(encoded(record) + b'\n')
            if stats['tdocs'] % 5000 == 0: print(json.dumps(dict(stats)), flush=True)
    report = {'wg': args.wg, 'counts': dict(stats), 'compressed_bytes': args.output.stat().st_size,
              'sha256': digest(args.output), 'code_sha256': code, 'seconds': time.monotonic()-started,
              'scope': 'Complete indexed TDOC input selection, archive/member identities and expected chunk hashes; parser execution reported separately.',
              'full_text_included': False, 'full_raw_reconstruction_claimed': False}
    args.report.write_bytes(encoded(report) + b'\n'); print(json.dumps(report))


def reparse_tdoc(args):
    """Reparse hash-pinned DOCX sources using frozen metadata, without services."""
    recipe = json.loads(args.recipe.read_text())
    repository = args.repository.resolve()
    for relative, expected in recipe['code_sha256'].items():
        if digest(contained(repository, relative)) != expected:
            raise ValueError('Pinned parser code differs: ' + relative)
    sources = []
    for source in recipe['sources']:
        path = contained(args.source_root, source['path'])
        if not source.get('conversion') and digest(path) != source['sha256']:
            raise ValueError('Pinned DOCX differs: ' + source['path'])
        if source.get('conversion'):
            conversion_receipt = path.with_name(path.name + '.conversion.json')
            proof = json.loads(conversion_receipt.read_text())
            if proof['output_sha256'] != digest(path) or proof['native_sha256'] != source['conversion']['native_sha256']:
                raise ValueError('DOC conversion receipt differs')
            if source['conversion'].get('retain_native_sidecar'):
                if digest(path.with_suffix('.doc')) != source['conversion']['native_sha256']:
                    raise ValueError('Native field-recovery sidecar differs')
        sources.append(path)
    module, rechunk = load_offline_phase6(repository, recipe['wg']), load_rechunk(repository, recipe['wg'])
    # Source ordering is frozen in the recipe. The single-document pilot uses
    # TdocParser directly; multi-source production needs its bundle contract.
    if recipe.get('native_supplement'):
        from tdoc_document_supplements import _native_blocks
        from common.chunker import enforce_hard_max
        blocks=_native_blocks(str(sources[0].resolve()),digest(sources[0]))
        if sources[0].suffix.lower()=='.pptx':
            from pptx_search_text import search_blocks
            blocks=search_blocks(sources[0])
        groups={}
        for index,(locator,body)in enumerate(blocks.items()):
            group=locator.rsplit(' cell ',1)[0]if locator.startswith('workbook sheet ')else locator
            groups.setdefault(group,[]).append((index,locator,body))
        sections=[]
        for title,units in groups.items():
            text='\n'.join(f'[{locator}] {body}'for _,locator,body in units if body.strip())
            if text:sections.append(module.Section(title=title,level=1,content=text,start_idx=units[0][0],end_idx=units[-1][0]+1))
        content=module.ParsedContent(tdoc_number=recipe['tdoc'],doc_type=recipe['native_supplement']['source_type'],sections=sections,paragraph_count=len(blocks))
    elif len(sources) == 1:
        content = module.TdocParser(sources[0], recipe['tdoc']).parse()
    else:
        content = module.parse_documents(sources, recipe['tdoc'])
    chunks = module.ChunkEngine().chunk_sections(content.sections, recipe['tdoc'])
    if recipe.get('native_supplement')or recipe.get('parser_pipeline')=='source_supplement':
        from common.chunker import enforce_hard_max
        chunks=enforce_hard_max(chunks,hard_max=6500)
    else:
        chunks = module._enforce_hard_max(chunks, hard_max=module._HARD_MAX_TOK)
        chunks = rechunk.add_chunk_ids(rechunk.merge_small_chunks(rechunk.split_oversized_chunks(chunks)), recipe['tdoc'])
    raw_actual = [{'chunkId': c['chunkId'], 'content_sha256': hashlib.sha256(c['content'].encode()).hexdigest()}
              for c in chunks]
    projection = recipe.get('snapshot_projection')
    if projection:
        if projection.get('format') != 'same-document-parser-character-ranges-and-whitespace-v1':
            raise ValueError('Unknown TDOC snapshot projection format')
        if raw_actual != projection['raw_parser_chunks']:
            raise ValueError('TDOC snapshot projection raw parser digest sequence differs')
        raw_text = tuple(c['content'] for c in chunks)
        seen = set()
        for bridge in projection['bridges']:
            index = bridge['target_chunk_index']
            if not isinstance(index, int) or not 0 <= index < len(chunks) or index in seen:
                raise ValueError('TDOC snapshot projection target index differs')
            seen.add(index)
            if chunks[index]['chunkId'] != bridge['target_chunk_id']:
                raise ValueError('TDOC snapshot projection target ID differs')
            pieces = []
            for segment in bridge['segments']:
                if 'whitespace' in segment:
                    value = segment['whitespace']
                    if not isinstance(value, str) or value.strip():
                        raise ValueError('TDOC projection literal must contain whitespace only')
                else:
                    pointer = segment['pointer']
                    if (len(pointer) != 3 or pointer[0] != 'chunks' or pointer[2] != 'content'
                            or not isinstance(pointer[1], int) or not 0 <= pointer[1] < len(raw_text)):
                        raise ValueError('TDOC projection source pointer differs')
                    start, end = segment['start'], segment['end']
                    source_text = raw_text[pointer[1]]
                    if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start <= end <= len(source_text):
                        raise ValueError('TDOC projection source bounds differ')
                    value = source_text[start:end]
                pieces.append(value)
            value = ''.join(pieces)
            if hashlib.sha256(value.encode()).hexdigest() != bridge['target_content_sha256']:
                raise ValueError('TDOC snapshot projection target SHA differs')
            chunks[index] = dict(chunks[index], content=value)
    actual = [{'chunkId': c['chunkId'], 'content_sha256': hashlib.sha256(c['content'].encode()).hexdigest()}
              for c in chunks]
    matched = actual == recipe['expected_chunks']
    report = {'tdoc': recipe['tdoc'], 'wg': recipe['wg'], 'source_count': len(sources),
              'expected_chunks': len(recipe['expected_chunks']), 'actual_chunks': len(chunks),
              'all_chunk_ids_and_content_sha256_matched': matched,
              'metadata_mode': 'Frozen metadata and ordered source hashes from recipe; MetadataResolver excluded and external source-selection manifest check replaced by these hash gates explicitly.',
              'recipe_sha256': digest(args.recipe), 'actual_chunk_digests': actual,
              'raw_parser_chunk_digests': raw_actual,
              'snapshot_projection': {'applied': bool(projection), 'bridged_chunks': len(projection['bridges']) if projection else 0},
              'runtime': runtime(),
              'scope': 'Raw DOCX to current parsed text; frozen snapshot bridge is a separate checked stage.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes(encoded(report) + b'\n')
    if not matched:
        raise ValueError('Raw-source parser output differs from frozen expected chunk digest sequence')
    if args.output:
        payload = encoded({'tdocNumber': recipe['tdoc'], 'meetingId': recipe['meetingId'],
                           'type': content.doc_type, 'paragraphCount': content.paragraph_count,
                           'metadata': recipe['metadata'], 'chunks': chunks}) + b'\n'
        if args.output.exists() and args.output.read_bytes() != payload:
            raise ValueError('Existing parsed output differs from verified replay')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if not args.output.exists(): args.output.write_bytes(payload)
    print(json.dumps({k: v for k, v in report.items() if k != 'actual_chunk_digests'}))


def acquire_tdoc(args):
    """Acquire official archives, verify all hashes, then select pinned members."""
    recipe = json.loads(args.recipe.read_text()); args.cache.mkdir(parents=True, exist_ok=True)
    receipt, started = [], time.monotonic()
    for source in recipe['sources']:
        archive = args.cache / (source['archive_sha256'] + '.zip')
        downloaded, used_url = False, None
        if not archive.exists() and getattr(args, 'local_archive_repository', None):
            for relative in source.get('archive_paths', []):
                candidate = contained(args.local_archive_repository, relative)
                if candidate.is_file() and digest(candidate) == source['archive_sha256']:
                    archive = candidate; break
        if not archive.exists():
            if not args.download: raise ValueError('Archive not cached; --download enables official retrieval')
            errors = []
            for url in source['official_urls']:
                parsed = urlparse(url)
                if parsed.scheme != 'https' or parsed.hostname not in ('www.3gpp.org', '3gpp.org'):
                    errors.append({'url': url, 'reason': 'Expected official HTTPS 3GPP host'}); continue
                partial = archive.with_suffix('.download.partial')
                try:
                    request = urllib.request.Request(url, headers={'User-Agent': 'SPECTRA-source-check/1.0'})
                    with urllib.request.urlopen(request, timeout=args.timeout) as response, partial.open('xb') as out:
                        for block in iter(lambda: response.read(1 << 20), b''): out.write(block)
                    if digest(partial) != source['archive_sha256']: raise ValueError('Downloaded archive SHA differs')
                    partial.rename(archive); downloaded, used_url = True, url; break
                except Exception as error:
                    partial.unlink(missing_ok=True); errors.append({'url': url, 'reason': type(error).__name__ + ': ' + str(error)})
            if not archive.exists(): raise ValueError('Official archive unavailable: ' + json.dumps(errors))
        if digest(archive) != source['archive_sha256']: raise ValueError('Cached archive SHA differs')
        chain = source.get('member_chain')
        if not chain and not source.get('direct_source_file'):
            if 'member' not in source: raise ValueError('Source requires an explicit conversion or nested-member recipe')
            chain = [{'name': source['member'], 'sha256': source['sha256']}]
        if source.get('direct_source_file'): content = archive.read_bytes(); chain = []
        handle = archive
        for member in chain:
            content = read_zip_member(handle, member['name'])
            if hashlib.sha256(content).hexdigest() != member['sha256']: raise ValueError('Archive member SHA differs')
            handle = io.BytesIO(content)
        target = contained(args.output, source['path']); target.parent.mkdir(parents=True, exist_ok=True)
        if source.get('conversion'):
            conversion = source['conversion']
            if hashlib.sha256(content).hexdigest() != conversion['native_sha256']:
                raise ValueError('Native conversion source differs')
            if conversion.get('retain_native_sidecar'):
                native_sidecar = target.with_suffix('.doc')
                if native_sidecar.exists() and digest(native_sidecar) != conversion['native_sha256']:
                    raise ValueError('Native field-recovery sidecar already differs')
                if not native_sidecar.exists(): native_sidecar.write_bytes(content)
            version = subprocess.run(['libreoffice', '--version'], check=True, capture_output=True, text=True).stdout.strip()
            if version != conversion['libreoffice_version']: raise ValueError('LibreOffice version differs')
            proof = {}
            if target.exists():
                proof = json.loads(target.with_name(target.name + '.conversion.json').read_text())
                if (proof.get('native_sha256') != conversion['native_sha256']
                        or proof.get('output_sha256') != digest(target)
                        or proof.get('libreoffice_version') != version):
                    raise ValueError('Existing converted source proof differs')
            else:
                with tempfile.TemporaryDirectory(prefix='spectra-offline-doc-', dir=args.cache) as temp:
                    work = Path(temp).resolve(); native = work / Path(chain[-1]['name'] if chain else conversion['native_name']).name; native.write_bytes(content)
                    if conversion.get('method') == 'native_accepted_uno_export_reopen':
                        repository = getattr(args, 'repository', None) or Path(__file__).resolve().parents[5]
                        relative = 'scripts/tsg/RAN/formal/common/native_word_conversion.py'
                        if digest(contained(repository, relative)) != recipe['code_sha256'][relative]:
                            raise ValueError('Native accepted converter code differs')
                        sys.path.insert(0, str(contained(repository, 'scripts/tsg/RAN/formal/common')))
                        import native_word_conversion
                        proof = native_word_conversion.recover_native_word(native, target)
                    else:
                        output = work / 'converted'; output.mkdir()
                        profile = (work / 'profile').as_uri()
                        output_format=conversion.get('output_format','docx')
                        proc = subprocess.run(['libreoffice', '-env:UserInstallation=' + profile, '--headless',
                                               '--convert-to', output_format, '--outdir', str(output), str(native)],
                                              capture_output=True, text=True, timeout=180)
                        converted = output / (native.stem + '.'+output_format)
                        if proc.returncode or not converted.exists(): raise ValueError('Native DOC conversion failed: ' + proc.stdout + proc.stderr)
                        target.write_bytes(converted.read_bytes())
            if conversion.get('method') == 'native_accepted_uno_export_reopen':
                if proof.get('acceptedRenderedText', {}).get('normalizedTextSha256') != conversion['accepted_rendered_normalized_sha256']:
                    raise ValueError('Native accepted rendered text digest differs')
            proof.update({'native_sha256': conversion['native_sha256'], 'output_sha256': digest(target),
                     'libreoffice_version': version, 'snapshot_docx_container_sha_equal': digest(target) == source['sha256'],
                     'validation': 'Converted container digest recorded; parsed chunk digests checked by reparse-tdoc.'})
            target.with_name(target.name + '.conversion.json').write_bytes(encoded(proof) + b'\n')
        else:
            if hashlib.sha256(content).hexdigest() != source['sha256']: raise ValueError('Selected DOCX SHA differs')
            if target.exists() and digest(target) != source['sha256']: raise ValueError('Output source already differs')
            if not target.exists(): target.write_bytes(content)
        receipt.append({'source': source['path'], 'archive_sha256': source['archive_sha256'],
                        'member_sha256': chain[-1]['sha256'] if chain else source['archive_sha256'], 'selected_docx_sha256': digest(target),
                        'expected_snapshot_docx_sha256': source['sha256'],
                        'downloaded': downloaded, 'used_url': used_url,
                        'member_chain': chain})
    report = {'recipe_sha256': digest(args.recipe), 'sources': receipt, 'all_archive_and_member_sha256_matched': True,
              'seconds': time.monotonic()-started, 'network_download_enabled': args.download, 'runtime': runtime()}
    args.report.parent.mkdir(parents=True, exist_ok=True); args.report.write_bytes(encoded(report) + b'\n')
    print(json.dumps(report))


def reparse_tdoc_batch(args):
    """Execute a fixed recipe list, preserving every outcome including failures."""
    names = sorted(args.recipes.glob('*.json'))
    args.output.mkdir(parents=True, exist_ok=True)
    outcomes, started = [], time.monotonic()
    for recipe_path in names:
        recipe = json.loads(recipe_path.read_text()); folder = args.output / recipe['tdoc']
        folder.mkdir(exist_ok=True)
        row = {'tdoc': recipe['tdoc'], 'recipe_sha256': digest(recipe_path), 'status': 'started'}
        begin = time.monotonic()
        try:
            acquisition = argparse.Namespace(recipe=recipe_path, cache=args.cache, output=folder/'sources',
                report=folder/'acquire_receipt.json', download=args.download, timeout=args.timeout,
                local_archive_repository=args.local_archive_repository)
            parsing = argparse.Namespace(repository=args.repository, recipe=recipe_path, source_root=folder/'sources',
                output=folder/'parsed/chunks.json', report=folder/'reparse_receipt.json')
            with contextlib.redirect_stdout(io.StringIO()):
                acquire_tdoc(acquisition); reparse_tdoc(parsing)
            row['status'] = 'all_expected_chunks_exact'
        except Exception as error:
            row.update(status='error', error_type=type(error).__name__, error=str(error))
        row['seconds'] = time.monotonic()-begin; outcomes.append(row)
        args.report.write_bytes(encoded({'outcomes': outcomes, 'complete': False, 'runtime': runtime()}) + b'\n')
        print(json.dumps(row), flush=True)
    report = {'outcomes': outcomes, 'complete': True, 'runtime': runtime(), 'seconds': time.monotonic()-started,
              'counts': dict(collections.Counter(r['status'] for r in outcomes)),
              'scope': 'Exact fixed recipe executions; broader corpus execution requires its own receipts.'}
    args.report.write_bytes(encoded(report) + b'\n'); print(json.dumps({k:v for k,v in report.items()if k!='outcomes'}))


def accepted_source_blocks(path, repository, reader='accepted_body'):
    """Canonical accepted block projection used by decision_disposition.py.

    This reproduces its _parse_source_blocks/AcceptedBlockTexts read rule,
    with no ontology or database imports and no output writes.
    """
    sys.path.insert(0, str(repository / 'scripts/tsg/RAN/formal/common'))
    sys.path.insert(0, str(repository / 'scripts/common'))
    import docx_text
    if reader == 'phase2_box_body':
        from docx import Document
        import decision_boxes
        import decision_marks
        document = Document(path)
        eq_image = docx_text.equation_images(path)
        marked = lambda block: docx_text.marked_text(block, is_equation_image=eq_image)
        rendered = []
        for index, block in enumerate(docx_text.iter_blocks(document._body._element)):
            if block.tag != '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl':
                rendered.append(marked(block)); continue
            candidates = []
            for mark, line, children in decision_boxes.table_marks(
                    block, document._body, companies=frozenset(), meeting=path.stem.removeprefix('Final_Report_')):
                box = decision_boxes.BoxMark(index, None, mark, line, children)
                head = decision_marks.mark_head(mark, marked(line))
                following = box.following(marked, lambda table: '\n'.join(docx_text.table_line_rows(table, para=marked)))
                candidates.append((head + ('\n' + following if following.strip() else '')) if head else following)
            rendered.append('\n'.join(candidates))
        return rendered
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    with zipfile.ZipFile(path) as archive:
        tree = ET.fromstring(docx_text.zip_part(archive, 'word/document.xml'))
    body = tree.find(w + 'body')
    if body is None: raise ValueError('DOCX has no body')
    blocks = list(docx_text.iter_blocks(body))
    if reader == 'accepted_body':
        para = docx_text.final_text
    elif reader == 'phase2_marked_body':
        eq_image = docx_text.equation_images(path)
        para = lambda block: docx_text.marked_text(block, is_equation_image=eq_image)
    else:
        raise ValueError('Unknown source block reader: ' + reader)
    return ['\n'.join(docx_text.table_line_rows(b, para=para))
            if b.tag == w + 'tbl' else para(b) for b in blocks]


def prepare_resolution_recipes(args):
    """Map indexed Resolution content to hash-pinned native source block spans."""
    repository = args.repository.resolve()
    con = readonly(args.database)
    wanted = {r[0].rsplit('#', 1)[0] for r in con.execute(
        "SELECT DISTINCT chunk_id FROM docs WHERE collection LIKE '%_resolution_chunks'")}; con.close()
    reports, spans = {}, {}
    folder = repository / f'ontology/output/tsg/RAN/formal/parsed_reports/{args.wg}'
    for path in sorted(folder.glob(args.wg + '*.json')):
        report = json.loads(path.read_text()); reports[report['meeting_id']] = report['docx_path']
        for group in ('agreements', 'conclusions', 'working_assumptions'):
            for row in report.get(group, []):
                if row.get('body_blocks'):
                    spans[row['decision_id']] = (report['docx_path'], row['body_blocks'])
    phase2 = repository / f'ontology/output/tsg/RAN/formal/instances/phase-2/{args.wg}'
    dispositions = phase2 / 'decision_dispositions.jsonld'
    if dispositions.exists():
        for row in json.loads(dispositions.read_text()).get('@graph', []):
            rid = row.get('dispositionOf', '').split('/')[-1]
            if rid not in wanted: continue
            assessment = json.loads(row.get('assessmentMethod') or '{}')
            block_range = assessment.get('decisionBodyBlocks')
            if block_range and row.get('evidencePath'): spans[rid] = (row['evidencePath'], block_range)
    groups, statuses = collections.defaultdict(list), collections.Counter()
    for path in sorted(phase2.glob('resolutions_*.jsonld')):
        for index, node in enumerate(json.loads(path.read_text()).get('@graph', [])):
            rid = node.get('resolutionId')
            if rid not in wanted: continue
            if rid in spans: source, span = spans[rid]
            else:
                meeting = node.get('madeAt', '').split('/')[-1].replace(args.wg + '_', args.wg + '#', 1)
                source, span = reports.get(meeting), None
            groups[source].append((str(path.relative_to(repository)), index, node, span))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists(): raise ValueError('Resolution recipe output exists')
    source_digests, started = {}, time.monotonic()
    with args.output.open('xb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=6) as gz:
        for source, records in sorted(groups.items(), key=lambda x: str(x[0])):
            texts, marked_texts, box_texts, sha = None, None, None, None
            if source:
                source_path = contained(repository, source)
                sha = digest(source_path); source_digests[source] = sha
                texts = accepted_source_blocks(source_path, repository)
            for path, index, node, span in records:
                content = node['content']
                record = {'resolution_id': node['resolutionId'], 'target_path': path, 'target_index': index,
                          'node_metadata': {k:v for k,v in node.items() if k not in ('content','note','contentWithEquations')},
                          'content_sha256': hashlib.sha256(content.encode()).hexdigest(), 'content_chars': len(content),
                          'source_docx_path': source, 'source_docx_sha256': sha,
                          'reader': 'accepted_body'}
                if texts is None:
                    record['status'] = 'source_report_unresolved'
                else:
                    bounds = span or [0, len(texts)]
                    joined = '\n'.join(texts[bounds[0]:bounds[1]])
                    at = joined.find(content)
                    if at >= 0:
                        record.update(status='exact_raw_body_span', body_blocks=bounds,
                                      segments=[{'start':at,'end':at+len(content)}])
                    else:
                        bridge = ParsedLocators.resolution_bridge(content, source, ['joined_body_range'], joined)
                        if bridge:
                            record.update(status='exact_raw_body_bridge', body_blocks=bounds, segments=bridge['segments'])
                        else:
                            if marked_texts is None:
                                marked_texts = accepted_source_blocks(source_path, repository, 'phase2_marked_body')
                            joined = '\n'.join(marked_texts[bounds[0]:bounds[1]])
                            at = joined.find(content)
                            bridge = ParsedLocators.resolution_bridge(content, source, ['joined_body_range'], joined)
                            if at >= 0:
                                record.update(status='exact_raw_body_span', body_blocks=bounds,
                                              reader='phase2_marked_body', segments=[{'start':at,'end':at+len(content)}])
                            elif bridge:
                                record.update(status='exact_raw_body_bridge', body_blocks=bounds,
                                              reader='phase2_marked_body', segments=bridge['segments'])
                            else:
                                if box_texts is None:
                                    box_texts = accepted_source_blocks(source_path, repository, 'phase2_box_body')
                                joined = '\n'.join(box_texts[bounds[0]:bounds[1]])
                                at = joined.find(content)
                                if at >= 0:
                                    record.update(status='exact_raw_body_span', body_blocks=bounds,
                                                  reader='phase2_box_body', segments=[{'start':at,'end':at+len(content)}])
                                else: record.update(status='raw_body_text_differs', body_blocks=bounds)
                statuses[record['status']] += 1; gz.write(encoded(record) + b'\n')
            print(json.dumps({'report': source, 'records': len(records), 'statuses': dict(statuses)}), flush=True)
    report = {'wg': args.wg, 'indexed_resolution_ids': len(wanted), 'statuses': dict(statuses),
              'source_docx_sha256': source_digests, 'bytes':args.output.stat().st_size, 'sha256':digest(args.output),
              'runtime':runtime(), 'seconds':time.monotonic()-started,
              'scope':'Hash-pinned DOCX accepted block span maps; official acquisition recipes and fresh executions are separate stages.',
              'full_text_included':False}
    args.report.write_bytes(encoded(report)+b'\n'); print(json.dumps({k:v for k,v in report.items()if k!='source_docx_sha256'}))


def document_xml_sha(path):
    with zipfile.ZipFile(path) as archive:
        return hashlib.sha256(archive.read('word/document.xml')).hexdigest()


def prepare_report_sources(args):
    """Connect report inputs to official source identities by bytes or XML bytes."""
    repository=args.repository.resolve(); by_path={}; by_sha={}; by_xml=collections.defaultdict(list)
    with gzip.open(args.source_inventory,'rt')as handle:
        for line in handle:
            row=json.loads(line)
            for path in row['paths']: by_path[path]=row;by_path[path.lower()]=row
    merge_url_supplements(args.source_inventory,by_path)
    if args.tdoc_recipes:
        with gzip.open(args.tdoc_recipes,'rt')as handle:
            for line in handle:
                for source in json.loads(line)['sources']:
                    if source['source_status'] in ('exact_archive_member','native_doc_conversion_recipe','exact_source_file'):
                        by_sha[source['sha256']]=source
    reports=json.loads(args.resolution_receipt.read_text())['source_docx_sha256']; missing=[]; result=[]
    for path,sha in reports.items():
        if sha in by_sha:
            source=dict(by_sha[sha]);source['path']=path
            result.append({'source_docx_path':path,'equivalence':'container_sha256','sources':[source]})
        else: missing.append(path)
    wanted={document_xml_sha(contained(repository,path)):path for path in missing}
    folder=repository/f'data/corpus/tsg/RAN/formal/meetings/{args.wg}/derived'
    for path in folder.rglob('*'):
        if path.suffix.lower()!='.docx':continue
        name=str(path.relative_to(folder)).lower()
        if not any(word in name for word in ('report','minutes','meeting')):continue
        try: xml=document_xml_sha(path)
        except (OSError,KeyError,zipfile.BadZipFile):continue
        if xml in wanted:by_xml[xml].append(path)
    for path in missing:
        original=contained(repository,path);xml=document_xml_sha(original);chosen=None;attempts=[]
        for candidate in by_xml[xml]:
            source=source_recipe(candidate,repository,by_path);attempts.append({'path':str(candidate.relative_to(repository)),'status':source['source_status']})
            if source['source_status'] in ('exact_archive_member','native_doc_conversion_recipe','exact_source_file'):
                source['snapshot_derived_path']=source['path'];source['path']=path;chosen=source;break
        result.append({'source_docx_path':path,'equivalence':'word_document_xml_sha256','word_document_xml_sha256':xml,
                       'sources':[chosen] if chosen else [],'mapping_attempts':attempts})
    result.sort(key=lambda row:row['source_docx_path'])
    payload={'wg':args.wg,'reports':result,'scope':'Archive/member identity plus container or word/document.xml equivalence; final resolution content hashes gate replay.'}
    args.output.write_bytes(encoded(payload)+b'\n')
    report={'wg':args.wg,'reports':len(reports),'mapped_reports':sum(bool(r['sources'])for r in result),
            'equivalence_counts':dict(collections.Counter(r['equivalence']for r in result if r['sources'])),
            'sha256':digest(args.output),'bytes':args.output.stat().st_size,'runtime':runtime()}
    args.report.write_bytes(encoded(report)+b'\n');print(json.dumps(report))


def restore_resolutions(args):
    """Restore only indexed graph nodes from acquired native report body spans."""
    repository=args.repository.resolve();graphs=collections.defaultdict(dict);outcomes=[];cached={};failures=[]
    manifest=json.loads(args.sources.read_text());sources={r['source_docx_path']:r['sources'][0]for r in manifest['reports']if r['sources']}
    verified=set();code_verified=False
    for row in recipe_rows(args.recipes):
            source=contained(args.source_root,row['source_docx_path'])
            if not code_verified:
                if not row.get('code_sha256'):raise ValueError('Resolution replay requires a recipe manifest with shared code pins')
                for path,expected in row['code_sha256'].items():
                    if digest(contained(repository,path))!=expected:raise ValueError('Pinned reader code differs: '+path)
                code_verified=True
            if row['source_docx_path']not in verified:
                identity=sources[row['source_docx_path']]
                if identity.get('conversion'):
                    proof=json.loads(source.with_name(source.name+'.conversion.json').read_text())
                    if proof['output_sha256']!=digest(source)or proof['native_sha256']!=identity['conversion']['native_sha256']:
                        raise ValueError('Materialized report conversion differs')
                elif digest(source)!=identity['sha256']:raise ValueError('Materialized report source SHA differs')
                verified.add(row['source_docx_path'])
            key=(str(source),row.get('reader','accepted_body'))
            if key not in cached:
                if len(cached)>=4:cached.clear()
                cached[key]=accepted_source_blocks(source,repository,key[1])
            blocks=cached[key];a,b=row['body_blocks'];joined='\n'.join(blocks[a:b])
            segments=row.get('segments',[])
            for segment in segments:
                if 'whitespace' in segment and segment['whitespace'].strip():raise ValueError('Non-whitespace literal prohibited')
            content=''.join(s['whitespace']if'whitespace'in s else joined[s['start']:s['end']]for s in segments)
            actual=hashlib.sha256(content.encode()).hexdigest();matched=actual==row['content_sha256']
            if not matched:failures.append({'resolution_id':row['resolution_id'],'actual_sha256':actual,'expected_sha256':row['content_sha256']})
            else:graphs[row['target_path']][row['target_index']]=dict(row['node_metadata'],content=content)
            outcomes.append(matched)
    report={'rows':len(outcomes),'matched':sum(outcomes),'all_content_sha256_matched':all(outcomes),'failures':failures,
            'recipe_sha256':digest(args.recipes),'source_manifest_sha256':digest(args.sources),
            'verified_source_files':len(verified),'reader_code_pins_verified':code_verified,'runtime':runtime(),
            'scope':'Exact indexed content and selected nontext node metadata restored at original graph indexes; unused graph positions are empty metadata objects.'}
    args.report.write_bytes(encoded(report)+b'\n')
    if failures:raise ValueError('Resolution content SHA differs')
    for relative,nodes in graphs.items():
        target=contained(args.output,relative)
        if target.exists():raise ValueError('Output graph exists')
        graph=[{}for _ in range(max(nodes)+1)]
        for index,node in nodes.items():graph[index]=node
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(encoded({'@graph':graph})+b'\n')
    print(json.dumps(report))


def acquire_reports(args):
    """Acquire a complete fixed report list, preserving each measured outcome."""
    manifest=json.loads(args.sources.read_text());outcomes=[];args.output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='spectra-report-recipes-')as temp:
        for index,row in enumerate(manifest['reports']):
            result={'source_docx_path':row['source_docx_path'],'status':'started'}
            recipe=Path(temp)/f'{index}.json';receipt=Path(temp)/f'{index}.receipt.json'
            try:
                if not row['sources']:raise ValueError('Report source unmapped')
                recipe.write_bytes(encoded({'sources':row['sources']}))
                acquire_tdoc(argparse.Namespace(recipe=recipe,cache=args.cache,output=args.output,report=receipt,
                    download=args.download,timeout=args.timeout,local_archive_repository=args.local_archive_repository))
                result.update(status='acquired_and_hash_verified',receipt=json.loads(receipt.read_text()))
            except Exception as error:result.update(status='error',error_type=type(error).__name__,error=str(error))
            outcomes.append(result);args.report.write_bytes(encoded({'complete':False,'outcomes':outcomes,'runtime':runtime()})+b'\n')
    result={'complete':True,'outcomes':outcomes,'counts':dict(collections.Counter(r['status']for r in outcomes)),
            'source_manifest_sha256':digest(args.sources),'runtime':runtime()}
    args.report.write_bytes(encoded(result)+b'\n');print(json.dumps({k:v for k,v in result.items()if k!='outcomes'}))
    if any(r['status']=='error'for r in outcomes):raise ValueError('One or more report acquisitions failed')


def restore_tdocs(args):
    """Acquire and parse an ordered recipe frontier using frozen metadata."""
    args.output.mkdir(parents=True,exist_ok=True);counts=collections.Counter();started=time.monotonic();processed=0
    args.report.parent.mkdir(parents=True,exist_ok=True)
    outcome_path=args.report.with_suffix('.outcomes.jsonl')
    if args.report.exists():raise ValueError('Replay report exists; choose a new report path for the next checked run')
    with outcome_path.open('xb')as outcomes, tempfile.TemporaryDirectory(prefix='spectra-tdoc-recipes-')as temp:
        recipe_path=Path(temp)/'recipe.json';acq=Path(temp)/'acquire.json';parsed=Path(temp)/'parse.json'
        for index,recipe in enumerate(recipe_rows(args.recipes)):
            if index<args.start:continue
            if args.stop is not None and index>=args.stop:break
            row={'index':index,'tdoc':recipe['tdoc'],'status':'started'}
            try:
                if recipe['raw_source_status']!='all_sources_with_executable_recipe':raise ValueError('Recipe has unresolved sources')
                recipe_path.write_bytes(encoded(recipe))
                acquire_tdoc(argparse.Namespace(recipe=recipe_path,cache=args.cache,output=args.source_root,report=acq,
                    download=args.download,timeout=args.timeout,local_archive_repository=args.local_archive_repository,
                    repository=args.repository))
                target=contained(args.output,recipe['parsed_path'])
                reparse_tdoc(argparse.Namespace(repository=args.repository,recipe=recipe_path,source_root=args.source_root,
                    output=target,report=parsed))
                row.update(status='all_expected_chunks_exact',chunks=len(recipe['expected_chunks']),
                           acquisition=json.loads(acq.read_text()),parse=json.loads(parsed.read_text()))
            except Exception as error:row.update(status='error',error_type=type(error).__name__,error=str(error))
            outcomes.write(encoded(row)+b'\n');outcomes.flush();counts[row['status']]+=1;processed+=1
            args.report.write_bytes(encoded({'complete':False,'counts':dict(counts),'processed':processed,
                'outcomes_path':outcome_path.name,'runtime':runtime()})+b'\n')
            if processed%100==0:print(json.dumps({'processed':processed,'counts':dict(counts)}),flush=True)
    result={'complete':True,'recipe_frontier_sha256':digest(args.recipes),'range':[args.start,args.stop],
            'counts':dict(counts),'processed':processed,'outcomes_path':outcome_path.name,
            'outcomes_sha256':digest(outcome_path),
            'runtime':runtime(),'seconds':time.monotonic()-started}
    args.report.write_bytes(encoded(result)+b'\n');print(json.dumps(result))
    if counts['error']:raise ValueError('One or more TDOC replays failed')


class ParsedLocators:
    """Locators into existing parsed inputs; never claims fresh raw-source parsing."""
    def __init__(self, repository, wg):
        self.root, self.wg = Path(repository).resolve(), wg
        self.cr = {}
        self.resolutions = {}
        base = f'vectordb/parsed/cr/{wg}/{wg.lower()}_cr_chunks.json'
        p = self.root / base
        if p.exists():
            for i, row in enumerate(read_json(str(p)).get('chunks', [])):
                self.cr[row.get('chunkId')] = (base, ['chunks', i, 'text'], row.get('text', ''))
        folder = self.root / f'ontology/output/tsg/RAN/formal/instances/phase-2/{wg}'
        for p in sorted(folder.glob('resolutions_*.jsonld')):
            for i, row in enumerate(read_json(str(p)).get('@graph', [])):
                rid = row.get('resolutionId')
                if rid:
                    value = (str(p.relative_to(self.root)), ['@graph', i, 'content'], row.get('content', ''))
                    if rid in self.resolutions and self.resolutions[rid][2] != value[2]:
                        raise ValueError(f'Conflicting parsed Resolution: {rid}')
                    self.resolutions[rid] = value

    def locate(self, row):
        cid, collection, text = row['chunk_id'], row['collection'], row['text']
        candidate, adjacent = None, None
        if collection.endswith('_cr_chunks'):
            candidate = self.cr.get(cid)
        elif collection.endswith('_resolution_chunks'):
            candidate = self.resolutions.get((cid or '').rsplit('#', 1)[0])
        elif collection.endswith('_tdoc_chunks'):
            meta = json.loads(row['meta'])
            meeting, tdoc = meta.get('meetingId'), row['tdoc']
            if meeting and tdoc:
                relative = f'vectordb/parsed/tdocs/{self.wg}/{meeting}/{tdoc}/chunks.json'
                p = contained(self.root, relative)
                if p.exists():
                    data = read_json(str(p))
                    for i, chunk in enumerate(data.get('chunks', [])):
                        if chunk.get('chunkId') == cid:
                            candidate = (relative, ['chunks', i, 'content'], chunk.get('content', ''))
                            adjacent = (relative, data['chunks'], i)
                            break
        if not candidate:
            return {'status': 'parsed_input_missing'}
        relative, pointer, original = candidate
        offset = original.find(text) if isinstance(original, str) else -1
        if offset < 0:
            if adjacent:
                bridge = self.bridge(text, *adjacent)
                if bridge:
                    return bridge
            if collection.endswith('_resolution_chunks'):
                bridge = self.resolution_bridge(text, relative, pointer, original)
                if bridge:
                    return bridge
            return {'status': 'parsed_text_differs', 'path': relative, 'pointer': pointer}
        return {'status': 'exact_parsed_slice', 'path': relative, 'pointer': pointer,
                'start': offset, 'end': offset + len(text)}

    @staticmethod
    def resolution_bridge(text, relative, pointer, original):
        """Preserve chunk-prefix/overlap drift using ranges of the same record.

        Unmatched paragraphs must occur verbatim in that resolution. Only
        leading/trailing whitespace may be represented as a literal.
        """
        segments, consumed = [], 0
        for block in difflib.SequenceMatcher(None, text, original, autojunk=False).get_matching_blocks():
            gap = text[consumed:block.a]
            for line in gap.splitlines(keepends=True):
                core = line.strip()
                if not core:
                    segments.append({'whitespace': line}); continue
                at = original.find(core)
                if at < 0: return None
                prefix = len(line) - len(line.lstrip())
                if prefix: segments.append({'whitespace': line[:prefix]})
                segments.append({'pointer': pointer, 'start': at, 'end': at + len(core)})
                suffix = line[prefix + len(core):]
                if suffix: segments.append({'whitespace': suffix})
            if block.size: segments.append({'pointer': pointer, 'start': block.b, 'end': block.b + block.size})
            consumed = block.a + block.size
        result = ''.join(s['whitespace'] if 'whitespace' in s else original[s['start']:s['end']] for s in segments)
        if result != text: return None
        return {'status': 'exact_parsed_bridge', 'path': relative, 'segments': segments,
                'recipe': 'same-resolution-character-ranges-and-whitespace-v1'}

    @staticmethod
    def bridge(text, relative, chunks, center):
        """Record measured version drift using this chunk and its two neighbors.

        Exact source character ranges are retained; only whitespace may be a
        literal. An unmatched contiguous fragment may use an exact occurrence
        elsewhere in this same document. Other gaps keep the row unresolved.
        This is a fixed snapshot bridge, not a claim about the original parser.
        """
        strings, locations, cursor = [], [], 0
        for index in range(max(0, center - 1), min(len(chunks), center + 2)):
            if strings:
                strings.append('\n')
                locations.append((cursor, cursor + 1, None))
                cursor += 1
            part = chunks[index].get('content', '')
            strings.append(part)
            locations.append((cursor, cursor + len(part), index))
            cursor += len(part)
        joined = ''.join(strings)
        segments, consumed = [], 0
        for block in difflib.SequenceMatcher(None, text, joined, autojunk=False).get_matching_blocks():
            gap = text[consumed:block.a]
            if gap and not gap.isspace():
                matches = [(abs(i-center), i, c.get('content', '').find(gap)) for i, c in enumerate(chunks)
                           if gap in c.get('content', '')]
                if not matches:
                    return None
                _, index, offset = min(matches)
                segments.append({'pointer': ['chunks', index, 'content'], 'start': offset, 'end': offset + len(gap)})
            elif gap:
                segments.append({'whitespace': gap})
            begin, end = block.b, block.b + block.size
            for left, right, index in locations:
                a, b = max(begin, left), min(end, right)
                if a >= b:
                    continue
                if index is None:
                    segments.append({'whitespace': joined[a:b]})
                else:
                    segments.append({'pointer': ['chunks', index, 'content'], 'start': a-left, 'end': b-left})
            consumed = block.a + block.size
        reconstructed = ''.join(s['whitespace'] if 'whitespace' in s else
                                chunks[s['pointer'][1]]['content'][s['start']:s['end']] for s in segments)
        if reconstructed != text:
            return None
        return {'status': 'exact_parsed_bridge', 'path': relative, 'segments': segments,
                'recipe': 'same-document-current-chunks-character-ranges-and-whitespace-v1'}


def official_urls(paths, ftp_dirs=None):
    urls = set()
    for path in paths:
        match = re.search(r'/meetings/(TSG_RAN|RAN[1-5])/source/([^/]+)/(Docs|Reports?)/(.+)$', path)
        if match:
            group, meeting, kind, name = match.groups()
            remote = 'TSG_RAN' if group == 'TSG_RAN' else (ftp_dirs or {}).get(group)
            if not remote:
                continue
            urls.add('https://www.3gpp.org/ftp/tsg_ran/' + remote + '/' +
                     quote(meeting, safe='') + '/' + kind + '/' + quote(name, safe=''))
    return sorted(urls)


def export(args):
    source, out = args.database.resolve(), args.output.resolve()
    if out.exists():
        raise ValueError('Output already exists')
    out.mkdir(parents=True)
    before = source.stat()
    con = readonly(source)
    schema = con.execute("SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY rowid").fetchall()
    kind = 'wg' if any(r[1] == 'docs' for r in schema) else 'plenary'
    tables = ['docs', 'cr_clause', 'manifest', 'build_info'] if kind == 'wg' else [
        'inodes', 'files', 'owners', 'members', 'member_owner', 'chunks', 'build_info']
    locators = ParsedLocators(args.repository, source.stem.upper()) if args.repository and kind == 'wg' else None
    counts, statuses, table_hashes = {}, collections.Counter(), {}
    start = time.monotonic()
    schema_record = {'format': 'spectra-retrieval-frontier-v1', 'kind': kind,
                     'sqlite_version': sqlite3.sqlite_version, 'source_bytes': before.st_size,
                     'schema': schema, 'tables': tables,
                     'scope': 'Text-free logical snapshot frontier; original texts must be acquired or locally regenerated.'}
    if args.hash_database:
        schema_record['source_sha256'] = digest(source)
    (out / 'schema.json').write_bytes(encoded(schema_record) + b'\n')
    for table in tables:
        columns = [r[1] for r in con.execute('PRAGMA table_info(' + ident(table) + ')')]
        order = 'collection,chunk_id,id' if table == 'docs' else 'rowid'
        h = hashlib.sha256()
        count = 0
        p = out / (table + '.jsonl.gz')
        with p.open('xb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=6) as gz:
            for values in con.execute('SELECT * FROM ' + ident(table) + ' ORDER BY ' + order):
                row = dict(zip(columns, values))
                if 'text' in row:
                    data = row['text'].encode('utf-8')
                    record = {k: v for k, v in row.items() if k != 'text'}
                    record.update(text_sha256=hashlib.sha256(data).hexdigest(), text_bytes=len(data), text_chars=len(row['text']))
                    if locators:
                        record['text_locator'] = locators.locate(row)
                        statuses[record['text_locator']['status']] += 1
                else:
                    record = row
                if table == 'files':
                    record['official_urls'] = official_urls(json.loads(row['paths']))
                    statuses['official_url_present' if record['official_urls'] else 'official_url_unresolved'] += 1
                payload = encoded(record) + b'\n'
                h.update(payload)
                gz.write(payload)
                count += 1
        counts[table], table_hashes[table] = count, h.hexdigest()
        print(json.dumps({'table': table, 'rows': count, 'compressed_bytes': p.stat().st_size}), flush=True)
    con.close()
    after = source.stat()
    unchanged = (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino)
    if not unchanged:
        raise ValueError('Original database changed during export')
    receipt = {'kind': kind, 'rows': counts, 'locator_statuses': dict(statuses), 'table_stream_sha256': table_hashes,
               'files': {p.name: {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(out.iterdir())},
               'source_unchanged_stat': unchanged, 'seconds': time.monotonic() - start,
               'full_text_included': False, 'fresh_raw_source_reconstruction_claimed': False}
    (out / 'receipt.json').write_bytes(encoded(receipt) + b'\n')
    print(json.dumps(receipt), flush=True)


def rows(bundle, table):
    receipt = json.loads((bundle / 'receipt.json').read_text()) if (bundle / 'receipt.json').exists() else {}
    names = receipt.get('table_parts', {}).get(table, [table + '.jsonl.gz'])
    for name in names:
        with gzip.open(contained(bundle, name), 'rt', encoding='utf-8') as handle:
            for line in handle:
                yield json.loads(line)


def split_table(args):
    """Split metadata JSONL into deterministic gzip transport parts."""
    schema, receipt = verify_bundle(args.bundle)
    if args.table in receipt.get('table_parts', {}):
        raise ValueError('Table is already split')
    names, raw, gz, count = [], None, None, 0
    try:
        for row in rows(args.bundle, args.table):
            if count % args.rows_per_part == 0:
                if gz: gz.close(); raw.close()
                name = f'{args.table}.part{len(names):04d}.jsonl.gz'; names.append(name)
                raw = (args.bundle / name).open('xb')
                gz = gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=6)
            gz.write(encoded(row) + b'\n'); count += 1
    finally:
        if gz: gz.close(); raw.close()
    if count != receipt['rows'][args.table]: raise ValueError('Split row count differs')
    if any((args.bundle / name).stat().st_size >= 100 * (1 << 20) for name in names):
        raise ValueError('A transport part reaches GitHub 100 MiB limit')
    receipt.setdefault('table_parts', {})[args.table] = names
    del receipt['files'][args.table + '.jsonl.gz']
    for name in names:
        p = args.bundle / name
        receipt['files'][name] = {'bytes': p.stat().st_size, 'sha256': digest(p)}
    (args.bundle / 'receipt.json').write_bytes(encoded(receipt) + b'\n')
    print(json.dumps({'table': args.table, 'rows': count, 'parts': {n: receipt['files'][n]['bytes'] for n in names},
                      'publication_selection': 'receipt.files plus receipt.json; unsplit local table retained separately'}))


def refresh_locators(args):
    """Recheck only unresolved rows against the immutable original snapshot."""
    schema, receipt = verify_bundle(args.bundle)
    if schema['kind'] != 'wg' or digest(args.database) != schema['source_sha256']:
        raise ValueError('Original WG snapshot digest differs')
    con = readonly(args.database)
    con.row_factory = sqlite3.Row
    locators = ParsedLocators(args.repository, args.database.stem.upper())
    target = args.bundle / 'docs.jsonl.gz'
    partial = target.with_suffix('.refresh.partial')
    statuses, changed, stream = collections.Counter(), [], hashlib.sha256()
    with partial.open('xb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=6) as gz:
        for record in rows(args.bundle, 'docs'):
            old = record['text_locator']['status']
            if old not in ('exact_parsed_slice', 'exact_parsed_bridge'):
                source = con.execute('SELECT * FROM docs WHERE id=?', (record['id'],)).fetchone()
                if hashlib.sha256(source['text'].encode()).hexdigest() != record['text_sha256']:
                    raise ValueError('Snapshot row text differs')
                record['text_locator'] = locators.locate(source)
                changed.append({'id': record['id'], 'chunk_id': record['chunk_id'], 'before': old,
                                'after': record['text_locator']['status']})
            statuses[record['text_locator']['status']] += 1
            payload = encoded(record) + b'\n'
            stream.update(payload); gz.write(payload)
    con.close()
    saved = args.bundle / 'docs.initial.jsonl.gz'
    if not saved.exists(): target.rename(saved)
    partial.replace(target)
    initial_receipt = args.bundle / 'receipt.initial.json'
    if not initial_receipt.exists(): initial_receipt.write_bytes((args.bundle / 'receipt.json').read_bytes())
    receipt['locator_statuses'] = dict(statuses)
    receipt['table_stream_sha256']['docs'] = stream.hexdigest()
    receipt['files'][target.name] = {'bytes': target.stat().st_size, 'sha256': digest(target)}
    receipt['bridge_code_sha256'] = digest(Path(__file__))
    (args.bundle / 'receipt.json').write_bytes(encoded(receipt) + b'\n')
    args.report.write_bytes(encoded({'changed': changed, 'statuses': dict(statuses)}) + b'\n')
    print(json.dumps({'changed_rows': len(changed), 'statuses': dict(statuses)}))


def verify_bundle(bundle):
    receipt = json.loads((bundle / 'receipt.json').read_text())
    for name, expected in receipt['files'].items():
        p = contained(bundle, name)
        if p.stat().st_size != expected['bytes'] or digest(p) != expected['sha256']:
            raise ValueError('Bundle checksum mismatch: ' + name)
    return json.loads((bundle / 'schema.json').read_text()), receipt


def prepare_output(path, schema):
    if path.exists():
        raise ValueError('Output database already exists')
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute('PRAGMA journal_mode=OFF')
    con.execute('PRAGMA synchronous=OFF')
    con.execute('PRAGMA cache_size=-65536')
    for typ, name, sql in schema['schema']:
        if typ == 'table' and name in schema['tables']:
            con.execute(sql)
    return con


def insert(con, table, row):
    columns = [r[1] for r in con.execute('PRAGMA table_info(' + ident(table) + ')')]
    con.execute('INSERT INTO ' + ident(table) + ' VALUES (' + ','.join('?' for _ in columns) + ')',
                [row.get(k) for k in columns])


def finish(con, schema):
    for typ, name, sql in schema['schema']:
        if typ == 'table' and name == 'search':
            con.execute(sql)
    con.execute("INSERT INTO search(search) VALUES ('rebuild')")
    con.execute("INSERT INTO search(search) VALUES ('optimize')")
    for typ, name, sql in schema['schema']:
        if typ == 'index':
            con.execute(sql)
    con.commit()
    status = con.execute('PRAGMA quick_check').fetchall()
    if status != [('ok',)]:
        raise ValueError('Restored SQLite quick_check failed')
    con.close()


def restore_wg(args):
    schema, receipt = verify_bundle(args.bundle)
    if schema['kind'] != 'wg':
        raise ValueError('Expected a WG frontier')
    if args.output.exists():
        raise ValueError('Output database already exists')
    partial = args.output.with_suffix(args.output.suffix + '.partial')
    con = prepare_output(partial, schema)
    count, unmatched, table_hashes = 0, [], {}
    try:
        for record in rows(args.bundle, 'docs'):
            locator = record.get('text_locator', {})
            if locator.get('status') not in ('exact_parsed_slice', 'exact_parsed_bridge'):
                unmatched.append(record['id'])
                continue
            data = read_json(str(contained(args.repository, locator['path'])))
            segments = locator.get('segments', [locator])
            parts = []
            for segment in segments:
                if 'whitespace' in segment:
                    if segment['whitespace'] and not segment['whitespace'].isspace():
                        raise ValueError('Bridge literal contains source text')
                    parts.append(segment['whitespace'])
                else:
                    value = data
                    for token in segment['pointer']:
                        value = value[token]
                    parts.append(value[segment['start']:segment['end']])
            text = ''.join(parts)
            if hashlib.sha256(text.encode()).hexdigest() != record['text_sha256']:
                raise ValueError(f"Regenerated text differs at docs.id={record['id']}")
            record['text'] = text
            insert(con, 'docs', record)
            count += 1
            if count % 10000 == 0:
                con.commit()
        if unmatched:
            raise ValueError(f'{len(unmatched)} rows have unresolved parsed locators; refusing incomplete restoration')
        for table in ('cr_clause', 'manifest', 'build_info'):
            for row in rows(args.bundle, table):
                insert(con, table, row)
        finish(con, schema)
        if args.output.exists():
            raise ValueError('Output appeared during restoration')
        partial.rename(args.output)
        report = {'restored_docs': count, 'all_text_sha256_matched': True,
                  'runtime': runtime(),
                  'sqlite_version': sqlite3.sqlite_version, 'source_sqlite_version': schema['sqlite_version'],
                  'output_bytes': args.output.stat().st_size,
                  'scope': 'Exact logical text rows from existing parsed inputs; no fresh raw-source parsing claim.'}
        args.report.write_bytes(encoded(report) + b'\n')
        print(json.dumps(report))
    except BaseException:
        con.close()
        partial.unlink(missing_ok=True)
        raise


def compress_probe(args):
    """Measure actual complete-stream gzip size without retaining source text."""
    before = args.database.stat()
    compressor = zlib.compressobj(args.level, zlib.DEFLATED, 31)
    compressed = original = 0
    h = hashlib.sha256()
    started = time.monotonic()
    with args.database.open('rb') as handle:
        for block in iter(lambda: handle.read(4 << 20), b''):
            h.update(block)
            original += len(block)
            compressed += len(compressor.compress(block))
    compressed += len(compressor.flush())
    after = args.database.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Input changed during compression probe')
    report = {'source_bytes': original, 'source_sha256': h.hexdigest(), 'gzip_level': args.level,
              'actual_complete_gzip_bytes': compressed, 'seconds': time.monotonic() - started,
              'compressed_text_retained': False, 'source_unchanged_stat': True}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes(encoded(report) + b'\n')
    print(json.dumps(report))


def source_inventory(args):
    """Pin complete local source trees without exporting their document text."""
    repository = args.repository.resolve()
    sys.path.insert(0, str(repository / 'scripts/common'))
    from common import axis
    ftp_dirs = {wg: axis.ftp_dir(wg) for wg in axis.TSG_REGISTRY['RAN']['wgs']}
    url_by_name = collections.defaultdict(set)
    for row in rows(args.plenary_bundle, 'files'):
        for name in json.loads(row['names']):
            url_by_name[name].update(row['official_urls'])
    paths_by_inode = collections.defaultdict(list)
    for prefix in ('meetings', 'change-requests'):
        base = repository / f'data/corpus/tsg/RAN/formal/{prefix}/{args.wg}/source'
        for folder, dirs, files in os.walk(base):
            dirs.sort()
            for name in sorted(files):
                p = Path(folder) / name
                st = p.stat()
                paths_by_inode[(st.st_dev, st.st_ino)].append(str(p.relative_to(repository)))
    groups = sorted(paths_by_inode.values(), key=lambda a: min(a))

    def inspect(paths):
        p = contained(repository, paths[0])
        before = p.stat()
        urls = set(official_urls(paths, ftp_dirs))
        for relative in paths:
            urls.update(url_by_name[Path(relative).name])
        entry = {'paths': sorted(paths), 'archive_bytes': before.st_size, 'archive_sha256': digest(p),
                 'official_urls': sorted(urls), 'members': []}
        if zipfile.is_zipfile(p):
            with zipfile.ZipFile(p) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    h = hashlib.sha256()
                    try:
                        with archive.open(member) as f:
                            for block in iter(lambda: f.read(1 << 20), b''):
                                h.update(block)
                        entry['members'].append({'path': member.filename, 'bytes': member.file_size,
                                                 'sha256': h.hexdigest(), 'crc32': member.CRC,
                                                 'nested_archive': Path(member.filename).suffix.lower() in ('.zip', '.7z', '.rar')})
                    except (OSError, RuntimeError, zipfile.BadZipFile) as error:
                        entry['members'].append({'path': member.filename, 'bytes': member.file_size,
                                                 'status': type(error).__name__})
        else:
            entry['archive_format'] = 'non_zip_or_unsupported'
        after = p.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError('Local source changed: ' + paths[0])
        return entry

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise ValueError('Source inventory output exists')
    stats = collections.Counter()
    started = time.monotonic()
    with args.output.open('xb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=6) as gz:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            # executor.map is ordered; the number of paths is bounded by the local source census.
            for entry in pool.map(inspect, groups):
                gz.write(encoded(entry) + b'\n')
                stats['source_files'] += 1
                stats['source_bytes'] += entry['archive_bytes']
                stats['official_url_present' if entry['official_urls'] else 'official_url_unresolved'] += 1
                stats['members'] += len(entry['members'])
                stats['members_hashed'] += sum('sha256' in m for m in entry['members'])
                stats['nested_members'] += sum(m.get('nested_archive', False) for m in entry['members'])
                if stats['source_files'] % 5000 == 0:
                    print(json.dumps(dict(stats)), flush=True)
    report = {'wg': args.wg, 'scope': 'Complete local meetings and change-request source trees; a superset of indexed inputs.',
              'counts': dict(stats), 'compressed_bytes': args.output.stat().st_size,
              'sha256': digest(args.output), 'seconds': time.monotonic() - started,
              'axis_registry_sha256': digest(repository / 'scripts/common/common/axis.py'),
              'url_network_validation_claimed': False, 'nested_member_recursion_claimed': False,
              'full_text_included': False}
    args.report.write_bytes(encoded(report) + b'\n')
    print(json.dumps(report))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    p = subs.add_parser('split-recipes')
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--rows-per-part',type=int,default=50000)
    p.set_defaults(run=split_recipes)
    p = subs.add_parser('restore-tdocs')
    p.add_argument('--repository',type=Path,required=True)
    p.add_argument('--recipes',type=Path,required=True)
    p.add_argument('--cache',type=Path,required=True)
    p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--download',action='store_true')
    p.add_argument('--local-archive-repository',type=Path)
    p.add_argument('--timeout',type=int,default=60)
    p.add_argument('--start',type=int,default=0)
    p.add_argument('--stop',type=int)
    p.set_defaults(run=restore_tdocs)
    p = subs.add_parser('export')
    p.add_argument('--database', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--repository', type=Path)
    p.add_argument('--hash-database', action='store_true')
    p.set_defaults(run=export)
    p = subs.add_parser('restore-wg')
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.set_defaults(run=restore_wg)
    p = subs.add_parser('refresh-locators')
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--database', type=Path, required=True)
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.set_defaults(run=refresh_locators)
    p = subs.add_parser('split-table')
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--table', required=True)
    p.add_argument('--rows-per-part', type=int, default=400000)
    p.set_defaults(run=split_table)
    p = subs.add_parser('compress-probe')
    p.add_argument('--database', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--level', type=int, choices=range(1, 10), default=1)
    p.set_defaults(run=compress_probe)
    p = subs.add_parser('source-inventory')
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--wg', choices=['RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'], required=True)
    p.add_argument('--plenary-bundle', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--workers', type=int, default=4)
    p.set_defaults(run=source_inventory)
    p = subs.add_parser('reparse-tdoc')
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--recipe', type=Path, required=True)
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--output', type=Path)
    p.add_argument('--report', type=Path, required=True)
    p.set_defaults(run=reparse_tdoc)
    p = subs.add_parser('acquire-tdoc')
    p.add_argument('--repository', type=Path, default=Path(__file__).resolve().parents[5])
    p.add_argument('--recipe', type=Path, required=True)
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--download', action='store_true')
    p.add_argument('--local-archive-repository', type=Path)
    p.add_argument('--timeout', type=int, default=60)
    p.set_defaults(run=acquire_tdoc)
    p = subs.add_parser('reparse-tdoc-batch')
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--recipes', type=Path, required=True)
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--download', action='store_true')
    p.add_argument('--local-archive-repository', type=Path)
    p.add_argument('--timeout', type=int, default=60)
    p.set_defaults(run=reparse_tdoc_batch)
    p = subs.add_parser('prepare-tdoc-recipes')
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--database', type=Path, required=True)
    p.add_argument('--wg', choices=['RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'], required=True)
    p.add_argument('--source-inventory', type=Path, required=True)
    p.add_argument('--url-inventory', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.set_defaults(run=prepare_tdoc_recipes)
    p = subs.add_parser('repair-tdoc-recipes')
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--source-inventory', type=Path, required=True)
    p.add_argument('--url-inventory', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.set_defaults(run=repair_tdoc_recipes)
    p = subs.add_parser('prepare-resolution-recipes')
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--database', type=Path, required=True)
    p.add_argument('--wg', choices=['RAN1','RAN2','RAN3','RAN4','RAN5'], required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.set_defaults(run=prepare_resolution_recipes)
    p = subs.add_parser('prepare-report-sources')
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--wg', choices=['RAN1','RAN2','RAN3','RAN4','RAN5'], required=True)
    p.add_argument('--source-inventory', type=Path, required=True)
    p.add_argument('--tdoc-recipes', type=Path)
    p.add_argument('--resolution-receipt', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.set_defaults(run=prepare_report_sources)
    p = subs.add_parser('restore-resolutions')
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--recipes', type=Path, required=True)
    p.add_argument('--sources', type=Path, required=True)
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.set_defaults(run=restore_resolutions)
    p = subs.add_parser('acquire-reports')
    p.add_argument('--sources',type=Path,required=True)
    p.add_argument('--cache',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--download',action='store_true')
    p.add_argument('--local-archive-repository',type=Path)
    p.add_argument('--timeout',type=int,default=60)
    p.set_defaults(run=acquire_reports)
    args = parser.parse_args()
    args.run(args)


if __name__ == '__main__':
    main()
