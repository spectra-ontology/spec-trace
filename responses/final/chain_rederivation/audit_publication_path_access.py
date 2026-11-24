"""재유도 풀이 에이전트가 지시문이 허용한 경로 밖의 출판 트리(`scripts/publication` · `docs/publication` · `logs/publication`)나
DB·네트워크·모델 서비스에 닿았는지 도구 호출 입력 전체(Bash 명령·Read·Write·Edit 경로)에서 찾는다. 결과 보고(SubagentHandback)의 글은 접근이 아니라 빼고 센다.

허용 경로는 지시문에 적힌 출판 트리 경로(질문 묶음·답 파일·기록 파일)다. 지시문이 "같은 폴더"로 가리킨 파일은
앞서 적힌 경로의 폴더에 붙여 허용한다. 쓰인 경로는 셋으로 가른다: 지시문이 적은 파일(named), 그런 파일이 놓인
폴더 자체(파일 목록 보기, directoryOfNamed), 그 밖(other). 상대경로와 절대경로를 모두 잡도록 출판 트리 이름이
들어간 모든 토큰을 모은다.

사용: python3 audit_publication_path_access.py SESSION_ID AGENT_ID... > out.json
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path.home() / ".claude/projects/<project-dir>" / sys.argv[1] / "subagents"
TREE = re.compile(r"(?:scripts|docs|logs)/publication/[^\s'\"`;|)<>,]*")
SERVICE = re.compile(r"\b(sqlite3|neo4j|cypher-shell|bolt://|qdrant|curl|wget|requests\.|https?://|docker|ollama|openrouter|anthropic)\b", re.I)

out = {}
for agent in sys.argv[2:]:
    records = [json.loads(line) for line in (ROOT / f"agent-{agent}.jsonl").read_text().splitlines()]
    prompt = (records[0].get("message") or {}).get("content", "")
    if isinstance(prompt, list):
        prompt = " ".join(c.get("text", "") for c in prompt if isinstance(c, dict))
    allowed = {p.rstrip(".") for p in TREE.findall(prompt) if not p.endswith("/")}
    for path in list(allowed):
        folder = path.rsplit("/", 1)[0] + "/"
        for name in re.findall(r"`([\w.]+\.jsonl?d?)`", prompt):
            if "/" not in name:
                allowed.add(folder + name)
    folders = {p.rsplit("/", 1)[0] + "/" for p in allowed}
    touched, services, calls = {}, {}, 0
    for record in records:
        message = record.get("message") or {}
        if record.get("type") != "assistant" or not isinstance(message.get("content"), list):
            continue
        for part in message["content"]:
            if not (isinstance(part, dict) and part.get("type") == "tool_use"):
                continue
            if part.get("name") == "SubagentHandback":
                continue  # 결과 보고문이라 접근이 아니다
            calls += 1
            text = json.dumps(part.get("input") or {}, ensure_ascii=False)
            for path in TREE.findall(text):
                path = path.rstrip(".\\")
                touched[path] = touched.get(path, 0) + 1
            for token in SERVICE.findall(text):
                services[token.lower()] = services.get(token.lower(), 0) + 1
    kinds = {p: "named" if p in allowed else "directoryOfNamed" if p in folders else "other" for p in touched}
    out[agent] = {"toolCalls": calls, "allowedPublicationPaths": sorted(allowed),
                  "publicationPathsUsed": {p: {"uses": n, "kind": kinds[p]} for p, n in sorted(touched.items())},
                  "otherPublicationPaths": sorted(p for p, k in kinds.items() if k == "other"),
                  "serviceTokens": services}
json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
