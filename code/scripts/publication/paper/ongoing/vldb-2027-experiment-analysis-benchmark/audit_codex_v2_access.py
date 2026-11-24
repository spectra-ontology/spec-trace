"""Codex 재실행(값 영역 묶음 · 읽기 전용 탐색) 기록에서 작업 폴더 밖에 닿은 흔적을 모두 표시한다 (모델 호출 없음).

`audit_codex_query_writer_access.py` 의 방식을 넓혔다. 실행마다 다음을 본다.

1. events.jsonl 의 항목을 id 로 모아(완료 항목 우선) 실행 명령 · 파일 변경 · 그 밖의 도구 호출(웹 검색 · MCP 등)을 꺼낸다.
2. 명령과, 작업 폴더에 남은 새 파일(풀이 스크립트 · 결과 파일)의 내용에서 다음을 찾는다.
   - 작업 폴더 밖의 절대경로(명령을 감싸는 `/bin/bash -lc` 와 `/dev/null` 등 표준 입출력 장치는 뺀다)
   - 상위 폴더(`..`) · 홈 폴더(`~`, `$HOME`, `expanduser`, `Path.home`)
   - 네트워크 · 데이터베이스 접속 낱말(curl · wget · ssh · http · socket · urllib · requests · neo4j · bolt · 그래프 ·
     벡터 서버 포트 · docker · cypher-shell)과 database.sqlite 가 아닌 데이터베이스 파일
   - 저장소 · 정답 낱말(gold · items_final · chain_items · logs/ · scripts/ · credentials · spectra · sigir)
   그래프 탐색 실행의 도우미 호출(`query_graph.py`)과 관계형 탐색 실행의 database.sqlite 는 허용 목록이다.
3. 파일 변경 경로가 작업 폴더 밖이면 표시하고, 만들었다가 지워 내용을 볼 수 없는 파일을 따로 적는다.
4. 같은 폴더 안이지만 지시에 없던 동작(목록 보기 · 도우미 파일 읽기)은 참고 항목으로 따로 적는다.
5. 무결성: 관계형 사본의 sha256 실행 전후 · 원본 일치, 그래프의 노드 · 관계 수 실행 전후 일치, 중계 서버 기록의 요약.

사용: python3 audit_codex_v2_access.py --records <run_records> --work <작업 폴더 뿌리> --sqlite-dir <dir> --out <json>
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path

ALLOWED_ABSOLUTE = {"/bin/bash", "/dev/null", "/dev/stdin", "/dev/stdout", "/dev/stderr", "/usr/bin/env",
                    "/usr/bin/python3", "/bin/sh"}
ABSOLUTE = re.compile(r"(?<![\w.:/-])/(?:[\w.+@-]+/)*[\w.+@-]+/?")
PARENT = re.compile(r"(?:^|[\s'\"=(,/])\.\.(?:/|$|[\s'\")])")
HOME = re.compile(r"(?:^|[\s'\"=(])~(?:/|[\s'\")]|$)|\$\{?HOME\b|expanduser|Path\.home", re.M)
NETWORK = re.compile(r"\b(curl|wget|ssh|scp|ncat|telnet|nc|socket|urllib|requests|httpx|aiohttp|neo4j|bolt|"
                     r"cypher-shell|docker|qdrant)\b|https?://|\b(7474|7687|7688|7689|7690|7691|7692|6333|6334)\b", re.I)
DATABASE_FILE = re.compile(r"[\w./-]*\.(?:sqlite3?|db)\b", re.I)
REPOSITORY = re.compile(r"\b(gold|items_final|chain_items\w*|credentials|spectra|sigir)\b|\b(?:logs|scripts)/", re.I)
LISTING = re.compile(r"(?:^|[;&|\s(])(ls|find|tree|du)(?:\s|$)|os\.listdir|os\.walk|os\.scandir|\bglob\b|iterdir", re.M)
HELPER_READ = re.compile(r"(?:cat|less|more|head|tail|sed|awk|grep|open\(|read_text)\W[^\n]*query_graph\.py")


def items_of(events: Path) -> tuple[list[dict], dict]:
    """item id 마다 마지막(완료가 있으면 완료) 상태를 돌려준다."""
    found, meta = {}, {"eventKinds": collections.Counter(), "usage": None, "thread": None}
    for line in events.read_text(errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            meta["eventKinds"]["unparsed"] += 1
            continue
        meta["eventKinds"][event.get("type")] += 1
        if event.get("type") == "thread.started":
            meta["thread"] = event.get("thread_id")
        if event.get("type") == "turn.completed":
            meta["usage"] = event.get("usage")
        item = event.get("item")
        if isinstance(item, dict) and item.get("id"):
            if event.get("type") == "item.completed" or item["id"] not in found:
                found[item["id"]] = item
    meta["eventKinds"] = dict(meta["eventKinds"])
    return list(found.values()), meta


def unwrap(command: str) -> str:
    match = re.match(r"^/bin/(?:ba)?sh -l?c (['\"])(.*)\1$", command, re.S)
    return match.group(2) if match else command


def findings(text: str, workdir: str, condition: str, language: str) -> dict:
    """한 덩어리의 글(명령 · 파일 내용)에서 작업 폴더 밖을 가리키는 흔적을 낱말별로 모은다."""
    out = collections.defaultdict(list)
    for match in ABSOLUTE.finditer(text):
        path = match.group(0).rstrip("/")
        if path in ALLOWED_ABSOLUTE or path == workdir or path.startswith(workdir + "/"):
            continue
        out["absolutePath"].append(path)
    # 작업 폴더 경로 자체에 든 낱말(임시 폴더 이름)은 밖을 가리키는 흔적이 아니므로 지우고 나머지 낱말을 찾는다.
    text = text.replace(workdir, "<workdir>")
    if PARENT.search(text):
        out["parentDirectory"].append(PARENT.search(text).group(0).strip())
    out["home"] += [m.group(0).strip() for m in HOME.finditer(text)]
    allowed_db = {"database.sqlite"} if (condition, language) == ("exp", "sql") else set()
    out["databaseFile"] += [m.group(0) for m in DATABASE_FILE.finditer(text)
                            if m.group(0).lstrip("./") not in allowed_db]
    out["network"] += [m.group(0) for m in NETWORK.finditer(text)]
    out["repository"] += [m.group(0) for m in REPOSITORY.finditer(text)]
    return {key: sorted(set(values))[:20] for key, values in out.items() if values}


def snippet(text: str, limit: int = 400) -> str:
    return text if len(text) <= limit else text[:limit] + f"... [{len(text)} chars]"


def audit_run(record_dir: Path, workdir: Path, run: dict, sqlite_dir: Path) -> dict:
    name, condition, language = run["name"], run["condition"], run["language"]
    items, meta = items_of(record_dir / "events.jsonl")
    kinds = collections.Counter(item.get("type") for item in items)
    commands = [item for item in items if item.get("type") == "command_execution"]
    flagged, notes = [], []
    for item in commands:
        text = unwrap(item.get("command", ""))
        hits = findings(text, str(workdir), condition, language)
        if hits:
            flagged.append({"where": "command", "id": item["id"], "hits": hits, "command": snippet(text)})
        if LISTING.search(text):
            notes.append({"kind": "listing", "id": item["id"], "command": snippet(text, 200)})
        if HELPER_READ.search(text):
            notes.append({"kind": "helperRead", "id": item["id"], "command": snippet(text, 200)})
    changed_paths = []
    for item in items:
        if item.get("type") == "file_change":
            for change in item.get("changes") or []:
                path = str(change.get("path", ""))
                changed_paths.append((path, change.get("kind")))
                inside = (not path.startswith("/") and ".." not in Path(path).parts) or \
                    path == str(workdir) or path.startswith(str(workdir) + "/")
                if not inside:
                    flagged.append({"where": "file_change", "id": item["id"], "path": path, "kind": change.get("kind")})
    other_tools = [{"id": item["id"], "type": item.get("type"), "detail": snippet(json.dumps(item, ensure_ascii=False))}
                   for item in items if item.get("type") not in
                   ("command_execution", "file_change", "agent_message", "reasoning", "todo_list")]
    flagged += [{"where": "tool", **tool} for tool in other_tools]

    def table(path: Path) -> dict:
        return dict(line.split("\t") for line in path.read_text().splitlines() if line)

    before, after = table(record_dir / "workdir_before.tsv"), table(record_dir / "workdir_after.tsv")
    created = sorted(set(after) - set(before))
    scanned = {}
    for relative in created:
        copy = record_dir / "workdir" / relative
        if not copy.exists():
            continue
        text = copy.read_text(errors="replace")
        hits = findings(text, str(workdir), condition, language)
        scanned[relative] = {"bytes": len(text.encode()), "hits": hits}
        if hits and relative != "queries.jsonl":
            flagged.append({"where": "created_file", "path": relative, "hits": hits})
    changed_inside = {str(Path(p).relative_to(workdir)) if p.startswith(str(workdir) + "/") else p
                      for p, _ in changed_paths}
    unscannable = sorted(p for p in changed_inside if p not in after)
    modified_inputs = sorted(p for p in set(before) & set(after) if before[p] != after[p])

    integrity: dict = {}
    if (condition, language) == ("exp", "sql"):
        original = hashlib.sha256((sqlite_dir / f"{run['wg']}.sqlite").read_bytes()).hexdigest()
        integrity = {"originalSha256": original, "copyBefore": run["before"], "copyAfter": run["after"],
                     "unchanged": run["before"] == run["after"] == original}
    if (condition, language) == ("exp", "cy"):
        log = [json.loads(line) for line in (record_dir / "proxy_log.jsonl").read_text().splitlines() if line] \
            if (record_dir / "proxy_log.jsonl").exists() else []
        statuses = collections.Counter(entry["status"] for entry in log)
        integrity = {"graphBefore": run["before"], "graphAfter": run["after"],
                     "unchanged": run["before"] == run["after"],
                     "proxyRequests": len(log), "proxyStatuses": dict(statuses),
                     "proxyTruncated": sum(1 for entry in log if entry.get("truncated")),
                     "proxyTimeouts": sum(1 for entry in log if "TimedOut" in str(entry.get("error", ""))),
                     "proxyRejectedReasons": dict(collections.Counter(entry["reason"] for entry in log
                                                                      if entry["status"] == "rejected")),
                     "proxyMaxSeconds": max((entry["seconds"] for entry in log), default=None)}
    return {"name": name, "workdir": workdir.name, "thread": meta["thread"], "usage": meta["usage"],
            "eventKinds": meta["eventKinds"], "itemKinds": dict(kinds), "nCommands": len(commands),
            "workdirBefore": sorted(before), "workdirAfter": sorted(after), "created": created,
            "modifiedInputs": modified_inputs, "unscannableDeletedFiles": unscannable,
            "createdFileScan": scanned, "integrity": integrity,
            "flagged": flagged, "notes": notes, "outsideWorkdir": bool(flagged)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--sqlite-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    runs = [json.loads(line) for line in (args.records / "runs.jsonl").read_text().splitlines() if line]
    latest = {run["name"]: run for run in runs}
    results = [audit_run(args.records / name, args.work / name, run, args.sqlite_dir)
               for name, run in sorted(latest.items())]
    report = {"method": __doc__.split("\n")[0], "runs": results,
              "summary": {"runs": len(results), "runsWithFlags": [r["name"] for r in results if r["outsideWorkdir"]],
                          "flagCounts": {r["name"]: len(r["flagged"]) for r in results if r["flagged"]},
                          "noteCounts": {r["name"]: dict(collections.Counter(n["kind"] for n in r["notes"]))
                                         for r in results if r["notes"]},
                          "integrityFailures": [r["name"] for r in results
                                                if r["integrity"] and not r["integrity"]["unchanged"]],
                          "modifiedInputs": {r["name"]: r["modifiedInputs"] for r in results if r["modifiedInputs"]},
                          "unscannableDeletedFiles": {r["name"]: r["unscannableDeletedFiles"]
                                                      for r in results if r["unscannableDeletedFiles"]}}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(report["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
