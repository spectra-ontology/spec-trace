#!/usr/bin/env bash
# 식별자 경로 읽기 응답을 dense 와 같은 채점기로 묶고, 담은 문맥에 정답이 남았는지 센다. 네 실행이 끝난 뒤 돌린다.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
S=scripts/publication/paper/ongoing/sigir-2027-research
L=logs/publication/paper/ongoing/sigir-2027-research
PYTHONPATH=scripts/common:$S .venv/bin/python $S/summarize_chain_scores.py \
  --items $L/integration/items_final/gate/core/chain_items_admitted.jsonl \
          $L/integration/items_final/gate/ran5/chain_items_admitted.jsonl \
  --responses $L/chain_eval/identifier_route/*.jsonl \
  --out $L/final/identifier_route/summary.json
PYTHONPATH=scripts/common:$S .venv/bin/python $S/run_identifier_route_reader.py --judge \
  --judge-out $L/final/identifier_route/budget_containment.json
