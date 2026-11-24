"""tsg_cr_decision.py — TSG RAN 회의가 CR 팩 안의 CR 하나하나에 내린 판정을 TDoc 목록에서 읽는다.

한 CR 이 두 팩 이상의 표지에 실리는 일이 있다. 팩이 잘못된 표지로 올라와 다시 배포되거나(reissued),
팩이 새 번호로 고쳐지거나(revised), 회의가 팩의 일부만 승인하고 나머지를 다른 팩으로 다시 받기 때문이다.
그러면 같은 CR 의 문서 사본이 여러 팩 디렉토리에 놓이고, 어느 팩이 그 CR 을 실제로 다룬 팩인지는
파일 이름 · 경로 순서 · 팩 번호 크기로 정할 수 없다. 번호가 큰 팩이 고친 팩인 경우가 많지만,
회의가 「이 사본은 버린다」고 한 팩이 큰 번호이기도 하고 같은 회의에서 둘 다 승인되기도 한다.

정본은 TSG RAN 회의 보고서 zip 에 든 `TDoc_List_Meeting_RAN#NN_*.xlsx|xlsm` 의 CR 시트(`CRs_RAN…`)다.
한 행이 (팩 · WG 문서) 한 쌍이고, `Plenary doc` · `WG doc` · `TSG status` 칸이 그 쌍에 대한 회의 판정이다.
예를 들어 RAN#108 시트에서 `R1-2504980` 은 RP-251576 에 `reissued`, RP-251836 에 `approved` 로 실린다.

판정의 순위(`rank`, 작을수록 그 팩이 CR 을 다룬 팩이다):

    0  approved
    1  그 밖의 최종 판정(postponed · not pursued · withdrawn · rejected · noted · merged · not treated)
       그리고 판정을 모르는 쌍(TDoc 목록이 없는 회의의 팩 · 어느 시트에도 없는 RP 문서)
    2  revised · reissued — 같은 CR 이 다른 팩에서 다시 다뤄졌다는 뜻이다
    3  팩은 CR 시트에 있는데 그 CR 은 그 팩 행에 없다(`not listed`) — 표지에만 적힌 CR 이다.
       또는 RP 문서가 TDoc 시트(`Tdoclist…` · `Tdoc_list…`)에 팩이 아닌 종류로 실렸다(`not a pack`) —
       회의에서 고친 CR 을 RP 번호로 다시 올린 것이고, CR 디렉토리에는 팩처럼 놓인다

CR 시트에 행이 없는 팩은 TDoc 시트의 팩 판정(`Decision`)을 그 CR 의 판정으로 쓴다.

`rank`는 판정 순위를 반환한다. 같은 순위의 후보를 고르는 기준은 각 호출자가 정한다.

> 주의: TDoc 목록은 RAN#75 부터 RAN#110 까지 있고 RAN#111 · RAN#112 보고서 zip 에는 없다. 그 회의의 팩은
> 판정을 모르는 쌍(순위 1)이 된다. 보고서 본문 산문의 판정 문구는 회의마다 형식이 달라 읽지 않는다.
>
> 주의: 한 회의의 보고서 zip 여럿이 TDoc 목록의 서로 다른 판을 담기도 한다(RAN#78 · #81 · #90-e · #93-e
> · #107). zip 안 항목 시각이 가장 늦은 판을 쓴다. 이른 판은 회의 전에 만든 것이라 판정 칸이 비었다.

CR 시트의 한 행은 그 CR 의 Spec · CR 번호 · 개정 · Release 도 적는다(`identity`). 3GPP CR 데이터베이스에서
옮긴 값이라, CR 문서의 파일 이름이나 서식 머리가 다른 값을 적으면 시트를 따른다(Phase-4 기록은 `correct_identity`,
Phase-8 청크의 `CR0123r1` 꼴 번호는 `sheet_cr_label`). 단 Spec 은 파일 이름과 서식 머리가 같은 Spec 을 적으면
문서 값을 둔다(아래 주의).

> 주의: 파일 이름 · 서식 머리 · 서식 `Release:` 칸은 어느 하나도 늘 옳지 않다. RAN4 `R4-2002340` 은 파일 이름이
> `38113_CR0438r2…` 이지만 서식 · 표지 · CR 시트가 모두 38.133 이고, RAN1 `R1-1905750` 은 파일 이름 · 시트가
> 38.213 인데 서식 머리가 36.213 을 적는다. 서식의 CR 번호 칸이 옛 번호를 적기도 한다(RAN4 `R4-2012173` 은
> 파일 이름 · 시트가 CR1020 인데 서식이 0884). Release 는 파일 이름이 CR 이 아니라 주제의 Release 를 적는 일이
> 있다(RAN5 `R5-199549 - Rel-15_NR_38.521-2_FR2_6.3A.4` 는 38.905 CR 이고 서식 · 시트가 Rel-16). 미러 CR 은
> 파일 이름과 서식이 원래 CR 의 Release 를 그대로 두기도 한다(RAN1 `R1-2310448` 은 Category A 이고 서식의
> Current version 이 18.0.0 인데 파일 이름 · 서식이 Release 17, 시트가 Rel-18). 시트에 쌍이 없는 CR(TDoc 목록이
> 없는 회의의 팩)만 문서에서 읽은 값을 그대로 둔다.
>
> 주의: CR 시트도 Spec 을 잘못 적을 수 있다. RAN3 `R3-205801`(RP-201556 · RP-201949)은 파일 이름
> `38.473_CR0396r2…` · 서식 머리 · 제목이 모두 38.473 이고 본문도 F1AP 를 고치는데, CR 시트와 팩 표지는
> 38.423 CR0396 으로 적는다. 같은 회의의 `R3-205799` 가 38.423 CR0395 라 CR 데이터베이스에 등록할 때 Spec 을
> 잘못 고른 것으로 보인다. RAN#89e 는 RP-201556 사본을 `reissued`, RP-201949 사본을 `withdrawn` 으로 두었고,
> 38.423 변경 이력의 RP-201949 행에는 CR0395 가 있고 CR0396 은 없으며, 38.473 변경 이력에도 CR0396 이
> 없다. 그래서 Spec 은 파일 이름과 서식 머리가 같은 값을 적으면 문서 값을 두고, 둘이 다를 때만 시트 값을 쓴다
> (`R4-2002340` · RAN2 `R2-2313679` 처럼 한쪽만 틀린 경우).
>
> 주의: 표지는 시트가 다른 팩에만 둔 CR 을 함께 적기도 한다. RAN#100 RP-230979 의 표지는 RP-230977 ·
> RP-230978 의 RAN5 CR 들을, RAN#98-e RP-223292 의 표지는 RP-223293 의 `R4-2220380` 을 적지만 CR 시트는
> 그 CR 들을 RP-230977 · RP-230978 · RP-223293 에만 `approved` 로 둔다. 회의 보고서 본문은 두 팩을 모두
> 승인했다고만 적어 이 쌍들을 가르지 못한다.
"""
from __future__ import annotations

import functools
import io
import re
import sys
import zipfile
from pathlib import Path

_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(_ROOT / "scripts" / "common" / "common"))
import axis  # noqa: E402

REPORTS = axis.tree_path("corpus", wg="TSG_RAN", doc_type="meetings", slot="source")

_LIST = re.compile(r"TDoc_List_Meeting_(RAN#[0-9]+(?:-?e)?)[^/]*\.xls[xm]$")
# WG 문서 번호는 두 꼴이다. `R1-2504980` 처럼 머리와 숫자를 하이픈으로 잇는 꼴, 그리고 RAN5 하위 그룹 문서처럼
# 하이픈 없이 `R5s` 와 숫자 여섯 자리를 붙인 꼴이다. 뒤 꼴은 CR 시트의 WG doc 칸과 Phase-4 파싱 기록 · 그래프의
# CR 노드 `tdocNumber` 가 모두 소문자 `s` 로 적으므로 그 표기로 정규화한다. `s` 를 떼고 `R5-` 로 바꾸지 않는다.
# 같은 숫자의 `R5-` 문서가 따로 있고 다른 문서다. 시트와 그래프에 없는 꼴(하이픈 붙은 하위 그룹 꼴, 다른 WG 의
# 하위 그룹 꼴, 여섯 자리가 아닌 숫자)은 받지 않는다.
_TDOC = re.compile(r"\b(?:([A-Z][A-Z\d]?)-(\d{5,7})|(R5)S(\d{6}))\b")

APPROVED = "approved"
SUPERSEDED = frozenset({"revised", "reissued"})
NOT_LISTED = "not listed"
NOT_A_PACK = "not a pack"


def _norm(t) -> str:
    m = _TDOC.search(str(t or "").strip().upper())
    if not m:
        return ""
    return f"{m.group(1)}-{m.group(2)}" if m.group(1) else f"{m.group(3)}s{m.group(4)}"


def _latest_lists() -> dict[str, tuple[Path, str]]:
    """회의 디렉토리 → (보고서 zip, 그 안의 TDoc 목록 항목). 항목 시각이 가장 늦은 판."""
    out = {}
    for md in sorted(REPORTS.glob("TSGR_*")):
        best = None
        for z in sorted((md / "Report").glob("*.zip")):
            try:
                with zipfile.ZipFile(z) as zf:
                    for i in zf.infolist():
                        if _LIST.search(i.filename):
                            key = (i.date_time, i.filename)
                            if best is None or key > best[0]:
                                best = (key, z, i.filename)
            except (OSError, zipfile.BadZipFile):
                continue
        if best:
            out[md.name] = (best[1], best[2])
    return out


def _sheet_rows(wb, prefix: str, need: set[str]):
    """이름이 `prefix` 로 시작하는 시트(밑줄 무시)의 (머리 칸 → 위치, 행 반복자). 칸이 모자라면 건너뛴다."""
    for sn in wb.sheetnames:
        if not sn.lower().replace("_", "").startswith(prefix) or "ran" not in sn.lower():
            continue
        rows = wb[sn].iter_rows(values_only=True)
        hdr = [str(h).strip() if h else "" for h in next(rows, ())]
        if need <= set(hdr):
            yield {h: i for i, h in enumerate(hdr) if h}, rows
            return


def decisions():
    """CR 시트와 TDoc 시트를 읽어 세 표를 돌려준다.

    pairs   (팩, WG 문서) → (판정, 회의)    CR 시트의 행
    packs   CR 시트에 행이 있는 팩 집합
    plenary RP 문서 → (문서 종류, 판정, 회의)  TDoc 시트의 행. 팩이 아닌 RP 문서(회의에서 고친 CR 등)를 가린다
    """
    return _lists()[:3]


@functools.lru_cache(maxsize=1)
def _lists():
    """`decisions` 의 세 표와, (팩, WG 문서) → (Spec, CR, 개정, Release) 인 CR 시트의 신원 표."""
    import openpyxl

    pairs: dict[tuple[str, str], tuple[str, str]] = {}
    packs: set[str] = set()
    plenary: dict[str, tuple[str, str, str]] = {}
    ids: dict[tuple[str, str], tuple[str, str, str, str]] = {}
    for _md, (z, name) in sorted(_latest_lists().items()):
        meeting = _LIST.search(name).group(1).replace("-e", "e")
        with zipfile.ZipFile(z) as zf:
            data = zf.read(name)
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        try:
            for col, rows in _sheet_rows(wb, "crs", {"Plenary doc", "WG doc", "TSG status"}):
                for r in rows:
                    pack, wg = _norm(r[col["Plenary doc"]]), _norm(r[col["WG doc"]])
                    if not pack.startswith("RP-") or not wg:
                        continue
                    packs.add(pack)
                    status = str(r[col["TSG status"]] or "").strip().lower()
                    old = pairs.get((pack, wg))
                    # 중복 쌍은 순위가 앞서는 행의 판정과 CR 식별자를 함께 보존한다.
                    if old is None or _status_rank(status) < _status_rank(old[0]):
                        pairs[(pack, wg)] = (status, meeting)
                        ids.pop((pack, wg), None)
                        if {"Spec", "CR", "REL"} <= col.keys():
                            ids[(pack, wg)] = tuple(str(r[col[c]] or "").strip() if c in col else ""
                                                    for c in ("Spec", "CR", "Rev", "REL"))
            for col, rows in _sheet_rows(wb, "tdoclist", {"Tdoc", "Doc-type", "Decision"}):
                for r in rows:
                    t = _norm(r[col["Tdoc"]])
                    if t.startswith("RP-"):
                        plenary[t] = (str(r[col["Doc-type"]] or "").strip().lower(),
                                      str(r[col["Decision"]] or "").strip().lower(), meeting)
        finally:
            wb.close()
    return pairs, frozenset(packs), plenary, ids


def _status_rank(status: str) -> int:
    if status == APPROVED:
        return 0
    if status in SUPERSEDED:
        return 2
    if status in (NOT_LISTED, NOT_A_PACK):
        return 3
    return 1


def decision(tdoc: str, pack: str) -> tuple[str, str]:
    """(판정, 회의).

    CR 시트에 그 쌍이 있으면 그 판정. 팩은 CR 시트에 있는데 쌍이 없으면 'not listed'. 팩이 CR 시트에 없으면
    TDoc 시트를 본다 — CR 팩이면 팩 전체의 판정, 팩이 아닌 RP 문서면 'not a pack'. 어느 시트에도 없으면 ('', '').
    """
    pairs, packs, plenary = decisions()
    key = (_norm(pack), _norm(tdoc))
    if key in pairs:
        return pairs[key]
    if key[0] in packs:
        return NOT_LISTED, ""
    if key[0] in plenary:
        kind, dec, meeting = plenary[key[0]]
        return (dec if kind == "cr pack" else NOT_A_PACK), meeting
    return "", ""


def rank(tdoc: str, pack: str) -> int:
    return _status_rank(decision(tdoc, pack)[0])


def identity(tdoc: str, pack: str) -> dict[str, str] | None:
    """CR 시트가 그 쌍에 적은 `spec` · `cr` · `rev` · `release`. 시트에 그 쌍이 없으면 None."""
    row = _lists()[3].get((_norm(pack), _norm(tdoc)))
    if row is None:
        return None
    return dict(zip(("spec", "cr", "rev", "release"), row))


def _cr_digits(value) -> str:
    return re.sub(r"(?i)r\d+$", "", str(value or "").strip()).lstrip("0")


def _document_spec(source_path: str) -> str:
    """CR 문서의 파일 이름과 서식 머리가 같은 Spec 을 적으면 그 Spec, 아니면 빈 문자열."""
    import cr_form
    import docx_text

    name = cr_form.filename_spec(Path(source_path).name)
    if not name:
        return ""
    path = Path(source_path) if Path(source_path).is_absolute() else _ROOT / source_path
    return name if cr_form.header_spec(docx_text.open_document(str(path))) == name else ""


def correct_identity(results) -> tuple[dict[str, dict[str, list]], int, dict[str, list]]:
    """기록의 `spec_number` · `cr_number` · `release` 를 CR 시트 값으로 맞춘다.

    돌려주는 값은 ({tdoc: {필드: [읽은 값, 시트 값]}}, 시트에 쌍이 없는 기록 수, {tdoc: [문서 Spec, 시트 Spec]}).
    시트가 빈 칸이면 그 필드는 두고, CR 번호는 앞 0 과 개정 꼬리(`r1`)를 떼고 견준다. 개정은 이 함수가 다루지
    않는다. 기록은 CR 번호를 숫자만으로, 개정을 따로 `rev` 에 둔다.

    Spec 은 파일 이름과 서식 머리가 같은 Spec 을 적고 기록도 그 값이면 시트가 달라도 두고, 세 번째 값에 적는다
    (모듈 주의의 `R3-205801`).
    """
    corrections: dict[str, dict[str, list]] = {}
    kept_spec: dict[str, list] = {}
    unlisted = 0
    for r in results:
        if not r.tdoc_number:
            continue
        reg = identity(r.tdoc_number, r.cr_pack_id or "")
        if reg is None:
            unlisted += 1
            continue
        fixed = {}
        if reg["spec"] and r.spec_number != reg["spec"]:
            if r.spec_number and _document_spec(r.source_path) == r.spec_number:
                kept_spec[r.tdoc_number] = [r.spec_number, reg["spec"]]
            else:
                fixed["spec_number"] = [r.spec_number, reg["spec"]]
        if reg["cr"] and _cr_digits(r.cr_number) != _cr_digits(reg["cr"]):
            fixed["cr_number"] = [r.cr_number, reg["cr"]]
        if reg["release"] and r.release != reg["release"]:
            fixed["release"] = [r.release, reg["release"]]
        for field, (_old, new) in fixed.items():
            setattr(r, field, new)
        if fixed:
            corrections[r.tdoc_number] = fixed
    return dict(sorted(corrections.items())), unlisted, dict(sorted(kept_spec.items()))


def sheet_cr_label(cr_number: str, tdoc: str, pack: str) -> str:
    """`CR0123r1` 꼴 CR 번호. CR 시트가 그 쌍에 다른 번호를 두면 시트의 번호와 개정으로 적는다.

    번호가 시트와 같으면 받은 값을 그대로 둔다. 팩이 없거나 시트에 쌍이 없어도 그대로 둔다.

    > 주의: 파일 이름과 서식이 같은 번호를 적어도 시트가 다른 번호를 둘 수 있다. RAN4 RAN#96 의 `R4-2210547`
    > (RP-221661)과 `R4-2211342`(RP-221681)는 둘 다 38.101-1 CR1117 을 적고, 시트는 뒤 CR 에 CR1124 를 둔다.
    > 한 Spec 안에서 번호가 겹친 것을 시트가 가른 경우라 시트 번호를 쓴다.

    > 주의: 개정은 어느 출처도 늘 맞지 않는다. RAN1 `R1-2104065` 는 파일 이름(`CR0182r1`)과 서식이 개정 1,
    > CR 시트와 팩 표지가 개정 없음이고, RAN2 `R2-1902814` 는 파일 이름 · 서식 · 팩 표지가 개정 2, 시트만
    > 개정 1 이다. 그래서 개정은 번호가 틀린 파일 이름에서만 시트 값으로 바꾼다. 번호가 틀린 이름은 개정도
    > 믿을 수 없어서다.
    """
    reg = identity(tdoc, pack) if pack else None
    if reg is None or not reg["cr"]:
        return cr_number
    if _cr_digits(re.sub(r"(?i)^CR", "", cr_number or "")) == _cr_digits(reg["cr"]):
        return cr_number
    rev = reg["rev"]
    return f"CR{reg['cr']}r{rev}" if rev.isdigit() and rev != "0" else f"CR{reg['cr']}"


def tsg_cr(pack: str) -> bool:
    """`pack` 디렉토리가 CR 팩이 아니라 TSG 회의에 RP 번호로 바로 올라온 CR 하나인가.

    CR 시트에 그 RP 번호의 팩 행이 없고 TDoc 시트가 그 RP 문서의 종류를 `cr` 로 둘 때다.
    """
    _pairs, packs, plenary = decisions()
    p = _norm(pack)
    return p not in packs and plenary.get(p, ("",))[0] == "cr"


def split_tsg_cr(results) -> tuple[list, list]:
    """(나머지 기록, TSG CR 디렉토리에 든 문서의 기록). `cr_pack_id` 가 `tsg_cr` 인 기록을 가른다.

    그런 디렉토리의 문서는 그 RP 번호의 CR 이고 WG CR 이 아니다. 문서가 WG 번호를 적어도(고친 WG CR 의
    번호 · 서식 머리의 틀린 번호) 그 번호의 WG CR 기록이 되면 남의 CR 노드에 이 문서의 서식이 실리고, 팩이 아닌
    RP 번호가 팩이 된다. 부르는 쪽은 가른 기록을 `tsg_direct_cr` 에 그 WG 번호와 함께 남긴다.

    > 주의: RAN4 `RP-243079` 는 TDoc 시트에서 RAN#106 의 `cr`(`approved`)이고 그 디렉토리의 `RP-243079.docx` 는
    > 38.101-1 CR2562 rev 2 다. 서식 머리는 `R4-2420 522` 를 적는데 CR 시트의 비고는 그 번호가 표지에 잘못 적힌
    > 번호라고 하고, Phase-1 의 `R4-2420522` 는 38.307 의 draftCR 이다. 이 문서를 WG 번호로 받으면 그 draftCR 이
    > 38.101-1 CR 의 서식을 갖고 `RP-243079` 팩에 소속된다. 같은 RAN4 의 `RP-182836` · `RP-182837` 은 파일 이름이
    > 그 CR 이 바탕으로 삼은 WG CR(RP-182359 의 `R4-1816555` · `R4-1815562`)의 번호를 적고, `RP-190679` 는 파일 이름이
    > RP-190403 의 38.101-2 CR0018 인 `R4-1902678` 을 적는데 CR 시트 비고는 표지의 Tdoc 번호가 틀렸다고 한다.
    """
    kept, own = [], []
    for r in results:
        (own if r.tdoc_number and r.cr_pack_id and tsg_cr(r.cr_pack_id) else kept).append(r)
    return kept, own


def reconcile_cover_numbers(results, read_cover) -> dict[str, list]:
    """파일 이름의 번호가 그 팩의 CR 이 아닐 때 서식 머리가 적은 번호로 기록을 고친다.

    대상은 (파일 이름 번호 · 팩) 쌍이 CR 시트에서 `not listed` 인 기록이다. `read_cover(source_path)` 가
    서식 머리의 번호를 주고, 그 번호와 팩의 쌍이 CR 시트에 판정을 가지면(순위 3 미만) `tdoc_number` 를 그
    번호로 바꾼다. 같은 팩에 그 번호의 기록이 이미 있으면 두 기록이 한 CR 을 다투게 되므로 두고, 서식이 번호를
    주지 못해도 둔다. 중복 제거보다 먼저 불러야 고친 번호로 사본을 견준다.

    돌려주는 값은 {파일 이름 번호: [서식 번호, 팩, source_path]} 다.

    > 주의: RAN4 RAN#90-e 의 다섯 문서는 파일 이름이 회의에서 고치기 전 판의 번호를 적고 서식 머리는 고친 판의
    > 번호를 적는다. `R4-2017368`(RP-202487 · 38.133 CR1161) 의 서식은 `R4-2017378` 을, `R4-2016504`
    > (RP-202416) 는 `R4-2017665` 를, `R4-2017096`(RP-202419) 는 `R4-2017351` 을, `R4-2017128`(RP-202430) 는
    > `R4-2017330` 을, `R4-2014167`(RP-202440) 는 `R4-2017804` 를 적는다. CR 시트는 다섯 팩 모두 서식 번호에만
    > `approved` 를 두고 파일 이름 번호는 그 팩 행에 없다. WG 목록에서도 파일 이름 번호는 `revised`, 서식 번호는
    > `agreed` 이고 서식 번호는 파일 이름 번호의 개정 사슬(`IS_REVISION_OF`) 끝에 있다(`R4-2016504` 는
    > `R4-2017516` 을 거쳐 `R4-2017665` 로, 나머지 넷은 한 번에 닿는다). 파일 이름 번호로 받으면 팩 소속과
    > CR 서식 내용이 회의에서 대체된 판의 노드에 실리고 승인된 판의 노드는 팩을 잃는다.
    """
    have = {(_norm(r.tdoc_number), _norm(r.cr_pack_id)) for r in results if r.tdoc_number and r.cr_pack_id}
    fixed: dict[str, list] = {}
    for r in results:
        if not (r.tdoc_number and r.cr_pack_id) or decision(r.tdoc_number, r.cr_pack_id)[0] != NOT_LISTED:
            continue
        cover = read_cover(r.source_path)
        if not cover or _norm(cover) == _norm(r.tdoc_number) or rank(cover, r.cr_pack_id) >= 3:
            continue
        if (_norm(cover), _norm(r.cr_pack_id)) in have:
            continue
        fixed[r.tdoc_number] = [cover, r.cr_pack_id, r.source_path]
        r.tdoc_number = cover
        have.add((_norm(cover), _norm(r.cr_pack_id)))
    return dict(sorted(fixed.items()))
