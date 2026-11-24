"""Phase-1 노드가 없는 CR 에 CR 서식 값으로 제목 · MODIFIES · RELATED_TO 를 채운다.

Phase-4 적재기는 Phase-1 Tdoc List 가 다루지 않는 CR 을 `_createdBy='phase-4-backfill'` 노드로
만든다(`load_cr_extensions` 의 MERGE). Phase-1 노드라면 Tdoc List 의 Title · Spec · Related WIs
칸이 `title` 속성과 `MODIFIES`(→ Spec) · `RELATED_TO`(→ WorkItem) 간선이 되는데, backfill 노드에는
그 칸을 읽는 자리가 없어 제목이 비고 두 간선이 없다. 그러면 spec · 작업 항목으로 CR 을 찾는 질의가
그 CR 을 말없이 건너뛴다. 같은 값은 CR 문서 자신의 서식(`cr_form.form_fields` 의 title · work_item,
머리의 spec 번호)에 있고 Phase-4 파서가 `cr_documents.json` 에 이미 적는다. 여기서 그 값을 쓴다.

쓰는 자리는 backfill 노드뿐이다. Phase-1 이 만든 노드(`:Tdoc`)는 건드리지 않는다. 그 노드의 값은
Tdoc List 가 정본이다. 제목은 비어 있거나 앞선 적재가 이 자리에서 채운 것(`titleSource='cr-form'`)일
때만 쓴다. 간선은 Phase-1 과 같은 대상 키(`Spec {id}` · `WorkItem {id}`)로 이미 있는 노드에만 달고,
대상 노드가 없으면 만들지 않고 센다. 이 자리가 단 간선에는 `_createdBy='phase-4-backfill'` 를 붙여
다른 생성 코드의 간선과 가른다. 흡수(`absorb_backfill_twins`)는 그 간선을 짝으로 옮기지 않고 버린다(짝인
Phase-1 노드에는 Tdoc List 가 단 같은 뜻의 간선이 있다). 정합화는 입력에 없는 것을 걷는다.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

BACKFILL = "phase-4-backfill"
TITLE_SOURCE = "cr-form"
FORM_REL_TYPES = ("MODIFIES", "RELATED_TO")

# Phase-1(`phase-1/jsonld/03_tdoc_instances.py`)의 spec 번호 패턴과 참조 id 규칙이다.
_SPEC_NUM_RE = re.compile(r"^\d{2}\.\d{3}(-\d{1,2}){0,2}$")
_WI_SLUG_RE = re.compile(r"[^a-zA-Z0-9_-]")

BATCH_SIZE = 500


def spec_id(spec_number: str) -> str:
    return f"tdoc:spec/{spec_number.replace('.', '_')}"


def work_item_id(code: str) -> str:
    return f"tdoc:workitem/{_WI_SLUG_RE.sub('_', code)}"


def _text(value, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{label}: 문자열이 필요합니다")
    return value.strip()


def load_form_records(path: Path) -> list[dict]:
    """Phase-4 파서 산출(`cr_documents.json`)에서 이 자리가 쓰는 칸만 읽는다.

    목록의 키는 WG 마다 `documents` 나 `cr_documents` 다.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = data.get("documents", data.get("cr_documents")) if isinstance(data, dict) else None
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        raise ValueError(f"{path.name}: documents 객체 목록이 필요합니다")
    keep = ("tdoc_number", "title", "spec_number", "work_item")
    return [{k: r.get(k) for k in keep} for r in rows]


def form_values(records: list[dict], normalize_spec=None) -> tuple[dict[str, dict], Counter]:
    """tdocNumber → {title, specs(Spec id), wis(WorkItem id)}. 칸별로 기록끼리 값이 갈리면 그 칸은 비우고 센다."""
    seen: dict[str, list[tuple]] = {}
    skipped = Counter()
    for r in records:
        tdoc = _text(r.get("tdoc_number"), "tdoc_number")
        if not tdoc:
            continue
        title = _text(r.get("title"), "title")
        raw_spec = _text(r.get("spec_number"), "spec_number")
        sn = normalize_spec(raw_spec) if normalize_spec and raw_spec else raw_spec
        specs = ()
        if sn:
            if _SPEC_NUM_RE.match(sn):
                specs = (spec_id(sn),)
            else:
                skipped["spec 번호 형식 밖"] += 1
        # Related WIs 칸과 같이 쉼표로 가른다. 영숫자가 없는 토큰은 '없음'을 적은 것이라 신원이 아니다.
        codes = [c.strip() for c in _text(r.get("work_item"), "work_item").split(",")]
        wis = tuple(dict.fromkeys(work_item_id(c) for c in codes if any(ch.isalnum() for ch in c)))
        seen.setdefault(tdoc, []).append((title, specs, wis))
    out = {}
    for tdoc, rows in seen.items():
        value = {}
        for i, key in enumerate(("title", "specs", "wis")):
            distinct = {row[i] for row in rows if row[i]}
            if len(distinct) > 1:
                skipped[f"{key} 기록 충돌"] += 1
            value[key] = next(iter(distinct)) if len(distinct) == 1 else ("" if key == "title" else ())
        out[tdoc] = {"title": value["title"], "specs": list(value["specs"]), "wis": list(value["wis"])}
    return out, skipped


def _existing(session, label: str, ids: set[str]) -> set[str]:
    return {
        r["id"] for r in session.run(
            f"UNWIND $ids AS id MATCH (n:{label} {{id: id}}) RETURN DISTINCT id AS id", ids=sorted(ids))
    }


def fill_backfill_form(session, records: list[dict], input_tdocs: set[str], dry_run: bool,
                       run=None, normalize_spec=None) -> dict[str, int]:
    """입력 CR 가운데 Phase-1 노드가 없는 것(적재 뒤 backfill 노드로 서는 것)을 채운다. 채운(또는 채울) 수를 돌려준다.

    `run(query, **params)` 은 한 행을 돌려주는 쓰기 실행기다. 주지 않으면 `session.run(...).single()` 이다.
    dry-run 은 읽기만 한다.
    """
    if run is None:
        run = lambda q, **kw: session.run(q, **kw).single()  # noqa: E731
    values, skipped = form_values(records, normalize_spec)
    wanted = sorted(t for t in input_tdocs if t in values)
    has_tdoc = {
        r["t"] for r in session.run(
            "UNWIND $tdocs AS t MATCH (:Tdoc {tdocNumber: t}) RETURN DISTINCT t AS t", tdocs=wanted)
    }
    targets = [t for t in wanted if t not in has_tdoc]
    no_record = sum(1 for t in input_tdocs if t not in values and t not in has_tdoc)
    spec_ok = _existing(session, "Spec", {s for t in targets for s in values[t]["specs"]})
    wi_ok = _existing(session, "WorkItem", {w for t in targets for w in values[t]["wis"]})

    titles = [{"t": t, "title": values[t]["title"]} for t in targets if values[t]["title"]]
    mods = [{"t": t, "id": s} for t in targets for s in values[t]["specs"] if s in spec_ok]
    rels = [{"t": t, "id": w} for t in targets for w in values[t]["wis"] if w in wi_ok]
    out = {
        "backfill CR (Phase-1 노드 없음)": len(targets),
        "  CR 서식 기록 없음": no_record,
        "  제목 채움": len(titles),
        "  제목 칸 빔": sum(1 for t in targets if not values[t]["title"]),
        "  MODIFIES 간선": len(mods),
        "  MODIFIES 대상 Spec 노드 없음": sum(1 for t in targets for s in values[t]["specs"] if s not in spec_ok),
        "  spec 번호 칸 빔": sum(1 for t in targets if not values[t]["specs"]),
        "  RELATED_TO 간선": len(rels),
        "  RELATED_TO 대상 WorkItem 노드 없음": sum(1 for t in targets for w in values[t]["wis"] if w not in wi_ok),
        "  작업 항목 칸 빔": sum(1 for t in targets if not values[t]["wis"]),
    }
    for k, v in sorted(skipped.items()):
        out[f"  기록 건너뜀 ({k})"] = v
    if dry_run:
        return out

    node = f"MATCH (c:CR {{tdocNumber: x.t}}) WHERE c._createdBy = '{BACKFILL}' AND NOT c:Tdoc "
    done = Counter()
    for i in range(0, len(titles), BATCH_SIZE):
        done["title"] += run(
            "UNWIND $batch AS x " + node
            + f"AND (c.title IS NULL OR c.title = '' OR c.titleSource = '{TITLE_SOURCE}') "
            f"SET c.title = x.title, c.titleSource = '{TITLE_SOURCE}' RETURN count(c) AS cnt",
            batch=titles[i:i + BATCH_SIZE])["cnt"]
    for rel_type, label, pairs in (("MODIFIES", "Spec", mods), ("RELATED_TO", "WorkItem", rels)):
        for i in range(0, len(pairs), BATCH_SIZE):
            done[rel_type] += run(
                "UNWIND $batch AS x " + node + f"MATCH (n:{label} {{id: x.id}}) "
                f"WHERE NOT EXISTS {{ MATCH (c)-[:{rel_type}]->(n) }} "
                f"CREATE (c)-[:{rel_type} {{_createdBy: '{BACKFILL}'}}]->(n) RETURN count(*) AS cnt",
                batch=pairs[i:i + BATCH_SIZE])["cnt"]
    out["  (쓰기) 제목"] = done["title"]
    out["  (쓰기) 새 MODIFIES"] = done["MODIFIES"]
    out["  (쓰기) 새 RELATED_TO"] = done["RELATED_TO"]
    return out


def reconcile_backfill_form(session, records: list[dict], input_tdocs: set[str], dry_run: bool,
                            normalize_spec=None) -> dict[str, int]:
    """이 자리가 채운 제목 · 간선 가운데 입력이 요구하지 않는 것을 걷는다. 걷은(또는 걷을) 수를 돌려준다.

    입력 밖 CR 의 backfill 노드가 다른 생성 코드의 간선 때문에 남을 때, 이 자리의 값만 걷히지 않으면
    옛 입력의 제목 · spec · 작업 항목이 그 노드에 남는다.
    """
    values, _ = form_values(records, normalize_spec)
    want = {(t, "MODIFIES", s) for t in input_tdocs for s in values.get(t, {}).get("specs", [])}
    want |= {(t, "RELATED_TO", w) for t in input_tdocs for w in values.get(t, {}).get("wis", [])}
    want_title = {(t, values[t]["title"]) for t in input_tdocs if t in values and values[t]["title"]}
    rel_ids = [
        r["rid"] for r in session.run(
            f"MATCH (c:CR)-[r:{'|'.join(FORM_REL_TYPES)} {{_createdBy: '{BACKFILL}'}}]->(n) "
            "RETURN elementId(r) AS rid, c.tdocNumber AS t, type(r) AS ty, n.id AS id, c:Tdoc AS tdoc")
        if r["tdoc"] or (r["t"], r["ty"], r["id"]) not in want
    ]
    node_ids = [
        r["nid"] for r in session.run(
            f"MATCH (c:CR {{titleSource: '{TITLE_SOURCE}'}}) WHERE NOT c:Tdoc "
            "RETURN elementId(c) AS nid, c.tdocNumber AS t, c.title AS title")
        if (r["t"], r["title"]) not in want_title
    ]
    if not dry_run:
        for i in range(0, len(rel_ids), BATCH_SIZE):
            session.run("UNWIND $ids AS rid MATCH ()-[r]->() WHERE elementId(r) = rid DELETE r",
                        ids=rel_ids[i:i + BATCH_SIZE])
        for i in range(0, len(node_ids), BATCH_SIZE):
            session.run("UNWIND $ids AS nid MATCH (c) WHERE elementId(c) = nid REMOVE c.title, c.titleSource",
                        ids=node_ids[i:i + BATCH_SIZE])
    return {"CR 서식 간선 (입력 밖)": len(rel_ids), "CR 서식 제목 (입력 밖)": len(node_ids)}
