#!/bin/bash
# Rebuild benchmark items from the released records with the released builder and compare them
# with the stored item file.
#
# Usage: results_rebuild_check.sh PYTHON RELEASE WORK_DIR WG...
#
# WORK_DIR receives the record files of the given working groups at the path the builder reads
# (ontology/output/tsg/RAN/formal/instances/<phase>/<WG>/): a symbolic link for a file stored
# plain, a decompressed copy for a file stored with gzip. The builder then runs from WORK_DIR with
# the stored anchor list, and the lines of its output are compared with the lines of the stored
# core item file that belong to the same working groups.
set -euo pipefail
PY=$1; RELEASE=$(readlink -f "$2"); WORK=$3; shift 3
mkdir -p "$WORK"; WORK=$(readlink -f "$WORK")
INST="$WORK/ontology/output/tsg/RAN/formal/instances"
for wg in "$@"; do
  for phase in phase-1 phase-2 phase-4; do
    src="$RELEASE/records/$phase/$wg"
    [ -d "$src" ] || continue
    mkdir -p "$INST/$phase/$wg"
    for f in "$src"/*; do
      name=$(basename "$f")
      case "$name" in
        *.gz) [ -f "$INST/$phase/$wg/${name%.gz}" ] || gzip -dc "$f" > "$INST/$phase/$wg/${name%.gz}" ;;
        *) ln -sfn "$f" "$INST/$phase/$wg/$name" ;;
      esac
    done
  done
done
find "$INST" \( -type f -o -type l \) | sort | while read -r p; do
  echo "input $(stat -L -c %s "$p") ${p#$WORK/}"
done
BUILDER="$RELEASE/code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/build_chain_items.py"
ANCHORS="$RELEASE/benchmark/chain_items_rebuilt/chain_items.jsonl"
EXTRA=()
if [ "$#" = 1 ] && [ "$1" = RAN5 ]; then
  ANCHORS="$RELEASE/benchmark/chain_items_ran5/chain_items.jsonl"
  mkdir -p "$INST/RAN5_graph_export"
  ln -sfn "$RELEASE/records/RAN5_graph_export/RAN5" "$INST/RAN5_graph_export/RAN5"
  EXTRA=(--phase4-root "$INST/RAN5_graph_export")
elif [[ " $* " == *" RAN5 "* ]]; then
  echo "Run RAN5 separately: its pack/clause files use the documented graph export." >&2
  exit 2
fi
cd "$WORK" || exit 1
"$PY" -I -B "$BUILDER" --wg "$@" --per-cell 20 --seed 20261111 --out-dir "$WORK/out" \
  --anchors-from "$ANCHORS" "${EXTRA[@]}" \
  > "$WORK/build.stdout" 2> "$WORK/build.stderr"
echo "builder exit $?"
"$PY" -I -B - "$RELEASE" "$WORK" "$@" <<'EOF'
import hashlib, json, sys
release, work, wgs = sys.argv[1], sys.argv[2], set(sys.argv[3:])
part = "ran5" if wgs == {"RAN5"} else "core"
stored = [l for l in open(release + f"/benchmark/items_final/{part}/chain_items.jsonl", "rb").read().split(b"\n")
          if l and json.loads(l)["wg"] in wgs]
try:
    built = [l for l in open(work + "/out/chain_items.jsonl", "rb").read().split(b"\n") if l]
except OSError as e:
    print("no output", e)
    sys.exit(1)
same = sum(1 for a, b in zip(stored, built) if a == b)
print(json.dumps({"workingGroups": sorted(wgs), "storedLines": len(stored), "builtLines": len(built),
                  "identicalLinesInOrder": same,
                  "storedSha256": hashlib.sha256(b"\n".join(stored)).hexdigest(),
                  "builtSha256": hashlib.sha256(b"\n".join(built)).hexdigest()}))
for i, (a, b) in enumerate(zip(stored, built)):
    if a != b:
        x, y = json.loads(a), json.loads(b)
        print("first difference at line", i + 1, x.get("id"), y.get("id"),
              [k for k in set(x) | set(y) if x.get(k) != y.get(k)])
        break
sys.exit(0 if stored == built else 1)
EOF
