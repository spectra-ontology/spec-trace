"""Check the query JSONL against the packet: count, keys, id order, SELECT/WITH only."""
import json
import sys

packet = json.load(open(sys.argv[1], encoding="utf-8"))
lines = open(sys.argv[2], encoding="utf-8").read().splitlines()
ids = [it["id"] for it in packet["items"]]
ok = len(lines) == len(ids)
problems = []
for i, line in enumerate(lines):
    obj = json.loads(line)
    if set(obj) != {"id", "sql"}:
        problems.append(f"line {i + 1}: keys {sorted(obj)}")
    if i < len(ids) and obj.get("id") != ids[i]:
        problems.append(f"line {i + 1}: id {obj.get('id')} != {ids[i]}")
    head = obj.get("sql", "").lstrip().split(" ", 1)[0].upper()
    if head not in ("SELECT", "WITH"):
        problems.append(f"line {i + 1}: starts with {head}")
    if obj.get("sql", "").count("(") != obj.get("sql", "").count(")"):
        problems.append(f"line {i + 1}: unbalanced parentheses")
print("items", len(ids), "lines", len(lines))
print("PASS" if ok and not problems else "FAIL", problems)
