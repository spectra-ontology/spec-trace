#!/usr/bin/env python3
"""RAN2 TDoc List 파일명에서 회의 식별자를 추출하고 정규화한다.

`02_reference_classes.py`는 Meeting의 id를, `03_tdoc_instances.py`는 Tdoc의
presentedAt 값을 생성한다. 두 생성기는 이 모듈의 같은 추출 함수를 사용한다.
적재기 `01_load_kg.py`는 다음 조건으로 두 노드를 연결한다.

    MATCH (m:Meeting {id: t._presentedAt}) MERGE (t)-[:PRESENTED_AT]->(m)

Meeting의 id와 presentedAt이 다르면 MATCH에 일치하는 노드가 없어
PRESENTED_AT 관계가 생성되지 않는다.

과거에는 두 생성기가 각각 추출 규칙을 구현했다. 파일명
`..._RAN3#127_EOM_v5.xlsx`의 EOM(End of Meeting)을 전자회의의 e로 오인하는
결함을 `03`에서만 수정했다. 당시 RAN2 입력 60파일 중 1건(`TDoc_List_TSGR2_131bis.xlsx`)에서 결과가 달랐다.
이전 `02` 구현은 `TSGR2_` 형식을 읽지 못해 해당 Meeting을 생성하지 않았다.

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
    """`TDoc_List_Meeting_RAN2#113-bis-e.xlsx` → `RAN2#113bis-e`.

    다음 세 파일명 형식을 순서대로 검사한다.

      ① `RAN2#N[-bis]-e` — e 그룹에 구분자와 단어 경계 `(?=[^A-Za-z0-9]|$)` 를 함께
         적용한다. `EOM`(End of Meeting)·`EOPM`의 첫 글자를 전자회의
         접미사로 잘못 해석하지 않도록 한다.
      ② `TSGR2_N…` — FTP 폴더 이름을 그대로 쓴 파일들. RAN2 는 회차 뒤 낱글자 접미사가 없다.
      ③ e 없는 `RAN2[#-_]N[-bis]`.

    각 형식은 회차·bis 뒤의 낱말 경계를 확인한다. 알 수 없는 글자 접미사가 붙은
    파일명을 알려진 회의 번호의 접두사만으로 해석하지 않는다.
    """
    match = re.search(
        r'RAN2[#\-_](\d+)(?:[-_]?(bis|BIS|Bis))?(?:[-_](e))(?=[^A-Za-z0-9]|$)',
        filename,
        re.IGNORECASE
    )
    if not match:
        m_tsgr = re.search(r'TSGR2_(\d+)(?:[-_]?(bis|BIS|Bis))?(?:[-_]?(e)(?=[^A-Za-z0-9]|$))?(?=[^A-Za-z0-9]|$)',
                           filename, re.IGNORECASE)
        if m_tsgr:
            n = m_tsgr.group(1)
            b = "bis" if m_tsgr.group(2) else ""
            e = "-e" if m_tsgr.group(3) else ""
            return f"RAN2#{n}{b}{e}"


        match = re.search(
            r'RAN2[#\-_](\d+)(?:[-_]?(bis|BIS|Bis))?(?=[^A-Za-z0-9]|$)',
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
    return f"RAN2#{meeting_num}{suffix}"


def canonical_meeting_id(meeting_id: str) -> str:
    """보유형을 정본형으로 변환한다. `RAN2#111-e`는 `RAN2#111`이 된다.

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
