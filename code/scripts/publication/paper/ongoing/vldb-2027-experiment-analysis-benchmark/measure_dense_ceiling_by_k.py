"""밀집 검색 문맥의 정답 담김 상한을 청크 수 k 마다 센다 (모델 호출 없음, 임베딩은 로컬 bge-m3).

왜 세는가
  dense 방법은 `run_chain_eval.retrieve(item, 8)` 로 청크 8개를 골라 청크마다 메타데이터 JSON 과 본문 앞 1500자를
  준다. k 를 늘리면 문맥에 정답이 얼마나 더 들어오는지를 같은 기준으로 재어, "청크 8개라서 낮다"는 설명이
  어디까지 맞는지 가른다.

무엇을 세는가
  k 마다 `measure_text_route_ceiling.dense_chunks(item, k)` 를 따로 부른다(= `retrieve(item, k)`). 큰 k 의 결과를
  앞에서 잘라 쓰지 않는 까닭은 Qdrant 가 `limit` 에 맞춰 탐색 폭을 넓혀 작은 k 의 상위 목록이 큰 k 목록의
  앞부분과 다를 수 있어서다. dense 실행이 k 에서 실제로 받을 문맥을 그대로 잰다. 두 목록이 앞부분에서 같은지는
  문항마다 `prefixOfLargest` 로 남긴다.
  담김 판정은 `measure_text_route_ceiling.judge` 를 그대로 쓴다. 정답 행의 모든 칸이 문맥에 문자열로 들어 있으면
  그 행을 담김으로 센다(대소문자 무시, bis 회의 표기 맞춤, 칸이 서로 다른 청크에 흩어져도 담김 → 느슨한 상한).
  - meta: 청크마다 `retrieve` 가 붙이는 메타데이터 JSON + 본문 앞 1500자(dense 실행과 같은 문맥).
  - textonly: 메타데이터를 `{}` 로 비운 같은 청크. 정답 칸이 메타데이터에만 있는지 본문에도 있는지를 가른다.
  allRows(정답 행이 모두 담긴 문항 수)·anyRow(한 행 이상)와 singleChunk·singleDocument·multiDocument,
  청크 수·글자 수의 중앙값과 최댓값, 칸 이름마다 담긴 칸의 비율을 전체·WG·종류·WG×종류로 남긴다.
  빈 정답 문항은 상한을 정의할 수 없으므로 emptyGold 로 문항 수만 센다.
  k 가 커지면 글자 수가 독해 모델의 문맥 길이를 넘는다. 이 값은 담김의 상한이지 그 k 로 모델이 실제로 읽을 수 있는
  문맥이라는 뜻이 아니다. 글자 수를 함께 남겨 어느 k 까지 문맥 길이 안에 드는지를 읽을 수 있게 한다.

대조
  - 밀집 검색이 돌려준 청크마다 텍스트 경로 상한 색인(`text_route_ceiling/index/{wg}.sqlite3`)의 같은 청크와
    메타데이터·본문이 같은지 대조한다. 색인의 점 수가 지금 컬렉션과 다르면 멈춘다(`Index.check_counts`).
  - `--reference` 로 기존 문항별 상한 결과(`text_route_ceiling/items.jsonl`)를 주면, 질문 해시가 같은 문항에서
    k=8 meta 의 행별 판정이 기존 `dense_8x1500` 과 같은지 센다.

자원
  사용 가능한 메모리가 8 GiB 아래로 내려가면 멈춘다. 임베딩은 `retrieve` 와 같은 로컬 인코더만 쓴다.
  Qdrant 는 읽기만 한다.

사용 (저장소 루트에서):
  PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark \
    python3 scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_dense_ceiling_by_k.py \
      --items <jsonl> [<jsonl> ...] --out <json>
  문항별 결과는 `<out 이름>_items.jsonl` 에 쌓고, 질문 해시·정답 해시·k 목록이 모두 같은 문항은 다시 세지 않는다.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import statistics
import time
from pathlib import Path

from measure_text_route_ceiling import ROOT, WGS, Index, available_gib, dense_chunks, guard_memory, judge

VARIANTS = ("meta", "textonly")
# dense 실행(`solve_text`)이 청크마다 넣는 본문 길이.
TEXT_LIMIT = 1500


def question_sha(item: dict) -> str:
    return hashlib.sha256(item["question"].encode()).hexdigest()


def gold_sha(item: dict) -> str:
    """판정은 정답 행에 달려 있으므로, 질문이 같아도 정답이 바뀐 문항은 다시 센다."""
    rows = sorted(json.dumps(row, ensure_ascii=False) for row in item["gold"])
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def measure_item(item: dict, index: Index, ks: list[int]) -> dict:
    by_k, seen = {}, {}
    for k in ks:
        chunks = dense_chunks(item, k)
        by_k[k] = chunks
        for chunk in chunks:
            seen.setdefault((chunk["collection"], chunk["chunkId"]), chunk)
    integrity = collections.Counter()
    for (collection, chunk_id), chunk in seen.items():
        stored = index.by_chunk(collection, chunk_id)
        if stored is None:
            integrity["missingOrAmbiguous"] += 1
        else:
            integrity["compared"] += 1
            integrity["metaMismatch"] += stored["metaJson"] != chunk["metaJson"]
            integrity["textMismatch"] += stored["text"] != chunk["text"]
    largest = [(chunk["collection"], chunk["chunkId"]) for chunk in by_k[max(ks)]]
    results = {}
    for k, chunks in by_k.items():
        keys = [(chunk["collection"], chunk["chunkId"]) for chunk in chunks]
        textonly = [{**chunk, "metaJson": "{}"} for chunk in chunks]
        results[str(k)] = {"meta": judge(chunks, TEXT_LIMIT, item), "textonly": judge(textonly, TEXT_LIMIT, item),
                           "prefixOfLargest": keys == largest[:len(keys)],
                           "byCollection": dict(collections.Counter(chunk["collection"].split("_", 1)[1]
                                                                    for chunk in chunks))}
    return {"id": item["id"], "questionSha256": question_sha(item), "goldSha256": gold_sha(item),
            "wg": item["wg"], "family": item["family"],
            "fields": item["fields"], "goldRows": len(item["gold"]), "ks": ks, "byK": results,
            "integrity": dict(integrity)}


def summarize(records: list[dict], ks: list[int]) -> dict:
    def group(selected: list[dict]) -> dict:
        scored = [record for record in selected if record["goldRows"]]
        out = {"n": len(scored), "emptyGold": len(selected) - len(scored), "byK": {}}
        for k in map(str, ks):
            entry = {}
            for variant in VARIANTS:
                stats = collections.Counter()
                chunks, chars = [], []
                for record in scored:
                    result = record["byK"][k][variant]
                    rows = result["rows"]
                    chunks.append(result["chunks"])
                    chars.append(result["chars"])
                    if "missing" not in rows:
                        stats["allRows"] += 1
                        worst = "documents" if "documents" in rows else "document" if "document" in rows else "chunk"
                        stats[{"chunk": "singleChunk", "document": "singleDocument",
                               "documents": "multiDocument"}[worst]] += 1
                    stats["anyRow"] += any(row != "missing" for row in rows)
                entry[variant] = {key: stats[key] for key in ("allRows", "anyRow", "singleChunk", "singleDocument",
                                                              "multiDocument")}
                if scored:
                    entry[variant].update(chunksMedian=statistics.median(chunks), chunksMax=max(chunks),
                                          charsMedian=statistics.median(chars), charsMax=max(chars))
            collections_used = collections.Counter()
            for record in scored:
                collections_used.update(record["byK"][k]["byCollection"])
            entry["chunksByCollection"] = dict(sorted(collections_used.items()))
            entry["prefixOfLargest"] = sum(record["byK"][k]["prefixOfLargest"] for record in scored)
            out["byK"][k] = entry
        return out

    groups = [{"by": "total", "value": "all", **group(records)}]
    for key in ("wg", "family"):
        for value in sorted({record[key] for record in records}):
            groups.append({"by": key, "value": value, **group([r for r in records if r[key] == value])})
    for wg, family in sorted({(record["wg"], record["family"]) for record in records}):
        groups.append({"by": "wg×family", "value": f"{wg}|{family}",
                       **group([r for r in records if r["wg"] == wg and r["family"] == family])})
    fields: dict = {}
    for family in sorted({record["family"] for record in records}):
        selected = [record for record in records if record["family"] == family and record["goldRows"]]
        if not selected:
            continue
        names = selected[0]["fields"]
        total = sum(record["goldRows"] for record in selected)
        fields[family] = {k: {variant: {name: round(sum(record["byK"][k][variant]["fieldsHeld"][position]
                                                        for record in selected) / total, 4)
                                        for position, name in enumerate(names)} for variant in VARIANTS}
                          for k in map(str, ks)}
    # k 를 늘렸는데 담김이 사라진 문항: 작은 k 의 목록이 큰 k 목록의 앞부분이 아닐 때만 생길 수 있다.
    lost: dict = {}
    for variant in VARIANTS:
        for small, large in zip(ks, ks[1:]):
            lost[f"{variant}:{small}->{large}"] = [
                record["id"] for record in records if record["goldRows"]
                and "missing" not in record["byK"][str(small)][variant]["rows"]
                and "missing" in record["byK"][str(large)][variant]["rows"]]
    return {"groups": groups, "fieldHeldRate": fields, "containedAtSmallerKLostAtLarger": lost}


def compare_reference(records: list[dict], path: Path) -> dict:
    reference = {}
    for line in path.read_text().splitlines():
        stored = json.loads(line)
        reference[stored["id"]] = stored
    counts = collections.Counter()
    differing = []
    for record in records:
        stored = reference.get(record["id"])
        if stored is None or stored["questionSha256"] != record["questionSha256"]:
            counts["notInReference"] += 1
            continue
        if stored["goldRows"] != record["goldRows"]:
            counts["goldRowsDiffer"] += 1
            continue
        same = stored["routes"]["dense_8x1500"]["rows"] == record["byK"]["8"]["meta"]["rows"]
        counts["same" if same else "different"] += 1
        if not same:
            differing.append(record["id"])
    return {"file": str(path.resolve().relative_to(ROOT)), "route": "dense_8x1500", **counts, "differentIds": differing}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--ks", type=int, nargs="+", default=[8, 16, 32, 64, 128, 256],
                        help="문맥에 넣는 청크 수들. 8 은 dense 실행의 값이고, 두 배씩 늘린다")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reference", type=Path, help="기존 문항별 상한 결과(items.jsonl). k=8 판정을 대조한다")
    args = parser.parse_args()
    ks = sorted(set(args.ks))
    if 8 not in ks and args.reference:
        raise SystemExit("--reference 대조에는 k=8 이 필요하다")
    items = [json.loads(line) for path in args.items for line in path.read_text().splitlines() if line.strip()]
    per_item = args.out.with_name(args.out.stem + "_items.jsonl")
    stored = [json.loads(line) for line in per_item.read_text().splitlines()] if per_item.exists() else []
    current = {item["id"]: (question_sha(item), gold_sha(item)) for item in items}
    kept = [record for record in stored
            if current.get(record["id"]) == (record["questionSha256"], record.get("goldSha256")) and record["ks"] == ks]
    if len(kept) != len(stored):
        per_item.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in kept))
    done = {record["id"] for record in kept}
    seconds: collections.Counter = collections.Counter()
    live = {}
    with per_item.open("a") as out:
        for wg in WGS:
            todo = [item for item in items if item["wg"] == wg and item["id"] not in done]
            if not any(item["wg"] == wg for item in items):
                continue
            index = Index(wg)
            live[wg] = index.check_counts()
            for position, item in enumerate(todo, 1):
                guard_memory()
                started = time.time()
                record = measure_item(item, index, ks)
                record["seconds"] = round(time.time() - started, 2)
                seconds[wg] += record["seconds"]
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                out.flush()
                if position % 20 == 0 or position == len(todo):
                    print(json.dumps({"wg": wg, "done": position, "of": len(todo), "lastSeconds": record["seconds"],
                                      "availableGiB": round(available_gib(), 1)}), flush=True)
            index.con.close()
    records = [json.loads(line) for line in per_item.read_text().splitlines()]
    records = [record for record in records
               if current.get(record["id"]) == (record["questionSha256"], record.get("goldSha256"))]
    integrity = collections.Counter()
    for record in records:
        integrity.update(record["integrity"])
    report = {
        "items": {"files": [str(path.resolve().relative_to(ROOT)) if path.resolve().is_relative_to(ROOT) else str(path)
                            for path in args.items],
                  "total": len(items), "measured": len(records)},
        "ks": ks,
        "retrieval": "k 마다 run_chain_eval.retrieve(item, k) 를 따로 부름: WG 의 결정·CR·기고문 컬렉션마다 k 개를 찾아 "
                     "점수순 k 개(로컬 bge-m3 질의 임베딩)",
        "metric": "정답 행의 모든 칸이 문맥(청크마다 메타데이터 JSON + 본문 앞 1500자)에 들어 있으면 담김, "
                  "대소문자 무시, bis 회의 표기는 한 가지 철자로 맞춤. allRows=모든 행 담김, anyRow=한 행 이상 담김. "
                  "textonly 는 메타데이터를 {} 로 비운 같은 청크. 빈 정답 문항은 emptyGold 로만 센다.",
        "integrity": {"denseChunksAgainstIndex": dict(integrity), "liveCounts": live},
        "runtime": {"secondsByWgThisRun": {wg: round(value, 1) for wg, value in sorted(seconds.items())},
                    "secondsTotalAllRecords": round(sum(record["seconds"] for record in records), 1)},
        **summarize(records, ks),
    }
    if args.reference:
        report["reference"] = compare_reference(records, args.reference)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    total = report["groups"][0]
    print(json.dumps({"n": total["n"], "emptyGold": total["emptyGold"],
                      "allRows": {k: {variant: total["byK"][k][variant]["allRows"] for variant in VARIANTS}
                                  for k in total["byK"]},
                      "reference": report.get("reference", {}).get("same")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
