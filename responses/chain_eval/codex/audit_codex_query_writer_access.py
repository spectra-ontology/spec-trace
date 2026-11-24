"""Codex 풀이 한 건의 events.jsonl 에서 실행 명령을 모두 꺼내, 작업 폴더의 두 파일 밖을 건드렸는지 표시한다."""
import json, re, sys, collections
d = sys.argv[1]
cmds, usage, thread, kinds = [], None, None, collections.Counter()
for line in open(f"{d}/events.jsonl"):
    try: e = json.loads(line)
    except Exception: continue
    kinds[e.get("type")] += 1
    if e.get("type") == "thread.started": thread = e.get("thread_id")
    if e.get("type") == "turn.completed": usage = e.get("usage")
    it = e.get("item") or {}
    if e.get("type") == "item.completed":
        kinds["item:" + str(it.get("type"))] += 1
        if it.get("type") == "command_execution": cmds.append(it.get("command", ""))
SUSPECT = re.compile(r"(\.\./|/home/|/tmp/|~|neo4j|bolt|sqlite|curl|wget|http|ssh|nc |docker|cypher-shell|gold|items_final|logs/|scripts/)", re.I)
flag = []
for c in cmds:
    # 허용: 작업 폴더 안의 packet.json / queries.jsonl 과 그 폴더 안 임시 스크립트
    hits = [m.group(0) for m in SUSPECT.finditer(c)]
    if hits: flag.append((hits[:5], c[:300]))
files = sorted(set(re.findall(r"[\w./-]+\.(?:json|jsonl|py|txt|sh|sql|cypher)\b", " ".join(cmds))))
print(json.dumps({"dir": d.rsplit('/',1)[1], "thread": thread, "usage": usage, "nCommands": len(cmds),
                  "eventKinds": dict(kinds), "filesNamed": files[:40], "flagged": flag[:10]}, ensure_ascii=False, indent=1))
