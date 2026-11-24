"""Check the query file shape against the packet: one JSON line per item, keys id and sql, ids in order."""
import json
import re
import sys

packet = json.load(open(sys.argv[1], encoding="utf-8"))
raw = open(sys.argv[2], encoding="utf-8").read().splitlines()
ids = [it["id"] for it in packet["items"]]
ok = len(raw) == len(ids)
problems = []
for i, line in enumerate(raw):
    rec = json.loads(line)
    if set(rec) != {"id", "sql"}:
        problems.append((i, "keys"))
    if i < len(ids) and rec["id"] != ids[i]:
        problems.append((i, "id order"))
    sql = rec["sql"]
    if not re.match(r"\s*(WITH|SELECT)\b", sql, re.I):
        problems.append((i, "not select"))
    if sql.count("(") != sql.count(")"):
        problems.append((i, "paren balance"))
    if ";" in sql:
        problems.append((i, "semicolon"))
    fields = packet["items"][i]["fields"]
    final = sql[sql.rfind("SELECT DISTINCT"):]
    aliases = re.findall(r"\bAS (\w+)", final.split("FROM")[0])
    if aliases != fields:
        problems.append((i, "aliases %s" % aliases))
ok = ok and not problems
print("lines", len(raw), "items", len(ids), "pass", ok, problems)
