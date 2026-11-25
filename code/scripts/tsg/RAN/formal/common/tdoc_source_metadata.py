#!/usr/bin/env python3
"""tdoc_source_metadata.py — project adjudicated CR source identities.

Spec: Phase-1 CR identity; Phase-4/6/8 document metadata.
Ontology: the same source-owned CR number, revision, Spec and Release in every view.
Cycle: checked cover/report ledgers → explicit field overlay → unchanged source body.
배경: all document views share source-owned identities while retaining their bodies.
사용: identity_fields(root, wg); overlay_record(...); phase4_sources(...).
LLM 호출: none. Only retained, SHA-checked original documents are used.
"""
from __future__ import annotations

from functools import lru_cache
import gc
import json
from pathlib import Path
import re

from tdoc_source_identity_corrections import validated_corrections
from tdoc_source_supplements import validated_records
from tdoc_source_classification import validated_classifications


@lru_cache(maxsize=8)
def identity_fields(root: Path, wg: str, selected_targets: tuple[str, ...] | None = None) -> dict[str, dict]:
    """Validate the complete source ledger once per producer process."""
    result = {}
    for row in validated_corrections(root, wg) + validated_classifications(root, wg, selected_targets=selected_targets):
        if selected_targets is not None and row['target'] not in selected_targets:
            continue
        fields = {}
        for delta in row['deltas']:
            field, value = delta['field'], delta['sourceBackedValue']
            if field == 'modifies':
                fields['spec_number'] = value.removeprefix('tdoc:spec/').replace('_', '.')
            elif field == 'targetRelease':
                fields['release'] = value.removeprefix('tdoc:release/').replace('_', '-')
            elif field == 'tdoc:crNumber':
                fields['cr_number'] = value
            elif field == 'tdoc:crRevision':
                fields['rev'] = value
            elif field == 'tdoc:crCategory':
                fields['category'] = value
            elif field == 'tdoc:type':
                fields['document_type'] = value
        if fields:
            current = result.setdefault(row['target'], {})
            if any(key in current and current[key] != value for key, value in fields.items()):
                raise ValueError('Conflicting source identity fields: ' + row['target'])
            current.update(fields)
    return result


def overlay_record(record, fields):
    """Only source-adjudicated identity fields are projected onto a parsed CR."""
    changed = {}
    fields = dict(fields)
    fields.pop('document_type', None)
    number = record.get('cr_number') if isinstance(record, dict) else getattr(record, 'cr_number', None)
    combined = re.fullmatch(r'(\d+)r(\d+)', str(number or ''))
    if combined and {'cr_number', 'rev'} & fields.keys():
        revised = fields.pop('rev', combined[2])
        fields['cr_number'] = fields.get('cr_number', combined[1]) + (f'r{revised}' if revised not in ('', '-', '0') else '')
        current_revision = record.get('rev') if isinstance(record, dict) else getattr(record, 'rev', None)
        if current_revision is not None:
            fields['rev'] = revised
    for field, value in fields.items():
        current = record.get(field) if isinstance(record, dict) else getattr(record, field)
        if str(current) != str(value):
            changed[field] = [current, value]
            if isinstance(record, dict):
                record[field] = value
            else:
                setattr(record, field, value)
    return changed


def corrected_label(label: str, fields: dict) -> str:
    """Preserve the unmodified half of a CR number/revision identity."""
    if not {'cr_number', 'rev'} & fields.keys():
        return label
    match = re.fullmatch(r'CR(\d+)(?:r(\d+))?', label)
    if not match:
        raise ValueError('A source CR identity correction needs a structured CR label: ' + label)
    number = fields.get('cr_number', match[1])
    revision = fields.get('rev', match[2] or '0')
    return f'CR{number}' + (f'r{revision}' if revision not in ('', '-', '0') else '')


def overlay_chunk(chunk: dict, fields: dict, *, tdoc=False) -> dict:
    """Return a payload with the same body, identity, ordering and unknown fields."""
    after = dict(chunk)
    if 'release' in fields:
        after['release'] = fields['release']
    if tdoc:
        if 'document_type' in fields:
            after['type'] = fields['document_type']
        return after
    if 'category' in fields:
        after['category'] = fields['category']
    if 'spec_number' in fields:
        before, spec = chunk['specNumber'], fields['spec_number']
        after['specNumber'] = spec
        after['sectionIds'] = [spec + sid[len(before):] if sid.startswith(before + '-') else sid
                               for sid in chunk.get('sectionIds', [])]
        sid = chunk.get('chunkSectionId')
        if isinstance(sid, str) and sid.startswith(before + '-'):
            after['chunkSectionId'] = spec + sid[len(before):]
    if {'cr_number', 'rev'} & fields.keys():
        after['crNumber'] = corrected_label(chunk['crNumber'], fields)
    return after


def phase4_sources(parser, records, *, selected_meetings=None, selected_targets=None, progress=None):
    """Include selected actual source supplements and apply reviewed identities."""
    root, wg = parser.PROJECT_ROOT, parser.WG
    if selected_meetings is None:
        path = root / f'ontology/output/tsg/RAN/formal/instances/phase-1/{wg}/meetings.jsonld'
        selected_meetings = {n['tdoc:meetingNumber'] for n in json.loads(path.read_text())['@graph']}
    by_target = {record.tdoc_number: record for record in records}
    if len(by_target) != len(records):
        raise ValueError('Phase-4 source projection requires deduplicated Tdoc identities')
    added = []
    changes = {}
    for row in validated_records(root, wg, set(selected_meetings)):
        if selected_targets is not None and row['target'] not in selected_targets:
            continue
        if row.get('kind') == 'document':
            continue
        identity = row['sourceIdentity']
        if row['target'] in by_target:
            changed = overlay_record(by_target[row['target']], dict(spec_number=identity['specNumber'],
                release=identity['release'], cr_number=identity['crNumber'], rev=identity['crRevision']))
            if changed:
                changes[row['target']] = changed
            continue
        import inspect
        kwargs = {'source_pack_id': ''} if 'source_pack_id' in inspect.signature(parser.parse_cr_document).parameters else {}
        record = parser.parse_cr_document(root / row['path'], identity['release'], **kwargs)
        if record.errors:
            raise ValueError(f"Checked source supplement did not parse: {row['target']}: {record.errors}")
        record.tdoc_number = row['target']
        overlay_record(record, dict(spec_number=identity['specNumber'], release=identity['release'],
                                   cr_number=identity['crNumber'], rev=identity['crRevision']))
        records.append(record)
        by_target[row['target']] = record
        added.append(row['target'])
    classified, native_bodies = [], []
    from tdoc_classification_views import source_body_rows, source_fields
    for row in source_body_rows(root, wg, set(selected_meetings), selected_targets=selected_targets):
        if row['target'] in by_target:
            continue
        fields = source_fields(row)
        fields = {key: fields[key] for key in ('spec_number', 'release', 'cr_number', 'rev', 'category')}
        # The own cover can state a Release even when the report omitted or
        # disagreed with that field; its original parsed value remains explicit.
        release = row['coverIdentity']['metadata'].get('Release', '')
        record = parser.parse_cr_document(root / row['coverIdentity']['path'], release, source_pack_id='')
        if record.errors:
            raise ValueError(f"Source-classified CR did not parse: {row['target']}: {record.errors}")
        if record.tdoc_number != row['target']:
            raise ValueError('Source-classified CR parsed a different own document identity')
        overlay_record(record, fields)
        records.append(record); by_target[row['target']] = record
        (native_bodies if row.get('nativeSourceKind') or row.get('recoverNativeBody')
         else classified).append(row['target'])
        # python-docx packages contain cyclic references to their XML parts.
        # Keep only the serialized record between source documents.
        if (len(classified) + len(native_bodies)) % 16 == 0:
            gc.collect()
        if progress and (len(classified) + len(native_bodies)) % 200 == 0:
            progress(len(classified) + len(native_bodies))
    absent = []
    for target, fields in identity_fields(root, wg, selected_targets).items():
        if target not in by_target:
            # The CR-pack population is narrower than the meeting spreadsheet.
            # Existing records are overlaid; their absence is an inventory fact.
            absent.append(target)
            continue
        changed = overlay_record(by_target[target], fields)
        if changed:
            changes[target] = changed
    records.sort(key=lambda r: r.source_path)
    return dict(identityCorrections=changes, sourceSupplements=sorted(added),
                sourceClassifications=sorted(classified), sourceNativeBodies=sorted(native_bodies),
                correctionsOutsideInputPopulation=sorted(absent))
