#!/usr/bin/env python3
"""tdoc_supplement_vectors.py — 원문 보충 문서의 검색 산출물을 재현한다.

Spec: docs/tsg/RAN/formal/RAN5/phase-6/design-spec/tdoc_vectordb_specs(Tdoc).md §3
Ontology: source-validated CR/Tdoc identities and document bodies.
Cycle: source supplement → existing Phase-6/8 parsers → guarded vector projection.
배경: 문서 목록 밖에 있는 실제 최종 CR도 동일한 생산 파서로 검색한다.
사용: python3 -B scripts/tsg/RAN/formal/common/tdoc_supplement_vectors.py --wg RAN5 [--native-only] [--apply]
LLM 호출: 없음. 새 벡터는 컬렉션에 선언된 로컬 인코더를 사용한다.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts/common'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import axis, review_artifacts  # noqa: E402
from common.service_endpoints import QDRANT_URL
from common.atomic_io import write_text_atomic  # noqa: E402
from common.exception_notes import add_exception_note  # noqa: E402
from common.embedding_registry import embed_local, encoder_for, force_hf_offline  # noqa: E402
from common.gpu_duty import rested  # noqa: E402
from common.chunker import enforce_hard_max, HARD_MAX_DEFAULT  # noqa: E402
from tdoc_source_supplements import validated_records  # noqa: E402


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for part in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(part)
    return digest.hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def extra_tdoc_tasks(wg, tasks, output_base, selected_meetings, *, resume=False):
    """선택한 회의의 보충 원문을 일반 parser task와 같은 형태로 추가한다."""
    rows = validated_records(ROOT, wg, set(selected_meetings))
    claimed = {(task[4], task[1]) for task in tasks}
    for row in rows:
        if Path(row['path']).suffix.lower() not in {'.docx', '.docm'}:
            # Phase-6 source coverage is Word. Native spreadsheet/presentation
            # identity is retained in Phase-1 without pretending its body was parsed.
            continue
        number = meeting_number(wg, row)
        target = row['target']
        if (number, target) in claimed:
            continue
        if resume and (output_base / number / target / 'chunks.json').exists():
            continue
        tasks.append(((ROOT / row['path'],), target, output_base, '', number))
    return tasks


def meeting_number(wg, row):
    """Source spelling is resolved through actual Phase-1 meeting identities."""
    path = ROOT / f'ontology/output/tsg/RAN/formal/instances/phase-1/{wg}/meetings.jsonld'
    nodes = json.loads(path.read_text())['@graph']
    names = {n['tdoc:meetingNumber'] for n in nodes}
    identity = row['sourceIdentity']
    for key in ('meetingNumber', 'canonicalMeetingNumber'):
        if identity[key] in names:
            return identity[key]
    match = re.fullmatch(rf'{wg}#(\d+)(.*)', identity['canonicalMeetingNumber'])
    aliases = [name for name in names if name in {f'{wg}#{match[1]}', f'{wg}#{match[1]}-e'}]
    if len(aliases) != 1:
        raise ValueError(f'Ambiguous source supplement meeting: {row["target"]}')
    return aliases[0]


def native_rows(rows):
    """Select only the source-validated native supplement formats in Spec §2.6."""
    selected = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('path'), str):
            raise ValueError('Invalid native supplement source coordinate')
        suffix = Path(row['path']).suffix.lower()
        if suffix in {'.docx', '.docm'}:
            continue
        view = row.get('nativeView')
        if (row.get('kind') != 'document' or suffix not in {'.pptx', '.xlsx', '.xls'}
                or (suffix == '.xls' and (not isinstance(view, dict)
                    or not isinstance(view.get('path'), str)
                    or Path(view['path']).suffix.lower() != '.xlsx'))
                or (suffix != '.xls' and view is not None)):
            raise ValueError('Unsupported native supplement source: ' + row['target'])
        selected.append(row)
    if not selected:
        raise ValueError('No validated native source supplements')
    return selected


def native_content(lib, wg, row):
    """Project checked native units and their locators into the Phase-6 schema."""
    from tdoc_source_supplements import validate_record
    from tdoc_document_supplements import native_blocks
    from tdoc_body_source_metadata import validate_source_selection
    native_rows([row])
    validate_record(ROOT, row)
    validate_source_selection(ROOT, wg, 'tdoc', row['target'], [ROOT / row['path']])
    blocks = native_blocks(ROOT, row)
    if Path(row['path']).suffix.lower() == '.pptx':
        if (not isinstance(blocks, dict) or not blocks
                or any(not isinstance(k, str) or re.fullmatch(r'presentation slide [1-9]\d*', k) is None
                       or not isinstance(v, str) for k, v in blocks.items())
                or not any(v.strip() for v in blocks.values())):
            raise ValueError('Invalid primary presentation source units')
        # Primary native identity quotes keep their original getter contract.
        # Search text separately preserves editable math and explicit run roles.
        from pptx_search_text import search_blocks
        search = search_blocks(ROOT / row['path'])
        if list(search) != list(blocks):
            raise ValueError('Presentation source/search slide locators differ')
        blocks = search
    if not isinstance(blocks, dict) or not blocks:
        raise ValueError('Native supplement produced no body: ' + row['target'])
    groups = {}
    for index, (locator, text) in enumerate(blocks.items()):
        if not isinstance(locator, str) or not locator or not isinstance(text, str):
            raise ValueError('Invalid native supplement body unit: ' + row['target'])
        pattern = (r'presentation slide [1-9]\d*' if Path(row['path']).suffix.lower() == '.pptx'
                   else r'workbook sheet .+ cell [A-Z]+[1-9]\d*')
        if re.fullmatch(pattern, locator) is None:
            raise ValueError('Invalid native supplement locator: ' + row['target'])
        # Slides and worksheet cells retain their native order and coordinates.
        group = locator.rsplit(' cell ', 1)[0] if locator.startswith('workbook sheet ') else locator
        groups.setdefault(group, []).append((index, locator, text))
    sections = []
    for title, units in groups.items():
        text = '\n'.join(f'[{locator}] {body}' for _, locator, body in units if body.strip())
        if text:
            sections.append(lib.Section(title=title, level=1, content=text,
                                        start_idx=units[0][0], end_idx=units[-1][0] + 1))
    if not sections:
        raise ValueError('Native supplement produced no nonempty body: ' + row['target'])
    return lib.ParsedContent(tdoc_number=row['target'], doc_type=row['sourceIdentity']['type'],
                             sections=sections, paragraph_count=len(blocks))


def native_metadata(resolver, wg, rows):
    """Bind native source identities to unique retained and live Phase-1 facts."""
    base = ROOT / f'ontology/output/tsg/RAN/formal/instances/phase-1/{wg}'
    documents = json.loads((base / 'tdocs.jsonld').read_text())['@graph']
    meetings = json.loads((base / 'meetings.jsonld').read_text())['@graph']
    targets = [row['target'] for row in rows]
    if len(set(targets)) != len(targets):
        raise ValueError('Duplicate native supplement document identity')
    with resolver._driver.session() as session:
        live = session.run(
            'MATCH (t:Tdoc) WHERE t.tdocNumber IN $targets '
            'OPTIONAL MATCH (t)-[:PRESENTED_AT]->(m:Meeting) '
            'RETURN t.tdocNumber AS target, t.title AS title, t.type AS type, '
            'collect(DISTINCT m.meetingNumber) AS meetings, '
            'collect(DISTINCT elementId(m)) AS meetingNodes, elementId(t) AS element',
            targets=targets).data()
    if any(item.get('target') not in targets for item in live):
        raise ValueError('Unexpected live native supplement document identity')
    result = {}
    for row in rows:
        target, identity = row['target'], row['sourceIdentity']
        meeting = meeting_number(wg, row)
        retained = [node for node in documents if node.get('tdoc:tdocNumber') == target]
        observed = [node for node in live if node.get('target') == target]
        if len(retained) != 1 or len(observed) != 1:
            raise ValueError('Native supplement requires unique Phase-1 document: ' + target)
        node, actual = retained[0], observed[0]
        presented = [item for item in meetings if item.get('@id') == node.get('presentedAt')]
        if (identity.get('tdocNumber') != target or not identity.get('title')
                or node.get('tdoc:title') != identity['title']
                or node.get('tdoc:type') != identity['type']
                or len(presented) != 1 or presented[0].get('tdoc:meetingNumber') != meeting
                or presented[0].get('tdoc:workingGroup') != wg
                or actual.get('title') != identity['title'] or actual.get('type') != identity['type']
                or actual.get('meetings') != [meeting]
                or len(actual.get('meetingNodes', [])) != 1):
            raise ValueError('Native supplement Phase-1 source identity differs: ' + target)
        metadata = resolver.resolve_metadata(target, meeting)
        if (metadata.get('title') != identity['title'] or metadata.get('type') != identity['type']
                or metadata.get('tdocNumber') != target or metadata.get('meetingId') != meeting):
            raise ValueError('Native supplement live metadata changed: ' + target)
        result[target] = metadata
    return result


def parse_cr_supplements(parser, rows, existing_tdocs=()):
    """실제 CR 표지를 검증하고 기존 Phase-8 본문·청킹 경로를 재사용한다."""
    result = []
    existing_tdocs = set(existing_tdocs)
    for row in rows:
        if row.get('kind') == 'document':
            continue
        if row['target'] in existing_tdocs:
            continue
        identity = row['sourceIdentity']
        form, proposal, error, _ = parser._read_cr(str(ROOT / row['path']))
        if error or proposal is None:
            raise ValueError(f"Source supplement parse failed: {row['target']}: {error}")
        form.tdoc_number = row['target']
        # The general parser uses filename hints for spec/release. These sources
        # have an independently validated own cover, including files without hints.
        if form.category != identity['category']:
            raise ValueError(f"Parsed CR form differs from validated cover: {row['target']}")
        form.spec_number = identity['specNumber']
        form.release = identity['release']
        metadata = dict(meeting=meeting_number('RAN5', row), source=identity['sourceToWG'],
                        work_item=identity['workItem'], title=identity['title'])
        revision = str(identity['crRevision'])
        cr_label = f"CR{identity['crNumber']}" + (f'r{revision}' if revision not in ('', '-', '0') else '')
        chunks = parser.generate_cr_chunks(form, *proposal, phase4_meta=metadata, cr_number=cr_label)
        if not chunks:
            raise ValueError(f"Source supplement produced no CR chunks: {row['target']}")
        result.extend(chunks)
    return result


CR_FIELDS = {'chunkId': 'chunk_id', 'tdocNumber': 'tdoc_number', 'chunkType': 'chunk_type',
             'sectionTitle': 'section_title', 'text': 'content', 'tokenCount': 'token_count',
             'strategy': 'strategy', 'specNumber': 'spec_number', 'release': 'release',
             'category': 'category', 'clausesAffected': 'clauses_affected', 'hasTables': 'has_tables',
             'hasFigures': 'has_figures', 'crNumber': 'cr_number', 'crPackId': 'cr_pack_id',
             'meeting': 'meeting', 'tsgMeeting': 'tsg_meeting', 'source': 'source', 'title': 'title',
             'workItem': 'work_item', 'sectionIds': 'section_ids', 'chunkSectionId': 'chunk_section_id',
             'chunkIndex': 'chunk_index', 'totalChunks': 'total_chunks', 'bodySnippet': 'body_snippet',
             '_crDelProof': '_crDelProof'}


def serialize_cr(chunk):
    return {key: getattr(chunk, attribute) for key, attribute in CR_FIELDS.items()}


def tdoc_payloads(tdoc, meeting, metadata, chunks):
    return [dict(chunkId=c.get('chunkId', f"{tdoc}-{c['chunkIndex']:03d}"), tdocNumber=tdoc,
                 meetingId=meeting, type=metadata['type'], chunkIndex=c['chunkIndex'],
                 sectionTitle=c.get('sectionTitle', ''), content=c['content'],
                 tokenCount=c['tokenCount'], source=metadata['source'], release=metadata['release'],
                 agendaItem=metadata.get('agendaItem', ''), title=metadata['title'],
                 **({'chunkType': c['chunkType']} if 'chunkType' in c else {})) for c in chunks]


def source_fence(wg, rows):
    manifest = ROOT / f'ontology/input/tsg/RAN/formal/meetings/{wg}/tdoc_source_supplements.json'
    canonical = ROOT / f'ontology/output/tsg/RAN/formal/instances/phase-1/{wg}/tdocs.jsonld'
    base = ROOT / f'scripts/tsg/RAN/formal/{wg}'
    files = {manifest, canonical, canonical.with_name('meetings.jsonld'), Path(__file__).resolve(),
             Path(__file__).with_name('tdoc_source_supplements.py'),
             Path(__file__).with_name('tdoc_source_metadata.py'),
             Path(__file__).with_name('tdoc_source_identity_corrections.py'),
             Path(__file__).with_name('tdoc_source_classification.py'),
             Path(__file__).with_name('tdoc_classification_views.py'),
             Path(__file__).with_name('tdoc_document_supplements.py'),
             Path(__file__).with_name('pptx_search_text.py'),
             Path(__file__).with_name('docx_text.py'),
             Path(__file__).with_name('symbol_fonts.py'),
             Path(__file__).with_name('tdoc_body_source_metadata.py'),
             base / 'phase-6/tdoc-parser/parse_tdoc_lib.py',
             base / 'phase-8/cr-parser/01_parse_cr_chunks.py',
             base / 'phase-6/qdrant/02_load_qdrant.py', base / 'phase-8/qdrant/01_load_qdrant.py',
             ROOT / 'scripts/common/common/chunker.py', ROOT / 'scripts/common/common/embedding_registry.py',
             ROOT / 'scripts/common/common/local_model.py'}
    for row in rows:
        files.add(ROOT / row['path'])
        files.add(ROOT / row['report']['path'])
        files.update(ROOT / item['path'] for item in row['meetingSourceFiles'])
        if row.get('nativeView'):
            files.add(ROOT / row['nativeView']['path'])
    from tdoc_source_identity_corrections import source_inputs
    # Phase-8 also consumes adjudicated identities. Pin that dependency and its
    # original evidence rather than only the immediate parser file.
    files.update(ROOT / path for path in source_inputs(ROOT, wg, {meeting_number(wg, row) for row in rows}))
    from tdoc_source_classification import source_inputs as classification_source_inputs
    files.update(ROOT / path for path in classification_source_inputs(ROOT, wg, None))
    from tdoc_body_source_metadata import source_inputs as body_source_inputs
    files.update(ROOT / path for path in body_source_inputs(ROOT, wg))
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(files)}


def backup_file(path, directory):
    prefix = hashlib.sha256(str(path.relative_to(ROOT)).encode()).hexdigest() + '.'
    fd, name = tempfile.mkstemp(prefix=prefix, suffix='.gz', dir=directory)
    dest = Path(name)
    digest = hashlib.sha256()
    try:
        with os.fdopen(fd, 'wb') as raw:
            with path.open('rb') as source, gzip.GzipFile(fileobj=raw, mode='wb') as output:
                for block in iter(lambda: source.read(1024 * 1024), b''):
                    digest.update(block)
                    output.write(block)
            raw.flush()
            os.fsync(raw.fileno())
        return dict(path=str(path.relative_to(ROOT)), backup=str(dest.relative_to(ROOT)), sha256=digest.hexdigest(),
                    backupSha256=sha(dest))
    except BaseException:
        dest.unlink(missing_ok=True)
        raise


def append_cr_artifact(path, chunks, run_dir, *, provenance_field='sourceSupplements'):
    """선택한 문서만 기존 원자적 JSON 산출물에 추가한다. 기존 청크는 보존한다."""
    import json_stream
    backup = backup_file(path, run_dir)
    snapshot = ROOT / backup['backup']
    keep_snapshot = False
    try:
        old_sha = backup['sha256']
        wanted = {c['tdocNumber'] for c in chunks}
        current = Counter()
        existing_bodies = {}
        with gzip.open(snapshot, 'rt', encoding='utf-8') as source:
            for chunk in json_stream.iter_array(source, 'chunks'):
                if chunk['tdocNumber'] in wanted:
                    current[chunk['tdocNumber']] += 1
                    if chunk['chunkId'] in existing_bodies:
                        raise ValueError('Duplicate source supplement identity in the CR artifact')
                    existing_bodies[chunk['chunkId']] = chunk['text']
        expected_bodies = {c['chunkId']: c['text'] for c in chunks if c['tdocNumber'] in current}
        if existing_bodies != expected_bodies:
            raise ValueError('Occupied CR artifact differs from the checked source projection')
        additions = [c for c in chunks if c['tdocNumber'] not in current]
        if not additions:
            return None
        with gzip.open(snapshot, 'rt', encoding='utf-8') as source:
            reader = json_stream._Reader(source)
            reader.expect('{')
            if reader.value() != 'metadata':
                raise ValueError('CR artifact metadata must precede its chunk array')
            reader.expect(':')
            metadata = reader.value()
        if provenance_field not in {'sourceSupplements', 'sourceClassifications', 'sourceRecoveredBodies'}:
            raise ValueError('Unsupported source artifact provenance field')
        camel = 'totalChunks' in metadata
        count_key = 'totalChunks' if camel else 'total_chunks'
        file_key = 'totalFiles' if camel else 'total_cr_files'
        strategy_key = 'strategyDistribution' if camel else 'strategy_distribution'
        if count_key not in metadata or file_key not in metadata or strategy_key not in metadata:
            raise ValueError('Unknown CR artifact metadata count contract')
        metadata[count_key] += len(additions)
        added_targets = sorted({c['tdocNumber'] for c in additions})
        metadata[provenance_field] = sorted(set(metadata.get(provenance_field, [])) | set(added_targets))
        if camel:
            metadata['processed'] += len(added_targets)
        else:
            metadata['header_chunks'] += sum(c.get('chunkType') == 'header' for c in additions)
            metadata['body_chunks'] += sum(c.get('chunkType') == 'body' for c in additions)
        metadata[file_key] += len(added_targets)
        for target in added_targets:
            strategy = next(c['strategy'] for c in additions if c['tdocNumber'] == target)
            distribution = metadata[strategy_key]
            distribution[strategy] = distribution.get(strategy, 0) + 1
        journal = snapshot.with_suffix('.journal.json')
        write_text_atomic(journal, json.dumps(dict(preimage=backup,
                          additions=added_targets), ensure_ascii=False, indent=2))
        # Once an apply intent exists, retain its exact preimage for recovery.
        keep_snapshot = True
        fd, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                with gzip.open(snapshot, 'rt', encoding='utf-8') as source:
                    reader = json_stream._Reader(source); reader.expect('{')
                    handle.write('{'); first_key = True; seen_keys = set()
                    while reader.peek() != '}':
                        if not first_key: reader.expect(',')
                        key = reader.value(); reader.expect(':')
                        if not isinstance(key, str) or key in seen_keys:
                            raise ValueError('Invalid or duplicate CR artifact top-level key')
                        seen_keys.add(key)
                        if not first_key: handle.write(',')
                        first_key = False
                        json.dump(key, handle); handle.write(':')
                        if key != 'chunks':
                            value = reader.value()
                            json.dump(metadata if key == 'metadata' else value, handle, ensure_ascii=False)
                            continue
                        reader.expect('['); handle.write('[\n'); first = True
                        while reader.peek() != ']':
                            if not first: reader.expect(','); handle.write(',\n')
                            json.dump(reader.value(), handle, ensure_ascii=False, separators=(',', ':'))
                            first = False
                        reader.expect(']')
                        for chunk in additions:
                            if not first: handle.write(',\n')
                            json.dump(chunk, handle, ensure_ascii=False, separators=(',', ':')); first = False
                        handle.write('\n]')
                    reader.expect('}')
                    if reader.peek() or not {'metadata', 'chunks'} <= seen_keys:
                        raise ValueError('Incomplete/trailing CR artifact JSON')
                    handle.write('}\n')
                handle.flush()
                os.fsync(handle.fileno())
            if sha(path) != old_sha or sha(snapshot) != backup['backupSha256']:
                raise RuntimeError('CR artifact changed before atomic append')
            os.replace(name, path)
        finally:
            Path(name).unlink(missing_ok=True)
        return dict(**backup, addedChunks=len(additions), afterSha256=sha(path))

    finally:
        if not keep_snapshot:
            snapshot.unlink(missing_ok=True)


def _note_secondary_error(primary, message):
    """정리 중 추가 오류를 기록하고 원래 예외를 유지한다(Python 3.10 포함)."""
    add_exception_note(primary, message)


def reconcile(wg, *, apply=False, native_only=False):
    from qdrant_client import QdrantClient, models
    from common.resolution_vectors import valid_vector
    rows = validated_records(ROOT, wg)
    if not rows:
        raise ValueError(f'No validated source supplements for {wg}')
    if native_only:
        rows = native_rows(rows)
    before_fence = source_fence(wg, rows)
    base = ROOT / f'scripts/tsg/RAN/formal/{wg}'
    lib = load_module(base / 'phase-6/tdoc-parser/parse_tdoc_lib.py', f'_supp_{wg}_tdoc')
    cr = None if native_only else load_module(base / 'phase-8/cr-parser/01_parse_cr_chunks.py', f'_supp_{wg}_cr')
    tloader = load_module(base / 'phase-6/qdrant/02_load_qdrant.py', f'_supp_{wg}_tdoc_loader')
    cloader = None if native_only else load_module(base / 'phase-8/qdrant/01_load_qdrant.py', f'_supp_{wg}_cr_loader')
    resolver = lib.MetadataResolver(neo4j_uri=axis.bolt_uri(wg), wg=wg)
    parsed = []
    t_payloads = []
    try:
        resolver.connect()
        if not resolver._connected:
            raise RuntimeError('Source supplement requires live metadata')
        checked_metadata = native_metadata(resolver, wg, rows) if native_only else None
        for row in rows:
            if not native_only and Path(row['path']).suffix.lower() not in {'.docx', '.docm'}:
                continue
            target, meeting = row['target'], meeting_number(wg, row)
            metadata = checked_metadata[target] if native_only else resolver.resolve_metadata(target, meeting)
            expected_type = row['sourceIdentity'].get('type', 'CR')
            if metadata['type'] != expected_type or not metadata['title']:
                raise ValueError(f'Source supplement missing canonical live document: {target}')
            content = native_content(lib, wg, row) if native_only else lib.parse_documents([ROOT / row['path']], target)
            chunks = enforce_hard_max(lib.ChunkEngine().chunk_sections(content.sections, tdoc_number=target),
                                      hard_max=HARD_MAX_DEFAULT)
            if not chunks:
                raise ValueError(f'Source supplement produced no Tdoc chunks: {target}')
            parsed.append((content, chunks, metadata, meeting))
            t_payloads.extend(tdoc_payloads(target, meeting, metadata, chunks))
    finally:
        primary_error = sys.exc_info()[1]
        try:
            resolver.close()
        except BaseException as close_error:
            if primary_error is None:
                raise
            _note_secondary_error(primary_error, f"Metadata resolver close also failed: {type(close_error).__name__}: {close_error}")
    cr_payloads = [] if native_only else cr._harden_per_cr([serialize_cr(c) for c in parse_cr_supplements(cr, rows)])
    client = QdrantClient(url=QDRANT_URL, timeout=120)
    try:
        plans = []
        targets = [r['target'] for r in rows]
        collections = [(f'{wg.lower()}_tdoc_chunks', t_payloads, tloader, 'content')]
        if not native_only:
            collections.append((f'{wg.lower()}_cr_chunks', cr_payloads, cloader, 'text'))
        for name, payloads, loader, text_key in collections:
            expected = {}
            for payload in payloads:
                pid = (loader.generate_point_id(payload['tdocNumber'], payload['chunkIndex'])
                       if text_key == 'content' else loader.generate_point_id(payload['chunkId']))
                if pid in expected or not payload[text_key].strip():
                    raise ValueError(f'Invalid supplement point identity/body: {name}/{pid}')
                expected[pid] = payload
            filt = models.Filter(must=[models.FieldCondition(key='tdocNumber', match=models.MatchAny(any=targets))])
            actual, offset, seen_offsets = {}, None, set()
            while True:
                points, offset = client.scroll(name, scroll_filter=filt, offset=offset, limit=128,
                                               with_payload=True, with_vectors=True)
                actual.update({p.id: p for p in points})
                if offset is None:
                    break
                if offset in seen_offsets:
                    raise ValueError('Supplement point scroll cursor repeated or cycled')
                seen_offsets.add(offset)
            # Existing source-produced CRs retain their original generation and vectors.
            occupied = {p.payload['tdocNumber'] for p in actual.values()}
            for target in occupied:
                old = {pid: p.payload[text_key] for pid, p in actual.items() if p.payload['tdocNumber'] == target}
                new = {pid: p[text_key] for pid, p in expected.items() if p['tdocNumber'] == target}
                if not set(old) <= set(new) or any(text != new[pid] for pid, text in old.items()):
                    raise ValueError(f'Existing source projection differs; reassess before replacement: {name}/{target}')
            additions = {pid: p for pid, p in expected.items() if pid not in actual}
            # A target filter cannot reveal an occupied id with a foreign payload.
            # Reject that collision before creating artifacts, then recheck at upsert.
            ids = list(additions)
            for start in range(0, len(ids), 128):
                if client.retrieve(name, ids[start:start + 128], with_payload=False, with_vectors=False):
                    raise ValueError(f'Supplement point id is occupied outside its source selection: {name}')
            config = client.get_collection(name).config.params.vectors
            encoder = encoder_for(name)
            if config.size != encoder.dim or str(config.distance).casefold() != 'cosine':
                raise ValueError(f'Supplement vector space mismatch: {name}')
            if any(not valid_vector(p.vector, encoder.dim) for p in actual.values()):
                raise ValueError(f'Invalid occupied supplement vector: {name}')
            plans.append((name, expected, actual, additions, encoder, text_key))
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        run_dir = review_artifacts.review_run(ROOT, 'tdoc-source-vectors', stamp, wg)
        run_dir.mkdir(parents=True)
        report = dict(wg=wg, apply=apply, status='planned', sourceFiles=before_fence,
                      collections=[dict(collection=n, expected=len(e), existing=len(a), additions=len(x))
                                   for n, e, a, x, _, _ in plans])
        if native_only:
            report['nativeOnly'] = True
        write_text_atomic(run_dir / 'status.json', json.dumps(report, ensure_ascii=False, indent=2))
        if not apply:
            return report
        # All source/identity/space/occupied-point checks precede the first artifact or vector mutation.
        current_rows = validated_records(ROOT, wg)
        if source_fence(wg, native_rows(current_rows) if native_only else current_rows) != before_fence:
            raise RuntimeError('Source supplement generation changed before apply')
        artifact_preimages = []
        report['newArtifacts'] = [f'vectordb/parsed/tdocs/{wg}/{meeting}/{content.tdoc_number}'
                                  for content, _, _, meeting in parsed]
        write_text_atomic(run_dir / 'status.json', json.dumps(report, ensure_ascii=False, indent=2))
        existing_artifacts = set()
        row_by_target = {row['target']: row for row in rows}
        markers = {}
        for content, chunks, metadata, meeting in parsed:
            output = ROOT / f'vectordb/parsed/tdocs/{wg}/{meeting}/{content.tdoc_number}'
            row = row_by_target[content.tdoc_number]
            marker = dict(sourcePath=row['path'], sourceSha256=row['sha256'])
            markers[content.tdoc_number] = marker
            if output.exists():
                chunks_file = output / 'chunks.json'
                if chunks_file.exists():
                    document = json.loads(chunks_file.read_text())
                    if document['metadata'] != metadata or document['chunks'] != chunks:
                        raise ValueError(f'Occupied supplement Tdoc artifact requires review: {output.relative_to(ROOT)}')
                    existing_artifacts.add(content.tdoc_number)
                elif any(output.iterdir()):
                    marker_path = output / 'source_supplement.json'
                    if not marker_path.exists() or json.loads(marker_path.read_text()) != marker:
                        raise ValueError(f'Unidentified partial supplement artifact: {output.relative_to(ROOT)}')
        for content, chunks, metadata, meeting in parsed:
            if content.tdoc_number not in existing_artifacts:
                output = ROOT / f'vectordb/parsed/tdocs/{wg}/{meeting}/{content.tdoc_number}'
                output.mkdir(parents=True, exist_ok=True)
                write_text_atomic(output / 'source_supplement.json', json.dumps(markers[content.tdoc_number]))
                lib.OutputGenerator(ROOT / f'vectordb/parsed/tdocs/{wg}').generate(content, chunks, metadata, meeting)
        cr_path = ROOT / f'vectordb/parsed/cr/{wg}/{wg.lower()}_cr_chunks.json'
        entry = None if native_only else append_cr_artifact(cr_path, cr_payloads, run_dir)
        if entry:
            artifact_preimages.append(entry)
        report['artifactPreimages'] = artifact_preimages
        report['newPointIds'] = {n: sorted(x) for n, _, _, x, _, _ in plans}
        write_text_atomic(run_dir / 'status.json', json.dumps(report, ensure_ascii=False, indent=2))
        force_hf_offline()
        written_vectors = {}
        for name, expected, actual, additions, encoder, text_key in plans:
            addition_items = list(additions.items())
            for start in range(0, len(addition_items), 64):
                selected = addition_items[start:start + 64]
                vectors = rested(embed_local, encoder, [p[text_key] for _, p in selected], batch_size=4)
                if len(vectors) != len(selected):
                    raise RuntimeError('Supplement embedding cardinality mismatch')
                if source_fence(wg, rows) != before_fence:
                    raise RuntimeError('Source supplement generation changed during apply')
                for pid, payload in selected:
                    if client.retrieve(name, [pid], with_payload=False, with_vectors=False):
                        raise RuntimeError(f'Supplement point appeared concurrently: {name}/{pid}')
                if any(not valid_vector(v, encoder.dim) for v in vectors):
                    raise ValueError('Invalid supplement embedding')
                client.upsert(name, [models.PointStruct(id=pid, vector=v, payload=p)
                                    for (pid, p), v in zip(selected, vectors)], wait=True)
                written_vectors.update({(name, pid): v for (pid, _), v in zip(selected, vectors)})
            expected_ids = list(expected)
            for start in range(0, len(expected_ids), 128):
                ids = expected_ids[start:start + 128]
                got = {p.id: p for p in client.retrieve(name, ids, with_payload=True, with_vectors=True)}
                if set(got) != set(ids):
                    raise RuntimeError(f'Supplement coverage readback failed: {name}')
                for pid in ids:
                    want = actual[pid].payload if pid in actual else expected[pid]
                    if got[pid].payload != want:
                        raise RuntimeError(f'Supplement payload changed: {name}/{pid}')
                    if pid in actual and got[pid].vector != actual[pid].vector:
                        raise RuntimeError(f'Existing supplement vector changed: {name}/{pid}')
                    if not valid_vector(got[pid].vector, encoder.dim):
                        raise RuntimeError(f'Invalid supplement vector readback: {name}/{pid}')
                    if (name, pid) in written_vectors:
                        vector = written_vectors[name, pid]
                        norm = math.sqrt(sum(v * v for v in vector))
                        # Qdrant stores normalized float32 cosine vectors. Eight
                        # binary32 epsilons cover its normalization/serialization.
                        epsilon = 8 * 2 ** -23
                        if any(not math.isclose(a, b / norm, rel_tol=epsilon, abs_tol=epsilon)
                               for a, b in zip(got[pid].vector, vector)):
                            raise RuntimeError(f'Supplement embedding readback differs: {name}/{pid}')
        current_rows = validated_records(ROOT, wg)
        if source_fence(wg, native_rows(current_rows) if native_only else current_rows) != before_fence:
            raise RuntimeError('Source supplement generation changed after apply')
        report['status'] = 'complete'
        report['newVectorsReadBack'] = len(written_vectors)
        write_text_atomic(run_dir / 'status.json', json.dumps(report, ensure_ascii=False, indent=2))
        return report
    finally:
        primary_error = sys.exc_info()[1]
        try:
            client.close()
        except BaseException as close_error:
            if primary_error is None:
                raise
            _note_secondary_error(primary_error, f"Qdrant client close also failed: {type(close_error).__name__}: {close_error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wg', choices=['RAN5'], required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--native-only', action='store_true',
                        help='Project only validated PPTX/workbook supplements; retain the Word/CR path separately')
    args = parser.parse_args()
    print(json.dumps(reconcile(args.wg, apply=args.apply, native_only=args.native_only), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
