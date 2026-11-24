"""Phase-1 `CR.crNumber` 를 TSG CR 시트가 확인한 Phase-4 CR 번호로 맞추고, 비어 있으면 그 번호로 채운다.

`crNumber` 는 Phase-1 이 WG Tdoc 목록의 CR 칸에서 받는다. 그 칸은 TSG 회의가 확정한 번호와 다를 수 있다
(WG 회의 뒤 번호가 겹쳐 TSG CR 시트가 다른 번호를 주는 경우 등). CR 번호의 정본은 TSG 회의 보고서의
CR 시트이고, Phase-4 파서는 기록의 번호를 그 시트 값으로 맞춘다(`tsg_cr_decision.correct_identity`).
그래서 Phase-4 적재기가 이 모듈로 Phase-1 값을 시트가 확인한 값으로 바꾼다.

값이 있는 노드를 바꾸는 조건은 셋이 모두 맞을 때다.
1. 기록의 (팩 · WG 문서) 쌍이 CR 시트에 있고 시트 CR 칸이 비어 있지 않으며, 기록 번호가 그 시트 번호와 같다
   (`verified_numbers`). 시트에 쌍이 없으면 문서가 적은 번호를 확인할 길이 없어 두지 않는다.
2. 노드의 `crNumber` 가 있고 그 번호가 시트 번호와 다르다. 번호는 개정 꼬리(`r1`)와 앞 0 을 떼고 견준다.
3. 같은 WG 그래프에서 같은 Spec 의 다른 CR 노드가 그 번호를 쓰고 있지 않다. 쓰고 있으면 한 Spec 안의 번호가
   두 CR 로 겹치므로 덮어쓰지 않고 충돌로만 보고한다. 단 그 노드가 대상과 같은 개정 사슬(`REVISED_TO` ·
   `IS_REVISION_OF` 로 이어진 Tdoc 묶음, 방향 · 길이 무관) 안이면 같은 CR 의 다른 개정이라 충돌로 치지 않는다.
   이번에 함께 바꾸거나 채울 노드끼리 같은 Spec · 번호를 사슬 밖에서 나누어도 충돌이다.

`crNumber` 가 없는(null) 노드는 1 · 3 에 더해 기록 문서의 파일 이름이 적은 CR 번호도 시트 번호와 같을 때만
같은 SET 경로로 채운다. Tdoc 목록이 번호를 주지 않은 자리에 새 값을 넣는 것이라 시트와 파일 이름 두 출처가
모두 그 번호를 적어야 한다. 채우지 못한 null 노드는 사유별로 센다(`Phase-4 기록 없음` = WG 단계에서 TSG 팩에
오르지 않은 CR 처럼 Phase-4 가 번호를 갖지 않는 노드).

충돌 행은 어느 쪽도 쓰지 않고(대상도 점유 노드도 그대로 둔다) 사유 코드를 붙여 보고한다(`conflict_reason`).
`same_meeting_double_use`(시트가 확인한 번호를 같은 회의의 다른 CR 이 이미 쓴다)는 시트 측 결함 후보로 보고서의
`sheet_defect_candidates` 에 따로 둔다. 시트에 쌍이 없어 채우지 못한 null(`unpaired_null`)도 채우지 않고 원인
코드(`unpaired_cause`)별로 센다.

새 속성은 만들지 않는다. 바꾸거나 채운 노드의 원래 값은 보고 파일(`logs/tsg/RAN/formal/RAN{N}/phase-4/` 아래)에 남긴다.
Phase-1 을 다시 적재하면 `crNumber` 가 Tdoc 목록 값으로 돌아가므로 Phase-4 적재를 다시 돌려야 맞춰진다.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import cr_form
import tsg_cr_decision

REPORT_NAME = "crnumber_sheet_reconcile.json"

_REV_TAIL = re.compile(r"(?i)r\d+$")
_CR_PREFIX = re.compile(r"(?i)^CR")


def cr_digits(value) -> str:
    """견줄 번호: `CR` 머리 · 개정 꼬리 · 앞 0 을 뗀 값. 빈 값이면 빈 문자열."""
    text = _CR_PREFIX.sub("", str(value or "").strip())
    return _REV_TAIL.sub("", text).lstrip("0")


def load_number_records(path: Path) -> list[dict]:
    """Phase-4 파서 산출(`cr_documents.json`)에서 이 자리가 쓰는 칸만 읽는다. 목록 키는 `documents` 나 `cr_documents`."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = data.get("documents", data.get("cr_documents")) if isinstance(data, dict) else None
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        raise ValueError(f"{path.name}: documents 객체 목록이 필요합니다")
    keep = ("tdoc_number", "cr_pack_id", "cr_number", "spec_number", "source_path")
    return [{k: r.get(k) for k in keep} for r in rows]


def filename_number(source_path) -> str:
    """기록 문서의 파일 이름이 적은 CR 번호(`cr_digits` 꼴). 파일 이름에 번호가 없으면 빈 문자열."""
    m = cr_form._CR_NAME.search(Path(str(source_path or "")).name)
    return cr_digits(m.group(1)) if m else ""


_PACKS_BY_TDOC: dict[int, dict[str, set[str]]] = {}


def _sheet_packs_by_tdoc(key: int, pairs) -> dict[str, set[str]]:
    """CR 시트 쌍 표를 WG 문서 → 팩 집합으로 한 번만 뒤집는다(`key` 는 표의 id)."""
    if key not in _PACKS_BY_TDOC:
        index: dict[str, set[str]] = {}
        for pk, w in pairs:
            index.setdefault(w, set()).add(pk)
        _PACKS_BY_TDOC.clear()
        _PACKS_BY_TDOC[key] = index
    return _PACKS_BY_TDOC[key]


def unpaired_cause(tdoc, pack) -> str:
    """CR 시트에서 (팩 · WG 문서) 쌍의 CR 번호를 얻지 못한 원인 코드.

    tdoc_form_not_normalized   Tdoc 번호가 시트 정규화(`tsg_cr_decision._norm`) 꼴이 아니라 키를 만들 수 없다
    sheet_cr_blank             시트에 쌍은 있는데 CR 칸이 비었다
    sheet_no_identity_columns  시트에 쌍은 있는데 그 시트에 Spec · CR · REL 칸이 없다
    tdoc_under_other_pack      그 Tdoc 이 시트에서 다른 팩 아래에 있다
    tdoc_not_in_pack_rows      팩은 CR 시트에 있는데 그 Tdoc 행이 없다
    pack_only_in_tdoc_sheet    팩이 TDoc 시트에만 있고 CR 시트에는 없다
    pack_not_in_any_list       팩이 어느 시트에도 없다(그 회의 목록을 받지 못한 경우 포함)
    """
    t, pk = tsg_cr_decision._norm(tdoc), tsg_cr_decision._norm(pack)
    if not t:
        return "tdoc_form_not_normalized"
    pairs, packs, plenary = tsg_cr_decision.decisions()
    if (pk, t) in pairs:
        return "sheet_cr_blank" if tsg_cr_decision.identity(t, pk) is not None else "sheet_no_identity_columns"
    if _sheet_packs_by_tdoc(id(pairs), pairs).get(t, set()) - {pk}:
        return "tdoc_under_other_pack"
    if pk in packs:
        return "tdoc_not_in_pack_rows"
    return "pack_only_in_tdoc_sheet" if pk in plenary else "pack_not_in_any_list"


def verified_numbers(records: list[dict], reasons: dict[str, str] | None = None,
                     causes: dict[str, str] | None = None) -> tuple[dict[str, dict], Counter]:
    """tdocNumber → {number: 시트 CR 칸 값, spec: 기록 Spec, name: 파일 이름 판정}. 기록 번호가 시트와 같은 것만 담는다.

    `name` 은 그 Tdoc 의 받은 기록 모두의 파일 이름 번호가 시트 번호와 같으면 "같음", 번호가 없는 이름이 있으면
    "없음", 다른 번호가 있으면 "다름" 이다(null 채움만 이 판정을 쓴다).
    한 Tdoc 의 기록이 둘 이상인데 확인된 번호가 갈리면 그 Tdoc 은 빼고 센다.
    `reasons` 를 주면 담지 못한 Tdoc 마다 첫 사유를 적는다. `causes` 를 주면 사유가 "시트에 쌍 없음" 인 Tdoc 의
    원인 코드(`unpaired_cause`)를 적는다.
    """
    out: dict[str, dict] = {}
    split: set[str] = set()
    skipped = Counter()
    why: dict[str, str] = {}
    for r in records:
        tdoc, pack = r.get("tdoc_number"), r.get("cr_pack_id")
        if not tdoc:
            continue
        if not pack:
            skipped["팩 없음"] += 1
            why.setdefault(tdoc, "팩 없음")
            continue
        reg = tsg_cr_decision.identity(tdoc, pack)
        if reg is None or not reg["cr"]:
            skipped["시트에 쌍 없음"] += 1
            if why.setdefault(tdoc, "시트에 쌍 없음") == "시트에 쌍 없음" and causes is not None:
                causes.setdefault(tdoc, unpaired_cause(tdoc, pack))
            continue
        if not cr_digits(r.get("cr_number")) or cr_digits(r.get("cr_number")) != cr_digits(reg["cr"]):
            skipped["기록 번호가 시트와 다름"] += 1
            why.setdefault(tdoc, "기록 번호가 시트와 다름")
            continue
        fname = filename_number(r.get("source_path"))
        name = "같음" if fname == cr_digits(reg["cr"]) else ("없음" if not fname else "다름")
        entry = {"number": reg["cr"], "spec": r.get("spec_number") or "", "name": name}
        old = out.get(tdoc)
        if old is not None and cr_digits(old["number"]) != cr_digits(entry["number"]):
            split.add(tdoc)
        if old is not None and old["name"] != name:
            old["name"] = "다름" if "다름" in (old["name"], name) else "없음"
        out.setdefault(tdoc, entry)
    for tdoc in split:
        del out[tdoc]
        why[tdoc] = "확인 번호가 갈린 Tdoc"
    skipped["확인 번호가 갈린 Tdoc"] = len(split)
    if reasons is not None:
        reasons.update({t: w for t, w in why.items() if t not in out})
    if causes is not None:
        for t in [t for t in causes if t in out or why.get(t) != "시트에 쌍 없음"]:
            del causes[t]
    return out, skipped


_KG_QUERY = """
MATCH (n:CR) WHERE n.tdocNumber IS NOT NULL
OPTIONAL MATCH (n)-[:MODIFIES]->(sp:Spec)
WITH n, collect(DISTINCT sp.specNumber) AS s2
OPTIONAL MATCH (n)-[:PRESENTED_AT]->(mt:Meeting)
RETURN elementId(n) AS eid, n.tdocNumber AS tdoc, n.crNumber AS cr, n.specNumber AS s1, s2,
       n.type AS type, collect(DISTINCT elementId(mt)) AS meetings
"""

# 충돌 사유 코드. 앞에서부터 처음 맞는 것을 붙인다.
CONFLICT_REASONS = (
    "proposal_collision",        # 사슬 밖 상대가 모두 이번에 같은 번호를 제안받은 대상이고, 그 번호를 이미 쓰는 노드는 없다
    "target_other_type",         # 대상의 Phase-1 type 이 "other"(Tdoc 목록이 CR 로 분류하지 않은 문서)
    "target_no_phase1_type",     # 대상에 Phase-1 type 이 없다(Tdoc 목록 행 없이 만들어진 노드)
    "same_meeting_double_use",   # 대상과 같은 회의의 다른 CR 이 그 번호를 이미 쓴다
    "occupant_outside_chain",    # 그 밖: 다른 회의(또는 회의 모름)의 사슬 밖 노드가 그 번호를 쓴다
)


def conflict_reason(target: dict, occupants: list[dict]) -> str:
    """충돌 행 하나의 사유 코드(`CONFLICT_REASONS`). `occupants` 는 사슬 밖에서 그 번호를 이미 쓰는 노드들."""
    if not occupants:
        return "proposal_collision"
    if target.get("type") == "other":
        return "target_other_type"
    if target.get("type") is None:
        return "target_no_phase1_type"
    mine = set(target.get("meetings") or [])
    if any(mine & set(o.get("meetings") or []) for o in occupants):
        return "same_meeting_double_use"
    return "occupant_outside_chain"


_CHAIN_QUERY = """
MATCH (a:Tdoc)-[:REVISED_TO|IS_REVISION_OF]->(b:Tdoc)
WHERE a.tdocNumber IS NOT NULL AND b.tdocNumber IS NOT NULL AND a.tdocNumber <> b.tdocNumber
RETURN DISTINCT a.tdocNumber AS a, b.tdocNumber AS b
"""


def revision_chains(session) -> dict[str, str]:
    """tdocNumber → 그 Tdoc 이 든 개정 사슬의 대표 tdocNumber. 사슬에 들지 않은 Tdoc 은 담지 않는다."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in session.run(_CHAIN_QUERY):
        ra, rb = find(e["a"]), find(e["b"])
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    return {t: find(t) for t in list(parent)}


def plan(session, verified: dict[str, dict], reasons: dict[str, str] | None = None) -> dict:
    """그래프를 읽어 바꿀 노드 · 채울 노드 · 충돌 · 채우지 못한 null 을 가른다. 쓰지 않는다."""
    nodes = session.run(_KG_QUERY).data()
    chain = revision_chains(session)
    same_chain = lambda a, b: a in chain and chain.get(a) == chain.get(b)  # noqa: E731
    by_tdoc: dict[str, list[dict]] = {}
    users: dict[tuple[str, str], set[str]] = {}
    numbered: dict[str, list[dict]] = {}
    for n in nodes:
        if n["cr"] is not None:
            numbered.setdefault(n["tdoc"], []).append(n)
        n["specs"] = sorted({s for s in [n["s1"], *n["s2"]] if s})
        by_tdoc.setdefault(n["tdoc"], []).append(n)
        if n["cr"] is not None:
            for sp in n["specs"]:
                users.setdefault((sp, cr_digits(n["cr"])), set()).add(n["tdoc"])
    proposals, null_left = [], []
    same = absent = 0
    for tdoc, v in sorted(verified.items()):
        targets = by_tdoc.get(tdoc)
        if not targets:
            absent += 1
            continue
        want = cr_digits(v["number"])
        for n in targets:
            if n["cr"] is None and v["name"] != "같음":
                reason = "파일 이름에 CR 번호 없음" if v["name"] == "없음" else "파일 이름 번호가 시트와 다름"
                null_left.append({"tdoc": tdoc, "sheet": v["number"], "reason": reason})
                continue
            if n["cr"] is not None and cr_digits(n["cr"]) == want:
                same += 1
                continue
            specs = set(n["specs"]) | ({v["spec"]} if v["spec"] else set())
            proposals.append({"tdoc": tdoc, "eid": n["eid"], "before": n["cr"], "after": v["number"],
                              "specs": sorted(specs), "_want": want})
    proposers: dict[tuple[str, str], set[str]] = {}
    for p in proposals:
        for sp in p["specs"]:
            proposers.setdefault((sp, p["_want"]), set()).add(p["tdoc"])
    change, fill, conflict = [], [], []
    chain_skipped = 0
    for p in proposals:
        tdoc, want = p.pop("tdoc"), p.pop("_want")
        p = {"tdoc": tdoc, **p}
        occupied = set().union(*(users.get((sp, want), set()) for sp in p["specs"])) - {tdoc}
        rivals = set().union(*(proposers.get((sp, want), set()) for sp in p["specs"])) - {tdoc}
        in_chain = {o for o in occupied | rivals if same_chain(tdoc, o)}
        chain_skipped += len(in_chain)
        others = sorted((occupied | rivals) - in_chain)
        if in_chain:
            p["chain_tdocs"] = sorted(in_chain)
        if others:
            p["other_tdocs"] = others
            occ = sorted(occupied - in_chain)
            target = next(n for n in by_tdoc[tdoc] if n["eid"] == p["eid"])
            p["reason"] = conflict_reason(target, [n for o in occ for n in numbered.get(o, [])])
            p["other_sheet_verified"] = sum(o in verified for o in others)
            conflict.append(p)
            if p["before"] is None:
                null_left.append({"tdoc": tdoc, "sheet": p["after"], "reason": "충돌"})
        else:
            (fill if p["before"] is None else change).append(p)
    seen_null = {r["tdoc"] for r in null_left} | {p["tdoc"] for p in fill}
    for n in nodes:
        if n["cr"] is not None or n["tdoc"] in seen_null:
            continue
        if n["tdoc"] in verified:
            continue
        reason = (reasons or {}).get(n["tdoc"], "Phase-4 기록 없음")
        null_left.append({"tdoc": n["tdoc"], "reason": reason})
    return {"change": change, "fill": fill, "conflict": conflict, "null": null_left, "same": same, "absent": absent,
            "chain_skipped": chain_skipped}


def reconcile_cr_numbers(session, records: list[dict], dry_run: bool, report_path: Path | None = None,
                         run=None, fill_null: bool = False) -> dict[str, int]:
    """시트가 확인한 번호로 `crNumber` 를 맞추거나 채운다. `report_path` 가 있으면 바꾼 노드 · 채운 노드 · 충돌 ·
    채우지 못한 null 을 그 파일에 쓴다.

    `run` 은 쓰기 질의를 실행할 함수다(적재기의 트랜잭션 재시도 래퍼). 없으면 `session.run`.
    `fill_null` 이 거짓이면 null 채움은 세기만 하고 쓰지 않는다. 채움은 실제 적재 승인을 받은 실행에서만 켠다.
    충돌 행은 `fill_null` 과 무관하게 쓰지 않는다.
    """
    reasons: dict[str, str] = {}
    causes: dict[str, str] = {}
    verified, skipped = verified_numbers(records, reasons, causes)
    p = plan(session, verified, reasons)
    unpaired = [r for r in p["null"] if r["reason"] == "시트에 쌍 없음"]
    for r in unpaired:
        r["cause"] = causes.get(r["tdoc"], "unknown")
    defects = [c for c in p["conflict"] if c["reason"] == "same_meeting_double_use"]
    conflict_reasons = Counter(c["reason"] for c in p["conflict"])
    unpaired_causes = Counter(r["cause"] for r in unpaired)
    write_fill = p["fill"] if fill_null else []
    rows = [{"eid": r["eid"], "before": r["before"], "after": r["after"]} for r in p["change"] + write_fill]
    if not dry_run and rows:
        (run or session.run)(
            "UNWIND $rows AS r MATCH (n) WHERE elementId(n) = r.eid "
            "AND (n.crNumber = r.before OR (r.before IS NULL AND n.crNumber IS NULL)) "
            "SET n.crNumber = r.after",
            rows=rows,
        )
    null_reasons = Counter(r["reason"] for r in p["null"])
    counts = {
        "확인 번호 Tdoc": len(verified),
        "바꿈" if not dry_run else "바꿀 것": len(p["change"]),
        "null 채움" if not dry_run and fill_null else "null 채울 것": len(p["fill"]),
        "충돌(두지 않음)": len(p["conflict"]),
        **{f"충돌 사유: {k}": conflict_reasons[k] for k in CONFLICT_REASONS if conflict_reasons[k]},
        "시트 결함 후보(같은 회의 이중 사용)": len(defects),
        "충돌에서 뺀 개정 사슬 점유": p["chain_skipped"],
        "crNumber null 남음": len(p["null"]),
        **{f"null 남음: {k}": v for k, v in sorted(null_reasons.items())},
        "unpaired null": len(unpaired),
        **{f"unpaired 원인: {k}": v for k, v in sorted(unpaired_causes.items())},
        "이미 같음": p["same"],
        "그래프에 없음": p["absent"],
        **{f"건너뜀: {k}": v for k, v in sorted(skipped.items()) if v},
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        strip = lambda rows: [{k: v for k, v in r.items() if k != "eid"} for r in rows]  # noqa: E731
        report_path.write_text(json.dumps({
            "dry_run": dry_run,
            "fill_null": fill_null,
            "counts": counts,
            "changed": strip(p["change"]),
            "filled": strip(p["fill"]),
            "conflicts": strip(p["conflict"]),
            "conflict_reasons": {k: conflict_reasons[k] for k in CONFLICT_REASONS},
            "sheet_defect_candidates": strip(defects),
            "unpaired_null": {"count": len(unpaired), "causes": dict(sorted(unpaired_causes.items()))},
            "null_crnumber": p["null"],
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return counts
