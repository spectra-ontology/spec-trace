#!/bin/bash
# 헤드룸 분할의 Codex 네 조건(스키마만 · 읽기 전용 탐색 × SQL · Cypher)을 한 번에 하나씩 돌린다. 저장소 루트에서 실행한다.
#   WORK=<작업 폴더 뿌리> bash run_headroom.sh sch_sql_RAN1 exp_cy_RAN3 ...
# 이름은 {sch|exp}_{cy|sql}_RAN{N}. 지시문은 채택 문항 측정 때 보관한 틀을 그대로 쓰고(스키마만 = chain_eval/codex/invocation,
# 탐색 = chain_eval/codex_v2/invocation), 문항 묶음만 헤드룸 분할의 것으로 바꾼다. 실행 설정(모델 · 추론 강도 · 샌드박스)도 같다.
# 작업 폴더에는 packet.json 과, 탐색 조건이면 database.sqlite(읽기 전용 사본) 또는 query_graph.py(중계 서버로만 질의를
# 보내는 도우미) 하나만 둔다. 사건 기록은 작업 폴더 밖에 쓴다. 그래프 탐색 실행만 localhost 중계 서버 접속용으로
# sandbox_workspace_write.network_access=true 를 켠다. 기록은 헤드룸 폴더 아래에만 쓰고 보관된 기록은 건드리지 않는다.
set -u
: "${WORK:?WORK must point to the scratch root for working directories}"
L=logs/publication/paper/ongoing/sigir-2027-research
S=scripts/publication/paper/ongoing/sigir-2027-research
H=$L/final/next_cycle/headroom
V=$H/codex
R=$V/run_records
MAXROWS=2000
mkdir -p "$R" "$V/queries"

graph_counts() {
  PYTHONPATH=scripts/common python3 -c "
import json, sys
from neo4j import GraphDatabase
from common.credentials import neo4j_auth
with GraphDatabase.driver(sys.argv[1], auth=neo4j_auth()) as d, d.session(default_access_mode='READ') as s:
    print(json.dumps({'nodes': s.run('MATCH (n) RETURN count(n) AS c').single()['c'],
                      'relationships': s.run('MATCH ()-[r]->() RETURN count(r) AS c').single()['c']}))" "$1"
}

for name in "$@"; do
  IFS=_ read -r cond lang wg <<< "$name"
  n=${wg#RAN}
  d=$WORK/$name
  rec=$R/$name
  [ -e "$rec/prompt.txt" ] && { echo "skip $name (run record exists)"; continue; }
  mkdir -p "$d" "$rec"
  case $lang in cy) full=cypher;; sql) full=sql;; *) echo "bad name $name"; continue;; esac
  packet=$H/packets/$full/${wg}_schema.json
  case $cond in sch) tpl=$L/chain_eval/codex/invocation/prompt_${full}.txt;;
                exp) tpl=$L/chain_eval/codex_v2/invocation/prompt_${full}_explore.txt;;
                *) echo "bad name $name"; continue;; esac
  cp "$packet" "$d/packet.json"
  extra=()
  before='null'; after='null'; proxy=''
  if [ "$cond" = exp ] && [ "$lang" = sql ]; then
    cp "$L/integration/sqlite_final/${wg}.sqlite" "$d/database.sqlite"
    chmod 444 "$d/database.sqlite"
    before="\"$(sha256sum "$L/integration/sqlite_final/${wg}.sqlite" | cut -d' ' -f1)\""
  fi
  if [ "$cond" = exp ] && [ "$lang" = cy ]; then
    port=$((47686 + n))
    bolt=bolt://localhost:$((7686 + n))
    PYTHONPATH=scripts/common python3 "$S/codex_explore_graph_proxy.py" --bolt "$bolt" --port "$port" \
      --log "$rec/proxy_log.jsonl" --max-rows $MAXROWS --timeout 60 > "$rec/proxy.stdout" 2> "$rec/proxy.stderr" &
    proxy=$!
    python3 -c "import time; time.sleep(3)"
    sed "s/PROXY_PORT/$port/" "$L/chain_eval/codex_v2/invocation/query_graph.py.template" > "$d/query_graph.py"
    chmod 444 "$d/query_graph.py"
    before=$(graph_counts "$bolt")
    extra=(-c sandbox_workspace_write.network_access=true)
  fi
  items=$(python3 -c "import json,sys;print(len(json.load(open(sys.argv[1]))['items']))" "$d/packet.json")
  prompt=$(sed -e "s/NITEMS/$items/g" -e "s/MAXROWS/$MAXROWS/g" "$tpl")
  printf '%s' "$prompt" > "$rec/prompt.txt"
  ( cd "$d" && find . -type f -printf '%P\t%s\n' | sort ) > "$rec/workdir_before.tsv"
  t0=$(date +%s); started=$(date -Is)
  echo "start $name $started"
  ~/.local/bin/codex exec --json --skip-git-repo-check --ignore-user-config -s workspace-write -C "$d" \
    -m gpt-6.1-sol -c model_reasoning_effort='"ultra"' "${extra[@]}" "$prompt" </dev/null \
    > "$WORK/$name.events.jsonl" 2> "$WORK/$name.stderr.txt"
  code=$?
  t1=$(date +%s); ended=$(date -Is)
  if [ -n "$proxy" ]; then
    after=$(graph_counts "$bolt")
    kill "$proxy"; wait "$proxy" 2>/dev/null
  fi
  if [ "$cond" = exp ] && [ "$lang" = sql ]; then
    after="\"$(sha256sum "$d/database.sqlite" | cut -d' ' -f1)\""
  fi
  cp "$WORK/$name.events.jsonl" "$rec/events.jsonl"
  cp "$WORK/$name.stderr.txt" "$rec/stderr.txt"
  ( cd "$d" && find . -type f -printf '%P\t%s\n' | sort ) > "$rec/workdir_after.tsv"
  mkdir -p "$rec/workdir"
  ( cd "$d" && find . -type f ! -name packet.json ! -name database.sqlite ! -name query_graph.py -printf '%P\n' ) |
    while IFS= read -r f; do mkdir -p "$rec/workdir/$(dirname "$f")"; cp "$d/$f" "$rec/workdir/$f"; done
  lines=0
  [ -f "$d/queries.jsonl" ] && { cp "$d/queries.jsonl" "$V/queries/$name.jsonl"; lines=$(wc -l < "$d/queries.jsonl"); }
  net=false; [ ${#extra[@]} -gt 0 ] && net=true
  echo "end $name exit=$code $ended wall=$((t1 - t0))s lines=$lines"
  printf '{"name": "%s", "condition": "%s", "language": "%s", "wg": "%s", "items": %s, "exit": %s, "startedAt": "%s", "endedAt": "%s", "wallSeconds": %s, "queryLines": %s, "networkAccess": %s, "before": %s, "after": %s, "packetSha256": "%s", "promptTemplate": "%s", "promptTemplateSha256": "%s"}\n' \
    "$name" "$cond" "$lang" "$wg" "$items" "$code" "$started" "$ended" "$((t1 - t0))" "$lines" "$net" "$before" "$after" \
    "$(sha256sum "$packet" | cut -d' ' -f1)" "$tpl" "$(sha256sum "$tpl" | cut -d' ' -f1)" >> "$R/runs.jsonl"
done
