"""작업 폴더에 남은 파일마다 도구 호출 입력에서 그 파일을 가리킨 에이전트를 센다 (스크립트 안의 쓰기를 보완하는 검사).

`audit_scratch_helper_ownership.py` 는 명령 글에서 쓰기를 읽으므로, 풀이 스크립트가 안에서 만든 파일은 놓칠 수 있다.
이 검사는 반대 방향에서 출발한다. 폴더에 실제로 남은 파일을 하나씩 놓고, 둘 이상의 에이전트가 그 파일을 가리켰는지 본다.

가리킴: 도구 호출 입력 글에 그 파일의 절대 경로가 그대로 있거나, 같은 입력에서 부모 폴더의 절대 경로를 정확히 담은
변수 V 에 대해 `$V/이름` 이 있다. heredoc 안의 다른 언어 변수도 같은 모양이면 걸리므로, 걸린 항목은 대화 기록에서 확인한다.
환경 변수 FLAT 이 있으면 폴더 바로 아래 파일만 본다.

사용: python3 audit_scratch_file_mentions.py SESSION_ID ROOT_DIR AGENT_ID... > out.json
"""
import json
import os
import pathlib
import re
import sys

session, root, agents = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3:]
base = pathlib.Path.home() / ".claude/projects/<project-dir>" / session / "subagents"
inputs = {}
for agent in agents:
    texts = []
    for line in (base / f"agent-{agent}.jsonl").read_text().splitlines():
        record = json.loads(line)
        message = record.get("message") or {}
        if record.get("type") == "assistant" and isinstance(message.get("content"), list):
            for part in message["content"]:
                if isinstance(part, dict) and part.get("type") == "tool_use":
                    texts.append(json.dumps(part.get("input"), ensure_ascii=False).replace("\\n", "\n"))
    inputs[agent] = texts
files = [path for path in (root.glob("*") if os.environ.get("FLAT") else root.rglob("*"))
         if path.is_file() and "__pycache__" not in path.parts]
multi = {}
for path in files:
    full, parent, name = str(path), str(path.parent), path.name
    exact = re.compile(re.escape(full) + r"(?![\w.-])")
    assign = re.compile(r"\b([A-Za-z_]\w*)=['\"]?" + re.escape(parent) + r"/?['\"]?(?=[\s;&|)]|$)")

    def points(text: str) -> bool:
        if name not in text:  # 두 모양 모두 파일 이름을 그대로 담으므로, 이름이 없는 입력은 볼 필요가 없다
            return False
        if exact.search(text):
            return True
        return any(re.search(r"\$\{?" + variable + r"\}?/" + re.escape(name) + r"(?![\w.-])", text)
                   for variable in set(assign.findall(text)))

    who = [agent for agent, texts in inputs.items() if any(points(text) for text in texts)]
    if len(who) > 1:
        multi[str(path.relative_to(root))] = who
print(json.dumps({"root": str(root), "agents": len(agents), "files": len(files), "mentionedByMoreThanOneAgent": multi},
                 ensure_ascii=False, indent=1))
