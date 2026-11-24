# Per-item diagnosis of the Codex value-domain and exploration Text-to-Cypher runs, run from the repository root.
# Reads the stored responses and re-runs each missed query against the loaded RAN1-RAN5 graphs; no model call.
S=scripts/publication/paper/ongoing/sigir-2027-research
L=logs/publication/paper/ongoing/sigir-2027-research
O=$L/final/codex_rerun/cypher_miss_diagnosis
RESP=$(ls $L/chain_eval/codex_v2/responses/RAN*_cy_*_codex.jsonl)
PYTHONPATH=scripts/common:$S python3 -B $S/diagnose_subagent_misses.py \
  --items $L/integration/items_final/gate/core/chain_items_admitted.jsonl $L/integration/items_final/gate/ran5/chain_items_admitted.jsonl \
  --responses $RESP \
  --bolt RAN1=bolt://localhost:7687 --bolt RAN2=bolt://localhost:7688 --bolt RAN3=bolt://localhost:7689 \
  --bolt RAN4=bolt://localhost:7690 --bolt RAN5=bolt://localhost:7691 \
  --out $O.json > $O.stdout 2> $O.stderr
