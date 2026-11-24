#!/usr/bin/env python3
"""RAN5 TDoc List 파일명에서 회의 식별자를 추출하고 정규화한다.

Phase-1의 참조 생성기와 TDoc 생성기가 이 모듈을 함께 사용한다. 적재기는
TDoc의 presentedAt 값과 Meeting의 id가 일치하는 노드에 PRESENTED_AT을 연결하므로
두 생성기가 같은 회의 식별자를 사용해야 한다.

extract_meeting_from_filename은 개최 형식을 남긴 보유형을 반환하며
Meeting.meetingNumber에 사용한다. canonical_meeting_id는 전자회의 표시를 제거한
정본형을 반환하며 Meeting.canonicalMeetingNumber에 사용한다. Phase-10의
core/config_loader.normalize_meeting_id는 폴더명 입력에 같은 정규화 규칙을 적용한다.

규칙은 docs/tsg/build/standards/meeting_id_normalization.md §3에 정의되어 있다.
scripts/common/data-integrity/check_meeting_extractor_parity.py는 두 생성기의 추출 결과를 대조한다.
"""
from __future__ import annotations

import re

# 회차가 없는 3GU 형식 TDoc List는 파일명에 포함된 내보내기 날짜로 회의를 선택한다.
_3GU_DATE_TO_MEETING = {
    "2025-09-05": "RAN5#108",
    "2026-02-23": "RAN5#110",
}


def extract_meeting_from_filename(filename: str) -> str | None:
    """`TDoc_List_Meeting_RAN5#86-e.xlsx` → `RAN5#86-e`. RAN5 에 bis 회의는 없다.

    다음 세 파일명 형식을 순서대로 검사한다.

      ① `RAN5#N[-e]` 와 마스터 로컬본의 `R5#N` — e 그룹에는 단어 경계
         `(?=[^A-Za-z0-9]|$)` 를 건다.
      ② `TSGR5_N…` — FTP 폴더 이름을 그대로 쓴 파일들. 폴더명은 회차 뒤에 개최지를
         달고(`TSGR5_76_Berlin`) 밑줄이 겹치기도 한다(`TSGR5__107_Malta`).
      ③ 회차가 없는 3GU 형식 — 등록된 내보내기 날짜와 일치하는 회의를 반환한다.
    """
    match = re.search(
        r'(?:RAN5|R5)#(\d+)(?:[-_](e))?(?=[^A-Za-z0-9]|$)',
        filename,
        re.IGNORECASE
    )
    if match:
        meeting_num = match.group(1)
        suffix = "-e" if match.group(2) else ""
        return f"RAN5#{meeting_num}{suffix}"

    m_tsgr = re.search(r'TSGR5_+(\d+)(?:[-_](e))?(?=[^A-Za-z0-9]|$)',
                       filename, re.IGNORECASE)
    if m_tsgr:
        return f"RAN5#{m_tsgr.group(1)}{'-e' if m_tsgr.group(2) else ''}"

    for date_str, meeting_id in _3GU_DATE_TO_MEETING.items():
        if date_str in filename or date_str.replace("-", "") in filename:
            return meeting_id

    return None


def canonical_meeting_id(meeting_id: str) -> str:
    """개최 형식을 남긴 회의 식별자를 정본형으로 변환한다.

    끝의 전자회의 표시(e 또는 electronic)를 제거한다. bis는 회의를 구분하는
    식별자이므로 유지하고, 구분자 없이 소문자로 정규화한다. 기준은
    docs/tsg/build/standards/meeting_id_normalization.md §3.2이며,
    check_meeting_consistency.py의 canonical_meeting_id와 같은 결과를 반환해야 한다.
    """
    s = re.sub(r"[-_](?:e|electronic)$", "", meeting_id.strip(), flags=re.IGNORECASE)
    s = re.sub(r"[-_]?bis", "bis", s, flags=re.IGNORECASE)
    return re.sub(r"[-_](?:e|electronic)$", "", s, flags=re.IGNORECASE)
