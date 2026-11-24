# Per-item diagnosis of the dense-tool search misses of runA, run from the repository root.
# Reads the stored responses and the full-text index of each working group; no model call.
S=scripts/publication/paper/ongoing/sigir-2027-research
L=logs/publication/paper/ongoing/sigir-2027-research
O=$L/final/supplement_cycle/dense_agent/runA/miss_diagnosis
PYTHONPATH=scripts/common:$S python3 -B $S/diagnose_text_route_misses.py --route dense_tool --run runA \
  --out $O.json > $O.stdout 2> $O.stderr
