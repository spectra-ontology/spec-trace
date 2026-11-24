"""평가에 쓴 하위 에이전트 세션마다 토큰 · 도구 호출 · 걸린 시간을 대화 기록에서 센다 (모델 호출 없음).

세션 목록은 `chain_eval/subagent_model_provenance.json` 의 conditions 다(조건 → WG → 세션). 대화 기록은 Claude Code 가
남긴 하위 에이전트 기록 파일이며, 같은 메시지 id 의 사용량은 한 번만 센다(스트리밍 중 같은 메시지가 여러 줄로 남는다).
조건이 푼 문항 수는 채점에 들어간 답 파일의 줄 수다(`ANSWERS` 가 조건마다 그 파일을 적는다). 세션이 쓴 작업 사본은
세션 폴더에 있어 남지 않으므로 쓰지 않는다. 다시 띄운 세션의 앞 세션(relaunchOf)은 conditions 에 없어서 합에 들지 않는다.

결과: 조건마다 세션 수 · 문항 수 · 입력(새 입력 · 캐시 쓰기 · 캐시 읽기) · 출력 토큰 · 도구 호출 · 세션 벽시계 초의
합과 문항당 값. 세션별 행도 남긴다(대화 기록 경로는 남기지 않는다).

사용 (저장소 루트에서 실행):
  python3 measure_agent_session_cost.py --base <paper logs dir> --out <json>
"""
from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
TRANSCRIPTS = Path.home() / ".claude/projects" / str(REPO).replace("/", "-")
SC = "final/supplement_cycle"
QW = "chain_eval/subagent_queries"
ANSWERS = {
    "text2cypher_runA_runB": [f"{QW}/RAN?_text2cypher_run[AB].jsonl"],
    "text2sql_runA_runB": [f"{QW}/RAN?_text2sql_run[AB].jsonl"],
    "text2cypher_runs_C_to_E": [f"{QW}/RAN?_text2cypher_run[CDE].jsonl"],
    "text2sql_runs_C_to_E": [f"{QW}/RAN?_text2sql_run[CDE].jsonl"],
    "text2cypher_runs_F_to_J": [f"{QW}/RAN?_text2cypher_run[FGHIJ].jsonl"],
    "text2sql_runs_F_to_J": [f"{QW}/RAN?_text2sql_run[FGHIJ].jsonl"],
    "text_search": ["chain_eval/text_search_full/RAN?_text_search_claude_subagent.jsonl"],
    "text_search_runB": ["chain_eval/text_search_full_runB/RAN?_text_search_claude_subagent.jsonl"],
    "text_search_runC": ["chain_eval/text_search_full_runC/RAN?_text_search_claude_subagent.jsonl"],
    "text_search_text_only": ["chain_eval/text_only_full/RAN?_text_search_text_only_claude_subagent.jsonl"],
    "text_search_text_only_runB": [f"{SC}/text_only_agent/runB/collected/RAN?_packet_answers.jsonl"],
    "text_search_text_only_runC": [f"{SC}/text_only_agent/runC/collected/RAN?_packet_answers.jsonl"],
    "raw_index_runA": [f"{SC}/raw_agent/runA/collected/RAN?_packet_answers.jsonl"],
    "raw_index_runB": [f"{SC}/raw_agent/runB/collected/RAN?_packet_answers.jsonl"],
    "dense_tool_runA": [f"{SC}/dense_agent/runA/collected/RAN?_packet_answers.jsonl"],
    "dense_tool_runB": [f"{SC}/dense_agent/runB/collected/RAN?_packet_answers.jsonl"],
    "dense_tool_capped_runA": [f"{SC}/dense_capped_agent/runA/collected/RAN?_packet_answers.jsonl"],
    "abstention3_text_search": ["abstention3/responses/RAN?_text_search_claude_subagent.jsonl"],
    "abstention3_text_search_text_only": ["abstention3/responses/RAN?_text_search_text_only_claude_subagent.jsonl"],
    "abstention3_text2cypher_runA_runB": ["abstention3/responses/RAN?_text2cypher_claude_subagent_run[AB].jsonl"],
}


def ts(s: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def session_usage(path: Path) -> dict:
    seen, tools, first, t0, t1, models = {}, 0, None, None, None, set()
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = d.get("timestamp")
            if t:
                t0 = t0 or t
                t1 = t
            m = d.get("message") or {}
            if first is None and d.get("type") == "user":
                c = m.get("content")
                first = c if isinstance(c, str) else json.dumps(c)
            if d.get("type") == "assistant":
                if m.get("usage") and m.get("id"):
                    seen[m["id"]] = m["usage"]
                if m.get("model"):
                    models.add(m["model"])
                for b in m.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        tools += 1
    tok = {"input": 0, "cacheWrite": 0, "cacheRead": 0, "output": 0}
    for u in seen.values():
        tok["input"] += u.get("input_tokens") or 0
        tok["cacheWrite"] += u.get("cache_creation_input_tokens") or 0
        tok["cacheRead"] += u.get("cache_read_input_tokens") or 0
        tok["output"] += u.get("output_tokens") or 0
    return {"tokens": tok, "tools": tools, "turns": len(seen), "models": sorted(models),
            "seconds": (ts(t1) - ts(t0)).total_seconds() if t0 and t1 else None, "first": first or ""}


def answer_count(base: Path, patterns: list[str]) -> tuple[int, list[str]]:
    files = sorted({p for pat in patterns for p in base.glob(pat)})
    n = sum(sum(1 for line in f.read_text(encoding="utf-8").splitlines() if line.strip()) for f in files)
    return n, [str(f.relative_to(base)) for f in files]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="paper logs dir holding chain_eval/ and final/")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    base = Path(args.base)
    prov_path = base / "chain_eval/subagent_model_provenance.json"
    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    out = {"provenance": str(prov_path), "conditions": {}}
    for cond, wgs in prov["conditions"].items():
        rows = []
        for wg, entries in wgs.items():
            for e in entries:
                path = TRANSCRIPTS / e["session"] / "subagents" / f"agent-{e['agentId']}.jsonl"
                if not path.is_file():
                    rows.append({"wg": wg, "run": e.get("run"), "missing": True})
                    continue
                u = session_usage(path)
                u.pop("first")
                rows.append({"wg": wg, "run": e.get("run"), **u})
        ok = [r for r in rows if not r.get("missing")]
        tot = {k: sum(r["tokens"][k] for r in ok) for k in ("input", "cacheWrite", "cacheRead", "output")}
        items, files = answer_count(base, ANSWERS.get(cond, []))
        secs = sorted(r["seconds"] or 0 for r in ok)
        agg = {"sessions": len(rows), "missing": len(rows) - len(ok), "items": items, "answerFiles": files,
               "tokens": tot, "tools": sum(r["tools"] for r in ok), "seconds": sum(secs),
               "sessionSecondsMedian": secs[len(secs) // 2] if secs else None,
               "models": sorted({m for r in ok for m in r["models"]})}
        if items:
            agg["perItem"] = {"inputAll": (tot["input"] + tot["cacheWrite"] + tot["cacheRead"]) / items,
                              "inputUncached": (tot["input"] + tot["cacheWrite"]) / items,
                              "output": tot["output"] / items, "tools": agg["tools"] / items,
                              "seconds": agg["seconds"] / items}
        out["conditions"][cond] = {"total": agg, "sessions": rows}
        pi = agg.get("perItem") or {}
        print(f"{cond:38s} sess={len(rows):3d} miss={agg['missing']} items={items:5d} files={len(files):2d} "
              + " ".join(f"{k}={v:.1f}" for k, v in pi.items()), flush=True)
    Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
