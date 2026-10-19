"""Exact original generic rule functions; no repository/file-system main."""
import re, hashlib, json, gzip
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
TDOC = re.compile(r'R1-\d{7}(?!\d)')
HEADER = re.compile(r'^\s*R1-\d{7}(?!\d)')
FINAL_INTRO = re.compile(r'^(?:The\s+)?(?:final\s+CRs?\b|draft\s+CR\b.*?\bfinal\s+CR\b)', re.I)
CAPTURE_INTRO = re.compile(r'^The agreement above is captured in:\s*$', re.I)
STATUS = re.compile(r'^\s*\(Rel[^\n]*(?:agreed|endorsed)\b', re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': sha(data)}


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def read_jsonl_gzip(path):
    with gzip.open(path, 'rt') as f:
        return [json.loads(line) for line in f]


def candidate_blocks(blocks):
    """Identify explicit capture syntax and conservatively guard its ownership.

    A TDoc paragraph is claimed only when it follows a formal capture colon in
    the same uninterrupted capture block. A preceding unclaimed TDoc paragraph
    causes later capture candidates to be held. This is conservative abstention,
    not a global definition of where all Agreement bodies end.
    """
    found, claimed = [], set()
    for i, block in enumerate(blocks):
        text = block['text'].strip()
        if block['kind'] != 'p' or not (FINAL_INTRO.match(text) or CAPTURE_INTRO.fullmatch(text)):
            continue
        # Require a positive recorded statement or a capture-list introducer.
        if not (CAPTURE_INTRO.fullmatch(text) or re.search(r'\b(?:agreed|endorsed)\b', text, re.I) or text.endswith(':')):
            continue
        indices = [i]
        if text.endswith(':'):
            for j in range(i + 1, len(blocks)):
                nxt = blocks[j]
                t = nxt['text'].strip()
                if nxt['kind'] != 'p' or not t:
                    break
                if HEADER.match(t) or STATUS.match(t):
                    indices.append(j)
                else:
                    break
        references = sorted({m.group() for j in indices for m in TDOC.finditer(blocks[j]['text'])})
        if not references:
            continue
        previous_unclaimed_headers = [j for j in range(i) if blocks[j]['kind'] == 'p' and HEADER.match(blocks[j]['text']) and j not in claimed]
        status = 'held_prior_unclaimed_TDoc_header' if previous_unclaimed_headers else 'accepted_explicit_capture_prefix'
        found.append({'intro_offset': i, 'capture_offsets': indices, 'tdoc_ids': references,
                      'status': status, 'prior_unclaimed_header_offsets': previous_unclaimed_headers})
        if status == 'accepted_explicit_capture_prefix':
            claimed.update(indices)
    return found


def controls():
    p = lambda text: {'kind': 'p', 'text': text}
    t = lambda text: {'kind': 'tbl', 'text': text}
    cases = []
    def check(name, blocks, expected):
        actual = candidate_blocks(blocks)
        value = [(c['status'], c['tdoc_ids']) for c in actual]
        cases.append({'name': name, 'actual': value, 'expected': expected, 'pass': value == expected})
    good = 'accepted_explicit_capture_prefix'
    held = 'held_prior_unclaimed_TDoc_header'
    check('generic_capture_mirror_pair', [p('Agreement'), p('Final CRs capturing the above TPs are in:'), p('R1-2000001 CR title'), p('(Rel-18, 38.000) is agreed.'), p('R1-2000002 mirror'), p('(Rel-19, 38.000) is agreed.')], [(good, ['R1-2000001', 'R1-2000002'])])
    check('blank_ends_before_unclaimed_header', [p('The agreement above is captured in:'), p('R1-2000001 own'), p(''), p('R1-2000002 later')], [(good, ['R1-2000001'])])
    check('earlier_unclaimed_header_holds_ownership', [p('Agreement'), p('R1-2000002 separately listed'), p('Final CR is agreed in:'), p('R1-2000001 title')], [(held, ['R1-2000001'])])
    check('technical_reason_sentence_is_not_intro', [p('Reason for change: the Final CR used an older parameter R1-2000001.')], [])
    check('table_text_is_not_intro', [t('Final CR is agreed in R1-2000001.')], [])
    check('unaffirmed_proposal_is_not_asserted', [p('Final CR R1-2000001 may be proposed after further study.')], [])
    check('strict_seven_digit_identity', [p('Final CR R1-20000010 is agreed.')], [])
    check('duplicate_reference_in_one_capture_is_idempotent', [p('Final CR R1-2000001 is endorsed in R1-2000001.')], [(good, ['R1-2000001'])])
    check('claimed_capture_headers_do_not_break_next_capture', [p('Final CR is in:'), p('R1-2000001 title'), p('(Rel-18, 38.000) is agreed.'), p('Final CR R1-2000002 is endorsed.')], [(good, ['R1-2000001']), (good, ['R1-2000002'])])
    assert all(x['pass'] for x in cases)
    return cases

