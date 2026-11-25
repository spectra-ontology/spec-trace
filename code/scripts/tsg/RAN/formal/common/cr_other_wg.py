"""cr_other_wg.py — 다른 WG 의 CR 슬롯에 놓인 CR 을 그 CR 을 만든 WG 의 입력으로 돌린다.

Phase-0 은 CR 을 TSG 팩 단위로 모으고, 팩은 그 팩을 TSG 에 낸 WG 의 슬롯
(`change-requests/{WG}/derived/Rel-*/TSG/{팩}/`)에 놓는다. 그런데 한 WG 가 낸 팩에 다른 WG 번호의 CR 이
실리기도 한다. RAN3 가 낸 `RP-190561` · `RP-191427` 은 RAN2 CR 인 36.300 CR1229(`R2-1902764`) ·
CR1239r1(`R2-1908521`)을 RAN3 CR 과 함께 싣고, 팩 표지도 그 행을 RAN2 회의(`RAN2#105` · `R2-106`)와
R2 번호로 적는다. 파서는 자기 슬롯만 읽고 자기 WG 번호만 CR 로 받으므로 이런 CR 은 어느 WG 에서도
읽히지 않는다. 만든 WG 는 파일을 보지 못하고, 놓인 WG 는 번호를 받지 않아 `tdocNumber` 추출 실패
(Phase-4)와 식별자 없는 파일(Phase-8)로 센다.

그래서 CR 파일의 주인을 파일 이름의 WG 번호로 정한다. 이름에서 처음 나오는 WG 번호(`R{1~5}-NNNNNN(N)` ·
`R5sNNNNNN`)의 WG 가 주인이다. RP 번호로 시작하는 이름(TSG 에 바로 낸 문서 · 팩 표지)과 WG 번호가 없는
이름은 주인을 정하지 않고 놓인 슬롯의 WG 에 둔다. `collect(wg)` 는

* 자기 슬롯의 `cr_inputs.collect` 결과에서 다른 WG 가 주인인 파일을 빼서 따로 돌려주고(`other_wg`),
* 다른 WG 슬롯에서 이 WG 가 주인인 파일을 더한다.

> 주의: 팩 번호와 디렉토리 Release 는 파일이 실제로 놓인 슬롯을 기준으로 읽는다(`slot_of` · `release`).
> 자기 슬롯 `INPUT_DIR` 을 기준으로 `cr_inputs.pack_id` 를 부르면 다른 슬롯의 파일에서 ValueError 가 난다.
>
> 주의: 다른 슬롯에 놓인 CR 의 팩은 만든 WG 슬롯에 없으므로 그 WG 의 표지 파서는 표지를 보지 못한다.
> 표지가 없으면 CRPack 에 `tsgMeeting` 이 빠진다. 표지 파서는 `foreign_packs(wg)` 의 팩도 읽어야 하고, 표의
> 행을 자기 WG 번호로 거르므로 그 팩의 다른 WG 행은 들어오지 않는다.
>
> 주의: 이름에 다른 WG 번호가 처음 나오는 파일을 슬롯 WG 의 CR 로 받는 일이 맞는 경우는 지금 슬롯에
> 없다(다섯 WG 슬롯 전체에서 이름의 첫 WG 번호가 슬롯 WG 와 다른 `.docx` 는 위 두 파일뿐이다). 그런
> 파일이 새로 생기면 `other_wg` 메타데이터에 경로와 주인 WG 가 남는다.
"""
from __future__ import annotations

import functools
import re
from pathlib import Path

import cr_inputs

_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
WGS = tuple(f"RAN{n}" for n in range(1, 6))
#: 파일 이름 안의 WG 번호. 앞뒤가 글자 · 숫자에 붙지 않은 것만 본다.
_WG_TDOC = re.compile(r"(?<![0-9A-Za-z])(?:R([1-5])[-_]\d{6,7}|R(5)s\s?\d{6})(?!\d)")
_RP_NAME = re.compile(r"RP[-_ ]?\d", re.I)


def owner_wg(name: str) -> str | None:
    """파일 이름이 정하는 주인 WG(`RAN2`). RP 번호로 시작하거나 WG 번호가 없으면 None."""
    if _RP_NAME.match(name):
        return None
    m = _WG_TDOC.search(name)
    return f"RAN{m.group(1) or m.group(2)}" if m else None


@functools.lru_cache(maxsize=None)
def _slot(wg: str) -> tuple[tuple[tuple[Path, str], ...], tuple[Path, ...]]:
    files, unconverted = cr_inputs.collect(cr_inputs.derived_dir(wg))
    return tuple(files), tuple(unconverted)


def slot_of(path: Path) -> Path:
    """파일이 놓인 WG 슬롯(`cr_inputs.derived_dir`)."""
    for wg in WGS:
        root = cr_inputs.derived_dir(wg)
        if path.is_relative_to(root):
            return root
    raise ValueError(f"CR 슬롯 밖의 파일: {path}")


def release(path: Path) -> str:
    """파일이 놓인 디렉토리 Release(`Rel-15`)."""
    return path.relative_to(slot_of(path)).parts[0]


def pack_id(path: Path) -> str:
    """파일이 든 팩(`RP-NNNNNN`). 다른 WG 슬롯에 놓인 파일도 그 슬롯을 기준으로 읽는다."""
    return cr_inputs.pack_id(path, slot_of(path))


def collect(wg: str) -> tuple[list[tuple[Path, str]], list[Path], dict[str, str]]:
    """`cr_inputs.collect` 에 주인 규칙을 더한 `(파일, Release)` 목록 · 읽을 수 없는 문서 · {자기 슬롯에 놓인
    다른 WG 주인 파일(저장소 루트 기준): 주인 WG}.

    순서는 자기 슬롯 파일 다음 다른 슬롯 파일(WG 순)이고, 각 슬롯 안은 `cr_inputs.collect` 의 순서다.
    """
    root = _ROOT
    own_files, own_unconverted = _slot(wg)
    other_wg: dict[str, str] = {}
    files: list[tuple[Path, str]] = []
    unconverted: list[Path] = []
    for f, rel in own_files:
        owner = owner_wg(f.name)
        if owner and owner != wg:
            other_wg[str(f.relative_to(root))] = owner
        else:
            files.append((f, rel))
    for f in own_unconverted:
        owner = owner_wg(f.name)
        if owner and owner != wg:
            other_wg[str(f.relative_to(root))] = owner
        else:
            unconverted.append(f)
    for other in WGS:
        if other == wg:
            continue
        o_files, o_unconverted = _slot(other)
        files += [(f, rel) for f, rel in o_files if owner_wg(f.name) == wg]
        unconverted += [f for f in o_unconverted if owner_wg(f.name) == wg]
    return files, unconverted, dict(sorted(other_wg.items()))


def foreign_packs(wg: str) -> list[tuple[Path, str]]:
    """이 WG 가 주인인 CR 이 놓인 다른 WG 슬롯의 팩 `(팩 디렉토리, Release)`. 자기 슬롯에 같은 팩이 있으면 뺀다."""
    own = {p.name for p in cr_inputs.derived_dir(wg).glob("Rel-*/TSG/*") if p.is_dir()}
    files, unconverted, _ = collect(wg)
    packs: dict[Path, str] = {}
    for f in [f for f, _ in files] + unconverted:
        root = slot_of(f)
        if root == cr_inputs.derived_dir(wg):
            continue
        parts = f.relative_to(root).parts
        pack_dir = root.joinpath(*parts[:3])
        if pack_dir.name not in own:
            packs.setdefault(pack_dir, parts[0])
    return sorted(packs.items())
