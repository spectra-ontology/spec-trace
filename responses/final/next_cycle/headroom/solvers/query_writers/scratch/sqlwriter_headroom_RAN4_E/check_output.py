"""Check the generated JSONL against the packet: count, keys, id order, SELECT/WITH only."""
import json
import sys

packet = json.load(open(sys.argv[1], encoding="utf-8"))
ids = [it["id"] for it in packet["items"]]
lines = open(sys.argv[2], encoding="utf-8").read().splitlines()
ok = len(lines) == len(ids)
for i, line in enumerate(lines):
    rec = json.loads(line)
    if set(rec) != {"id", "sql"} or rec["id"] != ids[i]:
        ok = False
    head = rec["sql"].lstrip().split(None, 1)[0].upper()
    if head not in ("SELECT", "WITH") or rec["sql"].count(";"):
        ok = False
    if rec["sql"].count("(") != rec["sql"].count(")"):
        ok = False
print("items", len(ids), "lines", len(lines), "pass", ok)
if len(sys.argv) > 3:
    for idx in map(int, sys.argv[3:]):
        print("----", ids[idx])
        print(json.loads(lines[idx])["sql"])
