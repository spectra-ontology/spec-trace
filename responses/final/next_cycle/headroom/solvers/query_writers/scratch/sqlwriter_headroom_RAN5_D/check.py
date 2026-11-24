"""Check the query file: line count, JSON keys, id order, SELECT/WITH only, balanced parentheses."""
import json
import sys

pkt = json.load(open(sys.argv[1], encoding="utf-8"))
ids = [it["id"] for it in pkt["items"]]
lines = open(sys.argv[2], encoding="utf-8").read().splitlines()
ok = len(lines) == len(ids)
print("lines", len(lines), "items", len(ids))
for i, ln in enumerate(lines):
    o = json.loads(ln)
    if set(o) != {"id", "sql"} or o["id"] != ids[i]:
        ok = False
        print("bad", i, o.get("id"))
    s = o["sql"]
    if not s.lstrip().upper().startswith(("WITH", "SELECT")):
        ok = False
        print("not select", o["id"])
    depth = 0
    for ch in s:
        depth += ch == "("
        depth -= ch == ")"
        if depth < 0:
            break
    if depth != 0:
        ok = False
        print("paren", o["id"])
    if s.count("'") % 2:
        ok = False
        print("quote", o["id"])
print("PASS" if ok else "FAIL")
