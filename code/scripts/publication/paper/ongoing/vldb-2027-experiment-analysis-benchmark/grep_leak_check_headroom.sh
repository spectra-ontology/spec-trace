#!/usr/bin/env bash
# Independent of build_headroom_packets.py's own leak check: grep -F every gold cell and every item id of the given
# items against every packet and prompt file of a build directory, and say for each gold-cell hit whether the value
# is also in the item's own question.
#   bash grep_leak_check.sh <build-dir> <items.jsonl> [<items.jsonl> ...]
set -euo pipefail
build=$1; shift
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
python3 -B - "$tmp" "$@" <<'PY'
import json, sys
tmp, paths = sys.argv[1], sys.argv[2:]
with open(f"{tmp}/cells.tsv", "w") as cells, open(f"{tmp}/ids.txt", "w") as ids:
    for path in paths:
        for line in open(path):
            if not line.strip():
                continue
            item = json.loads(line)
            ids.write(item["id"] + "\n")
            for row in item["gold"]:
                for cell in row:
                    inq = int(str(cell) in item["question"])
                    cells.write(f"{item['id']}\t{cell}\t{inq}\n")
PY
find "$build" -type f \( -name '*.json' -o -name '*.txt' \) ! -name build_manifest.json ! -name leak_check.json \
  ! -name sample.json ! -name build_report.json | sort > "$tmp/files"
echo "files scanned: $(wc -l < "$tmp/files")"
echo "gold cells: $(wc -l < "$tmp/cells.tsv")"
id_hits=$( (xargs -a "$tmp/files" -d '\n' grep -hoF -f "$tmp/ids.txt" || true) | wc -l)
echo "item-id occurrences in packet/prompt files: $id_hits"
total=0; in_q=0; outside=0
while IFS=$'\t' read -r id value inq; do
  n=$( (xargs -a "$tmp/files" -d '\n' grep -lF -- "$value" || true) | wc -l)
  total=$((total+1))
  if [ "$n" -gt 0 ]; then
    if [ "$inq" = 1 ]; then in_q=$((in_q+1)); else outside=$((outside+1)); echo "HIT not in own question: $id | $value | files: $n"; fi
  fi
done < "$tmp/cells.tsv"
echo "gold cells found in some file: $((in_q+outside)) (also in own question: $in_q; not in own question: $outside) of $total"
