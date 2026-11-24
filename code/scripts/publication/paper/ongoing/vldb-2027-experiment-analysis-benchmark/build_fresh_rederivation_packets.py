"""앞선 재유도에 한 번도 들어가지 않은 문항으로 새 재유도 표본과 Codex 풀이 묶음·지시문을 만든다 (모델 호출 없음).

앞선 재유도 라운드의 묶음·답·결과 파일(`--previous` 로 준 폴더 바로 아래의 *.json · *.jsonl)에 나온 문항 id 를
모두 모아 제외 목록으로 둔다. 파일 안의 `id` 키 값과, 문항 id 와 똑같은 문자열 값을 모두 문항 id 로 센다.
남은 문항에서 작업반·문항 종류 칸마다 `--per-cell` 개를 고른다. 고르는 순서는 `build_text_search_packets.order_key()`
(`--seed` 와 문항 id 를 이은 글의 SHA-256)라 문항 파일의 줄 순서와 무관하다. 칸에 남은 문항이 모자라면 있는 만큼
고르고 모자란 수를 `shortfall` 로 적는다.

묶음 줄에는 묶음 id(`run_chain_eval.packet_id()`)·작업반·질문·요청 필드만 싣고 묶음 id 차례로 놓는다. 정답·근거·
문항 종류는 싣지 않는다. 지시문은 앞선 재유도 풀이 지시문과 같은 기록 목록·답 형식·표기 규칙을 쓰되, 경로는
Codex 작업 폴더 안의 상대경로로 바꾸고 작업 폴더 밖을 읽지 말라는 규칙을 더한다. 작업반마다 작업 폴더에 둘
기록 파일 목록(`records` 아래 상대경로 → 저장소 상대경로)을 `record_files.json` 에 적는다.

사용 (저장소 루트에서 `PYTHONPATH=scripts/common:<이 폴더>`):
  python3 build_fresh_rederivation_packets.py --items <admitted.jsonl> [...] --previous <dir> [...] \
      --per-cell 4 --seed fresh-codex-rederivation --out-dir <dir>
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from build_text_search_packets import order_key
from run_chain_eval import item_ids, packet_id, packet_order

INSTANCES = "ontology/output/tsg/RAN/formal/instances"
RAN5_EXPORT = "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/RAN5_graph_export/RAN5"
# 앞선 재유도 지시문이 작업반마다 보기로 든 문서 번호·작업반 회의 표기. RAN5 지시문만 전자 회의의 정식 회의 번호
# (`RAN5#90`, 기록의 meetingNumber 는 `RAN5#90-e`)를 들었고 나머지 넷은 meetingNumber 그대로(`-e` 포함)를 들었다.
# 이 묶음에서는 다섯 작업반 모두 기록의 meetingNumber 값을 그대로 보기로 든다.
EXAMPLES = {"RAN1": ("R1-2205027", "RAN1#102-e"), "RAN2": ("R2-2205027", "RAN2#110-e"),
            "RAN3": ("R3-205027", "RAN3#110-e"), "RAN4": ("R4-2205027", "RAN4#102-e"),
            "RAN5": ("R5-205027", "RAN5#90-e")}
PHASE2_RESOLUTIONS = {"RAN5": ("resolutions_document_dispositions.jsonld", "resolutions_conclusions.jsonld",
                               "discussions.jsonld")}
DEFAULT_RESOLUTIONS = ("resolutions_document_dispositions.jsonld", "resolutions_agreements.jsonld",
                       "resolutions_conclusions.jsonld", "resolutions_working_assumptions.jsonld")
PHASE4_FILES = ("crpacks.jsonld", "section_extensions.jsonld", "cr_extensions.jsonld")

PROMPT = """You are an independent solver in a validity check of a question set. Answer {n} questions about the 3GPP {wg} standardization process using ONLY the record files in the current working directory. The purpose is to test whether each question SENTENCE alone determines its answer, so independence matters more than anything else.

Hard rules:
- Read only files inside the current working directory: `questions.jsonl` and the files under `records/`. Do not open, list or search any path outside this directory (no parent directories, no home directory, no other temporary folders, no absolute paths), even when a record mentions another path. Do not use the web, a database (no Neo4j, no Qdrant, no SQLite), or any model/API service. Do not start or stop any service or container. Do not create or modify any file except `answers.jsonl` and helper scripts under `work/` in this directory. No git operations.
- If a question sentence can reasonably be read in more than one way, pick the reading you find most natural, answer under it, and describe the alternative in the `note` field. Do not guess what an answer key would say.
- Report honestly; if you cannot determine an answer, say so in `note` and give your best rows. Use only values found in the records; never fill from your own knowledge.

Questions: `questions.jsonl` (each line: id, wg, question, fields — `fields` is the column order of each answer row).

Record files (JSON-LD, top-level key `@graph` is a list of records; explore their keys yourself with small Python snippets):
- Documents (TDocs, CRs; includes revision links, target release, list status fields): `records/phase-1/tdocs.jsonld` (the other files in `records/phase-1/`, e.g. meetings, may also be read)
- Decision events with their meeting: {resolutions}
- Disposition records (one per decision event and target document; carry a disposition code, an evidence status, and an assessment method that states the scope): `records/phase-2/decision_dispositions.jsonld`{size_note}
- Plenary CR packs and their member CRs: `records/phase-4/crpacks.jsonld`
- Specification clauses and the CRs that modify them, and CR-side extensions: `records/phase-4/section_extensions.jsonld`, `cr_extensions.jsonld` (same directory){manifest_note}

Answer format conventions (the same ones given to every solver): copy document numbers, meeting names and clause numbers exactly as the records write them, in the forms {tdoc} (document), {meeting} (working-group meeting), RP-221234 (CR pack), RAN#96 (plenary meeting), 6.2.1 (clause). Disposition values are the lower-case codes found in the records (agreed, revised, noted, endorsed, withdrawn, not_pursued, ...). If the records hold no such row, the answer is an empty row list.

Practical: files are up to several hundred MB; check `free -h` first, load one file at a time with Python `json`, keep only what you need, and do not run more than one heavy process at once (the machine is shared with other jobs; if available memory is under 10 GiB, process the file in a streaming or reduced way rather than loading it whole). Put any helper scripts under `work/`. Keep command output short (head/cut).

Output: write `answers.jsonl` in this directory, one line per question: {{"id": <id>, "rows": [[...], ...], "note": "<ambiguities or difficulties, empty string if none>"}}. Rows are lists of strings in the `fields` order; include every row the question asks for, no duplicates.

Final message: for each id, the number of rows and any ambiguity you noted, plus a one-paragraph description of how you interpreted the record structure. Do not claim correctness — you cannot know it.
"""


def load_items(paths: list[Path]) -> dict[str, dict]:
    items = [json.loads(line) for path in paths for line in path.read_text().splitlines() if line.strip()]
    return {item["id"]: item for item in items}


def ids_in(value, known: set[str], found: set[str]) -> None:
    if isinstance(value, dict):
        for name, inner in value.items():
            if name == "id" and isinstance(inner, str):
                found.add(inner)
            ids_in(inner, known, found)
    elif isinstance(value, list):
        for inner in value:
            ids_in(inner, known, found)
    elif isinstance(value, str) and value in known:
        found.add(value)


def previous_ids(folders: list[Path], known: set[str]) -> tuple[set[str], list[dict]]:
    """앞선 라운드 파일에 나온 문항 id 와 파일별 개수. 문항 집합에 없는 id 는 따로 센다."""
    union: set[str] = set()
    per_file = []
    for folder in folders:
        for path in sorted([*folder.glob("*.json"), *folder.glob("*.jsonl")]):
            found: set[str] = set()
            if path.suffix == ".jsonl":
                for line in path.read_text().splitlines():
                    if line.strip():
                        ids_in(json.loads(line), known, found)
            else:
                ids_in(json.loads(path.read_text()), known, found)
            per_file.append({"path": str(path), "itemIds": len(found & known), "otherIds": sorted(found - known)})
            union |= found & known
    return union, per_file


def record_files(wg: str) -> dict[str, str]:
    """작업 폴더 `records/` 아래 상대경로 → 저장소 상대경로. phase-1 은 폴더의 기록 파일(*.jsonld)을 모두 두고,
    같은 폴더의 빌드 로그(*.txt)는 기록이 아니므로 두지 않는다."""
    table = {f"phase-1/{path.name}": str(path) for path in sorted(Path(f"{INSTANCES}/phase-1/{wg}").glob("*.jsonld"))}
    for name in (*PHASE2_RESOLUTIONS.get(wg, DEFAULT_RESOLUTIONS), "decision_dispositions.jsonld"):
        table[f"phase-2/{name}"] = f"{INSTANCES}/phase-2/{wg}/{name}"
    phase4 = RAN5_EXPORT if wg == "RAN5" else f"{INSTANCES}/phase-4/{wg}"
    for name in (*PHASE4_FILES, *(("export_manifest.json",) if wg == "RAN5" else ())):
        table[f"phase-4/{name}"] = f"{phase4}/{name}"
    missing = [source for source in table.values() if not Path(source).is_file()]
    if missing:
        raise SystemExit(f"{wg}: 기록 파일이 없다: {missing}")
    return table


def prompt(wg: str, n: int) -> str:
    names = PHASE2_RESOLUTIONS.get(wg, DEFAULT_RESOLUTIONS)
    others = ", ".join(f"`{name}`" for name in names[1:-1])
    resolutions = (f"`records/phase-2/{names[0]}`, plus {others} and `{names[-1]}` in that same directory"
                   if others else f"`records/phase-2/{names[0]}`, plus `{names[-1]}` in that same directory")
    size = Path(f"{INSTANCES}/phase-2/{wg}/decision_dispositions.jsonld").stat().st_size
    size_note = (f" (about {round(size / 1e6)} MB — load it alone, and drop it from memory after extracting what you need)"
                 if size > 300e6 else "")
    manifest_note = "; you may also read `export_manifest.json` there" if wg == "RAN5" else ""
    tdoc, meeting = EXAMPLES[wg]
    return PROMPT.format(n=n, wg=wg, resolutions=resolutions, size_note=size_note, manifest_note=manifest_note,
                         tdoc=tdoc, meeting=meeting)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--previous", type=Path, nargs="+", required=True, help="앞선 재유도 라운드 폴더")
    parser.add_argument("--per-cell", type=int, required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    items = load_items(args.items)
    excluded, per_file = previous_ids(args.previous, set(items))
    cells: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for item in items.values():
        cells[(item["wg"], item["family"])].append(item)
    chosen: dict[str, list[dict]] = collections.defaultdict(list)
    cell_report = []
    for (wg, family), members in sorted(cells.items()):
        unused = [item for item in members if item["id"] not in excluded]
        picked = sorted(unused, key=lambda item: order_key(args.seed, item["id"]))[:args.per_cell]
        chosen[wg] += picked
        cell_report.append({"wg": wg, "family": family, "items": len(members), "excluded": len(members) - len(unused),
                            "unused": len(unused), "chosen": len(picked), "shortfall": args.per_cell - len(picked),
                            "ids": [item["id"] for item in picked]})
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "invocation").mkdir(exist_ok=True)
    files = {}
    for wg, members in sorted(chosen.items()):
        item_ids(members)
        lines = [json.dumps({"id": packet_id(item), "wg": wg, "question": item["question"], "fields": item["fields"]},
                            ensure_ascii=False) for item in packet_order(members)]
        (args.out_dir / f"packet_{wg}.jsonl").write_text("\n".join(lines) + "\n")
        (args.out_dir / "invocation" / f"prompt_{wg}.txt").write_text(prompt(wg, len(members)))
        files[wg] = record_files(wg)
    (args.out_dir / "invocation" / "record_files.json").write_text(json.dumps(files, indent=1) + "\n")
    sample = {"seed": args.seed, "perCell": args.per_cell, "order": "sha256(seed + ':' + item id) ascending",
              "items": [str(path) for path in args.items], "itemCount": len(items),
              "previousRounds": [str(folder) for folder in args.previous], "previousFiles": per_file,
              "excludedCount": len(excluded), "excludedIds": sorted(excluded),
              "sampled": sum(len(members) for members in chosen.values()),
              "byWg": {wg: len(members) for wg, members in sorted(chosen.items())},
              "shortfallTotal": sum(cell["shortfall"] for cell in cell_report),
              "cells": cell_report,
              "packetIds": {packet_id(item): item["id"] for members in chosen.values() for item in members}}
    (args.out_dir / "sample.json").write_text(json.dumps(sample, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({key: sample[key] for key in ("excludedCount", "sampled", "byWg", "shortfallTotal")}))


if __name__ == "__main__":
    main()
