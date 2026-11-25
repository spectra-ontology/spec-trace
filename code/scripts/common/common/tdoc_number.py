"""TDoc 폴더 이름에서 TDoc 번호를 결정하는 공통 규칙.

코퍼스의 TDoc 폴더 이름은 3GPP 아카이브 이름을 그대로 사용하므로 번호 외의 문자가
포함될 수 있다. 이를 번호로 그대로 사용하면 Phase-1 KG의 Tdoc 번호와 일치하지 않아
메타데이터 조회가 실패한다. 이 실패는 예외 없이 해당 문서의 검색 누락으로 나타날 수 있다.

번호 생성과 번호 검사는 같은 규칙을 사용한다. 생성된 번호에 정규화 규칙을 다시 적용했을 때
값이 변하지 않는지 검사한다(고정점). 새로운 표기 형식의 정규화 규칙이 추가되면,
게이트도 같은 함수를 사용해 정규화 전 식별자를 검출한다.

참조하는 코드:
  - `scripts/tsg/RAN/formal/RAN{1..5}/phase-6/tdoc-parser/parse_tdoc_lib.py` — 파싱(03)의 산출물
    이름과 보강(04·05)의 원본 조회 이름
  - `scripts/common/data-integrity/check_tdoc_identifier_hygiene.py` — 파생 식별자 판정
  - `scripts/tsg/RAN/formal/RAN{1..5}/phase-6/metadata/01_enrich_metadata.py` — 접미사가 붙은 이름의
    메타데이터를 접두의 TDoc 번호로 조회(`parent_tdoc_number`)
"""
from __future__ import annotations

import re
import unicodedata
from urllib.parse import unquote

# TDoc 번호 꼴: 머리(`R1` · `RP` · `S2` …) + 구분자 + 숫자.
_TDOC_NUMBER_SHAPE = re.compile(r"([A-Za-z]+\d*)[-_](\d+)")


def tdoc_number_of(folder_name: str) -> str:
    """TDoc 폴더 이름을 TDoc 번호로 정규화한다.

    아카이브 이름의 앞뒤 공백은 제거한다. `%20`으로 인코딩된 공백을 포함한 폴더도
    있다(`R1-2110701%20`).

    보이지 않는 서식 문자(번호 뒤의 U+200E), 줄 바꿈 없는 하이픈(U+2011) 같은 유니코드
    대시, 끝 마침표(`R1-1814136.`), 소문자 접두(`r1-1713016`), 밑줄 구분자(`R3_230984`)를
    정규화한다. 처리 결과가 번호 형식과 전체 일치할 때만 접두를 대문자로, 구분자를 `-`로
    변환한다. 접미사가 붙은 이름(`R3-185310-1` · `R4-2103133x` · `…_attach_S5-237084` · 제목이
    붙은 이름)은 다른 파일을 구분하므로 유지한다. 같은 회의에 정규 이름 폴더가 함께 있으면
    접미사가 있는 이름은 정렬상 뒤에 온다. 파싱(03)은 정규 이름 폴더를 선택하고,
    같은 번호의 다른 폴더는 중복으로 기록한 뒤 제외한다.
    """
    name = unquote(folder_name)
    bare = "".join("-" if unicodedata.category(ch) == "Pd" else ch
                   for ch in name if unicodedata.category(ch) != "Cf")
    m = _TDOC_NUMBER_SHAPE.fullmatch(bare.strip().rstrip(".").strip())
    return f"{m.group(1).upper()}-{m.group(2)}" if m else name.strip()


def parent_tdoc_number(number: str) -> str | None:
    """접미사가 붙은 TDoc 이름에서 접두의 정규 TDoc 번호를 반환한다.

    접미사가 없거나 접두가 번호 형식이 아니면 None을 반환한다.
    `tdoc_number_of`가 유지하는 접미사 이름(`R3-237153_attach_S2-2311681` · `R4-2103133x`)은
    Phase-1 목록에 해당 이름의 행이 없다. 접두의 번호는 해당 파일을 포함한 TDoc의 번호이므로,
    원래 이름으로 메타데이터를 찾지 못했을 때 이 번호로 다시 조회한다. 식별자 자체는 유지한다.
    """
    m = _TDOC_NUMBER_SHAPE.match(number)
    if not m or m.end() == len(number):
        return None
    return f"{m.group(1).upper()}-{m.group(2)}"
