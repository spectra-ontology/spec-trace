"""Check the generated JSONL against the packet: count, keys, id order, paren balance."""
import json
import sys

packet = json.load(open(sys.argv[1], encoding="utf-8"))
ids = [it["id"] for it in packet["items"]]
rows = [json.loads(line) for line in open(sys.argv[2], encoding="utf-8").read().splitlines()]
ok = len(rows) == len(ids)
ok &= all(set(r) == {"id", "sql"} for r in rows)
ok &= [r["id"] for r in rows] == ids
ok &= all(r["sql"].count("(") == r["sql"].count(")") for r in rows)
ok &= all(r["sql"].lstrip().upper().startswith(("WITH", "SELECT")) for r in rows)
ok &= all(";" not in r["sql"] for r in rows)
print("lines", len(rows), "items", len(ids), "pass", ok)
seen = set()
for r, it in zip(rows, packet["items"]):
    key = tuple(it["fields"])
    if key not in seen:
        seen.add(key)
        print("----", r["id"])
        print(r["sql"].replace(", ", ",\n  ") if "--show" in sys.argv else "")
