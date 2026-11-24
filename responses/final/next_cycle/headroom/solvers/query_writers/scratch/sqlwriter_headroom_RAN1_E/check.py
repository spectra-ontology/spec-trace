"""Check the generated JSONL against the packet: line count, keys, id order."""
import json
import sys

packet = json.load(open(sys.argv[1]))
ids = [it["id"] for it in packet["items"]]
raw = open(sys.argv[2]).read().splitlines()
ok = len(raw) == len(ids)
got = []
for line in raw:
    obj = json.loads(line)
    ok = ok and set(obj) == {"id", "sql"} and isinstance(obj["sql"], str) and obj["sql"].lstrip().upper().startswith(("SELECT", "WITH"))
    got.append(obj["id"])
ok = ok and got == ids
print("lines", len(raw), "items", len(ids), "pass", ok)
if len(sys.argv) > 3:
    seen = set()
    for line in raw:
        obj = json.loads(line)
        key = obj["sql"][-60:][:20]
        fam = "A" if "MAX(e2.tsg_number)" in obj["sql"] else ("B" if "NOT EXISTS" in obj["sql"] else "C")
        if fam not in seen:
            seen.add(fam)
            print(fam, obj["id"])
            print(obj["sql"])
            print()
