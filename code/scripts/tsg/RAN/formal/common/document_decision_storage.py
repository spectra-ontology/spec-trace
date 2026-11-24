#!/usr/bin/env python3
"""document_decision_storage.py — 원문 문서처분 사건의 정본 직렬화와 보호 적재.

Spec: docs/tsg/build/standards/decision_disposition_contract.md.
Ontology: source-defined document Resolution and qualified DecisionDisposition.
Cycle: checked source entry → canonical Phase-1 identities → journaled transaction.
배경: 문서별 처분은 기술 Agreement와 독립된 사건이며 전자회의의 실제 IRI를 쓴다.
사용: document_resolution_nodes(reports); load_document_resolutions(session, nodes).
LLM 호출: 없음. 원문·정본 식별자·transaction postcondition만 사용한다.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import uuid
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / '.git').exists()) / 'scripts/common'))
from common import axis
from common.atomic_io import write_json_atomic
from common.review_artifacts import resolve_recorded_path

_NODE_CACHE = {}


def durable_json(path, value):
    """Replace a complete UTF-8 journal atomically and flush it to disk."""
    path = Path(path)
    write_json_atomic(path, value)
    descriptor = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def transaction_failure_receipt(error, prior, verified, snapshot, *, rollback_state='rolled_back'):
    """Record only outcomes supported by a fresh read of the owned state."""
    receipt = {'state': 'commit_outcome_unknown', 'error': str(error)}
    try:
        observed = snapshot()
    except Exception as readback_error:
        receipt['readbackError'] = str(readback_error)
    else:
        receipt['observedSha256'] = hashlib.sha256(json.dumps(observed, sort_keys=True).encode()).hexdigest()
        if observed == prior:
            receipt.update(state=rollback_state, transactionReadback='matches_preimage')
        elif verified is not None and observed == verified['snapshot']:
            receipt.update(state='committed', transactionReadback='matches_verified_postimage',
                           result=verified['result'])
        else:
            receipt.update(state='changed_requires_review', transactionReadback='differs_from_expected')
    return receipt


def source_fingerprints(wg, root):
    import decision_disposition as d
    result = {}
    directory = root / f'ontology/output/tsg/RAN/formal/parsed_reports/{wg}'
    for path in sorted(directory.glob('*.json')):
        if not path.name.startswith('_'):
            result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    for report in d.reports_for_wg(wg, root):
        path = root / report['docx_path']
        result[report['docx_path']] = d.source_blocks(str(path.resolve()))[1]
    for name in ('tdocs', 'meetings', 'agenda_items'):
        _, receipt = phase1(wg, name, root)
        result[receipt['path']] = receipt['sha256']
    review_path = root / f'ontology/input/tsg/RAN/formal/meetings/{wg}/document_decision_identity_reviews.json'
    if review_path.exists():
        result[str(review_path.relative_to(root))] = hashlib.sha256(review_path.read_bytes()).hexdigest()
        for review in json.loads(review_path.read_text())['reviews']:
            for evidence in review['actualDocumentEvidence']:
                result[evidence['path']] = evidence['sha256']
            result.update(official_review_archive_inputs(review, root))
            for evidence in review.get('registeredMasterEvidence', []):
                result[evidence['path']] = evidence['sha256']
            adjudication = review.get('sourceIdentityAdjudication', {})
            for key in ('archive', 'master'):
                if evidence := adjudication.get(key):
                    result[evidence['path']] = evidence['sha256']
            if native := adjudication.get('nativeConversionVerification'):
                result[native['nativePath']] = native['nativeSha256']
                result[native['retainedDocxPath']] = native['retainedDocxSha256']
            if native := adjudication.get('nativeAcceptedView'):
                result[native['nativePath']] = native['nativeSha256']
                result[native['derivedPath']] = native['derivedSha256']
    alias_path = root / f'ontology/input/tsg/RAN/formal/meetings/{wg}/document_decision_target_aliases.json'
    if alias_path.exists():
        result[str(alias_path.relative_to(root))] = hashlib.sha256(alias_path.read_bytes()).hexdigest()
        for alias in json.loads(alias_path.read_text())['aliases']:
            for evidence in alias['actualDocumentEvidence'] + [alias['masterEvidence']] + raw_zip_receipts(alias):
                result[evidence['path']] = evidence['sha256']
    return result


def raw_zip_receipts(alias):
    receipts = alias['rawZipEvidence']
    return receipts if isinstance(receipts, list) else [receipts]


def official_review_archive_inputs(review, root):
    """Keep optional original-archive identity corroboration inside the source fence."""
    archive = review.get('officialSourceArchive')
    if not archive:
        return {}
    result = {archive['path']: archive['sha256']}
    for member in archive['members']:
        for evidence in review['actualDocumentEvidence']:
            sibling = Path(evidence['path']).with_name(Path(member['name']).name)
            if (root / sibling).is_file():
                result[str(sibling)] = member['sha256']
    return result


def check_official_review_archive(review, root):
    archive = review.get('officialSourceArchive')
    if not archive:
        return
    check_fingerprints(official_review_archive_inputs(review, root), root)
    with zipfile.ZipFile(root / archive['path']) as original:
        for member in archive['members']:
            if hashlib.sha256(original.read(member['name'])).hexdigest() != member['sha256']:
                raise ValueError('Document identity original archive member changed')


def check_registered_master_evidence(review, root):
    """Verify optional physical registration rows used for literal header variants."""
    import openpyxl
    for evidence in review.get('registeredMasterEvidence', []):
        source = (root / evidence['path']).resolve(); source.relative_to(root.resolve())
        if hashlib.sha256(source.read_bytes()).hexdigest() != evidence['sha256']:
            raise ValueError('Identity corroboration master changed')
        book = openpyxl.load_workbook(source, read_only=True, data_only=True)
        try:
            row = next(book[evidence['sheet']].iter_rows(min_row=evidence['row'],
                       max_row=evidence['row'], values_only=True))
            values = ['' if value is None else str(value) for value in row]
            expected = ['' if value is None else str(value) for value in evidence['cells']]
            if values != expected or values[0] != review['targetTdocNumber']:
                raise ValueError('Identity corroboration exact master row changed')
        finally:
            book.close()


def check_fingerprints(fingerprints, root):
    for relative, digest in fingerprints.items():
        try:
            resolve_recorded_path(root, relative, digest)
        except ValueError as error:
            raise ValueError('Source/identity artifact changed before commit: ' + relative) from error


@lru_cache(maxsize=32)
def _phase1(path_string, mtime, size):
    path = Path(path_string)
    raw = path.read_bytes()
    graph = json.loads(raw)['@graph']
    return graph, hashlib.sha256(raw).hexdigest()


def phase1(wg, name, root):
    path = root / f'ontology/output/tsg/RAN/formal/instances/phase-1/{wg}/{name}.jsonld'
    stat = path.stat()
    graph, sha = _phase1(str(path), stat.st_mtime_ns, stat.st_size)
    return graph, {'path': str(path.relative_to(root)), 'sha256': sha}


def check_archived_slide_evidence(source, evidence_group):
    """Verify exact drawing text from an original ZIP member without extraction."""
    raw = source.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for evidence in evidence_group:
            if sha != evidence['sha256']:
                raise ValueError('Document identity review archive receipt changed')
            locator = re.fullmatch(r'(ppt/slides/slide\d+\.xml) drawing:a:t text sequence', evidence['locator'])
            if locator is None or not evidence['zipMember'].lower().endswith('.pptx'):
                raise ValueError('Unsupported archived slide identity evidence')
            payload = archive.read(evidence['zipMember'])
            if hashlib.sha256(payload).hexdigest() != evidence['memberSha256']:
                raise ValueError('Document identity review PPTX member changed')
            with zipfile.ZipFile(io.BytesIO(payload)) as presentation:
                tree = ET.fromstring(presentation.read(locator[1]))
            quote = '\n'.join(node.text or '' for node in tree.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t'))
            if quote != evidence['quote']:
                raise ValueError('Document identity review slide quote changed')


def check_word_header_evidence(source, evidence_group):
    """Bind a cover number in a specific accepted Word header part to its bytes."""
    import docx_text
    raw = source.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        parts = {}
        for evidence in evidence_group:
            match = re.fullmatch(r'(word/header\d+\.xml) accepted paragraphs \[(\d+),(\d+)\)', evidence['locator'])
            if match is None or sha != evidence['sha256']:
                raise ValueError('Unsupported or changed Word header evidence')
            if match[1] not in parts:
                tree = ET.fromstring(docx_text.zip_part(archive, match[1]))
                parts[match[1]] = [docx_text.final_text(child) for child in tree
                                  if child.tag == '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p']
            start, end = int(match[2]), int(match[3])
            texts = parts[match[1]]
            if not 0 <= start < end <= len(texts) or '\n'.join(texts[start:end]) != evidence['quote']:
                raise ValueError('Document identity review Word header quote changed')


def prop(node, key, default=None):
    return node.get(key, node.get('tdoc:' + key, default))


@lru_cache(maxsize=32)
def _endpoint_index(path_string, mtime, size, keys):
    graph, _ = _phase1(path_string, mtime, size)
    result = {}
    for node in graph:
        key = tuple(str(prop(node, field)) for field in keys)
        result.setdefault(key, []).append(node['@id'])
        if keys[0] in {'canonicalMeetingNumber', 'meetingNumber'}:
            alias = (canonical_meeting_number(key[0]),) + key[1:]
            if alias != key:
                result.setdefault(alias, []).append(node['@id'])
    for key in result:
        result[key] = list(dict.fromkeys(result[key]))
    return result


def endpoint_index(wg, name, keys, root):
    path = root / f'ontology/output/tsg/RAN/formal/instances/phase-1/{wg}/{name}.jsonld'
    stat = path.stat()
    return _endpoint_index(str(path), stat.st_mtime_ns, stat.st_size, keys)


def canonical_meeting_number(value):
    return re.sub(r'(?:[-_]e|_Electronic)$', '', str(value), flags=re.I)


def check_own_header_adjudication(review, root):
    """Bind a literal cover-label typo to original member bytes and exact rows."""
    import decision_disposition as d
    import openpyxl
    item = review.get('sourceIdentityAdjudication')
    if item is None:
        return
    classification = review.get('classification')
    if classification not in {'own_cover_tdoc_header_typo_bound_by_original_archive_and_master',
                               'cover_revision_label_correction_explicit_in_same_annex_row',
                               'own_cover_tdoc_label_discrepancy_bound_by_original_archive_master_and_exact_cr_identity'}:
        raise ValueError('Unsupported own-header source adjudication')
    target = review['targetTdocNumber']
    master = item['master']
    master_path = (root / master['path']).resolve(); master_path.relative_to(root.resolve())
    if hashlib.sha256(master_path.read_bytes()).hexdigest() != master['sha256']:
        raise ValueError('Own-header adjudication master changed')
    book = openpyxl.load_workbook(master_path, read_only=True, data_only=True)
    try:
        actual_rows = []
        for row in master['rows']:
            values = next(book[row['sheet']].iter_rows(min_row=row['row'], max_row=row['row'], values_only=True))
            normalized = lambda cells: ['' if value is None else str(value) for value in cells]
            if normalized(values) != normalized(row['cells']):
                raise ValueError('Own-header adjudication exact master row changed')
            actual_rows.append(values)
        own = [row for row in actual_rows if row[0] == target]
        if len(own) != 1:
            raise ValueError('Own-header adjudication needs one primary own document row')
        if classification == 'own_cover_tdoc_header_typo_bound_by_original_archive_and_master':
            corrections = [row for row in actual_rows if row[0] == own[0][17] and row[16] == target
                           and re.search(r'(?:tdoc number|tdoc-number)', str(row[7]), re.I)
                           and re.search(r'(?:error|correct)', str(row[7]), re.I)]
            if len(corrections) != 1:
                raise ValueError('Own-header adjudication lacks an explicit linked coversheet correction')
        elif classification == 'cover_revision_label_correction_explicit_in_same_annex_row':
            expected = f'CR rev{item["reportRevision"]} is correct but CR rev{item["coverRevision"]} used in CR coversheet'
            own_quote = '\n'.join(evidence['quote'] for evidence in review['actualDocumentEvidence'])
            fields = review['sourceAnnexFields']
            header = re.search(r'\|\s*(\d{2,3}\.\d{3}(?:-\d+)?)\s*\|\s*CR\s*\|\s*(\d+)\s*\|\s*rev\s*\|\s*(\d+)\s*\|\s*Current version:', own_quote, re.I)
            if (expected not in review['decisionEvidence']['decisionText'] or not header
                    or target not in d.tdoc_ids(own_quote) or fields['spec'] != header[1]
                    or int(fields['crNumber']) != int(header[2])
                    or int(header[3]) != item['coverRevision']
                    or int(fields['crRevision']) != item['reportRevision']
                    or str(own[0][19]) != fields['spec']
                    or int(own[0][22]) != int(fields['crNumber'])
                    or int(own[0][23]) != item['reportRevision']):
                raise ValueError('Cover revision label correction lacks exact same-row and master support')
        else:
            fields = review['sourceAnnexFields']
            actual = own[0]
            if (str(actual[19]) != fields['spec'] or int(actual[22]) != int(fields['crNumber'])
                    or str(actual[18]) != fields['release']
                    or (fields.get('crRevision') is not None and
                        int(actual[23] or 0) != int(fields['crRevision']))):
                raise ValueError('Own-label adjudication master CR identity differs from the exact source row')
            check_annex_own_cr_fields({'document_entry': {'sourceFields': fields}},
                dict(review, identityStatus='same_document_source_verified'))
            quote = '\n'.join(evidence['quote'] for evidence in review['actualDocumentEvidence'])
            wrong_number = item['literalCoverTdocNumber']
            if wrong_number == target or wrong_number not in re.findall(r'R[1-5]-\s*\d{6,8}', quote):
                # Compare only insignificant space after the literal hyphen.
                ids = [re.sub(r'\s+', '', value) for value in re.findall(r'R[1-5]-\s*\d{6,8}', quote)]
                if wrong_number == target or wrong_number not in ids:
                    raise ValueError('Own-label adjudication does not preserve the literal differing cover number')
    finally:
        book.close()
    archive = item['archive']
    archive_path = (root / archive['path']).resolve(); archive_path.relative_to(root.resolve())
    if hashlib.sha256(archive_path.read_bytes()).hexdigest() != archive['sha256']:
        raise ValueError('Own-header adjudication original archive changed')
    actual_shas = {proof['sha256'] for proof in review['actualDocumentEvidence']}
    native = item.get('nativeConversionVerification')
    accepted = item.get('nativeAcceptedView')
    with zipfile.ZipFile(archive_path) as original:
        for member in archive['members']:
            digest = hashlib.sha256(original.read(member['name'])).hexdigest()
            if digest != member['sha256'] or (digest not in actual_shas and
                    (native is None or digest != native['nativeSha256']) and
                    (accepted is None or digest != accepted['nativeSha256'])):
                raise ValueError('Own-header adjudication member is not the checked own source')
    if native:
        for path_key, sha_key in (('nativePath', 'nativeSha256'), ('retainedDocxPath', 'retainedDocxSha256')):
            source = (root / native[path_key]).resolve(); source.relative_to(root.resolve())
            if hashlib.sha256(source.read_bytes()).hexdigest() != native[sha_key]:
                raise ValueError('Own-header adjudication conversion source changed')
        texts, digest, _ = d.source_blocks(str((root / native['retainedDocxPath']).resolve()))
        body_sha = hashlib.sha256(json.dumps(list(texts), ensure_ascii=False,
                                            separators=(',', ':')).encode()).hexdigest()
        if (digest not in actual_shas or not native['allAcceptedBodyBlocksEqual']
                or len(texts) != native['acceptedBlocks'] or body_sha != native['acceptedBodySha256']):
            raise ValueError('Own-header adjudication checked conversion view changed')
        d.source_blocks.cache_clear()
    if accepted:
        receipt = accepted['conversionReceipt']
        for path_key, sha_key in (('nativePath', 'nativeSha256'), ('derivedPath', 'derivedSha256')):
            source = (root / accepted[path_key]).resolve(); source.relative_to(root.resolve())
            if hashlib.sha256(source.read_bytes()).hexdigest() != accepted[sha_key]:
                raise ValueError('Native accepted identity view changed')
        if (accepted['derivedSha256'] not in actual_shas
                or receipt.get('method') != 'native_accepted_uno_export_reopen'
                or receipt.get('status') != 'verified' or not receipt.get('strictXml')
                or receipt.get('redlinesAfter') != 0
                or receipt.get('acceptedRenderedText', {}).get('equal') is not True
                or receipt.get('sourceSha256') != accepted['nativeSha256']
                or receipt.get('outputSha256') != accepted['derivedSha256']):
            raise ValueError('Native accepted identity view lacks its exact source and verified rendering receipt')


@lru_cache(maxsize=16)
def _tdoc_index(path_string, mtime, size):
    graph, sha = _phase1(path_string, mtime, size)
    result = {}
    for node in graph:
        number = prop(node, 'tdocNumber')
        if number in result:
            raise ValueError('Duplicate Phase-1 document identity: ' + str(number))
        result[number] = node
    return result, sha


@lru_cache(maxsize=16)
def _document_identity_reviews(path_string, mtime, size):
    import decision_disposition as d
    path = Path(path_string)
    root = next(parent for parent in path.parents if (parent / '.git').exists())
    raw = path.read_bytes()
    reviews = {}
    for review in json.loads(raw)['reviews']:
        key = (review['meetingId'], review['targetTdocNumber'], review['decisionEvidence']['locator'])
        if key in reviews:
            raise ValueError('Duplicate document identity review')
        if review['identityStatus'] not in {'same_document_source_verified', 'same_document_metadata_discrepancy', 'identity_conflict',
                                            'unresolved_source_document'}:
            raise ValueError('Unsupported document identity review status')
        all_quotes = '\n'.join(evidence['quote'] for evidence in review['actualDocumentEvidence'])
        unresolved = review['identityStatus'] == 'unresolved_source_document'
        if unresolved and (review['actualDocumentEvidence'] or not review.get('inventoryReason')):
            raise ValueError('Unresolved source review requires an explicit inventory reason and no fabricated document evidence')
        if (review['identityStatus'] == 'same_document_source_verified'
                and review['targetTdocNumber'] not in d.tdoc_ids(all_quotes)):
            raise ValueError('A normal own-source identity review requires the exact document number in source text')
        if (not unresolved and review['targetTdocNumber'] not in d.tdoc_ids(all_quotes)
                and not any(review['targetTdocNumber'] in Path(evidence['path']).name
                            for evidence in review['actualDocumentEvidence'])):
            raise ValueError('Document identity evidence does not identify the reviewed Tdoc')
        evidence_by_path = {}
        for evidence in review['actualDocumentEvidence']:
            evidence_by_path.setdefault(evidence['path'], []).append(evidence)
        for relative, evidence_group in evidence_by_path.items():
            source = (root / relative).resolve()
            source.relative_to(root.resolve())
            if any('zipMember' in evidence for evidence in evidence_group):
                if not all('zipMember' in evidence for evidence in evidence_group):
                    raise ValueError('Mixed archive and DOCX identity receipts')
                check_archived_slide_evidence(source, evidence_group)
                continue
            headers = [item for item in evidence_group if re.match(r'word/header\d+\.xml ', item['locator'])]
            if headers:
                check_word_header_evidence(source, headers)
                evidence_group = [item for item in evidence_group if item not in headers]
                if not evidence_group:
                    continue
            try:
                texts, sha, _ = d.source_blocks(str(source))
                if hashlib.sha256(source.read_bytes()).hexdigest() != sha:
                    raise ValueError('Document identity review actual-source receipt changed')
                for evidence in evidence_group:
                    match = re.fullmatch(r'word/document.xml accepted body blocks \[(\d+),(\d+)\)', evidence['locator'])
                    if (match is None or sha != evidence['sha256'] or
                            '\n'.join(texts[int(match[1]):int(match[2])]) != evidence['quote']):
                        raise ValueError('Document identity review actual-source receipt changed')
            finally:
                # The checked review is cached above; retain no full DOCX bodies
                # from the thousands of independent cover evidence documents.
                d.source_blocks.cache_clear()
        check_own_header_adjudication(review, root)
        check_official_review_archive(review, root)
        check_registered_master_evidence(review, root)
        reviews[key] = dict(review, receiptPath=str(path.relative_to(root)),
                            receiptSha256=hashlib.sha256(raw).hexdigest())
    return reviews


def document_evidence_locator(event):
    """Keep a row disposition distinct from the other rows in its source table."""
    start, end = event['body_blocks']
    field = event['document_entry']
    if field.get('sourceKind') == 'annex_cr_table_row':
        table = field['annexTable']
        return (f'word/document.xml accepted table block {table["tableBlock"]} row {table["acceptedRow"]}; '
                f'governing body blocks [{start},{end})')
    return f'word/document.xml accepted body blocks [{start},{end})'


def check_annex_own_cr_fields(event, review):
    """A normal Annex review binds every specified row field to its actual cover."""
    if review['identityStatus'] != 'same_document_source_verified':
        return
    quote = '\n'.join(item['quote'] for item in review['actualDocumentEvidence'])
    headers = list(re.finditer(r'(?<![\w.])(?:(?:TS|TR)\s*)?(\d{2,3}\.\d{3}(?:-\d+)?)>?\s*\|\s*CR\s*\|\s*([^|]*)\|\s*(?:⌘\s*)?rev\s*\|\s*([^|]*)\|\s*(?:⌘\s*)?Current version:', quote, re.I))
    # 양식의 자리표시 꺾쇠(`<0761>`)는 번호가 아니다. 꺾쇠만 벗기고 안의 글자는 그대로 읽는다.
    identities = {(match[1], re.sub(r'^CR\s*(?=\d)', '', re.sub(r'^<(.*)>$', r'\1', match[2].strip()), flags=re.I),
                   match[3].strip()) for match in headers}
    if len(identities) != 1:
        raise ValueError('Normal Annex identity needs one actual assigned CR-form identity')
    spec, number, revision = identities.pop()
    fields = event['document_entry']['sourceFields']
    if not number.isdigit():
        if (fields.get('crNumber') is not None
                or event['document_entry'].get('annexTable', {}).get('tableScope') not in ('in_principle', 'endorsed')
                or re.fullmatch(r'(?:-+|x{3,4}|CRNum|Num|draftCR|DRAFT)?', number, re.I) is None):
            raise ValueError('Normal Annex identity needs an assigned number or an explicitly unassigned draft scope')
    if ((fields.get('spec') and fields['spec'] != spec)
            or (fields.get('crNumber') is not None and int(fields['crNumber']) != int(number))):
        raise ValueError('Normal Annex actual CR identity differs from the checked source row')
    # CR 표지는 최초본의 개정 칸에 '-'를 적는다. 회의록 행이 같은 최초본을 0으로 적은 경우만 같은 값으로 읽는다.
    if revision == '-' and fields.get('crRevision') is not None and int(fields['crRevision']) == 0:
        revision = '0'
    if (fields.get('crRevision') is not None and
            (not revision.isdigit() or int(fields['crRevision']) != int(revision))):
        raise ValueError('Normal Annex actual CR revision differs from the checked source row')
    release_cell = re.search(r'Release:\s*(?:⌘\s*)?\|\s*([^|\n]*)', quote, re.I)
    release_value = re.sub(r'^<Release>\s*', '', release_cell[1].strip(), flags=re.I) if release_cell else ''
    # 일부 표지는 Release 값과 양식 안내문을 한 칸에 둔다. 안내문의 고정 첫 구절부터는 값이 아니다.
    release_value = re.sub(r'\s+Use one of the following (?:releases|categories)\b.*$', '', release_value, flags=re.I | re.S)
    release = re.fullmatch(r'(?:Rel(?:ease)?[-\s]*|R)?(\d+)', release_value, re.I)
    if fields.get('release') and (not release or fields['release'] != 'Rel-' + release[1]):
        raise ValueError('Normal Annex actual CR release differs from the checked source row')


def document_identity_review(event, target, root):
    wg = event['meeting_id'].split('#')[0]
    path = root / f'ontology/input/tsg/RAN/formal/meetings/{wg}/document_decision_identity_reviews.json'
    if not path.exists():
        return None
    stat = path.stat()
    locator = document_evidence_locator(event)
    review = _document_identity_reviews(str(path), stat.st_mtime_ns, stat.st_size).get((event['meeting_id'], target, locator))
    if review:
        import decision_disposition as d
        receipt = review['decisionEvidence']
        source = root / event['document_entry']['sourcePath']
        if event['document_entry'].get('sourceKind') == 'annex_cr_table_row':
            from document_decision_source import annex_source_evidence
            checked = annex_source_evidence(event, root)
            expected = {key: checked[key] for key in ('path', 'sha256', 'locator', 'quote')}
            check_annex_own_cr_fields(event, review)
        else:
            texts, digest, _ = d.source_blocks(str(source.resolve()))
            expected = {'path': str(source.relative_to(root)), 'sha256': digest,
                        'locator': locator, 'quote': '\n'.join(texts[slice(*event['body_blocks'])])}
        if any(receipt[key] != value for key, value in expected.items()):
            raise ValueError('Document identity review report source changed')
        for evidence in review['actualDocumentEvidence']:
            if hashlib.sha256((root / evidence['path']).read_bytes()).hexdigest() != evidence['sha256']:
                raise ValueError('Document identity review actual source changed')
    return review


@lru_cache(maxsize=16)
def _target_aliases(path_string, mtime, size):
    import decision_disposition as d
    import openpyxl
    path = Path(path_string)
    root = next(parent for parent in path.parents if (parent / '.git').exists())
    raw = path.read_bytes()
    aliases = {}
    for alias in json.loads(raw)['aliases']:
        key = (alias['meetingId'], alias['sourceTdocNumber'], alias['decisionEvidence']['locator'])
        if key in aliases or not re.fullmatch(r'R[1-5]-\d{6,8}', alias['resolvedTdocNumber']):
            raise ValueError('Invalid or duplicate entry-specific target alias')
        for evidence in alias['actualDocumentEvidence']:
            source = (root / evidence['path']).resolve(); source.relative_to(root.resolve())
            texts, sha, _ = d.source_blocks(str(source))
            match = re.fullmatch(r'word/document.xml accepted body blocks \[(\d+),(\d+)\)', evidence['locator'])
            if (match is None or sha != evidence['sha256'] or hashlib.sha256(source.read_bytes()).hexdigest() != sha
                    or '\n'.join(texts[int(match[1]):int(match[2])]) != evidence['quote']):
                raise ValueError('Target alias actual document evidence changed')
        master = alias['masterEvidence']; master_path = (root / master['path']).resolve()
        master_path.relative_to(root.resolve())
        if hashlib.sha256(master_path.read_bytes()).hexdigest() != master['sha256']:
            raise ValueError('Target alias master evidence changed')
        book = openpyxl.load_workbook(master_path, read_only=True, data_only=True)
        try:
            sheet = book[master['sheet']]
            headers = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))
            values = next(sheet.iter_rows(min_row=master['row'], max_row=master['row'], values_only=True))
            actual = {str(key): '' if value is None else str(value) for key, value in zip(headers, values)}
            if any(actual.get(key) != value for key, value in master['fields'].items()):
                raise ValueError('Target alias exact master row changed')
            if actual.get('TDoc') != alias['resolvedTdocNumber']:
                raise ValueError('Target alias is not the checked primary TDoc')
        finally:
            book.close()
        for archive in raw_zip_receipts(alias):
            archive_path = (root / archive['path']).resolve()
            archive_path.relative_to(root.resolve())
            if hashlib.sha256(archive_path.read_bytes()).hexdigest() != archive['sha256']:
                raise ValueError('Target alias raw ZIP changed')
            with zipfile.ZipFile(archive_path) as zf:
                members = archive['members']
                if members and isinstance(members[0], dict):
                    actual_shas = {item['sha256'] for item in alias['actualDocumentEvidence']}
                    for member in members:
                        digest = hashlib.sha256(zf.read(member['name'])).hexdigest()
                        if digest != member['sha256'] or digest not in actual_shas:
                            raise ValueError('Target alias ZIP member does not match the checked actual document')
                elif sorted(zf.namelist()) != sorted(members):
                    raise ValueError('Target alias ZIP membership changed')
        aliases[key] = dict(alias, receiptPath=str(path.relative_to(root)),
                            receiptSha256=hashlib.sha256(raw).hexdigest())
    return aliases


def resolve_document_target(event, target, root):
    """Resolve a proven spelling error only within its exact original source entry."""
    wg = event['meeting_id'].split('#')[0]
    path = root / f'ontology/input/tsg/RAN/formal/meetings/{wg}/document_decision_target_aliases.json'
    if not path.exists():
        return target, None
    stat = path.stat()
    locator = document_evidence_locator(event)
    alias = _target_aliases(str(path), stat.st_mtime_ns, stat.st_size).get((event['meeting_id'], target, locator))
    if alias:
        import decision_disposition as d
        source = root / event['document_entry']['sourcePath']
        expected = alias['decisionEvidence']
        if event['document_entry'].get('sourceKind') == 'annex_cr_table_row':
            from document_decision_source import annex_source_evidence
            checked = annex_source_evidence(event, root)
        else:
            texts, sha, _ = d.source_blocks(str(source.resolve()))
            checked = {'path': str(source.relative_to(root)), 'sha256': sha,
                       'locator': locator, 'quote': '\n'.join(texts[slice(*event['body_blocks'])])}
        if any(expected[key] != checked[key] for key in ('path', 'sha256', 'locator', 'quote')):
            raise ValueError('Entry-specific target alias report source changed')
        return alias['resolvedTdocNumber'], alias
    return target, None


def assess_document_identity(event, target, code, assessment, root):
    """Bind an explicit CR descriptor to the actual target, preserving conflicts."""
    wg = event['meeting_id'].split('#')[0]
    path = root / f'ontology/output/tsg/RAN/formal/instances/phase-1/{wg}/tdocs.jsonld'
    stat = path.stat()
    index, sha = _tdoc_index(str(path), stat.st_mtime_ns, stat.st_size)
    resolved, alias = resolve_document_target(event, target, root)
    actual = index.get(resolved)
    field = event['document_entry']
    identity = {'path': str(path.relative_to(root)), 'sha256': sha,
                'targetPresent': actual is not None,
                'sourceDocumentType': field['documentType']}
    if alias:
        assessment = dict(assessment, targetAlias=alias)
    # A direct source adjudication remains binding even when a narrower metadata
    # parser no longer observes a conflict. Missing source documents cannot be
    # promoted to identified targets by removing a descriptor comparison.
    review = document_identity_review(event, target, root)
    if review and review['identityStatus'] in {'identity_conflict', 'unresolved_source_document'}:
        return 'ambiguous', dict(assessment, rule='source_target_identity_review_pending',
            scope='undetermined', sourceDispositionCode=code, identityStatus=review['identityStatus'],
            targetIdentity=identity, identityReview=review)
    if actual is None:
        if field.get('sourceKind') == 'annex_cr_table_row' and review is None and alias is None:
            return 'ambiguous', dict(assessment, rule='annex_target_identity_requires_own_source_review',
                scope='undetermined', sourceDispositionCode=code, targetIdentity=identity)
        return code, dict(assessment, targetIdentity=identity)
    identity.update({'id': actual['@id'], 'type': prop(actual, 'type'),
                     'crNumber': prop(actual, 'crNumber'), 'modifies': prop(actual, 'modifies'),
                     'targetRelease': prop(actual, 'targetRelease'),
                     'crRevision': prop(actual, 'crRevision')})
    conflicts = []
    revision_conflicts = []
    # The output explicitly named by "approved as" has its own identity; the
    # predecessor's CR descriptor does not describe that output's metadata.
    if target == event['subject_tdoc']:
        source_kind = field['documentType'].lower().replace(' ', '')
        actual_cr = str(identity['type']).lower().replace(' ', '') in {'cr', 'draftcr', 'pcr'}
        # A draft CR can be a discussion/text proposal rather than a formal CR
        # form. Preserve that source kind without changing the actual Tdoc type.
        if source_kind == 'cr' and not actual_cr:
            conflicts.append('source_CR_type_differs_from_target_type')
        import decision_disposition as d
        texts, _, _ = d.source_blocks(str((root / next_source_path(event, root)).resolve()))
        if field.get('sourceKind') == 'annex_cr_table_row':
            # These are separately checked header-indexed cells of this exact
            # accepted row. Titles and adjacent rows cannot supply CR identity.
            source_fields = field['sourceFields']
            metadata = str(source_fields.get('spec') or '') + ' CR-' + str(source_fields.get('crNumber') or '')
            if source_fields.get('crRevision') is not None and str(source_fields['crRevision']).isdigit():
                metadata += ' rev' + str(source_fields['crRevision'])
            if source_fields.get('release'):
                metadata += ' (' + source_fields['release'] + ')'
            identity['sourceFields'] = source_fields
        else:
            metadata = texts[field['typeBlock']] if field['typeBlock'] is not None else field['headerText']
        descriptor = re.search(r'\b(\d{2,3}\.\d{3}(?:-\d+)?)\s*(?:v\S+\s*)?\bCR\s*[-#]?\s*(\d+)\b', metadata, re.I)
        if descriptor:
            identity['sourceSpec'], identity['sourceCrNumber'] = descriptor.groups()
            source_number = int(descriptor[2])
            actual_number = identity['crNumber']
            # CR-0000 is an explicit draft placeholder, not a concrete identity
            # that can contradict a numbered formal CR (or vice versa).
            if (actual_cr and actual_number is not None and str(actual_number).isdigit()
                    and int(str(actual_number)) and source_number
                    and int(str(actual_number)) != source_number):
                conflicts.append('source_CR_number_differs_from_target')
            modifies = str(identity['modifies'] or '').split('/')[-1].replace('_', '.')
            if actual_cr and modifies and modifies != descriptor[1]:
                conflicts.append('source_CR_spec_differs_from_target')
            revision = re.match(r'\s*rev(?:ision)?\.?\s*[:#-]?\s*(\d+)\b',
                                metadata[descriptor.end():], re.I)
            if revision:
                identity['sourceCrRevision'] = int(revision[1])
                actual_revision = identity['crRevision']
                if actual_revision is None or not str(actual_revision).isdigit():
                    # 등록 정보에 개정 번호가 없을 때는 대상 문서 자신의 표지가 개정 번호를 정한다.
                    # 부록 행의 일치 검토 기록은 불러올 때 표지 개정 칸과 행의 값을 대조해 통과한 것이다.
                    if (field.get('sourceKind') == 'annex_cr_table_row' and review
                            and review['identityStatus'] == 'same_document_source_verified'):
                        identity['crRevisionBoundBy'] = 'own_cover_identity_review'
                    else:
                        revision_conflicts.append('source_CR_revision_not_bound_to_target')
                elif int(revision[1]) != int(str(actual_revision)):
                    revision_conflicts.append('source_CR_revision_differs_from_target')
        # Release belongs to the checked CR descriptor. Titles often mention
        # older releases and non-CR work plans have no CR identity descriptor.
        release = (re.search(r'\bRel\s*[-_ ]\s*(\d+)\b', metadata[descriptor.end():], re.I)
                   if descriptor and actual_cr else None)
        actual_release = re.search(r'Rel[-_ ](\d+)', str(identity['targetRelease']), re.I)
        if release and actual_release:
            identity['sourceRelease'] = 'Rel-' + release[1]
            if int(release[1]) != int(actual_release[1]):
                conflicts.append('source_CR_release_differs_from_target')
    if conflicts or revision_conflicts:
        identity['conflicts'] = conflicts + revision_conflicts
        # Same document-number identity does not identify the particular CR
        # revision approved in the report. A metadata review cannot extend an
        # approval to retained bytes of a different (or unknown) revision.
        if not revision_conflicts and review and review['identityStatus'] == 'same_document_metadata_discrepancy':
            return code, dict(assessment, targetIdentity=identity,
                identityStatus='same_document_metadata_discrepancy', identityReview=review)
        pending = dict(assessment, rule='source_target_identity_conflict',
            scope='undetermined', sourceDispositionCode=code, identityStatus='identity_conflict', targetIdentity=identity)
        if review:
            pending['identityReview'] = review
        return 'ambiguous', pending
    if field.get('sourceKind') == 'annex_cr_table_row' and review is None and alias is None:
        return 'ambiguous', dict(assessment, rule='annex_target_identity_requires_own_source_review',
            scope='undetermined', sourceDispositionCode=code, targetIdentity=identity)
    if review and field.get('sourceKind') == 'annex_cr_table_row':
        return code, dict(assessment, targetIdentity=identity,
                          identityStatus=review['identityStatus'], identityReview=review)
    return code, dict(assessment, targetIdentity=identity)


def next_source_path(event, root):
    # document_decisions sets this source identity; no filename guessing.
    return event['document_entry']['sourcePath']


def document_resolution_node(event, root=None):
    import decision_disposition as d
    from document_decision_source import classify_document_decision
    root = root or d.ROOT
    wg = event['meeting_id'].split('#')[0]
    meetings = endpoint_index(wg, 'meetings', ('canonicalMeetingNumber',), root)
    candidates = meetings.get((event['meeting_id'],), [])
    if not candidates:
        candidates = meetings.get((canonical_meeting_number(event['meeting_id']),), [])
    if len(candidates) != 1:
        # A cancelled meeting and the e-meeting that replaced it share one canonical
        # number; the report's own meeting number then names the exact meeting.
        candidates = endpoint_index(wg, 'meetings', ('meetingNumber',), root).get((event['meeting_id'],), [])
    if len(candidates) != 1:
        raise ValueError('Document disposition meeting must resolve to exactly one canonical Phase-1 identity: ' + event['meeting_id'])
    codes = []
    for target in event['referenced_tdocs']:
        code = classify_document_decision(event, target)[0]
        code, _ = assess_document_identity(event, target, code, {}, root)
        codes.append(code)
    node = {'@id': 'tdoc:resolution/' + event['decision_id'],
        '@type': ['Resolution', 'Agreement'] if 'agreed' in codes else ['Resolution'],
        'resolutionId': event['decision_id'], 'content': event['content'],
        'resolutionScope': 'document_disposition', 'madeAt': candidates[0],
        'sequence': event['sequence'],
        'references': ['tdoc:' + resolve_document_target(event, target, root)[0] for target in event['referenced_tdocs']],
        'aboutTdoc': 'tdoc:' + resolve_document_target(event, event['subject_tdoc'], root)[0]}
    if event['agenda_item'] != 'UNKNOWN':
        agendas = endpoint_index(wg, 'agenda_items', ('meetingNumber', 'agendaNumber'), root)
        number = event['meeting_id'].split('#', 1)[1]
        candidates = agendas.get((number, event['agenda_item']), [])
        if not candidates:
            candidates = agendas.get((canonical_meeting_number(number), event['agenda_item']), [])
        if len(candidates) > 1:
            raise ValueError('Nonunique canonical agenda identity')
        if candidates:
            node['resolutionBelongsTo'] = candidates[0]
    return node


def document_resolution_nodes(reports, root=None):
    import decision_disposition as d
    from document_decision_source import document_decisions
    root = root or d.ROOT
    sources = [document_decisions(report, root)[0] for report in reports]
    wg = reports[0]['meeting_id'].split('#')[0] if reports else None
    paths = ([root / f'ontology/output/tsg/RAN/formal/instances/phase-1/{wg}/{name}.jsonld'
              for name in ('tdocs', 'meetings', 'agenda_items')] if wg else [])
    review = root / f'ontology/input/tsg/RAN/formal/meetings/{wg}/document_decision_identity_reviews.json'
    if review.exists():
        paths.append(review)
    alias = root / f'ontology/input/tsg/RAN/formal/meetings/{wg}/document_decision_target_aliases.json'
    if alias.exists():
        paths.append(alias)
    key = (str(root), tuple(id(events) for events in sources),
           tuple((str(path), path.stat().st_mtime_ns, path.stat().st_size) for path in paths))
    if key not in _NODE_CACHE:
        _NODE_CACHE[key] = [document_resolution_node(event, root) for events in sources for event in events]
    return _NODE_CACHE[key]


def storage_rows(nodes):
    from ontology.jsonld_context import reference_identifier
    result = []
    for node in nodes:
        if not node['resolutionId'].startswith('DOC-') or node.get('resolutionScope') != 'document_disposition':
            raise ValueError('Only explicitly scoped document source events are owned')
        result.append({'properties': {key: value for key, value in node.items()
                      if not key.startswith('@') and key not in {'madeAt', 'references', 'aboutTdoc', 'resolutionBelongsTo'}},
            'agreement': 'Agreement' in node['@type'], 'meetingId': node['madeAt'],
            'agendaId': node.get('resolutionBelongsTo'),
            'references': [reference_identifier(value) for value in node['references']],
            'aboutTdoc': reference_identifier(node['aboutTdoc'])})
    if len({row['properties']['resolutionId'] for row in result}) != len(result):
        raise ValueError('Duplicate document source event identity')
    return result


def source_event_snapshot(tx, ids):
    result = tx.run('''MATCH (r:Resolution) WHERE r.resolutionId IN $ids
        OPTIONAL MATCH (r)-[e:MADE_AT|RESOLUTION_BELONGS_TO|REFERENCES|ABOUT_TDOC]->(n)
        RETURN r.resolutionId AS resolutionId, properties(r) AS properties, labels(r) AS labels,
               collect({type:type(e), properties:properties(e), target:coalesce(n.id,n.tdocNumber)}) AS edges
        ORDER BY resolutionId''', ids=ids).data()
    for row in result:
        row['labels'].sort()
        row['edges'].sort(key=lambda value: json.dumps(value, sort_keys=True))
    return result


def load_document_resolutions(session, nodes, root=None, *, transaction=None):
    """Write only owned source events after a durable preimage and endpoint fences."""
    import decision_disposition as d
    root = root or d.ROOT
    rows = storage_rows(nodes)
    if not rows:
        return {'sourceEvents': 0}
    wg = nodes[0]['madeAt'].split('/')[-1].split('_')[0]
    ids = [row['properties']['resolutionId'] for row in rows]
    reader = transaction if transaction is not None else session
    prior = source_event_snapshot(reader, ids)
    fingerprints = source_fingerprints(wg, root)
    check_fingerprints(fingerprints, root)
    journal_dir = axis.tree_path('logs_common', wg=wg, root=root) / 'verification' / 'decision-dispositions'
    journal_dir.mkdir(parents=True, exist_ok=True)
    journal = journal_dir / ('source-event-preimage-' + uuid.uuid4().hex + '.json')
    recovery = {'wg': wg, 'before': prior, 'incoming': rows, 'sourceFiles': fingerprints,
                'state': 'prepared', 'qualificationStatus': 'awaiting_dispositions'}
    durable_json(journal, recovery)
    completed_postimage = None
    def write(tx):
        nonlocal completed_postimage
        completed_postimage = None
        if source_event_snapshot(tx, ids) != prior:
            raise ValueError('Source event preimage changed; no writes performed')
        for previous in prior:
            if previous['properties'].get('resolutionScope') != 'document_disposition':
                raise ValueError('Source event identity collides with a different Resolution')
        meetings = tx.run('UNWIND $ids AS id OPTIONAL MATCH(m:Meeting {id:id}) RETURN id,count(m) AS n',
                          ids=sorted({row['meetingId'] for row in rows})).data()
        if any(row['n'] != 1 for row in meetings):
            raise ValueError('Source document Meeting endpoints missing or nonunique: ' + str(meetings))
        numbers = sorted({number for row in rows for number in row['references']})
        targets = tx.run('MATCH(t:Tdoc) WHERE t.tdocNumber IN $numbers RETURN t.tdocNumber AS number,t.id AS id', numbers=numbers).data()
        target_ids = {}
        for target in targets:
            if target['number'] in target_ids:
                raise ValueError('Nonunique source document target endpoint')
            target_ids[target['number']] = target['id'] or target['number']
        agendas = tx.run('MATCH(a:AgendaItem) WHERE a.id IN $ids RETURN a.id AS id',
                        ids=sorted({row['agendaId'] for row in rows if row['agendaId']})).data()
        agenda_ids = {item['id'] for item in agendas}
        if len(agenda_ids) != len(agendas):
            raise ValueError('Nonunique source document agenda endpoint')
        # Only the four source-owned relationship types of these DOC events
        # are replaced. Incoming qualified assertions and technical AGR/CON/WA
        # events remain outside this transaction's ownership.
        tx.run('''MATCH(r:Resolution)-[e:MADE_AT|RESOLUTION_BELONGS_TO|REFERENCES|ABOUT_TDOC]->()
                  WHERE r.resolutionId IN $ids DELETE e''', ids=ids).consume()
        # Batches share one transaction, so a failed postcondition rolls back
        # every source event in this WG, while Bolt payloads remain bounded.
        for offset in range(0, len(rows), 1000):
            batch = rows[offset:offset + 1000]
            tx.run('''UNWIND $rows AS row
                MERGE(r:Resolution {resolutionId:row.properties.resolutionId}) SET r=row.properties
                REMOVE r:Agreement
                FOREACH(_ IN CASE WHEN row.agreement THEN [1] ELSE [] END | SET r:Agreement)
                WITH r,row MATCH(m:Meeting {id:row.meetingId}) MERGE(r)-[:MADE_AT]->(m)
                WITH r,row OPTIONAL MATCH(a:AgendaItem {id:row.agendaId})
                FOREACH(_ IN CASE WHEN a IS NULL THEN [] ELSE [1] END | MERGE(r)-[:RESOLUTION_BELONGS_TO]->(a))
                WITH r,row OPTIONAL MATCH(t:Tdoc {tdocNumber:row.aboutTdoc})
                FOREACH(_ IN CASE WHEN t IS NULL THEN [] ELSE [1] END | MERGE(r)-[:ABOUT_TDOC]->(t))''', rows=batch).consume()
            tx.run('''UNWIND $rows AS row MATCH(r:Resolution {resolutionId:row.properties.resolutionId})
                UNWIND row.references AS number MATCH(t:Tdoc {tdocNumber:number})
                MERGE(r)-[:REFERENCES]->(t)''', rows=batch).consume()
        after = source_event_snapshot(tx, ids)
        actual = {row['resolutionId']: row for row in after}
        if len(actual) != len(rows):
            raise ValueError('Source event count postcondition failed')
        for row in rows:
            saved = actual[row['properties']['resolutionId']]
            if saved['properties'] != row['properties'] or ('Agreement' in saved['labels']) != row['agreement']:
                raise ValueError('Source event property/label postcondition failed')
            if [edge['target'] for edge in saved['edges'] if edge['type'] == 'MADE_AT'] != [row['meetingId']]:
                raise ValueError('Source event canonical Meeting postcondition failed')
            expected_edges = [('MADE_AT', row['meetingId'])]
            if row['agendaId'] in agenda_ids:
                expected_edges.append(('RESOLUTION_BELONGS_TO', row['agendaId']))
            if row['aboutTdoc'] in target_ids:
                expected_edges.append(('ABOUT_TDOC', target_ids[row['aboutTdoc']]))
            expected_edges.extend(('REFERENCES', target_ids[number]) for number in row['references'] if number in target_ids)
            actual_edges = [(edge['type'], edge['target']) for edge in saved['edges'] if edge['type']]
            if sorted(actual_edges) != sorted(expected_edges) or any(edge['properties'] for edge in saved['edges'] if edge['type']):
                raise ValueError('Source event complete owned-edge postcondition failed')
        check_fingerprints(fingerprints, root)
        prior_index = {row['resolutionId']: row for row in prior}
        result = {'sourceEvents': len(rows), 'agreements': sum(row['agreement'] for row in rows),
                'changedSourceEvents': sum(prior_index.get(row['resolutionId']) != row for row in after),
                'missingTdocTargets': sorted(set(numbers) - set(target_ids)),
                'missingAgendaEndpoints': sorted({row['agendaId'] for row in rows if row['agendaId']} - agenda_ids),
                'preimageJournal': str(journal.relative_to(root)),
                'postimageSha256': hashlib.sha256(json.dumps(after, sort_keys=True).encode()).hexdigest()}
        completed_postimage = {'snapshot': after, 'result': result}
        return result
    if transaction is not None:
        try:
            result = write(transaction)
            durable_json(journal, dict(recovery, state='awaiting_outer_commit', result=result))
        except Exception as error:
            durable_json(journal, dict(recovery, state='commit_outcome_unknown',
                stage='caller_write_failed', error=str(error)))
            raise
        return result
    try:
        result = session.execute_write(write)
    except Exception as error:
        failure = transaction_failure_receipt(error, prior, completed_postimage,
            lambda: source_event_snapshot(session, ids))
        durable_json(journal, dict(recovery, **failure))
        raise
    durable_json(journal, dict(recovery, state='committed', result=result))
    return result


OWNED_EVENT_EDGES = {'MADE_AT', 'RESOLUTION_BELONGS_TO', 'REFERENCES', 'ABOUT_TDOC', 'HAS_DISPOSITION'}


def absent_event_snapshot(tx, ids):
    """Complete properties and both edge directions of the events to retire."""
    result = tx.run('''MATCH (r:Resolution) WHERE r.resolutionId IN $ids
        OPTIONAL MATCH (r)-[e]-(n)
        RETURN r.resolutionId AS resolutionId, properties(r) AS properties, labels(r) AS labels,
               collect({type:type(e), outgoing:startNode(e)=r, properties:properties(e), labels:labels(n),
                        neighbour:coalesce(n.dispositionId,n.id,n.tdocNumber),
                        disposition:CASE WHEN n:DecisionDisposition THEN properties(n) END}) AS edges
        ORDER BY resolutionId''', ids=ids).data()
    for row in result:
        row['labels'].sort()
        row['edges'] = sorted((edge for edge in row['edges'] if edge['type']),
                              key=lambda value: json.dumps(value, sort_keys=True))
    return result


def check_retirable_event(row, current_dispositions):
    """An absent event owns only source edges, superseded assertions and candidate anchors."""
    rid = row['resolutionId']
    if row['properties'].get('resolutionScope') != 'document_disposition' or not rid.startswith('DOC-'):
        raise ValueError(f'Retirement reaches a Resolution outside the source event layer: {rid}')
    for edge in row['edges']:
        if edge['outgoing'] and edge['type'] in OWNED_EVENT_EDGES - {'HAS_DISPOSITION'}:
            continue
        if edge['disposition'] is not None and edge['type'] in ('HAS_DISPOSITION', 'DISPOSITION_OF'):
            if edge['neighbour'] in current_dispositions or edge['disposition'].get('evidenceStatus') != 'pending':
                raise ValueError(f'Absent source event carries a current assertion: {rid}')
            continue
        if (not edge['outgoing'] and edge['type'] == 'ANCHORS' and edge['properties'].get('channel') == 'resolution'
                and edge['properties'].get('state') == 'candidate'):
            continue
        raise ValueError(f'Absent source event has an edge outside this layer: {rid} {edge["type"]}')


def retire_absent_document_events(session, wg, nodes, disposition_ids, root=None):
    """Remove source events the current source no longer yields, after a durable preimage.

    The complete current generation must already be loaded. An absent event is
    removed together with its superseded pending assertions; regenerated
    candidate anchors leave with it. Any other attachment stops the transaction.
    """
    import decision_disposition as d
    root = root or d.ROOT
    current = {node['resolutionId'] for node in nodes}
    if not current:
        raise ValueError('Retirement requires the complete current source generation')
    current_dispositions = set(disposition_ids)
    stored = [row['id'] for row in session.run(
        "MATCH (r:Resolution {resolutionScope:'document_disposition'}) RETURN r.resolutionId AS id").data()]
    if not current <= set(stored):
        raise ValueError('Load the current source generation before retiring absent events')
    absent = sorted(set(stored) - current)
    if not absent:
        return {'retiredSourceEvents': 0}
    prior = absent_event_snapshot(session, absent)
    for row in prior:
        check_retirable_event(row, current_dispositions)
    journal_dir = axis.tree_path('logs_common', wg=wg, root=root) / 'verification' / 'decision-dispositions'
    journal_dir.mkdir(parents=True, exist_ok=True)
    journal = journal_dir / ('retired-event-preimage-' + uuid.uuid4().hex + '.json')
    recovery = {'wg': wg, 'before': prior, 'state': 'prepared'}
    durable_json(journal, recovery)
    assertions = sorted({edge['neighbour'] for row in prior for edge in row['edges'] if edge['disposition'] is not None})
    def write(tx):
        if absent_event_snapshot(tx, absent) != prior:
            raise ValueError('Absent source event preimage changed; no writes performed')
        tx.run('MATCH (x:DecisionDisposition) WHERE x.dispositionId IN $ids DETACH DELETE x', ids=assertions).consume()
        tx.run('MATCH (r:Resolution) WHERE r.resolutionId IN $ids DETACH DELETE r', ids=absent).consume()
        left = tx.run('''OPTIONAL MATCH (r:Resolution) WHERE r.resolutionId IN $ids
            WITH count(r) AS events
            OPTIONAL MATCH (x:DecisionDisposition) WHERE x.dispositionId IN $assertions
            RETURN events, count(x) AS assertions''', ids=absent, assertions=assertions).data()[0]
        after = {row['id'] for row in tx.run(
            "MATCH (r:Resolution {resolutionScope:'document_disposition'}) RETURN r.resolutionId AS id").data()}
        if left['events'] or left['assertions'] or after != current:
            raise ValueError('Source event retirement postcondition failed; transaction rolled back')
        return {'retiredSourceEvents': len(absent), 'retiredAssertions': len(assertions),
                'retiredCandidateAnchors': sum(edge['type'] == 'ANCHORS' for row in prior for edge in row['edges']),
                'preimageJournal': str(journal.relative_to(root))}
    try:
        result = session.execute_write(write)
    except Exception as error:
        durable_json(journal, dict(recovery, **transaction_failure_receipt(
            error, prior, None, lambda: absent_event_snapshot(session, absent))))
        raise
    durable_json(journal, dict(recovery, state='committed', result=result))
    return result
