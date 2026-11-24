#!/usr/bin/env python3
"""decision_disposition.py — 대상별 회의 처분과 정본 근거를 함께 표현한다.

Spec: docs/tsg/build/standards/decision_disposition_contract.md.
Ontology: DecisionDisposition qualifies Resolution → Tdoc; REFERENCES stays a reference.
Cycle: parsed report + accepted DOCX span → target disposition → validated loader.
배경: 문서의 전역 status와 참조 관계는 특정 결정의 승인 행위를 뜻하지 않는다.
사용: build_report_dispositions(report, root); validate_dispositions(rows, root).
LLM 호출: 없음. 명시된 문장 규칙과 판정불가 상태를 함께 보존한다.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import uuid
import zipfile
from xml.etree import ElementTree as ET

import docx_text
from document_decision_source import IN_PRINCIPLE_WORD

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(ROOT / 'scripts/common'))
from common import axis
from common.atomic_io import write_json_atomic
from ontology.jsonld_context import canonical_document, reference_identifier

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
TDOC = re.compile(r'\bR([1-5])\s*[-–]?\s*(\d{6,7})\b', re.I)
CODES = {'agreed', 'withdrawn', 'rejected', 'noted', 'postponed', 'revised',
         'ambiguous', 'endorsed', 'not_pursued', 'partially_agreed',
         'conditionally_agreed', 'not_agreed', 'not_treated', 'merged',
         'not_concluded', 'replied_to'}
DISPOSITION = re.compile(
    r'(?P<withdrawn>\bwithdrawn\b)|(?P<rejected>\brejected\b)|'
    r'(?P<not_pursued>\bnot\s+(?:be\s+)?pursued\b)|'
    r'(?P<not_agreed>\b(?:(?:not|cannot|can not|can’t|can\x27t)\s+(?:be\s+|been\s+)?(?:agreed|approved|accepted|adopt(?:ed)?)|no\s+(?:common\s+)?consensus)\b)|'
    r'(?P<postponed>\b(?:postponed|deferred)\b)|'
    r'(?P<revised>\b(?:revised|revision|rev(?=\s+in\s+R[1-5]-))\b)|'
    r'(?P<noted>\b(?:noted|for\s+info(?:rmation)?(?:\s+only)?)\b)|'
    r'(?P<endorsed>\bendors(?:ed|e)\b)|'
    r'(?P<agreed>\b(?:agreed|agree|approved|accepted|adopt(?:ed)?)\b)', re.I)
# `X is agreed as a baseline and revised in Y` approves X's content as the base of its
# revision Y. Like `X is agreed in Y`, the approval names Y as its output, and the
# coordinated predicate `revised in Y` is X's own disposition. Only `and` coordinates the
# two decisions of one meeting action. `Agreed, but then revised (by MCC) in Y` reports a
# revision made after the approval, so that approval stays X's disposition.
APPROVAL_THEN_REVISION = re.compile(
    r'(?P<approval>\b(?:agreed|approved|endorsed))(?:\s+as\s+(?:a\s+|the\s+)?baseline)?\s*,?'
    r'\s+and\s+(?:is\s+|was\s+)?(?P<revised>revised)\s+(?:in|to|into)\s+(?P<output>R[1-5]-\d{6,7})\b',
    re.I)


def tdoc_ids(text):
    return [f'R{m[1]}-{m[2]}' for m in TDOC.finditer(text)]


def normalize(text):
    return ' '.join(text.split())


class AcceptedBlockTexts:
    """Read every required evidence span, without reparsing unrelated table cells."""
    def __init__(self, blocks):
        self.blocks, self.cache = blocks, {}

    def __len__(self):
        return len(self.blocks)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        if index not in self.cache:
            block = self.blocks[index]
            self.cache[index] = ('\n'.join(docx_text.table_line_rows(block, para=docx_text.final_text))
                                 if block.tag == W + 'tbl' else docx_text.final_text(block))
        return self.cache[index]


def _read_source_blocks(path_string):
    return _parse_source_blocks(path_string, Path(path_string).read_bytes())


def _parse_source_blocks(path_string, data):
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        # 바이트에서 연 묶음에는 경로가 없다. 변환본의 필드 결과를 원본 .doc에서 되찾는
        # 손질이 원본을 찾을 수 있도록 읽은 파일의 경로를 알려 준다.
        zf.filename = path_string
        root = ET.fromstring(docx_text.zip_part(zf, 'word/document.xml'))
    body = root.find(W + 'body')
    if body is None:
        raise ValueError(f'No document body: {path_string}')
    blocks = list(docx_text.iter_blocks(body))
    texts = AcceptedBlockTexts(blocks)
    return texts, hashlib.sha256(data).hexdigest(), blocks


@lru_cache(maxsize=320)
def _source_blocks(path_string, data):
    return _parse_source_blocks(path_string, data)


def source_blocks(path_string):
    """Bind accepted text and SHA to the bytes read for this invocation.

    Filesystems may retain identical stat fields for same-size rapid writes.
    Cache parsing by the actual compressed source bytes instead of metadata.
    """
    path = Path(path_string)
    return _source_blocks(str(path), path.read_bytes())


# Source verification callers deliberately bypass or clear the shared cache.
source_blocks.__wrapped__ = _read_source_blocks
source_blocks.cache_clear = _source_blocks.cache_clear
source_blocks.cache_info = _source_blocks.cache_info


def _future_or_conditional(text, start, end):
    before = text[:start].lower()
    after = text[end:].lower()
    return bool(re.search(r'\b(?:will|would|should|could|can|may|to|shall)\s+(?:be\s+)?$', before)
                or re.search(r'\bto\s+be\s+\w+(?:\s+\w+){0,3}\s+and\s*$', before)
                or re.search(r'\b(?:if|unless|once|provided\s+that|subject to)\b', before)
                or re.match(r'\s+(?:if|once|provided\s+that|pending|subject to)\b', after))


def sentence_contexts(text):
    """Keep source abbreviations inside their grammatical scope."""
    start = 0
    for boundary in re.finditer(r'(?<=[.!?])\s+(?=[A-Z])', text):
        word = re.search(r'([A-Za-z]+)\.$', text[:boundary.start()])
        if word and word[1].lower() in {'mon', 'tue', 'tues', 'wed', 'thu', 'thur', 'thurs', 'fri', 'sat', 'sun', 'fig', 'sec', 'cat', 'no', 'dr', 'mr', 'e', 'i'}:
            continue
        yield text[start:boundary.start()]
        start = boundary.end()
    yield text[start:]


def target_content_scope(prefix, target):
    """An explicit content noun governs this target, rather than a nearby status."""
    scoped_prefix = re.sub(r'^\s*(?:(?:\[\d+\]|\d+[:.]?)\s*)+', '', prefix)
    if (re.match(r'^\s*(?:(?:The|This)\s+)?(?:intent\b|offline\s+(?:agreement|consensus)\b)', scoped_prefix, re.I)
            and target in prefix):
        return True
    if (target in prefix and re.search(r'\bparameters\b[^.;\n]*\bagreed\s+in\s+R[1-5]-\d+', prefix, re.I)):
        return True
    if (target in prefix and re.search(r'\bissues\s+raised\s+in\s+R[1-5]-\d+[^.;\n]*\bagreed\s+to\s+be\s+fixed\b', prefix, re.I)):
        return True
    return bool(re.search(
        r'\b(?:TPs?(?:\s*[-#]?\s*[A-Z0-9]+)?|text\s+proposals?|proposals?|changes?|corrections?|content|intent|issues?(?:\s+raised)?|assumptions?|options?|rows?|tables?|parameters?|observations?|updates?|results?|model|template)\b'
        r'[^\n;]*\b(?:in|on|of|from|by)\s+(?:(?:the\s+)?Appendix\s+of\s+|(?:WF|CRs?)\s+)?\[?\s*'
        + re.escape(target) + r'\b', prefix, re.I))


_WITH_CHANGE = (r'with\s+(?:(?!(?:no|not|without)\b)[\w’-]+\s+){0,3}?(?:changes?|updates?|additions?|modifications?'
                r'|modified\s+text|deletions?|corrections?|clarifications?|revisions?|remov(?:al|ing)|revised\s+title)')
# Wording that qualifies an agreement as approval subject to edits or to a condition.
APPROVAL_QUALIFIER = re.compile(
    r'\b(?:' + _WITH_CHANGE + r'|with\s+TP\s+as|with\s+the\s+proposed\s+sentence\s+modified|with\s+[^.;\n]*?\bmodified\s+to'
    r'|assum(?:e|ed|ing)\s+(?:that\s+)?the\s+following|as\s+(?:revised|modified)|' + IN_PRINCIPLE_WORD + r')\b', re.I)
# The "with ... change" qualifier. When a content noun already names part of the
# target ("agree with the first change in R2-x"), this wording is the agreement's
# scope, and the content-scope rule classifies it as partial adoption.
WITH_CHANGE_QUALIFIER = re.compile(_WITH_CHANGE + r'\b', re.I)


def target_document_subject(prefix):
    prefix = re.sub(r'^\s*(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday)\s*:\s*)', '', prefix, flags=re.I)
    return bool(re.match(r'^\s*(?:(?:Agreement|Conclusion)\s*:\s*)?(?:(?:The|A|One|Two)\s+)?'
                         r'(?:(?:Rel-?\d+|R\d+|draft|mirror|final|shadow|moderator|corresponding|updated|following)\s+)*'
                         r'(?:CRs?(?:[_#]?\d+\w*)?\b|draft[_ ]?CR(?:_\d+)?\b|LS\b|Reply\s+LS\b|TR\s*(?:skeleton\b|\d{2,3}\.)|spreadsheet\b|document\b)', prefix, re.I))


def strip_parentheticals(text):
    while True:
        cleaned = re.sub(r'\([^()]*\)', '', text)
        if cleaned == text:
            return cleaned
        text = cleaned


def classify_statement(text, target, *, subject=False, meeting_id=None):
    """Bind explicit target predicates, revision endpoints and their modality.

    No inference uses an Agreement label, global Tdoc status, nearby status
    word, or an unscoped historical statement as a document approval.
    """
    text = re.sub(r'\bin(?=R[1-5]-\d)', 'in ', text, flags=re.I)
    text = re.sub(r'(R[1-5]-\d{6,7})(?=on\b|for\b|is\b|are\b)', r'\1 ', text, flags=re.I)
    text = TDOC.sub(lambda m: f'R{m[1]}-{m[2]}', text)
    occurrences = [m for m in TDOC.finditer(text) if m.group(0).upper() == target.upper()]
    contexts = []
    if subject and not occurrences:
        contexts = [(text, False)]
    else:
        for occurrence in occurrences:
            left = max(text.rfind('\n', 0, occurrence.start()), text.rfind(';', 0, occurrence.start())) + 1
            right = min((i for mark in ('\n', ';') if (i := text.find(mark, occurrence.end())) >= 0), default=len(text))
            candidate = text[left:right]
            contexts.extend((c, False) for c in sentence_contexts(candidate))
            if re.match(r'^\s*(?:\|\s*)?' + re.escape(target) + r'\b', candidate, re.I):
                next_head = re.search(r'(?m)^\s*(?:\|\s*)?R[1-5]\s*[-–]\s*\d{6,7}\b', text[right:])
                end = right + next_head.start() if next_head else len(text)
                contexts.append((text[left:end], True))
    conclusions = []
    for context, entry in dict.fromkeys(contexts):
        if re.search(r'\([^)]*\b(?:was|previously|formerly|rev(?:ision)?\s+of)\b[^)]*' + re.escape(target), context, re.I):
            continue
        if re.search(r'\bfinal\s+CR\s+for\s+(?:the\s+)?draft\s+CR\s+in\s+' + re.escape(target) + r'\b', context, re.I):
            continue
        targets = list(TDOC.finditer(context))
        here = [m for m in targets if m.group(0).upper() == target.upper()]
        statuses = list(DISPOSITION.finditer(context))
        # The target must be the grammatical subject of the coordinated predicates
        # (`R2-x was agreed ... and revised in R2-y`); another document's approval and
        # revision say nothing about the target.
        revision_roles = {}
        for clause in APPROVAL_THEN_REVISION.finditer(context):
            if clause['output'].upper() != target.upper() and any(
                    re.fullmatch(r'\s+(?:is|are|was|were)\s+', context[hit.end():clause.start()], re.I)
                    for hit in here):
                revision_roles[clause.start('approval')] = 'output_approval'
                revision_roles[clause.start('revised')] = 'subject_revision'
        for status in statuses:
            code = status.lastgroup
            before, after = context[:status.start()], context[status.end():]
            if meeting_id:
                predicate_tail = next(sentence_contexts(after.split('\n', 1)[0]))
                named_meetings = re.findall(r'\bRAN\s*([1-5])\s*#\s*(\d+(?:bis|b)?(?:-?e)?)\b', predicate_tail, re.I)
                if named_meetings and any(f'RAN{wg}#{number}'.lower() != meeting_id.lower() for wg, number in named_meetings):
                    # A different meeting's explicitly dated disposition is
                    # evidence of history, not a new approval event here.
                    continue
            if '?' in context or _future_or_conditional(context, status.start(), status.end()):
                continue
            if re.search(r'\b(?:already|previously|formerly)\b', before, re.I):
                continue
            role = revision_roles.get(status.start())
            if role == 'output_approval':
                continue
            if role == 'subject_revision':
                conclusions.append(('revised', context, 'explicit_target_coordinated_revision_output'))
                continue
            if code == 'agreed':
                if ('?' in context or _future_or_conditional(context, status.start(), status.end())
                        or re.search(r'\b(?:not|never)\s+(?:been\s+)?$', before, re.I)
                        or re.search(r'\b(?:already|previously|formerly)\b', before, re.I)):
                    continue
                content_scoped = target_content_scope(context, target)
                if any(not (content_scoped and WITH_CHANGE_QUALIFIER.fullmatch(qualifier.group(0)))
                       for qualifier in APPROVAL_QUALIFIER.finditer(context)):
                    code = 'conditionally_agreed'
                if re.search(r'\badding\s+(?:further|additional)\s+(?:issues?|changes?)\b', context, re.I):
                    code = 'conditionally_agreed'
                if re.search(r'\b(?:TP\s*#?\s*\d+|proposals?\s*\d+|(?:first|second|third|\d+(?:st|nd|rd|th))\s+proposal|proposal\s+in\s+the\s+paragraph|sections?\s*\d+|annex\s+[a-z]|slides?\s*#?\d+|rows?\s*\d+|tables?\s*\d+|part(?:s)?\s+of|except|terminolog\w*|template|the\s+following\s+changes|agreed\s+modifications|baseline\s+assumption|plan\s+for|change\s+of\s+(?:the\s+)?baseline)\b', context, re.I):
                    code = 'partially_agreed'
                if re.search(r'\b(?:changes?|TPs?\d*|text\s+proposals?|proposals?\s+in\s+(?:the\s+)?(?:paragraph|\d)|correction\s*\d+|H\d+|P\d+)\b[^\n.;]*\b(?:in|of|from|by)\s+(?:CR\s+)?\[?\s*R[1-5]-\d', context[:status.start()], re.I):
                    code = 'partially_agreed'
                if status.group(0).lower().startswith('adopt') and not re.match(r'\s+(?:the\s+)?(?:CR|document|tdoc)\b', after, re.I):
                    code = 'partially_agreed'
            if subject and not targets:
                if code == 'agreed' and re.search(r'\b(?:proposals?|list|test\s+cases?)\b', before, re.I) and not re.search(r'\b(?:CRs?|documents?|contributions?)\b', before, re.I):
                    code = 'partially_agreed'
                if code == 'agreed' and not re.search(r'\b(?:proposals?|CRs?|document|contribution|list)\b', before, re.I):
                    # A technical change agreed in the subject's discussion is
                    # qualified as partial content adoption, not whole-CR approval.
                    if re.search(r'\bit\s+was\s*$', before, re.I):
                        code = 'partially_agreed'
                    elif before.strip(' :\n\t').lower() not in ('conclusion', ''):
                        continue
                if code == 'agreed' and re.search(r'\b(?:CT\d|SA\d|RAN[1-4])\b', before):
                    continue
                conclusions.append((code, context, 'explicit_conclusion_for_checked_subject'))
                continue
            attached = False
            for hit in here:
                if hit.end() <= status.start():
                    if re.search(r'\b(?:responses?|repl(?:y|ies))\b[^.;\n]*\bLS\b[^.;\n]*$', context[:hit.start()], re.I):
                        # A reply to an incoming LS is a different entity. The
                        # cited incoming document does not inherit the reply's
                        # disposition, even when its number is parenthesized.
                        continue
                    revision_output = re.match(r'\s+in\s+(R[1-5]-\d{6,7})\b', after, re.I)
                    if revision_output and revision_output[1].upper() != target.upper() and code != 'revised':
                        continue
                    bridge = context[hit.end():status.start()]
                    # Revision aliases are annotations, never approval targets.
                    bridge = strip_parentheticals(bridge)
                    bridge = TDOC.sub('', bridge)
                    if code == 'partially_agreed':
                        bridge = re.sub(r'\b(?:Annex\s+[A-Z]|Section\s+[0-9.]+|Proposal\s*\d+)\b', '', bridge, flags=re.I)
                    bridge = re.sub(r'\b(?:Rel-?\d+|TS\s*\d{2,3}\.\d+|NR|LTE|CRs?|draft|shadow|in)\b', '', bridge, flags=re.I)
                    if re.fullmatch(r'[\s,|&:/(){}\[\]\-]*(?:(?:and|is|are|was|were|which|has|have|been|now|also|respectively)\b[\s,|&:/(){}\[\]\-]*)*', bridge, re.I):
                        attached = True
                    # A CR entry may put its metadata and predicate on the next
                    # line. This exact field shape is the RAN1 final-CR grammar.
                    raw_bridge = context[hit.end():status.start()]
                    scoped_subject = target_content_scope(context[:hit.end()], target)
                    document_subject = target_document_subject(context[:hit.start()])
                    if ((scoped_subject or document_subject) and not TDOC.search(raw_bridge)
                            and re.search(r'\b(?:is|are|was|were)\s*$', raw_bridge, re.I)):
                        attached = True
                        if scoped_subject and code == 'agreed':
                            code = 'partially_agreed'
                    if (re.search(r'\bTP\s*#?\s*\d+[^\n]*\b(?:in|of)\s+(?:(?:the\s+)?Appendix\s+of\s+)?' + re.escape(target), context[:hit.end()], re.I)
                            and not TDOC.search(raw_bridge)
                            and re.search(r'\b(?:is|are|was|were)\s*$', raw_bridge, re.I)):
                        attached = True
                    if (re.match(r'^\s*(?:The\s+)?tdoc\s+' + re.escape(target) + r'\s*:', context, re.I)
                            and not TDOC.search(raw_bridge)
                            and re.search(r'\s+(?:is|was)\s*$', raw_bridge, re.I)):
                        attached = True
                    if entry and '\n' in raw_bridge and re.search(r'\n\s*\([^\n)]*(?:Rel-?\d|CR\d|Cat\s)[^\n)]*\)\s*(?:is|are|was|were)?\s*$', raw_bridge, re.I):
                        if not TDOC.search(raw_bridge):
                            attached = True
                elif status.end() <= hit.start():
                    bridge = context[status.end():hit.start()]
                    later_statuses = list(DISPOSITION.finditer(context[hit.end():]))
                    if code == 'revised' and re.fullmatch(r'\s*(?:in|to|into|as)\s+(?:the\s+)?', bridge, re.I):
                        # 'X is revised in Y' names Y as the output of the
                        # revision. The revised document is the subject X;
                        # Y takes its own disposition from its own predicate.
                        continue
                    if (code == 'revised' and TDOC.search(before)
                            and any(s.lastgroup in {'agreed', 'endorsed'} for s in later_statuses)):
                        # 'old Rev in new Agreed' revises the old document and
                        # approves the new one; the output's later predicate
                        # is its disposition rather than a conflicting event.
                        continue
                    # Explicit content-adoption imperatives bind the named
                    # proposal source, not an incidental parenthetical or a
                    # later source in 'on top of changes in ...'.
                    earlier = list(TDOC.finditer(bridge))
                    nominal = bridge[:earlier[0].start()] if earlier else bridge
                    content_noun = re.search(r'\b(?:TP[\w#.-]*|text\s+proposals?|proposals?|changes?(?:-\d+)?|corrections?|parameters?|structure|approach|method|Alt\d+|tables?|observations?|updates?|results?|model|template)\b', nominal, re.I)
                    coordinated = not earlier or bool(re.fullmatch(r'[\s,/&\[\]()\-]*(?:and\s*)?', bridge[earlier[-1].end():], re.I))
                    imperative = status.group(0).lower() in {'adopt', 'agree', 'endorse'}
                    imperative = imperative or (code == 'not_agreed' and status.group(0).lower() == 'not adopt'
                                                and before.strip().lower() in {'do', ''})
                    past_imperative = (status.group(0).lower() == 'endorsed'
                                       and bool(re.fullmatch(r'[\s\d:|\[\].-]*', before)))
                    if ((imperative or past_imperative)
                            and content_noun and coordinated
                            and not re.search(r'\b(?:if|unless|will|would|should|can|could|may|supersedes?|response|reply)\b', nominal, re.I)
                            and (re.search(r'\b(?:in|of|from|CR)\s*\[?\s*$', nominal, re.I)
                                 or nominal.rstrip().endswith('('))):
                        attached = True
                        if code in {'agreed', 'partially_agreed'}:
                            code = 'partially_agreed'
                    # 'Option 1 is agreed and R3-x can be endorsed' has two
                    # different grammatical subjects. A status preceding a
                    # target binds only a document-list/imperative predicate.
                    prefix = before.strip(' \t\n-:[]|')
                    prefix = re.sub(r'^(?:Monday|Tuesday|Wednesday|Thursday|Friday)\s*:\s*', '', prefix, flags=re.I)
                    prefix = re.sub(r'^(?:(?:\[?\d+\]?|\d+[a-z]?|(?:DISC\s+)?S\d+_\d+)\s*[:\]]?\s*)+', '', prefix, flags=re.I)
                    simple_prefix = strip_parentheticals(prefix)
                    simple_prefix = re.split(r'\band\b', simple_prefix, flags=re.I)[-1].strip()
                    document_prefix = re.fullmatch(r'(?:(?:Agreement|Conclusion)\s*[:\]]?\s*)?(?:(?:(?:The|This)\s+)?(?:(?:final|shadow|draft|corresponding)\s+)?(?:CRs?|documents?|contributions?|LS)\s*(?:(?:for|to)\s+(?:TS\s*)?\d{2,3}\.\d+\s*)?(?:(?:is|are|was|were)\s*)?)?', simple_prefix, re.I)
                    if (target_document_subject(prefix) and not TDOC.search(prefix)
                            and not re.search(r'\b(?:will|would|should|can|could|may|to\s+be|previously|already|formerly|not)\b', prefix, re.I)):
                        document_prefix = True
                    if re.fullmatch(r'(?:The\s+)?final\s+CR\s+for\s+(?:the\s+)?draft\s+CR\s+in\s+R[1-5]-\d+\s+is', prefix, re.I):
                        document_prefix = True
                    if status.group(0).lower() in {'agree', 'endorse', 'adopt'}:
                        document_prefix = True
                    if code == 'revised':
                        document_prefix = True
                    if re.search(r'R[1-5]-\d+\s+(?:is|was|are|were)\s*$', prefix, re.I):
                        document_prefix = True
                    if (not document_prefix and re.search(r'\b(?:TPs?|text\s+proposals?|corrections?)\b', simple_prefix, re.I)
                            and re.search(r'\b(?:is|are|was|were)\s*$', simple_prefix, re.I)):
                        document_prefix = True
                        if code == 'agreed':
                            code = 'partially_agreed'
                    if not document_prefix and not TDOC.search(bridge):
                        continue
                    if re.search(r'\b(?:with\s+(?:revisions?|changes?)\s+as\s+needed)\b', context, re.I) and code == 'agreed':
                        code = 'conditionally_agreed'
                    bridge = strip_parentheticals(bridge)
                    bridge = re.sub(r'\bfor\s+TS\s*\d{2,3}\.\d+\b', '', bridge, flags=re.I)
                    if document_prefix:
                        bridge = re.sub(r'\b(?:as\s+)?v\d+(?:\.\d+)+\b|\bCR\s*#?\d+(?:r\d+|rev\d+)?\b|\b(?:TS|TR)\s*\d{2,3}\.\d+\b|\b(?:to|for)\s+\d{2,3}\.\d+\b', '', bridge, flags=re.I)
                    if code == 'partially_agreed':
                        bridge = re.sub(r'\bTP\s*#?\s*\d+\b', '', bridge, flags=re.I)
                    bridge = TDOC.sub('', bridge)
                    allowed = r'[\s,|&:/()\[\]\-]*(?:(?:and|in|the|CRs?|final|draft|shadow|as)\b[\s,|&:/()\[\]\-]*)*'
                    if status.group(0).lower() in ('agree', 'endorse'):
                        allowed = r'[\s,|&:/()\[\]\-]*(?:(?:and|in|the|CRs?|to|final|draft|shadow|as)\b[\s,|&:/()\[\]\-]*)*'
                    if re.fullmatch(allowed, bridge, re.I):
                        attached = True
            if attached:
                if code == 'agreed' and (target_content_scope(context, target)
                        or re.search(r'\bagreed\s+to\s+be\s+(?:included|merged|captured|incorporated)\s+(?:in|to)\s+(?:a\s+)?(?:(?:RRC|MAC)\s+)?rapporteur\s+CR\b', context, re.I)):
                    code = 'partially_agreed'
                conclusions.append((code, context, 'explicit_target_predicate'))
    if not conclusions:
        return 'ambiguous', '', 'no_explicit_target_disposition'
    if len({v[0] for v in conclusions}) != 1:
        return 'ambiguous', '\n'.join(dict.fromkeys(v[1] for v in conclusions)), 'multiple_dispositions_require_adjudication'
    return conclusions[0]


def decision_source(report, decision, root=ROOT):
    path = (root / report['docx_path']).resolve()
    path.relative_to(root.resolve())
    texts, digest, blocks = source_blocks(str(path))
    span = decision.get('body_blocks')
    if not (isinstance(span, list) and len(span) == 2 and 0 <= span[0] < span[1] <= len(texts)):
        raise ValueError(f'{decision["decision_id"]}: a valid source body_blocks span is required')
    start, end = span
    source = '\n'.join(texts[start:end])
    if 'document_entry' in decision:
        field = decision['document_entry']
        if field.get('sourceKind') == 'annex_cr_table_row':
            from document_decision_source import annex_source_evidence
            return annex_source_evidence(decision, root)
        if field['headerBlock'] != start or field['decisionBlock'] + 1 != end or texts[field['headerBlock']] != field['headerText'] or texts[field['decisionBlock']] != field['decisionText']:
            raise ValueError('Document disposition does not match its accepted entry source')
        return {'path': str(path.relative_to(root.resolve())), 'sha256': digest,
                'locator': f'word/document.xml accepted body blocks [{start},{end})',
                'quote': source, 'decisionText': field['decisionText'], 'subjectChecked': True}
    subject = decision.get('subject_tdoc')
    subject_checked = False
    if subject:
        # Same structural boundary as the RAN5 parser, independently checked
        # against accepted source paragraphs instead of trusting ABOUT_TDOC.
        for index in range(start - 1, -1, -1):
            block = blocks[index]
            if block.tag != W + 'p':
                continue
            style = block.find(f'{W}pPr/{W}pStyle')
            name = style.get(W + 'val', '').lower() if style is not None else ''
            if name.startswith(('heading', 'toc')) or re.match(r'^\s*Decision\s*:', texts[index], re.I):
                break
            ids = tdoc_ids(texts[index])
            if re.match(r'^\s*R5\s*[-–]', texts[index]) and ids:
                subject_checked = ids[0] == subject
                if subject_checked:
                    start = index
                break
    return {'path': str(path.relative_to(root.resolve())), 'sha256': digest,
            'locator': f'word/document.xml accepted body blocks [{start},{end})',
            'quote': '\n'.join(texts[start:end]), 'decisionText': source,
            'subjectChecked': subject_checked}


def decisions_for_report(report, root=ROOT):
    from document_decision_source import document_decisions
    return [decision for group in ('agreements', 'conclusions', 'working_assumptions')
            for decision in report.get(group, [])] + document_decisions(report, root)[0]


def assess_decision(report, decision, source, target, root=ROOT):
    from document_decision_source import classify_document_decision
    subject = decision.get('subject_tdoc') == target and source['subjectChecked']
    code, context, method = (classify_document_decision(decision, target) if 'document_entry' in decision else
                            classify_statement(source['decisionText'], target, subject=subject, meeting_id=report['meeting_id']))
    scope = ('undetermined' if code == 'ambiguous' else
             'subdocument' if code == 'partially_agreed' or target_content_scope(context, target) else 'whole_target')
    identity = f'{report["meeting_id"].split("#")[0]}:{decision["decision_id"]}:{target}'
    assessment = {'rule': method, 'scope': scope, 'decisionBodyBlocks': decision['body_blocks'], 'subject': target if subject else None}
    if 'document_entry' in decision:
        assessment['documentEntry'] = decision['document_entry']
        from document_decision_storage import assess_document_identity
        code, assessment = assess_document_identity(decision, target, code, assessment, root)
    code, assessment = assess_identity(identity, code, assessment, source, root)
    return identity, code, assessment


def build_report_dispositions(report, root=ROOT, include_document=True):
    rows = []
    decisions = decisions_for_report(report, root) if include_document else [decision
        for group in ('agreements', 'conclusions', 'working_assumptions') for decision in report.get(group, [])]
    for decision in decisions:
            targets = list(dict.fromkeys(decision.get('referenced_tdocs', []) +
                           ([decision['subject_tdoc']] if decision.get('subject_tdoc') else [])))
            if not targets:
                continue
            source = decision_source(report, decision, root)
            for target in targets:
                identity, code, assessment = assess_decision(report, decision, source, target, root)
                resolved_target = target
                if 'document_entry' in decision:
                    from document_decision_storage import resolve_document_target
                    resolved_target = resolve_document_target(decision, target, root)[0]
                rows.append({'@id': 'tdoc:decision-disposition/' + hashlib.sha256(identity.encode()).hexdigest(),
                             '@type': 'DecisionDisposition', 'dispositionId': identity,
                             'dispositionOf': 'tdoc:resolution/' + decision['decision_id'],
                             'dispositionTarget': 'tdoc:' + resolved_target, 'dispositionCode': code,
                             'targetTdocNumber': target,
                             'evidenceStatus': 'source_verified' if code != 'ambiguous' else 'pending',
                             'evidencePath': source['path'], 'evidenceSha256': source['sha256'],
                             'evidenceLocator': source['locator'], 'evidenceQuote': source['quote'],
                             'assessmentMethod': json.dumps(assessment, sort_keys=True)})
    return rows


@lru_cache(maxsize=16)
def _review_index(root_string, receipts):
    """Validate explicit identity-review receipts, independently of live status."""
    root = Path(root_string)
    reviews = {}
    for relative, digest in receipts:
        path = root / relative
        payload = json.loads(path.read_text())
        for review in payload['reviews']:
            source = review['targetIdentityEvidence']
            source_path = (root / source['path']).resolve()
            source_path.relative_to(root.resolve())
            if hashlib.sha256(source_path.read_bytes()).hexdigest() != source['sha256']:
                raise ValueError('Identity-review target source changed; re-review required')
            import openpyxl
            workbook = openpyxl.load_workbook(source_path, read_only=True, data_only=True)
            try:
                sheet = workbook[source['sheet']]
                headers = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))
                values = next(sheet.iter_rows(min_row=source['row'], max_row=source['row'], values_only=True))
                actual = {str(key): str(value) if value is not None else '' for key, value in zip(headers, values)}
                if any(actual.get(key) != value for key, value in source['fields'].items()):
                    raise ValueError('Identity-review target row differs from its receipt')
            finally:
                workbook.close()
            identity = review['dispositionId']
            if identity in reviews:
                raise ValueError('Duplicate disposition identity review')
            reviews[identity] = dict(review, receiptPath=relative, receiptSha256=digest)
    return reviews


def assess_identity(identity, code, assessment, source, root=ROOT):
    """A literal source ID cannot overcome a source-grounded identity conflict."""
    paths = sorted((root / 'ontology/input/tsg/RAN/formal/meetings').glob('RAN*/decision_disposition_identity_reviews.json'))
    receipts = tuple((str(path.relative_to(root)), hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths)
    review = _review_index(str(root), receipts).get(identity)
    if review is None:
        return code, assessment
    expected = review['decisionEvidence']
    if any(source[key] != expected[key] for key in ('path', 'sha256', 'locator')):
        raise ValueError('Identity-review decision source changed; re-review required')
    return 'ambiguous', dict(assessment, rule='source_target_identity_conflict', scope='undetermined',
                             sourceDispositionCode=code, identityStatus='identity_conflict',
                             identityReview=review)


def validate_dispositions(rows, root=ROOT):
    """Re-evaluate source locators and target rules before any DB transaction."""
    # A prior producer call must not cache away a changed identity source.
    _review_index.cache_clear()
    identities = set()
    checked_sources = set()
    indexes = {}
    document_wgs = {row['dispositionId'].split(':', 1)[0] for row in rows
                    if row['dispositionId'].split(':', 2)[1].startswith('DOC-')}
    for row in rows:
        if row.get('dispositionId') in identities:
            raise ValueError('Duplicate disposition identity')
        identities.add(row.get('dispositionId'))
        expected_iri = 'tdoc:decision-disposition/' + hashlib.sha256(row['dispositionId'].encode()).hexdigest()
        if row.get('@type') != 'DecisionDisposition' or row.get('@id') != expected_iri:
            raise ValueError('Disposition RDF type or stable identity disagrees with its source key')
        if row.get('dispositionCode') not in CODES:
            raise ValueError('Unknown dispositionCode')
        expected_status = 'pending' if row['dispositionCode'] == 'ambiguous' else 'source_verified'
        if row.get('evidenceStatus') != expected_status:
            raise ValueError('Disposition evidence status disagrees with its assessment')
        path = (root / row['evidencePath']).resolve(); path.relative_to(root.resolve())
        texts, digest, _ = source_blocks(str(path))
        if digest != row['evidenceSha256']:
            raise ValueError('Disposition evidence source SHA changed')
        match = re.fullmatch(r'word/document.xml accepted body blocks \[(\d+),(\d+)\)', row['evidenceLocator'])
        annex = re.fullmatch(r'word/document.xml accepted table block (\d+) row (\d+); governing body blocks \[(\d+),(\d+)\)', row['evidenceLocator'])
        if not match and not annex:
            raise ValueError('Disposition source locator is required')
        start, end = map(int, match.groups() if match else annex.groups()[2:])
        # A table assertion cites its own row plus governing paragraphs. Its
        # evidence is re-read with annex_source_evidence below; copying every
        # other table row into the target's source quote would conflate claims.
        if match and '\n'.join(texts[start:end]) != row['evidenceQuote']:
            raise ValueError('Disposition evidence quote / source span mismatch')
        if not row['evidenceQuote'].strip():
            raise ValueError('Disposition evidence quote is empty')
        if path not in checked_sources:
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError('Disposition source changed during this process')
            checked_sources.add(path)
        method = json.loads(row['assessmentMethod'])
        ds, de = method['decisionBodyBlocks']
        if not (start <= ds < de <= end):
            raise ValueError('Decision span is outside its evidence')
        resolved_target = reference_identifier(row['dispositionTarget']).removeprefix('tdoc:')
        wg, rid, declared_target = row['dispositionId'].split(':', 2)
        target = declared_target
        if row.get('targetTdocNumber') != target:
            raise ValueError('Disposition target identity mismatch')
        if reference_identifier(row['dispositionOf']).removeprefix('resolution/') != rid:
            raise ValueError('Disposition Resolution identity mismatch')
        if wg not in indexes:
            indexes[wg] = {d['decision_id']: (report, d)
                           for report in reports_for_wg(wg, root)
                           for d in (decisions_for_report(report, root) if wg in document_wgs else
                               [item for group in ('agreements', 'conclusions', 'working_assumptions') for item in report.get(group, [])])}
        report, decision = indexes[wg][rid]
        expected_target = target
        if 'document_entry' in decision:
            from document_decision_storage import resolve_document_target
            expected_target = resolve_document_target(decision, target, root)[0]
        if resolved_target != expected_target:
            raise ValueError('Disposition canonical target differs from its entry-specific source alias')
        expected_source = decision_source(report, decision, root)
        if (decision['body_blocks'] != [ds, de] or
                expected_source['path'] != row['evidencePath'] or
                expected_source['locator'] != row['evidenceLocator'] or
                expected_source['quote'] != row['evidenceQuote']):
            raise ValueError('Disposition evidence is not this Resolution source span')
        expected_targets = decision.get('referenced_tdocs', []) + ([decision['subject_tdoc']] if decision.get('subject_tdoc') else [])
        if target not in expected_targets:
            raise ValueError('Disposition target is not attributed to this decision')
        checked_subject = decision.get('subject_tdoc') == target and expected_source['subjectChecked']
        if bool(method.get('subject')) != bool(checked_subject):
            raise ValueError('Disposition subject attribution mismatch')
        _, code, expected_assessment = assess_decision(report, decision, expected_source, target, root)
        if row['dispositionCode'] != code or method != expected_assessment:
            raise ValueError('Disposition disagrees with source-bound local rules')
        if row['evidenceStatus'] == 'source_verified' and row['dispositionCode'] == 'ambiguous':
            raise ValueError('Ambiguous disposition cannot be promoted')
    return rows


def reports_for_wg(wg, root=ROOT):
    directory = root / f'ontology/output/tsg/RAN/formal/parsed_reports/{wg}'
    return [report for path in sorted(directory.glob('*.json'))
            if not path.name.startswith('_')
            if (report := json.loads(path.read_text())).get('meeting_id')]


def generate_for_wg(wg, output_dir, root=ROOT):
    """Shared full/incremental producer: the artifact is a function of all reports."""
    return write_dispositions(reports_for_wg(wg, root), output_dir, root)


def prepare_for_wg(wg, root=ROOT):
    """Preflight before a loader opens a writable driver; never reuse stale claims."""
    rows = [row for report in reports_for_wg(wg, root)
            for row in build_report_dispositions(report, root)]
    return validate_dispositions(rows, root)


def pending_assessment(row, root=ROOT):
    """Separate absent predicates from unresolved grammar without claiming either true.

    Categories describe observable source syntax. In particular an unresolved
    target context is never counted as proof that the source lacks a disposition.
    """
    method = json.loads(row['assessmentMethod'])
    start, end = method['decisionBodyBlocks']
    locator = re.fullmatch(r'word/document.xml accepted body blocks \[(\d+),(\d+)\)', row['evidenceLocator'])
    if ((locator and list(map(int, locator.groups())) == [start, end])
            or ' accepted table block ' in row['evidenceLocator']):
        text = row['evidenceQuote']
    else:
        texts, _, _ = source_blocks(str((root / row['evidencePath']).resolve()))
        text = '\n'.join(texts[start:end])
    normalized = TDOC.sub(lambda m: f'R{m[1]}-{m[2]}', text)
    target = row['targetTdocNumber']
    contexts = [c for part in re.split(r'\n|;', normalized)
                for c in sentence_contexts(part) if target in c]
    predicates = [c for c in contexts if DISPOSITION.search(c)]
    if method['rule'] == 'annex_target_identity_requires_own_source_review':
        category = 'annex_target_own_source_not_yet_reviewed'
    elif method['rule'] == 'annex_in_principle_requires_final_source':
        category = 'explicit_in_principle_without_final_document_approval'
    elif method['rule'] == 'source_target_identity_review_pending':
        category = ('source_document_or_report_revision_not_recovered'
                    if method.get('identityStatus') == 'unresolved_source_document'
                    else 'source_target_identity_conflict')
    elif method['rule'] == 'source_target_identity_conflict':
        category = 'source_target_identity_conflict'
    elif method['rule'] == 'multiple_dispositions_require_adjudication':
        category = 'multiple_explicit_dispositions_require_scope_adjudication'
    elif not DISPOSITION.search(text):
        category = 'no_supported_disposition_predicate_in_decision_span'
    elif not predicates:
        category = 'disposition_predicate_only_outside_target_context'
    elif all('?' in c or all(_future_or_conditional(c, m.start(), m.end())
                            for m in DISPOSITION.finditer(c)) for c in predicates):
        category = 'question_future_or_conditional_target_context'
    elif all(re.search(r'\b(?:already|previously|formerly|previous\s+meeting|rev(?:ision)?\s+of)\b|\([^)]*\bwas\b', c, re.I)
             for c in predicates):
        category = 'historical_disposition_or_revision_alias_context'
    elif all(re.search(r'\b(?:according\s+to|in\s+response\s+to|reply\s+LS|received\s+LS|reference\s+to)\b', c, re.I)
             for c in predicates):
        category = 'reference_or_incoming_ls_context'
    else:
        category = 'unresolved_explicit_looking_target_context'
    return {'dispositionId': row['dispositionId'], 'category': category,
            'rule': method['rule'], 'source': row['evidencePath'],
            'locator': row['evidenceLocator'], 'sha256': row['evidenceSha256'],
            'targetContextsWithPredicates': predicates}


def coverage_for_wg(wg, rows, root=ROOT):
    reports = reports_for_wg(wg, root)
    from document_decision_source import document_decisions
    source_census = [document_decisions(report, root)[1] for report in reports]
    pending = [pending_assessment(row, root) for row in rows if row['evidenceStatus'] == 'pending']
    return {'wg': wg, 'reports': len(reports),
            'decisions': sum(len(report.get(group, [])) for report in reports
                             for group in ('agreements', 'conclusions', 'working_assumptions')),
            'restoredDocumentDecisions': sum(item.get('sourceDecisionEvents', 0) for item in source_census),
            'documentSourceCensus': source_census,
            'decisionsWithTargets': len({row['dispositionOf'] for row in rows}),
            'targetPairs': len(rows),
            'codes': dict(Counter(row['dispositionCode'] for row in rows)),
            'evidenceStatuses': dict(Counter(row['evidenceStatus'] for row in rows)),
            'scopes': dict(Counter(json.loads(row['assessmentMethod'])['scope'] for row in rows)),
            'pendingCategories': dict(Counter(row['category'] for row in pending)),
            'pending': pending,
            'sourceVerificationMeaning': 'Accepted source span, current SHA and local target/scope rule match; not expert adjudication.',
            'pendingCategoryMeaning': 'Source syntax categories; unresolved explicit-looking contexts remain pending, rather than evidence of no disposition.'}


def neo4j_rows(rows):
    result = []
    for row in rows:
        properties = {k: v for k, v in row.items() if not k.startswith('@')
                      and k not in ('dispositionOf', 'dispositionTarget')}
        result.append({'properties': properties,
                       'resolutionId': reference_identifier(row['dispositionOf']).removeprefix('resolution/'),
                       'tdocNumber': reference_identifier(row['dispositionTarget'])})
    return result


def resolution_snapshot(tx, resolution_ids):
    """Read a stable preimage of the untouched decision/reference layer."""
    rows = tx.run('''
        MATCH (r:Resolution) WHERE r.resolutionId IN $ids
        OPTIONAL MATCH (r)-[e:REFERENCES|ABOUT_TDOC]->(t:Tdoc)
        RETURN r.resolutionId AS resolutionId, properties(r) AS properties,
               collect({type:type(e), target:t.tdocNumber}) AS references
        ORDER BY resolutionId
    ''', ids=resolution_ids).data()
    for row in rows:
        row['references'] = sorted(row['references'], key=lambda e: (e['type'] or '', e['target'] or ''))
    return rows


def disposition_snapshot(tx, wg):
    rows = tx.run('''
        MATCH (d:DecisionDisposition) WHERE d.dispositionId STARTS WITH $prefix
        OPTIONAL MATCH (d)-[e]-(n)
        RETURN elementId(d) AS elementId, properties(d) AS properties,
               collect({type:type(e), outgoing:startNode(e)=d,
                        properties:properties(e), endpoint:elementId(n),
                        endpointProperties:properties(n), endpointLabels:labels(n)}) AS edges
        ORDER BY elementId
    ''', prefix=wg + ':').data()
    for row in rows:
        row['edges'] = sorted(row['edges'], key=lambda edge: json.dumps(edge, sort_keys=True))
    return rows


def prepare_disposition_indexes(session):
    """Prepare schema before a caller opens its data generation transaction."""
    session.run('CREATE INDEX decision_disposition_identity IF NOT EXISTS FOR (d:DecisionDisposition) ON (d.dispositionId)').consume()
    session.run('CALL db.awaitIndexes(300)').consume()


def record_disposition_commit_failure(result, error):
    """Retain an unknown caller outcome until full committed readback succeeds."""
    if not result.get('outerTransactionPending'):
        return
    from document_decision_storage import durable_json
    result = {key: value for key, value in result.items() if key != 'outerTransactionPending'}
    journal = ROOT / result['preimageJournal']
    outcome_path = journal.with_suffix('.result.json')
    outcome = json.loads(outcome_path.read_text())
    if outcome.get('result') != result:
        raise ValueError('Disposition caller failure receipt differs')
    durable_json(outcome_path, dict(outcome, state='commit_outcome_unknown', error=str(error)))
    source_events = result['documentSourceEvents']
    if source_events.get('preimageJournal'):
        event_journal = ROOT / source_events['preimageJournal']
        event_receipt = json.loads(event_journal.read_text())
        durable_json(event_journal, dict(event_receipt, state='commit_outcome_unknown', error=str(error)))


def finalize_disposition_transaction(session, result):
    """Verify a committed caller transaction before publishing its receipts."""
    if not result.get('outerTransactionPending'):
        return result
    from document_decision_storage import (durable_json, source_event_snapshot,
        check_fingerprints)
    result = {key: value for key, value in result.items() if key != 'outerTransactionPending'}
    journal = ROOT / result['preimageJournal']
    prepared = json.loads(journal.read_text())
    outcome = json.loads(journal.with_suffix('.result.json').read_text())
    if (outcome.get('state') not in {'awaiting_outer_commit', 'commit_outcome_unknown', 'committed'}
            or outcome.get('result') != result):
        raise ValueError('Disposition caller transaction receipt differs')
    resolution_ids = sorted({row['resolutionId'] for row in prepared['resolutionPreimage']})
    if (disposition_snapshot(session, prepared['wg']) != outcome['postimage'] or
            resolution_snapshot(session, resolution_ids) != prepared['resolutionPreimage']):
        raise ValueError('Disposition caller transaction committed readback differs')
    check_fingerprints(prepared['sourceFingerprints'], ROOT)
    source_events = result['documentSourceEvents']
    event_journal = None
    if source_events.get('preimageJournal'):
        event_journal = ROOT / source_events['preimageJournal']
        event_receipt = json.loads(event_journal.read_text())
        ids = [row['properties']['resolutionId'] for row in event_receipt['incoming']]
        actual = source_event_snapshot(session, ids)
        actual_sha = hashlib.sha256(json.dumps(actual, sort_keys=True).encode()).hexdigest()
        if (event_receipt.get('state') not in {'awaiting_outer_commit', 'commit_outcome_unknown', 'committed'}
                or event_receipt.get('result') != source_events
                or actual_sha != source_events['postimageSha256']):
            raise ValueError('Source event caller transaction committed readback differs')
        check_fingerprints(event_receipt['sourceFiles'], ROOT)
    if event_journal is not None:
        durable_json(event_journal, dict(event_receipt, state='committed', qualificationStatus='complete'))
    durable_json(journal.with_suffix('.result.json'), {'state': 'committed', 'result': result,
        'postimage': outcome['postimage']})
    return result


def load_dispositions(session, rows, *, transaction=None):
    """Match existing targets, retain every source assertion including absent targets.

    The source target spelling remains in the assertion properties; an absent
    Phase-1 Tdoc is measured, never created as a placeholder. All rows are
    written and checked in a single transaction. A supplied transaction belongs
    to the caller: schema is prepared first, and its receipts are finalized only
    after the caller commits the complete generation.
    """
    payload = neo4j_rows(rows)
    if not payload:
        return {'assertions': 0, 'missingTargets': 0}
    wg_names = {r['properties']['dispositionId'].split(':', 1)[0] for r in payload}
    if len(wg_names) != 1:
        raise ValueError('A disposition transaction belongs to exactly one WG')
    wg = next(iter(wg_names))
    from document_decision_storage import (document_resolution_nodes, load_document_resolutions,
        durable_json, source_fingerprints, check_fingerprints, transaction_failure_receipt)
    fingerprints = source_fingerprints(wg, ROOT)
    check_fingerprints(fingerprints, ROOT)
    validate_dispositions(rows)
    if transaction is None:
        prepare_disposition_indexes(session)
    reader = transaction if transaction is not None else session
    # Save the assertion preimage before disposition writes. The caller may
    # already have a transaction open for the complete data generation. Only
    # this assertion layer is owned here; Resolution and reference data stay.
    resolution_ids = sorted({r['resolutionId'] for r in payload})
    # The same maintained path is used by ordinary Phase-2 loaders and explicit
    # reconciliation; supplemental events survive a parser/loader rerun.
    source_events = load_document_resolutions(session, document_resolution_nodes(reports_for_wg(wg)),
        **({'transaction': transaction} if transaction is not None else {}))
    # Read endpoint labels and properties after the source stage updates them.
    # With a caller-owned transaction, these reads see the same pending data
    # generation as the disposition writes.
    prior = disposition_snapshot(reader, wg)
    source_preimage = resolution_snapshot(reader, resolution_ids)
    journal_dir = axis.tree_path('logs_common', wg=wg, root=ROOT) / 'verification' / 'decision-dispositions'
    journal_dir.mkdir(parents=True, exist_ok=True)
    journal = journal_dir / ('preimage-' + uuid.uuid4().hex + '.json')
    durable_json(journal, {'wg': wg, 'before': prior,
        'incomingIds': [r['properties']['dispositionId'] for r in payload],
        'incomingProperties': [r['properties'] for r in payload],
        'resolutionPreimage': source_preimage,
        'sourceFingerprints': fingerprints,
        'resolutionAndReferenceMutation': False})
    completed_postimage = None
    def write(tx):
        nonlocal completed_postimage
        completed_postimage = None
        current = disposition_snapshot(tx, wg)
        if current != prior or resolution_snapshot(tx, resolution_ids) != source_preimage:
            raise ValueError('Disposition preimage changed; no write performed')
        tx.run('''MATCH(d:DecisionDisposition)-[e:DISPOSITION_OF|DISPOSITION_TARGET]->()
                  WHERE d.dispositionId IN $ids DELETE e''',
               ids=[row['properties']['dispositionId'] for row in payload]).consume()
        tx.run('''MATCH(:Resolution)-[e:HAS_DISPOSITION]->(d:DecisionDisposition)
                  WHERE d.dispositionId IN $ids DELETE e''',
               ids=[row['properties']['dispositionId'] for row in payload]).consume()
        result = {'assertions': 0, 'missingTargets': 0}
        for offset in range(0, len(payload), 1000):
            batch_result = tx.run('''
            UNWIND $rows AS row
            MATCH (res:Resolution {resolutionId: row.resolutionId})
            MERGE (d:DecisionDisposition {dispositionId: row.properties.dispositionId})
            SET d = row.properties
            MERGE (res)-[:HAS_DISPOSITION]->(d)
            MERGE (d)-[:DISPOSITION_OF]->(res)
            WITH d, row
            OPTIONAL MATCH (t:Tdoc {tdocNumber: row.tdocNumber})
            FOREACH (_ IN CASE WHEN t IS NULL THEN [] ELSE [1] END |
              MERGE (d)-[:DISPOSITION_TARGET]->(t))
            RETURN count(DISTINCT d) AS assertions,
                   sum(CASE WHEN t IS NULL THEN 1 ELSE 0 END) AS missingTargets
        ''', rows=payload[offset:offset + 1000]).single()
            for key in result:
                result[key] += batch_result[key]
        if result['assertions'] != len(payload):
            raise ValueError(f'Disposition loading lost Resolution endpoints: {dict(result)} / {len(payload)}')
        # Preserve superseded evidence and remove it from current verified
        # consumption, rather than deleting the source assertion.
        tx.run('''
            MATCH (d:DecisionDisposition)
            WHERE d.dispositionId STARTS WITH $prefix
              AND NOT d.dispositionId IN $ids
            SET d.evidenceStatus = 'pending'
        ''', prefix=wg + ':', ids=[r['properties']['dispositionId'] for r in payload]).consume()
        verified = tx.run('''
            MATCH (d:DecisionDisposition)
            WHERE d.dispositionId IN $ids
            RETURN count(d) AS count
        ''', ids=[r['properties']['dispositionId'] for r in payload]).single()['count']
        if verified != len(payload):
            raise ValueError('Disposition postcondition failed; transaction rolled back')
        readback = tx.run('''MATCH(d:DecisionDisposition) WHERE d.dispositionId IN $ids
            OPTIONAL MATCH(d)-[e:DISPOSITION_OF|DISPOSITION_TARGET]->(n)
            WITH d,collect({type:type(e), resolutionId:n.resolutionId, target:n.tdocNumber}) AS edges
            OPTIONAL MATCH(r:Resolution)-[:HAS_DISPOSITION]->(d)
            RETURN properties(d) AS properties,edges,collect(r.resolutionId) AS inverse''',
            ids=[row['properties']['dispositionId'] for row in payload]).data()
        saved = {row['properties']['dispositionId']: row for row in readback}
        present_targets = {row['number'] for row in tx.run('''MATCH(t:Tdoc) WHERE t.tdocNumber IN $numbers
            RETURN t.tdocNumber AS number''', numbers=sorted({row['tdocNumber'] for row in payload})).data()}
        for row in payload:
            actual = saved[row['properties']['dispositionId']]
            expected = row['properties']
            edges = [(edge['type'], edge['resolutionId'], edge['target']) for edge in actual['edges'] if edge['type']]
            wanted = [('DISPOSITION_OF', row['resolutionId'], None)]
            if row['tdocNumber'] in present_targets:
                wanted.append(('DISPOSITION_TARGET', None, row['tdocNumber']))
            if (actual['properties'] != expected or sorted(edges) != sorted(wanted)
                    or actual['inverse'] != [row['resolutionId']]):
                raise ValueError('Disposition complete property/edge readback failed; transaction rolled back')
        if resolution_snapshot(tx, resolution_ids) != source_preimage:
            raise ValueError('Resolution/reference postcondition failed; transaction rolled back')
        check_fingerprints(fingerprints, ROOT)
        result = {**dict(result), 'preimageJournal': str(journal.relative_to(ROOT)), 'documentSourceEvents': source_events}
        completed_postimage = {'snapshot': disposition_snapshot(tx, wg), 'result': result}
        return result
    if transaction is not None:
        try:
            result = write(transaction)
            durable_json(journal.with_suffix('.result.json'), {'state': 'awaiting_outer_commit',
                'result': result, 'postimage': completed_postimage['snapshot']})
        except Exception as error:
            durable_json(journal.with_suffix('.result.json'), {'state': 'commit_outcome_unknown',
                'stage': 'caller_write_failed', 'error': str(error), 'sourceEventStage': source_events})
            raise
        return dict(result, outerTransactionPending=True)
    try:
        result = session.execute_write(write)
    except Exception as error:
        failure = transaction_failure_receipt(error, prior, completed_postimage,
            lambda: disposition_snapshot(session, wg), rollback_state='dispositions_rolled_back')
        durable_json(journal.with_suffix('.result.json'), {**failure, 'sourceEventStage': source_events,
            'recovery': 'Source events were committed before this stage. Recheck current source and disposition states before replaying the validated reconciliation.'})
        raise
    if source_events.get('preimageJournal'):
        event_journal = ROOT / source_events['preimageJournal']
        event_receipt = json.loads(event_journal.read_text())
        durable_json(event_journal, dict(event_receipt, qualificationStatus='complete'))
    durable_json(journal.with_suffix('.result.json'), {'state': 'committed', 'result': result})
    return result


def write_dispositions(reports, output_dir, root=ROOT, prepared_rows=None):
    rows = prepared_rows if prepared_rows is not None else [row for report in reports for row in build_report_dispositions(report, root)]
    validate_dispositions(rows, root)
    document = canonical_document({'@context': {'@vocab': 'https://w3id.org/spectra#',
        'tdoc': 'https://w3id.org/spectra#',
        'dispositionOf': {'@id': 'tdoc:dispositionOf', '@type': '@id'},
        'dispositionTarget': {'@id': 'tdoc:dispositionTarget', '@type': '@id'}}, '@graph': rows})
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / 'decision_dispositions.jsonld'
    write_json_atomic(path, document)
    from document_decision_storage import document_resolution_nodes
    events = document_resolution_nodes(reports, root)
    event_path = output_dir / 'resolutions_document_dispositions.jsonld'
    event_document = canonical_document({'@context': {'@vocab': 'https://w3id.org/spectra#',
        'tdoc': 'https://w3id.org/spectra#'}, '@graph': events})
    write_json_atomic(event_path, event_document)
    return {'path': str(path), 'count': len(rows), 'documentSourcePath': str(event_path),
            'documentSourceEvents': len(events), 'codes': dict(Counter(r['dispositionCode'] for r in rows))}
