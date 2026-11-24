# Per-item diagnosis of the Text-to-SQL misses of runs F to J, run from the repository root.
# Reads the stored responses and re-runs each missed query and its repair against the read-only relational exports; no model call.
S=scripts/publication/paper/ongoing/sigir-2027-research
L=logs/publication/paper/ongoing/sigir-2027-research
O=$L/final/diagnosis/text2sql_miss_diagnosis_runs_F_to_J
RESP=""
for r in F G H I J; do for w in 1 2 3 4 5; do RESP="$RESP $L/chain_eval/text2sql/RAN${w}_text2sql_run$r.jsonl"; done; done
PYTHONPATH=scripts/common:$S python3 -B $S/diagnose_text2sql_misses.py \
  --items $L/integration/items_final/gate/core/chain_items_admitted.jsonl $L/integration/items_final/gate/ran5/chain_items_admitted.jsonl \
  --responses $RESP \
  --sqlite-dir $L/integration/sqlite_final \
  --out $O.json > $O.stdout 2> $O.stderr
