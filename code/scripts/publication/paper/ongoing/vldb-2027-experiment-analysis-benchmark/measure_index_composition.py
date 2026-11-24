"""dense 방법이 찾는 Qdrant 컬렉션의 구성을 센다: WG·컬렉션마다 점 수, payload 키, dense 문맥에 들어가는 키 (모델 호출 없음).

왜 세는가
  dense 방법(`run_chain_eval.retrieve`)은 WG 마다 결정·CR·기고문 세 컬렉션을 찾고, 청크마다 payload 가운데
  `measure_text_route_ceiling.META_KEYS` 의 값 있는 키만 메타데이터 JSON 으로 붙인다. 이 스크립트는 그 컬렉션들에
  무엇이 얼마나 들어 있고, 어떤 키가 문맥에 들어가고 어떤 키가 들어가지 않는지를 전수로 센다.

무엇을 세는가 (컬렉션마다)
  - 점 수: 정확 개수(`points/count`, exact)를 읽기 시작과 끝에 한 번씩 읽고 훑은 점 수와 대조한다. 텍스트 경로 상한
    색인(`text_route_ceiling/index/{wg}.sqlite3`)의 manifest 와도 대조한다.
  - payload 키: 모든 점을 scroll 로 훑어(본문 키 `text`·`content` 는 빼고 읽는다) 키마다 있는 점 수와 값 있는 점 수
    (빈 문자열·null·빈 목록·빈 객체가 아닌 값)를 센다. 본문 키는 값 있는 점 수만 색인에서 센다.
  - 키를 청크 종류별로 나눠 센다. CR 은 `chunkType`, 결정 기록은 `resolutionType` 이 종류다. 기고문 컬렉션은 나누지 않는다.
  - dense 문맥 키(`META_KEYS`)마다 값의 서로 다른 개수.
  - 색인에서: 청크 번호 꼴(CR 머리 `…-header` · 본문 `…-body-…`, 결정 기록 `resolutionId` 앞머리 `DOC-`·`AGR-`·`CON-`),
    문서 수(`tdocNumber` 또는 `resolutionId` 의 서로 다른 개수), 문서당 청크 수.
  점은 바꾸지 않고 읽기만 한다. 벡터는 읽지 않는다.

사용 (저장소 루트에서):
  PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark \
    python3 scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_index_composition.py --out <json>
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import statistics
import time
import urllib.request
from pathlib import Path

from measure_text_route_ceiling import META_KEYS, WGS, Index, available_gib, guard_memory, point_count
from run_chain_eval import DENSE_COLLECTIONS, QDRANT, TEXT_KEYS, post

KIND_KEY = {"cr_chunks": "chunkType", "resolution_chunks": "resolutionType"}
HEADER = re.compile(r"-header(?:-\d+)?$")
BODY = re.compile(r"-body-\d+(?:-\d+)?$")


def filled(value) -> bool:
    return value not in (None, "", [], {})


def census(collection: str, kind_key: str | None, page: int) -> dict:
    """모든 점의 payload 키를 센다(본문 키 제외)."""
    count_start, started = point_count(collection), time.time()
    present: collections.Counter = collections.Counter()
    nonempty: collections.Counter = collections.Counter()
    by_kind: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    kinds: collections.Counter = collections.Counter()
    values: dict[str, set] = {key: set() for key in META_KEYS}
    scanned, offset, pages = 0, None, 0
    while True:
        body = {"limit": page, "with_payload": {"exclude": list(TEXT_KEYS)}, "with_vector": False}
        if offset is not None:
            body["offset"] = offset
        result = post(f"{QDRANT}/collections/{collection}/points/scroll", body, timeout=300)["result"]
        for point in result["points"]:
            payload = point.get("payload") or {}
            kind = str(payload.get(kind_key)) if kind_key else "all"
            kinds[kind] += 1
            for key, value in payload.items():
                present[key] += 1
                if filled(value):
                    nonempty[key] += 1
                    by_kind[kind][key] += 1
                    if key in values:
                        values[key].add(json.dumps(value, ensure_ascii=False, sort_keys=True))
            scanned += 1
        pages += 1
        if pages % 200 == 0:
            guard_memory()
            print(json.dumps({"collection": collection, "scanned": scanned, "of": count_start,
                              "seconds": round(time.time() - started), "availableGiB": round(available_gib(), 1)}),
                  flush=True)
        offset = result.get("next_page_offset")
        if offset is None:
            break
    count_end = point_count(collection)
    if not count_start == scanned == count_end:
        raise SystemExit(f"{collection}: 시작 {count_start} · 훑은 점 {scanned} · 끝 {count_end} 가 달라 멈춘다")
    keys = sorted(present, key=lambda key: (-present[key], key))
    return {"points": scanned, "seconds": round(time.time() - started, 1),
            "payloadKeys": {key: {"present": present[key], "nonEmpty": nonempty[key],
                                  "inDenseContext": key in META_KEYS} for key in keys},
            "chunkKinds": None if not kind_key else {
                "key": kind_key,
                "kinds": {kind: {"points": n, "nonEmpty": dict(sorted(by_kind[kind].items()))}
                          for kind, n in sorted(kinds.items(), key=lambda entry: -entry[1])}},
            "distinctValues": {key: len(found) for key, found in values.items() if found}}


def collection_info(collection: str) -> dict:
    """컬렉션 설정 가운데 벡터 크기·거리와 payload 색인 키(GET 요청, 읽기만 한다)."""
    with urllib.request.urlopen(f"{QDRANT}/collections/{collection}", timeout=60) as response:
        result = json.load(response)["result"]
    vectors = result["config"]["params"]["vectors"]
    return {"vectors": vectors, "indexedPayloadKeys": sorted(result.get("payload_schema", {}))}


def index_view(index: Index, collection: str, suffix: str) -> dict:
    """색인에서 센다: 본문이 빈 청크, 청크 번호 꼴, 문서 수와 문서당 청크 수."""
    rows = index.con.execute("SELECT chunk_id, meta, length(text) FROM docs WHERE collection = ?", (collection,))
    shapes: collections.Counter = collections.Counter()
    per_doc: collections.Counter = collections.Counter()
    empty_text = 0
    for chunk_id, meta, length in rows:
        empty_text += length == 0
        parsed = json.loads(meta)
        if suffix == "cr_chunks":
            shapes["header" if HEADER.search(chunk_id or "") else "body" if BODY.search(chunk_id or "") else "other"] += 1
        elif suffix == "resolution_chunks":
            prefix = parsed.get("resolutionId", "").split("-", 1)[0]
            shapes[prefix if prefix in ("DOC", "AGR", "CON") else "other"] += 1
        else:
            shapes["all"] += 1
        per_doc[parsed.get("tdocNumber") or parsed.get("resolutionId") or "(none)"] += 1
    sizes = list(per_doc.values())
    return {"emptyText": empty_text, "chunkIdShapes": dict(shapes), "documents": len(per_doc),
            "chunksWithoutDocumentKey": per_doc.get("(none)", 0),
            "chunksPerDocument": {"median": statistics.median(sizes), "max": max(sizes)} if sizes else None}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--wg", nargs="*", choices=WGS, help="이 WG 들만 센다")
    parser.add_argument("--page", type=int, default=2000, help="scroll 한 번에 읽는 점 수(결과에는 영향이 없다)")
    args = parser.parse_args()
    report, started = {"denseContextKeys": list(META_KEYS), "textKeys": list(TEXT_KEYS), "wgs": {}}, time.time()
    for wg in args.wg or WGS:
        guard_memory()
        index = Index(wg)
        manifest = {entry["collection"]: entry for entry in index.manifest()}
        entry = {}
        for suffix in DENSE_COLLECTIONS:
            collection = f"{wg.lower()}_{suffix}"
            found = {"collection": collection, **collection_info(collection),
                     **census(collection, KIND_KEY.get(suffix), args.page)}
            found["index"] = {"stored": manifest[collection]["stored"],
                              "nonStringText": manifest[collection]["nonStringText"],
                              "matchesLiveCount": manifest[collection]["stored"] == found["points"],
                              **index_view(index, collection, suffix)}
            entry[suffix] = found
            print(json.dumps({"collection": collection, "points": found["points"], "seconds": found["seconds"]}),
                  flush=True)
        index.con.close()
        report["wgs"][wg] = entry
    report["seconds"] = round(time.time() - started, 1)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
