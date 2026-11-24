#!/bin/bash
# Codex 재실행이 남긴 질의 묶음을 고치기 없이(첫 질의만) 실행해 응답 파일을 만든다. 저장소 루트에서 실행한다.
#   bash eval_all.sh dom_cy_RAN1 exp_sql_RAN3 ...
# 그래프 질의는 해당 WG 그래프에, 관계형 질의는 해당 WG 내보내기 파일에 보낸다. 모델은 부르지 않는다.
set -u
L=logs/publication/paper/ongoing/sigir-2027-research
S=scripts/publication/paper/ongoing/sigir-2027-research
V=$L/chain_eval/codex_v2
mkdir -p "$V/responses"
for name in "$@"; do
  IFS=_ read -r cond lang wg <<< "$name"
  n=${wg#RAN}
  if [ "$wg" = RAN5 ]; then items=$L/integration/items_final/gate/ran5/chain_items_admitted.jsonl
  else items=$L/integration/items_final/gate/core/chain_items_admitted.jsonl; fi
  case $cond in dom) label=domain;; exp) label=explore;; esac
  out=$V/responses/${wg}_${lang}_${cond}_codex.jsonl
  case $lang in
    cy) target=(--method text2cypher --bolt "bolt://localhost:$((7686 + n))");;
    sql) target=(--method text2sql --sqlite "$L/integration/sqlite_final/${wg}.sqlite");;
  esac
  t0=$(date +%s)
  PYTHONPATH=scripts/common python3 "$S/run_chain_eval.py" --items "$items" --wg "$wg" "${target[@]}" \
    --model "codex-gpt-6.1-sol-$label" --queries "$V/queries/$name.jsonl" --repairs 0 --out "$out" \
    > "${out%.jsonl}.stdout" 2> "${out%.jsonl}.stderr"
  code=$?
  echo "eval $name exit=$code wall=$(( $(date +%s) - t0 ))s lines=$(wc -l < "$out" 2>/dev/null || echo 0)"
done
