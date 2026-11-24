"""RAN1·RAN2 목록 줄 처분 기록의 코드를 회의록 원문에서 따로 다시 읽어 맞대어 본다 (모델 호출 없음).

단위는 처분 기록(DecisionDisposition) 한 건이다. 다음 세 조건을 모두 만족하는 기록이 모집단이다.
- evidenceStatus 가 `source_verified` 이다.
- assessmentMethod 의 scope 가 `whole_target`(대상 문서 전체에 대한 처분)이다.
- 인용문 첫 줄이 그 WG 문서 번호(`R1-…`·`R2-…`)로 시작하는 목록 줄이다. 회의록이 문서 하나를 "번호<탭>제목<탭>제출처"
  한 줄로 적고 그 아래 줄에 처분을 적는 형식이다. 탭 대신 공백을 쓴 회의록도 있다.
부속서 표 행(`Annex …` 로 시작하는 인용), 본문 합의문(`Agreement…` 로 시작하는 인용), 그 밖의 인용 형식,
subdocument·undetermined 범위, pending 기록은 이 검사 밖이다. 건수만 `excluded` 에 적는다.

WG마다 모집단을 dispositionId 순으로 정렬하고, `random.Random(seed)` 를 WG마다 새로 만들어 --sample 건을 비복원 추출한다.
각 기록에서 네 가지를 본다.
① 근거 파일의 SHA-256 이 기록의 evidenceSha256 과 같다.
② 공백을 모두 지운 인용문이 공백을 모두 지운 원문(수락본) 안에 이어진 글로 있다. 표 행은 `| 셀 | 셀 |` 로 적는다.
   기호 글꼴 글자(w:sym, 그리고 기호 글꼴 run 의 `w:t` 에 적힌 사용자 영역 글자 U+F000~U+F0FF. 회의록의 `Broadcom 🡪 …`
   화살표 따위)는 유니코드로 옮기는 표가 글꼴마다 달라 원문 글에서 뺀다.
   그래서 이런 글자가 든 인용문은 엄격한 비교(`quoteInSource`)에서 빠지고, 원문의 기호 자리 하나가 인용문 글자 하나와
   맞는다고 본 비교(`quoteInSourceWithSymbolsWhenWholeMissing`)로 따로 센다. 이 보조 비교는 감사 표본을 처음 돌린 뒤,
   엄격한 비교에서 빠진 6 건이 모두 이 화살표 자리에서 끊긴 것을 원문 XML 에서 보고 더했다. ④ 의 줄 목록은 바뀌지 않는다.
③ 대상 문서 번호(targetTdocNumber)가 인용문 안에 있다. 번호 뒤에 숫자가 이어지면 다른 번호로 본다.
④ 원문에서 그 문서 항목을 찾아 처분 줄을 아래 규칙으로 다시 읽고, 읽은 코드가 기록의 dispositionCode 와 같은지 본다.
   문서와 대상의 짝마다 기록이 한 건이라 기록 쪽 코드 집합은 원소가 하나다.

원문은 word/document.xml 의 수락본으로 읽는다. 삭제(w:del)·이동 전(w:moveFrom) 글은 빼고 삽입·이동 후 글은 넣는다.
문단 표시가 삭제된 문단은 다음 문단에 붙인다. 표는 행마다 한 줄이다.

항목 찾기: 인용문 첫 줄(공백 정리)과 같은 표 밖 문단을 찾는다. 여럿이면 인용문 전체가 그 문단부터 이어지는 자리만 남기고,
그래도 여럿이면 locator 의 첫 블록 번호에 가장 가까운 자리를 쓰고 `anchorCandidates` 에 그 수를 적는다.
목록 줄은 표 밖 문단으로, 첫 줄이 같은 WG 번호로 시작하고 다음 셋 가운데 하나를 만족한다. 그 줄에 탭이 있다. 번호 바로 뒤에
공백(줄 바꿈 없는 공백 포함)이 둘 이상 온다. 문단 스타일이 Doc-title·Doctitle 이다. 번호 뒤에 공백 하나를 두고 글이 이어지는 줄
(`R2-2208228 is noted.`)은 처분·토론 줄이다.
항목은 목록 줄 문단 안에서 줄 바꿈 뒤에 이어진 글과, 다음 문단부터 다음 목록 줄 또는 Heading 문단 앞까지의 줄이다.
목록 줄 바로 뒤에 빈 줄만 두고 다음 목록 줄이 오면(여러 문서를 함께 다룬 묶음) 묶음 끝 목록 줄 아래 줄을 함께 읽는다.
항목 안에서 대괄호 안에 글자가 든 줄(`[Post124][002] …`, `[109-e-NR-CRs-02] …`, 이메일 토론 제목)부터 항목 끝까지는 이메일
토론 블록으로 따로 둔다. 그 위의 줄(문서 자신의 줄)을 먼저 읽고, 거기서 처분이 나오지 않을 때(`no_decision_line`·
`target_not_bound`)만 블록의 결과 줄을 읽는다. 블록 안 처분은 그 토론이 다룬 다른 문서의 것일 때가 많기 때문이다.
블록을 읽어 정한 기록은 `viaEmailBlock` 으로 센다. 숫자만 든 `[044]` 는 이메일 토론 번호 표시라 제목으로 보지 않는다.
인용문이 아니라 원문 항목 전체를 읽으므로, 어느 줄이 처분을 정하는지도 함께 검사된다.

처분 줄 읽기 규칙. 실제 회의록 글을 보고 정했고, 구축 코드는 열어 보지도 가져오지도 않았다. 글은 따옴표·대시를 한 가지로 맞추고
공백을 정리하고 소문자로 바꿔 읽는다.
1. 표 행, `-`·`•`·`–`·`·` 로 시작하는 토론 줄, `Intended outcome`·`Deadline`·`Discussion`·`Moved from`·`(Moved from`·
   `Proposal(s)`·`P<숫자>`·`Observation(s)`·`Agreement(s)`·`Note(s)`·`The document was presented` 로 시작하는 줄은 처분 줄이 아니다.
2. 줄 앞의 `Decision(s):`, `=>`·`==>`·`->`·`⇒`, `[숫자]`(이메일 토론 번호) 표시는 떼고 읽는다. 이 표시가 있는 줄은 모든 절을
   읽고, 표시가 없는 줄은 첫 절이 처분 절일 때만 처분 줄로 본다. 절 앞의 `also`·`then`·`finally`·`and`·`but`·`so`·`hence`와
   `As per (the) (email) decision (posted) (on …),` 는 뗀다.
   술어(뒤에 in·as·by 가 붙을 수 있다)와 콜론만으로 된 줄(`Not treated:`, `Agreed in:`)은 그 아래 문서들을 이끄는 표지다.
   표지 자체는 처분 줄이 아니다. 표지 바로 아래부터 문서 번호로 시작하는 줄이 이어지는 동안 각 줄 앞에 표지를 붙여 읽는다
   (`agreed in r2-2313676 (38.331)`).
   절 안에서 술어 뒤에 (in·as·by·below 다음) 콜론이 오는 절도 같은 표지라 처분 절이 아니다.
3. 문장(`.`·`;` 뒤 공백), ` and `, 앞뒤에 공백을 둔 대시(` - `)로 절을 나눈다. 괄호·대괄호 안과 약어(cat.·rel.·no.·nr.·sec.·
   ver.·vs.·etc.·fig.·approx.) 뒤의 마침표·쌍반점, `e.g.`·`i.e.` 에서는 나누지 않는다.
   절이 처분 술어로 시작하거나 `<주어> is/are/was/were/has been/have been (also/then) <술어>` 꼴일 때만 처분 절이다.
   주어 종류는 주어에서 괄호 안 글을 뺀 나머지로 정한다(괄호 안은 주어를 꾸미는 말이다). 목록 줄과 다른 문서 번호도 이 나머지에서 센다.
   - 나머지가 비었거나 문서를 가리키는 말(the document·the CR·the LS·reply LS·the TP·the summary·the report·way forward …)뿐이고
     다른 문서 번호가 없으면 문서 처분이다.
   - 그렇지 않고 주어(괄호 안 포함)에 CR 번호(`CR0231`, `CR#0177`)가 있고 다른 문서 번호가 없으면 그 문서에 실린 CR 의 처분이다.
   - 그 밖의 주어(Proposal·P1·RAN2·option·다른 문서 번호 …)는 문서 일부나 다른 문서에 대한 결론이라 문서 처분에 쓰지 않는다.
4. 술어와 코드: not treated/handled/discussed/presented/considered → not_treated, not pursued → not_pursued,
   not agreed/approved/accepted/endorsed → not_agreed, withdrawn → withdrawn, postponed/deferred → postponed,
   rejected → rejected, merged → merged, revised → revised, endorsed → endorsed, agreed/approved/accepted → agreed,
   noted → noted, replied → replied_to. `for information` → noted 는 처분 표시가 있는 줄에서만 읽는다
   (`Decision: The document is for information.`). 토론 줄(`Huawei explains that this is for information`)에도 흔히 나오기 때문이다.
   agreed/approved/accepted(agreed 계열)와 endorsed 는 뒤에 오는 말에 따라 바꾼다(위에서부터 먼저 맞는 것).
   - (agreed 계열만) `to be added/included/merged/incorporated/captured/folded/reflected/put/implemented`, 또는 목적어 없이
     전치사가 바로 오는 능동형 `to add/include/merge/incorporate/… in/into/to` → 문서 내용을 다른 CR·TP·TR 에 넣기로 한 것이라
     merged. endorsed 뒤의 `to be merged to …` 는 승인한 문서를 넘기는 말이라 endorsed 로 둔다.
   - `to <동사>`(`to be` 는 빼고)·`that` → 기술 결론이라 처분 절이 아니다. `Endorsed to be provided to RAN` 은 처분 절이다.
   - 술어 뒤 `in`·`as` 바로 다음에 목록 줄과 다른 문서 번호가 오면(`agreed in R2-…`, `agreed with these changes as R2-…`,
     `agreed in principle in R2-…`) 이 문서는 그 번호로 고쳐 냈으므로 revised. 구판과 신판의 처분을 따로 읽는다는 뜻이다.
     `in`·`as` 없이 번호가 오는 `to be merged to R2-…` 는 이 규칙에 들지 않는다.
   - (agreed 계열만) 술어 바로 뒤 `in principle` → conditionally_agreed
   - (agreed 계열만) 술어 바로 뒤 `(,) with (the/these/this/following/some/minor/editorial/small/above/below) change(s)/modification(s)/
     correction(s)/amendment(s)/update(s)/removal/addition(s)` → conditionally_agreed
   - (agreed 계열만) `except`·`apart from`·`other than`·`but not`·`excluding`, 또는 술어 뒤가 proposal·P숫자·section·clause·TP·
     part·option·observation 으로 시작 → partially_agreed
5. 한 절에 문서 처분, 다른 절에 그 문서 CR 처분이 함께 있으면(The document is noted and CR0231 … is agreed) CR 처분을 쓴다.
   대상 문서의 실질이 CR 이고 결정이 그 CR 을 처분했기 때문이다.
6. 읽을 줄 안의 문서 처분 코드가 하나면 그 코드다. 서로 다른 코드가 둘 이상이면 판정하지 않는다(`conflicting`).
   문서 처분 절이 없고 일부 결론 가운데 partially_agreed 가 있으면 partially_agreed, 아무 처분 절도 없으면 판정하지 않는다
   (`no_decision_line`).
7. 대상 번호가 목록 줄 번호와 다르면(다른 번호로 낸 수정본) 그 번호가 든 절만 읽는다. 주어 자리에 번호가 있으면 그 번호를
   목록 줄 번호로 놓고 그 절을 3·4번대로 읽는다. 아니면 같은 절에서 번호 앞 가장 가까운 술어를 읽는다.
   agreed 계열 → agreed. 다만 술어와 번호 사이에 `in principle` 이 있거나 번호 뒤에 `with … change(s)/modification(s)/
   correction(s)/amendment(s)/update(s)/removal/removed/addition(s)` 가 오면 conditionally_agreed. endorsed → endorsed.
   술어가 그 밖의 것(revised·merged …)뿐이거나 번호가 처분 줄에 없으면 그 번호의 처분은 이 항목에 없으므로 판정하지 않는다
   (`target_not_bound`). 읽은 코드가 둘 이상이면 `conflicting` 이다.

규칙을 정한 순서: 모집단에서 감사 표본(seed 20261112, WG마다 500 건)을 뺀 나머지에서 개발 표본(seed 7 은 300 건, seed 8·9 는
500 건)을 뽑아 원문과 맞대며 규칙을 고쳤고, 규칙을 고정한 뒤 감사 표본을 한 번 돌렸다. 감사 표본의 결과를 보고 규칙을 고치지 않는다.

불일치는 둘로 나눈다. `undecided` 는 다시 읽기가 코드를 정하지 못한 경우(`anchor_not_found`·`no_decision_line`·
`conflicting`·`target_not_bound`), `different` 는 다른 코드를 읽은 경우다. --judgments 파일(dispositionId → 판단)이 있으면
불일치마다 사람이 원문 항목을 읽고 적은 판단을 붙인다. 판단의 verdict 는 넷이다. `record_correct` 는 기록이 맞고 다시 읽기가
틀렸거나 정하지 못한 경우, `reread_correct` 는 다시 읽기의 코드가 맞고 기록이 틀린 경우, `record_incorrect` 는 기록이 계약이나
원문과 맞지 않지만 다시 읽기가 정하지 못했거나 맞는 코드를 계약이 하나로 정하지 않는 경우(맞는 코드 후보는 correctCode 에 적는다),
`undetermined` 는 원문과 계약만으로 어느 쪽인지 정할 수 없는 경우다. 일치한 기록은 한 건씩 읽지 않는다.
판단마다 읽을 때의 기록 코드(judgedRecordCode)를 적는다. 판단 뒤 기록이 바뀌면 그 판단은 지금의 기록을 읽은 것이 아니므로,
기록이 판단의 correctCode 로 바뀐 경우만 `corrected_to_judged_code` 로 따로 세고 그 밖의 경우는 다시 읽을 때까지 감사를 멈춘다.

표본 크기: WG마다 500 건이면 비율 추정의 95% 구간 반폭이 가장 나쁜 경우(p=0.5)에도 1.96·√(0.25/500) ≈ 4.4%p 이고,
모집단이 유한하므로 실제로는 이보다 조금 좁다(RAN1 모집단 6078 건이면 약 4.2%p). 빈도가 1% 이상인 불일치 유형은
1-0.99^500 ≈ 99.3% 확률로 표본에 한 번 이상 나오므로, 불일치를 모두 직접 읽으면 그런 유형을 놓칠 가능성이 작다.
어떤 유형이 표본에 한 번도 나오지 않으면 그 빈도의 95% 상한은 약 3/500 = 0.6% 다. 일치율 구간은 Wilson 95% 구간이다.

사용: python3 -I audit_list_line_dispositions.py --sample 500 --seed 20261112 --out <json> [--judgments <json>]
저장소 루트에서 실행한다(근거 경로가 루트 상대 경로다).
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import random
import re
import xml.etree.ElementTree as ET
import zipfile
from functools import lru_cache
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
# 기본 입력은 그래프에 적재된 설치본이다. 재구축 세대를 감사하려면 --rebuild 로 그 디렉토리를 준다.
REBUILD = Path("ontology/output/tsg/RAN/formal/instances/phase-2")
PREFIX = {"RAN1": "R1", "RAN2": "R2"}
# 글을 담지 않거나 수락본에 없는 요소. pPr 은 문단 표시 삭제 여부만 따로 본다.
SKIP = {W + name for name in ("del", "moveFrom", "pPr", "rPr", "sectPr", "tblPr", "trPr", "tcPr", "tblGrid", "instrText")}
TDOC = re.compile(r"\b(?:r[1-5]|rp|s[1-6]|c[1-6])-\d{5,7}\b")
SYMBOL = "\x00"
PRIVATE_USE_SYMBOL = re.compile("[\uf000-\uf0ff]")

NOT_DECISION = re.compile(
    r"^(?:[-•–·]|intended\s+outcome|deadline|discussion|moved\s+from|\(moved\s+from|proposals?\b|p\d|observations?\b"
    r"|agreements?\b|note\b|notes\b|the\s+document\s+was\s+presented)")
MARKER = re.compile(r"^(?:decisions?\s*:\s*|=+>\s*|->\s*|⇒\s*|\[\d+[a-z]?\]\s*)+")
LEAD = re.compile(r"^(?:(?:also|then|finally|and|but|so|hence)\s+|as\s+per\s+(?:the\s+)?(?:email\s+)?decision"
                  r"(?:\s+posted)?(?:\s+on\s+[^,]*)?,\s*)+")
PRED = (r"not\s+(?:treated|handled|discussed|presented|considered)|not\s+pursued"
        r"|not\s+(?:agreed|approved|accepted|endorsed)|withdrawn|postponed|deferred|rejected|merged|revised"
        r"|endorsed|agreed|approved|accepted|noted|for\s+information|replied")
PRED_AT_START = re.compile(rf"^({PRED})\b")
PRED_AFTER_VERB = re.compile(rf"^(.*?)\b(?:is|are|was|were|has\s+been|have\s+been)\s+(?:also\s+|then\s+)?({PRED})\b")
PRED_ANYWHERE = re.compile(rf"\b({PRED})\b")
DOC_SUBJECT = re.compile(
    r"(?:the|this|that|both|these|its)?\s*(?:(?:draft|reply|response|revised|running|big|baseline)\s+)*"
    r"(?:document|doc|paper|contribution|cr|crs|change\s+request|tp|text\s+proposal|ls|lss|ls\s+reply|liaison|pcr|draft"
    r"|summary|report|way\s+forward|wf|work\s*plan|discussion\s+paper|tdoc)s?(?:\s+itself)?")
CR_SUBJECT = re.compile(r"\bcr\s*#?\s*\d")
CODE_OF = [("not_treated", r"not\s+(?:treated|handled|discussed|presented|considered)"), ("not_pursued", r"not\s+pursued"),
           ("not_agreed", r"not\s+"), ("withdrawn", r"withdrawn"), ("postponed", r"postponed|deferred"),
           ("rejected", r"rejected"), ("merged", r"merged"), ("revised", r"revised"), ("endorsed", r"endorsed"),
           ("agreed", r"agreed|approved|accepted"), ("noted", r"noted|for\s+information"), ("replied_to", r"replied")]
# 문서 내용을 다른 CR·TP·TR 에 넣기로 한 결정. 능동형은 목적어 없이 전치사가 바로 올 때만 문서 자체를 넣는 뜻이다
# (`agreed to include in the running CR`). `agreed to add a note in …` 처럼 목적어가 있으면 기술 결론이다.
FOLD_IN = re.compile(r"^\s*to\s+(?:be\s+(?:added|included|merged|incorporated|captured|folded|reflected|put|implemented)\b"
                     r"|(?:add|include|merge|incorporate|capture|fold|reflect|put|implement)\s+(?:in|into|to)\b)")
TECHNICAL = re.compile(r"^\s*(?:to\s+(?!be\b)\w|that\b)")
# 이메일 토론 제목 줄. 대괄호 안에 글자가 있다(`[Post124][002]…`, `[109-e-NR-CRs-02] …`). 숫자만 든 `[044]` 는 처분 표시다.
EMAIL_TITLE = re.compile(r"^\s*\[[^\]]*[a-z]{2,}[^\]]*\]", re.I)
ABBREVIATION = re.compile(r"\b(?:cat|rel|no|nr|sec|ver|vs|etc|fig|approx)\.$")
# 고쳐 낸 판의 번호(`agreed in R2-…`, `approved as R2-…`, `agreed with these changes as R2-…`).
REVISION_OUTPUT = re.compile(r"\b(?:in|as)\s+((?:r[1-5]|rp|s[1-6]|c[1-6])-\d{5,7})\b")
LABEL = re.compile(rf"^((?:{PRED})(?:\s+(?:in|as|by))?)\s*:\s*$")
WITH_CHANGES = re.compile(r"^\s*(?:,\s*)?with\s+(?:(?:the|these|this|following|some|minor|editorial|small|above|below)\s+)*"
                          r"(?:changes?|modifications?|corrections?|amendments?|updates?|removal|additions?)\b")
# 대상 번호 뒤에 붙은 수정 조건(`agreed in R1-… with changes-on-changes removed`).
TARGET_CONDITION = re.compile(r"\bwith\b.*\b(?:changes?|modifications?|corrections?|amendments?|updates?|removal|removed"
                              r"|additions?)\b")
PARTIAL = re.compile(r"\b(?:except|apart\s+from|other\s+than|but\s+not|excluding)\b"
                     r"|^\s*(?:the\s+)?(?:proposals?|p\d|sections?|clauses?|tps?\b|parts?|options?|observations?)")


def squeeze(text: str) -> str:
    return " ".join(text.split())


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _text(node, out: list[str]) -> None:
    for child in node:
        if child.tag in SKIP:
            continue
        if child.tag == W + "t":
            # 기호 글꼴 run 의 글자는 `w:t` 안에 사용자 영역 글자(U+F000~U+F0FF, `Wingdings` 의 `F0E8` 따위)로도 적힌다.
            # `w:sym` 과 같은 기호 자리로 읽는다.
            out.append(PRIVATE_USE_SYMBOL.sub(SYMBOL, child.text or ""))
        elif child.tag in (W + "tab", W + "ptab"):
            out.append("\t")
        elif child.tag in (W + "br", W + "cr"):
            out.append("\n")
        elif child.tag == W + "noBreakHyphen":
            out.append("-")
        elif child.tag == W + "sym":
            # 기호 글꼴 글자(`<w:sym w:font="Wingdings" w:char="F0E0"/>`). 유니코드로 옮기는 표가 글꼴마다 달라 자리 표시만 남긴다.
            out.append(SYMBOL)
        elif child.tag == MC + "AlternateContent":
            choice = child.find(MC + "Choice")
            if choice is not None:
                _text(choice, out)
        else:
            _text(child, out)


def _paragraph(p) -> tuple[str, str, bool]:
    """(스타일 id, 글, 문단 표시 삭제 여부)."""
    props = p.find(W + "pPr")
    style, mark_deleted = "", False
    if props is not None:
        node = props.find(W + "pStyle")
        style = node.get(W + "val", "") if node is not None else ""
        run_props = props.find(W + "rPr")
        mark_deleted = run_props is not None and run_props.find(W + "del") is not None
    out: list[str] = []
    _text(p, out)
    return style, "".join(out), mark_deleted


@lru_cache(maxsize=2)
def load_docx(path: str) -> tuple[str, tuple[tuple[str, str], ...], str, str]:
    """(파일 SHA-256, 수락본 줄 목록 (스타일, 글), 공백을 지운 전체 글, 기호 자리 표시를 남긴 같은 글).
    표 행의 스타일은 `TABLEROW`. 줄 목록과 셋째 값에서는 기호 글꼴 글자를 뺀다."""
    raw = Path(path).read_bytes()
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    lines: list[tuple[str, str]] = []
    carry = ""

    def walk(node) -> None:
        nonlocal carry
        for child in node:
            if child.tag == W + "p":
                style, text, mark_deleted = _paragraph(child)
                if mark_deleted:
                    carry += text
                    continue
                lines.append((style, carry + text))
                carry = ""
            elif child.tag == W + "tbl":
                for row in child.iter(W + "tr"):
                    cells = []
                    for cell in row.findall(W + "tc"):
                        cells.append(" ".join(_paragraph(p)[1] for p in cell.iter(W + "p")))
                    lines.append(("TABLEROW", "| " + " | ".join(cells) + " |"))
            elif child.tag in (W + "sdt", W + "sdtContent", W + "customXml", W + "smartTag"):
                walk(child)

    walk(root.find(W + "body"))
    if carry:
        lines.append(("", carry))
    with_symbols = compact("\n".join(text for _, text in lines))
    plain = tuple((style, text.replace(SYMBOL, "")) for style, text in lines)
    return hashlib.sha256(raw).hexdigest(), plain, with_symbols.replace(SYMBOL, ""), with_symbols


def quote_in_source_with_symbols(quote: str, with_symbols: str) -> bool:
    """원문의 기호 자리 하나가 인용문의 글자 하나와 맞는다고 보고 인용문이 원문 안에 이어진 글로 있는지 본다."""
    if SYMBOL not in with_symbols:
        return False
    pattern = "".join(f"(?:{re.escape(ch)}|\\x00)" for ch in compact(quote))
    return re.search(pattern, with_symbols) is not None


def is_list_line(style: str, text: str, prefix: str) -> bool:
    """문서 하나를 소개하는 목록 줄. 첫 줄이 WG 번호로 시작하고, 그 줄에 탭이 있거나, 번호 바로 뒤에 공백(줄 바꿈 없는 공백 포함)이
    둘 이상 오거나, 문단 스타일이 Doc-title·Doctitle 이다. 번호 뒤에 공백 하나만 두고 글이 이어지는 줄
    (`R2-2208228 is noted.`, `R2-1815686 and R2-1815687 are agreed in principle.`)은 처분·토론 줄이다."""
    if style == "TABLEROW":
        return False
    first = text.split("\n")[0]
    found = re.match(rf"^\s*{prefix}-\d{{5,7}}\b", first)
    if found is None:
        return False
    rest = first[found.end():]
    return "\t" in rest or re.match(r"[^\S\t\n]{2,}", rest) is not None or re.fullmatch(r"(?i)doc-?title", style) is not None


def is_heading(style: str) -> bool:
    return re.match(r"(?i)^heading\s*\d", style) is not None


def norm(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("–", "-").replace("—", "-")
    return squeeze(text).lower()


def find_anchor(lines, quote: str, locator: str) -> tuple[int | None, int]:
    """목록 줄의 자리와 후보 수. 인용문 전체가 이어지는 자리를 먼저 고른다."""
    head = squeeze(quote.split("\n")[0])
    hits = [i for i, (style, text) in enumerate(lines) if style != "TABLEROW" and squeeze(text.split("\n")[0]) == head]
    if not hits:
        return None, 0
    want = compact(quote)
    full = []
    for i in hits:
        got, j = "", i
        while len(got) < len(want) and j < len(lines):
            got += compact(lines[j][1])
            j += 1
        if got.startswith(want):
            full.append(i)
    pool = full or hits
    if len(pool) == 1:
        return pool[0], len(pool)
    start = re.search(r"\[(\d+),", locator)
    target = int(start.group(1)) if start else 0
    return min(pool, key=lambda i: abs(i - target)), len(pool)


def entry_lines(lines, anchor: int, prefix: str) -> tuple[list[tuple[int, str]], list[tuple[int, str]], bool]:
    """목록 줄 아래 처분을 읽을 줄 (줄 번호, 글). 문서 자신의 줄, 그 아래 이메일 토론 블록의 줄, 묶음 여부.
    줄바꿈(w:br)으로 나뉜 글은 따로 읽는다."""
    grouped = False
    i = anchor + 1
    # 목록 줄 문단 안에서 줄바꿈 뒤에 이어진 글(`…\tdiscussion` 다음의 `late` 따위)도 항목에 넣는다.
    tail = [(anchor, piece) for piece in lines[anchor][1].split("\n")[1:]]
    while True:
        own: list[tuple[int, str]] = list(tail)
        email: list[tuple[int, str]] = []
        j = i
        while j < len(lines):
            style, text = lines[j]
            if is_list_line(style, text, prefix) or is_heading(style):
                break
            if EMAIL_TITLE.match(text) or email:
                email.extend((j, piece) for piece in (text.split("\n") if style != "TABLEROW" else [""]))
            else:
                own.extend((j, piece) for piece in (text.split("\n") if style != "TABLEROW" else [""]))
            j += 1
        if any(text.strip() for _, text in own + email) or j >= len(lines) or not is_list_line(*lines[j], prefix):
            return own, email, grouped
        grouped, i = True, j + 1
        tail = [(j, piece) for piece in lines[j][1].split("\n")[1:]]


def clauses(body: str) -> list[str]:
    """절 나누기. 괄호 안과 약어(`cat.`·`rel.` …) 뒤의 마침표·쌍반점, `e.g.`·`i.e.` 는 나누지 않는다."""
    body = re.sub(r"\be\.g\.", "eg", re.sub(r"\bi\.e\.", "ie", body))
    masked, depth = [], 0
    for i, ch in enumerate(body):
        if ch in "([":
            depth += 1
        elif ch in ")]" and depth:
            depth -= 1
        if ch in ".;" and (depth or ABBREVIATION.search(body[:i + 1])):
            masked.append("\0" if ch == "." else "\1")
        else:
            masked.append(ch)
    parts = re.split(r"(?<=[.;])\s+|\s+and\s+|\s+-\s+", "".join(masked))
    parts = [part.replace("\0", ".").replace("\1", ";").strip(" .;,") for part in parts]
    return [part for part in parts if part]


def base_code(predicate: str) -> str:
    for code, pattern in CODE_OF:
        if re.match(pattern, predicate):
            return code
    raise ValueError(predicate)


def read_clause(clause: str, header: str, marked: bool = True) -> tuple[str, str] | None:
    """(주어 종류, 코드). 주어 종류는 doc · own_cr · part. 처분 절이 아니면 None.
    `for information` 은 토론 줄에도 흔히 나오므로(`Huawei explains that this is for information`) 처분 표시가 있는 줄에서만
    처분으로 읽는다."""
    clause = LEAD.sub("", clause)
    match = PRED_AT_START.match(clause)
    subject = ""
    if match is None:
        match = PRED_AFTER_VERB.match(clause)
        if match is None:
            return None
        subject = match.group(1).strip()
        predicate, rest = match.group(2), clause[match.end():]
    else:
        predicate, rest = match.group(1), clause[match.end():]
    if not marked and re.match(r"for\s+information", predicate):
        return None
    # 괄호 안은 주어를 꾸미는 말이다(`The document (RAN4 response to RAN1 LS in R1-…) is noted`).
    bare_subject = squeeze(re.sub(r"\([^)]*\)", " ", subject)).strip(" ,:")
    others = {number for number in TDOC.findall(bare_subject)} - {header}
    if not bare_subject or DOC_SUBJECT.fullmatch(bare_subject):
        kind = "doc" if not others else "part"
    elif CR_SUBJECT.search(subject) and not others:
        kind = "own_cr"
    else:
        kind = "part"
    code = base_code(predicate)
    if re.match(r"^\s*(?:in|as|by|below)?\s*:", rest):
        # `Not Treated:`·`Agreed in:` 는 뒤따르는 문서들을 이끄는 표지다.
        return None
    if code in ("agreed", "endorsed"):
        if code == "agreed" and FOLD_IN.match(rest):
            return kind, "merged"
        if TECHNICAL.match(rest):
            return None
        if set(REVISION_OUTPUT.findall(rest)) - {header}:
            return kind, "revised"
        if code == "agreed":
            if re.match(r"^\s*in[\s-]+principle\b", rest):
                return kind, "conditionally_agreed"
            if WITH_CHANGES.match(rest):
                return kind, "conditionally_agreed"
            if PARTIAL.search(rest):
                return kind, "partially_agreed"
    return kind, code


def decision_bodies(entry: list[tuple[int, str]]) -> list[tuple[int, str, bool]]:
    """(줄 번호, 표시를 뗀 글, 표시가 있었는지).
    `Agreed in:` 처럼 콜론으로 끝나는 표지 줄 아래에 문서 번호로 시작하는 줄이 이어지면 표지와 그 줄을 이어 한 줄로 읽는다
    (`agreed in r2-2313676 (38.331)`)."""
    out = []
    label = None
    for index, text in entry:
        line = norm(text)
        if not line:
            continue
        marker = MARKER.match(line)
        body = line[marker.end():] if marker else line
        if label is not None and TDOC.match(body):
            out.append((index, f"{label} {body}", True))
            continue
        label = None
        found = LABEL.match(body)
        if found:
            label = found.group(1)
            continue
        if NOT_DECISION.match(line) or not body or NOT_DECISION.match(body):
            continue
        out.append((index, body, marker is not None))
    return out


def reread(entry: list[tuple[int, str]], header: str, target: str) -> tuple[str | None, str, list[dict]]:
    """(다시 읽은 코드, 판정 상태, 쓴 처분 줄)."""
    header, target = header.lower(), target.lower()
    used: list[dict] = []
    doc_codes: list[str] = []
    cr_codes: list[str] = []
    part_codes: list[str] = []
    target_codes: list[str] = []
    for index, body, marked in decision_bodies(entry):
        readings = []
        for position, clause in enumerate(clauses(body)):
            reading = read_clause(clause, header, marked)
            if position == 0 and reading is None and not marked:
                break
            if reading is not None:
                readings.append((clause, reading))
            if target != header and contains_number(clause, target):
                target_codes.extend(target_code(clause, target, header))
        if not readings:
            continue
        used.append({"line": index, "text": body[:300], "readings": [[kind, code] for _, (kind, code) in readings]})
        for _, (kind, code) in readings:
            {"doc": doc_codes, "own_cr": cr_codes, "part": part_codes}[kind].append(code)
    if target != header:
        found = sorted(set(target_codes))
        if len(found) == 1:
            return found[0], "decided", used
        return None, ("conflicting" if found else "target_not_bound"), used
    codes = sorted(set(cr_codes) or set(doc_codes))
    if len(codes) == 1:
        return codes[0], "decided", used
    if len(codes) > 1:
        return None, "conflicting", used
    if "partially_agreed" in part_codes:
        return "partially_agreed", "decided", used
    return None, "no_decision_line", used


def target_code(clause: str, target: str, header: str) -> list[str]:
    """대상 번호가 있는 절에서 그 번호에 묶인 코드."""
    at = clause.index(target)
    subject = PRED_AFTER_VERB.match(LEAD.sub("", clause))
    if subject is not None and target in subject.group(1):
        reading = read_clause(clause, target)
        return [reading[1]] if reading is not None else []
    before = list(PRED_ANYWHERE.finditer(clause[:at]))
    if not before:
        return []
    code = base_code(before[-1].group(1))
    between, after = clause[before[-1].end():at], clause[at + len(target):]
    if code == "agreed":
        conditional = re.search(r"\bin[\s-]+principle\b", between) or TARGET_CONDITION.search(after)
        return ["conditionally_agreed" if conditional else "agreed"]
    if code == "endorsed":
        return ["endorsed"]
    return []


def contains_number(quote: str, number: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(number)}(?!\d)", quote) is not None


def wilson(hit: int, n: int, z: float = 1.959964) -> list[float]:
    if not n:
        return [0.0, 0.0]
    p = hit / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(centre - half, 4), round(centre + half, 4)]


def load_frame(wg: str, rebuild: Path) -> tuple[list[dict], dict]:
    """모집단 기록(필요한 필드만)과 제외 건수."""
    graph = json.loads((rebuild / wg / "decision_dispositions.jsonld").read_text())["@graph"]
    head = re.compile(rf"^\s*{PREFIX[wg]}-\d{{5,7}}\b")
    excluded: collections.Counter[str] = collections.Counter()
    frame = []
    for record in graph:
        if record.get("evidenceStatus") != "source_verified":
            excluded[f"evidenceStatus={record.get('evidenceStatus')}"] += 1
            continue
        scope = json.loads(record["assessmentMethod"]).get("scope")
        first = (record.get("evidenceQuote") or "").split("\n")[0]
        if head.match(first):
            form = "list_line"
        elif first.lstrip().startswith("Annex"):
            form = "annex_table_row"
        elif first.lstrip().lower().startswith("agreement"):
            form = "body_agreement"
        else:
            form = "other"
        if form != "list_line" or scope != "whole_target":
            excluded[f"source_verified form={form} scope={scope}"] += 1
            continue
        frame.append({key: record[key] for key in ("dispositionId", "dispositionCode", "targetTdocNumber", "evidencePath",
                                                   "evidenceSha256", "evidenceLocator", "evidenceQuote")})
    frame.sort(key=lambda record: record["dispositionId"])
    return frame, {"records": len(graph), **dict(sorted(excluded.items()))}


def audit_record(record: dict, prefix: str) -> dict:
    sha, lines, source, with_symbols = load_docx(record["evidencePath"])
    quote, target = record["evidenceQuote"], record["targetTdocNumber"]
    header = re.match(rf"^\s*({prefix}-\d{{5,7}})", quote).group(1)
    result = {"dispositionId": record["dispositionId"], "header": header, "target": target,
              "recordCode": record["dispositionCode"], "shaMatch": sha == record["evidenceSha256"],
              "quoteInSource": compact(quote) in source, "targetInQuote": contains_number(quote, target)}
    if not result["quoteInSource"]:
        result["quoteInSourceWithSymbols"] = quote_in_source_with_symbols(quote, with_symbols)
        fragments = [compact(piece) for piece in re.split(r"[|\n]", quote) if len(compact(piece)) >= 4]
        result["quoteFragmentsInSource"] = all(piece in source for piece in fragments)
    anchor, candidates = find_anchor(lines, quote, record["evidenceLocator"])
    result["anchorCandidates"] = candidates
    if anchor is None:
        result.update(rereadCode=None, status="anchor_not_found", decisionLines=[])
        return result
    own, email, grouped = entry_lines(lines, anchor, prefix)
    code, status, used = reread(own, header, target)
    via_email = False
    if status in ("no_decision_line", "target_not_bound") and email:
        # 문서 자신의 줄에 처분이 없을 때만 바로 아래 이메일 토론 블록의 결과 줄을 그 문서의 처분으로 읽는다.
        email_code, email_status, email_used = reread(email, header, target)
        if email_status != "no_decision_line" and email_status != "target_not_bound":
            code, status, used, via_email = email_code, email_status, email_used, True
    result.update(rereadCode=code, status=status, decisionLines=used, grouped=grouped, anchorLine=anchor,
                  viaEmailBlock=via_email)
    return result


def judgment_state(disposition_id: str, judgment: dict, record_code: str) -> str:
    """판단이 지금의 기록 코드에 대한 것인지 가린다.

    판단은 judgedRecordCode(읽을 때의 기록 코드)를 함께 적는다. 지금 기록이 그 코드면 `current` 다. 기록이 판단 뒤에
    판단의 correctCode 로 바뀌었으면 `corrected_to_judged_code` 이고, 기록은 사람이 원문에서 읽은 코드를 갖는다.
    그 밖의 차이는 판단이 지금의 기록을 읽은 것이 아니므로 다시 읽을 때까지 감사를 멈춘다.
    """
    judged = judgment.get("judgedRecordCode")
    if judged is None:
        raise SystemExit(f"{disposition_id}: 판단에 judgedRecordCode 가 없어 지금의 기록 코드 {record_code} 에 대한 판단인지 알 수 없다")
    if judged == record_code:
        return "current"
    if judgment.get("verdict") in ("record_incorrect", "reread_correct") and judgment.get("correctCode") == record_code:
        return "corrected_to_judged_code"
    raise SystemExit(f"{disposition_id}: 판단은 기록 코드 {judged} 를 읽었는데 지금 기록은 {record_code} 이므로 원문을 다시 읽어야 한다")


def audit_wg(wg: str, rebuild: Path, sample: int, seed: int, judgments: dict) -> dict:
    frame, excluded = load_frame(wg, rebuild)
    drawn = random.Random(seed).sample(frame, min(sample, len(frame)))
    results = [audit_record(record, PREFIX[wg]) for record in sorted(drawn, key=lambda r: r["evidencePath"])]
    quotes = {record["dispositionId"]: record["evidenceQuote"] for record in drawn}
    n = len(results)
    agree = sum(r["rereadCode"] == r["recordCode"] for r in results)
    decided = [r for r in results if r["rereadCode"] is not None]
    disagreements = []
    for r in results:
        if r["rereadCode"] == r["recordCode"]:
            continue
        kind = "different" if r["rereadCode"] is not None else "undecided"
        entry = {"dispositionId": r["dispositionId"], "recordCode": r["recordCode"], "rereadCode": r["rereadCode"],
                 "class": kind, "subclass": r["status"] if kind == "undecided" else f"{r['recordCode']}->{r['rereadCode']}",
                 "header": r["header"], "target": r["target"], "quote": quotes[r["dispositionId"]],
                 "decisionLines": r["decisionLines"]}
        if r["dispositionId"] in judgments:
            judgment = judgments[r["dispositionId"]]
            entry["judgment"] = judgment
            entry["judgmentState"] = judgment_state(r["dispositionId"], judgment, r["recordCode"])
        disagreements.append(entry)
    # 사람이 읽은 판단은 불일치에만 있다. 일치한 기록은 한 건씩 읽지 않았으므로 recordSupported 는
    # "다시 읽기가 같은 코드를 읽었거나, 불일치를 읽어 보니 기록이 맞았거나, 판단 뒤 기록이 판단의 코드로 고쳐졌다"는 뜻이다.
    verdicts = collections.Counter(d["judgment"]["verdict"] for d in disagreements
                                   if d.get("judgmentState") == "current")
    corrected = [d["dispositionId"] for d in disagreements if d.get("judgmentState") == "corrected_to_judged_code"]
    supported = agree + verdicts["record_correct"] + len(corrected)
    judged = ({"verdicts": dict(verdicts), "correctedToJudgedCode": corrected,
               "unjudged": sum("judgment" not in d for d in disagreements),
               "recordSupported": supported, "recordSupportedWilson95": wilson(supported, n)} if judgments else None)
    counts = {"frame": len(frame), "sampled": n,
              "shaMatch": sum(r["shaMatch"] for r in results),
              "quoteInSource": sum(r["quoteInSource"] for r in results),
              "quoteInSourceWithSymbolsWhenWholeMissing": sum(r.get("quoteInSourceWithSymbols", False) for r in results),
              "quoteFragmentsInSourceWhenWholeMissing": sum(r.get("quoteFragmentsInSource", False) for r in results),
              "targetInQuote": sum(r["targetInQuote"] for r in results),
              "anchorFound": sum(r["status"] != "anchor_not_found" for r in results),
              "anchorAmbiguous": sum(r["anchorCandidates"] > 1 for r in results),
              "groupedEntries": sum(bool(r.get("grouped")) for r in results),
              "targetDiffersFromHeader": sum(r["target"] != r["header"] for r in results),
              "viaEmailBlock": sum(bool(r.get("viaEmailBlock")) for r in results),
              "rereadDecided": len(decided), "codeAgree": agree,
              "codeAgreeAmongDecided": sum(r["rereadCode"] == r["recordCode"] for r in decided)}
    return {"wg": wg, "excluded": excluded, "counts": counts,
            "agreement": {"rate": round(agree / n, 4) if n else None, "wilson95": wilson(agree, n)},
            "agreementAmongDecided": {"rate": round(counts["codeAgreeAmongDecided"] / len(decided), 4) if decided else None,
                                      "wilson95": wilson(counts["codeAgreeAmongDecided"], len(decided))},
            "disagreementClasses": dict(collections.Counter(f"{d['class']}:{d['subclass']}" for d in disagreements)),
            "judgment": judged,
            "recordCodes": dict(collections.Counter(r["recordCode"] for r in results)),
            "disagreements": disagreements,
            "sampledRecords": [[r["dispositionId"], r["recordCode"], r["rereadCode"], r["status"]] for r in results]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sample", type=int, required=True, help="WG별 추출 건수")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--rebuild", type=Path, default=REBUILD, help="WG별 decision_dispositions.jsonld 가 있는 디렉토리(기본: 설치본)")
    parser.add_argument("--judgments", type=Path, help="불일치마다 원문을 읽고 적은 판단 (dispositionId → 판단)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    judgments = json.loads(args.judgments.read_text()) if args.judgments else {}
    result = {"unit": "source_verified · scope=whole_target · 인용문 첫 줄이 WG 문서 번호 목록 줄인 처분 기록 한 건",
              "excludedNote": "excluded 의 기록(부속서 표 행·본문 합의문·그 밖의 인용 형식, subdocument·undetermined 범위, "
                              "pending)은 이 검사에서 코드를 다시 읽지 않았다.",
              "sampleSizeNote": "WG마다 n=500: 가장 나쁜 경우(p=0.5) 95% 반폭 1.96·√(0.25/500)≈4.4%p, 빈도 1% 이상 불일치 유형이 "
                                "한 번 이상 나올 확률 1-0.99^500≈99.3%, 한 번도 안 나온 유형의 95% 상한 ≈3/500=0.6%.",
              "judgmentNote": "judgment 는 불일치만 원문으로 읽은 결과다. recordSupported = 코드 일치 + record_correct + 판단 뒤 판단의 코드로 고쳐진 기록이며, "
                              "일치한 기록은 한 건씩 읽지 않았으므로 두 독해가 같은 방향으로 틀린 경우는 이 수에 잡히지 않는다.",
              "rebuild": str(args.rebuild), "samplePerWg": args.sample, "seed": args.seed,
              "workingGroups": [audit_wg(wg, args.rebuild, args.sample, args.seed, judgments) for wg in PREFIX]}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    for row in result["workingGroups"]:
        print(row["wg"], row["counts"], row["agreement"], row["disagreementClasses"])


if __name__ == "__main__":
    main()
