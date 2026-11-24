"""보조 스크립트가 다른 에이전트의 스크립트를 하위 프로세스나 import 로 부른 후보를 대화 기록에서 찾는다.

`audit_scratch_helper_ownership.py` 는 도구 호출의 명령 한 줄을 읽으므로, 실행된 스크립트가 안에서 같은 폴더의
다른 스크립트를 부르는 경우(`subprocess.run([... dirname(__file__) + "/x.py"])`, `from x import …`)는 보지
못한다. 이 검사는 그 세션 전체 시간축(표준 입력으로 받는 `session_*_all_groups.json` 의 helpers.timeline)과
대화 기록의 코드 본문으로 그 빈칸을 채운다.

코드 본문: Write 의 content, Edit 의 new_string, Bash 명령 안의 heredoc 본문과 `-c` 인자.

내는 것.
- scriptNamesAnotherAgentsFile: 스크립트 S 가 시각 t 에 실행될 때, S 를 쓴 에이전트들이 t 까지 S 에 대해 남긴
  도구 호출(쓰기와 읽기, 고쳐 쓰기는 읽기로 잡히기도 한다)의 코드 본문이 같은 폴더의 다른 스크립트 P 를 파일
  이름이나 import 할 모듈 이름으로 적거나 P 의 전체 경로를 적고, t 에 P 의 마지막 쓴 주체가 S 를 실행한
  에이전트가 아닌 경우.
- inlineNamesAnotherAgentsFile: 한 도구 호출 안에서 P 의 폴더로 `cd` 하거나 그 폴더를 `sys.path` 에 넣고
  P 의 파일 이름이나 모듈 이름을 적었거나, 스크립트를 그 폴더에 바로 쓰면서 `__file__` 기준으로 P 의 이름을
  적었는데, 그때 P 의 마지막 쓴 주체가 다른 에이전트이고 시간축에 그 호출의 P 사건이 없는 경우.

한계. 이름을 문자열로 이어 붙여 만들거나(`"su" + "mm.py"`) 변수로 넘기면 찾지 못한다. 다른 폴더의 스크립트는
전체 경로로 적었을 때만 찾는다. 복사(`cp`)나 다른 스크립트가 만든 스크립트는 본문을 읽지 못한다. 디스크의 파일은
읽지 않는다(작업 폴더가 지워진 뒤에도 같은 결과를 내도록). 실제 실행 여부와 그 출력이 답에 쓰였는지는 판정하지
않는다. 이 결과도 판정할 후보 목록이고, 하나씩 대화 기록에서 확인한다(scratch_helper_ownership/adjudication.json).

사용: python3 audit_indirect_helper_execution.py SESSION_ID < session_xxxxxxxx_all_groups.json > out.json
"""
import bisect
import collections
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path.home() / ".claude/projects/<project-dir>" / sys.argv[1] / "subagents"
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n(.*?)\n[ \t]*\2(?=\n|$)", re.S)
DASH_C = re.compile(r"\s-c\s+(['\"])(.*?)(?<!\\)\1", re.S)
CONTEXT_FILE = ("__file__",)


def name_pattern(name: str, bare: bool) -> re.Pattern:
    before = r"(?<![\w./-])" if bare else r"(?<![\w.-])"
    return re.compile(before + re.escape(name) + r"(?![\w.-])")


def import_pattern(stem: str) -> re.Pattern:
    return re.compile(r"(?:^|[\n;])\s*(?:from\s+" + re.escape(stem) + r"\s+import\b|import\s+(?:[\w.]+\s*,\s*)*"
                      + re.escape(stem) + r"\b)")


def code_bodies(tool: str, given: dict) -> list[str]:
    if tool == "Write":
        return [given.get("content", "")]
    if tool == "Edit":
        return [given.get("new_string", "")]
    if tool == "MultiEdit":
        return [edit.get("new_string", "") for edit in given.get("edits", [])]
    command = given.get("command", "")
    return [m.group(3) for m in HEREDOC.finditer(command)] + [m.group(2) for m in DASH_C.finditer(command)]


timeline = json.load(sys.stdin)
agents = timeline["agents"]
events = sorted({(e["time"], e["agent"], e["kind"], e["path"]) for e in timeline["helpers"]["timeline"]})
writes, runs, touched = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
seen = set()
for time, agent, kind, path in events:
    seen.add((agent, time, path))
    touched[path].append((time, agent))
    if kind == "write":
        writes[path].append((time, agent))
    elif kind == "run":
        runs[path].append((time, agent))


def last_writer(path: str, time: str) -> str | None:
    entries = writes.get(path, [])
    index = bisect.bisect_right([t for t, _ in entries], time)
    return entries[index - 1][1] if index else None


calls = collections.defaultdict(list)  # (agent, time) -> [(code bodies, whole input text)]
for agent in agents:
    transcript = ROOT / f"agent-{agent}.jsonl"
    if not transcript.exists():
        continue
    for line in transcript.open():
        record = json.loads(line)
        content = (record.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for piece in content:
            if isinstance(piece, dict) and piece.get("type") == "tool_use":
                given = piece.get("input") or {}
                calls[(agent, record.get("timestamp"))].append(
                    (code_bodies(piece.get("name", ""), given), given.get("command") or given.get("content") or ""))

helpers = sorted(writes)
by_folder = collections.defaultdict(list)
for path in helpers:
    by_folder[os.path.dirname(path)].append(path)


def names(body: str, script: str, other: str) -> bool:
    if other == script:
        return False
    if other in body:
        return True
    if os.path.dirname(other) != os.path.dirname(script):
        return False
    name = os.path.basename(other)
    if name_pattern(name, bare=False).search(body):
        return True
    return other.endswith(".py") and bool(import_pattern(name.rsplit(".", 1)[0]).search(body))


script_hits = []
for script, started in sorted(runs.items()):
    for time, runner in started:
        authors = {a for t, a in writes.get(script, []) if t <= time}
        body = "\n".join(text for t, a in touched[script] if t <= time and a in authors
                         for bodies, _ in calls.get((a, t), []) for text in bodies)
        for other in helpers:
            if names(body, script, other):
                owner = last_writer(other, time)
                if owner != runner:
                    script_hits.append({"time": time, "runner": runner, "script": script, "names": other,
                                        "lastWriterOfNamed": owner})

inline_hits = []
for (agent, time), entries in sorted(calls.items(), key=lambda kv: (kv[0][1] or "", kv[0][0])):
    if time is None:
        continue
    text = "\n".join(whole for _, whole in entries)
    for folder, paths in by_folder.items():
        quoted = re.escape(folder)
        cd = re.search(r"\bcd\s+[\"']?" + quoted + r"/?[\"']?(?:\s|&|;|\)|$)", text)
        on_path = re.search(r"sys\.path\.(?:insert\(\s*0\s*,|append\()\s*[rf]?[\"']" + quoted + r"/?[\"']", text)
        here = (re.search(quoted + r"/[\w.-]+\.(?:py|sh)(?![\w./-])", text)
                and any(key in text for key in CONTEXT_FILE))
        if not (cd or on_path or here):
            continue
        for path in paths:
            if path in text:
                continue
            name = os.path.basename(path)
            bare = name_pattern(name, bare=True).search(text)
            imported = path.endswith(".py") and import_pattern(name.rsplit(".", 1)[0]).search(text)
            if not (bare or imported):
                continue
            owner = last_writer(path, time)
            if owner in (None, agent) or (agent, time, path) in seen:
                continue
            inline_hits.append({"time": time, "agent": agent, "path": path, "lastWriter": owner,
                                "context": "cd" if cd else ("sys.path" if on_path else "__file__"),
                                "namedAs": "import" if imported else "file name"})

json.dump({
    "method": __doc__.split("\n")[0],
    "session": sys.argv[1],
    "timelineEvents": len(events),
    "helpersWritten": len(helpers),
    "scriptNamesAnotherAgentsFile": script_hits,
    "inlineNamesAnotherAgentsFile": inline_hits,
}, sys.stdout, ensure_ascii=False, indent=1)
