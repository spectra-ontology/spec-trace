"""Check the query file shape against the packet (no database access)."""
import json
import sys

packet = json.load(open(sys.argv[1], encoding="utf-8"))
lines = open(sys.argv[2], encoding="utf-8").read().splitlines()
ids = [it["id"] for it in packet["items"]]
ok = len(lines) == len(ids)
problems = []
for i, line in enumerate(lines):
    try:
        obj = json.loads(line)
    except json.JSONDecodeError as exc:
        ok = False
        problems.append(f"line {i + 1}: not JSON ({exc})")
        continue
    if set(obj) != {"id", "sql"}:
        ok = False
        problems.append(f"line {i + 1}: keys {sorted(obj)}")
    if i < len(ids) and obj.get("id") != ids[i]:
        ok = False
        problems.append(f"line {i + 1}: id {obj.get('id')} != {ids[i]}")
    sql = obj.get("sql", "")
    head = sql.lstrip().upper()
    if not (head.startswith("SELECT") or head.startswith("WITH")):
        ok = False
        problems.append(f"line {i + 1}: does not start with SELECT/WITH")
    if sql.count("(") != sql.count(")") or sql.count("'") % 2:
        ok = False
        problems.append(f"line {i + 1}: unbalanced parentheses or quotes")
    fields = packet["items"][i]["fields"] if i < len(ids) else []
    final = sql.rsplit("SELECT DISTINCT", 1)[-1]
    for f in fields:
        if f" AS {f}" not in final:
            ok = False
            problems.append(f"line {i + 1}: alias {f} missing in final select")
print(f"items={len(ids)} lines={len(lines)} check={'PASS' if ok else 'FAIL'}")
for p in problems:
    print(p)
