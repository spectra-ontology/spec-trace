#!/usr/bin/env bash
# 다섯 작업 그룹의 MATERIALIZED 재실행을 코어 하나씩에 고정해 함께 돌린다 (저장소 루트에서 실행).
# 새 SQLite(3.50.4)에서 고정 효과를 보는 실험이므로 venv 해석기를 명시한다. systemd 유닛의 PATH 에서
# python3 는 시스템 해석기(SQLite 3.37.2)로 풀리므로 이름만 쓰면 옛 라이브러리에서 돈다.
# 옛 라이브러리에서 같은 SQL 을 돌린 대조 결과는 materialize/sqlite337_control/ 에 있다.
A=logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/next_cycle/work/vldb_draft/analysis
PY=.venv/bin/python3
lib=$("$PY" -c 'import sqlite3; print(sqlite3.sqlite_version)')
[ "$lib" = "3.50.4" ] || { echo "unexpected sqlite $lib" >> "$A/materialize/run.log"; exit 1; }
core=10
for wg in RAN1 RAN2 RAN3 RAN4 RAN5; do
  taskset -c "$core" "$PY" -B "$A/materialize_check.py" --wg "$wg" --out "$A/materialize/$wg.json" >> "$A/materialize/run.log" 2>&1 &
  core=$((core+1))
done
wait
echo "exit=$?" >> "$A/materialize/run.log"
