#!/usr/bin/env bash
# 헤드룸 분할의 풀이 세션이 쓴 파일을 채점기가 읽는 응답 파일로 옮긴다 (모델 호출 없음). 저장소 루트에서 실행한다.
#
#   bash collect_headroom_solver_runs.sh query A B C D E   질의 작성 세션의 질의를 한 번씩 실행한다(다시 쓰기 없음).
#   bash collect_headroom_solver_runs.sh text A B          본문 검색 세션의 답을 문항 id 로 되돌린다.
#   bash collect_headroom_solver_runs.sh dense A B         dense 도구 세션의 답을 문항 id 로 되돌린다.
#
# 질의 실행은 execute_repeated_runs.sh 의 설정(run_chain_eval.py --queries, 첫 질의만, 문항마다 한 번)을 그대로 쓴다.
# 그래프 질의는 bolt://localhost:7686+N(RAN N), 관계형 질의는 integration/sqlite_final/<WG>.sqlite 로 보낸다.
# 답 옮기기는 collect_packet_answers.py 가 한다(묶음 id → 문항 id, 질문 SHA-256 대조, 빠진 문항 수 보고).
# 세션 파일이 없거나 줄 수가 모자라면 알리고 건너뛴다. 이미 있는 응답은 다시 쓰지 않는다(FORCE=1 이면 다시 쓴다).
# SOLVERS=<dir> 를 주면 세션 파일과 응답의 뿌리를 바꾼다(시험용).
set -uo pipefail
L=logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark
S=scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark
H=$L/final/next_cycle/headroom
SOLVERS=${SOLVERS:-$H/solvers}
BUILD=${BUILD:-$H/solvers/build}
export PYTHONPATH=scripts/common:$S
[ -f "$S/run_chain_eval.py" ] || { echo "저장소 루트에서 실행한다" >&2; exit 2; }
kind=${1:-}; shift || true
[ $# -ge 1 ] || { echo "사용: bash $0 query|text|dense <run> [<run> ...]" >&2; exit 2; }

items_of() { if [ "$1" = RAN5 ]; then echo "$H/gate/ran5/chain_items_admitted.jsonl"; else echo "$H/gate/core/chain_items_admitted.jsonl"; fi; }
count_of() { python3 -c "import json,sys; print(sum(json.loads(l)['wg']==sys.argv[2] for l in open(sys.argv[1]) if l.strip()))" "$(items_of "$1")" "$1"; }

case $kind in
query)
  out_dir=$SOLVERS/responses/query_writers; mkdir -p "$out_dir"
  for run in "$@"; do for method in text2cypher text2sql; do for wg in RAN1 RAN2 RAN3 RAN4 RAN5; do
    queries=$SOLVERS/query_writers/subagent_queries/${wg}_${method}_run${run}.jsonl
    out=$out_dir/${wg}_${method}_run${run}.jsonl
    need=$(count_of "$wg")
    if [ ! -f "$queries" ]; then echo "skip $wg $method run$run: 질의 파일 없음"; continue; fi
    have=$(grep -c . "$queries")
    if [ "$have" -ne "$need" ]; then echo "skip $wg $method run$run: 질의 $have줄, 문항 $need개"; continue; fi
    if [ -f "$out" ] && [ "${FORCE:-0}" != 1 ]; then echo "keep $wg $method run$run: 응답 있음 ($(grep -c . "$out")줄)"; continue; fi
    if [ "$method" = text2cypher ]; then target=(--bolt "bolt://localhost:$((7686 + ${wg#RAN}))")
    else target=(--sqlite "$L/integration/sqlite_final/${wg}.sqlite"); fi
    t0=$(date +%s)
    python3 -B "$S/run_chain_eval.py" --items "$(items_of "$wg")" --wg "$wg" --method "$method" "${target[@]}" \
      --model "claude-opus-subagent-run$run" --queries "$queries" --repairs 0 --out "$out" \
      > "${out%.jsonl}.stdout" 2> "${out%.jsonl}.stderr"
    echo "eval $wg $method run$run exit=$? wall=$(( $(date +%s) - t0 ))s lines=$(grep -c . "$out" 2>/dev/null || echo 0)/$need"
  done; done; done ;;
text|dense)
  if [ "$kind" = text ]; then sub=text_search; method=text_search; parts=$BUILD/text_search/parts
  else sub=dense; method=dense_search; parts=$BUILD/dense/packets/parts; fi
  for run in "$@"; do
    out_dir=$SOLVERS/responses/${sub}_run${run}; mkdir -p "$out_dir"
    for packet in "$parts"/RAN*_part*.json; do
      part=$(basename "$packet" .json); wg=${part%%_*}
      answers=$SOLVERS/$sub/${sub}_run${run}/${part}_answers.jsonl
      out=$out_dir/$part.jsonl
      if [ ! -f "$answers" ]; then echo "skip $sub run$run $part: 답 파일 없음"; continue; fi
      if [ -f "$out" ] && [ "${FORCE:-0}" != 1 ]; then echo "keep $sub run$run $part: 응답 있음"; continue; fi
      python3 -B "$S/collect_packet_answers.py" --items "$(items_of "$wg")" --answers "$answers" --method "$method" \
        --model claude-subagent --out "$out" --packet "$packet" 2>&1 | tail -2 | sed "s/^/$sub run$run $part: /"
    done
  done ;;
*) echo "사용: bash $0 query|text|dense <run> [<run> ...]" >&2; exit 2 ;;
esac
