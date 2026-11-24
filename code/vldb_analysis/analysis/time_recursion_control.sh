#!/bin/bash
set -e
cd $REPO_ROOT
taskset -c 12-15 .venv/bin/python3 -B $REPO_ROOT/logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/next_cycle/work/vldb_draft/analysis/time_recursion_control.py --out $REPO_ROOT/logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/next_cycle/work/vldb_draft/analysis/recursion_control_sqlite350.json > $REPO_ROOT/logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/next_cycle/work/vldb_draft/analysis/recursion_control.log 2>&1
taskset -c 12-15 /usr/bin/python3 -B $REPO_ROOT/logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/next_cycle/work/vldb_draft/analysis/time_recursion_control.py --out $REPO_ROOT/logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/next_cycle/work/vldb_draft/analysis/recursion_control_sqlite337.json >> $REPO_ROOT/logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/next_cycle/work/vldb_draft/analysis/recursion_control.log 2>&1
echo done >> $REPO_ROOT/logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/next_cycle/work/vldb_draft/analysis/recursion_control.log
