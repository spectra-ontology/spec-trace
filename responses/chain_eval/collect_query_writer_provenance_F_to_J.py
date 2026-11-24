"""질의 작성 에이전트(Text2Cypher · Text2SQL 실행 F–J)의 세션 출처를 `subagent_model_provenance.json` 의 conditions 에 더한다 (모델 호출 없음).

더하는 조건은 text2cypher_runs_F_to_J · text2sql_runs_F_to_J 이고, 항목의 꼴은 text2cypher_runs_C_to_E · text2sql_runs_C_to_E 와 같다.
실행 F–J 의 지시문은 `subagent_queries/prompts/{cypher|sql}_{WG}_run{X}.txt` 에 있고, 에이전트는 첫 메시지로 그 글을 그대로 받았다.
모든 세션의 하위 에이전트 대화 기록에서 첫 메시지가 실행 F–J 질의 파일 하나(`subagent_queries/{WG}_text2{언어}_run{X}.jsonl`)와
같은 언어 · WG 의 패킷 하나를 적은 에이전트를 찾고, 그 첫 메시지가 대화의 첫 사용자 메시지이며 지시문 파일과 바이트로 같을 때만 잇는다.
promptSha256 은 지시문 파일의 sha256 이고 첫 메시지의 sha256 과 같다.
시작 · 종료 시각, 응답 모델, 응답 메시지 수, 실행 환경 안내, 뒤따른 사용자 메시지 종류는
collect_subagent_model_provenance.py 가 대화 기록에서 읽은 값을 그대로 쓴다. 모델은 응답 메시지의 model 필드에서만 읽는다.
한 지시문을 받은 에이전트가 둘 이상이면 앞 에이전트가 끝난 뒤에 다음 에이전트가 시작했는지 보고, 마지막 에이전트를 항목으로 쓰고
앞 에이전트들을 그 relaunchOf 에 적는다.
자리 하나라도 에이전트에 이어지지 않거나, 질의 파일을 적은 첫 메시지가 지시문 파일과 다르면 아무것도 쓰지 않고 끝 상태 1 로 끝난다.

사용: python3 collect_query_writer_provenance_F_to_J.py [--check]
`--check` 는 파일을 쓰지 않고 저장된 출처 기록과 비교해 다르면 끝 상태 1 로 끝난다.
"""
import argparse
import collections
import hashlib
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROVENANCE = HERE / "subagent_model_provenance.json"
COLLECTOR = HERE / "collect_subagent_model_provenance.py"
PROMPTS = HERE / "subagent_queries" / "prompts"
TRANSCRIPTS = pathlib.Path.home() / ".claude/projects/<project-dir>"
CONDITIONS = {"cypher": "text2cypher_runs_F_to_J", "sql": "text2sql_runs_F_to_J"}
PACKETS = {"cypher": "subagent_packets", "sql": "subagent_packets_sql"}
WGS = [f"RAN{n}" for n in range(1, 6)]
RUNS = [f"run{x}" for x in "FGHIJ"]
QUERY_FILE = re.compile(r"chain_eval/subagent_queries/(RAN\d)_text2(cypher|sql)_(run[F-J])\.jsonl")
PACKET_FILE = re.compile(r"chain_eval/(subagent_packets(?:_sql)?)/(RAN\d)_schema\.json")
NOTE_KEY = "queryWriterRunsFtoJ"
NOTE = {"note": "질의 작성 실행 F–J(conditions 의 " + " · ".join(CONDITIONS.values()) + ")는 실행 A–E 와 같은 꼴이다. 에이전트는 첫 메시지로 "
                "지시문 파일(prompt)의 글을 그대로 받았고, 첫 메시지와 지시문 파일이 바이트로 같은 에이전트만 이었다(promptSha256 은 둘 모두의 "
                "sha256). 한 지시문에 에이전트가 둘 이상이면 앞 에이전트는 relaunchOf 에 있다.",
        "script": "collect_query_writer_provenance_F_to_J.py"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def first_record(path: pathlib.Path) -> dict:
    with path.open(encoding="utf-8") as lines:
        return json.loads(lines.readline())


def first_text(record: dict) -> str:
    content = (record.get("message") or {}).get("content")
    if isinstance(content, list):
        return " ".join(c.get("text", "") for c in content if isinstance(c, dict))
    return content if isinstance(content, str) else ""


def is_first_user_text(record: dict) -> bool:
    return (record.get("type") == "user" and record.get("parentUuid") is None
            and isinstance((record.get("message") or {}).get("content"), str))


def collect(session: str, agents: list) -> dict:
    run = subprocess.run([sys.executable, "-B", str(COLLECTOR), session, *agents], capture_output=True, text=True, check=True)
    return json.loads(run.stdout)


def record_of(agent: str, session: str, info: dict, extra: dict) -> dict:
    out = {"agentId": agent, "session": session, **extra, "started": info["started"], "ended": info["ended"],
           "models": info["models"], "assistantMessages": info["assistantMessages"],
           "followupKinds": dict(sorted(collections.Counter(f["kind"] for f in info["followupInstructions"]).items()))}
    if info["harnessNotices"]:
        out["harnessNotices"] = info["harnessNotices"]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="저장된 결과와 비교만 한다")
    args = parser.parse_args()
    slots = {(lang, wg, run): PROMPTS / f"{lang}_{wg}_{run}.txt" for lang in CONDITIONS for wg in WGS for run in RUNS}
    found, problems = collections.defaultdict(list), []
    for transcript in sorted(TRANSCRIPTS.glob("*/subagents/agent-*.jsonl")):
        try:
            record = first_record(transcript)
        except (json.JSONDecodeError, OSError):
            continue
        text = first_text(record)
        queries, packets = set(QUERY_FILE.findall(text)), set(PACKET_FILE.findall(text))
        if len(queries) != 1 or len(packets) != 1:
            continue
        (wg, lang, run), (packet_dir, packet_wg) = next(iter(queries)), next(iter(packets))
        if packet_wg != wg or packet_dir != PACKETS[lang]:
            continue
        agent, session = transcript.stem.removeprefix("agent-"), transcript.parent.parent.name
        prompt = slots[(lang, wg, run)]
        if not is_first_user_text(record):
            problems.append(f"첫 기록이 대화의 첫 사용자 글이 아니다: {session} {agent}")
        elif not prompt.is_file() or sha(text.encode("utf-8")) != sha(prompt.read_bytes()):
            problems.append(f"첫 메시지가 지시문 파일과 다르다: {session} {agent} {prompt.name}")
        else:
            found[(lang, wg, run)].append((agent, session))
    problems += [f"이어진 에이전트가 없다: {slot[0]} {slot[1]} {slot[2]} (기록 없음)" for slot in slots if slot not in found]
    if problems:
        raise SystemExit("\n".join(problems))
    by_session = collections.defaultdict(list)
    for agents in found.values():
        for agent, session in agents:
            by_session[session].append(agent)
    info = {(agent, session): value for session, agents in by_session.items()
            for agent, value in collect(session, agents).items()}
    conditions = {condition: {wg: [] for wg in WGS} for condition in CONDITIONS.values()}
    for (lang, wg, run), prompt in slots.items():
        tied = {"prompt": str(prompt.relative_to(HERE)), "promptSha256": sha(prompt.read_bytes())}
        agents = sorted(found[(lang, wg, run)], key=lambda a: info[a]["started"])
        for before, after in zip(agents, agents[1:]):
            if info[before]["ended"] > info[after]["started"]:
                raise SystemExit(f"다시 띄운 에이전트가 앞 에이전트가 끝나기 전에 시작했다: {before[0]} {after[0]}")
        last, dropped = agents[-1], agents[:-1]
        entry = record_of(*last, info[last], {"run": run})
        if dropped:
            entry["relaunchOf"] = [{**record_of(*agent, info[agent], {}), "promptSha256": tied["promptSha256"]} for agent in dropped]
        entry.update(tied)
        conditions[CONDITIONS[lang]][wg].append(entry)
    original = PROVENANCE.read_text(encoding="utf-8")
    provenance = json.loads(original)
    if json.dumps(provenance, ensure_ascii=False, indent=1) != original:
        raise SystemExit("출처 기록 파일을 같은 꼴로 다시 쓸 수 없다")
    provenance["conditions"].update(conditions)
    provenance[NOTE_KEY] = NOTE
    text = json.dumps(provenance, ensure_ascii=False, indent=1)
    summary = {condition: {"entries": sum(len(es) for es in by_wg.values()),
                           "agentIds": len({e["agentId"] for es in by_wg.values() for e in es}),
                           "relaunched": sum(len(e.get("relaunchOf", [])) for es in by_wg.values() for e in es),
                           "harnessNotices": sum(len(s.get("harnessNotices", [])) for es in by_wg.values() for e in es
                                                 for s in [e, *e.get("relaunchOf", [])]),
                           "models": sorted({m for es in by_wg.values() for e in es for m in e["models"]}),
                           "relaunchOfModels": sorted({m for es in by_wg.values() for e in es
                                                       for d in e.get("relaunchOf", []) for m in d["models"]}),
                           "sessions": sorted({e["session"] for es in by_wg.values() for e in es}),
                           "started": min(e["started"] for es in by_wg.values() for e in es),
                           "ended": max(e["ended"] for es in by_wg.values() for e in es)}
               for condition, by_wg in conditions.items()}
    differ = text != original
    if not args.check:
        PROVENANCE.write_text(text, encoding="utf-8")
    print(json.dumps({"checked" if args.check else "written": sum(s["entries"] for s in summary.values()), "differ": differ,
                      "conditions": summary}, ensure_ascii=False, indent=1))
    if args.check and differ:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
