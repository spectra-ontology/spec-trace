#!/bin/bash
# 저장된 SQL 응답 재실행을 두 인터프리터로 차례로 돌린다. 저장소 루트에서 실행한다.
# 사용: replay_stored_sql.sh <새 SQLite 를 가진 python> <옛 SQLite 를 가진 python>
set -u
A=logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/next_cycle/work/vldb_draft/analysis
OUT=$A/replay
mkdir -p "$OUT"
run_library() {
    local tag=$1 py=$2 core=10 status=0
    local pids=()
    for wg in RAN1 RAN2 RAN3 RAN4 RAN5; do
        taskset -c "$core" "$py" -B "$A/replay_stored_sql.py" --wg "$wg" --out "$OUT/${wg}_${tag}.json" >> "$OUT/run_${tag}.log" 2>&1 &
        pids+=($!)
        core=$((core + 1))
    done
    for pid in "${pids[@]}"; do wait "$pid" || status=1; done
    echo "exit_${tag}=$status $(date +%H:%M:%S)" >> "$OUT/run.log"
}
echo "start $(date +%H:%M:%S)" >> "$OUT/run.log"
run_library new "$1"
run_library old "$2"
