#!/usr/bin/env python3
"""reconcile_tdoc_source_extensions.py — retain source CR form facts in Phase-4 and KG.

Spec: Phase-4 generators/loaders own Reason, Summary and Consequences text fields.
Ontology: CR source-form text, independently of meeting decision disposition.
Cycle: exact source metadata receipt → native parsed forms → JSON-LD/live preimages → guarded readback.
배경: restored native CR inputs also need their maintained Phase-4 text projections.
사용: --wg RAN4 --metadata-receipt retained.json --out retained.json [--apply].
LLM 호출: none. Retained original forms and explicit local Neo4j writes only.
"""
from __future__ import annotations

import argparse
import copy
import gc
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(ROOT / 'scripts/common'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common.atomic_io import write_text_atomic
from common import review_artifacts
from document_decision_storage import durable_json
import reconcile_tdoc_source_supplements as guarded
from tdoc_supplement_vectors import sha, load_module

FIELDS = {'reason_for_change': 'reasonForChange', 'summary_of_change': 'summaryOfChange',
          'consequences_if_not_approved': 'consequencesIfNotApproved'}


def source_properties(records, targets, fences, root, native_parser=None):
    by_id = {r['tdoc_number']: r for r in records}
    if len(by_id) != len(records) or not set(targets) <= set(by_id):
        raise ValueError('Native Phase-4 document identity absent/ambiguous')
    result = {}
    for index, target in enumerate(targets, 1):
        record = by_id[target]
        source = record['source_path']
        if record.get('errors') or source not in fences or sha(root / source) != fences[source]:
            raise ValueError('Native Phase-4 record lacks its validated own source: ' + target)
        if native_parser is not None:
            parsed = native_parser.parse_cr_document(root / source, record.get('release', ''), source_pack_id='')
            if parsed.errors or parsed.tdoc_number != target or any(
                    record.get(key) != getattr(parsed, key) for key in FIELDS):
                raise ValueError('Actual source form text differs from its retained Phase-4 record')
        properties = {prop: record[key] for key, prop in FIELDS.items() if record.get(key)}
        if any(not isinstance(value, str) for value in properties.values()):
            raise ValueError('CR source form field is not text')
        result['tdoc:' + target] = properties
        # python-docx packages contain cycles; retain the extracted strings
        # while promptly releasing already parsed source packages.
        if native_parser is not None and index % 16 == 0:
            gc.collect()
    return result


def project_extensions(document, properties):
    after = copy.deepcopy(document)
    nodes = {n['@id']: n for n in after['@graph']}
    if len(nodes) != len(after['@graph']):
        raise ValueError('Duplicate Phase-4 canonical identity')
    for id_, fields in properties.items():
        if not fields:
            continue
        if id_ not in nodes:
            node = {'@id': id_, '@type': 'tdoc:CR'}
            after['@graph'].append(node); nodes[id_] = node
        node = nodes[id_]
        types = node.get('@type', [])
        if 'tdoc:CR' not in ([types] if isinstance(types, str) else types):
            raise ValueError('Phase-4 extension has a different source class')
        for prop, value in fields.items():
            key = 'tdoc:' + prop
            if node.get(key) not in (None, value):
                raise ValueError('Unreviewed existing Phase-4 form discrepancy')
            node[key] = value
    return after


def check_sources(fences):
    for relative, expected in fences.items():
        try:
            review_artifacts.resolve_recorded_path(ROOT, relative, expected)
        except (OSError, ValueError) as error:
            raise ValueError('Source/form contract fence changed: ' + relative) from error


def expected_live(before, properties):
    after = copy.deepcopy(before)
    for node in after['nodes']:
        node['properties'].update(properties[node['properties']['id']])
    return after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wg', required=True, choices=['RAN2', 'RAN3', 'RAN4', 'RAN5'])
    parser.add_argument('--metadata-receipt', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--current-additions-only', action='store_true', help='Project only records newly parsed by this metadata batch')
    args = parser.parse_args(); args.out = args.out.resolve(); args.metadata_receipt = args.metadata_receipt.resolve()
    if not args.out.is_relative_to(ROOT) or not args.metadata_receipt.is_relative_to(ROOT) or args.out.exists():
        parser.error('Use a retained source receipt and a new result path inside the repository')
    metadata_raw = args.metadata_receipt.read_bytes()
    metadata = json.loads(metadata_raw)
    if metadata['mode'] != 'applied_exact_readback' or metadata['wg'] != args.wg:
        raise ValueError('Source extensions require an exactly completed metadata projection')
    # The prior receipt records the producer code at its own execution. This
    # independent projection rechecks its immutable input bytes and reparses
    # the three form fields using the current maintained source parser.
    generation_contracts = {p:s for p,s in metadata['sourceFences'].items() if p.startswith('scripts/')}
    fences = {p:s for p,s in metadata['sourceFences'].items() if not p.startswith('scripts/')}
    p4 = ROOT / f'ontology/output/tsg/RAN/formal/parsed_cr/{args.wg}/cr_documents.json'
    fences[p4.relative_to(ROOT).as_posix()] = metadata['phase4DocumentsAfterSha256']
    parser_paths = list((ROOT / f'scripts/tsg/RAN/formal/{args.wg}/phase-4/cr-parser').glob('*_parse_cr_documents.py'))
    if len(parser_paths) != 1: raise ValueError('One maintained Phase-4 parser is required')
    parser_path = parser_paths[0]
    loader = ROOT / f'scripts/tsg/RAN/formal/{args.wg}/phase-4/neo4j/01_load_cr_ontology.py'
    fences[args.metadata_receipt.relative_to(ROOT).as_posix()] = hashlib.sha256(metadata_raw).hexdigest()
    for path in (Path(__file__), Path(guarded.__file__), Path(review_artifacts.__file__), parser_path, loader,
                 Path(__file__).with_name('tdoc_supplement_vectors.py'),
                 Path(__file__).with_name('cr_form.py'), Path(__file__).with_name('docx_text.py')):
        fences[path.relative_to(ROOT).as_posix()] = sha(path)
    check_sources(fences)
    projection = metadata['phase4']['projection']
    targets = sorted(set(metadata['phase4']['sourceSupplementsAdded']) | (set() if args.current_additions_only
                     else set(projection['sourceSupplements']) | set(projection['sourceClassifications'])
                     | set(projection.get('sourceNativeBodies', []))))
    if not targets: raise ValueError('No source-native Phase-4 records selected')
    native_parser = load_module(parser_path, '_source_form_projection_parser')
    properties = source_properties(json.loads(p4.read_text())['documents'], targets, fences, ROOT, native_parser)
    path = ROOT / f'ontology/output/tsg/RAN/formal/instances/phase-4/{args.wg}/cr_extensions.jsonld'
    original = path.read_bytes() if path.exists() else None
    if args.wg != 'RAN5' and original is None:
        raise ValueError('Maintained Phase-4 JSON-LD input is absent')
    after = project_extensions(json.loads(original), properties) if original is not None else None
    proposal = dict(affected=targets, supplementTargets=[], endpoints={}, labels={},
                    properties=properties, removeEdges=[], addEdges=[])
    with guarded.GraphDatabase.driver(guarded.axis.bolt_uri(args.wg), auth=guarded.credentials.neo4j_auth()) as driver:
        with driver.session(default_access_mode=guarded.READ_ACCESS) as session:
            before = guarded.snapshot(session, targets); guarded.check_endpoints(session, proposal)
        for node in before['nodes']:
            id_ = node['properties']['id']
            if 'CR' not in node['labels'] or any(node['properties'].get(k) not in (None, v) for k,v in properties[id_].items()):
                raise ValueError('Unreviewed existing live CR form discrepancy')
        report = dict(mode='read_only_plan', wg=args.wg, targets=targets, sourceFiles=fences,
            properties=properties, liveBeforeSha256=guarded.digest(before),
            canonicalPath=path.relative_to(ROOT).as_posix() if original is not None else None,
            canonicalBeforeSha256=hashlib.sha256(original).hexdigest() if original is not None else None,
            sourceMetadataGenerationContracts=generation_contracts,
            sourceFactScope='Native CR-form Reason/Summary/Consequences; disposition remains separately assessed')
        if not args.apply:
            durable_json(args.out, report); print(json.dumps(dict(mode=report['mode'], targets=len(targets)))); return
        directory = args.out.with_suffix(''); directory.mkdir(parents=True)
        full = directory / 'live_full_preimage.json.gz'
        with gzip.open(full, 'xb') as stream: stream.write(json.dumps(before, ensure_ascii=False).encode())
        with full.open('rb') as stream: os.fsync(stream.fileno())
        report['livePreimage'] = dict(path=full.relative_to(ROOT).as_posix(), sha256=sha(full))
        if original is not None:
            backup = directory / 'cr_extensions_before.json.gz'
            with gzip.open(backup, 'xb') as stream: stream.write(original)
            with backup.open('rb') as stream: os.fsync(stream.fileno())
            report['canonicalPreimage'] = dict(path=backup.relative_to(ROOT).as_posix(), sha256=sha(backup))
        fd = os.open(directory, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
        report['mode'] = 'prepared_with_full_preimages'; durable_json(args.out, report)
        check_sources(fences)
        if original is not None and path.read_bytes() != original: raise ValueError('Canonical extension preimage changed')
        report['mode'] = 'applying'; durable_json(args.out, report)
        if after is not None: write_text_atomic(path, json.dumps(after, ensure_ascii=False, indent=2) + '\n')
        try:
            def apply(tx):
                check_sources(fences)
                result = guarded.apply_transaction(tx, proposal, before)
                check_sources(fences)
                if after is not None and json.loads(path.read_text()) != after:
                    raise ValueError('Canonical extension changed before transaction commit')
                return result
            with driver.session() as session: live_after = session.execute_write(apply)
        except BaseException as error:
            with driver.session(default_access_mode=guarded.READ_ACCESS) as session:
                current = guarded.snapshot(session, targets)
            if guarded.digest(current) == guarded.digest(before):
                if original is not None:
                    try:
                        current_canonical = path.read_bytes()
                    except FileNotFoundError:
                        current_canonical = None
                    owned_canonical = (json.dumps(after, ensure_ascii=False, indent=2) + '\n').encode()
                    if current_canonical != owned_canonical:
                        report['mode'] = 'canonical_changed_requires_review'
                        report['canonicalRollbackSkipped'] = 'current bytes differ from this projection'
                        durable_json(args.out, report)
                        raise
                    write_text_atomic(path, original.decode())
                report['mode'] = 'transaction_failed_rollback_verified'; durable_json(args.out, report)
                raise
            if guarded.digest(current) != guarded.digest(expected_live(before, properties)):
                report['mode'] = 'unexpected_live_state_requires_review'; durable_json(args.out, report)
                raise
            live_after = current
            report['transactionAcknowledgementRecoveredByExactReadback'] = True
            if not isinstance(error, Exception):
                report['mode'] = 'transaction_interrupted_live_projection_verified'
                durable_json(args.out, report)
                raise
        with driver.session(default_access_mode=guarded.READ_ACCESS) as session:
            live_readback = guarded.snapshot(session, targets)
        if guarded.digest(live_readback) != guarded.digest(live_after):
            raise ValueError('Committed full live CR form/edge readback differs')
        if after is not None and json.loads(path.read_text()) != after: raise ValueError('Canonical extension exact readback failed')
        check_sources(fences)
        report.update(mode='applied_exact_readback', liveAfterSha256=guarded.digest(live_readback),
            canonicalAfterSha256=sha(path) if original is not None else None,
            unrelatedNodePropertyOrRelationChanges=0,
            populatedProperties={prop: sum(prop in p for p in properties.values()) for prop in FIELDS.values()})
        durable_json(args.out, report)
        print(json.dumps(dict(mode=report['mode'],targets=len(targets),properties=report['populatedProperties'])))


if __name__ == '__main__': main()
