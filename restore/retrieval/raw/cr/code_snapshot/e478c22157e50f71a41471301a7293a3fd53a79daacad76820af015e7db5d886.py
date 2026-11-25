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
import importlib.metadata
import inspect
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import types
import zipfile

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'


RAW_FIELDS = {
    'reason_for_change': 'reason for change',
    'summary_of_change': 'summary of change',
    'consequences_if_not_approved': 'consequences if not approved',
    'clauses_affected': 'clauses affected',
}

SNAPSHOT_BRIDGE = {'rule': 'single_extra_lf_after_heading',
                   'source': 'Hash-pinned raw Phase-8 parser output',
                   'target': 'Frozen chunk ID and text SHA256 sequence',
                   'operation': 'Delete one LF at the first heading boundary only when the complete target digest matches'}


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


def runtime():
    packages={}
    for name in ('python-docx','lxml','transformers','tokenizers','torch'):
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:packages[name]=None
    return {'python':sys.version,'sqlite':sqlite3.sqlite_version,'executable':sys.executable,'packages':packages}


@lru_cache(maxsize=8)
def verify_code(repository, pins):
    for relative, expected in pins:
        path=(repository/relative).resolve()
        if not path.is_relative_to(repository) or sha(path)!=expected:
            raise ValueError('Code dependency digest differs: '+relative)
    return True


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
        identity_calls = 0
        source_metadata_imports = 0
        def visit_ImportFrom(self, node):
            if node.module == 'tdoc_body_source_metadata' and [x.name for x in node.names] == ['validate_source_selection']:
                self.removed += 1
                return None
            if node.module == 'tdoc_source_metadata' and [x.name for x in node.names] == ['identity_fields', 'corrected_label']:
                self.source_metadata_imports += 1
                return None
            return node
        def visit_Call(self, node):
            node = self.generic_visit(node)
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'tsg_cr_decision' and node.func.attr == 'sheet_cr_label':
                self.sheet_calls += 1
                node.func = ast.Name(id='frozen_sheet_cr_label', ctx=ast.Load())
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'resolve' and isinstance(node.func.value, ast.Call) and isinstance(node.func.value.func, ast.Name) and node.func.value.func.id == 'identity':
                self.identity_calls += 1
                node.func = ast.Name(id='frozen_identity', ctx=ast.Load())
            return node
    adapter = Adapt(); tree = adapter.visit(tree); ast.fix_missing_locations(tree)
    expected_shape = {'RAN1':(0,1,2,0),'RAN2':(1,1,3,0),'RAN3':(1,1,2,0),'RAN4':(1,1,3,0),'RAN5':(1,1,0,1)}[wg]
    if (adapter.removed, adapter.sheet_calls, adapter.identity_calls, adapter.source_metadata_imports) != expected_shape:
        raise ValueError('Metadata adapter source shape changed: '+str((adapter.removed,adapter.sheet_calls,adapter.identity_calls,adapter.source_metadata_imports)))
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
    result.frozen_identity = lambda path: tuple(result.frozen_context[0]['source_identity'])
    result.identity_fields = lambda root, view_wg: {}
    result.corrected_label = lambda label, fields: label
    exec(compile(tree, str(path), 'exec'), result.__dict__)
    return result


def checked_phase8(repository, wg, recipe, source):
    result = load_phase8(repository, wg, recipe['phase8_sha256'])
    result.frozen_context = recipe, source
    return result


@lru_cache(maxsize=5)
def checked_phase4(repository, wg, expected_sha):
    path = phase4_path(repository,wg)
    if sha(path) != expected_sha:
        raise ValueError('Phase-4 implementation changed')
    return module(path, 'cr_raw_phase4_' + wg)


def phase4_path(repository, wg):
    filename = '01_parse_cr_documents.py' if wg == 'RAN5' else '02_parse_cr_documents.py'
    return repository / f'scripts/tsg/RAN/formal/{wg}/phase-4/cr-parser/{filename}'


@lru_cache(maxsize=5)
def original_code_pins(repository, wg):
    code_paths = [repository / f'scripts/tsg/RAN/formal/{wg}/phase-8/cr-parser/01_parse_cr_chunks.py', phase4_path(repository,wg)]
    code_paths += list((repository / 'scripts/tsg/RAN/formal/common').glob('*.py'))
    code_paths += [repository / f'scripts/common/common/{name}' for name in
                   ('chunker.py', 'atomic_io.py', 'embedding_registry.py', 'tdoc_number.py', 'local_model.py')]
    return {str(p.relative_to(repository)):sha(p)for p in code_paths if p.is_file()}


def make_recipe(repository, wg, parser, cover_map, record, expected):
    chosen = record['tdoc_number']
    source = repository / record['source_path']
    pack = record.get('cr_pack_id', '')
    cover = cover_map.get((pack, chosen), {}) if pack else cover_map.get(chosen, {})
    pack_cover = cover_map.get((pack, ''), {}) if pack else cover
    first = expected[0]
    code_pins=original_code_pins(repository,wg)
    recipe = {
        'format': 'spectra-offline-cr-recipe-v1', 'wg': wg, 'tdoc': chosen,
        'source_path': record['source_path'], 'source_sha256': sha(source),
        'source_identity': [first['specNumber'], first['crNumber'], chosen],
        'phase8_sha256': code_pins[str(Path(parser.__file__).relative_to(repository))],
        'phase4_sha256': code_pins[str(phase4_path(repository,wg).relative_to(repository))],
        'code_sha256': code_pins,
        'cr_metadata': {k: v for k, v in record.items() if k not in RAW_FIELDS},
        'cover_metadata': cover, 'pack_metadata': pack_cover,
        'expected_raw_field_sha256': {k: text_sha(record.get(k)) for k in RAW_FIELDS},
        'expected_chunks': [{'chunkId': c['chunkId'], 'text_sha256': c.get('text_sha256') or text_sha(c['text'])} for c in expected],
        'metadata_adapter': {'validate_source_selection': 'explicit frozen target and checked source path',
                             'sheet_cr_label': 'frozen original index CR label; no live CR-sheet lookup'},
    }
    if '_target_index' in first:
        recipe['target_chunk_indices'] = [c['_target_index'] for c in expected]
        recipe['target_parsed_path'] = f'vectordb/parsed/cr/{wg}/{wg.lower()}_cr_chunks.json'
    if wg == 'RAN4':
        continuation_file=repository / 'vectordb/parsed/cr/RAN4/parse_stats.json'
        extras=json.loads(continuation_file.read_text()).get('continuations',{}).get(chosen,[])
        recipe['continuation_paths']=[{'path':path,'sha256':sha(repository/path)} for path in extras]
    if wg == 'RAN5':
        recipe['snapshot_bridge'] = SNAPSHOT_BRIDGE
    return recipe


def input_maps(repository, wg, frontier=None):
    parser = module(repository / f'scripts/tsg/RAN/formal/{wg}/phase-8/cr-parser/01_parse_cr_chunks.py', 'cr_prepare_' + wg)
    groups = defaultdict(list)
    if wg != 'RAN5':
        cover_map, cr_map = parser.load_phase4_metadata()
    else:
        records=json.loads((repository / f'ontology/output/tsg/RAN/formal/parsed_cr/{wg}/cr_documents.json').read_text())['documents']
        cr_map={r['tdoc_number']:r for r in records};cover_map={}
        packs=json.loads((repository / f'ontology/output/tsg/RAN/formal/parsed_cr/{wg}/crpacks.json').read_text())['packs']
        for pack in packs:
            for tdoc in pack.get('tdocNumbers',[]):
                cover_map[(pack['crPackId'],tdoc)]={'tsg_meeting':pack.get('tsgMeeting',''),'cr_pack_id':pack['crPackId']}
    if frontier:
        helper=exporter(repository)
        for row in helper.rows(frontier,'docs'):
            if row['collection'] != wg.lower()+'_cr_chunks':continue
            meta=json.loads(row['meta']);locator=row['text_locator']
            if locator['status']!='exact_parsed_slice' or locator['start']!=0 or locator['end']!=row['text_chars']:
                raise ValueError('CR frontier needs a separate frozen-snapshot text bridge')
            chunk={'chunkId':row['chunk_id'],'tdocNumber':row['tdoc'],'specNumber':meta.get('specNumber')or row['spec'],
                   'crNumber':meta.get('crNumber'),'text_sha256':row['text_sha256'],'_target_index':locator['pointer'][1]}
            groups[row['tdoc']].append(chunk)
        for group in groups.values():group.sort(key=lambda c:c['_target_index'])
        groups=dict(sorted(groups.items(),key=lambda x:x[1][0]['_target_index']))
    else:
        chunks_path = repository / f'vectordb/parsed/cr/{wg}/{wg.lower()}_cr_chunks.json'
        chunks = json.loads(chunks_path.read_text())['chunks']
        for chunk in chunks:
            groups[chunk['tdocNumber']].append(chunk)
    return parser, cover_map, cr_map, groups


def prepare(args):
    repository, wg = args.repository.resolve(), args.wg
    parser, cover_map, cr_map, groups = input_maps(repository, wg,getattr(args,'frontier',None))
    chosen = args.tdoc or next(iter(groups))
    expected = groups[chosen]
    recipe = make_recipe(repository, wg, parser, cover_map, cr_map[chosen], expected)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise ValueError('Recipe exists')
    args.output.write_bytes(encoded(recipe) + b'\n')
    print(json.dumps({'tdoc': chosen, 'chunks': len(expected), 'source_sha256': recipe['source_sha256']}))


def completed_gzip_rows(path):
    if path is None:return
    with gzip.open(path,'rt')as stream:
        while True:
            try:line=stream.readline()
            except EOFError:return
            if not line or not line.endswith('\n'):return
            yield json.loads(line)


def cr_document_leaves(path, helper, generic_leaves):
    """Hash Word members with one ZIP directory read per archive level.

    JSON/PDF attachments have separate source bytes and are outside a Word
    CR parser's selected input. Their directory entries are inspected, and
    their payloads are skipped. Nested Word members retain every archive hash.
    """
    word={'.doc','.docx','.docm','.rtf'};nested={'.zip','.rar','.7z'}
    def walk(handle,chain,depth):
        try:archive=zipfile.ZipFile(handle)
        except zipfile.BadZipFile:
            return [(chain+parts,magic)for parts,magic in generic_leaves(handle)
                    if Path(parts[-1]['name']).suffix.lower()in word]
        leaves=[]
        with archive:
            for member in archive.infolist():
                suffix=Path(member.filename).suffix.lower()
                if member.is_dir()or suffix not in word|nested:continue
                try:content=archive.read(member)
                except NotImplementedError:content=helper.read_zip_member(handle,member.filename)
                entry={'name':member.filename,'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)}
                if suffix in nested:
                    if depth<10:leaves+=walk(io.BytesIO(content),chain+[entry],depth+1)
                else:leaves.append((chain+[entry],content[:8].hex()))
        return leaves
    return walk(path,[],0)


def inventory(args):
    repository, wg = args.repository.resolve(), args.wg
    helper = exporter(repository)
    generic_leaves=helper.zip_leaf_members
    helper.zip_leaf_members = lru_cache(maxsize=8)(lambda path:cr_document_leaves(path,helper,generic_leaves))
    parser, cover_map, cr_map, groups = input_maps(repository, wg,getattr(args,'frontier',None))
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
    prefix=iter(completed_gzip_rows(args.resume_prefix));resumed=0
    total_chunks=sum(map(len,groups.values()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise ValueError('Inventory exists')
    with args.output.open('xb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, compresslevel=6, mtime=0) as gz:
        for tdoc, expected in groups.items():
            prior=next(prefix,None)
            if prior is not None:
                target=[{'chunkId':c['chunkId'],'text_sha256':c.get('text_sha256')or text_sha(c['text'])}for c in expected]
                if prior['tdoc']!=tdoc or prior.get('expected_chunks')!=target or prior.get('target_total_chunks')!=total_chunks:
                    raise ValueError('Inventory resume prefix target sequence differs')
                verify_code(repository,tuple(sorted(prior['code_sha256'].items())))
                counts[prior['status']]+=1;resumed+=1;gz.write(encoded(prior)+b'\n')
                if prior['status']not in('exact_archive_member','native_doc_conversion_recipe'):
                    unknown.append({k:v for k,v in prior.items()if k not in('code_sha256','cr_metadata','cover_metadata','pack_metadata','expected_chunks')})
                continue
            if args.resume_prefix:print(json.dumps({'next_unmapped_tdoc':tdoc}),flush=True)
            if tdoc not in cr_map:
                row = {'tdoc': tdoc, 'status': 'phase4_record_unresolved', 'expected_chunks': len(expected)}
                unknown.append(row); counts[row['status']] += 1; gz.write(encoded(row) + b'\n'); continue
            row = make_recipe(repository, wg, parser, cover_map, cr_map[tdoc], expected)
            row['target_total_chunks']=total_chunks
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
                        chain = next((parts for parts, magic in helper.zip_leaf_members(archive) if parts[-1]['sha256'] == wanted), None)
                    except Exception as error:
                        row['archive_scan_error'] = type(error).__name__ + ': ' + str(error)
                        chain = helper.zip_member_chain(archive, wanted)
                        if chain:
                            row['archive_scan_fallback'] = 'Exact SHA search through ZIP members; unrelated unsupported nested archives are outside the selected chain'
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
            for extra in row.get('continuation_paths',[]):
                selected=helper.source_recipe(repository/extra['path'],repository,by_path)
                row.setdefault('sources',[]).append(selected)
                if selected['source_status'] not in ('exact_archive_member','native_doc_conversion_recipe','exact_source_file'):
                    row['status']='continuation_source_unresolved'
            counts[row['status']] += 1
            if row['status'] not in ('exact_archive_member', 'native_doc_conversion_recipe'):
                unknown.append({k:v for k,v in row.items() if k not in ('code_sha256', 'cr_metadata', 'cover_metadata', 'pack_metadata', 'expected_chunks')})
            gz.write(encoded(row) + b'\n')
            if sum(counts.values()) % 250 == 0:
                print(json.dumps({'processed': sum(counts.values()), 'counts': dict(counts)}), flush=True)
    report = {'wg': wg, 'indexed_cr_tdocs': len(groups), 'phase4_records': len(cr_map), 'indexed_chunks': sum(map(len,groups.values())),
              'counts': dict(counts), 'unknown': unknown, 'sha256': sha(args.output), 'bytes': args.output.stat().st_size,
              'seconds': time.monotonic() - started,
              'resumed_prefix_rows':resumed,'resume_prefix_sha256':sha(args.resume_prefix)if args.resume_prefix else None,
              'scope': 'Archive/member mapping with source digests and conversion recipes; actual raw executions have separate receipts.'}
    args.report.write_bytes(encoded(report) + b'\n'); print(json.dumps({k:v for k,v in report.items() if k!='unknown'}))


def apply_snapshot_bridge(chunks, expected, policy):
    """Preserve a fixed snapshot's single-LF separator with digest checks."""
    if policy is None:return []
    if policy != SNAPSHOT_BRIDGE:raise ValueError('Unsupported CR snapshot bridge rule')
    if len(chunks)!=len(expected):return []
    applied=[]
    for chunk,target in zip(chunks,expected):
        if chunk['chunkId']!=target['chunkId']:continue
        text=chunk['text'];source_sha=text_sha(text)
        if source_sha==target['text_sha256']:continue
        boundary=text.find('\n')+1
        if '-body-' not in chunk['chunkId'] or boundary<=0 or text[boundary:boundary+1]!='\n':continue
        candidate=text[:boundary]+text[boundary+1:]
        if text_sha(candidate)!=target['text_sha256']:continue
        chunk['text']=candidate
        applied.append({'chunkId':chunk['chunkId'],'parser_text_sha256':source_sha,
                        'delete_span':[boundary,boundary+1],'deleted_sha256':text_sha('\n'),
                        'target_text_sha256':target['text_sha256']})
    return applied


def execute_recipe(repository, recipe, source, output=None):
    verify_code(repository,tuple(sorted(recipe.get('code_sha256',{}).items())))
    if sha(source) != recipe['source_sha256']:
        expected_native = (recipe.get('sources') or [{}])[0].get('conversion', {}).get('native_sha256')
        if not expected_native:
            raise ValueError('Source DOCX digest differs without a pinned native conversion')
        proof = source.with_name(source.name + '.conversion.json')
        if not proof.is_file() or json.loads(proof.read_text()).get('output_sha256') != sha(source):
            raise ValueError('Source DOCX digest differs')
        proof_data = json.loads(proof.read_text())
        if proof_data.get('native_sha256') != expected_native:
            raise ValueError('Converted native source digest differs')
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
    if wg == 'RAN5':
        form=parser.extract_cr_form(doc,source.name)
        form.tdoc_number=tdoc;form.spec_number=recipe['source_identity'][0]
        form.release=cr_meta.get('release') or form.release
        form.title=cr_meta.get('title') or form.title
        form._crDelProof=parser.cr_del_state.prove_xml([doc.element.body],lambda p:parser.docx_text.chunk_text(p,deleted=parser.docx_text.KEEP),raw_metadata=vars(form))
        p4={'cr_number':cr_meta.get('cr_number',''),'rev':cr_meta.get('rev',''),'cr_pack_id':pack,'meeting':'',
            'tsg_meeting':recipe['cover_metadata'].get('tsg_meeting',''),'source':'','title':cr_meta.get('title')or'',
            'work_item':cr_meta.get('work_item')or''}
        chunks=parser.generate_cr_chunks(form,*parser.extract_text_proposal(doc),phase4_meta=p4,cr_number=recipe['source_identity'][1])
        tree=ast.parse(Path(parser.__file__).read_text())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
        output_dict=next(n.value for n in main.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='output'for t in n.targets))
        expr=next(v for k,v in zip(output_dict.keys,output_dict.values)if isinstance(k,ast.Constant)and k.value=='chunks')
        chunks=eval(compile(ast.Expression(expr),str(parser.__file__),'eval'),parser.__dict__,{'all_chunks':chunks})
    else:
        kwargs={}
        if 'source_identity' in inspect.signature(parser.parse_single_cr).parameters:kwargs['source_identity']=tuple(recipe['source_identity'])
        if recipe.get('continuation_paths'):
            source_root=source
            for _ in Path(recipe['source_path']).parts:source_root=source_root.parent
            extras=[source_root/entry['path']for entry in recipe['continuation_paths']]
            if any(sha(path)!=entry['sha256'] for path,entry in zip(extras,recipe['continuation_paths'])):
                raise ValueError('Continuation source digest differs')
            kwargs['extra']=tuple(extras)
        chunks = [asdict(c)for c in parser.parse_single_cr(source, cover, {tdoc: cr_meta}, **kwargs)]
    chunks = parser._harden_per_cr(chunks)
    unbridged = [{'chunkId': c['chunkId'], 'text_sha256': text_sha(c['text'])} for c in chunks]
    bridge = apply_snapshot_bridge(chunks, recipe['expected_chunks'], recipe.get('snapshot_bridge'))
    actual = [{'chunkId': c['chunkId'], 'text_sha256': text_sha(c['text'])} for c in chunks]
    report = {'tdoc': tdoc, 'actual_source_sha256': sha(source),
              'snapshot_source_container_sha_equal': sha(source) == recipe['source_sha256'],
              'raw_field_sha_equal': field_match, 'expected_chunk_count': len(recipe['expected_chunks']),
              'actual_chunk_count': len(chunks), 'all_expected_chunks_exact': actual == recipe['expected_chunks'],
              'all_raw_fields_exact': all(field_match.values()),
              'supported_replay_exact': all(field_match.values()) and actual == recipe['expected_chunks'],
              'unbridged_all_expected_chunks_exact': unbridged == recipe['expected_chunks'],
              'snapshot_bridge_applied': bridge,
              'actual_chunk_digests': actual, 'seconds': time.monotonic() - started,
              'runtime':runtime(),
              'scope': 'Raw DOCX form fields and Phase-8 parsing/hardening, frozen metadata resolver adapter, and any explicitly declared digest-checked snapshot separator bridge.'}
    if output and report['supported_replay_exact']:
        output.parent.mkdir(parents=True, exist_ok=True)
        content = encoded({'tdoc': tdoc, 'chunks': chunks}) + b'\n'
        if output.exists() and output.read_bytes() != content:
            raise ValueError('Existing local parsed output differs')
        if not output.exists():
            output.write_bytes(content)
        report['local_output_sha256'] = sha(output)
    return report


def replay(args):
    repository = args.repository.resolve()
    recipe = json.loads(args.recipe.read_text())
    source = args.source or repository / recipe['source_path']
    report = execute_recipe(repository, recipe, source, args.output)
    report['recipe_sha256'] = sha(args.recipe)
    args.report.parent.mkdir(parents=True, exist_ok=True); args.report.write_bytes(encoded(report) + b'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'actual_chunk_digests'}))
    if not report['supported_replay_exact']:
        raise ValueError('Raw-source CR form fields or chunk digest sequence differ')


def batch(args):
    repository = args.repository.resolve()
    code_start=sha(Path(__file__))
    outcomes, counts, started = [], Counter(), time.monotonic()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.recipes, 'rt') as stream:
        for line in stream:
            recipe = json.loads(line); begin = time.monotonic()
            try:
                source = (args.source_root or repository) / recipe['source_path']
                output = args.text_cache / (recipe['tdoc'] + '.json') if args.text_cache else None
                report = execute_recipe(repository, recipe, source, output)
                report.pop('actual_chunk_digests')
                report['status'] = 'all_expected_chunks_exact' if report['supported_replay_exact'] else 'raw_fields_or_chunks_differ'
            except Exception as error:
                report = {'tdoc': recipe['tdoc'], 'status': 'error', 'error_type': type(error).__name__, 'error': str(error)}
            report['seconds'] = time.monotonic() - begin
            outcomes.append(report); counts[report['status']] += 1
            args.report.write_bytes(encoded({'complete': False, 'counts': dict(counts), 'outcomes': outcomes}) + b'\n')
            if len(outcomes) % 100 == 0:
                print(json.dumps({'processed':len(outcomes),'counts':dict(counts)}), flush=True)
    result = {'complete': True, 'recipes_sha256': sha(args.recipes), 'outcomes': outcomes, 'counts': dict(counts),
              'seconds': time.monotonic()-started, 'source_root_mode': 'separate_acquired_cache' if args.source_root else 'retained_hash_pinned_derived_DOCX',
              'runtime':runtime(),'runner_sha256_at_start':code_start,'runner_sha256_at_end':sha(Path(__file__)),
              'scope': 'Raw DOCX form-slot extraction and Phase-8 parser/hardening. Source acquisition is recorded separately.'}
    args.report.write_bytes(encoded(result)+b'\n'); print(json.dumps({k:v for k,v in result.items() if k!='outcomes'}))


def bind_targets(args):
    repository = args.repository.resolve()
    chunks = json.loads((repository / f'vectordb/parsed/cr/{args.wg}/{args.wg.lower()}_cr_chunks.json').read_text())['chunks']
    indices = {chunk['chunkId']: index for index, chunk in enumerate(chunks)}
    if len(indices) != len(chunks):
        raise ValueError('Chunk IDs are duplicated')
    if args.output.exists():
        raise ValueError('Bound recipe output exists')
    count = 0
    with gzip.open(args.recipes, 'rt') as inp, args.output.open('xb') as raw, gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as out:
        for line in inp:
            recipe = json.loads(line)
            recipe['target_parsed_path'] = f'vectordb/parsed/cr/{args.wg}/{args.wg.lower()}_cr_chunks.json'
            recipe['target_total_chunks'] = len(chunks)
            recipe['target_chunk_indices'] = [indices[chunk['chunkId']] for chunk in recipe['expected_chunks']]
            out.write(encoded(recipe) + b'\n'); count += len(recipe['target_chunk_indices'])
    print(json.dumps({'chunks':count,'sha256':sha(args.output),'bytes':args.output.stat().st_size}))


def assemble(args):
    """Assemble verified local text outputs at original JSON pointer indices."""
    rows, target, total, counts = {}, None, None, Counter()
    with gzip.open(args.recipes, 'rt') as stream:
        for line in stream:
            recipe = json.loads(line)
            current_target = recipe['target_parsed_path']
            if target is not None and target != current_target:
                raise ValueError('Recipes span multiple target files')
            target = current_target
            if total is not None and total != recipe['target_total_chunks']:
                raise ValueError('Recipes disagree on target size')
            total = recipe['target_total_chunks']
            path = args.text_cache / (recipe['tdoc'] + '.json')
            data = json.loads(path.read_text())
            actual = [{'chunkId': c['chunkId'], 'text_sha256': text_sha(c['text'])} for c in data['chunks']]
            if actual != recipe['expected_chunks']:
                raise ValueError('Local chunk cache digest sequence differs')
            if len(recipe['target_chunk_indices']) != len(data['chunks']):
                raise ValueError('Chunk target index and chunk lengths differ')
            for index, chunk in zip(recipe['target_chunk_indices'], data['chunks']):
                if index in rows:
                    raise ValueError('Repeated target index')
                rows[index] = {'chunkId':chunk['chunkId'],'text':chunk['text']}
                counts['chunks'] += 1
            counts['tdocs'] += 1
    if sorted(rows) != list(range(total)):
        raise ValueError('Chunk target indices are incomplete')
    output = args.output_root / target
    if output.exists():
        raise ValueError('Assembly target exists')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded({'chunks':[rows[i] for i in range(len(rows))]}) + b'\n')
    report = {'counts':dict(counts),'logical_text_fields_only':True,'target_path':target,'target_sha256':sha(output),
              'recipes_sha256':sha(args.recipes),'scope':'Original chunk JSON pointers and exact text; index row metadata comes from its frozen frontier.'}
    args.report.write_bytes(encoded(report)+b'\n'); print(json.dumps(report))


def verified_resume_result(repository, recipe, case, text_cache):
    prior=case/'replay.json';output=text_cache/(recipe['tdoc']+'.json')
    if not prior.is_file() or not output.is_file():return None
    saved=json.loads(prior.read_text())
    if saved.get('recipe_sha256')!=sha(case/'recipe.json'):
        raise ValueError('Resume recipe digest differs')
    if not saved.get('supported_replay_exact') or not all(saved.get('raw_field_sha_equal',{}).values()) or sha(output)!=saved.get('local_output_sha256'):
        raise ValueError('Resume parsed cache digest differs')
    if not (case/'acquire.json').is_file() or sha(case/'acquire.json')!=saved.get('acquisition_receipt_sha256'):
        raise ValueError('Resume acquisition receipt digest differs')
    verify_code(repository,tuple(sorted(recipe.get('code_sha256',{}).items())))
    data=json.loads(output.read_text())
    if [{'chunkId':c['chunkId'],'text_sha256':text_sha(c['text'])}for c in data['chunks']]!=recipe['expected_chunks']:
        raise ValueError('Resume target chunk sequence differs')
    saved.update(status='all_expected_chunks_exact',execution_mode='reused_verified_text_cache',
                 prior_replay_receipt_sha256=sha(prior))
    return saved


def acquire_and_parse_case(args, repository, helper, recipe, case, recipe_path, code_start):
    tdoc=recipe['tdoc']
    accepted=[source for source in recipe['sources']if source.get('conversion',{}).get('method')=='native_accepted_uno_export_reopen']
    acquire_recipe=recipe
    if accepted:
        acquire_recipe=json.loads(json.dumps(recipe))
        for source in acquire_recipe['sources']:
            if source.get('conversion',{}).get('method')=='native_accepted_uno_export_reopen':
                source['path']='native_accepted_inputs/'+tdoc+'/'+Path(source['member_chain'][-1]['name']).name
                source['sha256']=source['conversion']['native_sha256'];source.pop('conversion')
        acquisition_path=case/'acquisition_recipe.json';acquisition_path.write_bytes(encoded(acquire_recipe)+b'\n')
    else:acquisition_path=recipe_path
    helper.acquire_tdoc(argparse.Namespace(recipe=acquisition_path,cache=args.cache,output=args.source_root,
                        report=case/'acquire.json',download=args.download,timeout=args.timeout,
                        local_archive_repository=args.local_archive_repository))
    for source in accepted:
        native=args.source_root/'native_accepted_inputs'/tdoc/Path(source['member_chain'][-1]['name']).name
        target=args.source_root/source['path'];target.parent.mkdir(parents=True,exist_ok=True)
        conversion=source['conversion']
        version=subprocess.run(['libreoffice','--version'],check=True,capture_output=True,text=True).stdout.strip()
        if version!=conversion['libreoffice_version']:raise ValueError('Native accepted converter version differs')
        sys.path.insert(0,str(repository/'scripts/tsg/RAN/formal/common'))
        import native_word_conversion
        proof=native_word_conversion.recover_native_word(native,target)
        if proof['acceptedRenderedText']['normalizedTextSha256']!=conversion['accepted_rendered_normalized_sha256']:
            raise ValueError('Native accepted rendered digest differs')
        proof.update(native_sha256=conversion['native_sha256'],output_sha256=sha(target),
                     snapshot_docx_container_sha_equal=sha(target)==source['sha256'])
        target.with_name(target.name+'.conversion.json').write_bytes(encoded(proof)+b'\n')
        (case/'native_accepted_conversion.json').write_bytes(encoded(proof)+b'\n')
    result = execute_recipe(repository, recipe, args.source_root / recipe['source_path'], args.text_cache/(tdoc+'.json'))
    result.pop('actual_chunk_digests')
    result['status'] = 'all_expected_chunks_exact' if result['supported_replay_exact'] else 'raw_fields_or_chunks_differ'
    result.update(recipe_sha256=sha(recipe_path),acquisition_receipt_sha256=sha(case/'acquire.json'),execution_mode='acquired_and_parsed',runner_sha256=code_start)
    (case/'replay.json').write_bytes(encoded(result)+b'\n')
    return result


def acquired_batch(args):
    """Stream source acquisition and replay outcomes with checked per-case resume."""
    repository=args.repository.resolve();helper=exporter(repository)
    started=time.monotonic();counts=Counter();modes=Counter();code_start=sha(Path(__file__))
    processed=0;actual_chunks=0
    args.report.parent.mkdir(parents=True,exist_ok=True);args.receipt_dir.mkdir(parents=True,exist_ok=True)
    stream_path=args.report.with_name(args.report.stem+'.attempt-'+str(time.time_ns())+'.outcomes.jsonl')
    base={'format':'spectra-cr-acquired-summary-v1','outcomes_jsonl':stream_path.name,
          'recipes_sha256':sha(args.recipes),'network_enabled':args.download,'resume_enabled':args.resume,
          'runner_sha256_at_start':code_start,
          'scope':'Each case records actual acquisition and parsing or reuse of a verified prior local cache; raw form-field and chunk-sequence gates must both pass.'}
    def summary(complete):
        data=dict(base,complete=complete,processed=processed,counts=dict(counts),execution_modes=dict(modes),
                  actual_chunks=actual_chunks,seconds=time.monotonic()-started)
        if complete:data.update(outcomes_jsonl_sha256=sha(stream_path),runner_sha256_at_end=sha(Path(__file__)),runtime=runtime())
        args.report.write_bytes(encoded(data)+b'\n')
    with gzip.open(args.recipes,'rt')as recipes,stream_path.open('xb')as outcomes:
        for line in recipes:
            recipe=json.loads(line);tdoc=recipe['tdoc'];begin=time.monotonic()
            case=args.receipt_dir/tdoc;case.mkdir(exist_ok=True);recipe_path=case/'recipe.json'
            try:
                content=encoded(recipe)+b'\n'
                if recipe_path.exists() and recipe_path.read_bytes()!=content:raise ValueError('Existing case recipe differs')
                recipe_path.write_bytes(content)
                result=verified_resume_result(repository,recipe,case,args.text_cache)if args.resume else None
                if result is None:result=acquire_and_parse_case(args,repository,helper,recipe,case,recipe_path,code_start)
            except Exception as error:
                result={'tdoc':tdoc,'status':'error','error_type':type(error).__name__,'error':str(error),'execution_mode':'attempt_error'}
            result['seconds']=time.monotonic()-begin;processed+=1;counts[result['status']]+=1
            modes[result.get('execution_mode','unknown')]+=1;actual_chunks+=result.get('actual_chunk_count',0)
            outcomes.write(encoded(result)+b'\n');outcomes.flush();summary(False)
            print(json.dumps({'processed':processed,'counts':dict(counts),'tdoc':tdoc,'status':result['status'],'execution_mode':result.get('execution_mode')}),flush=True)
    summary(True)
    if counts.get('error',0) or counts.get('raw_fields_or_chunks_differ',0):
        raise ValueError('One or more acquisition/replay cases failed; inspect the streamed receipt')


def repair_sources(args):
    """Use whole-file source identity when the selected pack copy differs."""
    repository=args.repository.resolve();helper=exporter(repository)
    by_member,by_sha,by_path={},{},{}
    for inventory in [args.source_inventory]+args.additional_source_inventory:
        with gzip.open(inventory,'rt')as stream:
            for line in stream:
                row=json.loads(line);by_sha[row['archive_sha256']]=row
                for path in row['paths']:by_path[path]=row;by_path[path.lower()]=row
                for member in row.get('members',[]):
                    if member.get('sha256'):
                        by_member.setdefault(member['sha256'],[]).append((row,member))
    if args.url_inventory:
        with gzip.open(args.url_inventory,'rt')as stream:
            for line in stream:
                row=json.loads(line)
                if row['sha256']in by_sha:
                    target=by_sha[row['sha256']];target['official_urls']=sorted(set(target['official_urls'])|set(row['candidateUrls']))
    counts,gaps,changes=Counter(),[],[]
    supported=('exact_archive_member','native_doc_conversion_recipe','exact_source_file','native_doc_accepted_conversion_recipe')
    native_ledgers={}
    if args.output.exists():raise ValueError('Repaired recipe output exists')
    with gzip.open(args.recipes,'rt')as inp,args.output.open('xb')as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6)as out:
        for line in inp:
            row=json.loads(line)
            for index,source in enumerate(row.get('sources',[])):
                if source['source_status']in supported:continue
                exact_chain=None
                if source.get('archive_paths'):
                    try:exact_chain=helper.zip_member_chain(repository/source['archive_paths'][0],source['sha256'])
                    except Exception:pass
                if exact_chain:
                    replacement={k:v for k,v in source.items()if k not in ('mapping_error','document_candidates','conversion')}
                    replacement.update(source_status='exact_archive_member',member_chain=exact_chain,
                                       source_identity_basis='Exact complete DOCX SHA through selected ZIP member chain; unrelated unsupported nested archives excluded')
                    row['sources'][index]=replacement
                    changes.append({'tdoc':row['tdoc'],'source':source['path'],'archive_sha256':source['archive_sha256']})
                    continue
                matches=by_member.get(source['sha256'],[])
                if matches:
                    archive,member=sorted(matches,key=lambda item:item[0]['paths'][0])[0]
                    replacement={'path':source['path'],'sha256':source['sha256'],'source_status':'exact_archive_member',
                                 'archive_paths':archive['paths'],'archive_sha256':archive['archive_sha256'],
                                 'official_urls':archive['official_urls'],'member_chain':[{'name':member['path'],'sha256':member['sha256'],'bytes':member['bytes']}],
                                 'source_identity_basis':'Exact complete DOCX SHA in retained alternate official source archive',
                                 'previous_source_mapping':{k:v for k,v in source.items()if k in ('archive_paths','archive_sha256','source_status')}}
                    row['sources'][index]=replacement;changes.append({'tdoc':row['tdoc'],'source':source['path'],'archive_sha256':archive['archive_sha256']})
                else:
                    replacement=helper.source_recipe(repository/source['path'],repository,by_path)
                    if replacement['source_status']in supported:
                        row['sources'][index]=replacement;changes.append({'tdoc':row['tdoc'],'source':source['path'],'archive_sha256':replacement['archive_sha256']})
                        continue
                    wg=row['wg']
                    if wg not in native_ledgers:
                        ledger=repository/f'ontology/input/tsg/RAN/formal/meetings/{wg}/tdoc_native_cr_sources.json'
                        native_ledgers[wg]={r['target']:r for r in json.loads(ledger.read_text()).get('records',[])}if ledger.exists()else{}
                    native_row=native_ledgers[wg].get(row['tdoc'],{})
                    accepted=native_row.get('nativeAcceptedView')
                    if accepted and accepted['derivedPath']==source['path'] and accepted['derivedSha256']==source['sha256']:
                        archive=native_row['officialSourceArchive'];inventory=by_sha[archive['sha256']]
                        member=next(m for m in archive['members']if m['sha256']==accepted['nativeSha256'])
                        receipt=accepted['conversionReceipt']
                        replacement={'path':source['path'],'sha256':source['sha256'],'source_status':'native_doc_accepted_conversion_recipe',
                                     'archive_paths':inventory['paths'],'archive_sha256':archive['sha256'],'official_urls':inventory['official_urls'],
                                     'member_chain':[{'name':member['name'],'sha256':member['sha256']}],
                                     'conversion':{'method':'native_accepted_uno_export_reopen','native_sha256':accepted['nativeSha256'],
                                                   'libreoffice_version':receipt['converterVersion'],
                                                   'accepted_rendered_normalized_sha256':receipt['acceptedRenderedText']['normalizedTextSha256']},
                                     'source_identity_basis':'Original nativeAcceptedView ledger; tracked changes accepted by pinned original converter and rendered text digest'}
                        row['sources'][index]=replacement;changes.append({'tdoc':row['tdoc'],'source':source['path'],'archive_sha256':archive['sha256']})
            statuses=[s['source_status']for s in row.get('sources',[])]
            row['source_mapping_status']='all_sources_with_executable_recipe' if statuses and all(s in supported for s in statuses)else'additional_recipe_required'
            row['status']=row['source_mapping_status']
            row.pop('candidate_members',None)
            counts[row['source_mapping_status']]+=1
            for status in statuses:counts[status]+=1
            if row['source_mapping_status']!='all_sources_with_executable_recipe':gaps.append(row['tdoc'])
            out.write(encoded(row)+b'\n')
    report={'counts':dict(counts),'changed_sources':changes,'remaining_tdocs':gaps,'sha256':sha(args.output),'bytes':args.output.stat().st_size,
            'scope':'Exact source mapping and conversion recipes; raw parsing executions have separate receipts.'}
    args.report.write_bytes(encoded(report)+b'\n');print(json.dumps(report))


def main():
    p = argparse.ArgumentParser(description=__doc__); subs = p.add_subparsers(dest='command', required=True)
    q = subs.add_parser('prepare'); q.add_argument('--repository', type=Path, default=Path('.')); q.add_argument('--wg', default='RAN3'); q.add_argument('--tdoc'); q.add_argument('--frontier',type=Path); q.add_argument('--output', type=Path, required=True)
    q = subs.add_parser('replay'); q.add_argument('--repository', type=Path, default=Path('.')); q.add_argument('--recipe', type=Path, required=True); q.add_argument('--source', type=Path); q.add_argument('--report', type=Path, required=True); q.add_argument('--output', type=Path)
    q = subs.add_parser('inventory'); q.add_argument('--repository', type=Path, default=Path('.')); q.add_argument('--wg', default='RAN3'); q.add_argument('--frontier',type=Path); q.add_argument('--resume-prefix',type=Path); q.add_argument('--source-inventory', type=Path, required=True); q.add_argument('--url-inventory', type=Path); q.add_argument('--output', type=Path, required=True); q.add_argument('--report', type=Path, required=True)
    q = subs.add_parser('batch'); q.add_argument('--repository', type=Path, default=Path('.')); q.add_argument('--recipes', type=Path, required=True); q.add_argument('--source-root', type=Path); q.add_argument('--text-cache', type=Path); q.add_argument('--report', type=Path, required=True)
    q = subs.add_parser('bind-targets'); q.add_argument('--repository', type=Path, default=Path('.')); q.add_argument('--wg', default='RAN3'); q.add_argument('--recipes', type=Path, required=True); q.add_argument('--output', type=Path, required=True); q.set_defaults(function=bind_targets)
    q = subs.add_parser('assemble'); q.add_argument('--recipes', type=Path, required=True); q.add_argument('--text-cache', type=Path, required=True); q.add_argument('--output-root', type=Path, required=True); q.add_argument('--report', type=Path, required=True)
    q = subs.add_parser('acquired-batch'); q.add_argument('--repository',type=Path,default=Path('.')); q.add_argument('--recipes',type=Path,required=True); q.add_argument('--cache',type=Path,required=True); q.add_argument('--source-root',type=Path,required=True); q.add_argument('--text-cache',type=Path,required=True); q.add_argument('--receipt-dir',type=Path,required=True); q.add_argument('--report',type=Path,required=True); q.add_argument('--download',action='store_true'); q.add_argument('--timeout',type=int,default=60); q.add_argument('--local-archive-repository',type=Path); q.add_argument('--resume',action='store_true'); q.set_defaults(function=acquired_batch)
    q=subs.add_parser('repair-sources');q.add_argument('--repository',type=Path,default=Path('.'));q.add_argument('--recipes',type=Path,required=True);q.add_argument('--source-inventory',type=Path,required=True);q.add_argument('--additional-source-inventory',type=Path,action='append',default=[]);q.add_argument('--url-inventory',type=Path);q.add_argument('--output',type=Path,required=True);q.add_argument('--report',type=Path,required=True);q.set_defaults(function=repair_sources)
    args = p.parse_args(); (args.function if hasattr(args,'function') else globals()[args.command])(args)


if __name__ == '__main__':
    main()
