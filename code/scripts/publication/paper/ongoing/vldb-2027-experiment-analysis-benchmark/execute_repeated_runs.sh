#!/usr/bin/env bash
# 반복 질의 작성 실행(실행 C·D·E 등)의 질의 파일을 실행 A·B 와 같은 설정으로 실행한다 (모델 호출 없음).
#
# 실행 A·B 의 설정. 명령 줄은 따로 남아 있지 않아 저장된 응답(id 차례 · model · method 칸)과 묶음,
# 실행기 코드에서 되짚었고, 이 스크립트로 실행 A·B 를 다른 디렉토리에 다시 실행해 저장된 응답과 같은지 맞대어 확인한다.
# - 실행기 run_chain_eval.py 에 --queries 로 밖에서 쓴 질의를 주고 문항마다 한 번 실행한다.
#   --method text2cypher | text2sql, --model claude-opus-subagent-run<X>(응답의 model 칸).
# - --items 는 RAN1~RAN4 가 gate/core, RAN5 가 gate/ran5 의 chain_items_admitted.jsonl 이다.
# - Cypher 는 --bolt bolt://localhost:7687~7691(RAN1~RAN5). 실행 전에 그 포트 그래프의 스키마가 질의 작성자가 받은
#   묶음(subagent_packets/<WG>_schema.json)의 스키마와 같은 줄들인지 확인한다. 관계 유형 줄은 그래프의 관계 수 차례로
#   놓이므로, 묶음을 낸 뒤 관계 수가 달라진 그래프(RAN2 의 TRImpact 관계)에서는 줄 집합이 같고 차례만 다를 수 있다.
#   그때는 차례가 다른 줄 수를 적고 실행한다. 작성자에게 준 묶음은 실행마다 같은 파일이다.
# - SQL 은 --sqlite integration/sqlite_final/<WG>.sqlite. 실행 전에 그 파일의 표 정의가 묶음
#   (subagent_packets_sql/<WG>_schema.json)과 같은지 확인한다.
# - 주 지표는 첫 질의의 결과다. --repair-queries 를 주지 않는다(--repairs 는 기본값 2 이고 다시 쓴 질의가 없으면 쓰이지 않는다).
# - 응답은 Cypher 가 chain_eval/<WG>_text2cypher_claude_subagent_run<X>.jsonl, SQL 이
#   chain_eval/text2sql/<WG>_text2sql_run<X>.jsonl 이고, 표준 오류는 chain_eval/<WG>_subagent_run<X>.stderr 와
#   chain_eval/text2sql/<WG>_run<X>.stderr 다.
# - 실행한 뒤 실행 오류가 난 질의를 export_query_repair_requests.py 로
#   subagent_queries/repair_requests/<WG>_<언어>_run<X>_round1.jsonl 에 내보낸다(오류가 없으면 빈 파일).
# - 다시 쓴 질의 subagent_queries/<WG>_<언어>_run<X>_repair<k>.jsonl 이 있으면 k = 1, 2 차례로 --repair-queries 에 주어
#   보조 응답 <첫 응답 이름>_repair.jsonl(표준 오류 <첫 표준 오류 이름>_repair.stderr)을 따로 만든다.
#
# 질의 파일이 없거나 그 WG 문항 수보다 줄이 적으면(아직 쓰는 중) 알리고 건너뛴다. 질의 파일의 id 는 그 WG 문항의 묶음 id
# (또는 문항 id)여야 하고 문항마다 하나씩이어야 한다. 실행한 응답은 줄 수 · id · 질문 SHA-256 · model 칸을 확인한다.
# 응답이 이미 있고 완전하며 질의 파일보다 새로우면 다시 실행하지 않고 확인만 해서 따로 적는다(FORCE=1 이면 다시 실행한다).
#
# 사용: bash execute_repeated_runs.sh C [D E ...]
#   OUT_ROOT=<dir> 를 주면 응답·표준 오류·오류 내보내기를 그 디렉토리 아래(chain_eval 과 같은 상대 구조)에 쓴다.
#   실행 A·B 의 응답은 기록이므로 기본 위치에는 다시 쓰지 않는다. 재현 확인은 OUT_ROOT 를 다른 곳에 두고
#   `OUT_ROOT=<dir> bash execute_repeated_runs.sh A B` 로 한다.
set -uo pipefail

ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
cd "$ROOT" || exit 1
S=scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark
L=logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark
CHAIN=$L/chain_eval
QUERIES=$CHAIN/subagent_queries
OUT_ROOT=${OUT_ROOT:-$CHAIN}
if [ "$OUT_ROOT" = "$CHAIN" ]; then
    REQUESTS=$QUERIES/repair_requests
else
    REQUESTS=$OUT_ROOT/repair_requests
fi
export PYTHONPATH=scripts/common:$S
WGS=(RAN1 RAN2 RAN3 RAN4 RAN5)
LANGS=(text2cypher text2sql)

if [ $# -eq 0 ]; then
    echo "사용: bash $0 C [D E ...]" >&2
    exit 2
fi

items_of() {
    if [ "$1" = RAN5 ]; then
        echo "$L/integration/items_final/gate/ran5/chain_items_admitted.jsonl"
    else
        echo "$L/integration/items_final/gate/core/chain_items_admitted.jsonl"
    fi
}

bolt_of() { echo "bolt://localhost:$((7686 + ${1#RAN}))"; }

sqlite_of() { echo "$L/integration/sqlite_final/$1.sqlite"; }

# 질의 파일과 응답 파일을 확인한다. exit 0 = 이상 없음, 2 = 질의 파일이 아직 덜 쓰임, 1 = 내용 오류.
#   check queries  <wg> <lang> <질의 파일> <문항 파일> <bolt|sqlite>
#   check responses <wg> <lang> <응답 파일> <문항 파일> <model>
check() {
python3 -B - "$@" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

import run_chain_eval as rce

mode, wg, lang, path, items_path, target = sys.argv[1:7]
key = "sql" if lang == "text2sql" else "cypher"
items = [item for item in map(json.loads, Path(items_path).read_text().splitlines()) if item["wg"] == wg]
item_ids = {item["id"] for item in items}
n = len(items)


def records_of(file):
    lines = Path(file).read_text().splitlines()
    if any(not line.strip() for line in lines):
        print(f"  {file}: 빈 줄이 있다")
        sys.exit(1)
    try:
        return [json.loads(line) for line in lines]
    except json.JSONDecodeError as error:
        print(f"  {file}: JSON 으로 읽히지 않는 줄이 있다 ({error})")
        sys.exit(1)


if mode == "queries":
    records = records_of(path)
    to_item = rce.item_ids(items)
    bad = [r for r in records if not isinstance(r.get(key), str) or not r[key].strip() or "id" not in r]
    unknown = [r.get("id") for r in records if r.get("id") not in to_item]
    mapped = [to_item[r["id"]] for r in records if r.get("id") in to_item]
    duplicate = sorted({i for i in mapped if mapped.count(i) > 1})
    if bad or unknown or duplicate:
        print(f"  {path}: {key} 칸이 없는 줄 {len(bad)}, {wg} 문항에 없는 id {len(unknown)} {unknown[:3]}, "
              f"한 문항에 둘 이상인 id {len(duplicate)} {duplicate[:3]}")
        sys.exit(1)
    if len(mapped) < n:
        print(f"  {path}: 질의 {len(mapped)} / {n} 문항 (아직 덜 쓰임)")
        sys.exit(2)
    packet_ids = sum(r["id"] != to_item[r["id"]] for r in records)
    print(f"  질의 {len(mapped)} / {n} 문항, 묶음 id {packet_ids} · 문항 id {len(mapped) - packet_ids}")
    if lang == "text2cypher":
        from neo4j import GraphDatabase
        from common.credentials import neo4j_auth
        packet = json.loads(Path(f"logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/chain_eval/subagent_packets/{wg}_schema.json").read_text())
        driver = GraphDatabase.driver(target, auth=neo4j_auth())
        with driver.session() as session:
            schema = rce.graph_schema(session)
        driver.close()
        template = items[0].get("template") if items else None
        task = rce.cypher_task({"fields": ["<the item's fields>"], "template": template}, schema)
        if task == packet["task"]:
            print(f"  {target} 그래프 스키마 = 묶음 스키마")
        elif sorted(task.splitlines()) == sorted(packet["task"].splitlines()):
            moved = sum(a != b for a, b in zip(task.splitlines(), packet["task"].splitlines()))
            print(f"  {target} 그래프 스키마 = 묶음 스키마와 같은 줄 집합(관계 수 차례가 바뀐 관계 유형 {moved}줄의 자리만 다름)")
        else:
            print(f"  {target} 그래프 스키마가 묶음 스키마와 다르다")
            sys.exit(1)
    else:
        import sqlite3
        packet = json.loads(Path(f"logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/chain_eval/subagent_packets_sql/{wg}_schema.json").read_text())
        db = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
        if rce.sql_task({"fields": ["<the item's fields>"]}, rce.sqlite_schema(db)) != packet["task"]:
            print(f"  {target} 표 정의가 묶음 표 정의와 다르다")
            sys.exit(1)
        print(f"  {target} 표 정의 = 묶음 표 정의")
    sys.exit(0)

records = records_of(path)
model = target
ids = [r["id"] for r in records]
digest = {item["id"]: hashlib.sha256(item["question"].encode()).hexdigest() for item in items}
problems = []
if len(records) != n or set(ids) != item_ids or len(set(ids)) != len(ids):
    problems.append(f"응답 {len(records)}줄 · 고유 id {len(set(ids))} · {wg} 문항과 같은 id 집합 {set(ids) == item_ids} (문항 {n})")
stale = sum(r.get("questionSha256") != digest.get(r["id"]) for r in records)
if stale:
    problems.append(f"질문 SHA-256 이 다른 응답 {stale}")
labels = {(r.get("wg"), r.get("method"), r.get("model")) for r in records}
if labels != {(wg, lang, model)}:
    problems.append(f"wg · method · model 칸 {sorted(map(str, labels))}")
if problems:
    print(f"  {path}: " + "; ".join(problems))
    sys.exit(1)
failed = sum(r.get("rows") is None for r in records)
print(f"  응답 {len(records)} / {n} 문항, 실행 오류로 답이 없는 문항 {failed}")
PY
}

# 응답이 이미 있고 완전하며 질의 파일보다 새로우면 0.
fresh() {
    local out=$1 newest=$2 wg=$3 lang=$4 model=$5
    [ "${FORCE:-0}" = 1 ] && return 1
    [ -f "$out" ] && [ "$out" -nt "$newest" ] || return 1
    check responses "$wg" "$lang" "$out" "$(items_of "$wg")" "$model" >/dev/null
}

failures=0
executed=()
reused=()
skipped=()
for letter in "$@"; do
    if ! [[ $letter =~ ^[A-Z]$ ]]; then
        echo "실행 이름은 대문자 한 글자다: $letter" >&2
        exit 2
    fi
    if [ "$OUT_ROOT" = "$CHAIN" ] && { [ "$letter" = A ] || [ "$letter" = B ]; }; then
        echo "run$letter: 기록된 응답이므로 기본 위치에 다시 쓰지 않는다(OUT_ROOT 를 다른 곳에 두고 재현 확인)" >&2
        failures=$((failures + 1))
        continue
    fi
    run=run$letter
    model=claude-opus-subagent-$run
    for lang in "${LANGS[@]}"; do
        for wg in "${WGS[@]}"; do
            queries=$QUERIES/${wg}_${lang}_${run}.jsonl
            items=$(items_of "$wg")
            if [ "$lang" = text2cypher ]; then
                out=$OUT_ROOT/${wg}_text2cypher_claude_subagent_${run}.jsonl
                err=$OUT_ROOT/${wg}_subagent_${run}.stderr
                target=(--bolt "$(bolt_of "$wg")")
            else
                out=$OUT_ROOT/text2sql/${wg}_text2sql_${run}.jsonl
                err=$OUT_ROOT/text2sql/${wg}_${run}.stderr
                target=(--sqlite "$(sqlite_of "$wg")")
            fi
            label="$run $lang $wg"
            if [ ! -f "$queries" ]; then
                echo "건너뜀 $label: 질의 파일 없음 ($queries)"
                skipped+=("$label")
                continue
            fi
            echo "확인 $label: $queries"
            check queries "$wg" "$lang" "$queries" "$items" "${target[1]}"
            status=$?
            if [ $status -eq 2 ]; then
                echo "건너뜀 $label: 질의 파일이 아직 덜 쓰였다"
                skipped+=("$label")
                continue
            elif [ $status -ne 0 ]; then
                echo "오류 $label: 질의 파일 확인 실패"
                failures=$((failures + 1))
                continue
            fi
            mkdir -p "$(dirname "$out")" "$REQUESTS"
            if fresh "$out" "$queries" "$wg" "$lang" "$model"; then
                echo "건너뜀 $label: 응답이 이미 있다 ($out)"
                ran=0
            else
                ran=1
                echo "실행 $label → $out"
                if ! python3 -B "$S/run_chain_eval.py" --items "$items" --wg "$wg" --method "$lang" --model "$model" \
                        "${target[@]}" --queries "$queries" --out "$out" 2> "$err"; then
                    echo "오류 $label: run_chain_eval.py 실패 (표준 오류 $err)"
                    failures=$((failures + 1))
                    continue
                fi
            fi
            if ! check responses "$wg" "$lang" "$out" "$items" "$model"; then
                echo "오류 $label: 응답 확인 실패"
                failures=$((failures + 1))
                continue
            fi
            python3 -B "$S/export_query_repair_requests.py" --items "$items" --responses "$out" \
                --out "$REQUESTS/${wg}_${lang}_${run}_round1.jsonl"
            if [ $ran = 1 ]; then executed+=("$label"); else reused+=("$label"); fi
            # 기록된 다시 쓴 회차가 있으면 보조 응답을 따로 만든다. 회차 파일의 id 가 첫 질의 · 앞 회차와 맞는지는
            # run_chain_eval.py 가 실행 전에 확인하고, 맞지 않으면 실행하지 않고 멈춘다.
            repairs=()
            for k in 1 2; do
                [ -f "$QUERIES/${wg}_${lang}_${run}_repair$k.jsonl" ] || break
                repairs+=("$QUERIES/${wg}_${lang}_${run}_repair$k.jsonl")
            done
            [ ${#repairs[@]} -eq 0 ] && continue
            out_repair=${out%.jsonl}_repair.jsonl
            err_repair=${err%.stderr}_repair.stderr
            newest=${repairs[-1]}
            if fresh "$out_repair" "$newest" "$wg" "$lang" "$model"; then
                echo "건너뜀 $label 다시 쓴 회차: 응답이 이미 있다 ($out_repair)"
                continue
            fi
            echo "실행 $label 다시 쓴 회차 ${#repairs[@]}개 → $out_repair"
            if ! python3 -B "$S/run_chain_eval.py" --items "$items" --wg "$wg" --method "$lang" --model "$model" \
                    "${target[@]}" --queries "$queries" --repair-queries "${repairs[@]}" --out "$out_repair" \
                    2> "$err_repair"; then
                echo "오류 $label: 다시 쓴 회차 실행 실패 (표준 오류 $err_repair)"
                failures=$((failures + 1))
                continue
            fi
            check responses "$wg" "$lang" "$out_repair" "$items" "$model" || failures=$((failures + 1))
        done
    done
done

echo "실행하고 확인한 질의 파일 ${#executed[@]}개: ${executed[*]:-없음}"
echo "이미 있던 응답을 확인한 질의 파일 ${#reused[@]}개: ${reused[*]:-없음}"
echo "건너뛴 질의 파일 ${#skipped[@]}개: ${skipped[*]:-없음}"
echo "오류 $failures"
[ $failures -eq 0 ]
