"""부속서 CR 표의 행마다 그 문서의 실제 CR 표지를 읽어 대조한 identity review를 만든다 (모델 호출 없음).

회의록 부속서의 행은 문서번호·규격·CR 번호·개정 번호·릴리스를 적는다. 이 스크립트는 그 문서번호로 보관된
실제 문서를 열어 표지의 자기 문서번호, CR 양식 머리줄(`규격 | CR | 번호 | rev | 개정`), Release 칸, Title 칸을
읽고 행과 맞댄다. 판정은 기계 대조만으로 내리며 결과마다 근거 블록의 위치·원문·SHA-256을 함께 적는다.

판정
- same_document_source_verified: 자기 문서번호가 표지에 있고, 행이 적은 규격·CR 번호·개정·릴리스가 표지와 같고,
  제목의 단어열이 같다.
- same_document_metadata_discrepancy: 표지가 적은 값은 모두 행과 같되, 표지가 CR 번호나 개정 칸을 비워 두었거나
  (번호 배정 전 제출본) 제목의 단어열이 다르다. 두 쪽의 표기를 그대로 남긴다.
- identity_conflict: 자기 문서번호의 표지가 적은 CR 식별값이 행과 다르다. 처분을 넘기지 않는다.
표지의 개정 칸 `-`는 최초본 표기이므로 행의 0과 같은 값으로 읽는다.
- unresolved_source_document: 그 문서번호로 보관된 문서가 없다.
표지에서 CR 양식 머리줄이나 자기 문서번호를 읽지 못한 행은 기록을 만들지 않으며, 그 행의 처분은 보류로 남는다.

이미 있는 review는 그대로 두고 없는 행만 더한다.

사용: python3 build_annex_identity_reviews.py --wg RAN1 [--dry-run]
`scripts/tsg/RAN/formal/common`에서 `PYTHONPATH=../../../../common:.`로 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import decision_disposition as d
from document_decision_source import annex_cr_table_events, annex_source_evidence
from document_decision_storage import check_annex_own_cr_fields, document_evidence_locator
from common.atomic_io import write_text_atomic

CR_FORM = re.compile(r'(?<![\w.])(?:(?:TS|TR)\s*)?(\d{2,3}\.\d{3}(?:-\d+)?)>?\s*\|\s*CR\s*\|\s*([^|]*)\|\s*(?:⌘\s*)?rev\s*\|\s*([^|]*)\|'
                     r'\s*(?:⌘\s*)?Current version:', re.I)
TITLE = re.compile(r'\|\s*Title:\s*(?:⌘\s*)?\|\s*([^|\n]*)', re.I)
RELEASE = re.compile(r'Release:\s*(?:⌘\s*)?\|\s*([^|\n]*)', re.I)
COVER_BLOCKS = 40  # 표지 양식은 문서 맨 앞에 온다. 이 범위 밖의 문구는 표지로 읽지 않는다.

REASONS = {
    'same_document_source_verified':
        'Actual own-numbered CR form has the report specification/CR number, explicit revision/release, and the same '
        'normalized title word sequence; unspecified report fields remain unspecified. Machine comparison of the '
        'quoted cover blocks; no manual reading is asserted.',
    'same_document_metadata_discrepancy':
        'Actual own-numbered CR form agrees with every report field that the cover assigns. The cover leaves the '
        'fields listed in coverFieldsLeftUnassigned blank or as a placeholder, or the two literal titles differ in '
        'word sequence; both literal forms are preserved. Machine comparison of the quoted cover blocks; no manual '
        'reading is asserted.',
    'identity_conflict':
        'The actual own-numbered source cover and the exact Annex row disagree on an assigned CR identity field. '
        'Both literal identities and the source bytes are retained; the source disposition is not transferred.',
    'unresolved_source_document':
        'No retained document under this document number exists in the local corpus census, so the Annex row has no '
        'actual cover to compare with.',
}


def words(text: str) -> list[str]:
    return re.findall(r'[a-z0-9]+', text.casefold())


def cover(path: Path, target: str, root: Path):
    """표지에서 자기 문서번호·CR 양식 머리줄·Title/Release 칸이 든 블록을 찾는다. 못 찾으면 None."""
    try:
        texts, digest, _ = d.source_blocks(str(path))
    except Exception:  # 열 수 없는 파일은 표지 근거가 되지 못한다
        return None
    head = texts[:COVER_BLOCKS]
    own = next((i for i, text in enumerate(head) if target in d.tdoc_ids(text)), None)
    form = next((i for i, text in enumerate(head) if CR_FORM.search(text)), None)
    if own is None or form is None:
        return None
    blocks = {own, form}
    title = next((i for i, text in enumerate(head) if TITLE.search(text)), None)
    release = next((i for i, text in enumerate(head) if RELEASE.search(text)), None)
    blocks |= {i for i in (title, release) if i is not None}
    relative = str(path.relative_to(root))
    evidence = [{'path': relative, 'sha256': digest, 'locator': f'word/document.xml accepted body blocks [{i},{i + 1})',
                 'quote': texts[i]} for i in sorted(blocks)]
    quote = '\n'.join(item['quote'] for item in evidence)
    identities = {(m[1], m[2].strip(), m[3].strip()) for m in CR_FORM.finditer(quote)}
    if len(identities) != 1:
        return None
    spec, number, revision = identities.pop()
    released = RELEASE.search(quote)
    titled = TITLE.search(quote)
    return {'evidence': evidence,
            'actualFields': {'spec': spec, 'crNumber': number, 'crRevision': revision,
                             'release': released[1].strip() if released else None,
                             'title': titled[1].strip() if titled else None}}


UNASSIGNED_NUMBER = re.compile(r'(?:-+|x{3,4}|CRNum|Num|draftCR|DRAFT)?', re.I)


def compare(fields: dict, actual: dict, scope: str) -> tuple[list[str], list[str]]:
    """행이 적은 값과 표지 값을 맞대어 (실제로 다른 칸, 표지가 비워 둔 칸)을 돌려준다."""
    differs, blank = [], []
    if fields.get('spec') and fields['spec'] != actual['spec']:
        differs.append('spec')
    number = re.sub(r'^CR\s*(?=\d)', '', re.sub(r'^<(.*)>$', r'\1', actual['crNumber']), flags=re.I)
    if number.isdigit():
        if fields.get('crNumber') is not None and int(fields['crNumber']) != int(number):
            differs.append('crNumber')
    elif UNASSIGNED_NUMBER.fullmatch(number) is None:
        differs.append('crNumber')
    elif fields.get('crNumber') is not None or scope not in ('in_principle', 'endorsed'):
        blank.append('crNumber')
    if fields.get('crRevision') is not None:
        row, revision = int(fields['crRevision']), actual['crRevision']
        if revision.isdigit() or revision == '-':
            if row != (int(revision) if revision.isdigit() else 0):
                differs.append('crRevision')
        elif revision == '' and row == 0:
            blank.append('crRevision')
        else:
            differs.append('crRevision')
    if fields.get('release'):
        value = re.sub(r'^<Release>\s*', '', actual['release'] or '', flags=re.I)
        value = re.sub(r'\s+Use one of the following (?:releases|categories)\b.*$', '', value, flags=re.I | re.S)
        release = re.fullmatch(r'(?:Rel(?:ease)?[-\s]*|R)?(\d+)', value, re.I)
        if not release or fields['release'] != 'Rel-' + release[1]:
            differs.append('release')
    return differs, blank


def review_for(event: dict, root: Path, corpus: Path):
    target = event['subject_tdoc']
    checked = annex_source_evidence(event, root)
    field = event['document_entry']
    base = {'meetingId': event['meeting_id'], 'targetTdocNumber': target,
            'decisionEvidence': {**{key: checked[key] for key in ('path', 'sha256', 'locator', 'quote')},
                                 'decisionText': field['decisionText'], 'subjectChecked': True}}
    assert base['decisionEvidence']['locator'] == document_evidence_locator(event)
    files = sorted(path for folder in corpus.glob(f'*/Docs/{target}') for path in folder.rglob('*')
                   if path.is_file() and path.suffix.lower() == '.docx')
    if not files:
        return {**base, 'identityStatus': 'unresolved_source_document', 'reason': REASONS['unresolved_source_document'],
                'inventoryReason': REASONS['unresolved_source_document'], 'actualDocumentEvidence': [],
                'sourceAnnexFields': field['sourceFields']}
    covers = [found for found in (cover(path, target, root) for path in files) if found]
    d.source_blocks.cache_clear()
    if not covers:
        return None
    report_fields = dict(field['sourceFields'])
    scope = field['annexTable']['tableScope']
    compared = [(found, *compare(report_fields, found['actualFields'], scope)) for found in covers]
    agreeing = [item for item in compared if not item[1]]
    if not agreeing:
        found, differs, _ = compared[0]
        return {**base, 'identityStatus': 'identity_conflict', 'reason': REASONS['identity_conflict'],
                'classification': 'report_retained_assigned_identity_requires_resolution',
                'actualDocumentEvidence': found['evidence'], 'sourceAnnexFields': report_fields,
                'actualFields': found['actualFields'], 'differingFields': differs,
                'retainedSourceVariantCount': len(covers)}
    # 표지가 모든 칸을 채운 판본을 먼저 쓴다.
    found, _, blank = min(agreeing, key=lambda item: len(item[2]))
    title = found['actualFields']['title']
    same_title = title is not None and words(title) == words(report_fields['title'])
    status = 'same_document_source_verified' if same_title and not blank else 'same_document_metadata_discrepancy'
    review = {**base, 'identityStatus': status, 'reason': REASONS[status], 'actualDocumentEvidence': found['evidence'],
              'classification': {'reportFields': report_fields, 'actualFields': found['actualFields'],
                                 'titleWordSequenceEqual': same_title, 'coverFieldsLeftUnassigned': blank,
                                 'agreeingSourceVariants': len(agreeing),
                                 'conflictingSourceVariants': len(compared) - len(agreeing)}}
    check_annex_own_cr_fields(event, review)
    return review


def reviews_of(arguments):
    """회의록 하나의 부속 표 행을 모두 판정한다. 프로세스 풀의 작업 단위다."""
    path, wg, present = arguments
    root = d.ROOT
    corpus = root / f'data/corpus/tsg/RAN/formal/meetings/{wg}/derived'
    report = json.loads(Path(path).read_text())
    counts: collections.Counter = collections.Counter()
    added = []
    if 'docx_path' not in report:
        return added, counts
    events, _ = annex_cr_table_events(report, root)
    for event in events:
        key = (event['meeting_id'], event['subject_tdoc'], document_evidence_locator(event))
        if key in present:
            counts['already_reviewed'] += 1
            continue
        review = review_for(event, root, corpus)
        if review is None:
            counts['no_readable_own_cover'] += 1
            continue
        counts[review['identityStatus']] += 1
        present.add(key)
        added.append(review)
    return added, counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--wg', required=True)
    parser.add_argument('--dry-run', action='store_true', help='판정 수만 세고 파일을 쓰지 않는다')
    parser.add_argument('--workers', type=int, default=8, help='회의록을 나누어 읽는 프로세스 수')
    parser.add_argument('--out', type=Path, help='기록을 쓸 파일. 생략하면 그 WG의 검토 기록 정본 위치에 쓴다')
    args = parser.parse_args()
    root = d.ROOT
    corpus = root / f'data/corpus/tsg/RAN/formal/meetings/{args.wg}/derived'
    out = args.out or root / f'ontology/input/tsg/RAN/formal/meetings/{args.wg}/document_decision_identity_reviews.json'
    payload = json.loads(out.read_text()) if out.exists() else {'schema': 1, 'scope': '', 'reviews': []}
    present = {(r['meetingId'], r['targetTdocNumber'], r['decisionEvidence']['locator']) for r in payload['reviews']}
    counts: collections.Counter = collections.Counter()
    added = []
    reports = sorted((root / f'ontology/output/tsg/RAN/formal/parsed_reports/{args.wg}').glob('*.json'))
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for found, counted in pool.map(reviews_of, [(str(path), args.wg, present) for path in reports]):
            added += found
            counts += counted
    print(json.dumps({'wg': args.wg, 'added': len(added), **counts}, ensure_ascii=False))
    if args.dry_run or not added:
        return
    payload['reviews'] += added
    total = collections.Counter(r['identityStatus'] for r in payload['reviews'])
    if not payload['scope']:
        payload['scope'] = (f'Source-specific own-document reviews of the explicit {args.wg} Annex CR table rows: '
                            + ', '.join(f'{count} {status}' for status, count in sorted(total.items()))
                            + '. Each review binds the exact Annex row to quoted cover blocks of the actual document.')
    # 한 파일을 모두 준비한 뒤 교체해 저장 실패 시 기존 검토 기록을 보존합니다.
    write_text_atomic(out, json.dumps(payload, ensure_ascii=False, indent=1) + '\n')


if __name__ == '__main__':
    main()
