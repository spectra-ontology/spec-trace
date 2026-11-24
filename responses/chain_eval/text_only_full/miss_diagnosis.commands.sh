# Per-item diagnosis of the text-only search misses, run from the repository root.
# Reads the stored responses and the full-text index of each working group; no model call.
S=scripts/publication/paper/ongoing/sigir-2027-research
L=logs/publication/paper/ongoing/sigir-2027-research
O=$L/chain_eval/text_only_full/miss_diagnosis
PYTHONPATH=scripts/common:$S python3 -B $S/diagnose_text_route_misses.py --route text_search_text_only \
  --out $O.json > $O.stdout 2> $O.stderr
