#!/usr/bin/env python3
"""publish_ts_source_context_plan.py — build the parser's reviewed split contract.

Spec: chunking_standards.md and fenced source-context split preparation.
Ontology: per-edition bindings retain actual table and row provenance.
Cycle: validate complete shadow → bind source edition → deduplicate parser aliases.
배경: 감사용 임시 산출물 대신 정식 재생성 경로가 읽는 계획을 만든다.
사용: --shadow FILE --catalog FILE --output ontology/config/ts_source_context_splits.json.gz.
LLM 호출: 없음. Only the explicitly selected local configuration is written.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path

from prepare_ts_source_context_split import write, file_sha
from ts_source_context_publication import producer_alias
from ts_source_context_split import SourceContextError

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())


def _read_pinned(path):
    path = Path(path)
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw), hashlib.sha256(raw).hexdigest()


def publish(shadow_path, catalog_path, output, contexts_path):
    shadow, shadow_sha = _read_pinned(shadow_path)
    catalog, catalog_sha = _read_pinned(catalog_path)
    if shadow['errors'] or shadow['summary']['completeParents'] != shadow['summary']['parents']:
        raise SourceContextError('incomplete source context preparation')
    editions, catalog_fences = {}, {}
    for edition in catalog['editions']:
        key = tuple(edition['edition'])
        if key in editions:
            raise SourceContextError('duplicate source catalog edition')
        editions[key] = edition
        for path, expected in edition['sourceFences'].items():
            if path in catalog_fences and catalog_fences[path] != expected:
                raise SourceContextError('conflicting source catalog file hashes')
            catalog_fences[path] = expected
    if catalog_fences != shadow['sourceFences']:
        raise SourceContextError('source catalog differs from prepared source generation')
    contexts, contexts_sha = _read_pinned(contexts_path)
    if (contexts.get('catalogSHA256') != catalog_sha
            or catalog_sha not in shadow.get('inputSHA256', {}).values()):
        raise SourceContextError('source catalog bytes differ from the prepared catalog')
    if contexts['sourceFences'] != shadow['sourceFences']:
        raise SourceContextError('runtime physical-table context source generation differs')
    actual_tables = {}
    for entry in contexts['tables']:
        key = tuple(entry['edition']), entry['table']['ownerSectionId']
        actual_tables.setdefault(key, []).append(entry['table'])
    staged_sections = {}
    for path, expected in shadow['sourceShadowSHA256'].items():
        stage, stage_sha = _read_pinned(path)
        if stage_sha != expected:
            raise SourceContextError('runtime source section generation changed')
        # Stage filenames are an index only; the shadow's actual binding below
        # selects the exact edition and explicit section identity.
        staged_sections[Path(path).name.removesuffix('.json.gz')] = {
            s['sectionId']: s for s in stage['sections']}
    source_sections = {}
    records = {}
    for record in shadow['records']:
        if len(record['groups']) != 1:
            raise SourceContextError('explicit source partition is required before parser publication')
        group = record['groups'][0]
        for binding in group['sourceBindings']:
            wg, spec, release = binding['edition']
            cid = producer_alias(record['chunkId'], spec, release)
            key = wg, spec, release, cid
            section_key = (wg, spec, release, binding['sectionId'])
            source_sections[section_key] = dict(edition=[wg, spec, release],
                sectionId=binding['sectionId'],
                newText=staged_sections['_'.join(binding['edition'])][binding['sectionId']]['newText'],
                tables=actual_tables.get((tuple(binding['edition']), binding['sectionId']), []))
            fences = editions[tuple(binding['edition'])]['sourceFences']
            for path, expected in fences.items():
                if file_sha(ROOT / path) != expected:
                    raise SourceContextError('source edition bytes changed before plan publication')
            prior = records.get(key)
            children = deepcopy(group['children'])
            if len(children) != len(binding['childSourceProvenance']):
                raise SourceContextError('source edition provenance omits a child')
            # A shared text's source coordinates belong to this actual edition,
            # rather than the first representative edition of the text group.
            for child, provenance in zip(children, binding['childSourceProvenance']):
                for name in ('sourceRows', 'sourceIntervals'):
                    child[name] = deepcopy(provenance[name])
                if (child['textSHA256'] != provenance['textSHA256']
                        or len(child['context']) != len(provenance['context'])):
                    raise SourceContextError('source edition child context differs')
                for unit, actual in zip(child['context'], provenance['context']):
                    if unit['kind'] != actual['kind'] or unit['plainSHA256'] != actual['plainSHA256']:
                        raise SourceContextError('source edition context quotation differs')
                    text = unit['text']
                    unit.clear()
                    unit.update(deepcopy(actual), text=text)
            value = dict(edition=[wg, spec, release], producerChunkId=cid,
                sourceFences=fences, groups=[dict(sourceBindings=[deepcopy(binding)], children=children)])
            if prior and [c['textSHA256'] for c in prior['groups'][0]['children']] != [c['textSHA256'] for c in children]:
                raise SourceContextError('conflicting producer aliases for one actual edition')
            records[key] = value
    plan = dict(schema='reviewed-source-context-splits',
        preparation=dict(path=str(shadow_path), sha256=shadow_sha),
        sourceCatalog=dict(path=str(catalog_path), sha256=catalog_sha),
        actualSourceContexts=dict(path=str(contexts_path), sha256=contexts_sha),
        regeneration='prepare_ts_source_context_split.py, then publish_ts_source_context_plan.py',
        boundary='Source-SHA and exact complete parent quotations gate this reviewed subset. New source generations require explicit re-preparation.',
        records=[records[k] for k in sorted(records)],
        sourceSections=[source_sections[k] for k in sorted(source_sections)])
    write(output, plan)
    print(json.dumps(dict(records=len(records), path=str(output), sha256=file_sha(output))), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('shadow', 'catalog', 'output', 'contexts'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    publish(args.shadow, args.catalog, args.output, args.contexts)
