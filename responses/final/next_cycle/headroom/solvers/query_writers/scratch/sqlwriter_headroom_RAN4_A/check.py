"""Check the generated JSONL against the packet: count, keys, id order, read-only form."""
import json
import re
import sys

packet = json.load(open(sys.argv[1]))
lines = open(sys.argv[2]).read().splitlines()
ids = [it["id"] for it in packet["items"]]
ok = len(lines) == len(ids)
print("lines", len(lines), "items", len(ids))
for i, line in enumerate(lines):
    rec = json.loads(line)
    if set(rec) != {"id", "sql"} or rec["id"] != ids[i]:
        ok = False
        print("bad", i, rec.get("id"))
    sql = rec["sql"]
    if not re.match(r"^(WITH|SELECT)\b", sql) or sql.count("(") != sql.count(")") or ";" in sql:
        ok = False
        print("form", rec["id"])
    if re.search(r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|ATTACH|PRAGMA)\b", sql, re.I):
        ok = False
        print("write", rec["id"])
    fields = packet["items"][i]["fields"]
    final = sql[sql.rfind("SELECT DISTINCT"):]
    aliases = re.findall(r"AS (\w+)\s*(?:,|FROM)", final.split(" FROM ")[0] + " FROM")
    if aliases != fields:
        ok = False
        print("fields", rec["id"], aliases, fields)
print("PASS" if ok else "FAIL")
