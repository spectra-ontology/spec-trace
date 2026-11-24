"""Check the generated JSONL against the packet: count, keys, id order, and light SQL shape checks."""
import json
import re
import sys

pkt = json.load(open(sys.argv[1]))
raw = open(sys.argv[2]).read().splitlines()
items = pkt["items"]
ok = True
if len(raw) != len(items):
    print("line count mismatch", len(raw), len(items))
    ok = False
for n, (line, it) in enumerate(zip(raw, items)):
    try:
        obj = json.loads(line)
    except Exception as e:
        print("bad json line", n, e)
        ok = False
        continue
    if set(obj) != {"id", "sql"} or len(obj) != 2:
        print("bad keys", n, sorted(obj))
        ok = False
    if obj.get("id") != it["id"]:
        print("id mismatch", n, obj.get("id"), it["id"])
        ok = False
    sql = obj.get("sql", "")
    if not re.match(r"^\s*(WITH|SELECT)\b", sql, re.I):
        print("not SELECT/WITH", it["id"])
        ok = False
    if sql.count("(") != sql.count(")") or sql.count("'") % 2:
        print("unbalanced", it["id"])
        ok = False
    final = sql.rsplit("\nSELECT DISTINCT ", 1)
    if len(final) != 2:
        print("no final SELECT DISTINCT", it["id"])
        ok = False
        continue
    head = final[1].split("\nFROM", 1)[0]
    aliases = re.findall(r" AS (\w+)(?:,|$)", head)
    if aliases != it["fields"]:
        print("alias mismatch", it["id"], aliases, it["fields"])
        ok = False
    if re.search(r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|ATTACH|PRAGMA)\b", sql, re.I):
        print("non-read keyword", it["id"])
        ok = False
print("PASS" if ok else "FAIL", len(raw), len(items))
