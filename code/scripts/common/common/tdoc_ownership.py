"""회의 간에 같은 TDoc 번호가 사용될 때 적재 대상 회의를 선언하고 선택 규칙을 적용한다.

포인트 식별자는 `md5(f"{tdocNumber}_{chunkIndex}")`로 정해지며 회의 정보는 포함하지 않는다.
3GPP FTP에 같은 TDoc 번호가 두 회의에 등록된 사례가 있어, 컬렉션에는 둘 중 한 회의의
문서만 적재할 수 있다. 수집 단계의 배치 오류가 아니므로 외부 원문은 수정하지 않고,
적재 대상 회의를 명시적으로 선택한다.

명시적인 선택 규칙이 없으면 `sorted(base_path.iterdir())`의 순회 순서에 따라
사전순으로 뒤에 있는 문서가 앞의 문서를 덮어쓴다. 이 순서는 적재 대상 회의의 근거가 아니다.
RAN3의 세 사례는 적재 대상 회의가 모두 사전순으로 앞에 있어, 이 규칙 없이는
다른 회의의 사본이 적재된다.

선언과 적용 함수를 같은 모듈에서 관리한다(§0.5 집행 짝 = 규칙은 한 자리에만).
선언만 추가하고 적재 단계에 적용하지 않으면 위반이 계속 보고된다. 두 모듈로 나누면
한쪽만 수정되어 선언과 실제 적재 조건이 불일치할 수 있다.

참조 경로:
  - `scripts/common/data-integrity/check_vdb_tree_parity.py` (게이트 52) — 판정
  - `scripts/tsg/RAN/formal/RAN{1..5}/phase-6/qdrant/02_load_qdrant.py` — 적재 시 적용
"""

from __future__ import annotations

#: 3GPP FTP에서 같은 TDoc 번호가 두 회의에 등록되어 있고 본문도 다른 사례다.
#: 두 회의의 `source/Docs/`에 크기·md5·내부 파일명이 다른 zip이 각각 있으므로,
#: 자체 배치 오류로 처리하여 원문을 수정하지 않는다. 컬렉션에는 한 회의의 문서만
#: 적재할 수 있어 대상 회의와 근거를 선언하고 실제 적재 내용이 선언과 일치하는지 확인한다.
#: 근거는 해당 회의의 `TDoc_List` 등재 여부와 번호대 배정이다.
#: 선언에 없는 번호에서 본문이 다른 중복이 발견되면 새 사례로 보고 차단한다.
DECLARED_OWNER: dict[str, tuple[str, str]] = {
    "R2-166867": ("RAN2#95bis",
                  "번호대 R2-166000..167324 = RAN2#95bis 배정이고 그 목록에 등재. "
                  "RAN2#95 (R2-164600..165989) 목록에는 없다."),
    "R3-202018": ("RAN3#107bis-e",
                  "번호대 R3-201500..202933 = RAN3#107bis-e 배정이고 그 목록에 "
                  "'(TP for NR_IAB BL CR for TS 38.473): Routing Selection' 으로 등재. "
                  "RAN3#119bis-e 목록에는 없다."),
    "R3-230849": ("RAN3#119",
                  "번호대 R3-230001..231064 = RAN3#119 배정이고 그 목록에 "
                  "'NRPPA corrections of references to RRC' 로 등재. RAN3#123 목록에는 없다."),
    "R3-241112": ("RAN3#123",
                  "번호대 R3-240001..241213 = RAN3#123 배정이고 그 목록에 "
                  "'CHO with CPAC' 로 등재. RAN3#123-bis (R3-241501..242243) 목록에는 없다."),
}


def drop_misplaced(chunks: list[dict]) -> tuple[list[dict], list[str]]:
    """선언된 TDoc 번호에 대해 적재 대상 회의가 아닌 회의의 청크를 제외한다.

    식별자가 겹치는 청크뿐 아니라 해당 사본의 모든 청크를 제외한다. 나머지 청크를
    적재하면 하나의 문서 번호에 두 회의의 본문이 섞이기 때문이다. 게이트 52의
    기대 집합에서도 같은 청크를 제외하여 검사와 적재에 같은 규칙을 적용한다.

    선언에 없는 tdoc은 변경하지 않는다. 선언되지 않은 번호에서 서로 다른 본문이
    발견되면 자동으로 선택하지 않고 게이트 52가 「선언되지 않은 갈라짐」으로 차단한다.

    반환: (유지한 청크, 제외한 청크의 이름). 호출부에서 제외 내역과 개수를
    기록할 수 있도록 제외한 청크의 이름을 함께 반환한다.
    """
    kept: list[dict] = []
    dropped: list[str] = []
    for c in chunks:
        owner = DECLARED_OWNER.get(c.get("tdocNumber"))
        if owner is not None and c.get("meetingId") != owner[0]:
            dropped.append(f"{c.get('meetingId')}/{c.get('tdocNumber')}"
                           f"#{c.get('chunkIndex')} (정당 소유 {owner[0]})")
            continue
        kept.append(c)
    return kept, dropped
