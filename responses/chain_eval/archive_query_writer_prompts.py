"""질의 작성 에이전트(Text2Cypher · Text2SQL 실행 A–E)가 받은 작업 지시문을 대화 기록에서 그대로 꺼내 보관하고 실행 사이에 같은지 본다 (모델 호출 없음).

에이전트 목록은 `subagent_model_provenance.json` 의 conditions(text2cypher_runA_runB · text2sql_runA_runB ·
text2cypher_runs_C_to_E · text2sql_runs_C_to_E)에서 읽는다. 지시문은 각 하위 에이전트 대화 기록의 첫 메시지다.
`subagent_queries/prompts/{cypher|sql}_{WG}_run{X}.txt` 에 바이트 그대로 쓰고, `prompt_identity.json` 에
지시문마다 sha256 과 정규화한 판의 sha256 을 적는다. 정규화는 두 곳만 바꾼다:
출력 파일 이름의 실행 글자(`_runA.jsonl` → `_run?.jsonl`)와, SQL 지시문이 생성 스크립트 자리로 알려 준
세션 작업 폴더(`…/<세션>/scratchpad/sqlwriter_…_RAN{n}_{X}/` → `<scratch>/`).
WG · 언어마다 다섯 실행의 정규화 판이 모두 같으면 identicalAfterNormalising 이 참이다.
연결이 끊겨 다시 띄운 에이전트(relaunchOf)의 지시문은 다시 띄운 에이전트의 지시문과 바이트로 같은지 본다.

사용: python3 archive_query_writer_prompts.py [--check]
`--check` 는 파일을 쓰지 않고 저장된 지시문 · JSON 과 비교해 다르면 끝 상태 1 로 끝난다.
"""
import argparse
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "subagent_queries" / "prompts"
TRANSCRIPTS = pathlib.Path.home() / ".claude/projects/<project-dir>"
CONDITIONS = {"cypher": ("text2cypher_runA_runB", "text2cypher_runs_C_to_E"),
              "sql": ("text2sql_runA_runB", "text2sql_runs_C_to_E")}
RUN_IN_OUTPUT = re.compile(r"_run[A-E]\.jsonl")
SQL_SCRATCH = re.compile(r"<tmp>/[0-9a-f-]{36}/scratchpad/"
                         r"sqlwriter(?:_final)?_RAN\d_[A-E]/")


def prompt_of(session: str, agent: str) -> str:
    first = json.loads((TRANSCRIPTS / session / "subagents" / f"agent-{agent}.jsonl").open().readline())
    content = (first.get("message") or {}).get("content", "")
    if not isinstance(content, str):
        raise SystemExit(f"첫 메시지가 글 하나가 아니다: {agent}")
    return content


def normalise(text: str) -> str:
    return SQL_SCRATCH.sub("<scratch>/", RUN_IN_OUTPUT.sub("_run?.jsonl", text))


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="저장된 결과와 비교만 한다")
    args = parser.parse_args()
    provenance = json.loads((HERE / "subagent_model_provenance.json").read_text())
    files, prompts, all_identical = {}, {}, True
    for lang, conditions in CONDITIONS.items():
        for condition in conditions:
            for wg, entries in provenance["conditions"][condition].items():
                for entry in entries:
                    text = prompt_of(entry["session"], entry["agentId"])
                    expected = f"/{wg}_text2{'cypher' if lang == 'cypher' else 'sql'}_{entry['run']}.jsonl"
                    if expected not in text:
                        raise SystemExit(f"지시문이 자기 출력 파일을 적지 않는다: {entry['agentId']} {expected}")
                    name = f"{lang}_{wg}_{entry['run']}.txt"
                    files[OUT / name] = text
                    record = {"agentId": entry["agentId"], "session": entry["session"], "prompt": f"prompts/{name}",
                              "bytes": len(text.encode()), "promptSha256": sha(text),
                              "normalisedSha256": sha(normalise(text))}
                    relaunched = []
                    for dropped in entry.get("relaunchOf", []):
                        before = prompt_of(dropped["session"], dropped["agentId"])
                        relaunched.append({"agentId": dropped["agentId"], "promptSha256": sha(before),
                                           "sameBytesAsRelaunch": before == text})
                    if relaunched:
                        record["relaunchOf"] = relaunched
                    slot = prompts.setdefault(lang, {}).setdefault(wg, {"runs": {}})
                    if entry["run"] in slot["runs"]:
                        raise SystemExit(f"한 칸에 실행이 둘이다: {lang} {wg} {entry['run']}")
                    slot["runs"][entry["run"]] = record
    for lang, by_wg in prompts.items():
        for wg, slot in by_wg.items():
            slot["runs"] = dict(sorted(slot["runs"].items()))
            normalised = {r["normalisedSha256"] for r in slot["runs"].values()}
            slot["identicalAfterNormalising"] = len(normalised) == 1 and len(slot["runs"]) == 5
            all_identical &= slot["identicalAfterNormalising"]
        prompts[lang] = dict(sorted(by_wg.items()))
    relaunches = [q for by_wg in prompts.values() for slot in by_wg.values() for r in slot["runs"].values()
                  for q in r.get("relaunchOf", [])]
    result = {
        "description": __doc__.split("\n")[0],
        "normalisation": ["출력 파일 이름의 실행 글자 `_run[A-E].jsonl` → `_run?.jsonl`",
                          "SQL 생성 스크립트 폴더 `…/<세션>/scratchpad/sqlwriter(_final)_RAN{n}_{X}/` → `<scratch>/`"],
        "prompts": prompts,
        "summary": {"prompts": len(files),
                    "slots": sum(len(by_wg) for by_wg in prompts.values()),
                    "allSlotsIdenticalAfterNormalising": all_identical,
                    "relaunches": len(relaunches),
                    "relaunchesWithSameBytes": sum(q["sameBytesAsRelaunch"] for q in relaunches)},
    }
    files[OUT / "prompt_identity.json"] = json.dumps(result, ensure_ascii=False, indent=1) + "\n"
    differ = []
    for path, text in files.items():
        if args.check:
            if not path.exists() or path.read_text() != text:
                differ.append(path.name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print(json.dumps({"compared" if args.check else "written": len(files), "differ": differ, **result["summary"]},
                     ensure_ascii=False, indent=1))
    if differ or not all_identical:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
