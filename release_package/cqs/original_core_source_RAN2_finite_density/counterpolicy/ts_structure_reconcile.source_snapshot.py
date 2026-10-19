"""Phase-3 TS 구조 적재기가 소유한 KG 부분을 입력과 같게 맞춘다.

적재기는 MERGE 만 하므로, 재파싱으로 사라진 절·표·그림과 거짓으로 해소됐던 참조 간선이
그래프에 그대로 남는다. 이 모듈은 적재 직전에 불러, 입력이 다루는 spec 의 구조 간선을 걷고
입력에 없는 노드를 지운다. 이어지는 적재가 입력대로 다시 세운다.

- 범위: 입력에 나오는 specNumber 의 release-키 Spec 에 매달린 Section, 그리고 ID 가 그 spec 의
  것인 Section·TSTable·TSFigure (`{spec}-Rel-NN-…`). 추상 허브 Spec 과 그 문서 간선은 건드리지 않는다.
- 소유 간선 타입은 적재기마다 다르므로 부르는 쪽이 넘긴다(자기가 MERGE 하는 타입만).
- 입력에 없는 Section 에 다른 생산자의 간선(Tdoc/CR→Section, Email ANCHORS, ConformanceTest
  definedInSection 등)이 붙어 있으면 그 노드는 그 생산자의 것이기도 하므로 지우지 않고 센다.
  소유 간선은 걷혔으므로 구조에서는 빠진다. 그 생산자를 다시 돌리면 간선이 옮겨 가고,
  이 적재기를 다시 돌리면 그때 지워진다.

LLM 호출: 없음
"""

from __future__ import annotations

NODE_LABELS = ("Section", "TSTable", "TSFigure")
_ID_KEY = {"Section": "sectionId", "TSTable": "tableId", "TSFigure": "figureId"}


def _spec_of(node_id: str) -> str:
    return node_id.split("-Rel-", 1)[0] if "-Rel-" in node_id else ""


def _batched(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def reconcile_structure(session, specs: set[str], desired: dict[str, set[str]],
                        owned_rel_types: list[str], dry_run: bool,
                        batch_size: int = 500) -> tuple[dict[str, int], dict[str, list[str]]]:
    """specs = 입력의 specNumber 집합, desired = {라벨: 입력의 ID 집합}.

    (지운 — dry_run 이면 지울 — 수, 남긴 노드의 ID 목록)을 돌려준다.
    """
    out: dict[str, int] = {}
    kept_ids: dict[str, list[str]] = {}
    scoped: dict[str, set[str]] = {}
    for label in NODE_LABELS:
        key = _ID_KEY[label]
        ids = {r["id"] for r in session.run(f"MATCH (n:{label}) RETURN n.{key} AS id")
               if r["id"] and _spec_of(r["id"]) in specs}
        if label == "Section":
            ids |= {r["id"] for r in session.run(
                "MATCH (s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) "
                "WHERE sp.specRelease IS NOT NULL AND sp.specNumber IN $specs "
                "RETURN s.sectionId AS id", specs=sorted(specs))}
        scoped[label] = ids

    # 소유 간선: 범위 안 노드에 닿은 것은 방향과 상대를 가리지 않고 전부 걷는다.
    # 양 끝이 모두 범위 안인 간선은 두 노드에서 다 보이므로 ID 로 모아 한 번씩만 센다.
    rel_ids: set[str] = set()
    for label in NODE_LABELS:
        key = _ID_KEY[label]
        for batch in _batched(sorted(scoped[label]), batch_size):
            rel_ids |= {r["rid"] for r in session.run(
                f"UNWIND $ids AS nid MATCH (n:{label} {{{key}: nid}})-[r]-() "
                "WHERE type(r) IN $owned RETURN DISTINCT elementId(r) AS rid",
                ids=batch, owned=owned_rel_types)}
    if not dry_run:
        for batch in _batched(sorted(rel_ids), batch_size):
            session.run("UNWIND $ids AS rid MATCH ()-[r]->() WHERE elementId(r) = rid DELETE r",
                        ids=batch)
    out["소유 구조 간선 (걷고 다시 세움)"] = len(rel_ids)

    # 입력에 없는 노드.
    for label in NODE_LABELS:
        key = _ID_KEY[label]
        stale = sorted(scoped[label] - desired.get(label, set()))
        gone, kept = [], []
        for batch in _batched(stale, batch_size):
            for r in session.run(
                    f"UNWIND $ids AS nid MATCH (n:{label} {{{key}: nid}}) "
                    "OPTIONAL MATCH (n)-[x]-() WHERE NOT type(x) IN $owned "
                    "RETURN nid AS id, count(x) AS foreign",
                    ids=batch, owned=owned_rel_types):
                (kept if r["foreign"] else gone).append(r["id"])
        if gone and not dry_run:
            for batch in _batched(gone, batch_size):
                session.run(f"UNWIND $ids AS nid MATCH (n:{label} {{{key}: nid}}) DETACH DELETE n",
                            ids=batch)
        out[f"{label} (입력 밖)"] = len(gone)
        out[f"{label} kept (다른 생산자 간선)"] = len(kept)
        if kept:
            kept_ids[label] = kept
    return out, kept_ids
