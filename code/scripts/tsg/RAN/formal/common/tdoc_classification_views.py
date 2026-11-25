#!/usr/bin/env python3
"""tdoc_classification_views.py — source-classified CR inputs for maintained document views.

Spec: Phase-4 source parsing and Phase-8 CR body chunking.
Ontology: own-numbered CR source identities and unchanged source body provenance.
Cycle: validated class ledger → actual own source parser → CR body chunks.
배경: assigned CR forms uploaded as generic reservations need the same maintained parsers.
사용: phase8_classified_chunks(parser, rows, records); extra_phase8_sources(...).
LLM 호출: none. Local source parsing only; no embeddings or database writes.
"""
from __future__ import annotations

from dataclasses import asdict
import gc
import json
import re

from tdoc_source_classification import validated_classifications
from tdoc_source_identity_corrections import validated_corrections


def source_body_rows(root, wg, selected_meetings=None, *, selected_targets=None):
    """Return assigned CR forms explicitly selected for native body projection.

    Classification and metadata correction stay distinct ledgers. A correction
    can additionally select its verified own source for the ordinary CR body
    parser without changing its class or decision disposition.
    """
    rows = list(validated_classifications(root, wg, selected_meetings, selected_targets=selected_targets))
    seen = {r['target'] for r in rows}
    for correction in validated_corrections(root, wg, selected_meetings):
        if (not correction.get('recoverNativeBody') or correction['target'] in seen
                or (selected_targets is not None and correction['target'] not in selected_targets)):
            continue
        import cr_form
        import docx_text
        evidence = correction['review']['actualDocumentEvidence']
        identities = {(e['path'], e['sha256']) for e in evidence}
        if len(identities) != 1:
            raise ValueError('Native body correction requires one selected own source')
        path, sha = next(iter(identities))
        cover = '\n'.join(e['quote'] for e in evidence)
        header = re.search(r'\|\s*(\d{2}\.\d{3}(?:-\d+)?)\s*\|\s*CR\s*\|\s*(\d+)\s*\|\s*rev\s*\|\s*([^|]*)\|\s*Current version:', cover, re.I)
        release = re.search(r'Release:\s*\|\s*<?\s*(Rel-\d+)\b', cover, re.I)
        fields = cr_form.form_fields(docx_text.open_document(root / path))
        if not header or int(header[2]) == 0 or not release or not fields.get('title'):
            raise ValueError('Native body correction requires its assigned own CR form')
        revision = header[3].strip() or '0'
        if revision == '-': revision = '0'
        actual = {'modifies': 'tdoc:spec/' + header[1].replace('.', '_'),
                  'tdoc:crNumber': header[2], 'tdoc:crRevision': revision,
                  'targetRelease': 'tdoc:release/' + release[1].replace('-', '_')}
        rows.append({**correction, 'deltas': [dict(field=k, sourceBackedValue=v) for k,v in actual.items()],
            'coverIdentity': dict(path=path, sha256=sha, metadata={
                'Title': fields['title'], 'Release': release[1],
                'Category': fields.get('category', ''), 'Source to WG': fields.get('source', ''),
                'Work item code': fields.get('work_item', '')})})
        seen.add(correction['target'])
    from tdoc_native_cr_sources import validated_native_sources
    for native in validated_native_sources(root, wg, selected_meetings, selected_targets=selected_targets):
        if native['target'] in seen:
            prior = next(r for r in rows if r['target'] == native['target'])
            if prior['coverIdentity'] != native['coverIdentity']:
                raise ValueError('Two different native source owners selected for one CR body')
            continue
        rows.append(native); seen.add(native['target'])
    return rows


def source_fields(row):
    result = {d['field']: d['sourceBackedValue'] for d in row['deltas']}
    meta = row['coverIdentity']['metadata']
    return dict(spec_number=result['modifies'].removeprefix('tdoc:spec/').replace('_', '.'),
                cr_number=result['tdoc:crNumber'], rev=result['tdoc:crRevision'],
                release=result.get('targetRelease', '').removeprefix('tdoc:release/').replace('_', '-')
                    or meta.get('Release', '').strip('<> '), category=meta.get('Category', ''),
                title=meta.get('Title', ''), source=meta.get('Source to WG', ''),
                work_item=meta.get('Work item code', ''))


def phase8_classified_chunks(parser, rows, records, *, existing_tdocs=(), progress=None):
    """Parse only missing source-owned bodies through the WG's ordinary CR chunker."""
    by_id = {r['tdoc_number']: r for r in records}
    existing = set(existing_tdocs)
    chunks = []
    completed = 0

    def checkpoint():
        nonlocal completed
        completed += 1
        if completed % 16 == 0:
            gc.collect()
        if progress and completed % 200 == 0:
            progress(completed)
    for row in rows:
        target = row['target']
        if target in existing:
            continue
        if target not in by_id:
            raise ValueError('Source-classified CR body needs its parsed Phase-4 record: ' + target)
        fields = source_fields(row)
        if parser.WG == 'RAN5':
            from tdoc_supplement_vectors import serialize_cr
            form, proposal, error, _ = parser._read_cr(str(parser.PROJECT_ROOT / row['coverIdentity']['path']))
            if error or proposal is None:
                raise ValueError('Source-classified CR native parse failed: ' + target)
            form.tdoc_number = target
            form.spec_number = fields['spec_number']; form.release = fields['release']
            if form.category != fields['category']:
                raise ValueError('Source-classified CR native category differs: ' + target)
            revision = fields['rev']
            label = 'CR' + fields['cr_number'] + (f'r{revision}' if revision not in ('', '-', '0') else '')
            parsed = parser.generate_cr_chunks(form, *proposal, phase4_meta=dict(
                meeting=row['meetingId'].removeprefix('RAN5#'), title=fields['title'],
                source=fields['source'], work_item=fields['work_item']), cr_number=label)
            if not parsed or any(c.tdoc_number != target for c in parsed):
                raise ValueError('Source-classified CR produced no native chunks: ' + target)
            chunks.extend(serialize_cr(c) for c in parsed)
            checkpoint()
            continue
        record = {**by_id[target], **fields, 'cr_pack_id': ''}
        revision = fields['rev']
        label = 'CR' + fields['cr_number'] + (f'r{revision}' if revision not in ('', '-', '0') else '')
        source_cover = {target: dict(title=fields['title'], source=fields['source'],
            category=fields['category'], work_item=fields['work_item'], meeting=row['meetingId'])}
        parsed = parser.parse_single_cr(parser.PROJECT_ROOT / row['coverIdentity']['path'],
            source_cover, {target: record}, source_identity=(fields['spec_number'], label, target))
        if not parsed or any(c.tdocNumber != target for c in parsed):
            raise ValueError('Source-classified CR produced no chunks or a different identity: ' + target)
        for chunk in parsed:
            payload = asdict(chunk)
            # RAN4's original body contract omitted Release; a source-owned
            # Release remains an explicit payload field for these new inputs.
            payload['release'] = fields['release']
            if row.get('nativeSourceIdentity'):
                payload['sourceNativeCRIdentity'] = {**row['nativeSourceIdentity'],
                    'sourcePath': row['coverIdentity']['path'],
                    'sourceSha256': row['coverIdentity']['sha256']}
            chunks.append(payload)
        checkpoint()
    return parser._harden_per_cr(chunks)


def extra_phase8_sources(parser, paths):
    """Return validated source rows whose own Tdoc has no collected CR input."""
    rows = source_body_rows(parser.PROJECT_ROOT, parser.WG)
    existing = {resolved[2] for p in paths if (resolved := parser.identity().resolve(p))}
    return [r for r in rows if r['target'] not in existing]


def phase4_records(parser):
    path = parser.PHASE4_META if parser.WG == 'RAN5' else parser.PHASE4_DIR / 'cr_documents.json'
    return json.loads(path.read_text())['documents']
