"""For each text solver: helper files it wrote vs helper files it executed; flag execution of files it did not write.

usage: python3 audit_helpers.py --subagents <dir> <final_agent_ids.tsv> kind [kind ...]
--subagents is the directory with the session's agent-<id>.jsonl transcripts.
"""
import argparse, json, re
from pathlib import Path
parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
parser.add_argument("--subagents", type=Path, required=True)
parser.add_argument("tsv", type=Path)
parser.add_argument("kinds", nargs="+")
args = parser.parse_args()
SUB = args.subagents
rows = [l.split("\t") for l in args.tsv.read_text().splitlines() if l.strip()]
kinds = set(args.kinds)
for kind, wg, run, aid, *_ in rows:
    if kind not in kinds: continue
    cmds = []
    for line in (SUB / f"agent-{aid}.jsonl").open():
        r = json.loads(line); c = (r.get("message") or {}).get("content")
        if r.get("type") == "assistant" and isinstance(c, list):
            for x in c:
                if x.get("type") == "tool_use":
                    i = x["input"]
                    if x["name"] == "Write": cmds.append(("W", i["file_path"]))
                    elif x["name"] == "Bash": cmds.append(("B", i.get("command", "")))
    wrote, ran = [], []
    for k, v in cmds:
        if k == "W": wrote.append(v); continue
        # expand simple VAR=path assignments
        env = dict(re.findall(r"\b([A-Z_]+)=(/[\w./\-]+)", v))
        def ex(s):
            return re.sub(r"\$\{?([A-Z_]+)\}?", lambda m: env.get(m.group(1), m.group(0)), s)
        for m in re.finditer(r"(?:cat|tee)\s*>+\s*(\S+)|>\s*(\S+\.(?:py|sh))", v):
            wrote.append(ex(m.group(1) or m.group(2)).strip("'\""))
        for m in re.finditer(r"(?:bash|sh|python3?(?:\s+-I)?)\s+(\S+\.(?:py|sh))|(?:^|[;&|\s])(\.?/?\S+\.sh)\b", v):
            f = ex(m.group(1) or m.group(2)).strip("'\"")
            if "search_records_text.py" in f: continue
            ran.append(f)
    wn = {Path(x).name for x in wrote}
    foreign = sorted({f for f in ran if Path(f).name not in wn})
    print(kind, wg, aid, "wrote", sorted(set(wrote))[:8], "| ran-not-written", foreign)
