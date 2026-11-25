#!/usr/bin/env python3
"""Check raw CR forms against fixed Phase-8 chunk digests without services.

Recipes hold source digests, structural metadata and expected chunk digests.
Reason, summary, consequences and clauses are read from the acquired DOCX.
Only the metadata resolver calls are adapted; body parsing and hardening use
the hash-pinned original implementation.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from dataclasses import asdict
from functools import lru_cache
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import time
import types


RAW_FIELDS = {
    'reason_for_change': 'reason for change',
    'summary_of_change': 'summary of change',
    'consequences_if_not_approved': 'consequences if not approved',
    'clauses_affected': 'clauses affected',
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda: stream.read(4 << 20), b''):
            h.update(part)
    return h.hexdigest()


def text_sha(value):
    return hashlib.sha256((value or '').encode()).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def exporter(repository):
    return module(repository / 'scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/export_retrieval_artifact.py', 'cr_probe_exporter')


@lru_cache(maxsize=5)
def load_phase8(repository, wg, expected_sha):
    path = repository / f'scripts/tsg/RAN/formal/{wg}/phase-8/cr-parser/01_parse_cr_chunks.py'
    if sha(path) != expected_sha:
        raise ValueError('Phase-8 implementation changed')
    tree = ast.parse(path.read_text(), filename=str(path))
    class Adapt(ast.NodeTransformer):
        removed = 0
        sheet_calls = 0
        def visit_ImportFrom(self, node):
            if node.module == 'tdoc_body_source_metadata' and [x.name for x in node.names] == ['validate_source_selection']:
                self.removed += 1
                return None
            return node
        def visit_Call(self, node):
            node = self.generic_visit(node)
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'tsg_cr_decision' and node.func.attr == 'sheet_cr_label':
                self.sheet_calls += 1
                node.func = ast.Name(id='frozen_sheet_cr_label', ctx=ast.Load())
            return node
    adapter = Adapt(); tree = adapter.visit(tree); ast.fix_missing_locations(tree)
    if (adapter.removed, adapter.sheet_calls) != (1, 1):
        raise ValueError('Metadata adapter source shape changed')
    name = 'cr_raw_phase8_' + wg
    result = types.ModuleType(name); result.__file__ = str(path); sys.modules[name] = result
    def validate_source_selection(root, view_wg, view, target, paths):
        recipe, source = result.frozen_context
        if view_wg != wg or view != 'cr' or target != recipe['tdoc'] or [Path(p).resolve() for p in paths] != [source.resolve()]:
            raise ValueError('Frozen source selection differs')
    def frozen_sheet_cr_label(number, tdoc, pack):
        recipe, source = result.frozen_context
        expected_identity = recipe['source_identity']
        if (number, tdoc, pack) != (expected_identity[1], recipe['tdoc'], recipe['cr_metadata'].get('cr_pack_id', '')):
            raise ValueError('Frozen CR identity differs')
        return number
    result.validate_source_selection = validate_source_selection
    result.frozen_sheet_cr_label = frozen_sheet_cr_label
    exec(compile(tree, str(path), 'exec'), result.__dict__)
    return result


def checked_phase8(repository, wg, recipe, source):
    result = load_phase8(repository, wg, recipe['phase8_sha256'])
    result.frozen_context = recipe, source
    return result


@lru_cache(maxsize=5)
def checked_phase4(repository, wg, expected_sha):
    path = repository / f'scripts/tsg/RAN/formal/{wg}/phase-4/cr-parser/02_parse_cr_documents.py'
    if sha(path) != expected_sha:
        raise ValueError('Phase-4 implementation changed')
    return module(path, 'cr_raw_phase4_' + wg)


def make_recipe(repository, wg, parser, cover_map, record, expected):
    chosen = record['tdoc_number']
    source = repository / record['source_path']
    pack = record.get('cr_pack_id', '')
    cover = cover_map.get((pack, chosen), {}) if pack else cover_map.get(chosen, {})
    pack_cover = cover_map.get((pack, ''), {}) if pack else cover
    first = expected[0]
    code_paths = [Path(parser.__file__), repository / f'scripts/tsg/RAN/formal/{wg}/phase-4/cr-parser/02_parse_cr_documents.py']
    code_paths += list((repository / 'scripts/tsg/RAN/formal/common').glob('*.py'))
    code_paths += [repository / f'scripts/common/common/{name}' for name in
                   ('chunker.py', 'atomic_io.py', 'embedding_registry.py', 'tdoc_number.py', 'local_model.py')]
    recipe = {
        'format': 'spectra-offline-cr-recipe-v1', 'wg': wg, 'tdoc': chosen,
        'source_path': record['source_path'], 'source_sha256': sha(source),
        'source_identity': [first['specNumber'], first['crNumber'], chosen],
        'phase8_sha256': sha(Path(parser.__file__)),
        'phase4_sha256': sha(repository / f'scripts/tsg/RAN/formal/{wg}/phase-4/cr-parser/02_parse_cr_documents.py'),
        'code_sha256': {str(p.relative_to(repository)): sha(p) for p in code_paths if p.is_file()},
        'cr_metadata': {k: v for k, v in record.items() if k not in RAW_FIELDS},
        'cover_metadata': cover, 'pack_metadata': pack_cover,
        'expected_raw_field_sha256': {k: text_sha(record.get(k)) for k in RAW_FIELDS},
        'expected_chunks': [{'chunkId': c['chunkId'], 'text_sha256': text_sha(c['text'])} for c in expected],
        'metadata_adapter': {'validate_source_selection': 'explicit frozen target and checked source path',
                             'sheet_cr_label': 'frozen original index CR label; no live CR-sheet lookup'},
    }
    return recipe


def input_maps(repository, wg):
    parser = module(repository / f'scripts/tsg/RAN/formal/{wg}/phase-8/cr-parser/01_parse_cr_chunks.py', 'cr_prepare_' + wg)
    cover_map, cr_map = parser.load_phase4_metadata()
    chunks_path = repository / f'vectordb/parsed/cr/{wg}/{wg.lower()}_cr_chunks.json'
    chunks = json.loads(chunks_path.read_text())['chunks']
    groups = defaultdict(list)
    for chunk in chunks:
        groups[chunk['tdocNumber']].append(chunk)
    return parser, cover_map, cr_map, groups


def prepare(args):
    repository, wg = args.repository.resolve(), args.wg
    parser, cover_map, cr_map, groups = input_maps(repository, wg)
    chosen = args.tdoc or next(iter(groups))
    expected = groups[chosen]
    recipe = make_recipe(repository, wg, parser, cover_map, cr_map[chosen], expected)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise ValueError('Recipe exists')
    args.output.write_bytes(encoded(recipe) + b'\n')
    print(json.dumps({'tdoc': chosen, 'chunks': len(expected), 'source_sha256': recipe['source_sha256']}))


def inventory(args):
    repository, wg = args.repository.resolve(), args.wg
    helper = exporter(repository)
    parser, cover_map, cr_map, groups = input_maps(repository, wg)
    sources, by_path = {}, {}
    with gzip.open(args.source_inventory, 'rt') as stream:
        for line in stream:
            row = json.loads(line); sources[row['archive_sha256']] = row
            for path in row['paths']:
                by_path[path] = row
                by_path[path.lower()] = row
    if args.url_inventory:
        with gzip.open(args.url_inventory, 'rt') as stream:
            for line in stream:
                row = json.loads(line)
                if row['sha256'] in sources:
                    found = sources[row['sha256']]
                    found['official_urls'] = sorted(set(found['official_urls']) | set(row['candidateUrls']))
    counts, unknown, started = Counter(), [], time.monotonic()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise ValueError('Inventory exists')
    with args.output.open('xb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, compresslevel=6, mtime=0) as gz:
        for tdoc, expected in groups.items():
            if tdoc not in cr_map:
                row = {'tdoc': tdoc, 'status': 'phase4_record_unresolved', 'expected_chunks': len(expected)}
                unknown.append(row); counts[row['status']] += 1; gz.write(encoded(row) + b'\n'); continue
            row = make_recipe(repository, wg, parser, cover_map, cr_map[tdoc], expected)
            path = Path(row['source_path'])
            source = None
            for parent in path.parents:
                candidate = str(parent).replace('/derived/', '/source/', 1) + '.zip'
                if candidate in by_path:
                    source = by_path[candidate]; break
            if source is None:
                row['status'] = 'source_archive_unresolved'
            else:
                archive = repository / source['paths'][0]
                wanted = row['source_sha256']
                chain = next(([{'name': m['path'], 'sha256': m['sha256'], 'bytes': m['bytes']}]
                              for m in source.get('members', []) if m.get('sha256') == wanted), None)
                if chain is None:
                    try:
                        chain = helper.zip_member_chain(archive, wanted)
                    except Exception as error:
                        row['archive_scan_error'] = type(error).__name__ + ': ' + str(error)
                selected = {'path': row['source_path'], 'sha256': wanted,
                            'archive_paths': source['paths'], 'archive_sha256': source['archive_sha256'],
                            'official_urls': [url for url in source['official_urls'] if url.startswith('https://')],
                            'archive_bytes': source['archive_bytes']}
                if chain:
                    selected.update(source_status='exact_archive_member', member_chain=chain)
                    row['status'] = 'exact_archive_member'
                else:
                    try:
                        leaves = helper.zip_leaf_members(archive)
                        desired = path.name.casefold()
                        native_names = {desired[:-1] if desired.endswith('.docx') else desired,
                                        str(Path(desired).with_suffix('.doc')),
                                        str(Path(desired).with_suffix('.docm'))}
                        candidates = [(chain, magic) for chain, magic in leaves if Path(chain[-1]['name']).name.casefold() in native_names]
                        if len(candidates) == 1:
                            chain, magic = candidates[0]
                            selected.update(helper.native_conversion_record(chain, magic))
                            row['status'] = 'native_doc_conversion_recipe'
                        else:
                            row['status'] = 'member_or_conversion_unresolved'
                            row['candidate_members'] = [{'member_chain': chain, 'magic_prefix': magic} for chain, magic in leaves]
                    except Exception as error:
                        row['status'] = 'member_scan_error'; row['error'] = type(error).__name__ + ': ' + str(error)
                row['sources'] = [selected]
            if row['status'] not in ('exact_archive_member', 'native_doc_conversion_recipe'):
                selected = helper.source_recipe(repository / row['source_path'], repository, by_path)
                row['sources'] = [selected]
                row['status'] = selected['source_status']
            counts[row['status']] += 1
            if row['status'] not in ('exact_archive_member', 'native_doc_conversion_recipe'):
                unknown.append({k:v for k,v in row.items() if k not in ('code_sha256', 'cr_metadata', 'cover_metadata', 'pack_metadata', 'expected_chunks')})
            gz.write(encoded(row) + b'\n')
            if sum(counts.values()) % 250 == 0:
                print(json.dumps({'processed': sum(counts.values()), 'counts': dict(counts)}), flush=True)
    report = {'wg': wg, 'indexed_cr_tdocs': len(groups), 'phase4_records': len(cr_map), 'indexed_chunks': sum(map(len,groups.values())),
              'counts': dict(counts), 'unknown': unknown, 'sha256': sha(args.output), 'bytes': args.output.stat().st_size,
              'seconds': time.monotonic() - started,
              'scope': 'Archive/member mapping with source digests and conversion recipes; actual raw executions have separate receipts.'}
    args.report.write_bytes(encoded(report) + b'\n'); print(json.dumps({k:v for k,v in report.items() if k!='unknown'}))


def execute_recipe(repository, recipe, source):
    if sha(source) != recipe['source_sha256']:
        proof = source.with_name(source.name + '.conversion.json')
        if not proof.is_file() or json.loads(proof.read_text()).get('output_sha256') != sha(source):
            raise ValueError('Source DOCX digest differs')
    wg = recipe['wg']
    phase4 = checked_phase4(repository, wg, recipe['phase4_sha256'])
    doc = phase4.docx_text.open_document(str(source))
    form = phase4.find_cr_form_table(doc)
    if form is None:
        raise ValueError('Source CR form not found')
    raw = {key: phase4.cr_form_slot.form_value(form, label) for key, label in RAW_FIELDS.items()}
    field_match = {k: text_sha(v) == recipe['expected_raw_field_sha256'][k] for k, v in raw.items()}
    cr_meta = dict(recipe['cr_metadata']); cr_meta.update(raw)
    tdoc, pack = recipe['tdoc'], cr_meta.get('cr_pack_id', '')
    cover = {(pack, tdoc): recipe['cover_metadata'], (pack, ''): recipe['pack_metadata'], tdoc: recipe['cover_metadata']}
    parser = checked_phase8(repository, wg, recipe, source)
    started = time.monotonic()
    chunks = parser.parse_single_cr(source, cover, {tdoc: cr_meta}, source_identity=tuple(recipe['source_identity']))
    chunks = parser._harden_per_cr([asdict(c) for c in chunks])
    actual = [{'chunkId': c['chunkId'], 'text_sha256': text_sha(c['text'])} for c in chunks]
    report = {'tdoc': tdoc, 'actual_source_sha256': sha(source),
              'snapshot_source_container_sha_equal': sha(source) == recipe['source_sha256'],
              'raw_field_sha_equal': field_match, 'expected_chunk_count': len(recipe['expected_chunks']),
              'actual_chunk_count': len(chunks), 'all_expected_chunks_exact': actual == recipe['expected_chunks'],
              'actual_chunk_digests': actual, 'seconds': time.monotonic() - started,
              'runtime': {'python': sys.version, 'executable': sys.executable, 'sqlite': sqlite3.sqlite_version},
              'scope': 'Raw DOCX form fields and Phase-8 parsing/hardening; frozen metadata resolver adapter.'}
    return report


def replay(args):
    repository = args.repository.resolve()
    recipe = json.loads(args.recipe.read_text())
    source = args.source or repository / recipe['source_path']
    report = execute_recipe(repository, recipe, source)
    report['recipe_sha256'] = sha(args.recipe)
    args.report.parent.mkdir(parents=True, exist_ok=True); args.report.write_bytes(encoded(report) + b'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'actual_chunk_digests'}))
    if not report['all_expected_chunks_exact']:
        raise ValueError('Raw-source CR chunk digest sequence differs')


def batch(args):
    repository = args.repository.resolve()
    outcomes, counts, started = [], Counter(), time.monotonic()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.recipes, 'rt') as stream:
        for line in stream:
            recipe = json.loads(line); begin = time.monotonic()
            try:
                source = (args.source_root or repository) / recipe['source_path']
                report = execute_recipe(repository, recipe, source)
                report.pop('actual_chunk_digests')
                report['status'] = 'all_expected_chunks_exact' if report['all_expected_chunks_exact'] else 'chunk_digest_differs'
            except Exception as error:
                report = {'tdoc': recipe['tdoc'], 'status': 'error', 'error_type': type(error).__name__, 'error': str(error)}
            report['seconds'] = time.monotonic() - begin
            outcomes.append(report); counts[report['status']] += 1
            args.report.write_bytes(encoded({'complete': False, 'counts': dict(counts), 'outcomes': outcomes}) + b'\n')
            if len(outcomes) % 100 == 0:
                print(json.dumps({'processed':len(outcomes),'counts':dict(counts)}), flush=True)
    result = {'complete': True, 'recipes_sha256': sha(args.recipes), 'outcomes': outcomes, 'counts': dict(counts),
              'seconds': time.monotonic()-started, 'source_root_mode': 'separate_acquired_cache' if args.source_root else 'retained_hash_pinned_derived_DOCX',
              'runtime': {'python': sys.version, 'sqlite': sqlite3.sqlite_version, 'executable': sys.executable},
              'scope': 'Raw DOCX form-slot extraction and Phase-8 parser/hardening. Source acquisition is recorded separately.'}
    args.report.write_bytes(encoded(result)+b'\n'); print(json.dumps({k:v for k,v in result.items() if k!='outcomes'}))


def main():
    p = argparse.ArgumentParser(description=__doc__); subs = p.add_subparsers(dest='command', required=True)
    q = subs.add_parser('prepare'); q.add_argument('--repository', type=Path, default=Path('.')); q.add_argument('--wg', default='RAN3'); q.add_argument('--tdoc'); q.add_argument('--output', type=Path, required=True)
    q = subs.add_parser('replay'); q.add_argument('--repository', type=Path, default=Path('.')); q.add_argument('--recipe', type=Path, required=True); q.add_argument('--source', type=Path); q.add_argument('--report', type=Path, required=True)
    q = subs.add_parser('inventory'); q.add_argument('--repository', type=Path, default=Path('.')); q.add_argument('--wg', default='RAN3'); q.add_argument('--source-inventory', type=Path, required=True); q.add_argument('--url-inventory', type=Path); q.add_argument('--output', type=Path, required=True); q.add_argument('--report', type=Path, required=True)
    q = subs.add_parser('batch'); q.add_argument('--repository', type=Path, default=Path('.')); q.add_argument('--recipes', type=Path, required=True); q.add_argument('--source-root', type=Path); q.add_argument('--report', type=Path, required=True)
    args = p.parse_args(); globals()[args.command](args)


if __name__ == '__main__':
    main()
