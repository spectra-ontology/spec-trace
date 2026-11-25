#!/usr/bin/env python3
"""ts_source_context_publication.py — publish verified source-qualified TS children.

Spec: chunking_standards.md; source-SHA-bound contextual split plan.
Ontology: keep explicit section identity and actual source edition with excerpts.
Cycle: match source/parent → allocate nested identities → refresh section indices.
배경: 재생성 시에도 검증한 표 문맥과 원문 결속을 같은 경로로 적용한다.
사용: qualify_producer_chunks(chunks, wg, spec, release, source_files, root).
LLM 호출: 없음. No database or encoder calls.
"""
from __future__ import annotations

from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import re

from ts_search_presentation import TAG, source_info
from ts_source_context_split import SourceContextError, sha, normalized, bind_source, split_bound_source


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def body_key(chunk):
    keys = [k for k in ('text', 'content') if isinstance(chunk.get(k), str)]
    if len(keys) != 1:
        raise SourceContextError('one explicit TS body field is required')
    return keys[0]


def nested_children(parent, children, reserved, *, source_bindings, plan_sha):
    """Allocate collision-free standard numeric children of the complete old CID."""
    result, suffix = [], 1
    for index, child in enumerate(children, 1):
        while f"{parent['chunkId']}-{suffix:03d}" in reserved:
            suffix += 1
        cid = f"{parent['chunkId']}-{suffix:03d}"
        reserved.add(cid)
        suffix += 1
        source_info(child['text'])
        if sha(child['text']) != child['textSHA256'] or child['tokens'] > 6500:
            raise SourceContextError('qualified child identity or token budget changed')
        payload = deepcopy(parent)
        payload.update(chunkId=cid, tokenCount=child['tokens'])
        payload[body_key(payload)] = child['text']
        actual_bindings = []
        for binding in source_bindings:
            value = {k: deepcopy(v) for k, v in binding.items() if k != 'childSourceProvenance'}
            if 'childSourceProvenance' in binding:
                provenance = binding['childSourceProvenance'][index - 1]
                if provenance['textSHA256'] != child['textSHA256']:
                    raise SourceContextError('shared source edition child text differs')
                value['childSourceProvenance'] = deepcopy(provenance)
            actual_bindings.append(value)
        payload['sourceContext'] = dict(
            schema='source-qualified-ts-excerpt', parentChunkId=parent['chunkId'],
            planSHA256=plan_sha, childIndex=index, childCount=len(children),
            sourceBindings=actual_bindings, sourceRows=deepcopy(child['sourceRows']),
            sourceIntervals=deepcopy(child['sourceIntervals']),
            corePlainSHA256=child['corePlainSHA256'],
            context=[{k: deepcopy(v) for k, v in unit.items() if k != 'text'}
                     for unit in child['context']])
        result.append(payload)
    return result


def replace_and_reindex(chunks, replacements, *, plan_sha, reserved=None):
    """Replace selected parents; keep all other CIDs and section metadata intact.

    The caller supplies one producer section-group list. Explicit sectionId,
    rather than a suffix heuristic, defines the index unit. A shared set can
    reserve identities across every group/file in the same WG collection.
    """
    reserved = set(c['chunkId'] for c in chunks) if reserved is None else reserved
    if len({c['chunkId'] for c in chunks}) != len(chunks):
        raise SourceContextError('duplicate input chunk identity')
    touched = {c['sectionId'] for c in chunks if c['chunkId'] in replacements}
    bases = {sid: min(c['chunkIndex'] for c in chunks if c['sectionId'] == sid)
             for sid in touched}
    output, seen = [], set()
    for parent in chunks:
        record = replacements.get(parent['chunkId'])
        if record is None:
            output.append(deepcopy(parent))
            continue
        if len(record['groups']) != 1:
            raise SourceContextError('source editions need distinct explicit identity groups')
        group = record['groups'][0]
        plain = TAG.sub('', parent[body_key(parent)])
        reconstructed = ''.join(TAG.sub('', c['coreText']) for c in group['children'])
        if plain != reconstructed:
            raise SourceContextError('producer parent differs from verified complete source excerpt; regenerate source-context plan')
        if len(group['children']) < 2:
            raise SourceContextError('a split plan must produce multiple explicit children')
        output.extend(nested_children(parent, group['children'], reserved,
            source_bindings=group['sourceBindings'], plan_sha=plan_sha))
        seen.add(parent['chunkId'])
    for sid in touched:
        section = [c for c in output if c['sectionId'] == sid]
        for index, chunk in enumerate(section, bases[sid]):
            chunk.update(chunkIndex=index, totalChunks=len(section))
    return output, seen


def producer_alias(cid, spec, release):
    prefix = spec + '-' + release + '-'
    return spec + '-' + cid[len(prefix):] if cid.startswith(prefix) else cid


def release_identity(chunk, spec, release):
    """Insert the edition while preserving every existing numeric CID suffix."""
    prefix = spec + '-'
    if not chunk['chunkId'].startswith(prefix):
        raise SourceContextError('producer CID does not belong to its explicit specification')
    result = deepcopy(chunk)
    result['chunkId'] = prefix + release + '-' + chunk['chunkId'][len(prefix):]
    if 'sourceContext' in result:
        parent = result['sourceContext']['parentChunkId']
        if not parent.startswith(prefix):
            raise SourceContextError('source-context parent belongs to another specification')
        result['sourceContext']['parentChunkId'] = prefix + release + '-' + parent[len(prefix):]
    return result


def qualify_producer_chunks(chunks, wg, spec, release, source_files, root):
    """Apply maintained reviewed plans to a parser's exact original source input.

    New source bytes or changed parent quotations require explicit regeneration
    with prepare_ts_source_context_split.py. They never silently reuse a plan.
    Editions outside the reviewed plan keep their ordinary parser contract.
    """
    path = Path(root) / 'ontology/config/ts_source_context_splits.json.gz'
    if not path.exists():
        raise SourceContextError('maintained source-context split plan is missing')
    plan_bytes = path.read_bytes()
    plan = json.loads(gzip.decompress(plan_bytes))
    plan_sha = hashlib.sha256(plan_bytes).hexdigest()
    edition = [wg, spec, release]
    selected = [r for r in plan['records'] if r['edition'] == edition]
    if not selected:
        return chunks
    files = {Path(p).resolve().relative_to(Path(root).resolve()).as_posix(): file_sha(p)
             for p in source_files}
    expected = {p: value for r in selected for p, value in r['sourceFences'].items()}
    if any(files.get(p) != value for p, value in expected.items()):
        raise SourceContextError('actual source edition changed; regenerate with prepare_ts_source_context_split.py')
    target_sections = {s['sectionId'] for s in plan.get('sourceSections', []) if s['edition'] == edition}
    if target_sections and all(c.get('sourceContext', {}).get('planSHA256') == plan_sha
            for c in chunks if c['sectionId'] in target_sections):
        if not target_sections.issubset({c['sectionId'] for c in chunks}):
            raise SourceContextError('reviewed actual source section was not regenerated')
        return chunks
    replacements = {}
    for record in selected:
        cid = record['producerChunkId']
        if cid in replacements and replacements[cid]['groups'] != record['groups']:
            raise SourceContextError('conflicting reviewed source-context postimages')
        replacements[cid] = record
    known = {c['chunkId'] for c in chunks}
    if not set(replacements).issubset(known):
        raise SourceContextError('reviewed source parent no longer produced; regenerate source-context plan')
    exact = all(TAG.sub('', c[body_key(c)]) == ''.join(TAG.sub('', child['coreText'])
                for child in replacements[c['chunkId']]['groups'][0]['children'])
                for c in chunks if c['chunkId'] in replacements)
    if not exact:
        # The maintained paragraph splitter can produce different boundaries
        # from an older artifact while the actual source edition stays fixed.
        # Rebind those newly generated chunks to the full actual source section
        # instead of attaching an old CID's different quotation by name.
        return qualify_regenerated_sections(chunks, plan, edition, plan_sha)
    result, seen = replace_and_reindex(chunks, replacements, plan_sha=plan_sha)
    if seen != set(replacements):
        raise SourceContextError('source-context plan incompletely applied')
    return result


def producer_source_context(wg, spec, release, source_files, root):
    """Fence a source edition before the generic character-based splitter runs."""
    path = Path(root) / 'ontology/config/ts_source_context_splits.json.gz'
    if not path.exists():
        raise SourceContextError('maintained source-context split plan is missing')
    plan_bytes = path.read_bytes()
    plan = json.loads(gzip.decompress(plan_bytes))
    plan_sha = hashlib.sha256(plan_bytes).hexdigest()
    edition = [wg, spec, release]
    selected = [r for r in plan['records'] if r['edition'] == edition]
    if not selected:
        return None
    expected = {p:value for r in selected for p,value in r['sourceFences'].items()}
    actual = {Path(p).resolve().relative_to(Path(root).resolve()).as_posix():file_sha(p) for p in source_files}
    if any(actual.get(p) != value for p,value in expected.items()):
        raise SourceContextError('source edition changed; regenerate source-context plan')
    return dict(plan=plan, edition=edition, planSHA256=plan_sha)


def qualify_generated_section(section, spec, context):
    """Split a reviewed actual section before generic slicing can bisect tags."""
    if context is None:
        return None
    actual = next((s for s in context['plan'].get('sourceSections', [])
                   if s['edition'] == context['edition'] and s['sectionId'] == section.section_id), None)
    if actual is None:
        return None
    text = '\n'.join(section.blocks)
    if TAG.sub('', text) != TAG.sub('', actual['newText']):
        raise SourceContextError('complete actual parser section differs; regenerate source-context plan')
    parent = dict(chunkId=section.section_id+'-001', sectionId=section.section_id,
        specNumber=spec, sectionNumber=section.section_number, sectionTitle=section.section_title,
        level=section.level, parentSectionId=section.parent_section_id,
        chunkIndex=1, totalChunks=1, text=text)
    return qualify_regenerated_sections([parent], context['plan'], context['edition'], context['planSHA256'])


def qualify_regenerated_sections(chunks, plan, edition, plan_sha):
    """Qualify current parser boundaries only after unique full-source binding."""
    from common.chunker import count_tokens
    actual = {s['sectionId']: s for s in plan.get('sourceSections', []) if s['edition'] == edition}
    if not actual:
        raise SourceContextError('actual full section context is unavailable; regenerate the source-context plan')
    output, reserved, touched = [], {c['chunkId'] for c in chunks}, set()
    for parent in chunks:
        source = actual.get(parent['sectionId'])
        if source is None:
            output.append(deepcopy(parent))
            continue
        plain = TAG.sub('', parent[body_key(parent)])
        source_norm = source_info(source['newText'])[1]
        query = normalized(plain)
        if not query or source_norm.count(query) != 1:
            raise SourceContextError('current parser excerpt lacks a unique complete actual source binding; regenerate source-context plan')
        bound = bind_source(parent[body_key(parent)], source['newText'],
            [dict(payloadStart=0, payloadEnd=len(plain), startInNormalizedSource=source_norm.index(query))],
            source['tables'], edition=tuple(edition), section_id=parent['sectionId'])
        children = split_bound_source(bound, count_tokens)
        binding = dict(edition=edition, sectionId=parent['sectionId'],
            assessmentMethod='exact unchanged source edition and unique complete current-parser excerpt',
            childSourceProvenance=[dict(textSHA256=c['textSHA256'], sourceRows=c['sourceRows'],
                sourceIntervals=c['sourceIntervals'], context=[{k:v for k,v in u.items() if k != 'text'}
                    for u in c['context']]) for c in children])
        qualified = nested_children(parent, children, reserved, source_bindings=[binding], plan_sha=plan_sha)
        if len(qualified) == 1:
            qualified[0]['chunkId'] = parent['chunkId']
        output.extend(qualified)
        touched.add(parent['sectionId'])
    for sid in touched:
        section = [c for c in output if c['sectionId'] == sid]
        base = min(c['chunkIndex'] for c in chunks if c['sectionId'] == sid)
        for index, c in enumerate(section, base):
            c.update(chunkIndex=index, totalChunks=len(section))
    return output
