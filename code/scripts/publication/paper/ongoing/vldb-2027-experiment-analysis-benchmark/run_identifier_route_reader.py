"""식별자를 따라 모은 문맥을 이 호스트의 모델에 주고 답을 받아 그대로 저장한다 (ollama, 과금 API 없음).

왜 푸는가
  `measure_raw_source_route.py` 와 `measure_text_route_ceiling.py` 는 식별자 따라가기 문맥에 정답이 들어오는지만 센다.
  이 스크립트는 같은 문맥을 모델의 문맥 길이에 맞춰 담아 실제로 읽게 하고, `run_chain_eval.py` 의 dense 와 같은
  답 규칙 · 요청 꼴 · 결과 줄 꼴로 응답을 남긴다. 채점은 `score_chain_eval.py` · `summarize_chain_scores.py` 가 그대로 한다.

두 문맥 (`--route`)
  raw_source  원문 경로. `measure_raw_source_route.py` 가 남긴 `orders.jsonl` 의 청크 차례(시작 청크 다음 따라간 청크)를
              그대로 쓴다. 변형은 그 측정의 `ceiling.json` 에서 raw_wgtsg_1500 의 allRows 가 raw_wg_1500 보다 크면
              raw_wgtsg_1500(작업반 + TSG 총회), 아니면 raw_wg_1500(작업반만)이다. 구절 머리는 원문 파일의 문서 번호 ·
              파일 이름이고 본문은 원문 글 앞 1500자다.
  hopkey      기록 필드 경로. `measure_text_route_ceiling.py` 의 hopkey_1500 과 같은 청크 집합이다(문항마다 집합이 같은지
              `hop_ids` 로 맞춰 본다). 차례는 질문에 나온 번호마다 `key_ids`(id 순), 이어서 절 청크(id 순), 이어서 따라간
              번호(정렬 차례)마다 `key_ids`(id 순)이다. 구절 머리는 그 측정이 본 메타데이터 JSON 이고 본문은 앞 1500자다.

요청
  `run_chain_eval.text_request` 에 청크를 줄 때와 같은 메시지다. 시스템은 "Answer from the retrieved records only. " 뒤에
  `answer_rules(item)`, 사용자는 "Retrieved records:\\n{[n] 머리\\n본문 …}\\n\\nQuestion: {질문}" 이다. 요청은
  `chat_request(model, messages, 16384)` 로 만든다(온도 0 · 씨앗 0 · JSON 형식 · 출력 최대 8192 토큰).

담기 (실행 전에 정한 규칙)
  구절을 경로 차례로 통째로 넣고, 프롬프트 토큰 수가 `PROMPT_TOKENS` 이하인 가장 긴 앞부분을 쓴다. 토큰 수는 같은
  요청을 출력 한 토큰(num_predict 1)으로 보내 ollama 가 센 `prompt_eval_count` 다. 담을 구절 수는 이 수가 단조로 늘어난다고
  보고 어림과 이분으로 찾는다(답은 찾는 차례와 상관없다, `fit` 참고).
  `PROMPT_TOKENS` = 문맥 16384 − 응답 몫 4096. 응답 몫은 두 문항 파일에서 가장 긴 정답 JSON(3809자)을 글자당
  토큰 하나로 쳐도 담는 길이다. 프롬프트와 출력을 합쳐 문맥을 다 채운 응답은 `packing.contextFilled` 로 남긴다.

결과 줄
  `run_chain_eval.py` 의 dense 와 같은 열쇠(id · questionSha256 · wg · family · method · model · seconds · rows · response ·
  requestSha256 · retrieved)에 `packing`(담은 구절 수 · 글자 수 · 토큰 수 · 잰 기록)을 더한다. method 는
  `identifier_raw_source` · `identifier_hopkey` 다. 파일은 `chain_eval/identifier_route/{WG}_{route}_{model}.jsonl`
  (모델 이름의 `:` · `.` 은 `_`)이다. 다시 실행하면 저장된 줄의 담은 구절 수로 요청을 다시 만들어 `requestSha256` 이
  같은 문항은 건너뛴다.

풀이 쪽은 정답을 읽지 않는다. `--judge` 는 저장된 응답의 담은 구절에 정답이 남아 있는지를 따로 센다
(`measure_raw_source_route.Judge`, 담김 규칙은 두 측정과 같다).

사용: PYTHONPATH=scripts/common:<이 폴더> python3 run_identifier_route_reader.py --route raw_source --model qwen2.5:14b
      PYTHONPATH=… python3 run_identifier_route_reader.py --judge
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import statistics
import time
from pathlib import Path

from measure_raw_source_route import (ITEM_FILES, ORDER_CHARS, PLENARY, Judge, PlenarySource, WgSource, load,
                                      read_jsonl, visible as raw_visible)
from measure_text_route_ceiling import (DOC_RE, PACK_RE, ROOT, WGS, Index, available_gib, gold_sha, guard_memory,
                                        hop_ids, named_identifiers, seed_ids, shown, visible as hop_visible)
from run_chain_eval import OLLAMA, answer_rules, chat_request, packet_id, post, question_sha, request_sha, rows_of
from score_chain_eval import meeting_spelling

TRACK = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
RAW_DIR = TRACK / "final/raw_source_route"
HOPKEY_ITEMS = TRACK / "final/text_route_ceiling/items.jsonl"
OUT_DIR = TRACK / "chain_eval/identifier_route"
REPORT_DIR = TRACK / "final/identifier_route"
ROUTES = ("raw_source", "hopkey")
CONTEXT = 16384
ANSWER_RESERVE = 4096
PROMPT_TOKENS = CONTEXT - ANSWER_RESERVE
PASSAGE_CHARS = 1500
# 어림으로 다가가다 늦어지면 이분으로 바꾸는 잼 횟수. 답(가장 긴 앞부분)은 바뀌지 않고 시간만 달라진다.
SEARCH_PROBES = 8


def model_tag(model: str) -> str:
    return model.replace(":", "_").replace(".", "_")


def out_path(out_dir: Path, wg: str, route: str, model: str) -> Path:
    return out_dir / f"{wg}_{route}_{model_tag(model)}.jsonl"


def raw_variant() -> tuple[str, dict]:
    """원문 경로 변형을 원문 측정의 담김 수로 고른다. 고른 근거(두 변형의 allRows)를 함께 돌려준다."""
    ceiling = json.loads((RAW_DIR / "ceiling.json").read_text())
    total = ceiling["groups"][0]
    if total["by"] != "total":
        raise SystemExit("ceiling.json 의 첫 묶음이 전체가 아니다")
    wg_only = total["routes"]["raw_wg_1500"]["allRows"]
    with_tsg = total["routes"].get("raw_wgtsg_1500", {}).get("allRows")
    chosen = "raw_wgtsg_1500" if with_tsg is not None and with_tsg > wg_only else "raw_wg_1500"
    return chosen, {"raw_wg_1500": f"{wg_only}/{total['n']}",
                    "raw_wgtsg_1500": None if with_tsg is None else f"{with_tsg}/{total['n']}",
                    "measuredItems": ceiling["items"]["measured"], "chosen": chosen}


class RawRoute:
    """원문 경로의 구절. 청크 차례는 `orders.jsonl` 에 있는 그대로다."""

    def __init__(self, variant: str):
        self.variant = variant
        self.orders = {order["id"]: order for order in read_jsonl(RAW_DIR / "orders.jsonl")}
        self.plenary = PlenarySource(PLENARY) if "wgtsg" in variant else None
        self.wg_sources: dict[str, WgSource] = {}

    def passages(self, item: dict) -> dict:
        order = self.orders.get(item["id"])
        if order is None or order["questionSha256"] != question_sha(item):
            raise SystemExit(f"{item['id']}: orders.jsonl 에 지금 질문의 경로 차례가 없다 — 원문 측정을 먼저 다시 한다")
        plan = order["orders"][self.variant]
        wg = item["wg"]
        if wg not in self.wg_sources:
            self.wg_sources[wg] = WgSource(wg)
        sources = [self.wg_sources[wg]] + ([self.plenary] if self.plenary else [])
        fetched: dict[str, dict] = {}
        load(plan["keys"], sources, fetched)
        chunks = [fetched[key] for key in plan["keys"]]
        return {"keys": plan["keys"], "texts": [raw_visible(chunk, PASSAGE_CHARS) for chunk in chunks],
                "groups": [chunk["group"] for chunk in chunks], "routeChunks": plan["total"],
                "orderTruncated": plan["stored"] < plan["total"]}


class HopkeyRoute:
    """기록 필드 경로(hopkey_1500)의 구절. 집합은 `hop_ids` 와 같고, 차례는 경로를 밟은 차례다."""

    variant = "hopkey_1500"

    def __init__(self):
        self.indexes: dict[str, Index] = {}

    def ordered_ids(self, index: Index, named: dict) -> list[int]:
        seeds: list[int] = []
        for ident in named["docs"] + named["packs"]:
            seeds += sorted(index.key_ids(ident))
        if named["clause"]:
            seeds += sorted(index.clause_ids(*named["clause"]))
        seeds = list(dict.fromkeys(seeds))
        looked_up = set(named["docs"] + named["packs"])
        found: set[str] = set()
        for chunk in index.rows(seeds):
            text = hop_visible(chunk, PASSAGE_CHARS)
            found.update(match.upper() for match in DOC_RE.findall(text))
            found.update(match.upper() for match in PACK_RE.findall(text))
        hops: list[int] = []
        for ident in sorted(found - looked_up):
            hops += sorted(index.key_ids(ident))
        ordered = list(dict.fromkeys(seeds + hops))
        expected, _ = hop_ids(index, seed_ids(index, named, False), looked_up, PASSAGE_CHARS, False)
        if set(ordered) != expected:
            raise SystemExit("hopkey 경로 차례가 measure_text_route_ceiling.hop_ids 의 집합과 다르다")
        return ordered

    def passages(self, item: dict) -> dict:
        wg = item["wg"]
        if wg not in self.indexes:
            self.indexes[wg] = Index(wg)
        index = self.indexes[wg]
        ordered = self.ordered_ids(index, named_identifiers(item["question"]))
        keys, texts, groups, total = [], [], [], 0
        for start in range(0, len(ordered), 900):
            if total >= ORDER_CHARS:
                break
            part = ordered[start:start + 900]
            fetched = index.fetch(part)
            for row_id in part:
                if total >= ORDER_CHARS:
                    break
                text = hop_visible(fetched[row_id], PASSAGE_CHARS)
                keys.append(f"{fetched[row_id]['collection']}:{fetched[row_id]['chunkId']}")
                texts.append(text)
                groups.append(fetched[row_id]["doc"])
                total += len(text) + 2
        return {"keys": keys, "texts": texts, "groups": groups, "routeChunks": len(ordered),
                "orderTruncated": len(keys) < len(ordered)}


def passage_request(item: dict, model: str, texts: list[str]) -> dict:
    """`run_chain_eval.text_request` 에 청크를 줄 때와 같은 메시지를 구절 글로 만든다."""
    rules = "Answer from the retrieved records only. " + answer_rules(item)
    passages = "\n\n".join(f"[{n + 1}] {text}" for n, text in enumerate(texts))
    question = f"Retrieved records:\n{passages}\n\nQuestion: {item['question']}"
    return chat_request(model, [{"role": "system", "content": rules}, {"role": "user", "content": question}], CONTEXT)


def prompt_tokens(request: dict) -> int:
    probe = {**request, "options": {**request["options"], "num_predict": 1}}
    return post(OLLAMA, probe)["prompt_eval_count"]


def fit(item: dict, model: str, texts: list[str], rate: float | None) -> tuple[int, list[list[int]], float | None]:
    """프롬프트 토큰이 `PROMPT_TOKENS` 이하인 가장 긴 앞부분의 구절 수를 잰다.

    토큰 수는 구절 수에 따라 단조로 늘므로 답은 어느 자리를 어떤 차례로 재든 같다. 차례는 시간만 정한다.
    ollama 는 앞부분이 같은 프롬프트를 다시 계산하지 않으므로 아래에서 위로 다가가거나 넘친 자리에서 내려오는 잼은
    늘어난 몫만 계산한다. 문맥보다 긴 프롬프트는 잘라 센 데다(문맥 길이로 나온다) 쌓아 둔 앞부분도 버리게 되므로
    첫 자리는 앞 문항들에서 잰 구절 글자 수 대 토큰 수 가운데 가장 작은 값(`rate`)으로 어림해 넘치지 않게 고른다.
    돌려주는 것: 구절 수, 잰 기록([구절 수, 토큰 수]), 이 문항에서 잰 글자 수 대 토큰 수(다음 문항의 어림에 쓴다).
    """
    measured: dict[int, int] = {}

    def tokens(count: int) -> int:
        if count not in measured:
            measured[count] = prompt_tokens(passage_request(item, model, texts[:count]))
        return measured[count]

    base = tokens(0)
    if base > PROMPT_TOKENS:
        raise SystemExit(f"{item['id']}: 구절 없이도 프롬프트가 {PROMPT_TOKENS} 토큰을 넘는다")
    total = len(texts)
    cumulative = [0]
    for text in texts:
        cumulative.append(cumulative[-1] + len(text) + 6)
    if rate is None:
        rate = sum(len(message["content"]) for message in passage_request(item, model, [])["messages"]) / base

    def reach(start: int, per_token: float, cap: float | None = None) -> int:
        target = cumulative[start] + (PROMPT_TOKENS - tokens(start)) * per_token
        if cap is not None:
            target = min(target, cap)
        return max(count for count in range(start, total + 1) if cumulative[count] <= target)

    low, high, probes = 0, None, 0
    guess = reach(0, rate)
    while low < total and (high is None or high - low > 1):
        guess = min(max(guess, low + 1), total if high is None else high - 1)
        probes += 1
        if tokens(guess) <= PROMPT_TOKENS:
            low = guess
        else:
            high = guess
        if low == total or (high is not None and high - low <= 1):
            break
        if probes >= SEARCH_PROBES:
            guess = (low + (total + 1 if high is None else high)) // 2
        elif high is not None and tokens(high) < CONTEXT:
            slope = (cumulative[high] - cumulative[low]) / max(tokens(high) - tokens(low), 1)
            guess = reach(low, slope)
        else:
            # 잘려 센 점은 기울기에 쓰지 않고, 글자 수로 두 점의 가운데를 넘지 않게 해 한 구절씩만 다가가지 않게 한다.
            per_token = cumulative[low] / (tokens(low) - base) if low else rate
            cap = None if high is None else (cumulative[low] + cumulative[high]) / 2
            guess = reach(low, per_token, cap)
    exact = [count for count, value in measured.items() if count and value < CONTEXT]
    learned = cumulative[max(exact)] / (tokens(max(exact)) - base) if exact else None
    return low, [[count, value] for count, value in measured.items()], learned


def sample_key(item: dict) -> str:
    """처리량 표본 차례. `packet_id` 의 해시 부분으로 정렬해 작업반 · 문항 종류가 섞이게 한다(앞머리는 작업반이다)."""
    return packet_id(item).split("-q", 1)[1]


def stored_records(path: Path, items: dict[str, dict]) -> dict[str, dict]:
    """문항마다 마지막 줄만 남긴다. 지금 대상 문항은 질문이 같고 담기 기록이 있는 줄만 다시 쓸 후보다."""
    stored: dict[str, dict] = {}
    for record in read_jsonl(path):
        stored[record["id"]] = record
    return {identifier: record for identifier, record in stored.items()
            if identifier not in items
            or (record.get("questionSha256") == question_sha(items[identifier]) and record.get("requestSha256")
                and isinstance(record.get("packing", {}).get("packedChunks"), int))}


def solve(args) -> None:
    items = [json.loads(line) for path in args.items for line in path.read_text().splitlines() if line.strip()]
    items = [item for item in items if item["wg"] in args.wg]
    if args.sample:
        chosen = {item["id"] for item in sorted(items, key=sample_key)[:args.sample]}
        items = [item for item in items if item["id"] in chosen]
    if args.route == "raw_source":
        variant, basis = raw_variant()
        route = RawRoute(variant)
    else:
        basis = None
        route = HopkeyRoute()
    print(json.dumps({"route": args.route, "variant": route.variant, "variantBasis": basis, "model": args.model,
                      "items": len(items), "promptTokens": PROMPT_TOKENS}, ensure_ascii=False), flush=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    done = reused = 0
    spent: list[float] = []
    rate: float | None = None
    for wg in WGS:
        todo = [item for item in items if item["wg"] == wg]
        if not todo:
            continue
        path = out_path(args.out_dir, wg, args.route, args.model)
        current = {item["id"]: item for item in todo}
        stored = stored_records(path, current)
        path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in stored.values()))
        with path.open("a") as out:
            for item in todo:
                guard_memory()
                started = time.time()
                built = route.passages(item)
                previous = stored.get(item["id"])
                if previous:
                    again = passage_request(item, args.model, built["texts"][:previous["packing"]["packedChunks"]])
                    if request_sha(again) == previous["requestSha256"]:
                        reused += 1
                        done += 1
                        continue
                count, probes, learned = fit(item, args.model, built["texts"], rate)
                if learned is not None:
                    rate = learned if rate is None else min(rate, learned)
                request = passage_request(item, args.model, built["texts"][:count])
                asked = time.time()
                answer = post(OLLAMA, request)
                text = answer["message"]["content"]
                packed = built["texts"][:count]
                record = {"id": item["id"], "questionSha256": question_sha(item), "wg": item["wg"],
                          "family": item["family"], "method": f"identifier_{args.route}", "model": args.model,
                          "seconds": round(time.time() - started, 1), "rows": rows_of(text), "response": text,
                          "requestSha256": request_sha(request),
                          "retrieved": [{"key": key} for key in built["keys"][:count]],
                          "packing": {"variant": route.variant, "routeChunks": built["routeChunks"],
                                      "orderedChunks": len(built["texts"]), "orderTruncated": built["orderTruncated"],
                                      "packedChunks": count, "packedAllOrdered": count == len(built["texts"]),
                                      "packedChars": sum(len(text) for text in packed),
                                      "answerSeconds": round(time.time() - asked, 1),
                                      "promptTokenLimit": PROMPT_TOKENS, "promptTokens": answer.get("prompt_eval_count"),
                                      "outputTokens": answer.get("eval_count"), "doneReason": answer.get("done_reason"),
                                      "contextFilled": (answer.get("prompt_eval_count") or 0)
                                      + (answer.get("eval_count") or 0) >= CONTEXT,
                                      "probes": probes}}
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                out.flush()
                done += 1
                spent.append(record["seconds"])
                left = len(items) - done
                print(json.dumps({"route": args.route, "model": args.model, "wg": wg, "done": done, "of": len(items),
                                  "id": item["id"], "seconds": record["seconds"], "packed": count,
                                  "ordered": len(built["texts"]), "promptTokens": record["packing"]["promptTokens"],
                                  "readable": record["rows"] is not None,
                                  "etaMinutes": round(statistics.mean(spent) * left / 60, 1),
                                  "availableGiB": round(available_gib(), 1)}, ensure_ascii=False), flush=True)
    print(json.dumps({"route": args.route, "model": args.model, "items": len(items), "reused": reused,
                      "solved": len(spent)}, ensure_ascii=False), flush=True)
    if args.throughput_out:
        write_throughput(args, items, spent)


def write_throughput(args, items: list[dict], spent: list[float]) -> None:
    records = []
    for wg in WGS:
        path = out_path(args.out_dir, wg, args.route, args.model)
        ids = {item["id"] for item in items if item["wg"] == wg}
        records += [record for record in read_jsonl(path) if record["id"] in ids]
    report = json.loads(args.throughput_out.read_text()) if args.throughput_out.exists() else {}
    seconds = [record["seconds"] for record in records]
    total_items = sum(1 for path in args.items for line in path.read_text().splitlines() if line.strip())
    report[f"{args.route}/{args.model}"] = {
        "sample": "packet_id 해시 부분 차례의 앞 문항(작업반 · 문항 종류가 섞인다)", "items": len(records),
        "solvedNow": len(spent), "responses": [shown(out_path(args.out_dir, wg, args.route, args.model))
                                               for wg in WGS if any(r["wg"] == wg for r in records)],
        "secondsMean": round(statistics.mean(seconds), 2), "secondsMedian": statistics.median(seconds),
        "secondsMax": max(seconds),
        "packedChunksMedian": statistics.median(record["packing"]["packedChunks"] for record in records),
        "promptTokensMedian": statistics.median(record["packing"]["promptTokens"] for record in records),
        "probesMedian": statistics.median(len(record["packing"]["probes"]) for record in records),
        "readable": f"{sum(record['rows'] is not None for record in records)}/{len(records)}",
        "fullRunItems": total_items,
        "fullRunMinutesAtMean": round(statistics.mean(seconds) * total_items / 60, 1)}
    args.throughput_out.parent.mkdir(parents=True, exist_ok=True)
    args.throughput_out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")


def judge(args) -> None:
    """저장된 응답의 담은 구절에 정답 행이 남아 있는지 센다(모델 호출 없음)."""
    items = {json.loads(line)["id"]: json.loads(line)
             for path in args.items for line in path.read_text().splitlines() if line.strip()}
    raw_items = {record["id"]: record for record in read_jsonl(RAW_DIR / "items.jsonl")}
    hop_items = {record["id"]: record for record in read_jsonl(HOPKEY_ITEMS)}
    report = {"rule": "담은 구절마다 소문자 · bis 회의 표기 맞춤 뒤 정답 칸(cell_key)이 들어 있는지 본다. allRows = 모든 정답 행의 "
                      "모든 칸이 담은 구절 어딘가에 있음. routeAllRows = 같은 문항의 경로 전체(측정 파일)에서 allRows. "
                      "빈 정답 문항은 세지 않는다.",
              "promptTokenLimit": PROMPT_TOKENS, "runs": {}}
    routes: dict[str, object] = {}
    for route_name in ROUTES:
        for model in args.models:
            records = []
            for wg in WGS:
                records += read_jsonl(out_path(args.out_dir, wg, route_name, model))
            records = [record for record in records if record["id"] in items
                       and record["questionSha256"] == question_sha(items[record["id"]])]
            if not records:
                continue
            if route_name not in routes:
                routes[route_name] = (RawRoute(records[0]["packing"]["variant"]) if route_name == "raw_source"
                                      else HopkeyRoute())
            route = routes[route_name]
            ceiling = raw_items if route_name == "raw_source" else hop_items
            stats = collections.Counter()
            by_family: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
            packed_chunks, packed_chars, tokens = [], [], []
            for record in records:
                item = items[record["id"]]
                packing = record["packing"]
                packed_chunks.append(packing["packedChunks"])
                packed_chars.append(packing["packedChars"])
                tokens.append(packing["promptTokens"])
                stats["contextFilled"] += packing["contextFilled"]
                stats["orderTruncated"] += packing["orderTruncated"]
                stats["orderCapBinding"] += packing["orderTruncated"] and packing["packedAllOrdered"]
                stats["unreadable"] += record["rows"] is None
                if not item["gold"]:
                    continue
                built = route.passages(item)
                checker = Judge(item)
                for text, group in zip(built["texts"][:packing["packedChunks"]], built["groups"]):
                    checker.add(meeting_spelling(text.lower()), group)
                rows = checker.result(item["fields"])["rows"]
                held_all = "missing" not in rows
                measured = ceiling[record["id"]]
                if measured["goldSha256"] != gold_sha(item) or measured["questionSha256"] != question_sha(item):
                    raise SystemExit(f"{record['id']}: 경로 측정 파일의 질문 · 정답이 지금 문항과 다르다 — 측정을 먼저 다시 한다")
                route_rows = measured["routes"][packing["variant"]]["rows"]
                route_all = "missing" not in route_rows
                for counter in (stats, by_family[item["family"]]):
                    counter["items"] += 1
                    counter["budgetAllRows"] += held_all
                    counter["budgetAnyRow"] += any(row != "missing" for row in rows)
                    counter["routeAllRows"] += route_all
                    counter["lostByBudget"] += route_all and not held_all
            report["runs"][f"{route_name}/{model}"] = {
                "variant": records[0]["packing"]["variant"], "responses": len(records),
                "answerable": stats["items"],
                **{key: f"{stats[key]}/{stats['items']}" for key in ("budgetAllRows", "budgetAnyRow", "routeAllRows",
                                                                     "lostByBudget")},
                "packedChunksMedian": statistics.median(packed_chunks), "packedCharsMedian": statistics.median(packed_chars),
                "promptTokensMedian": statistics.median(tokens), "promptTokensMax": max(tokens),
                "contextFilled": stats["contextFilled"], "orderTruncated": stats["orderTruncated"],
                "orderCapBinding": stats["orderCapBinding"],
                "unreadable": f"{stats['unreadable']}/{len(records)}",
                "byFamily": {family: {key: f"{counter[key]}/{counter['items']}"
                                      for key in ("budgetAllRows", "routeAllRows", "lostByBudget")}
                             for family, counter in sorted(by_family.items())}}
    args.judge_out.parent.mkdir(parents=True, exist_ok=True)
    args.judge_out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({run: {key: value[key] for key in ("budgetAllRows", "routeAllRows")}
                      for run, value in report["runs"].items()}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", default=list(ITEM_FILES), help="문항 파일(chain_items_admitted.jsonl)")
    parser.add_argument("--route", choices=ROUTES)
    parser.add_argument("--model")
    parser.add_argument("--wg", nargs="*", default=list(WGS), choices=WGS)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR, help="응답 파일 폴더")
    parser.add_argument("--sample", type=int, help="처리량 재기용: packet_id 해시 부분 차례의 앞 문항 이 수만 푼다")
    parser.add_argument("--throughput-out", type=Path, help="푼 뒤 처리량을 이 JSON 에 경로/모델 열쇠로 더한다")
    parser.add_argument("--judge", action="store_true", help="저장된 응답의 담은 구절에 정답이 남았는지 센다")
    parser.add_argument("--models", nargs="*", default=["qwen2.5:14b", "llama3.1:8b"], help="--judge 가 볼 모델")
    parser.add_argument("--judge-out", type=Path, default=REPORT_DIR / "budget_containment.json")
    args = parser.parse_args()
    if args.judge:
        judge(args)
        return
    if not args.route or not args.model:
        parser.error("--route 와 --model 을 준다")
    solve(args)


if __name__ == "__main__":
    main()
