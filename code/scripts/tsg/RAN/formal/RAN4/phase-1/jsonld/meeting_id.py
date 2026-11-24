#!/usr/bin/env python3
"""RAN4 TDoc List 파일명에서 회의 식별자를 추출하고 정규화한다.

`02_reference_classes.py`는 Meeting의 id를, `03_tdoc_instances.py`는 Tdoc의
presentedAt 값을 생성한다. 두 생성기는 이 모듈의 같은 추출 함수를 사용한다.
적재기 `01_load_kg.py`는 다음 조건으로 두 노드를 연결한다.

    MATCH (m:Meeting {id: t._presentedAt}) MERGE (t)-[:PRESENTED_AT]->(m)

Meeting의 id와 presentedAt이 다르면 MATCH에 일치하는 노드가 없어
PRESENTED_AT 관계가 생성되지 않는다.

과거에는 두 생성기가 각각 추출 규칙을 구현했다. 파일명
`..._RAN3#127_EOM_v5.xlsx`의 EOM(End of Meeting)을 전자회의의 e로 오인하는
결함을 `03`에서만 수정했다. 당시 RAN4 입력 62파일 중 4건에서 결과가 달랐다. `_EOM`/`_EOPM` 3건과
`TSGR4_` 형식 1건이었다.

규칙은 `docs/tsg/build/standards/meeting_id_normalization.md` §3에 정의한다.
`scripts/common/data-integrity/check_meeting_extractor_parity.py`는 두 생성기의 결과를 대조한다.

`extract_meeting_from_filename`은 개최 형식을 남긴 보유형을 반환하며
`Meeting.meetingNumber`에 사용한다. `canonical_meeting_id`는 전자회의 표시를
제거한 정본형을 반환하며 `Meeting.canonicalMeetingNumber`에 사용한다.
Phase-10의 `core/config_loader.normalize_meeting_id`는 폴더명 입력에 같은
정규화 규칙(문서 §3.2)을 적용한다.
"""
from __future__ import annotations

import re

def extract_meeting_from_filename(filename: str) -> str | None:
    """`TDoc_List_Meeting_RAN4#113-bis-e.xlsx` → `RAN4#113bis-e`.

    다음 세 파일명 형식을 순서대로 검사한다.

      ① `RAN4#N[-bis]-e` — e 그룹에 구분자와 단어 경계 `(?=[^A-Za-z0-9]|$)` 를 함께
         적용한다. `EOM`(End of Meeting)·`EOPM`의 첫 글자를 전자회의
         접미사로 잘못 해석하지 않도록 한다.
      ② `TSGR4_N…` — FTP 폴더 이름을 그대로 쓴 파일들.
      ③ e 없는 `RAN4[#-_]N[-bis]`.
    """
    # 전자회의 표시가 bis보다 앞에 있는 형식을 먼저 검사한다. 이 분기가 없으면
    # `RAN4#94-e-Bis`(실제 입력)는 ①에서 `RAN4#94-e`로, `RAN4#94_eBis`
    # (설계서 §6.1 표의 형식)는 ③에서 `RAN4#94`로 추출되어 bis가 누락된다.
    e_bis = re.search(r'RAN4[#\-_](\d+)[-_]e[-_]?bis(?=[^A-Za-z0-9]|$)',
                      filename, re.IGNORECASE)
    if e_bis:
        return f"RAN4#{e_bis.group(1)}bis-e"

    match = re.search(
        r'RAN4[#\-_](\d+)(?:[-_]?(bis|BIS|Bis))?(?:[-_](e))(?=[^A-Za-z0-9]|$)',
        filename,
        re.IGNORECASE
    )
    if not match:
        # 회차 뒤의 단일 글자 접미사는 받지 않는다. 해당 그룹을 추가하면
        # `TSGR4_104bis-e`의 b만 접미사로 추출하여 `RAN4#104b`가 된다.
        # 확인한 RAN4 FTP 폴더 59개에는 단일 글자 접미사가 없었고, [a-z]로
        # 읽힐 수 있는 글자는 모두 bis의 첫 글자였다(단일 글자는 RAN1에서 사용한다).
        # `TSGR4_104bis-e`와 `TSGR4_94_eBis`를 모두 처리하도록 bis와 e의
        # 존재 여부를 각각 검사한다. 순서를 고정하면 후자에서 bis가 누락된다.
        m_tsgr = re.search(r'TSGR4_(\d+)((?:[-_]?(?:bis|e))*)(?=[^A-Za-z0-9]|$)',
                           filename, re.IGNORECASE)
        if m_tsgr:
            n = m_tsgr.group(1)
            tokens = set(re.findall(r'bis|e', (m_tsgr.group(2) or "").lower()))
            b = "bis" if "bis" in tokens else ""
            e = "-e" if "e" in tokens else ""
            return f"RAN4#{n}{b}{e}"


        match = re.search(
            r'RAN4[#\-_](\d+)(?:[-_]?(bis|BIS|Bis))?',
            filename,
            re.IGNORECASE
        )
        if not match:
            return None
        meeting_num = match.group(1)
        bis_suffix = match.group(2)
        e_suffix = None
    else:
        meeting_num = match.group(1)
        bis_suffix = match.group(2)
        e_suffix = match.group(3)

    suffix = "bis" if bis_suffix else ""
    if e_suffix:
        suffix += "-e"
    return f"RAN4#{meeting_num}{suffix}"


def canonical_meeting_id(meeting_id: str) -> str:
    """보유형을 정본형으로 변환한다. `RAN4#101-e`는 `RAN4#101`이 된다.

    끝의 전자회의 표시(e 또는 electronic)를 제거하고, 회의를 구분하는 bis는
    구분자 없이 소문자로 정규화한다. 기준은
    `docs/tsg/build/standards/meeting_id_normalization.md` §3.2이다.

    과거의 `meeting_id[:-2] if endswith('-e')`만으로는 -bis가 정규화되지 않아
    `RAN3#127-bis`와 `RAN3#127bis`가 별도 이름으로 저장되었다.
    현재는 추출기와 같은 모듈에서 정규화 규칙을 관리한다.

    검사기 `check_meeting_consistency.py`의 canonical_meeting_id와 결과가 같아야 한다.
    검사 A는 저장된 정본 필드를 다시 계산한 값과 비교하여 불일치를 보고한다.
    """
    s = re.sub(r"[-_](?:e|electronic)$", "", meeting_id.strip(), flags=re.IGNORECASE)
    s = re.sub(r"[-_]?bis", "bis", s, flags=re.IGNORECASE)
    return re.sub(r"[-_](?:e|electronic)$", "", s, flags=re.IGNORECASE)
