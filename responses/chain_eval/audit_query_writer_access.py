"""Text2Cypher·Text2SQL 질의 작성 에이전트가 지정 패킷 밖의 파일·DB·네트워크에 접근했는지 대화 기록으로 검사한다."""
import json, pathlib, re, sys, collections
# 첫 인자는 대화 세션 id(하위 에이전트 기록이 놓인 폴더 이름), 나머지는 에이전트 id
d = pathlib.Path.home()/'.claude/projects/<project-dir>'/sys.argv[1]/'subagents'
ids = sys.argv[2:]
# 경로는 공백·따옴표·셸 구분자·마크다운 코드 표시(`)에서 끊는다. 보고 글의 `경로` 표기가 경로 끝에 붙지 않게 한다.
PATH = re.compile(r"(/(?:home|tmp)/[^\s'\"\;|)<>,`]+)")
NET = re.compile(r"\b(curl|wget|cypher-shell|bolt://|neo4j\b|GraphDatabase|sqlite3\.connect|requests\.|http://|https://|docker)\b")
out = {}
for i in ids:
    lines = (d/f'agent-{i}.jsonl').read_text().splitlines()
    prompt = json.loads(lines[0])['message']['content']
    if isinstance(prompt, list): prompt = ' '.join(c.get('text','') for c in prompt if isinstance(c, dict))
    allowed = set(PATH.findall(prompt))
    paths = collections.Counter(); net = []; tools = collections.Counter()
    for l in lines:
        r = json.loads(l); m = r.get('message', {})
        if not (isinstance(m, dict) and isinstance(m.get('content'), list)): continue
        for x in m['content']:
            if isinstance(x, dict) and x.get('type') == 'tool_use':
                tools[x['name']] += 1
                s = json.dumps(x.get('input', {}), ensure_ascii=False)
                s = s.encode().decode('unicode_escape', errors='ignore') if '\\n' in s else s
                for p in PATH.findall(s): paths[p.rstrip('.')] += 1
                for n in NET.findall(s): net.append(n)
    outside = sorted(p for p in paths if not any(p == a or p.startswith(a.rstrip('/') + '/') or a.startswith(p.rstrip('/') + '/') for a in allowed))
    out[i] = {"tools": dict(tools), "allowedInPrompt": sorted(allowed), "pathsOutsidePrompt": outside, "networkOrDbTokens": sorted(set(net))}
json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
