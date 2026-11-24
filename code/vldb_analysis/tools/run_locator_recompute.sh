#!/bin/bash
cd $REPO_ROOT || exit 1
L=logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark
.venv/bin/python3 -B scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_locator_recompute.py --out $L/final/next_cycle/analysis/locator_recompute.json > $L/final/next_cycle/analysis/locator_recompute.log 2>&1
echo "exit=$?" >> $L/final/next_cycle/analysis/locator_recompute.log
