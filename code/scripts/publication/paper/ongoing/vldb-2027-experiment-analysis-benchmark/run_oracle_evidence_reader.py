"""정답 근거가 든 청크만 문맥으로 주고 dense 방법과 같은 독해 모델·지시문으로 풀게 한다 (과금 API 없음).

왜 재는가
  dense 방법은 질문 임베딩으로 고른 청크 8개만 받는다. 점수가 낮은 까닭이 검색이 근거를 놓쳐서인지,
  근거를 받아도 독해 모델이 정답 행을 만들지 못해서인지를 가르려고, 검색을 정답 쪽 근거 고르기로 바꾼다.
  모델 호출은 `run_chain_eval.solve_text` 를 그대로 쓴다. 지시문, 문맥 꼴(청크마다 메타데이터 JSON 한 줄과
  본문 앞 1500자), ollama 설정(온도 0, seed 0, 출력 길이 = 문맥 길이의 절반)이 dense 실행과 같다.
  정답과 문항의 근거 필드를 읽어 청크를 고르므로 이 실행은 독해 쪽의 상한 실험이다. 문맥에는 방해 청크가 없다.

근거 청크 고르기
  사슬 문서
    - 문항 기준점(`anchor`)이 작업반 문서(`tdoc:R…`)이면 그 문서
    - 정답 행의 문서 칸(`document`, `final_document`)
    - 문항 근거(`evidence`)의 문서
    - revision_chain 은 기준점과 최종 문서 사이의 판들. 기준점에서 phase-1 `isRevisionOf` 를 거꾸로 이은 뒤
      판들(`build_chain_items.py` 의 `later_versions` 와 같은 관계) 가운데 최종 문서의 조상인 것만 넣는다.
  청크 (dense 가 찾는 세 컬렉션을 옮긴 텍스트 경로 상한 색인에서, 점 개수를 지금 컬렉션과 대조한 뒤 읽는다)
    - evidence: 문항 근거 처분 기록의 결정 청크(`dispositionId` 가운데 칸 = 결정 청크의 `resolutionId`)
    - resolution: 사슬 문서에 대한 결정 청크(`resolutionId` 가 `DOC-{회의}-{문서 번호}-…` 꼴)
    - cr_header: 사슬 문서의 CR 머리 청크(`…-header`). CR 묶음·TSG 회의·규격·절이 메타데이터에 있다.
    - tdoc_first: 사슬 문서의 기고문 청크 가운데 번호가 가장 작은 것(표지)
  CR 본문 청크, 기고문의 나머지 청크, 본문에 문서 번호만 적힌 다른 결정 청크는 넣지 않는다. 고르기 전에 잰 결과
  (답 있는 문항 581개)에서 본문 언급 결정 청크를 더해도 메타데이터 포함 담김 문항이 577개로 같았고 문맥만 커졌다.
  순서: 청크가 속한 문서 번호, 컬렉션(결정 · CR · 기고문, dense 의 컬렉션 순서), 청크 번호(숫자는 수로 비교) 순이다.
  정답 행의 순서는 쓰지 않는다.

두 가지 문맥
  - oracle_evidence: 청크를 dense 와 같은 꼴로 준다(메타데이터 JSON 한 줄 + 본문 앞 1500자).
  - oracle_evidence_textonly: 같은 청크에서 메타데이터를 비운다(`[n] {}` 한 줄 + 본문 앞 1500자).
    CR 묶음 번호(`crPackId`)·TSG 회의는 기록 구축이 총회 기록에서 붙인 메타데이터라서, 이 변형은 본문만으로
    무엇을 읽어 낼 수 있는지를 본다.

담김 (모델 호출 없음, `contexts`)
  `measure_text_route_ceiling.judge` 와 같은 판정이다. 정답 행의 모든 칸이 문맥 글에 문자열로 들어 있으면 담김
  (채점과 같이 대소문자 무시, bis 회의 표기 통일). 두 변형마다 문항별로 담김과 빠진 칸을 남긴다.

문맥 길이
  dense 실행은 `num_ctx` 16384 를 쓴다. 근거 청크가 많은 문항(예: 묶음 하나의 CR 수십 개)은 이보다 길어서,
  문항마다 16384 에서 두 배씩 올려 `--max-context` 까지 가운데 처음으로 "프롬프트 ≤ 문맥 길이의 절반"이 되는
  값을 쓴다. 절반인 까닭은 `chat` 이 출력 길이를 문맥 길이의 절반으로 묶기 때문이다. 이 조건이면 어떤 출력도
  문맥 밖으로 밀려나지 않는다. 프롬프트 토큰 수는 글자 수를 2 로 나눠 어림한다. 숫자·식별자가 빽빽한 이 문맥에서
  잰 비율(약 2.5자/토큰)보다 작게 잡아 토큰을 많게 어림하는 쪽이다. 실제 토큰 수는 응답의 `prompt_eval_count` 로
  기록한다. 그 값이 문맥 길이에 닿으면 ollama 가 프롬프트를 잘랐다는 뜻이고(시험에서 잘린 프롬프트는 정확히
  `num_ctx` 로 보고됐다), 프롬프트와 출력 토큰의 합이 문맥 길이에 닿으면 생성 중에 앞쪽이 밀려난 것이다.
  둘 다 한 단계 올려 다시 풀고, 상한에서도 닿으면 `contextFilled` 에 어느 쪽인지 적는다.
  ollama 는 `num_ctx` 가 바뀔 때 모델을 다시 올리므로 문항을 고른 문맥 길이 순으로 풀고, 같은 문맥 길이
  안에서는 프롬프트가 짧은 문항부터 푼다. 문항마다 호출이 따로라서 푸는 순서는 답에 영향이 없다.

GPU 층 수 고정
  ollama 는 모델을 올릴 때마다 그 순간 보고된 GPU 여유 메모리로 GPU 에 둘 층 수를 어림한다. 16 GB GPU 에서
  qwen2.5:14b 를 32768 문맥으로 올리면 여유 15.2 GiB 일 때 49 층 중 40 층을 두고 풀지만, 15.4 GiB 일 때는 41 층을
  두려다 계산 버퍼를 잡지 못하고(graph_reserve 실패) 러너가 죽어 HTTP 500 이 온다. `--gpu-layers 32768=40` 처럼
  문맥 길이 단계별 층 수를 주면 그 단계의 요청 `options.num_gpu` 에 넣어, 성공한 실행과 같은 배치로 고정한다.
  층 수는 어느 장치에서 계산하느냐는 배치라서 `inputSha256` 에 넣지 않는다. 실제로 보낸 요청은 응답 기록의
  `requestSha256` 에, 고정한 층 수는 시도 기록의 `numGpu` 에 남는다.

응답 상한
  한 호출이 `--timeout` 안에 끝나지 않으면 그 문항은 응답 없이 기록한다(`rows` 와 `response` 가 null,
  `error` = `timeout`, 시도 기록에 `timedOut` = 상한 초). 채점은 읽을 수 없는 응답으로 0점을 준다.
  기록이 있으므로 같은 입력으로 다시 실행해도 그 문항을 다시 부르지 않는다.

이어 풀기
  기록마다 `inputSha256` 을 남긴다. 첫 단계 요청(모델·지시문·문맥 글·ollama 설정, `run_chain_eval.chat_request`
  꼴)과 그 뒤에 오를 수 있는 문맥 길이 단계를 함께 SHA-256 으로 묶은 값이다. 다시 실행하면 문맥을 색인에서 새로
  만들어 같은 값을 다시 계산하고, 저장된 값과 같은 문항만 건너뛴다. 색인을 다시 만들어 청크 본문이나 메타데이터가
  바뀌었거나 질문 문장이 바뀌었으면 값이 달라지므로 그 문항을 다시 푼다. `inputSha256` 이 없는 옛 기록도 다시 푼다.

산출
  contexts: 문항별 근거 청크·담김(`--out` JSONL)과 묶음 요약(`--summary` JSON)
  answer: `run_chain_eval.py` 와 같은 응답 기록(JSONL, `score_chain_eval.py` 로 채점). 입력이 같은 저장 기록은 건너뛰고,
    끝나면 문항마다 마지막 기록 하나만 남긴다.

사용 (저장소 루트에서, `PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark`):
  python3 run_oracle_evidence_reader.py contexts --items <jsonl> [<jsonl> ...] --out <jsonl> --summary <json>
  python3 run_oracle_evidence_reader.py answer --items <jsonl> [<jsonl> ...] --wg RAN1 \
      --variant oracle_evidence --model llama3.1:8b --out <jsonl>
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import statistics
import time
from pathlib import Path

import run_chain_eval
from common.axis import tree_path
from measure_text_route_ceiling import DOC_RE, ROOT, Index, available_gib, guard_memory, judge
from run_chain_eval import DENSE_COLLECTIONS, OLLAMA, question_sha, request_sha, solve_text, text_request
from score_chain_eval import cell_key, meeting_spelling

WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
DOC_FIELDS = ("document", "final_document")
VARIANTS = ("oracle_evidence", "oracle_evidence_textonly")
KINDS = ("evidence", "resolution", "cr_header", "tdoc_first")
HEADER = re.compile(r"-header(?:-\d+)?$")
TEXT_LIMIT = 1500
CHARS_PER_TOKEN = 2.0

_reply: dict = {}
_post = run_chain_eval.post
_timeout = {"seconds": 600}


def _recording_post(url: str, payload: dict, timeout: int | None = None) -> dict:
    """`run_chain_eval.post` 를 그대로 부르고 ollama 응답의 토큰 수만 옆에 적어 둔다. 요청 내용은 바꾸지 않는다.

    응답 대기 상한만 `--timeout` 으로 정한다. 상한은 요청 내용과 모델 출력에 영향이 없다."""
    reply = _post(url, payload, timeout or _timeout["seconds"])
    if url == OLLAMA:
        _reply.clear()
        _reply.update({key: reply.get(key) for key in ("prompt_eval_count", "eval_count", "done_reason")})
    return reply


run_chain_eval.post = _recording_post


def as_list(value) -> list[str]:
    return [] if value is None else value if isinstance(value, list) else [value]


def natural(text: str) -> tuple:
    return tuple(int(part) if part.isdigit() else part for part in re.split(r"(\d+)", text or ""))


def load_items(paths: list[Path]) -> list[dict]:
    return [item for path in paths for item in map(json.loads, path.read_text().splitlines()) if item["gold"]]


class Revisions:
    """phase-1 기고문 기록의 개정 관계. `build_chain_items.py` 가 정답 사슬을 만들 때 읽은 같은 파일이다."""

    def __init__(self, wg: str):
        guard_memory()
        path = tree_path("ontology_instances", wg=wg, phase=1, root=ROOT) / "tdocs.jsonld"
        graph = json.loads(path.read_text())["@graph"]
        self.parents = {record["@id"]: as_list(record.get("isRevisionOf")) for record in graph
                        if "tdoc:tdocNumber" in record}
        self.successors: dict[str, list[str]] = collections.defaultdict(list)
        for identifier, parents in self.parents.items():
            for earlier in parents:
                self.successors[earlier].append(identifier)

    def between(self, anchor: str, final: str) -> list[str]:
        """기준점의 뒤 판들 가운데 최종 문서의 조상인 것(두 끝 제외)."""
        later, queue = set(), list(self.successors.get(f"tdoc:{anchor}", ()))
        while queue:
            current = queue.pop(0)
            if current not in later:
                later.add(current)
                queue.extend(self.successors.get(current, ()))
        ancestors, queue = set(), list(self.parents.get(f"tdoc:{final}", ()))
        while queue:
            current = queue.pop(0)
            if current not in ancestors and current != f"tdoc:{anchor}":
                ancestors.add(current)
                queue.extend(self.parents.get(current, ()))
        return sorted((identifier.split(":", 1)[1] for identifier in later & ancestors), key=natural)


def chain_documents(item: dict, revisions: Revisions | None) -> tuple[list[str], list[str]]:
    docs = []
    if item["anchor"].startswith("tdoc:R"):
        docs.append(item["anchor"].split(":", 1)[1])
    for row in item["gold"]:
        docs += [value for field, value in zip(item["fields"], row) if field in DOC_FIELDS]
    docs += [entry["document"] for entry in item["evidence"]]
    between = []
    if item["family"] == "revision_chain":
        anchor = item["anchor"].split(":", 1)[1]
        for row in item["gold"]:
            between += revisions.between(anchor, row[item["fields"].index("final_document")])
    return list(dict.fromkeys(docs)), list(dict.fromkeys(between))


def oracle_chunks(item: dict, index: Index, revisions: Revisions | None) -> dict:
    wg = item["wg"].lower()
    docs, between = chain_documents(item, revisions)
    kind_of: dict[int, str] = {}

    def add(ids, kind: str) -> None:
        for row_id in ids:
            kind_of.setdefault(row_id, kind)

    for resolution in dict.fromkeys(entry["dispositionId"].split(":")[1] for entry in item["evidence"]):
        add((row[0] for row in index.con.execute(
            "SELECT id FROM docs WHERE collection = ? AND chunk_id >= ? AND chunk_id < ?",
            (f"{wg}_resolution_chunks", resolution + "#", resolution + "$"))), "evidence")
    for doc in docs + between:
        add(index.resolution_documents().get(doc, set()), "resolution")
        rows = index.con.execute("SELECT id, collection, chunk_id FROM docs WHERE tdoc = ?", (doc,)).fetchall()
        add((row_id for row_id, collection, chunk_id in rows
             if collection == f"{wg}_cr_chunks" and HEADER.search(chunk_id or "")), "cr_header")
        first = min(((natural(chunk_id), row_id) for row_id, collection, chunk_id in rows
                     if collection == f"{wg}_tdoc_chunks"), default=None)
        if first:
            add([first[1]], "tdoc_first")
    found = index.fetch(kind_of)
    rank = {f"{wg}_{suffix}": position for position, suffix in enumerate(DENSE_COLLECTIONS)}

    def order(row_id: int) -> tuple:
        chunk = found[row_id]
        match = DOC_RE.search(chunk["doc"])
        return (natural(match.group(0).upper() if match else chunk["doc"]), rank[chunk["collection"]],
                natural(chunk["chunkId"]))

    chunks = [{**found[row_id], "kind": kind_of[row_id]} for row_id in sorted(found, key=order)]
    return {"documents": docs, "revisionIntermediates": between, "chunks": chunks}


def variant_chunks(chunks: list[dict], variant: str) -> list[dict]:
    """`solve_text` 가 받는 청크 꼴. 메타데이터는 dense 의 `retrieve` 가 붙이는 키와 같다(색인이 같은 키만 담는다)."""
    keep = variant == "oracle_evidence"
    return [{"collection": chunk["collection"], "chunkId": chunk["chunkId"], "score": None,
             "text": chunk["text"], "meta": json.loads(chunk["metaJson"]) if keep else {}} for chunk in chunks]


def containment(chunks: list[dict], item: dict, variant: str) -> dict:
    shown = chunks if variant == "oracle_evidence" else [{**chunk, "metaJson": "{}"} for chunk in chunks]
    result = judge(shown, TEXT_LIMIT, item)
    context = "\n".join(meeting_spelling((chunk["metaJson"] + "\n" + chunk["text"][:TEXT_LIMIT]).lower())
                        for chunk in shown)
    result["missingCells"] = sorted({(field, cell) for row in item["gold"] for field, cell in zip(item["fields"], row)
                                     if cell_key(cell) not in context})
    return result


def summarize(records: list[dict]) -> dict:
    def group(selected: list[dict]) -> dict:
        out = {"n": len(selected)}
        for variant in VARIANTS:
            rows = [record["containment"][variant]["rows"] for record in selected]
            out[variant] = {"allRows": sum("missing" not in r for r in rows),
                            "anyRow": sum(any(x != "missing" for x in r) for r in rows)}
        chunks = [record["chunkCount"] for record in selected]
        chars = [record["containment"]["oracle_evidence"]["chars"] for record in selected]
        out.update(chunksMedian=statistics.median(chunks), chunksMax=max(chunks),
                   charsMedian=statistics.median(chars), charsMax=max(chars))
        return out

    groups = [{"by": "all", "value": "all", **group(records)}]
    for key in ("wg", "family"):
        for value in sorted({record[key] for record in records}):
            groups.append({"by": key, "value": value, **group([r for r in records if r[key] == value])})
    for wg, family in sorted({(record["wg"], record["family"]) for record in records}):
        groups.append({"by": "wg×family", "value": f"{wg}|{family}",
                       **group([r for r in records if r["wg"] == wg and r["family"] == family])})
    fields: dict = {}
    for family in sorted({record["family"] for record in records}):
        selected = [record for record in records if record["family"] == family]
        names, total = selected[0]["fields"], sum(record["goldRows"] for record in selected)
        fields[family] = {variant: {name: round(sum(record["containment"][variant]["fieldsHeld"][position]
                                                    for record in selected) / total, 4)
                                    for position, name in enumerate(names)} for variant in VARIANTS}
    kinds = collections.Counter(kind for record in records for kind, n in record["kindCounts"].items()
                                for _ in range(n))
    return {"groups": groups, "fieldHeldRate": fields, "chunksByKind": dict(kinds),
            "revisionIntermediates": sum(len(record["revisionIntermediates"]) for record in records)}


def build_contexts(items: list[dict], out: Path, summary: Path) -> None:
    records, live = [], {}
    for wg in WGS:
        selected = [item for item in items if item["wg"] == wg]
        if not selected:
            continue
        index = Index(wg)
        live[wg] = index.check_counts()
        revisions = Revisions(wg) if any(item["family"] == "revision_chain" for item in selected) else None
        started = time.time()
        for item in selected:
            oracle = oracle_chunks(item, index, revisions)
            chunks = oracle["chunks"]
            records.append({
                "id": item["id"], "questionSha256": question_sha(item), "wg": wg, "family": item["family"],
                "fields": item["fields"], "goldRows": len(item["gold"]), "documents": oracle["documents"],
                "revisionIntermediates": oracle["revisionIntermediates"], "chunkCount": len(chunks),
                "kindCounts": dict(collections.Counter(chunk["kind"] for chunk in chunks)),
                "chunks": [{key: chunk[key] for key in ("collection", "chunkId", "kind")} for chunk in chunks],
                "containment": {variant: containment(chunks, item, variant) for variant in VARIANTS}})
        print(json.dumps({"wg": wg, "items": len(selected), "seconds": round(time.time() - started, 1),
                          "availableGiB": round(available_gib(), 1)}), flush=True)
        index.con.close()
        del revisions
    out.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records))
    report = {"items": len(records), "textLimit": TEXT_LIMIT, "liveCounts": live,
              "metric": "정답 행의 모든 칸이 문맥 글(청크마다 메타데이터 JSON + 본문 앞 1500자; textonly 는 메타데이터 `{}`)에 "
                        "들어 있으면 담김. 대소문자 무시, bis 회의 표기 통일. allRows=모든 행 담김, anyRow=한 행 이상 담김.",
              **summarize(records)}
    summary.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    head = report["groups"][0]
    print(json.dumps({variant: head[variant] for variant in VARIANTS} | {"n": head["n"]}, ensure_ascii=False))


def ladder(base: int, top: int) -> list[int]:
    values = [base]
    while values[-1] * 2 <= top:
        values.append(values[-1] * 2)
    return values


def prompt_chars(request: dict) -> int:
    """요청이 보내는 시스템·사용자 메시지 글자 수. `text_request` 가 만든 요청을 그대로 센다."""
    return sum(len(message["content"]) for message in request["messages"])


def input_sha(request: dict, steps: list[int]) -> str:
    """첫 단계 요청과 오를 수 있는 문맥 길이 단계를 묶은 해시. 같으면 같은 호출 순서가 다시 일어난다."""
    return request_sha({"firstRequest": request, "ladder": steps})


def filled(attempt: dict) -> str | None:
    """문맥이 찼는지. 프롬프트가 잘렸으면 `prompt`, 프롬프트와 출력의 합이 문맥 길이에 닿았으면 `output`.

    ollama 는 문맥 길이를 넘는 프롬프트를 앞부분만 남기고 자르고 그 프롬프트 토큰 수를 문맥 길이로 보고한다.
    생성 중에 문맥이 차면 앞쪽 토큰을 버리고 이어 쓴다. 어느 쪽이든 모델이 근거 일부를 못 본 채 답한 것이다.
    """
    prompt, output = attempt["prompt_eval_count"] or 0, attempt["eval_count"] or 0
    if prompt >= attempt["numCtx"]:
        return "prompt"
    return "output" if prompt + output >= attempt["numCtx"] else None


def answer(args) -> None:
    items = [item for item in load_items(args.items) if item["wg"] == args.wg]
    current = {item["id"] for item in items}
    stored: dict[str, dict] = {}
    if args.out.exists():
        for line in args.out.read_text().splitlines():
            record = json.loads(line)
            stored[record["id"]] = record
    index = Index(args.wg)
    index.check_counts()
    revisions = Revisions(args.wg) if any(item["family"] == "revision_chain" for item in items) else None
    steps = ladder(args.context, args.max_context)
    plan, reused = [], 0
    for item in items:
        chunks = variant_chunks(oracle_chunks(item, index, revisions)["chunks"], args.variant)
        chars = prompt_chars(text_request(item, args.model, steps[0], chunks))
        need = chars / CHARS_PER_TOKEN
        start = next((position for position, value in enumerate(steps) if need <= value // 2), len(steps) - 1)
        key = input_sha(text_request(item, args.model, steps[start], chunks), steps[start:])
        previous = stored.get(item["id"])
        if previous is not None and previous.get("questionSha256") == question_sha(item) \
                and previous.get("inputSha256") == key:
            reused += 1
            continue
        stored.pop(item["id"], None)
        plan.append((start, item, chunks, chars, key))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in stored.values()))
    plan.sort(key=lambda entry: (entry[0], entry[3]))
    with args.out.open("a") as out:
        for position, (start, item, chunks, chars, key) in enumerate(plan, 1):
            guard_memory()
            started, attempts = time.time(), []
            for step in steps[start:]:
                request = text_request(item, args.model, step, chunks)
                pinned = {"numGpu": args.gpu_layers[step]} if step in args.gpu_layers else {}
                if pinned:
                    request["options"]["num_gpu"] = pinned["numGpu"]
                try:
                    result = solve_text(request, chunks)
                except TimeoutError:
                    result = {"rows": None, "response": None, "error": "timeout"}
                    attempts.append({"numCtx": step, **pinned, "timedOut": _timeout["seconds"]})
                    break
                attempts.append({"numCtx": step, **pinned, **{name: _reply.get(name) for name in
                                                              ("prompt_eval_count", "eval_count", "done_reason")}})
                if filled(attempts[-1]) is None:
                    break
            last = attempts[-1]
            record = {"id": item["id"], "questionSha256": question_sha(item), "inputSha256": key,
                      "wg": item["wg"], "family": item["family"], "method": args.variant, "model": args.model,
                      "seconds": round(time.time() - started, 1), **result,
                      "oracle": {"promptChars": chars, "numCtx": last["numCtx"], "attempts": attempts,
                                 "contextFilled": None if "timedOut" in last else filled(last)}}
            stored[item["id"]] = record
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            if position % 20 == 0 or position == len(plan):
                print(json.dumps({"wg": args.wg, "variant": args.variant, "model": args.model, "done": position,
                                  "of": len(plan), "numCtx": last["numCtx"], "lastSeconds": record["seconds"],
                                  "availableGiB": round(available_gib(), 1)}), flush=True)
    args.out.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in stored.values()))
    print(json.dumps({"wg": args.wg, "variant": args.variant, "model": args.model, "items": len(items),
                      "reused": reused, "answered": len(plan),
                      "otherRecords": sum(1 for name in stored if name not in current)}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    ctx = sub.add_parser("contexts", help="근거 청크를 고르고 두 변형의 담김을 센다(모델 호출 없음)")
    ctx.add_argument("--items", type=Path, nargs="+", required=True)
    ctx.add_argument("--out", type=Path, required=True, help="문항별 근거 청크와 담김(JSONL)")
    ctx.add_argument("--summary", type=Path, required=True, help="묶음별 담김 요약(JSON)")
    run = sub.add_parser("answer", help="근거 청크 문맥으로 독해 모델을 부른다")
    run.add_argument("--items", type=Path, nargs="+", required=True)
    run.add_argument("--wg", required=True, choices=WGS)
    run.add_argument("--variant", required=True, choices=VARIANTS)
    run.add_argument("--model", required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--context", type=int, default=16384, help="첫 문맥 길이(dense 실행과 같은 값)")
    run.add_argument("--max-context", type=int, default=32768,
                     help="문맥 길이 상한. qwen2.5:14b 가 배운 문맥 길이이고, 16 GB GPU 에서 llama3.1:8b 를 65536 으로 "
                          "올리면 ollama 가 계산 버퍼를 잡지 못하고 멈춘다(graph_reserve 실패). 두 모델에 같은 상한을 쓴다")
    run.add_argument("--timeout", type=int, default=600,
                     help="ollama 응답 대기 상한(초). 16 GB GPU 에서 qwen2.5:14b 를 32768 문맥으로 부르면 모델 일부가 "
                          "CPU 로 내려가 한 호출이 600초를 넘을 수 있다")
    run.add_argument("--gpu-layers", nargs="*", default=[], metavar="CTX=N",
                     help="문맥 길이 단계별로 GPU 에 둘 층 수(ollama num_gpu). 예: 32768=40. 주지 않은 단계는 ollama 가 정한다")
    args = parser.parse_args()
    if args.command == "answer":
        _timeout["seconds"] = args.timeout
        pins = dict(entry.split("=", 1) for entry in args.gpu_layers)
        args.gpu_layers = {int(context): int(layers) for context, layers in pins.items()}
        unknown = set(args.gpu_layers) - set(ladder(args.context, args.max_context))
        if unknown:
            raise SystemExit(f"--gpu-layers 의 문맥 길이가 단계에 없다: {sorted(unknown)}")
    if args.command == "contexts":
        build_contexts(load_items(args.items), args.out, args.summary)
    else:
        answer(args)


if __name__ == "__main__":
    main()
