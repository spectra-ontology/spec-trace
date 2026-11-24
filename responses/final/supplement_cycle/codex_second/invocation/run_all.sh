#!/bin/bash
# 작업반마다 Codex 작업 폴더를 만들고 Codex 풀이를 한 번에 하나씩 돌린다. 저장소 루트에서 실행한다.
# 작업 폴더에는 묶음(questions.jsonl), record_files.json 이 적은 기록 파일의 복사본(쓰기 금지), 빈 work/ 만 둔다.
# 이벤트 로그·표준 오류·답·도움 스크립트는 작업 폴더 밖 run_records/<작업반>/ 에 남긴다.
# 사용: WORK_ROOT=<저장소 밖 빈 폴더> bash run_all.sh RAN1 RAN2 ...
set -u
W=${WORK_ROOT:?}
F=<repo>/logs/publication/paper/ongoing/sigir-2027-research/final/supplement_cycle/codex_second
for wg in "$@"; do
  d=$W/$wg
  out=$F/run_records/$wg
  [ -s "$out/answers.jsonl" ] && { echo "skip $wg"; continue; }
  avail=$(free -g | awk '/^Mem:/{print $7}')
  [ "$avail" -lt 8 ] && { echo "stop $wg: available ${avail}GiB"; exit 1; }
  [ -e "$d" ] && { echo "stop $wg: $d already exists"; exit 1; }
  mkdir -p "$d/work" "$out"
  cp "$F/packet_$wg.jsonl" "$d/questions.jsonl"
  python3 - "$wg" "$d" "$F/invocation/record_files.json" "$out/workdir_manifest.json" <<'EOF'
import hashlib, json, os, shutil, sys
wg, d, table, manifest = sys.argv[1:]
def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()
rows = []
for rel, source in json.load(open(table))[wg].items():
    target = os.path.join(d, "records", rel)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    shutil.copyfile(source, target)
    rows.append({"copy": "records/" + rel, "source": source, "bytes": os.path.getsize(target),
                 "sha256": digest(target), "sourceSha256": digest(source)})
rows.append({"copy": "questions.jsonl", "bytes": os.path.getsize(os.path.join(d, "questions.jsonl")),
             "sha256": digest(os.path.join(d, "questions.jsonl"))})
json.dump({"wg": wg, "files": rows, "allCopiesIdentical": all(r.get("sourceSha256", r["sha256"]) == r["sha256"] for r in rows)},
          open(manifest, "w"), indent=1)
EOF
  find "$d/records" "$d/questions.jsonl" -type f -exec chmod a-w {} +
  prompt=$(cat "$F/invocation/prompt_$wg.txt")
  echo "start $wg $(date -Is) avail=${avail}GiB"
  ~/.local/bin/codex exec --json --skip-git-repo-check --ignore-user-config -s workspace-write -C "$d" \
    -m gpt-6.1-sol -c model_reasoning_effort='"ultra"' "$prompt" </dev/null > "$out/events.jsonl" 2> "$out/stderr.txt"
  rc=$?
  [ -f "$d/answers.jsonl" ] && cp "$d/answers.jsonl" "$out/answers.jsonl"
  mkdir -p "$out/work" && cp -r "$d/work/." "$out/work/"
  (cd "$d" && find . -path ./records -prune -o -type f -printf '%P\t%s\n' | sort) > "$out/workdir_files.txt"
  # 풀이 뒤에도 기록 복사본과 묶음이 처음 그대로인지 다시 해시로 맞춘다.
  python3 - "$d" "$out/workdir_manifest.json" "$out/records_after_run.json" <<'EOF'
import hashlib, json, os, sys
d, manifest, report = sys.argv[1:]
def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()
rows = json.load(open(manifest))["files"]
changed = [r["copy"] for r in rows if not os.path.isfile(os.path.join(d, r["copy"]))
           or digest(os.path.join(d, r["copy"])) != r["sha256"]]
extra = sorted(os.path.relpath(os.path.join(root, name), d) for root, _, names in os.walk(os.path.join(d, "records"))
               for name in names if "records/" + os.path.relpath(os.path.join(root, name), os.path.join(d, "records"))
               not in {r["copy"] for r in rows})
json.dump({"checked": len(rows), "changed": changed, "extraUnderRecords": extra}, open(report, "w"), indent=1)
EOF
  echo "end $wg exit=$rc $(date -Is) lines=$(wc -l < "$out/answers.jsonl" 2>/dev/null)"
done
