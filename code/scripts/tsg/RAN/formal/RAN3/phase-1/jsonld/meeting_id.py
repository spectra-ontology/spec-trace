#!/usr/bin/env python3
"""RAN3 TDoc List 파일명에서 회의 식별자를 추출하고 정규화한다.

`02_reference_classes.py`는 Meeting의 id를, `03_tdoc_instances.py`는 Tdoc의
presentedAt 값을 생성한다. 두 생성기는 이 모듈의 같은 추출 함수를 사용한다.
적재기 `01_load_kg.py`는 다음 조건으로 두 노드를 연결한다.

    MATCH (m:Meeting {id: t._presentedAt}) MERGE (t)-[:PRESENTED_AT]->(m)

Meeting의 id와 presentedAt이 다르면 MATCH에 일치하는 노드가 없어
PRESENTED_AT 관계가 생성되지 않는다.

과거에는 두 생성기가 각각 추출 규칙을 구현했다. 파일명
`..._RAN3#127_EOM_v5.xlsx`의 EOM(End of Meeting)을 전자회의의 e로 오인하는
결함을 `03`에서만 수정했다. 당시 RAN3 입력 58파일 중 9건에서 결과가 달랐다. `_EOM`을 전자회의로 읽은
7건과 `RAN3-103`처럼 # 대신 -를 사용한 2건이었다.

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

# 파일명에 회의 식별자가 없는 워크북의 예외 매핑이다.
# 일부 TDoc List는 해당 회의의 TDoc 첨부로 배포되어 파일명에 문서 번호만 있다.
# 워크북의 TDoc 집합을 회의별 문서 집합과 대조해 확인한 매핑만 등록한다.
# 아래 표는 정규식으로 회의 식별자를 추출하지 못했을 때만 사용한다.
FILENAME_MEETING_BINDINGS: dict[str, str] = {
    # #119bis-e 목록은 회의명이 포함된 워크북으로 배포되지 않았다. 이 파일의
    # TDoc 1,073개 중 1,026개가 KG의 RAN3#119bis-e 문서 집합과 정확히 일치하며,
    # KG에 있는 해당 회의의 문서는 모두 이 파일에 포함된다.
    "R3-232502_attachment_TDoc_List_v20230508.xlsx": "RAN3#119bis-e",
    # #121은 회의명이 포함된 워크북(1,144개)이 따로 있다. 이 파일은 1,145개를
    # 포함하며 차이는 `R3-234845` 한 건이다. 이 파일의 모든 TDoc이 KG에서
    # RAN3#121에 연결되어 있어, 재생성 때도 이 매핑으로 해당 한 건을 포함한다.
    "R3-235002_attachment_Tdoc_list_v27Sep.xlsx": "RAN3#121",
}


def extract_meeting_from_filename(filename: str) -> str | None:
    """`TDoc_List_Meeting_RAN3#113-bis-e.xlsx` → `RAN3#113bis-e`.

    다음 세 파일명 형식을 순서대로 검사한다.

      ① `RAN3#N[-bis]-e` — e 그룹에 구분자와 단어 경계 `(?=[^A-Za-z0-9]|$)` 를 함께
         적용한다. `EOM`(End of Meeting)·`EOPM`의 첫 글자를 전자회의
         접미사로 잘못 해석하지 않도록 한다.
      ② `TSGR3_N…` — FTP 폴더 이름을 그대로 쓴 파일들.
      ③ e 없는 `RAN3[#-_]N[-bis]`.

    세 형식 모두 일치하지 않으면 `FILENAME_MEETING_BINDINGS`를 조회한다.
    워크북 내용으로 확인한 예외 매핑이며, 정규식이 일치하면 해당 추출 결과를 우선한다.
    """
    match = re.search(
        r'RAN3[#\-_](\d+)(?:[-_]?(bis|BIS|Bis))?(?:[-_](e))(?=[^A-Za-z0-9]|$)',
        filename,
        re.IGNORECASE
    )
    if not match:
        # ①과 같은 단어 경계를 적용해 `TSGR3_127_EOM`의 E를 전자회의로 해석하지 않는다.
        # 표시 `_Electronic` 은 낱말 전체가 표시이므로 경계 앞에서 함께 받는다.
        m_tsgr = re.search(r'TSGR3_(\d+)(?:[-_]?(bis|BIS|Bis))?(?:[-_]?(e)(?:lectronic)?(?=[^A-Za-z0-9]|$))?(?=[^A-Za-z0-9]|$)',
                           filename, re.IGNORECASE)
        if m_tsgr:
            n = m_tsgr.group(1)
            b = "bis" if m_tsgr.group(2) else ""
            e = "-e" if m_tsgr.group(3) else ""
            return f"RAN3#{n}{b}{e}"

        match = re.search(
            r'RAN3[#\-_](\d+)(?:[-_]?(bis|BIS|Bis))?(?=[^A-Za-z0-9]|$)',
            filename,
            re.IGNORECASE
        )
        if not match:
            return FILENAME_MEETING_BINDINGS.get(filename)
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
    return f"RAN3#{meeting_num}{suffix}"


def canonical_meeting_id(meeting_id: str) -> str:
    """보유형을 정본형으로 변환한다. `RAN3#127-e`는 `RAN3#127`이 된다.

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
