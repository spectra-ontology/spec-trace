#!/usr/bin/env python3
"""tdoc_native_cr_sources.py — validate source-owned native CR body inputs.

Spec: Phase-4/8 retained CR parsing, exact source ownership and Annex row evidence.
Ontology: an indexed source document is separate from its registered class and approval.
Cycle: retained own CR form plus exact report row → source facts → ordinary body parser.
배경: meeting-native CR sources may be outside the historical CR-pack population.
사용: validated_native_sources(root, wg); source_inputs(root, wg).
LLM 호출: none. Original local bytes only; no database, embedding or network calls.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
import re
from zipfile import ZipFile

from tdoc_source_supplements import SupplementError, canonical_meeting, checked_path

_VALIDATED_CACHE = {}


def identity_sources(row):
    sources = [(row['coverIdentity']['path'], row['coverIdentity']['sha256']),
               (row['reportEntry']['path'], row['reportEntry']['sourceSHA256'])]
    if row.get('officialSourceArchive'):
        sources.append((row['officialSourceArchive']['path'], row['officialSourceArchive']['sha256']))
    sources.extend((e['path'], e['sha256']) for e in
                   row.get('sourceIdentityReview', {}).get('registeredMasterEvidence', []))
    adjudication = row.get('sourceIdentityReview', {}).get('sourceIdentityAdjudication', {})
    for key in ('master', 'archive'):
        if item := adjudication.get(key): sources.append((item['path'], item['sha256']))
    for key in ('nativeConversionVerification', 'nativeAcceptedView'):
        if item := adjudication.get(key):
            for path_key, sha_key in (('nativePath', 'nativeSha256'), ('retainedDocxPath', 'retainedDocxSha256'),
                                      ('derivedPath', 'derivedSha256')):
                if path_key in item: sources.append((item[path_key], item[sha_key]))
    if item := row.get('nativeAcceptedView'):
        for path_key, sha_key in (('nativePath', 'nativeSha256'), ('derivedPath', 'derivedSha256')):
            if path_key in item: sources.append((item[path_key], item[sha_key]))
    return sources


def ledger_path(root: Path, wg: str) -> Path:
    return root / f'ontology/input/tsg/RAN/formal/meetings/{wg}/tdoc_native_cr_sources.json'


def validate_native_source(root: Path, row: dict) -> dict:
    from decision_disposition import source_blocks
    from document_decision_source import annex_source_evidence
    target = row['target']
    if not re.fullmatch(r'R[1-5]-\d{6,8}', target):
        raise SupplementError('Invalid native CR source identity')
    identity = row['coverIdentity']
    path = checked_path(root, identity['path'], identity['sha256'])
    from native_word_conversion import validate_docx
    validate_docx(path)
    if accepted := row.get('nativeAcceptedView'):
        receipt = accepted['conversionReceipt']
        for path_key, sha_key in (('nativePath', 'nativeSha256'), ('derivedPath', 'derivedSha256')):
            checked_path(root, accepted[path_key], accepted[sha_key])
        if (accepted['derivedPath'] != identity['path'] or accepted['derivedSha256'] != identity['sha256']
                or receipt.get('method') != 'native_accepted_uno_export_reopen'
                or receipt.get('status') != 'verified' or not receipt.get('strictXml')
                or receipt.get('redlinesAfter') != 0
                or receipt.get('acceptedRenderedText', {}).get('equal') is not True
                or receipt.get('sourceSha256') != accepted['nativeSha256']
                or receipt.get('outputSha256') != accepted['derivedSha256']):
            raise SupplementError('Native body accepted view lacks its exact verified rendering receipt')
    archive = row.get('officialSourceArchive')
    if archive:
        archive_path = checked_path(root, archive['path'], archive['sha256'])
        with ZipFile(archive_path) as zipped:
            if not archive.get('members'):
                raise SupplementError('Native CR archive lacks retained member provenance')
            for member in archive['members']:
                if hashlib.sha256(zipped.read(member['name'])).hexdigest() != member['sha256']:
                    raise SupplementError('Native CR archive member bytes changed')
        # A native DOC and a retained DOCX have separate hashes. Their presence
        # records provenance; it does not assert binary or conversion identity.
    # A cover is visited once; keep the shared Annex report cache for its many
    # rows instead of retaining hundreds of full CR XML trees in that cache.
    texts, sha, _ = source_blocks.__wrapped__(str(path.resolve()))
    if sha != identity['sha256']:
        raise SupplementError('Native CR source cache differs from its bytes')
    evidence = row['review']['actualDocumentEvidence']
    if not evidence or {(e['path'], e['sha256']) for e in evidence} != {(identity['path'], identity['sha256'])}:
        raise SupplementError('Native CR body requires one selected original source')
    header_evidence = [e for e in evidence if re.match(r'word/header\d+\.xml ', e['locator'])]
    if header_evidence:
        from document_decision_storage import check_word_header_evidence
        check_word_header_evidence(path, header_evidence)
    for item in evidence:
        if item in header_evidence:
            continue
        loc = re.fullmatch(r'word/document.xml accepted body blocks \[(\d+),(\d+)\)', item['locator'])
        if (not loc or int(loc[2]) != int(loc[1]) + 1
                or texts[int(loc[1])] != item['quote']):
            raise SupplementError('Native CR source quote or locator changed')
    quoted = '\n'.join(e['quote'] for e in evidence)
    parse_quoted = quoted
    if '⌘' in quoted and 'pop-up text over the ⌘ symbols' in quoted:
        # Only explicit form-help markers at cell starts are structural. A
        # glyph in the own Tdoc heading or body remains literal source text.
        parse_quoted = re.sub(r'(?<=\|)\s*⌘\s*', ' ', quoted)
        parse_quoted = re.sub(r'(:\s*)⌘(?=\s*\|)', r'\1', parse_quoted)
    headers = list(re.finditer(
        r'\|\s*(?:(?:TS|TR)\s*)?(\d{2}\.\d{3}(?:-\d+)?)\s*\|\s*CR\s*\|\s*(?:CR\s*)?(\d+)\s*\|\s*rev\s*\|\s*([^|]*)\|\s*Current version:',
        parse_quoted, re.I))
    if len(headers) != 1 or not int(headers[0][2]):
        raise SupplementError('Native source requires one assigned CR form identity')
    spec, number, revision = headers[0].groups()
    revision = revision.strip()
    unspecified_revision = bool(re.fullmatch(r'<\s*Rev\s*#\s*>', revision, re.I))
    ambiguous_revision = bool(re.fullmatch(r'\d+-', revision))
    if revision not in ('', '-') and not revision.isdigit() and not (unspecified_revision or ambiguous_revision):
        raise SupplementError('Native CR revision is not an explicit numeric or initial form value')
    cr_blocks = [int(re.search(r'\[(\d+),', e['locator'])[1]) for e in evidence if 'CHANGE REQUEST' in e['quote']]
    if len(cr_blocks) != 1:
        raise SupplementError('Native source requires its assigned CR form block')
    own_header = '\n'.join(texts[:cr_blocks[0]]) + '\n' + '\n'.join(e['quote'] for e in header_evidence)
    own_pattern = re.escape(target).replace(r'\-', r'\s*-\s*')
    candidates = [m for m in re.finditer(r'(?<![\w-])' + own_pattern + r'(?![\w-])', own_header)
                  if not re.search(r'(?:revision\s+of|based\s+on|previous(?:\s+version)?|replaces?)\s*[:( -]*$',
                                   own_header[max(0, m.start()-64):m.start()], re.I)]
    if not candidates:
        review = row.get('sourceIdentityReview', {})
        if review.get('targetTdocNumber') != target or review.get('actualDocumentEvidence') != evidence:
            raise SupplementError('Native source lacks its own exact header Tdoc identity')
        if review.get('sourceIdentityAdjudication'):
            from document_decision_storage import check_own_header_adjudication
            check_own_header_adjudication(review, root)
        elif (review.get('classification') == 'literal_own_cover_label_format_bound_by_original_archive_and_master'
                and review.get('registeredMasterEvidence') and archive):
            literal = review['literalOwnHeader']
            tail = r'(?:^|\t)(?:draft)?(?:' + re.escape(target.split('-')[0]) + r'-\s*)?' + target.split('-')[1] + r'\s*$'
            if literal not in own_header or not re.search(tail, literal, re.I):
                raise SupplementError('Native literal own-label format does not bind the target')
            from document_decision_storage import check_registered_master_evidence
            check_registered_master_evidence(review, root)
        else:
            raise SupplementError('Native source lacks its own exact header Tdoc identity')
    def field(label):
        match = re.search(r'\|\s*' + re.escape(label) + r':\s*\|\s*([^|\n]*)\|', parse_quoted, re.I)
        return match[1].strip() if match else ''
    metadata = {'Title': field('Title'), 'Release': field('Release').strip('<> '),
                'Category': field('Category'), 'Source to WG': field('Source to WG'),
                'Work item code': field('Work item code')}
    release = re.fullmatch(r'Rel\s*-\s*(\d+)', metadata['Release'], re.I)
    if not metadata['Title'] or not release:
        raise SupplementError('Native CR source requires its actual title and Release')
    if metadata != identity['metadata']:
        raise SupplementError('Native source metadata differs from its quoted CR form')
    report = row['reportEntry']
    event = report['sourceEvent']
    checked = annex_source_evidence(event, root)
    if (event['subject_tdoc'] != target
            or canonical_meeting(event['meeting_id']) != canonical_meeting(row['meetingId'])
            or checked['path'] != report['path'] or checked['sha256'] != report['sourceSHA256']
            or checked['locator'] != report['locator'] or checked['quote'] != report['quote']):
        raise SupplementError('Native CR source report row identity changed')
    if 'sourceIdentityReview' in row:
        proof = row['sourceIdentityReview']['decisionEvidence']
        if any(proof.get(key) != checked[key] for key in ('path', 'sha256', 'locator', 'quote')):
            raise SupplementError('Native own-header adjudication belongs to another source row')
    # Body facts come from this exact form. The Annex's disposition and any
    # disputed descriptor are retained separately and confer no approval here.
    normalized_revision = None if unspecified_revision or ambiguous_revision else revision if revision not in ('', '-') else '0'
    normalized_release = 'Rel-' + release[1]
    actual = {'modifies': 'tdoc:spec/' + spec.replace('.', '_'),
              'tdoc:crNumber': number, 'tdoc:crRevision': normalized_revision or '',
              'targetRelease': 'tdoc:release/' + normalized_release.replace('-', '_')}
    return {**row, 'nativeSourceKind': 'retained_assigned_cr_form',
            'nativeSourceIdentity': dict(specNumber=spec, crNumber=number,
                crRevision=normalized_revision, revisionRaw=revision, release=normalized_release,
                revisionEvidenceStatus='unspecified_placeholder' if unspecified_revision
                    else 'ambiguous_literal' if ambiguous_revision
                    else 'explicit_numeric' if revision.isdigit() else 'initial_form'),
            'deltas': [dict(field=k, sourceBackedValue=v) for k, v in actual.items()]}


def validated_native_sources(root, wg, selected_meetings=None, *, selected_targets=None):
    path = ledger_path(root, wg)
    if not path.exists():
        return []
    raw = json.loads(path.read_text())
    rows = raw.get('records')
    if raw.get('schema') != 1 or raw.get('wg') != wg or not isinstance(rows, list):
        raise SupplementError('Invalid native CR source ledger')
    if len({r['target'] for r in rows}) != len(rows):
        raise SupplementError('Duplicate native CR source target')
    selected = None if selected_meetings is None else {canonical_meeting(m) for m in selected_meetings}
    result = []
    for row in rows:
        if (selected is not None and canonical_meeting(row['meetingId']) not in selected
                or selected_targets is not None and row['target'] not in selected_targets):
            continue
        if not row['target'].startswith('R' + wg.removeprefix('RAN') + '-'):
            raise SupplementError('Native source is outside its working group')
        key = (str(root.resolve()), hashlib.sha256(json.dumps(row, sort_keys=True,
                ensure_ascii=False, separators=(',', ':')).encode()).hexdigest())
        if key in _VALIDATED_CACHE:
            # Reusing parsed evidence is safe only while every original byte
            # owner is unchanged; changing a row also changes the cache key.
            for relative, sha in identity_sources(row):
                checked_path(root, relative, sha)
            result.append(deepcopy(_VALIDATED_CACHE[key]))
        else:
            validated = validate_native_source(root, row)
            _VALIDATED_CACHE[key] = deepcopy(validated)
            result.append(validated)
    return result


def source_inputs(root, wg, selected_meetings=None, *, selected_targets=None):
    path = ledger_path(root, wg)
    if not path.exists():
        return {}
    result = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()}
    for row in validated_native_sources(root, wg, selected_meetings, selected_targets=selected_targets):
        for relative, sha in identity_sources(row):
            if relative in result and result[relative] != sha:
                raise SupplementError('Conflicting native source owner hashes')
            result[relative] = sha
    return result
