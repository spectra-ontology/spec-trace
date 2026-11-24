"""엔진 단락(RQ5 · 표 tab:engines · F7)에 쓰는 수치를 측정 기록에서 다시 계산한다.
usage: engine_numbers.py <analysis-dir>   (표 행과 수치 목록을 출력한다)
check_vldb_text.py 는 values() 의 문자열을 조각 파일의 허용 목록으로 읽는다."""
import json, sys
from pathlib import Path


def fmt(ms):
    """10 ms 이상은 소수 한 자리, 1 ms 이상은 두 자리, 그 아래는 세 자리."""
    return f"{ms:.1f}" if ms >= 10 else f"{ms:.2f}" if ms >= 1 else f"{ms:.3f}"


def load(analysis):
    a = Path(analysis)
    read = lambda name: json.loads((a / name).read_text())
    return {"s350": read("sql_plan_variants_sqlite350.json"), "s337": read("sql_plan_variants_sqlite337.json"),
            "pg": read("sql_plan_variants_postgres17.json"), "ref": read("reference_query_timing.json"),
            "cost": read("stored_cost_inventory.json"),
            "cap337": read("cap_library_ran1_runB_sqlite337.json"), "cap350": read("cap_library_ran1_runB_sqlite350.json"),
            "replay": read("release_replay_summary.json")}


def table(d):
    """revision_chain 82문항의 문항별 중앙값을 다시 모은 중앙값(p95), 조건별."""
    rc = lambda eng, cond: d[eng]["conditions"][cond]["byFamily"]["revision_chain"]
    pg = lambda cond: d["pg"]["conditions"][cond]["byFamily"]["revision_chain"]["total"]
    cell = lambda s: (fmt(s["medianMs"]), fmt(s["p95Ms"]))
    return [("stored", cell(rc("s350", "stored")), cell(rc("s337", "stored")), cell(pg("stored"))),
            ("materializedHint", cell(rc("s350", "materializedHint")), cell(rc("s337", "materializedHint")), cell(pg("stored.materializedHint"))),
            ("orderedJoin", cell(rc("s350", "orderedJoin")), cell(rc("s337", "orderedJoin")), cell(pg("stored.orderedJoin"))),
            ("analyzed", cell(rc("s350", "analyzed")), cell(rc("s337", "analyzed")), cell(pg("analyzed"))),
            ("analyzed.orderedJoin", None, None, cell(pg("analyzed.orderedJoin")))]


def values(analysis):
    """본문에 쓰는 수치 문자열 → 근거. 표의 수치와 문장의 수치를 모두 담는다."""
    d = load(analysis)
    out = {}
    def put(s, why):
        out.setdefault(s, why)
    for row in table(d):
        for eng, c in zip(("SQLite 3.50.4", "SQLite 3.37.2", "PostgreSQL 17.11"), row[1:]):
            if c:
                put(c[0], f"{eng} {row[0]} revision_chain median ms")
                put(c[1], f"{eng} {row[0]} revision_chain p95 ms")
    sq = d["ref"]["sqlite"]["byFamily"]
    other = [v["medianMs"] for f, v in sq.items() if f != "revision_chain"]
    put(fmt(min(other)), "reference timing SQLite 3.50.4, smallest median of the six non-recursive families")
    put(fmt(max(other)), "reference timing SQLite 3.50.4, largest median of the six non-recursive families")
    put(fmt(sq["revision_chain"]["medianMs"]), "reference timing SQLite 3.50.4, revision_chain median ms (same run as the six families)")
    neo = d["ref"]["neo4j"]["byFamily"]
    put(f"{min(v['medianMs'] for v in neo.values()):.1f}", "reference timing Neo4j, smallest family median ms (round trip included)")
    put(f"{max(v['medianMs'] for v in neo.values()):.1f}", "reference timing Neo4j, largest family median ms")
    put(fmt(neo["revision_chain"]["medianMs"]), "reference timing Neo4j revision_chain median ms")
    pga = d["pg"]["conditions"]["analyzed"]["byFamily"]["revision_chain"]
    put(fmt(pga["planning"]["medianMs"]), "PostgreSQL analyzed revision_chain median planning ms")
    seq = d["pg"]["conditions"]["stored"]["sequentialScansByFamily"]["revision_chain"]
    put(str(seq["disposition"]), "PostgreSQL stored: revision_chain items whose plan scans disposition sequentially")
    put(str(d["s350"]["design"]["revisionChainItems"]), "revision_chain items")
    put(str(d["s350"]["design"]["timedPasses"]), "timed passes per item")
    sql = d["cost"]["queryWriters"]["conditions"]["sql_claude"]["all"]
    cyp = d["cost"]["queryWriters"]["conditions"]["cypher_claude"]["all"]
    put(f"{sql['count']:,}", "Claude-written SQL executions (runs A-J)")
    put(str(sql["over1s"]), "SQL executions above 1 s")
    put(str(sql["atOrAbove60sOrTimeoutError"]), "SQL executions at the 60 s cap")
    put(str(cyp["over1s"]), "Cypher executions above 1 s")
    put(f"{cyp['max']:.1f}", "longest Cypher execution s")
    put(str(int(d["cap337"]["capSeconds"])), "cap of the library re-execution s")
    secs = sorted(r["seconds"] for r in d["cap350"]["results"])
    assert all(r["exact"] == 1 for r in d["cap350"]["results"]) and all(r["error"] == "interrupted" for r in d["cap337"]["results"])
    put(f"{secs[0]:.2f}", "fastest of the three re-executed queries under SQLite 3.50.4, s")
    put(f"{secs[-1]:.2f}", "slowest of the three, s")
    put(str(len(secs)), "re-executed interrupted queries")
    # 두 판 재실행과 MATERIALIZED 재실행: summarize_release_replay.py 의 집계에서 읽는다.
    rr = d["replay"]["totals"]
    assert rr["opus.executions"] == sql["count"] and rr["opus.lostUnderNew"] == rr["opus.lostUnderNewByCap"] == rr["hint.cappedOnlyUnderNew"]
    assert len(d["replay"]["gainedUnderNew"]) == len(secs) and rr["codex.outcomeDiffersOldNew"] == 0
    put(f"{rr['opus.oldExact']:,}", "stored SQL returning gold rows when re-run under SQLite 3.37.2")
    put(f"{rr['opus.newExact']:,}", "stored SQL returning gold rows when re-run under SQLite 3.50.4")
    put(str(rr["opus.oldCapped"]), "re-run executions at the cap under SQLite 3.37.2")
    put(str(rr["opus.newCapped"]), "re-run executions at the cap under SQLite 3.50.4")
    put(str(rr["opus.lostUnderNew"]), "executions gold under 3.37.2 and capped under 3.50.4")
    for fam in ("clause_history", "pack_origin"):
        put(str(d["replay"]["lostUnderNewByFamily"][fam]), f"losses in {fam}")
    put(str(rr["hint.cappedOnlyUnderNewWithFlippedCte"]), "losses with a CTE materialized by 3.37.2 and run as a co-routine by 3.50.4")
    put(str(rr["hint.goldUnderNewWithHint"]), "of those, gold rows under 3.50.4 with MATERIALIZED")
    put(f"{rr['codex.executions']:,}", "Codex SQL executions, same outcome under both releases")
    gained = sorted(x["newSeconds"] for x in d["replay"]["gainedUnderNew"])
    put(f"{gained[0]:.2f}", "replay: fastest of the executions capped under 3.37.2 and gold under 3.50.4, s")
    put(f"{gained[-1]:.2f}", "replay: slowest of those, s")
    differs = sorted(x["storedSeconds"] for x in d["replay"]["oldReplayDiffersFromStored"])
    put(f"{differs[0]:.1f}", "stored seconds of the replay-only caps under 3.37.2, lowest")
    put(f"{differs[-1]:.1f}", "highest")
    for cap in (1, 10, 30):
        put(str(cap), "lower cap applied to the recorded replay times, s")
        put(f"{rr[f'opus.oldExactWithin{cap}s']:,}", f"replay gold within {cap} s under SQLite 3.37.2")
        put(f"{rr[f'opus.newExactWithin{cap}s']:,}", f"replay gold within {cap} s under SQLite 3.50.4")
    put(f"{100 * rr['opus.oldExact'] / rr['opus.executions']:.1f}", "percent gold under 3.37.2")
    put(f"{100 * rr['opus.newExact'] / rr['opus.executions']:.1f}", "percent gold under 3.50.4")
    # 판본 문자열: 숫자 추출 규칙이 '3.50.4' 를 '3.50' 과 '4' 로 나눈다
    versions = [d["s350"]["context"]["sqliteLibrary"], d["s337"]["context"]["sqliteLibrary"],
                d["pg"]["context"]["settings"]["server_version"]]
    neo_v = {c["versions"][0] for wg in d["ref"]["context"]["neo4j"].values() if isinstance(wg, dict) and "components" in wg
             for c in wg["components"]}
    versions += sorted(neo_v)
    for v in versions:
        bits = v.split(".")
        put(".".join(bits[:2]), f"engine version {v}")
        for b in bits[2:]:
            put(b, f"engine version {v}")
    return out, versions


if __name__ == "__main__":
    d = load(sys.argv[1])
    for row in table(d):
        print(row)
    vals, versions = values(sys.argv[1])
    print("versions", versions)
    for k, v in vals.items():
        print(f"{k:>8}  {v}")
