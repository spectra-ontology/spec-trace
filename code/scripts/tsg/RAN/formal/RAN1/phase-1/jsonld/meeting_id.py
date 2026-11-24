#!/usr/bin/env python3
"""RAN1 TDoc List 파일명에서 회의 식별자를 추출하고 정규화한다.

`02_reference_classes.py`는 Meeting의 id를, `03_tdoc_instances.py`는 Tdoc의
presentedAt 값을 생성한다. 두 생성기는 이 모듈의 같은 추출 함수를 사용한다.
적재기 `01_load_kg.py`는 다음 조건으로 두 노드를 연결한다.

    MATCH (m:Meeting {id: t._presentedAt}) MERGE (t)-[:PRESENTED_AT]->(m)

Meeting의 id와 presentedAt이 다르면 MATCH에 일치하는 노드가 없어
PRESENTED_AT 관계가 생성되지 않는다.

과거에는 두 생성기가 각각 추출 규칙을 구현했다. 파일명
`..._RAN3#127_EOM_v5.xlsx`의 EOM(End of Meeting)을 전자회의의 e로 오인하는
결함을 `03`에서만 수정했다. 당시 RAN1 입력 61파일에서는 결과 차이가 없었지만,
차이가 발생한 세 WG와 같은 중복 구현을 사용했다.

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
    """`TDoc_List_TSGR1_100_e.xlsx` → `RAN1#100-e`.

    e 그룹에는 단어 경계 `(?=[^A-Za-z0-9]|$)`를 적용하여 EOM 같은 단어의
    첫 글자를 전자회의 접미사로 해석하지 않는다. 일치하는 파일명이 없으면 None을 반환한다.
    """
    match = re.search(
        r'TSGR1_(\d+)((?:[-_]?bis)|[a-z])?(?:[-_](e))?(?=[^A-Za-z0-9]|$)',
        filename,
        re.IGNORECASE
    )
    if not match:
        return None
    meeting_num = match.group(1)
    letter_suffix = match.group(2) or ""
    if letter_suffix.lstrip('-_').lower() == 'bis':
        letter_suffix = 'bis'
    e_suffix = match.group(3) or ""
    suffix = f"{letter_suffix}-e" if e_suffix else letter_suffix
    return f"RAN1#{meeting_num}{suffix}"


def canonical_meeting_id(meeting_id: str) -> str:
    """보유형을 정본형으로 변환한다. `RAN1#100-e`는 `RAN1#100`이 된다.

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
