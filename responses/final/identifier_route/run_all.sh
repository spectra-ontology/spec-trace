#!/usr/bin/env bash
# 식별자 경로 읽기 네 실행을 차례로 돈다(원문 경로 · 기록 필드 경로 × qwen2.5:14b · llama3.1:8b).
# 원문 경로는 그 측정(`measure_raw_source_route.py`)이 쓴 `ceiling.json` · `orders.jsonl` 을 읽으므로 측정이 끝난 뒤에만
# 돈다. 본 실행 앞에 모델마다 원문 경로 열 문항 처리량 표본을 잰다. 하나가 실패해도 다음 실행으로 넘어가고,
# 시작 · 끝 시각과 종료 코드를 남긴다. 다시 돌리면 끝난 문항은 건너뛴다.
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)" || exit 1
S=scripts/publication/paper/ongoing/sigir-2027-research
T=logs/publication/paper/ongoing/sigir-2027-research/final
R=$T/identifier_route
if pgrep -f measure_raw_source_route.py > /dev/null || [ ! -s "$T/raw_source_route/ceiling.json" ]; then
  echo '{"error": "원문 경로 측정이 끝나지 않았다"}'
  exit 1
fi
reader() {
  echo "{\"start\": \"$*\", \"at\": \"$(date -Is)\"}"
  PYTHONPATH=scripts/common:$S .venv/bin/python $S/run_identifier_route_reader.py "$@"
  code=$?
  echo "{\"end\": \"$*\", \"exit\": $code, \"at\": \"$(date -Is)\"}"
}
warm() {
  curl -s localhost:11434/api/generate -d "{\"model\": \"$1\", \"prompt\": \"hi\", \"stream\": false, \"options\": {\"num_ctx\": 16384, \"num_predict\": 1}}" > /dev/null
}
for model in qwen2.5:14b llama3.1:8b; do
  warm "$model"
  reader --route raw_source --model "$model" --sample 10 --out-dir $R/throughput_sample --throughput-out $R/throughput.json
done
warm qwen2.5:14b
reader --route raw_source --model qwen2.5:14b
reader --route hopkey --model qwen2.5:14b
warm llama3.1:8b
reader --route raw_source --model llama3.1:8b
reader --route hopkey --model llama3.1:8b
