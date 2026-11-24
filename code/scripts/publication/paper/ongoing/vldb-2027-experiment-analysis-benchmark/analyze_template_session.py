"""저장된 응답을 질문 틀과 풀이 세션 단위로 다시 묶어 정답 수와 구간을 잰다 (모델 호출 · 데이터베이스 질의 없음).

무엇을 재는가.
- 채점 규칙은 둘이다. 주 규칙(`identity`)은 `score_meeting_spelling_sensitivity.py` 의 `same_meeting` 규칙으로,
  `cell_key()` 뒤 `tsg_meeting` · `wg_meeting` 칸 끝의 `-e` 를 양쪽에서 지운 행 집합이 같으면 정답이다. 단 기록이
  `#N` 과 `#N-e` 를 서로 다른 회의로 함께 담은 이름(`separately_recorded_meetings()`)은 `-e` 를 지우지 않는다.
  보조 규칙(`recorded`)은 `cell_key()` 만 적용한 행 집합 일치다. 응답에 적힌 질문 SHA-256 이 현재 문항 질문과
  다르면 낡은 응답으로 세고 정답으로 치지 않는다.
- 질문 틀: `build_chain_items.FAMILIES` 의 질문 문장 틀을 정규식으로 바꾸어 667 문항 질문 각각이 자기 종류의
  틀과 완전히 맞는지 본다. 틀은 (종류, 질문 틀) 이고, 틀마다 문항 수와 조건마다의 정답 수를 적는다.
  WG 이름도 틀의 빈칸이므로 (종류, WG) 로 채운 35 개 사례도 함께 적는다.
- 풀이 세션: 각 조건의 하위 에이전트 프롬프트(`chain_eval/subagent_model_provenance.json` 의 `prompt`)가 읽으라고
  지시한 입력 파일을 열어, 문항이 어느 세션에 들어갔는지 되찾는다. 질의 작성(Text2Cypher · Text2SQL)은
  (WG, 실행) 이 한 세션이고, 글 검색 계열은 (WG, 분할, 실행) 이 한 세션이다.
- 세션 다시 뽑기 구간: Opus 질의 작성 실행 A~J 의 세션(언어마다 50)을 복원 추출해 정답 비율(정답 수 합 / 문항 수 합)의
  백분위 95% 구간을 낸다. 층 없이 50 개를 뽑는 구간과 WG 마다 그 WG 의 세션 수만큼 뽑는 층화 구간을 함께 적는다.
  10,000 회, 씨앗 20261113. 글 검색 계열의 여러 실행 조건도 같은 방법으로 덧붙인다.
- 군집 다시 뽑기 구간: 실행 하나(표의 한 행)마다 35 개 (WG, 종류) 군집을 복원 추출한 정답 비율 구간.
  `final/repeated_runs/analysis_plan.json` 과 같은 씨앗 20261112 · 10,000 회 · 군집 순서((WG, 종류) 정렬)를 써서
  모든 행이 같은 다시 뽑기 표를 공유한다.

사용 (저장소 루트에서):
    .venv/bin/python3 -I scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/analyze_template_session.py [--out <json>]
기본 출력은 `final/next_cycle/analysis/m2_template_session.json` 이다.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_chain_items import FAMILIES  # noqa: E402
from score_meeting_spelling_sensitivity import exact, make_row_key, separately_recorded_meetings  # noqa: E402

ROOT = next(path for path in Path(__file__).resolve().parents if (path / ".git").exists())
KEPT = separately_recorded_meetings()
IDENTITY_KEY = make_row_key("same_meeting", KEPT)
RECORDED_KEY = make_row_key("recorded", KEPT)
TRACK = "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
CE = f"{TRACK}/chain_eval"
SUPPLEMENT = f"{TRACK}/final/supplement_cycle"
ITEMS = [f"{TRACK}/integration/items_final/gate/core/chain_items_admitted.jsonl",
         f"{TRACK}/integration/items_final/gate/ran5/chain_items_admitted.jsonl"]
PROVENANCE = f"{CE}/subagent_model_provenance.json"
DEFAULT_OUT = f"{TRACK}/final/next_cycle/analysis/m2_template_session.json"
WGS = [f"RAN{n}" for n in range(1, 6)]
RUNS = "ABCDEFGHIJ"
RESAMPLES = 10_000
CLUSTER_SEED = 20261112
SESSION_SEED = 20261113
INPUT_FILE = re.compile(r"logs/[^\s\"']+?\.json")


def per_wg(pattern: str) -> list[str]:
    return [pattern.format(wg=wg) for wg in WGS]


def provenance_key(method: str, run: str) -> str:
    """조건 · 실행이 기록된 `subagent_model_provenance.json` 의 조건 이름."""
    if method in ("claude_text2cypher", "claude_text2sql"):
        lang = method.split("_")[1]
        if run in "AB":
            return f"{lang}_runA_runB"
        return f"{lang}_runs_C_to_E" if run in "CDE" else f"{lang}_runs_F_to_J"
    base = {"text_search": "text_search", "text_search_text_only": "text_search_text_only",
            "raw_index": "raw_index", "dense_tool": "dense_tool", "dense_tool_capped": "dense_tool_capped"}[method]
    if method in ("text_search", "text_search_text_only"):
        return base if run == "A" else f"{base}_run{run}"
    return f"{base}_run{run}"


def conditions() -> list[dict]:
    """채점할 모든 조건과 실행. `session` 은 풀이 세션 단위(`wg` 또는 `part`), Codex 는 프롬프트 기록이 없어 `None`."""
    out = []
    for run in RUNS:
        out.append({"name": f"claude_text2cypher_run{run}", "method": "claude_text2cypher", "run": run,
                    "session": "wg", "files": per_wg(f"{CE}/{{wg}}_text2cypher_claude_subagent_run{run}.jsonl")})
    for run in RUNS:
        out.append({"name": f"claude_text2sql_run{run}", "method": "claude_text2sql", "run": run,
                    "session": "wg", "files": per_wg(f"{CE}/text2sql/{{wg}}_text2sql_run{run}.jsonl")})
    text_search = {"A": f"{CE}/text_search_full/{{wg}}_text_search_claude_subagent.jsonl",
                   "B": f"{CE}/text_search_full_runB/{{wg}}_text_search_claude_subagent.jsonl",
                   "C": f"{CE}/text_search_full_runC/{{wg}}_text_search_claude_subagent.jsonl"}
    text_only = {"A": f"{CE}/text_only_full/{{wg}}_text_search_text_only_claude_subagent.jsonl",
                 "B": f"{SUPPLEMENT}/text_only_agent/runB/collected/{{wg}}_text_only_claude_subagent.jsonl",
                 "C": f"{SUPPLEMENT}/text_only_agent/runC/collected/{{wg}}_text_only_claude_subagent.jsonl"}
    for method, table in (("text_search", text_search), ("text_search_text_only", text_only)):
        for run, pattern in table.items():
            out.append({"name": f"{method}_run{run}", "method": method, "run": run, "session": "part",
                        "files": per_wg(pattern)})
    for method, folder, stem, runs in (("raw_index", "raw_agent", "raw_index", "AB"),
                                       ("dense_tool", "dense_agent", "dense_tool", "AB"),
                                       ("dense_tool_capped", "dense_capped_agent", "dense_tool_capped", "A")):
        for run in runs:
            out.append({"name": f"{method}_run{run}", "method": method, "run": run, "session": "part",
                        "files": per_wg(f"{SUPPLEMENT}/{folder}/run{run}/collected/{{wg}}_{stem}_claude_subagent.jsonl")})
    for name, pattern in (("codex_text2cypher", f"{CE}/codex/chain_cy_{{wg}}_codex.jsonl"),
                          ("codex_text2sql", f"{CE}/codex/chain_sql_{{wg}}_codex.jsonl"),
                          ("codex_v2_cy_dom", f"{CE}/codex_v2/responses/{{wg}}_cy_dom_codex.jsonl"),
                          ("codex_v2_cy_exp", f"{CE}/codex_v2/responses/{{wg}}_cy_exp_codex.jsonl"),
                          ("codex_v2_sql_dom", f"{CE}/codex_v2/responses/{{wg}}_sql_dom_codex.jsonl"),
                          ("codex_v2_sql_exp", f"{CE}/codex_v2/responses/{{wg}}_sql_exp_codex.jsonl")):
        out.append({"name": name, "method": name, "run": "A", "session": None, "files": per_wg(pattern)})
    return out


def load_items() -> dict[str, dict]:
    items = {}
    for path in ITEMS:
        for line in (ROOT / path).read_text().splitlines():
            item = json.loads(line)
            if item["id"] in items:
                raise SystemExit(f"문항 id 중복: {item['id']}")
            items[item["id"]] = item
    return items


def load_responses(condition: dict, items: dict) -> tuple[dict, dict]:
    """조건의 응답(id → 기록)과 점검 수치. 낡은 질문 · 중복 · 문항 밖 id 를 센다."""
    sha = {i: hashlib.sha256(item["question"].encode()).hexdigest() for i, item in items.items()}
    records, tally = {}, collections.Counter()
    for path in condition["files"]:
        for line in (ROOT / path).read_text().splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            identifier = record["id"]
            if identifier not in items:
                tally["notInItems"] += 1
                continue
            if identifier in records:
                tally["duplicate"] += 1
            if record.get("questionSha256") != sha[identifier]:
                tally["staleQuestion"] += 1
                continue
            records[identifier] = record
    tally["missing"] = len(set(items) - set(records))
    return records, dict(tally)


def outcomes(items: dict, records: dict) -> dict[str, dict[str, bool]]:
    """규칙 → 문항 id → 정답 여부. 응답이 없거나 낡은 문항은 거짓이다."""
    result = {"identity": {}, "recorded": {}}
    for identifier, item in items.items():
        rows = records[identifier].get("rows") if identifier in records else None
        result["identity"][identifier] = exact(item, rows, IDENTITY_KEY)
        result["recorded"][identifier] = exact(item, rows, RECORDED_KEY)
    return result


def template_regex(template: str) -> re.Pattern:
    """`{slot}` 빈칸을 이름 있는 묶음으로, 두 번째부터는 같은 값을 요구하는 역참조로 바꾼 정규식."""
    pattern, seen, last = "", set(), 0
    for match in re.finditer(r"\{(\w+)\}", template):
        pattern += re.escape(template[last:match.start()])
        slot = match.group(1)
        pattern += f"(?P={slot})" if slot in seen else f"(?P<{slot}>.+?)"
        seen.add(slot)
        last = match.end()
    return re.compile(pattern + re.escape(template[last:]))


def assign_templates(items: dict) -> tuple[dict, dict, list]:
    templates, of_item, unmatched = {}, {}, []
    for family, spec in FAMILIES.items():
        slots = list(dict.fromkeys(re.findall(r"\{(\w+)\}", spec["question"])))
        templates[family] = {"family": family, "template": spec["question"], "slots": slots,
                             "regex": template_regex(spec["question"])}
    for identifier, item in items.items():
        match = templates[item["family"]]["regex"].fullmatch(item["question"])
        if not match:
            unmatched.append(identifier)
            continue
        if "wg" in match.groupdict() and match.group("wg") != item["wg"]:
            unmatched.append(identifier)
            continue
        of_item[identifier] = item["family"]
    return templates, of_item, unmatched


def session_assignment(condition: dict, items: dict, provenance: dict, packet_of: dict) -> tuple[dict, dict]:
    """프롬프트가 지시한 입력 파일로 문항 → 세션 이름을 되찾는다. 점검 결과를 함께 낸다."""
    key = provenance_key(condition["method"], condition["run"])
    entries = provenance["conditions"].get(key)
    if entries is None:
        raise SystemExit(f"세션 기록 없음: {key}")
    item_of_packet = {packet: identifier for identifier, packet in packet_of.items()}
    session_of, agents, inputs = {}, collections.Counter(), {}
    run_label = f"run{condition['run']}"
    for wg in WGS:
        for entry in entries.get(wg, []):
            if condition["session"] == "wg" and entry.get("run") != run_label:
                continue
            name = f"{wg}/{run_label}" + (f"/{entry['part']}" if condition["session"] == "part" else "")
            agents[name] += 1
            prompt = (ROOT / CE / entry["prompt"]).resolve()
            found = INPUT_FILE.search(prompt.read_text())
            if not found:
                raise SystemExit(f"프롬프트에서 입력 파일을 찾지 못함: {prompt}")
            inputs[name] = found.group()
            packet = json.loads((ROOT / found.group()).read_text())
            for entry_item in packet["items"]:
                identifier = item_of_packet.get(entry_item["id"], entry_item["id"])
                if identifier not in items:
                    raise SystemExit(f"입력 파일 문항을 문항 id 로 되돌리지 못함: {entry_item['id']} ({found.group()})")
                if identifier in session_of and session_of[identifier] != name:
                    raise SystemExit(f"한 문항이 두 세션에 들어감: {identifier}")
                session_of[identifier] = name
    check = {"provenanceCondition": key, "sessions": len(agents),
             "sessionsWithRelaunchedAgent": sorted(name for name, n in agents.items() if n > 1),
             "itemsAssigned": len(session_of), "itemsUnassigned": len(set(items) - set(session_of)),
             "inputFiles": dict(sorted(inputs.items()))}
    return session_of, check


def rate_interval(values: np.ndarray) -> list[float]:
    return [round(100 * float(x), 2) for x in np.percentile(values, [2.5, 97.5])]


def session_bootstrap(sessions: list[dict], rule: str) -> dict:
    """세션 목록(각각 wg · total · 규칙별 정답 수)을 복원 추출한 정답 비율 구간. 층 없음과 WG 층화 둘."""
    hits = np.array([s[rule] for s in sessions], dtype=float)
    totals = np.array([s["total"] for s in sessions], dtype=float)
    rng = np.random.default_rng(SESSION_SEED)
    draw = rng.integers(0, len(sessions), size=(RESAMPLES, len(sessions)))
    plain = hits[draw].sum(1) / totals[draw].sum(1)
    rng = np.random.default_rng(SESSION_SEED)
    strat_hits, strat_totals = np.zeros(RESAMPLES), np.zeros(RESAMPLES)
    for wg in WGS:
        index = np.array([i for i, s in enumerate(sessions) if s["wg"] == wg])
        pick = index[rng.integers(0, len(index), size=(RESAMPLES, len(index)))]
        strat_hits += hits[pick].sum(1)
        strat_totals += totals[pick].sum(1)
    return {"sessions": len(sessions), "answered": int(hits.sum()), "total": int(totals.sum()),
            "answeredPercent": round(100 * hits.sum() / totals.sum(), 2),
            "unstratified95Percent": rate_interval(plain),
            "wgStratified95Percent": rate_interval(strat_hits / strat_totals)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=ROOT / DEFAULT_OUT)
    args = parser.parse_args()

    items = load_items()
    order = sorted(items)
    templates, template_of, unmatched = assign_templates(items)
    provenance = json.loads((ROOT / PROVENANCE).read_text())
    cluster_names = sorted({(item["wg"], item["family"]) for item in items.values()})
    cluster_index = {name: c for c, name in enumerate(cluster_names)}
    cluster_of = np.array([cluster_index[(items[i]["wg"], items[i]["family"])] for i in order])
    cluster_draw = np.random.default_rng(CLUSTER_SEED).integers(0, len(cluster_names),
                                                                 size=(RESAMPLES, len(cluster_names)))

    conds = conditions()
    loaded = {}
    packet_of: dict[str, str] = {}
    for condition in conds:
        records, tally = load_responses(condition, items)
        loaded[condition["name"]] = (records, tally)
        for identifier, record in records.items():
            if "packetId" in record:
                if packet_of.setdefault(identifier, record["packetId"]) != record["packetId"]:
                    raise SystemExit(f"한 문항에 두 packetId: {identifier}")

    per_condition, sessions_out, cluster_rows, outcome_arrays = {}, {}, {}, {}
    session_tables: dict[str, list[dict]] = collections.defaultdict(list)
    for condition in conds:
        records, tally = loaded[condition["name"]]
        result = outcomes(items, records)
        outcome_arrays[condition["name"]] = {rule: np.array([result[rule][i] for i in order], dtype=float)
                                             for rule in result}
        by_template = {}
        for family in templates:
            members = [i for i in order if template_of.get(i) == family]
            by_template[family] = {"items": len(members),
                                   **{rule: sum(result[rule][i] for i in members) for rule in result}}
        by_instance = collections.defaultdict(lambda: collections.Counter())
        for identifier in order:
            name = f"{items[identifier]['family']}|{items[identifier]['wg']}"
            by_instance[name]["items"] += 1
            for rule in result:
                by_instance[name][rule] += result[rule][identifier]
        per_condition[condition["name"]] = {
            "method": condition["method"], "run": condition["run"], "checks": tally,
            "answered": {rule: sum(result[rule].values()) for rule in result},
            "byTemplate": by_template,
            "missesByTemplateInstance": {name: c["items"] - c["identity"] for name, c in sorted(by_instance.items())
                                         if c["items"] - c["identity"]},
            "missedItems": [i for i in order if not result["identity"][i]],
        }
        # 군집 다시 뽑기(실행 한 행)
        row = {}
        for rule in result:
            hits = np.bincount(cluster_of, weights=[result[rule][i] for i in order], minlength=len(cluster_names))
            totals = np.bincount(cluster_of, minlength=len(cluster_names)).astype(float)
            values = hits[cluster_draw].sum(1) / totals[cluster_draw].sum(1)
            row[rule] = {"answered": int(hits.sum()), "answeredPercent": round(100 * hits.sum() / totals.sum(), 2),
                         "cluster95Percent": rate_interval(values)}
        cluster_rows[condition["name"]] = row
        if condition["session"] is None:
            continue
        session_of, check = session_assignment(condition, items, provenance, packet_of)
        table = collections.defaultdict(lambda: collections.Counter())
        for identifier in order:
            name = session_of.get(identifier, "unassigned")
            table[name]["total"] += 1
            for rule in result:
                table[name][rule] += result[rule][identifier]
        rows = [{"session": name, "wg": name.split("/")[0], "total": c["total"],
                 "identity": c["identity"], "recorded": c["recorded"]} for name, c in sorted(table.items())]
        session_tables[condition["method"]].extend(rows)
        misses = {r["session"]: r["total"] - r["identity"] for r in rows if r["total"] - r["identity"]}
        sessions_out[condition["name"]] = {
            "unit": condition["session"], "check": check, "perSession": rows,
            "missTotal": sum(misses.values()), "sessionsWithMisses": len(misses),
            "sessionsContainingAllMisses": sorted(misses, key=lambda s: -misses[s]),
        }

    # 여러 실행 조건의 평균 행에 대한 군집 구간(뽑힌 군집의 모든 실행을 더한다)
    method_rows = {}
    by_method = collections.defaultdict(list)
    for condition in conds:
        by_method[condition["method"]].append(condition["name"])
    for method, names in by_method.items():
        if len(names) < 2:
            continue
        row = {}
        for rule in ("identity", "recorded"):
            hits = sum(np.bincount(cluster_of, weights=outcome_arrays[name][rule], minlength=len(cluster_names))
                       for name in names)
            totals = np.bincount(cluster_of, minlength=len(cluster_names)).astype(float) * len(names)
            values = hits[cluster_draw].sum(1) / totals[cluster_draw].sum(1)
            row[rule] = {"runs": len(names), "meanAnswered": round(hits.sum() / len(names), 2),
                         "answeredPercent": round(100 * hits.sum() / totals.sum(), 2),
                         "cluster95Percent": rate_interval(values)}
        method_rows[method] = row

    bootstrap = {}
    for method, rows in session_tables.items():
        bootstrap[method] = {rule: session_bootstrap(rows, rule) for rule in ("identity", "recorded")}
        if method in ("claude_text2cypher", "claude_text2sql"):
            first_five = [r for r in rows if r["session"].split("/")[1] in {f"run{x}" for x in "ABCDE"}]
            bootstrap[method + "_runs_A_to_E"] = {rule: session_bootstrap(first_five, rule)
                                                  for rule in ("identity", "recorded")}

    # 틀별 실패 집계(Opus 질의 작성 실행 A~J)
    miss_share = {}
    for method in ("claude_text2cypher", "claude_text2sql"):
        names = by_method[method]
        totals = collections.Counter()
        for name in names:
            for family, counts in per_condition[name]["byTemplate"].items():
                totals[family] += counts["items"] - counts["identity"]
        overall = sum(totals.values())
        miss_share[method] = {"misses": overall, "byTemplate": {
            family: {"misses": n, "sharePercent": round(100 * n / overall, 1) if overall else 0.0,
                     "itemRuns": 10 * sum(1 for i in order if template_of.get(i) == family)}
            for family, n in totals.most_common()}}

    distinct_strings = len({t["template"] for t in templates.values()})
    report = {
        "rules": {"identity": "trailing '-e' removed from tsg_meeting and wg_meeting cells on both sides after "
                              "cell_key(), except names the records hold as a separate meeting next to the same "
                              "number without '-e' (score_meeting_spelling_sensitivity same_meeting)",
                  "keptElectronicSpellings": sorted(KEPT),
                  "recorded": "cell_key() only (score_meeting_spelling_sensitivity recorded)",
                  "staleQuestion": "a response whose questionSha256 differs from sha256(item question) counts as "
                                   "not answered"},
        "items": ITEMS, "itemCount": len(items),
        "templates": {
            "definition": "(family, question template) from build_chain_items.FAMILIES; every question is "
                          "full-matched against its family template with slot back-references",
            "templates": len(templates), "distinctTemplateStrings": distinct_strings,
            "sharedTemplateString": [sorted(f for f, t in templates.items() if t["template"] == s)
                                     for s in {t["template"] for t in templates.values()}
                                     if sum(t["template"] == s for t in templates.values()) > 1],
            "templateInstancesFamilyWg": len(cluster_names),
            "unmatchedQuestions": unmatched,
            "perTemplate": {family: {"template": t["template"], "slots": t["slots"],
                                     "items": sum(1 for i in order if template_of.get(i) == family),
                                     "itemsByWg": dict(sorted(collections.Counter(
                                         items[i]["wg"] for i in order if template_of.get(i) == family).items()))}
                            for family, t in templates.items()},
        },
        "conditions": per_condition,
        "missShareByTemplateOpusRunsAtoJ": miss_share,
        "sessions": sessions_out,
        "sessionBootstrap": {"resamples": RESAMPLES, "seed": SESSION_SEED,
                             "statistic": "answered items / items over the drawn sessions (item-weighted)",
                             "unstratified": "draw as many sessions as the method has, with replacement",
                             "wgStratified": "within each WG draw as many sessions as that WG has",
                             "methods": bootstrap},
        "clusterBootstrap": {"resamples": RESAMPLES, "seed": CLUSTER_SEED, "clusters": len(cluster_names),
                             "unit": "(wg, family), clusters sorted, same draw table for every row",
                             "perRun": cluster_rows, "methodMean": method_rows},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    for name, info in per_condition.items():
        print(name, info["answered"], info["checks"])


if __name__ == "__main__":
    main()
