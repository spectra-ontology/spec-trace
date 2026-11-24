"""동시에 돈 에이전트들이 같은 경로의 파일을 쓰고, 다른 에이전트가 마지막으로 쓴 파일을 실행·읽었는지 대화 기록의 시각 순서로 검사한다.

동시에 돈 에이전트들이 같은 작업 폴더에 같은 이름의 파일을 쓰면, 한 에이전트가 다른 에이전트의 스크립트를
실행하거나 다른 에이전트의 출력을 읽을 수 있다. 모든 에이전트의 도구 호출을 한 시간축에 놓고, 접근마다 그
직전 쓰기의 주체를 비교한다.

명령 한 줄을 읽는 방법.
- 명령을 줄 · `&&` · `||` · `;` · `|` 로 나누고, 조각마다 그때까지의 변수 값(`A=…` · `export A=…`, 대입할 때
  이미 펼친 값)과 `cd` 를 적용해 낱말을 펼친다. 상대 경로는 `cd` 가 없으면 저장소 루트 기준이다.
- 쓰기: `>` · `>>` · `2>` · `&>` 리다이렉트, `tee`, `cat > 파일 <<끝`, `sed -i`, `cp`·`mv` 의 대상,
  풀이 스크립트의 `--out`·`--output`·`-o` 값, Write·Edit 도구, heredoc 이나 `python -c` 안의 `open(…, 'w')`
  · `.write_text(…)` 에 적힌 글자 그대로의 경로.
- 실행: 조각의 첫 낱말이 `.py`·`.sh` 경로(`$S args`·`./x.sh`), 또는 `python`·`bash`·`sh`·`source`·`.` 뒤의
  첫 비선택 인자(`bash -x $S` 포함). `bash <<끝` 으로 넘긴 본문은 같은 방법으로 다시 읽는다.
- 접근: 펼친 낱말 · `<` 입력 · heredoc 본문의 따옴표 글자 가운데, 어느 에이전트든 한 번이라도 쓴 경로와
  같은 것. Read · Grep · Glob 도구의 경로도 접근이다. 같은 조각 안에서는 접근을 쓰기보다 먼저 놓는다.

내는 것.
- helpers: `.py`·`.sh` 의 쓰기 · 실행 · 읽기. 다른 에이전트가 마지막으로 쓴 보조 스크립트를 실행·읽은 경우
  (runOrReadOfAnotherAgentsFile)와 이 에이전트들 가운데 누구도 쓰지 않은 보조 스크립트를 실행한 경우
  (runOrReadWithoutRecordedWrite, 저장소 안 경로인지 함께 적는다).
- allFiles: 모든 파일에서 둘 이상의 에이전트가 쓴 경로(pathsWrittenByMoreThanOneAgent)와 다른 에이전트가
  마지막으로 쓴 파일에 접근한 경우(accessOfAnotherAgentsFile, (에이전트, 경로, 마지막 쓴 주체)마다 첫 시각과 횟수).

명령 문자열을 셸 없이 읽으므로 셸이 실제로 펼친 값과 다를 수 있다(반복문 변수 · 명령 치환은 펼치지 않는다).
그래서 이 결과는 판정할 후보 목록이고, 걸린 항목은 대화 기록에서 하나씩 확인한다.

사용: python3 audit_scratch_helper_ownership.py SESSION_ID AGENT_ID... > out.json
"""
import collections
import json
import os
import pathlib
import re
import shlex
import sys

REPO = next(path for path in pathlib.Path(__file__).resolve().parents if (path / ".git").exists())
ROOT = pathlib.Path.home() / ".claude/projects/<project-dir>" / sys.argv[1] / "subagents"
AGENTS = sys.argv[2:]
HELPER = re.compile(r"\.(?:py|sh)$")
VAR = re.compile(r"\$\{([A-Za-z_]\w*)(?::?[-?+=][^}]*)?\}|\$([A-Za-z_]\w*)")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1([^\n]*)\n(.*?)\n[ \t]*\2(?=\n|$)", re.S)
REDIRECT = re.compile(r"(?<![<>])(?:\d|&)?>{1,2}(?![&>])\s*([^\s;&|<>()]+)")
QUOTE_SPAN = re.compile(r"'[^']*'|\"(?:\\.|[^\"\\])*\"")
INPUT = re.compile(r"(?<![<\d])<\s*([^\s;&|<>()]+)")
INLINE_WRITE = re.compile(r"open\(\s*[rf]?['\"]([^'\"{}]+)['\"]\s*,\s*['\"][wax]|"
                          r"Path\(\s*[rf]?['\"]([^'\"{}]+)['\"]\s*\)\.write_(?:text|bytes)")
QUOTED = re.compile(r"['\"]([^'\"\s{}]+)['\"]")
PREFIX = {"time", "env", "nice", "nohup", "exec", "sudo", "then", "do", "else", "!", "(", "{", "command"}
INTERPRETER = re.compile(r"^(?:\S*/)?(?:python3?(?:\.\d+)?|bash|sh|zsh|source|\.)$")
PATH_OUT = {"--out", "--output", "-o"}


def substitute(text: str, env: dict) -> str:
    return VAR.sub(lambda m: env.get(m.group(1) or m.group(2), m.group(0)), text)


def resolve(token: str, cwd: str | None) -> str | None:
    token = token.strip("'\"")
    if not token or "$" in token or "*" in token or token.startswith("-") or token in {"/dev/null", "&1", "&2"}:
        return None
    if token.startswith("~/"):
        token = str(pathlib.Path.home()) + token[1:]
    if not token.startswith("/"):
        token = f"{cwd or REPO}/{token}"
    return os.path.normpath(token)


def split_pieces(body: str) -> list[str]:
    """따옴표 밖의 줄바꿈 · `;` · `&&` · `||` · `|` · 뒤로 돌리는 `&` 에서 나눈다. 따옴표 밖 `#` 뒤는 주석이다."""
    pieces, buf, quote, i = [], [], None, 0
    while i < len(body):
        c = body[i]
        if quote:
            buf.append(c)
            if c == "\\" and quote == '"' and i + 1 < len(body):
                buf.append(body[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "'\"":
            quote = c
        elif c == "\\" and i + 1 < len(body):
            if body[i + 1] != "\n":
                buf.extend((c, body[i + 1]))
            i += 2
            continue
        elif c == "#" and (not buf or buf[-1] in " \t\n;|&("):
            while i < len(body) and body[i] != "\n":
                i += 1
            continue
        elif body[i:i + 2] in ("&&", "||"):
            pieces.append("".join(buf))
            buf, i = [], i + 2
            continue
        elif c in "\n;|" or (c == "&" and body[i + 1:i + 2] != ">" and not (buf and buf[-1] in "<>")):
            pieces.append("".join(buf))
            buf, i = [], i + 1
            continue
        buf.append(c)
        i += 1
    pieces.append("".join(buf))
    return [piece.strip() for piece in pieces if piece.strip()]


def mask_code(text: str) -> tuple[str, list[str]]:
    """공백 · `<` · `>` 가 든 따옴표 글자를 자리표로 바꿔 리다이렉트 검사에서 뺀다."""
    kept = []

    def hide(match: re.Match) -> str:
        if re.search(r"[\s<>]", match.group(0)):
            kept.append(match.group(0))
            return f"__QUOTED{len(kept) - 1}__"
        return match.group(0)

    return QUOTE_SPAN.sub(hide, text), kept


def split_words(text: str) -> list[str]:
    try:
        return shlex.split(text, posix=True)
    except ValueError:
        return text.split()


def parse_command(command: str, env: dict | None = None, cwd: str | None = None) -> list[dict]:
    """명령 하나를 조각으로 나눠 조각마다 {writes, runs, candidates, edits} 를 낸다(경로는 펼쳐 정규화한 절대 경로)."""
    env = dict(env or {})
    bodies = []

    def blank(match: re.Match) -> str:
        bodies.append((match.start(), match.group(3), match.group(4)))
        return f"<<HEREDOC{len(bodies) - 1}{match.group(3)}"

    body = HEREDOC.sub(blank, command)
    out = []
    for piece in split_pieces(body):
        text = substitute(piece, env)
        writes, runs, edits, candidates, excluded = [], [], [], set(), set()
        heredocs = [bodies[int(n)] for n in re.findall(r"<<HEREDOC(\d+)", text)]
        masked, kept = mask_code(re.sub(r"<<HEREDOC\d+", " ", text))
        for match in REDIRECT.finditer(masked):
            path = resolve(match.group(1), cwd)
            if path:
                writes.append(path)
        for match in INPUT.finditer(masked):
            path = resolve(match.group(1), cwd)
            if path:
                candidates.add(path)
        stripped = INPUT.sub(" ", REDIRECT.sub(" ", masked))
        stripped = re.sub(r"__QUOTED(\d+)__", lambda m: kept[int(m.group(1))], stripped)
        words = split_words(stripped)
        while words and re.match(r"^[A-Za-z_]\w*=", words[0]) or words[:1] == ["export"]:
            if words[0] == "export":
                words = words[1:]
                continue
            name, value = words[0].split("=", 1)
            env[name] = value
            words = words[1:]
        while words and words[0] in PREFIX:
            words = words[1:]
        if words and words[0] == "timeout":
            words = words[2:]
        if not words:
            out.append({"writes": writes, "runs": runs, "edits": edits, "candidates": candidates})
            continue
        head = words[0]
        if head == "cd" and len(words) > 1:
            cwd = resolve(words[1], cwd) or cwd
            continue
        script_index = None
        if HELPER.search(head):
            script_index = 0
        elif INTERPRETER.match(head):
            index = 1
            while index < len(words) and words[index].startswith("-"):
                if words[index] in ("-c", "-m", "-"):
                    index = None
                    break
                index += 1
            if index is not None and index < len(words) and HELPER.search(words[index]):
                script_index = index
            if re.match(r"^(?:\S*/)?(?:bash|sh|zsh)$", head) and (script_index is None) and heredocs:
                for _, _, inner in heredocs:
                    out.extend(parse_command(inner, env, cwd))
        if script_index is not None:
            path = resolve(words[script_index], cwd)
            if path:
                runs.append(path)
                excluded.add(path)
            for flag, value in zip(words[script_index + 1:], words[script_index + 2:]):
                if flag in PATH_OUT:
                    path = resolve(value, cwd)
                    if path:
                        writes.append(path)
            for word in words[script_index + 1:]:
                if word.startswith(("--out=", "--output=")):
                    path = resolve(word.split("=", 1)[1], cwd)
                    if path:
                        writes.append(path)
        if head == "tee":
            for word in words[1:]:
                if not word.startswith("-"):
                    path = resolve(word, cwd)
                    if path:
                        writes.append(path)
                        excluded.add(path)
        if head in ("cp", "mv", "install"):
            operands = [w for w in words[1:] if not w.startswith("-")]
            if len(operands) >= 2:
                target = resolve(operands[-1], cwd)
                if target:
                    if operands[-1].endswith("/") or os.path.isdir(target) or len(operands) > 2:
                        writes.extend(p for p in (resolve(f"{target}/{os.path.basename(src.rstrip('/'))}", None)
                                                  for src in operands[:-1]) if p)
                    else:
                        writes.append(target)
                    excluded.add(target)
        if head == "sed" and any(w == "-i" or w.startswith("-i") for w in words[1:]):
            path = resolve(words[-1], cwd)
            if path:
                edits.append(path)
        inline = [inner for _, _, inner in heredocs]
        inline += [words[i + 1] for i, w in enumerate(words[:-1]) if w == "-c" and INTERPRETER.match(head)]
        for code in inline:
            for match in INLINE_WRITE.finditer(code):
                path = resolve(match.group(1) or match.group(2), cwd)
                if path:
                    writes.append(path)
            for match in QUOTED.finditer(code):
                path = resolve(match.group(1), cwd)
                if path:
                    candidates.add(path)
        for word in words[1:]:
            value = word.split("=", 1)[1] if word.startswith("--") and "=" in word else word
            path = resolve(value, cwd)
            if path and path not in excluded:
                candidates.add(path)
        out.append({"writes": writes, "runs": runs, "edits": edits, "candidates": candidates})
    return out


records = []
for agent in AGENTS:
    order = 0
    for line in (ROOT / f"agent-{agent}.jsonl").read_text().splitlines():
        record = json.loads(line)
        message = record.get("message") or {}
        if record.get("type") != "assistant" or not isinstance(message.get("content"), list):
            continue
        for part in message["content"]:
            if not (isinstance(part, dict) and part.get("type") == "tool_use"):
                continue
            name, data = part["name"], part.get("input") or {}
            if name == "Bash":
                pieces = parse_command(data.get("command", ""))
            elif name == "Write":
                pieces = [{"writes": [os.path.normpath(data.get("file_path", ""))], "runs": [], "edits": [],
                           "candidates": set()}]
            elif name == "Edit":
                pieces = [{"writes": [], "runs": [], "edits": [os.path.normpath(data.get("file_path", ""))],
                           "candidates": set()}]
            elif name in ("Read", "Grep", "Glob"):
                path = data.get("file_path") or data.get("path") or ""
                pieces = [{"writes": [], "runs": [], "edits": [],
                           "candidates": {os.path.normpath(path)} if path else set()}]
            else:
                pieces = []
            for piece in pieces:
                order += 1
                records.append({"time": record.get("timestamp", ""), "seq": order, "agent": agent, "tool": name,
                                **piece})

written = {path for r in records for path in r["writes"] + r["edits"]}
timeline = []
for r in records:
    base = {"time": r["time"], "seq": r["seq"], "agent": r["agent"], "tool": r["tool"]}
    accessed = (r["candidates"] & written) | set(r["edits"])
    for path in sorted(set(r["runs"])):
        timeline.append({**base, "order": 0, "kind": "run", "path": path})
    for path in sorted(accessed - set(r["runs"])):
        timeline.append({**base, "order": 1, "kind": "read", "path": path})
    for path in sorted(set(r["writes"]) | set(r["edits"])):
        timeline.append({**base, "order": 2, "kind": "write", "path": path})
timeline.sort(key=lambda e: (e["time"], e["seq"], e["order"]))

last_writer: dict[str, str] = {}
writers = collections.defaultdict(set)
helper_foreign, helper_unwritten = [], []
access_foreign: dict[tuple, dict] = {}
for event in timeline:
    path, agent = event["path"], event["agent"]
    if event["kind"] == "write":
        last_writer[path] = agent
        writers[path].add(agent)
        continue
    owner = last_writer.get(path)
    if HELPER.search(path):
        if owner is None and event["kind"] == "run":
            helper_unwritten.append({**event, "inRepo": path.startswith(f"{REPO}/")})
        elif owner is not None and owner != agent:
            helper_foreign.append({**event, "lastWriter": owner})
    if owner is not None and owner != agent:
        key = (agent, path, owner)
        entry = access_foreign.setdefault(key, {"agent": agent, "path": path, "lastWriter": owner,
                                                "firstTime": event["time"], "kinds": [], "count": 0})
        entry["count"] += 1
        if event["kind"] not in entry["kinds"]:
            entry["kinds"].append(event["kind"])

helper_events = [{k: v for k, v in e.items() if k != "order"} for e in timeline if HELPER.search(e["path"])]
json.dump({
    "method": __doc__.split("\n")[0],
    "agents": AGENTS,
    "toolCallPieces": len(records),
    "helpers": {
        "events": len(helper_events),
        "runsOrReads": sum(1 for e in helper_events if e["kind"] != "write"),
        "pathsWrittenByMoreThanOneAgent": {p: sorted(a) for p, a in sorted(writers.items())
                                           if len(a) > 1 and HELPER.search(p)},
        "runOrReadOfAnotherAgentsFile": [{k: v for k, v in e.items() if k != "order"} for e in helper_foreign],
        "runOrReadWithoutRecordedWrite": [{k: v for k, v in e.items() if k != "order"} for e in helper_unwritten],
        "timeline": helper_events,
    },
    "allFiles": {
        "pathsWritten": len(writers),
        "pathsWrittenByMoreThanOneAgent": {p: sorted(a) for p, a in sorted(writers.items()) if len(a) > 1},
        "accessOfAnotherAgentsFile": sorted(access_foreign.values(), key=lambda e: e["firstTime"]),
    },
}, sys.stdout, ensure_ascii=False, indent=1)
