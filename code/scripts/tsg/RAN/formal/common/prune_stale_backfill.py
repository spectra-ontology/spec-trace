#!/usr/bin/env python3
"""근거를 잃은 phase-6-backfill Tdoc 노드를 정규 번호 노드로 접어 넣고 지운다.

무엇이 근거를 잃은 노드인지와 왜 생기는지는 `scripts/common/common/backfill_provenance.py`
머리말에 있다. 이 도구는 그 판정이 `prune` 인 노드만 처리한다.

노드 하나마다 한 트랜잭션으로:
  1. 들어오는 ANCHORS 를 정규 번호 노드로 옮긴다. 키는 적재기
     (`scripts/tsg/RAN/email/RAN2/phase-3/neo4j/01_generate_hard_anchors.py`)와 같은
     (context_chunk_id, entity_URI) 이고, entity_URI 는 정규 번호로 바꾼다. 같은 키의 앵커가
     정규 번호 노드에 이미 있으면 새로 만들지 않는다(병합). 새로 만든 앵커는 원래 속성을 모두
     옮겨 받고, 원래의 entity_URI 를 `entity_URI_as_anchored` 에 남긴다.
  2. 노드를 DETACH DELETE 한다. 남는 관계는 PRESENTED_AT 뿐이고, 판정이 정규 번호 노드가 그
     회의에 모두 걸려 있음을 이미 확인했다.

지우기 전에 노드의 모든 속성과 관계(양 끝 · 속성 포함)를
`logs/tsg/RAN/formal/<WG>/phase-6/stale_backfill_prune.json` 에 덧적는다. 되돌릴 근거가
그 기록 하나라서 기록을 먼저 쓰고, 쓰기에 실패하면 지우지 않는다.

주의: 이메일 트랙의 앵커 통계(phase-4 SCI 통계 등)는 옛 entity_URI 로 집계되어 있다. 이
도구는 이메일 산출을 다시 만들지 않으므로, 옮기거나 키를 바꾼 앵커의 통계는 이메일 트랙을
다시 돌릴 때까지 옛 이름으로 남는다.

같은 결함의 형제가 하나 더 있다. 노드는 정규 번호로 서 있는데 그 노드에 걸린 ANCHORS 의 키
`entity_URI` 만 옛 이름(뒤 공백 등)인 경우다. 둘째 단계는 그런 앵커의 키를 대상의 `tdocNumber`
로 바꾸고 옛 키를 `entity_URI_as_anchored` 에 남긴다. 옛 키를 번호 규칙에 넣어 대상 번호가 되고
정규 키의 짝이 아직 없는 앵커만 바꾼다(`backfill_provenance.drifted_anchor_keys`). 바꾸기 전에
앵커마다 옛 키를 `logs/tsg/RAN/formal/<WG>/phase-6/anchor_key_rekey.json` 에 덧적는다.
같은 단계가 Meeting 대상 앵커도 다룬다. 회의 앵커의 키가 옛 Meeting.id(개최 형식 꼬리 `-e` 가
붙은 이름)로 남은 경우, 꼬리 하나를 걷으면 대상 id 가 되고 본문 회의 번호(`match_key`)가 대상
회의와 같으며 정규 키의 짝이 없는 앵커만 키를 `m.id` 로 바꾼다
(`backfill_provenance.drifted_meeting_anchor_keys`). 기록은 같은 파일에 덧적는다.

셋째 형제는 한 Tdoc 에서 같은 회의로 PRESENTED_AT 이 나란히 두 갈래 걸린 경우다
(`backfill_provenance.parallel_presented_at`). 셋째 단계는 하나만 남기고 나머지를 지운다. 지우는
관계의 속성과 두 끝을 `logs/tsg/RAN/formal/<WG>/phase-6/parallel_presented_at.json` 에 먼저 덧적는다.

넷째 단계는 값이 빈 문자열인 Tdoc 속성을 지운다(`backfill_provenance.empty_string_properties`).
값이 없으면 속성이 없는 것으로 두어, 질의를 쓰는 쪽이 빈 속성을 값으로 받지 않게 한다. 지우는
노드와 속성 이름을 `logs/tsg/RAN/formal/<WG>/phase-6/empty_string_properties.json` 에 먼저 덧적는다.
지운 값은 모두 빈 문자열이라, 되돌릴 때는 그 기록의 속성에 빈 문자열을 다시 넣는다.

기본은 dry-run 이다. 다시 돌리면 처리할 것이 없어 아무것도 하지 않는다.

사용:
    python3 scripts/tsg/RAN/formal/common/prune_stale_backfill.py --wg RAN2
    python3 ... --wg ALL --apply
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from neo4j import GraphDatabase

PROJECT_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
_SCRIPTS_COMMON = PROJECT_ROOT / "scripts" / "common"
if str(_SCRIPTS_COMMON) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_COMMON))
from common import axis, backfill_provenance, credentials  # noqa: E402
from document_decision_storage import durable_json  # noqa: E402

BOLT_PORTS = axis.bolt_ports(("RAN",))

Q_SNAPSHOT = """
MATCH (t) WHERE elementId(t) = $e
OPTIONAL MATCH (t)-[r]-(x)
RETURN properties(t) AS props, labels(t) AS labels,
       collect(CASE WHEN r IS NULL THEN NULL ELSE {
           type: type(r), direction: CASE WHEN startNode(r) = t THEN 'out' ELSE 'in' END,
           props: properties(r), other_element_id: elementId(x), other_labels: labels(x),
           other_key: coalesce(x.tdocNumber, x.meetingNumber, x.messageId, x.id, x.uri)} END) AS rels
"""

Q_ALREADY = """
MATCH (x)-[a:ANCHORS]->(t) WHERE elementId(t) = $e
MATCH (k) WHERE elementId(k) = $k
OPTIONAL MATCH (x)-[b:ANCHORS {context_chunk_id: a.context_chunk_id, entity_URI: $twin}]->(k)
RETURN count(a) AS anchors, count(b) AS already
"""

Q_MOVE = """
MATCH (x)-[a:ANCHORS]->(t) WHERE elementId(t) = $e
MATCH (k) WHERE elementId(k) = $k
MERGE (x)-[b:ANCHORS {context_chunk_id: a.context_chunk_id, entity_URI: $twin}]->(k)
ON CREATE SET b = properties(a), b.entity_URI = $twin, b.entity_URI_as_anchored = a.entity_URI
RETURN count(b) AS c
"""

Q_DELETE = "MATCH (t) WHERE elementId(t) = $e DETACH DELETE t RETURN count(*) AS c"

Q_REKEY = """
MATCH ()-[a:ANCHORS]->(t:Tdoc) WHERE elementId(a) = $a AND a.entity_URI = $old
SET a.entity_URI_as_anchored = a.entity_URI, a.entity_URI = t.tdocNumber
RETURN count(a) AS c
"""

Q_REKEY_MEETING = """
MATCH ()-[a:ANCHORS]->(m:Meeting) WHERE elementId(a) = $a AND a.entity_URI = $old
SET a.entity_URI_as_anchored = a.entity_URI, a.entity_URI = m.id
RETURN count(a) AS c
"""

# 남길 관계가 그대로 있을 때만 지운다. 판정과 쓰기 사이에 남길 관계가 사라졌으면 아무것도 지우지 않는다.
Q_DROP_PARALLEL = """
MATCH ()-[k:PRESENTED_AT]->() WHERE elementId(k) = $keep
MATCH ()-[r:PRESENTED_AT]->() WHERE elementId(r) IN $ids
DELETE r
RETURN count(r) AS c
"""


def _plain(v):
    # neo4j 의 시간 값 등은 JSON 으로 바로 나가지 않는다. 되돌릴 때 읽을 수 있게 문자열로 적는다.
    if isinstance(v, dict):
        return {k: _plain(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_plain(x) for x in v]
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    return str(v)


def _record(wg: str, entries: list[dict], name: str) -> Path:
    path = axis.tree_path("logs", wg=wg, phase="phase-6") / name
    path.parent.mkdir(parents=True, exist_ok=True)
    runs = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    runs.append({"applied_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "tool": Path(__file__).resolve().relative_to(PROJECT_ROOT).as_posix(),
                 "entries": entries})
    durable_json(path, runs)
    return path


def _assert_prune_preimage(tx, entry):
    current = tx.run(Q_SNAPSHOT, e=entry['element_id']).single()
    if current is None:
        raise RuntimeError('Prune node disappeared after the retained preimage')
    def relations(rows):
        # Relationship enumeration and label order carry no graph semantics.
        normalized = []
        for row in _plain(rows):
            value = dict(row)
            value['other_labels'] = sorted(value['other_labels'])
            normalized.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
        return sorted(normalized)
    if (_plain(current['props']) != entry['props']
            or sorted(current['labels']) != sorted(entry['labels'])
            or relations(current['rels']) != relations(entry['relationships'])):
        raise RuntimeError('Prune node or incident relationship changed after the retained preimage')


def run_wg(wg: str, apply: bool) -> int:
    driver = GraphDatabase.driver(f"bolt://localhost:{BOLT_PORTS[wg]}",
                                  auth=credentials.neo4j_auth())
    try:
        with driver.session() as session:
            return max(_prune_nodes(session, wg, apply), _rekey_anchors(session, wg, apply),
                       _rekey_meeting_anchors(session, wg, apply),
                       _dedupe_presented_at(session, wg, apply),
                       _drop_empty_strings(session, wg, apply))
    finally:
        driver.close()


def _q_drop_empty(key: str) -> str:
    """빈 문자열인 속성 하나를 지우는 질의. 판정과 쓰기 사이에 값이 바뀐 노드는 건드리지 않는다."""
    if not backfill_provenance.SAFE_KEY.fullmatch(key):
        raise ValueError(f"Cypher 이름으로 넣을 수 없는 속성 이름: {key!r}")
    return (f"MATCH (t:Tdoc) WHERE elementId(t) IN $ids AND t.`{key}` = '' "
            f"REMOVE t.`{key}` RETURN count(t) AS c")


def _drop_empty_strings(session, wg: str, apply: bool) -> int:
    found = backfill_provenance.empty_string_properties(session)
    drop = [e for e in found if e["verdict"] == "drop"]
    keys = Counter(k for e in drop for k in e["keys"])
    print(f"[{wg}] 빈 문자열 속성을 든 Tdoc {len(found)} · 처리 {len(drop)} · "
          f"보류 {len(found) - len(drop)} · 속성별 {dict(sorted(keys.items()))}")
    for e in found:
        if e["verdict"] != "drop":
            print(f"  blocked {e['name']!r} {e['keys']} — {e['reason']}")
    if not drop:
        return 0
    if not apply:
        print("  (dry-run. 처리하려면 --apply)")
        return 0
    path = _record(wg, _plain(drop), "empty_string_properties.json")
    print(f"  되돌림 기록: {path.relative_to(PROJECT_ROOT)}")
    removed = Counter()
    for key in sorted(keys):
        ids = [e["element_id"] for e in drop if key in e["keys"]]
        removed[key] = session.execute_write(
            lambda t, key=key, ids=ids: t.run(_q_drop_empty(key), ids=ids).single()["c"])
    print(f"  지운 속성 {dict(sorted(removed.items()))}")
    left = [e for e in backfill_provenance.empty_string_properties(session) if e["verdict"] == "drop"]
    if removed != keys or left:
        print(f"  🔴 처리 뒤에도 남음: {len(left)} · 기대 {dict(keys)} · 실제 {dict(removed)}")
        return 1
    return 0


def _dedupe_presented_at(session, wg: str, apply: bool) -> int:
    groups = backfill_provenance.parallel_presented_at(session)
    fix = [g for g in groups if g["verdict"] == "prune"]
    print(f"[{wg}] 같은 회의로 나란한 PRESENTED_AT {len(groups)} · 처리 {len(fix)} · "
          f"보류 {len(groups) - len(fix)}")
    for g in groups:
        tail = f" — {g['reason']}" if g["reason"] else ""
        print(f"  {g['verdict']:7} {g['name']!r} @ {g['meeting']!r} 남김 {g['keep']['props']} · "
              f"지움 {[e['props'] for e in g['drop']]}{tail}")
    if not fix:
        return 0
    if not apply:
        print("  (dry-run. 처리하려면 --apply)")
        return 0
    path = _record(wg, _plain(fix), "parallel_presented_at.json")
    print(f"  되돌림 기록: {path.relative_to(PROJECT_ROOT)}")
    done = sum(session.execute_write(
        lambda t, g=g: t.run(Q_DROP_PARALLEL, ids=[e["element_id"] for e in g["drop"]],
                             keep=g["keep"]["element_id"]).single()["c"]) for g in fix)
    print(f"  관계 {done} 지움")
    left = [g for g in backfill_provenance.parallel_presented_at(session) if g["verdict"] == "prune"]
    if done != sum(len(g["drop"]) for g in fix) or left:
        print(f"  🔴 처리 뒤에도 남음: {len(left)}")
        return 1
    return 0


def _rekey_anchors(session, wg: str, apply: bool) -> int:
    drifted = backfill_provenance.drifted_anchor_keys(session)
    fix = [d for d in drifted if d["fixable"]]
    print(f"[{wg}] 옛 이름 앵커 키 {len(drifted)} · 처리 {len(fix)} · 보류 {len(drifted) - len(fix)}")
    for key, n in sorted({(d["key"], d["number"]) for d in drifted}, key=str):
        print(f"  {key!r} → {n!r}")
    if not fix:
        return 0
    if not apply:
        print("  (dry-run. 처리하려면 --apply)")
        return 0
    path = _record(wg, fix, "anchor_key_rekey.json")
    print(f"  되돌림 기록: {path.relative_to(PROJECT_ROOT)}")
    done = sum(session.execute_write(
        lambda t, d=d: t.run(Q_REKEY, a=d["element_id"], old=d["key"]).single()["c"]) for d in fix)
    print(f"  앵커 키 {done} 바꿈")
    left = [d for d in backfill_provenance.drifted_anchor_keys(session) if d["fixable"]]
    if done != len(fix) or left:
        print(f"  🔴 처리 뒤에도 남음: {len(left)}")
        return 1
    return 0


def _rekey_meeting_anchors(session, wg: str, apply: bool) -> int:
    drifted = backfill_provenance.drifted_meeting_anchor_keys(session)
    fix = [d for d in drifted if d["fixable"]]
    print(f"[{wg}] 옛 이름 회의 앵커 키 {len(drifted)} · 처리 {len(fix)} · "
          f"보류 {len(drifted) - len(fix)}")
    for (key, mid), n in sorted(Counter((d["key"], d["number"]) for d in drifted).items(), key=str):
        print(f"  {key!r} → {mid!r} ({n})")
    if not fix:
        return 0
    if not apply:
        print("  (dry-run. 처리하려면 --apply)")
        return 0
    path = _record(wg, fix, "anchor_key_rekey.json")
    print(f"  되돌림 기록: {path.relative_to(PROJECT_ROOT)}")
    done = sum(session.execute_write(
        lambda t, d=d: t.run(Q_REKEY_MEETING, a=d["element_id"], old=d["key"]).single()["c"])
        for d in fix)
    print(f"  회의 앵커 키 {done} 바꿈")
    left = [d for d in backfill_provenance.drifted_meeting_anchor_keys(session) if d["fixable"]]
    if done != len(fix) or left:
        print(f"  🔴 처리 뒤에도 남음: {len(left)}")
        return 1
    return 0


def _prune_nodes(session, wg: str, apply: bool) -> int:
    stale = backfill_provenance.stale_nodes(session, wg)
    prune = [s for s in stale if s["verdict"] == "prune"]
    print(f"[{wg}] 근거 잃은 backfill {len(stale)} · 처리 {len(prune)} · "
          f"보류 {len(stale) - len(prune)}")
    for s in stale:
        tail = f" — {s['reason']}" if s["reason"] else ""
        print(f"  {s['verdict']:7} {s['name']!r} → {s['twin']!r} {s['edges']} "
              f"{s['meetings']}{tail}")
    if not prune:
        return 0

    entries = []
    for s in prune:
        snap = session.run(Q_SNAPSHOT, e=s["element_id"]).single()
        already = (session.run(Q_ALREADY, e=s["element_id"], k=s["twin_element_id"],
                               twin=s["twin"]).single()
                   if s["twin_element_id"] else {"anchors": 0, "already": 0})
        entries.append({**{k: s[k] for k in ("element_id", "name", "twin",
                                             "twin_element_id", "meetings")},
                        "labels": snap["labels"], "props": _plain(snap["props"]),
                        "relationships": _plain(snap["rels"]),
                        "anchors": already["anchors"], "anchors_merged": already["already"]})
        print(f"    앵커 {already['anchors']} (정규 번호 노드에 이미 있는 것 "
              f"{already['already']})")
    if not apply:
        print("  (dry-run. 처리하려면 --apply)")
        return 0

    path = _record(wg, entries, "stale_backfill_prune.json")
    print(f"  되돌림 기록: {path.relative_to(PROJECT_ROOT)}")
    moved = deleted = 0
    for s, ent in zip(prune, entries):
        def tx(t, s=s, ent=ent):
            _assert_prune_preimage(t, ent)
            m = (t.run(Q_MOVE, e=s["element_id"], k=s["twin_element_id"],
                       twin=s["twin"]).single()["c"] if s["twin_element_id"] else 0)
            if m != ent["anchors"]:
                raise RuntimeError(f"{s['name']!r}: 앵커 {ent['anchors']} 중 {m} 만 옮겨짐")
            d = t.run(Q_DELETE, e=s["element_id"]).single()["c"]
            return m, d
        m, d = session.execute_write(tx)
        moved += m
        deleted += d
    merged = sum(e["anchors_merged"] for e in entries)
    print(f"  앵커 {moved} 처리(새로 {moved - merged} · 병합 {merged}) · 노드 {deleted} 삭제")

    left = [s["name"] for s in backfill_provenance.stale_nodes(session, wg)
            if s["verdict"] == "prune"]
    if left:
        print(f"  🔴 처리 뒤에도 남음: {left}")
        return 1
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wg", required=True, choices=["ALL", *BOLT_PORTS])
    ap.add_argument("--apply", action="store_true", help="실제로 옮기고 지운다 (기본은 dry-run)")
    args = ap.parse_args(argv[1:])
    targets = list(BOLT_PORTS) if args.wg == "ALL" else [args.wg]
    return max(run_wg(wg, args.apply) for wg in targets)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
