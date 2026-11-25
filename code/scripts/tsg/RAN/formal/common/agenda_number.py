"""agenda_number.py — 회의록 의제 번호(`9.1.2` 꼴)의 문법. 목차 · 제목 · 문단 머리가 함께 쓴다.

원문은 같은 의제 번호를 여러 꼴로 적는다.

    `7.1\tMaintenance …\t12`     번호 뒤 탭
    `2.\tGeneral\t11`            번호 뒤 점(최상위 의제 전부가 이 꼴인 회의록도 있다)
    `33. Closing of the meeting`  번호 뒤 점과 빈칸
    `11.4.6a\tL2/3 protocols …`   마지막 마디에 소문자 하나

번호는 뒤따르는 점을 뗀 꼴로 돌려준다. `4-5\tVoid` 같은 범위와 `8.11, 8.12 …` 같은 나열은
의제 하나를 가리키지 않으므로 읽지 않는다.
"""
from __future__ import annotations

import re
from collections.abc import Callable, Iterable

#: 의제 번호 한 개. 캡처 그룹 없음.
NUMBER = r"\d+(?:\.\d+)*[a-z]?"

#: 번호 뒤 점(있으면)과 빈칸까지. 그룹 1 = 번호, 그룹 2 = 나머지 글.
HEAD = re.compile(rf"^({NUMBER})\.?\s+(.+)$", re.S)

#: 목차 한 줄 `번호 제목 쪽`. 그룹 1 = 번호, 2 = 제목, 3 = 쪽.
TOC_LINE = re.compile(rf"^({NUMBER})\.?\s+(.+?)\s+(\d+)$", re.S)


def split_meeting_agenda(raw: str) -> tuple[str, str] | tuple[None, None]:
    """`{회의}-{의제}`에서 회의명의 하이픈을 보존해 의제 번호를 분리한다.

    `121-bis-8.1`과 `114bis-e-11.4.6a`는 마지막 의제 문법으로 구분한다.
    UNKNOWN과 기존 비정형 참조도 돌려주어 호출자가 보존·건너뛰기를 결정한다.
    """
    if raw.endswith("-UNKNOWN"):
        return raw[:-len("-UNKNOWN")], "UNKNOWN"
    match = re.search(rf"-({NUMBER})$", raw)
    if match:
        return raw[:match.start()], match.group(1)
    parts = raw.split("-", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (None, None)


#: 제목 머리의 번호와 그 뒤 구분. 그룹 1 = 번호, 2 = 끝 점, 3 = 구분 빈칸.
_OWN = re.compile(rf"^({NUMBER})(\.?)(?:([ \t\u00a0]+)\S|$)")


def own(heading: str) -> str | None:
    """제목 문단이 스스로 적은 의제 번호. 없으면 None.

    제목 글에 적힌 번호가 그 절의 의제다. 목차는 제목에서 만들어지되 깊이를 잘라 싣고, 같은 제목
    (`Other` · `In principle agreed CRs`)이 여러 의제에 되풀이되므로 목차 제목 대조는 이 번호를 대신하지 못한다.

    마디 하나짜리 번호 뒤에 빈칸만 오면 번호가 아니라 글의 첫 낱말일 수 있어(`10 MHz …` · `71 GHz` ·
    `1 new cause …`) 받지 않는다. 탭 · 끝 점 · 두 마디 이상이면 받는다. 제목 글 없이 번호만 적힌
    제목(`5.3.40.4`)도 같은 기준으로 받는다.
    """
    m = _OWN.match(heading.strip())
    if not m:
        return None
    number, dot, gap = m.groups()
    if "\t" in (gap or "") or dot or "." in number:
        return number
    return None


def choose_agenda(
    candidates: Iterable[tuple[str, int]],
    parent_agenda: str | None = None,
    heading_level: int | None = None,
) -> str | None:
    """부모 의제와 TOC 수준에 맞는 번호가 하나일 때만 선택한다.

    각 후보는 같은 목차 항목에서 읽은 (의제 번호, TOC 수준)이다. 알려진 부모가
    있으면 그 하위 번호로 제한하며, 후보가 여러 번호로 남으면 None을 반환한다.
    """
    unique = {
        agenda
        for agenda, level in candidates
        if (heading_level is None or level == heading_level)
        and (not parent_agenda or parent_agenda == "UNKNOWN"
             or agenda.startswith(parent_agenda + "."))
    }
    return next(iter(unique)) if len(unique) == 1 else None


def inherit_unnumbered(sections: list, continues: Callable[[str, str], bool]) -> None:
    """UNKNOWN 구간 양끝의 원래 의제 번호를 한 번씩 읽어 앞 번호 상속을 판정한다.

    sections의 항목은 agenda_number 문자열 속성을 제공한다. 상속 여부는 호출자가
    제공한 번호 비교 함수로 정하고, 상속한 번호를 다음 구간의 판정 근거로 쓰지 않는다.
    """
    previous = None
    unknown_start = 0
    for index, section in enumerate(sections):
        agenda = section.agenda_number
        if agenda == "UNKNOWN":
            continue
        if unknown_start < index and previous and continues(previous, agenda):
            for unknown_index in range(unknown_start, index):
                sections[unknown_index].agenda_number = previous
        previous = agenda
        unknown_start = index + 1
