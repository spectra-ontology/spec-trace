"""보충 주기 검색 풀이 에이전트의 세션 출처를 `subagent_model_provenance.json` 의 conditions 에 더한다 (모델 호출 없음).

대상은 본문만 검색 실행 B·C, 원문 색인 검색 실행 A·B, 밀집 검색 도구 실행 A·B, 한 번에 돌려주는 청크 수에 상한을 둔
밀집 검색 도구 실행 A 다. 이 에이전트들의 첫 메시지는 과제 글 파일 하나를 가리키는 짧은 지시이고, 에이전트는 첫 도구
호출에서 그 파일을 cat 으로 읽었다. 그래서 과제 글과 에이전트를 첫 메시지의 해시가 아니라 두 가지로 잇는다:
첫 메시지가 가리킨 파일이 그 과제 글 하나이고, 첫 도구 호출(Bash `cat <과제 글>`)의 출력이 과제 글 파일의 글과 같다.
`cat <과제 글>; echo; wc -c <과제 글>` 로 읽은 호출은 출력이 과제 글의 글, 줄바꿈, 바이트 수와 경로로만 이루어졌는지 본다.
promptSha256 은 과제 글 파일의 sha256, instructionSha256 은 첫 메시지의 sha256 이다.
시작·종료 시각, 응답 모델, 응답 메시지 수, 실행 환경 안내, 뒤따른 사용자 메시지 종류는
collect_subagent_model_provenance.py 가 대화 기록에서 읽은 값을 그대로 쓴다.
한 과제 글을 받은 에이전트가 둘 이상이면 앞 에이전트가 답을 남기지 못하고 끝나 같은 과제 글로 다시 띄운 것이다
(각 실행 폴더 위의 session_observations.jsonl · session_incidents.jsonl). 앞 에이전트가 끝난 뒤에 다음 에이전트가
시작했는지 보고, 마지막 에이전트를 항목으로 쓰고 앞 에이전트들을 그 relaunchOf 에 적는다.
과제 글 하나라도 에이전트에 이어지지 않거나 읽은 글이 파일과 다르면 아무것도 쓰지 않고 끝 상태 1 로 끝난다.

사용: python3 collect_supplement_solver_provenance.py SESSION_ID [--check]
`--check` 는 파일을 쓰지 않고 저장된 출처 기록과 비교해 다르면 끝 상태 1 로 끝난다.
"""
import argparse
import collections
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROVENANCE = HERE / "subagent_model_provenance.json"
COLLECTOR = HERE / "collect_subagent_model_provenance.py"
SUPPLEMENT = HERE.parent / "final" / "supplement_cycle"
TRANSCRIPTS = pathlib.Path.home() / ".claude/projects/<project-dir>"
# 조건 이름 → 보충 주기 실행 폴더. 이름은 기존 조건(text_search_runB · text_search_text_only)처럼 경로 이름에 실행 글자를 붙인다
CONDITIONS = {"text_search_text_only_runB": "text_only_agent/runB", "text_search_text_only_runC": "text_only_agent/runC",
              "raw_index_runA": "raw_agent/runA", "raw_index_runB": "raw_agent/runB",
              "dense_tool_runA": "dense_agent/runA", "dense_tool_runB": "dense_agent/runB",
              "dense_tool_capped_runA": "dense_capped_agent/runA"}
WGS = [f"RAN{n}" for n in range(1, 6)]
PARTS = ("part1", "part2", "part3")
POINTER = re.compile(r"\AYour complete instructions are in this one text file: (\S+\.txt)\n")
NOTE_KEY = "supplementSolverPromptDelivery"
NOTE = {"note": "보충 주기 검색 풀이 에이전트(conditions 의 " + " · ".join(CONDITIONS) + ")는 첫 메시지로 과제 글 파일 경로만 받고 "
                "첫 도구 호출에서 그 파일을 cat 으로 읽었다. prompt · promptSha256 은 그 과제 글 파일, instructionSha256 은 첫 메시지다. "
                "첫 도구 호출의 출력이 과제 글 파일의 글과 같은지 보고 이었다. 한 과제 글에 에이전트가 둘이면 앞 에이전트가 답을 남기지 "
                "못하고 끝나 다시 띄운 것이고 앞 에이전트는 relaunchOf 에 있다.",
        "script": "collect_supplement_solver_provenance.py"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_of(content) -> str:
    if isinstance(content, list):
        return "".join(c.get("text", "") for c in content if isinstance(c, dict))
    return content or ""


def first_read(path: pathlib.Path):
    """첫 메시지, 첫 도구 호출, 그 출력. 대화 기록을 그 출력이 나올 때까지만 읽는다."""
    first, call = None, None
    with path.open(encoding="utf-8") as lines:
        for line in lines:
            record = json.loads(line)
            content = (record.get("message") or {}).get("content")
            if first is None:
                first = content if isinstance(content, str) else ""
                continue
            if not isinstance(content, list):
                continue
            for part in content:
                if part.get("type") == "tool_use" and call is None:
                    call = part
                elif part.get("type") == "tool_result" and call is not None and part.get("tool_use_id") == call["id"]:
                    return first, call, text_of(part.get("content"))
    return first, call, None


def read_matches(call, output, prompt: pathlib.Path) -> bool:
    """첫 도구 호출이 과제 글을 cat 으로 읽었고 그 출력이 파일의 글과 같은가."""
    if call is None or call.get("name") != "Bash" or output is None:
        return False
    command, text = call.get("input", {}).get("command"), prompt.read_text(encoding="utf-8")
    if command == f"cat {prompt}":
        return output == text.rstrip("\n")
    if command == f"cat {prompt}; echo; wc -c {prompt}":
        return output == f"{text}\n{prompt.stat().st_size} {prompt}"
    return False


def collect(session: str, agents: list) -> dict:
    run = subprocess.run([sys.executable, "-B", str(COLLECTOR), session, *agents], capture_output=True, text=True, check=True)
    return json.loads(run.stdout)


def record_of(session: str, agent: str, info: dict, extra: dict) -> dict:
    out = {"agentId": agent, "session": session, **extra, "started": info["started"], "ended": info["ended"],
           "models": info["models"], "assistantMessages": info["assistantMessages"],
           "followupKinds": dict(sorted(collections.Counter(f["kind"] for f in info["followupInstructions"]).items()))}
    if info["harnessNotices"]:
        out["harnessNotices"] = info["harnessNotices"]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("session", help="풀이 에이전트를 띄운 세션 id")
    parser.add_argument("--check", action="store_true", help="저장된 결과와 비교만 한다")
    args = parser.parse_args()
    prompts = {(SUPPLEMENT / folder / "prompts" / f"{wg}_{part}.txt"): (condition, wg, part)
               for condition, folder in CONDITIONS.items() for wg in WGS for part in PARTS}
    agents, problems = collections.defaultdict(list), []
    for transcript in sorted((TRANSCRIPTS / args.session / "subagents").glob("agent-*.jsonl")):
        first, call, output = first_read(transcript)
        named = POINTER.match(first or "")
        if not named or pathlib.Path(named.group(1)) not in prompts:
            continue
        prompt = pathlib.Path(named.group(1))
        if not read_matches(call, output, prompt):
            problems.append(f"첫 도구 호출이 과제 글을 그대로 읽지 않았다: {transcript.stem}")
        agents[prompt].append((transcript.stem.removeprefix("agent-"), sha(first.encode())))
    problems += [f"이어진 에이전트가 없다: {os.path.relpath(p, HERE)}" for p in prompts if p not in agents]
    if problems:
        raise SystemExit("\n".join(problems))
    info = collect(args.session, [agent for found in agents.values() for agent, _ in found])
    conditions = {condition: {wg: [] for wg in WGS} for condition in CONDITIONS}
    for prompt, (condition, wg, part) in sorted(prompts.items(), key=lambda kv: (list(CONDITIONS).index(kv[1][0]), kv[1][1:])):
        tied = {"prompt": os.path.relpath(prompt, HERE), "promptSha256": sha(prompt.read_bytes())}
        found = sorted(agents[prompt], key=lambda a: info[a[0]]["started"])
        for before, after in zip(found, found[1:]):
            if info[before[0]]["ended"] > info[after[0]]["started"]:
                raise SystemExit(f"다시 띄운 에이전트가 앞 에이전트가 끝나기 전에 시작했다: {before[0]} {after[0]}")
        (last, last_instruction), dropped = found[-1], found[:-1]
        entry = record_of(args.session, last, info[last], {"part": part, **tied, "instructionSha256": last_instruction})
        if dropped:
            entry["relaunchOf"] = [record_of(args.session, agent, info[agent], {**tied, "instructionSha256": instruction})
                                   for agent, instruction in dropped]
        conditions[condition][wg].append(entry)
    original = PROVENANCE.read_text(encoding="utf-8")
    provenance = json.loads(original)
    if json.dumps(provenance, ensure_ascii=False, indent=1) != original:
        raise SystemExit("출처 기록 파일을 같은 꼴로 다시 쓸 수 없다")
    provenance["conditions"].update(conditions)
    provenance[NOTE_KEY] = NOTE
    text = json.dumps(provenance, ensure_ascii=False, indent=1)
    entries = [e for by_wg in conditions.values() for es in by_wg.values() for e in es]
    summary = {condition: {"entries": sum(len(es) for es in by_wg.values()),
                           "relaunched": sum(len(e.get("relaunchOf", [])) for es in by_wg.values() for e in es),
                           "models": sorted({m for es in by_wg.values() for e in es for m in e["models"]}),
                           "relaunchOfModels": sorted({m for es in by_wg.values() for e in es
                                                       for d in e.get("relaunchOf", []) for m in d["models"]})}
               for condition, by_wg in conditions.items()}
    differ = text != original
    if not args.check:
        PROVENANCE.write_text(text, encoding="utf-8")
    print(json.dumps({"checked" if args.check else "written": len(entries), "differ": differ, "conditions": summary},
                     ensure_ascii=False, indent=1))
    if args.check and differ:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
