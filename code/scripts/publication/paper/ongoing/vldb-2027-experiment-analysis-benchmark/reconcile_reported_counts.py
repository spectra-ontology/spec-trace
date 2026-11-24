"""원고가 보고한 수 가운데 서로 맞지 않거나 설명이 빠진 수를 기록과 코드에서 다시 세어 맞춘다 (모델 호출 없음).

명령마다 원고의 한 자리를 다룬다.
- gate         빌드 게이트의 묶음 출처 조건(`verify_chain_items.py` 5번 검사)이 실제로 무엇을 거르는지, 저장된 게이트
               결과가 어느 입력으로 재현되는지, E4(목록의 묶음 칸) 대체가 바꾼 35 문항이 어느 쪽 불일치에서 왔는지
- clause-bases 표 3 의 절 연결 수와 판 읽기(clause_edition_readings.json)의 연결 수가 다른 까닭, 목록 release 와
               절 판이 다른 연결이 적재기의 어느 판 해소 단계에서 나왔는지, `clause_history` 문항의 두 읽기
- cr-counts    CR 142,860(목록 유형 CR)과 143,714(뒤 판이 없는 CR 양식 문서)의 정의와 둘의 차이 854 의 분해
- remainders   확인되지 않은 절 연결 1,238 가운데 두 무리 밖의 59, RAN1 처분·목록 차이 1,583 가운데 세 칸 밖의 410
- liaison      RAN1 에서 목록이 treated, 보고서가 noted 로 적은 628 문서의 유형과, 목록이 revised, 보고서가
               noted(324) 또는 endorsed(221)로 적은 545 문서의 목록 유형 · 목록에 적힌 다음 판(revisedTo)의 유무
- all          위 다섯을 차례로 실행한다

각 명령은 `logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/reconciliation/reconcile_<명령>.json` 을 쓰고,
원고의 해당 문장을 줄 번호와 함께 그대로 옮겨 둔다. 원고 파일은 읽기만 한다. 검사 하나라도 맞지 않으면 JSON 을
쓴 뒤 종료 코드 1 로 끝난다. SQLite DB 는 읽기 전용으로 열고, Neo4j 는 HTTP 읽기 질의만 보낸다.

사용: python3 reconcile_reported_counts.py {gate,clause-bases,cr-counts,remainders,liaison,all}   (저장소 루트에서 실행)
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import gc
import hashlib
import inspect
import json
import os
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE), str(ROOT / "scripts" / "common"), str(ROOT / "scripts" / "tsg" / "RAN" / "formal" / "common")]

import audit_clause_links as clause_audit  # noqa: E402
import classify_cross_source_differences as classify_mod  # noqa: E402
import measure_cross_source_agreement as cross_mod  # noqa: E402
import measure_substitution_ablation as ablation  # noqa: E402
import verify_chain_items as gate_mod  # noqa: E402
from classify_cross_source_differences import differences  # noqa: E402
from measure_cross_source_agreement import measure as cross_measure  # noqa: E402
from measure_process_record_observations import revision_chains  # noqa: E402

LOGS = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark")
FINAL = LOGS / "final"
OUT = FINAL / "reconciliation"
INSTANCES = Path("ontology/output/tsg/RAN/formal/instances")
SQLITE = LOGS / "integration" / "sqlite_final"
EXPORT_MANIFEST = SQLITE / "export_manifest.json"
# export 뒤에 바뀐 입력의 export 때 사본을 찾는 곳. 사본은 sha256 이 export 기록과 같을 때만 쓴다.
PRESERVED_EXPORT_INPUTS = (LOGS / "integration" / "before_baseline_revision_output_rule",)
MANUSCRIPT = Path("docs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/manuscript/main.tex")
GATE_IN = {part: LOGS / "integration" / "items_final" / part / "chain_items.jsonl" for part in ("core", "ran5")}
GATE_OUT = {part: LOGS / "integration" / "items_final" / "gate" / part for part in ("core", "ran5")}
# 게이트 실행 명령은 기록에 남아 있지 않다. 남은 입력 디렉토리로 만들 수 있는 조합을 모두 돌려 저장된 결과와 맞댄다.
GATE_CONFIGS = {"A": (LOGS / "integration" / "before_baseline_revision_output_rule", LOGS / "RAN5_graph_export"),
                "B": (None, LOGS / "RAN5_graph_export")}
WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
MIN_AVAILABLE_GIB = 8.0
TABLE3_ROW = re.compile(r"^(RAN[1-5]) & ([\d,]+) & ([\d,]+) & ([\d,]+) & ([\d,]+) & ")
RELEASE_MATCH = " AND doc.target_release = s.release"
LOADER = ablation.GENERATOR
PARSER = {**{wg: Path(f"scripts/tsg/RAN/formal/{wg}/phase-4/cr-parser/02_parse_cr_documents.py")
             for wg in ("RAN1", "RAN2", "RAN3", "RAN4")},
          "RAN5": Path("scripts/tsg/RAN/formal/RAN5/phase-4/cr-parser/01_parse_cr_documents.py")}
LIST_READER = {wg: Path(f"scripts/tsg/RAN/formal/{wg}/phase-1/jsonld/03_tdoc_instances.py") for wg in WGS}
EXAMPLES = 5


# --- 공통 -----------------------------------------------------------------------------------------------

class Checks:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, name: str, ok, **detail) -> bool:
        self.rows.append({"name": name, "pass": bool(ok), **detail})
        return bool(ok)

    @property
    def ok(self) -> bool:
        return all(row["pass"] for row in self.rows)


def default(value):
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def roundtrip(value):
    return json.loads(json.dumps(value, ensure_ascii=False, default=default))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def phase1(wg: str) -> dict[str, dict]:
    return {r["@id"]: r for r in json.loads((INSTANCES / f"phase-1/{wg}/tdocs.jsonld").read_text())["@graph"]}


def connect(wg: str) -> sqlite3.Connection:
    db = sqlite3.connect(f"file:{SQLITE / (wg + '.sqlite')}?mode=ro", uri=True)
    db.execute("PRAGMA temp_store=MEMORY")
    return db


def manuscript(needles: list[tuple[str, int, int]], checks: Checks) -> dict:
    """needle 마다 그 줄과 앞뒤 줄을 그대로 옮긴다. needle 은 원고에서 꼭 한 줄에만 있어야 한다."""
    data = MANUSCRIPT.read_bytes()
    lines = data.decode().splitlines()
    passages = []
    for needle, before, after in needles:
        hits = [number for number, text in enumerate(lines, 1) if needle in text]
        checks.add(f"manuscriptNeedleUnique:{needle}", len(hits) == 1, lines=hits)
        if hits:
            start, end = max(1, hits[0] - before), min(len(lines), hits[0] + after)
            passages.append({"needle": needle, "line": hits[0], "start": start, "end": end,
                             "text": "\n".join(lines[start - 1:end])})
    return {"path": str(MANUSCRIPT), "md5": hashlib.md5(data).hexdigest(), "lines": len(lines), "passages": passages}


def table3(checks: Checks) -> dict[str, dict]:
    rows = {}
    for text in MANUSCRIPT.read_text().splitlines():
        match = TABLE3_ROW.match(text.strip())
        if match:
            wg, *values = match.groups()
            rows[wg] = dict(zip(("packCr", "packCrWithForm", "links", "confirmed"),
                                (int(v.replace(",", "")) for v in values)))
    checks.add("table3RowsParsed", sorted(rows) == list(WGS), found=sorted(rows))
    return rows


def find_lines(path: Path, pattern: str) -> list[dict]:
    regex = re.compile(pattern)
    return [{"line": number, "text": text.strip()} for number, text in enumerate(path.read_text().splitlines(), 1)
            if regex.search(text)]


def write(command: str, facts: dict, needles: list[tuple[str, int, int]], checks: Checks, memory: list) -> int:
    passages = manuscript(needles, checks)
    script = Path(__file__).resolve()
    report = {"command": command, "script": str(script.relative_to(ROOT)),
              "scriptSha256": ablation.sha256_file(script), **facts, "manuscript": passages,
              "memoryChecks": memory, "checks": checks.rows, "allChecksPass": checks.ok}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"reconcile_{command}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=default) + "\n")
    failed = [row["name"] for row in checks.rows if not row["pass"]]
    print(command, "checks", len(checks.rows), "failed", len(failed), "->", path)
    for name in failed:
        print("  FAIL", name)
    return 0 if not failed else 1


# --- gate -----------------------------------------------------------------------------------------------

GATE_FAILURE_ORDER = ["gold_differs_from_independent_derivation", "row_width_differs_from_requested_fields",
                      "question_does_not_name_a_requested_field", "evidence_source_changed",
                      "document_list_pack_differs_from_pack_record", "same_cr_identity_packed_outside_gold",
                      "empty_gold_not_supported_by_disposition", "unexpected_empty_gold"]
PACK_SOURCES_SQL = ("SELECT doc.number FROM doc WHERE doc.id IN ({considered}) AND doc.pack_field GLOB 'RP-[0-9]*' "
                    "AND NOT EXISTS (SELECT 1 FROM pack_member m WHERE m.cr = doc.id AND m.pack = doc.pack_field)")
# (이름, 목록의 묶음 칸 — None 이면 목록에 문서 줄이 없다, 묶음 기록의 묶음, 5번 검사가 거르는가)
SYNTHETIC = (("listAndRecordSame", "RP-1", ["RP-1"], False),
             ("listAndRecordDifferent", "RP-1", ["RP-2"], True),
             ("listOnly", "RP-1", [], True),
             ("listDashRecordPack", "-", ["RP-1"], False),
             ("listEmptyRecordPack", "", ["RP-1"], False),
             ("listOtherTextRecordPack", "see RP-1", ["RP-1"], False),
             ("recordHasFurtherPack", "RP-1", ["RP-1", "RP-2"], False),
             ("listPackWithSuffix", "RP-1 rev", ["RP-1"], True),
             ("listPackInParentheses", "(RP-1)", ["RP-1"], False),
             ("neither", "", [], False),
             ("notInDocumentList", None, ["RP-1"], False))


def gate_static(checks: Checks) -> dict:
    order = re.findall(r'failures\.append\("([a-z_]+)"\)', inspect.getsource(gate_mod.check))
    checks.add("gateFailureOrder", order == GATE_FAILURE_ORDER, found=order)
    sql = " ".join(gate_mod.PACK_SOURCES_DIFFER.split())
    checks.add("packSourcesSqlAsRead", sql == PACK_SOURCES_SQL, found=sql)
    item5 = re.search(r"^5\. (.*?)^6\. ", gate_mod.__doc__, re.S | re.M)
    checks.add("gateDocstringItem5Found", item5 is not None)
    schema = re.search(r'db\.executescript\("""(.*?)"""\)', inspect.getsource(gate_mod.database), re.S)
    checks.add("gateSchemaFound", schema is not None)
    db = sqlite3.connect(":memory:")
    db.executescript(schema.group(1))
    query = gate_mod.PACK_SOURCES_DIFFER.format(considered=gate_mod.CONSIDERED["document"])
    cases = []
    for name, field, packs, expect in SYNTHETIC:
        db.execute("DELETE FROM doc")
        db.execute("DELETE FROM pack_member")
        if field is not None:
            db.execute("INSERT INTO doc VALUES (?, ?, ?, ?, ?, ?)", ("tdoc:X", "X", "", field, "1", ""))
        db.executemany("INSERT INTO pack_member VALUES (?, ?, ?)", [("tdoc:X", "tdoc:crpack/" + p, p) for p in packs])
        rejects = db.execute(query, {"anchor": "tdoc:X", "anchor_local": "X"}).fetchone() is not None
        cases.append({"case": name, "listPackField": field, "recordPacks": packs, "rejects": rejects,
                      "expected": expect})
        checks.add(f"synthetic:{name}", rejects == expect, rejects=rejects)
    return {"failureOrder": order, "packSourcesSql": sql, "docstringItem5": item5.group(1).strip() if item5 else None,
            "considered": {k: " ".join(v.split()) for k, v in gate_mod.CONSIDERED.items()},
            "syntheticCases": cases}


def gate_reproduce(checks: Checks, memory: list) -> tuple[dict, dict, dict]:
    """저장된 게이트 결과를 입력 조합마다 다시 만들고 바이트 단위로 맞댄다. (결과, 재현한 조합의 DB, 문항별 실패)."""
    items = {part: [json.loads(line) for line in GATE_IN[part].read_text().splitlines()] for part in GATE_IN}
    cache: dict[tuple, sqlite3.Connection] = {}

    def db_for(wg: str, config: str) -> sqlite3.Connection:
        p2, p4 = GATE_CONFIGS[config]
        key = (wg, str(p2) if p2 and (p2 / wg).is_dir() else "", str(p4) if p4 and (p4 / wg).is_dir() else "")
        if key not in cache:
            ablation.require_memory(MIN_AVAILABLE_GIB, f"gate DB {key}", memory)
            cache[key] = gate_mod.database(wg, p2, p4)
        return cache[key]

    results, failures_of = {}, {}
    for config in GATE_CONFIGS:
        results[config] = {}
        for part, loaded in items.items():
            sha_of: dict[str, str] = {}
            admitted, rejected = [], []
            counts: collections.Counter = collections.Counter()
            for item in loaded:
                failures = gate_mod.check(item, db_for(item["wg"], config), sha_of)
                failures_of[(config, item["id"])] = failures
                counts[(item["wg"], item["family"], "admitted" if not failures else "rejected")] += 1
                (rejected if failures else admitted).append({**item, **({"failures": failures} if failures else {})})
            admitted_text = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in admitted)
            report = {"checked": len(loaded), "admitted": len(admitted), "rejected": len(rejected),
                      "sourceFilesHashed": len(sha_of),
                      "byCell": [{"wg": wg, "family": family, "result": result, "n": n}
                                 for (wg, family, result), n in sorted(counts.items())],
                      "rejectedItems": [{"id": item["id"], "failures": item["failures"]} for item in rejected]}
            report_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
            stored_admitted = (GATE_OUT[part] / "chain_items_admitted.jsonl").read_bytes()
            stored_report = (GATE_OUT[part] / "chain_items_gate.json").read_bytes()
            results[config][part] = {
                "checked": len(loaded), "admitted": len(admitted), "rejected": len(rejected),
                "sourceFilesHashed": len(sha_of), "rejectedItems": report["rejectedItems"],
                "admittedFileIdentical": sha256_bytes(admitted_text.encode()) == sha256_bytes(stored_admitted),
                "reportFileIdentical": sha256_bytes(report_text.encode()) == sha256_bytes(stored_report)}
    reproducing = [c for c in GATE_CONFIGS if all(r["admittedFileIdentical"] and r["reportFileIdentical"]
                                                  for r in results[c].values())]
    checks.add("storedGateOutputReproduced", bool(reproducing), configs=reproducing)
    chosen = reproducing[0] if reproducing else "A"
    dbs = {wg: db_for(wg, chosen) for wg in WGS}
    configs = {c: {"phase2Root": str(p2) if p2 else None, "phase4Root": str(p4) if p4 else None}
               for c, (p2, p4) in GATE_CONFIGS.items()}
    return ({"inputs": {p: str(v) for p, v in GATE_IN.items()}, "stored": {p: str(v) for p, v in GATE_OUT.items()},
             "configs": configs, "byConfig": results, "reproducingConfigs": reproducing,
             "configUsedForDocumentClasses": chosen},
            {"dbs": dbs, "items": items, "cache": cache},
            {item_id: f for (config, item_id), f in failures_of.items() if config == chosen})


def gate_document_classes(context: dict, failures_of: dict, checks: Checks) -> dict:
    """게이트 DB 에서 문항이 살피는 문서를 두 출처의 관계로 나눈다."""
    doc_counts: collections.Counter = collections.Counter()
    item_counts: collections.Counter = collections.Counter()
    unchecked_admitted: collections.Counter = collections.Counter()
    mismatched, examples = [], collections.defaultdict(list)
    for part, loaded in context["items"].items():
        for item in loaded:
            db = context["dbs"][item["wg"]]
            considered = gate_mod.CONSIDERED.get(item["family"], gate_mod.CONSIDERED["document"])
            params = {"anchor": item["anchor"], "anchor_local": item["anchor"].rsplit("/", 1)[-1]}
            classes = collections.Counter()
            for (doc_id,) in db.execute(considered, params):
                packs = {p for (p,) in db.execute("SELECT pack FROM pack_member WHERE cr = ?", (doc_id,))}
                row = db.execute("SELECT pack_field FROM doc WHERE id = ?", (doc_id,)).fetchone()
                if row is None:
                    kind = "notInDocumentList:" + ("recordPack" if packs else "noRecordPack")
                else:
                    field = row[0]
                    if db.execute("SELECT ? GLOB 'RP-[0-9]*'", (field,)).fetchone()[0]:
                        if field not in packs:
                            kind = "listPackOutsideRecord"
                        else:
                            kind = "agreeRecordHasFurtherPack" if packs - {field} else "agree"
                        if not ablation.PACK_NUMBER.fullmatch(field):
                            kind += ":nonStandardPackText"
                    else:
                        text = "dash" if field == "-" else "emptyOrAbsent" if field == "" else "otherText"
                        kind = ("recordPackOnly:" if packs else "bothNoPack:") + text
                classes[kind] += 1
                if len(examples[kind]) < EXAMPLES:
                    examples[kind].append({"item": item["id"], "document": doc_id,
                                           "listPackField": None if row is None else row[0],
                                           "recordPacks": sorted(packs)})
            doc_counts.update(classes)
            for kind in classes:
                item_counts[kind] += 1
            fired = "document_list_pack_differs_from_pack_record" in failures_of[item["id"]]
            predicted = any(kind.startswith("listPackOutsideRecord") for kind in classes)
            if fired != predicted:
                mismatched.append(item["id"])
            if not failures_of[item["id"]]:
                for kind in classes:
                    if kind.startswith("recordPackOnly") or kind.startswith("agreeRecordHasFurtherPack"):
                        unchecked_admitted[kind] += 1
                if any(k.startswith("recordPackOnly") or k.startswith("agreeRecordHasFurtherPack") for k in classes):
                    unchecked_admitted["admittedItemsWithAny"] += 1
    checks.add("check5FiresExactlyOnListPackOutsideRecord", not mismatched, mismatched=mismatched)
    return {"unit": "문항이 살피는 문서(게이트 DB). 한 문서가 여러 문항에서 세일 수 있다",
            "documentsByClass": dict(sorted(doc_counts.items())), "itemsByClass": dict(sorted(item_counts.items())),
            "admittedItemsWithUncheckedDirection": dict(sorted(unchecked_admitted.items())),
            "examples": dict(sorted(examples.items()))}


def e4_rerun(checks: Checks, memory: list) -> dict:
    stored = json.loads((FINAL / "substitution_ablation.json").read_text())
    e4 = stored["substitutions"]["E4"]
    pre_wgs = set(stored["preIntegration"]["wgs"])
    items_by_wg: dict[str, list[dict]] = collections.defaultdict(list)
    for entry in stored["inputs"]["itemFiles"]:
        path = Path(entry["path"])
        checks.add(f"e4ItemFileUnchanged:{path.parent.name}", ablation.sha256_file(path) == entry["sha256"])
        for line in path.read_text().splitlines():
            if line.strip():
                item = json.loads(line)
                items_by_wg[item["wg"]].append(item)
    families = ablation.FAMILIES["E4"]
    stored_items = collections.defaultdict(list)
    for row in e4["items"]:
        stored_items[row["wg"]].append(row)
    all_default, all_blank, attribution = [], [], []
    for wg in sorted(items_by_wg):
        entry = stored["inputs"]["databases"][wg]
        checks.add(f"e4DatabaseUnchanged:{wg}", ablation.sha256_file(Path(entry["path"])) == entry["sha256"])
        ablation.require_memory(MIN_AVAILABLE_GIB, f"E4 {wg}", memory)
        db = connect(wg)
        rec = ablation.Records(db)
        items, pre = items_by_wg[wg], wg in pre_wgs
        baseline = {item["id"]: ablation.run(db, item) for item in items}
        excluded = {item["id"] for item in items if baseline[item["id"]] != {tuple(r) for r in item["gold"]}}

        def apply(sub) -> list[dict]:
            scope = [item for item in items if item["family"] in families]
            out = ablation.evaluate(db, sub, [item for item in scope if item["id"] not in excluded], wg, pre)
            out += [{"id": item["id"], "wg": wg, "family": item["family"], "outcome": "excluded",
                     "detail": "baselineDiffersFromGold",
                     "preIntegration": pre and item["family"] not in ablation.NO_DISPOSITION_FAMILIES}
                    for item in scope if item["id"] in excluded]
            return out

        sub, diag = ablation.substitute_e4(rec)
        out = apply(sub)
        checks.add(f"e4ItemsReproduced:{wg}",
                   roundtrip([{k: v for k, v in r.items() if k != "_example"} for r in out]) == stored_items[wg])
        checks.add(f"e4DiagnosticsReproduced:{wg}", roundtrip(diag) == e4["diagnosticsByWg"][wg])
        checks.add(f"gate5RecheckReproduced:{wg}",
                   roundtrip(ablation.gate5_recheck(rec, items)) == stored["byWg"][wg]["gate5PackSources"])
        blank_sub, _ = ablation.substitute_e4(rec, blank_defined=False)
        out_blank = apply(blank_sub)
        all_default += out
        all_blank += out_blank
        blank_changed = {r["id"] for r in out_blank if r["outcome"] == "changed"}
        changed = [item for item in items if item["id"] in {r["id"] for r in out if r["outcome"] == "changed"}]
        if changed:
            attribution += attribute_lost_rows(db, rec, sub, changed, blank_changed)
        del rec, sub, blank_sub
        db.close()
        gc.collect()
    counts, blank_counts = ablation.aggregate(all_default), ablation.aggregate(all_blank)
    checks.add("e4CountsReproduced", roundtrip(counts) == e4["counts"])
    checks.add("e4BlankCountsReproduced", roundtrip(blank_counts) == e4["blankCellUndefined"]["counts"])
    checks.add("e4ChangedAllLostOnly", counts["all"]["changedKinds"] == {"lostOnly": 35},
               found=counts["all"]["changedKinds"])
    default_changed = {r["id"] for r in all_default if r["outcome"] == "changed"}
    blank_changed = {r["id"] for r in all_blank if r["outcome"] == "changed"}
    checks.add("e4BlankChangedSubsetOfDefault", blank_changed <= default_changed)
    checks.add("e4LostRowsFullyRecoveredByRecordRows", all(a["recordRowsRestoreGold"] for a in attribution),
               failing=[a["id"] for a in attribution if not a["recordRowsRestoreGold"]])
    checks.add("e4LostDocumentsOutsideCheck5", all(a["lostDocumentsCheck5Condition"] == 0 for a in attribution))
    predicted_blank = {a["id"] for a in attribution if not a["emptyCellRestoreGold"]}
    checks.add("e4BlankChangedPredictedByEmptyCellDocuments", predicted_blank == blank_changed,
               onlyPredicted=sorted(predicted_blank - blank_changed), onlyStored=sorted(blank_changed - predicted_blank))
    directions_items = collections.Counter()
    directions_docs = collections.Counter()
    for a in attribution:
        recovering = sorted(d for d, v in a["directions"].items() if v["lostRowsRecovered"])
        directions_items["+".join(recovering)] += 1
        for d, v in a["directions"].items():
            directions_docs[d] += v["documents"]
    split = {"stayChangedWhenBlankCellUndefined": collections.Counter(), "becomeUndefined": collections.Counter()}
    for a in attribution:
        key = "stayChangedWhenBlankCellUndefined" if a["id"] in blank_changed else "becomeUndefined"
        split[key]["+".join(sorted(d for d, v in a["directions"].items() if v["lostRowsRecovered"]))] += 1
    return {"source": str(FINAL / "substitution_ablation.json"),
            "counts": {k: counts["all"][k] for k in ("evaluated", "unchanged", "changed", "undefined",
                                                     "changedKinds", "undefinedReasons")},
            "blankCellUndefinedCounts": {k: blank_counts["all"][k] for k in ("evaluated", "unchanged", "changed",
                                                                             "undefined", "changedAlsoUndefined")},
            "changedByWgFamily": dict(sorted(collections.Counter(
                f"{r['wg']}/{r['family']}" for r in all_default if r["outcome"] == "changed").items())),
            "lostRowDirections": {
                "meaning": "바뀐 문항의 읽은 문서 가운데 기록 묶음과 목록 값이 다른 문서를 방향별로 나누고, 그 방향의 "
                           "문서에만 기록 행을 되돌렸을 때 되찾는 손실 행을 센다",
                "itemsByRecoveringDirections": dict(sorted(directions_items.items())),
                "documentsByDirection": dict(sorted(directions_docs.items())),
                "byBlankCellReading": {k: dict(sorted(v.items())) for k, v in split.items()}},
            "items": attribution}


def attribute_lost_rows(db, rec, sub, changed: list[dict], blank_changed: set[str]) -> list[dict]:
    local = lambda packs: {p.rsplit("/", 1)[-1] for p in packs}
    rows_by_cr = {t: collections.defaultdict(list) for t in ("cr_in_pack", "pack_member")}
    for table, index in rows_by_cr.items():
        for row in rec.rows[table]:
            index[row[0]].append(tuple(row))
    out = []
    with ablation.Shadow(db, sub.tables) as shadow:
        for name, rows in sub.fill.items():
            shadow.insert(name, rows)

        def restore(item: dict, docs: set[str]) -> set[tuple]:
            marks = {t: db.execute(f"SELECT COALESCE(MAX(rowid), 0) FROM temp.{t}").fetchone()[0] for t in rows_by_cr}
            for table, index in rows_by_cr.items():
                shadow.insert(table, [row for d in sorted(docs) for row in index.get(d, ())])
            result = ablation.run(db, item)
            for table, mark in marks.items():
                db.execute(f"DELETE FROM temp.{table} WHERE rowid > ?", (mark,))
            return result

        for item in changed:
            gold = {tuple(r) for r in item["gold"]}
            filled = ablation.run(db, item)
            lost = gold - filled
            direction_of, described = {}, []
            for d in sorted(sub.read(item)):
                state = sub.state(d)
                if state not in sub.defined:
                    continue
                doc = rec.documents.get(d)
                record = local(rec.in_packs.get(d, ())) | local(rec.member_packs.get(d, ()))
                alternative = {doc.pack_field} if state == "link" else set()
                if record == alternative:
                    continue
                if state == "link":
                    direction = ("recordHasFurtherPack" if doc.pack_field in record
                                 else "listPackOutsideRecord:" + ("recordOtherPack" if record else "recordNone"))
                else:
                    direction = f"recordPackListSaysNone:{state}"
                direction_of[d] = direction
                check5 = bool(ablation.GLOB_PACK.match(doc.pack_field or "")
                              and "tdoc:crpack/" + doc.pack_field not in rec.member_packs.get(d, ()))
                described.append({"document": d, "direction": direction, "state": state,
                                  "listPackField": doc.pack_field, "recordPacks": sorted(record),
                                  "check5Condition": check5})
            full = restore(item, set(direction_of))
            directions = {}
            for direction in sorted(set(direction_of.values())):
                docs = {d for d, v in direction_of.items() if v == direction}
                result = restore(item, docs)
                directions[direction] = {"documents": len(docs), "lostRowsRecovered": len(lost & result),
                                         "rowsOutsideGold": len(result - gold)}
            empty_docs = {d for d, v in direction_of.items() if v == "recordPackListSaysNone:none-emptyCell"}
            recovering = {d for d in direction_of if lost & restore(item, {d})} if len(direction_of) <= 60 else None
            out.append({"id": item["id"], "wg": item["wg"], "family": item["family"], "anchor": item["anchor"],
                        "goldRows": len(gold), "lostRows": sorted(lost), "differingDocuments": len(direction_of),
                        "directions": directions, "recordRowsRestoreGold": full == gold,
                        "emptyCellRestoreGold": restore(item, empty_docs) == gold,
                        "staysChangedWhenBlankCellUndefined": item["id"] in blank_changed,
                        "lostDocumentsCheck5Condition": sum(e["check5Condition"] for e in described
                                                            if recovering is None or e["document"] in recovering),
                        "documents": [e | {"recoversLostRows": None if recovering is None
                                           else e["document"] in recovering} for e in described][:40],
                        "documentsShown": min(len(described), 40)})
    return out


def cmd_gate() -> int:
    checks, memory = Checks(), []
    facts = {"static": gate_static(checks)}
    reproduce, context, failures_of = gate_reproduce(checks, memory)
    facts["storedGate"] = reproduce
    facts["documentClasses"] = gate_document_classes(context, failures_of, checks)
    for db in context["cache"].values():
        db.close()
    del context
    gc.collect()
    facts["e4"] = e4_rerun(checks, memory)
    needles = [("remove items that admit two answers", 1, 7), ("its pack field (E4) and clauses-affected text (E6) those of 509 of 667", 0, 0),
               ("E4 pack (pack field) & 667", 0, 0), ("pack the list names against its pack record", 1, 1)]
    return write("gate", facts, needles, checks, memory)


# --- clause-bases ---------------------------------------------------------------------------------------

def static_release_evidence() -> dict:
    evidence = {}
    for wg in WGS:
        loader_text = LOADER[wg].read_text()
        # 적재기가 절 색인을 공통 모듈에서 가져오면 resolve 정의는 그 모듈에 있다.
        shared = re.search(r"^from (\w+) import [^\n]*\bSectionIndex\b", loader_text, re.M)
        if "    def resolve(" not in loader_text and shared:
            loader_text = (Path("scripts/tsg/RAN/formal/common/phase-4") / f"{shared.group(1)}.py").read_text()
        start = loader_text.find("    def resolve(")
        end = loader_text.find("\n    def ", start + 1)
        end = len(loader_text) if end < 0 else end
        evidence[wg] = {
            "loader": {"path": str(LOADER[wg]),
                       "resolveSource": loader_text[start:end].rstrip() if start >= 0 else None,
                       "releaseArgument": find_lines(LOADER[wg], r'cr\.get\("release"\)|d\.get\("release"\)')},
            "parser": {"path": str(PARSER[wg]),
                       "lines": find_lines(PARSER[wg], r"release=fname_release or release|"
                                                       r"if not fname_release and cr_table is not None|fname_release =")},
            "listReader": {"path": str(LIST_READER[wg]),
                           "lines": find_lines(LIST_READER[wg], r"row\.get\('Release'|release\.startswith\(\"Rel-\"\)")}}
    return evidence


def clause_bases_wg(wg: str, stored_readings: dict, stored_ablation: dict, table3_rows: dict, checks: Checks,
                    memory: list) -> dict:
    ablation.require_memory(MIN_AVAILABLE_GIB, f"clause-bases {wg}", memory)
    links = clause_audit.load_links(wg)
    from_extensions = collections.Counter(("tdoc:" + cr, section) for cr, section in links["links"])
    db = connect(wg)
    in_db = collections.Counter(db.execute("SELECT cr, section_id FROM cr_modifies_section"))
    total = sum(in_db.values())
    checks.add(f"linksSameAsExtensions:{wg}", from_extensions == in_db)
    checks.add(f"linksSameAsManifest:{wg}",
               total == stored_ablation["inputs"]["databases"][wg]["manifestTableRows"]["cr_modifies_section"])
    checks.add(f"linksSameAsTable3:{wg}", total == table3_rows[wg]["links"], table3=table3_rows[wg]["links"])
    for table in ("document", "section"):
        n, distinct = db.execute(f"SELECT COUNT(*), COUNT(DISTINCT id) FROM {table}").fetchone()
        checks.add(f"{table}IdUnique:{wg}", n == distinct)
    rows = db.execute("""SELECT c.cr, c.section_id, d.id IS NOT NULL, s.id IS NOT NULL, d.target_release, s.release
                         FROM cr_modifies_section c LEFT JOIN document d ON d.id = c.cr
                         LEFT JOIN section s ON s.id = c.section_id""").fetchall()
    category = collections.Counter()
    joined = []
    unjoined_crs: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for cr, section, has_doc, has_section, list_release, edition in rows:
        if not has_doc:
            category["noDocument"] += 1
            unjoined_crs["noDocument"][cr] += 1
        elif not has_section:
            category["noSection"] += 1
            unjoined_crs["noSection"][cr] += 1
        else:
            joined.append((cr, section, list_release, edition))
            if list_release is None or edition is None:
                category["releaseNull:" + ("list" if list_release is None else "") +
                         ("edition" if edition is None else "")] += 1
            else:
                category["sameRelease" if list_release == edition else "otherRelease"] += 1
    stored = stored_readings["clauseLinks"][wg]
    either_null = sum(n for k, n in category.items() if k.startswith("releaseNull"))
    checks.add(f"readingsClauseLinks:{wg}", len(joined) == stored["clauseLinks"], stored=stored["clauseLinks"])
    checks.add(f"readingsOtherEdition:{wg}", category["otherRelease"] == stored["linksToOtherEdition"])
    checks.add(f"readingsReleaseNotRecorded:{wg}", either_null == stored["linksWithReleaseNotRecorded"])
    checks.add(f"table3MinusJoinedIsUnjoined:{wg}",
               table3_rows[wg]["links"] - len(joined) == category["noDocument"] + category["noSection"])
    tdocs = phase1(wg)
    unjoined = {}
    for kind, crs in unjoined_crs.items():
        unjoined[kind] = {"links": sum(crs.values()), "distinctCr": len(crs),
                          "crInPhase1List": sum(cr in tdocs for cr in crs),
                          "crInPackRecord": sum(cr.removeprefix("tdoc:") in links["pack"] for cr in crs),
                          "examples": sorted(crs)[:EXAMPLES]}
    null_detail = None
    null_docs = sorted({cr for cr, _, list_release, _ in joined if list_release is None})
    if null_docs:
        doc_rows = {row[0]: row for row in db.execute(
            f"SELECT id, doc_type, presented_at FROM document WHERE id IN ({','.join('?' * len(null_docs))})", null_docs)}
        links_of = collections.Counter(cr for cr, _, list_release, _ in joined if list_release is None)
        null_detail = {
            "links": sum(links_of.values()), "documents": len(null_docs),
            "linksByDocType": dict(collections.Counter(doc_rows[d][1] for d in links_of.elements())),
            "documentsByDocType": dict(collections.Counter(doc_rows[d][1] for d in null_docs)),
            "linksByPresentedAt": dict(collections.Counter(doc_rows[d][2] for d in links_of.elements()).most_common()),
            "phase1HasTargetRelease": sum("targetRelease" in tdocs.get(d, {}) for d in null_docs),
            "phase1ReleaseKeys": dict(collections.Counter(
                k for d in null_docs for k in tdocs.get(d, {}) if "elease" in k)),
            "examples": null_docs[:EXAMPLES]}
    del tdocs
    gc.collect()
    mechanism = loader_mechanism(wg, joined)
    db.close()
    return {"linksInSqlite": total, "linksInExtensions": sum(from_extensions.values()),
            "duplicateLinks": sum(n - 1 for n in in_db.values() if n > 1), "joinedLinks": len(joined),
            "categories": dict(sorted(category.items())), "unjoined": unjoined, "listReleaseNull": null_detail,
            "storedReadings": stored, "loaderMechanism": mechanism}


def loader_mechanism(wg: str, joined: list[tuple]) -> dict:
    structure = clause_audit.load_structure(wg)
    source_paths, releases_read = clause_audit.build_parse(wg)
    unreproduced = []
    cells = collections.Counter()
    forward = collections.Counter()
    examples = collections.defaultdict(list)
    for cr, section, list_release, edition in joined:
        match = clause_audit.SECTION.match(section)
        spec, id_release, clause = match["spec"], match["release"], match["clause"]
        relation = "listNull" if list_release is None else "same" if list_release == edition else "other"
        builds = sorted(releases_read.get(cr.removeprefix("tdoc:"), ()))
        build = ("buildAbsent" if not builds else "buildMultiple" if len(builds) > 1
                 else "buildSameAsList" if builds[0] == list_release else "buildOtherThanList")
        outcomes = [(b, *clause_audit.resolve(structure, spec, clause, b)) for b in builds] or \
                   [(None, *clause_audit.resolve(structure, spec, clause, None))]
        hits = [(b, chosen, method) for b, chosen, method in outcomes if chosen == id_release]
        method = hits[0][2] if hits else "+".join(sorted({m for _, _, m in outcomes}))
        cells[(relation, build, method, bool(hits))] += 1
        if not hits:
            # 지금 빌드 입력으로는 연결의 판이 나오지 않는다. 빌드 입력의 다른 release 후보(팩 디렉토리, release 없음)로
            # 같은 규칙을 적용했을 때 연결의 판이 나오는지 함께 적는다.
            directories = sorted({m.group(1) for p in source_paths.get(cr.removeprefix("tdoc:"), ())
                                  if (m := re.search(r"/derived/(Rel-\d+)/", p))})
            unreproduced.append({
                "cr": cr, "section": section, "listRelease": list_release, "buildReleases": builds,
                "edition": edition, "ruleOutcomes": [{"release": b, "chosen": c, "method": m} for b, c, m in outcomes],
                "sourcePaths": sorted(source_paths.get(cr.removeprefix("tdoc:"), ())),
                "packDirectoryReleases": directories,
                "editionFromPackDirectoryRelease": [d for d in directories
                                                    if clause_audit.resolve(structure, spec, clause, d)[0] == id_release],
                "editionWithoutRelease": clause_audit.resolve(structure, spec, clause, None)[0] == id_release,
                "ruleSections": sorted({f"tdoc:section/{spec}-{c}-{clause}" for _, c, _ in outcomes if c})})
        if hits and method == "fallback_fwd":
            target = hits[0][0]
            later = [r for r in structure["releases"][spec]
                     if clause_audit.release_number(r) > clause_audit.release_number(target)
                     and (spec, r, clause) in structure["keys"]]
            nearest = min(later, key=clause_audit.release_number)
            forward["nearestLaterIsChosen" if nearest == id_release else "chosenIsLaterThanNearest"] += 1
        key = f"{relation}|{build}|{method}"
        if relation == "other" and len(examples[key]) < 3:
            examples[key].append({"cr": cr, "section": section, "listRelease": list_release,
                                  "buildReleases": builds, "edition": edition})
    # 규칙이 고르는 절에 다른 CR 의 연결이 있으면, 그 절은 그 연결을 만든 적재 때 판 해소 색인에 있었다.
    by_section = collections.defaultdict(set)
    for cr, section, _, _ in joined:
        by_section[section].add(cr)
    for row in unreproduced:
        row["otherCRsLinkedToRuleSections"] = {sid: len(by_section[sid] - {row["cr"]}) for sid in row["ruleSections"]}
    rows = [{"listVsEdition": r, "build": b, "method": m, "reproduced": h, "links": n}
            for (r, b, m, h), n in sorted(cells.items(), key=lambda kv: (-kv[1], kv[0]))]
    other = collections.Counter()
    for (r, b, m, h), n in cells.items():
        if r == "other":
            other[f"{b}|{m}|{'reproduced' if h else 'notReproduced'}"] += n
    return {"structureSource": structure["source"], "buildReleaseSource": str(clause_audit.PARSED_CR / wg /
                                                                            "cr_documents.json"),
            "reproduced": sum(n for (_, _, _, h), n in cells.items() if h), "links": sum(cells.values()),
            "cells": rows, "otherEditionLinks": dict(sorted(other.items(), key=lambda kv: -kv[1])),
            "fallbackForwardChoice": dict(forward), "otherEditionExamples": dict(examples),
            "unreproduced": unreproduced}


def audit_residual(wg: str) -> set[tuple[str, str]]:
    """저장된 절 연결 감사가 빌드가 파싱한 release 로도 판이 나오지 않는다고 적은 확인된 연결(`differs:notFromBuildParsedRelease`)."""
    stored = json.loads((LOGS / "clause_link_audit.json").read_text())["wg"][wg]["linkAudit"]["confirmedEditionRule"]
    residual = set()
    for row in stored["otherEditionLinks"]:
        edition = clause_audit.SECTION.match(row["section"])["release"]
        if edition not in row["ruleEditionFromBuildParsed"]:
            residual.add(("tdoc:" + row["cr"].removeprefix("tdoc:"), row["section"]))
    assert len(residual) == stored["tally"].get("differs:notFromBuildParsedRelease", 0)
    return residual


def clause_history_readings(stored_readings: dict, checks: Checks) -> dict:
    with_match = ablation.QUERIES["clause_history"]
    checks.add("releaseConditionOccursOnce", with_match.count(RELEASE_MATCH) == 1)
    without = with_match.replace(RELEASE_MATCH, "")
    items = []
    for path in (LOGS / "integration/items_final/gate/core/chain_items_admitted.jsonl",
                 LOGS / "integration/items_final/gate/ran5/chain_items_admitted.jsonl"):
        items += [json.loads(line) for line in path.read_text().splitlines()
                  if line.strip() and json.loads(line)["family"] == "clause_history"]
    by_wg = collections.Counter(item["wg"] for item in items)
    divergent, baseline_differs = [], []
    for wg in sorted(by_wg):
        db = connect(wg)
        for item in (i for i in items if i["wg"] == wg):
            gold = {tuple(r) for r in item["gold"]}
            if {tuple(r) for r in db.execute(with_match, {"anchor": item["anchor"]})} != gold:
                baseline_differs.append(item["id"])
            other = {tuple(r) for r in db.execute(without, {"anchor": item["anchor"]})}
            if other != gold:
                divergent.append({"id": item["id"], "goldRows": len(gold),
                                  "otherReleaseCRs": sorted({r[0] for r in other - gold}),
                                  "goldOnlyRows": len(gold - other)})
        db.close()
    stored = [{"id": d["id"], "goldRows": d["goldRows"], "otherReleaseCRs": d["otherReleaseCRs"]}
              for d in stored_readings["divergentItems"]]
    checks.add("clauseHistoryItems100", len(items) == 100, found=len(items))
    checks.add("clauseHistoryBaselineReproduced", not baseline_differs, failing=baseline_differs)
    checks.add("clauseHistoryDivergentAsStored",
               [{k: d[k] for k in ("id", "goldRows", "otherReleaseCRs")} for d in divergent] == stored)
    return {"items": len(items), "byWg": dict(by_wg), "sameRows": len(items) - len(divergent),
            "divergent": divergent, "queryWithReleaseMatch": " ".join(with_match.split()),
            "removedCondition": RELEASE_MATCH.strip()}


def cmd_clause_bases() -> int:
    checks, memory = Checks(), []
    readings = json.loads((FINAL / "clause_edition_readings.json").read_text())
    stored_ablation = json.loads((FINAL / "substitution_ablation.json").read_text())
    for wg in WGS:
        entry = stored_ablation["inputs"]["databases"][wg]
        checks.add(f"databaseUnchanged:{wg}", ablation.sha256_file(Path(entry["path"])) == entry["sha256"])
    rows = table3(checks)
    by_wg = {}
    for wg in WGS:
        by_wg[wg] = clause_bases_wg(wg, readings, stored_ablation, rows, checks, memory)
        print(wg, "joined", by_wg[wg]["joinedLinks"], by_wg[wg]["categories"], flush=True)
    del stored_ablation
    ran1to4_other = sum(by_wg[wg]["categories"].get("otherRelease", 0) for wg in WGS[:4])
    ran1to4_joined = sum(by_wg[wg]["joinedLinks"] for wg in WGS[:4])
    ran1to4_null = sum(v for wg in WGS[:4] for k, v in by_wg[wg]["categories"].items() if k.startswith("releaseNull"))
    checks.add("ran1to4OtherEdition269", ran1to4_other == 269, found=ran1to4_other)
    checks.add("ran5OtherEdition21778", by_wg["RAN5"]["categories"].get("otherRelease") == 21778)
    checks.add("ran5Joined38172", by_wg["RAN5"]["joinedLinks"] == 38172)
    for wg in WGS:
        mech = by_wg[wg]["loaderMechanism"]
        residual = audit_residual(wg)
        found = {(row["cr"], row["section"]) for row in mech["unreproduced"]}
        if not residual:
            checks.add(f"loaderRuleReproducesJoinedLinks:{wg}", mech["reproduced"] == mech["links"],
                       reproduced=mech["reproduced"], links=mech["links"])
        # 감사가 이미 적은 잔여가 있는 WG 는, 규칙이 재현하지 못한 연결이 그 잔여와 정확히 같은 집합이어야 통과한다.
        checks.add(f"unreproducedLinksEqualStoredAuditResidual:{wg}", found == residual,
                   reproduced=mech["reproduced"], links=mech["links"], unreproduced=len(found),
                   storedAuditResidual=len(residual))
    facts = {"table3": rows, "byWg": by_wg,
             "totals": {"table3Links": sum(r["links"] for r in rows.values()),
                        "joinedLinks": sum(v["joinedLinks"] for v in by_wg.values()),
                        "ran1to4": {"joined": ran1to4_joined, "otherEdition": ran1to4_other,
                                    "listReleaseNull": ran1to4_null,
                                    "withBothReleases": ran1to4_joined - ran1to4_null}},
             "releaseCode": static_release_evidence(),
             "clauseHistoryReadings": clause_history_readings(readings, checks)}
    needles = [("RAN1 & 2,120 & 2,120 & 6,141", 0, 6), ("104,125 of 105,363", 0, 3), ("of the links with a list", 2, 2)]
    return write("clause-bases", facts, needles, checks, memory)


# --- cr-counts ------------------------------------------------------------------------------------------

def cmd_cr_counts() -> int:
    checks, memory = Checks(), []
    traceability = json.loads((FINAL / "traceability_denominators.json").read_text())
    observations = json.loads((FINAL / "process_record_observations.json").read_text())["byWg"]
    by_wg, totals = {}, collections.Counter()
    for wg in WGS:
        ablation.require_memory(MIN_AVAILABLE_GIB, f"cr-counts {wg}", memory)
        tdocs = phase1(wg)
        list_cr = {i for i, r in tdocs.items() if r.get("@type") == "tdoc:CR" and r.get("tdoc:type") == "CR"}
        entry = {"phase1ListTypeCr": len(list_cr)}
        if traceability[wg]["source"] == "live graph":
            graph_cr = {row[0] for row in clause_audit.neo4j_rows(
                clause_audit.NEO4J_HTTP[wg], "MATCH (c:CR) WHERE c.type = 'CR' RETURN c.id")}
            entry["graphListTypeCr"] = len(graph_cr)
            entry["graphMinusPhase1"] = len(graph_cr - list_cr)
            entry["phase1MinusGraph"] = len(list_cr - graph_cr)
            population = graph_cr
        else:
            population = list_cr
        checks.add(f"listCrAsStored:{wg}", len(population) == traceability[wg]["cr"],
                   stored=traceability[wg]["cr"], found=len(population))
        db = connect(wg)
        kind = dict(db.execute("SELECT id, doc_type FROM document"))
        has_later = {earlier for (earlier,) in db.execute("SELECT earlier FROM revision")}
        final_cr_form = {i for i, k in kind.items() if i not in has_later and k == "tdoc:CR"}
        chains = revision_chains(db)
        db.close()
        stored_chain = observations[wg]["b_revisionChainLength"]["terminalCrDocuments"]
        checks.add(f"revisionChainsAsStored:{wg}", roundtrip(chains["terminalCrDocuments"]) == stored_chain)
        checks.add(f"finalCrFormCount:{wg}", len(final_cr_form) == stored_chain["n"])
        type_of = lambda i: (tdocs[i].get("tdoc:type") or "noListType") if i in tdocs else "notInPhase1List"
        final_not_list = final_cr_form - population
        list_not_final = population - final_cr_form
        why = collections.Counter()
        for i in list_not_final:
            if i not in kind:
                why["notInSqliteDocumentTable"] += 1
            elif kind[i] != "tdoc:CR":
                why["sqliteDocTypeNotCrForm:" + str(kind[i])] += 1
            elif i in has_later:
                why["hasLaterVersion"] += 1
            else:
                why["other"] += 1
        entry |= {"listTypeCr": len(population), "finalCrFormDocuments": len(final_cr_form),
                  "difference": len(final_cr_form) - len(population), "both": len(final_cr_form & population),
                  "finalCrFormByListType": dict(sorted(collections.Counter(map(type_of, final_cr_form)).items())),
                  "finalNotListTypeCr": dict(sorted(collections.Counter(map(type_of, final_not_list)).items())),
                  "listTypeCrNotFinal": dict(sorted(why.items())),
                  "finalWithAtLeastOneRevision": stored_chain["withAtLeastOneRevision"],
                  "longestChain": stored_chain["max"],
                  "crWithSection": traceability[wg]["crWithSection"]}
        checks.add(f"differenceDecomposes:{wg}",
                   entry["difference"] == len(final_not_list) - len(list_not_final))
        by_wg[wg] = entry
        for key in ("listTypeCr", "finalCrFormDocuments", "finalWithAtLeastOneRevision", "crWithSection"):
            totals[key] += entry[key]
        for part in ("finalNotListTypeCr", "listTypeCrNotFinal", "finalCrFormByListType"):
            for key, n in entry[part].items():
                totals[f"{part}:{key}"] += n
        del tdocs, kind
        gc.collect()
    totals_d = dict(sorted(totals.items()))
    totals_d["difference"] = totals["finalCrFormDocuments"] - totals["listTypeCr"]
    totals_d["shareWithRevision"] = round(totals["finalWithAtLeastOneRevision"] / totals["finalCrFormDocuments"], 4)
    totals_d["shareWithSection"] = round(totals["crWithSection"] / totals["listTypeCr"], 4)
    checks.add("listTypeCrTotal142860", totals["listTypeCr"] == 142860)
    checks.add("finalCrFormTotal143714", totals["finalCrFormDocuments"] == 143714)
    checks.add("difference854", totals_d["difference"] == 854)
    checks.add("revisionShare34.1", round(100 * totals_d["shareWithRevision"], 1) == 34.1)
    checks.add("sectionShare27.8", totals["crWithSection"] == 39724 and round(100 * totals_d["shareWithSection"], 1) == 27.8)
    checks.add("longestChain20InRAN3", max(by_wg, key=lambda w: by_wg[w]["longestChain"]) == "RAN3"
               and by_wg["RAN3"]["longestChain"] == 20)
    facts = {"definitions": {
        "listTypeCr": "문서 목록이 유형 CR 로 적은 문서(@type tdoc:CR, tdoc:type CR). RAN5 는 저장된 셈과 같이 그래프의 "
                      "CR 노드 가운데 type = 'CR' 인 노드",
        "finalCrFormDocuments": "SQLite 문서 표에서 doc_type 이 tdoc:CR(CR 양식: CR·draftCR·pCR)이고 뒤 판이 없는 문서"},
        "sources": {"traceability": str(FINAL / "traceability_denominators.json"),
                    "observations": str(FINAL / "process_record_observations.json"), "sqlite": str(SQLITE)},
        "byWg": by_wg, "totals": totals_d}
    needles = [("so they cover pack CRs: 39,724 of the 50,801", 1, 0), ("Total & 142,860", 0, 0),
               ("143,714 last versions of CRs, draft CRs and pseudo CRs", 1, 1)]
    return write("cr-counts", facts, needles, checks, memory)


# --- remainders -----------------------------------------------------------------------------------------

def export_input_state() -> dict[str, list[dict]]:
    """SQLite export 기록의 입력마다 지금 파일이 export 때와 같은지, 다르면 export 때 사본이 남아 있는지."""
    manifest = json.loads(EXPORT_MANIFEST.read_text())
    state = {}
    for wg, entry in manifest["exports"].items():
        rows = []
        for source in entry["inputs"]:
            path = Path(source["path"])
            now = ablation.sha256_file(path) if path.is_file() else None
            copies = [str(root / wg / path.name) for root in PRESERVED_EXPORT_INPUTS
                      if (root / wg / path.name).is_file()
                      and ablation.sha256_file(root / wg / path.name) == source["sha256"]]
            rows.append({"path": source["path"], "exportSha256": source["sha256"], "currentSha256": now,
                         "unchanged": now == source["sha256"], "exportCopy": copies[0] if copies else None})
        state[wg] = rows
    return state


@contextlib.contextmanager
def export_instances(wg: str, state: dict[str, list[dict]]):
    """처분·목록 셈 모듈이 읽는 인스턴스 트리를 export 때 입력으로 바꿔 끼운다. 바뀐 파일만 export 때 사본을 가리킨다."""
    with tempfile.TemporaryDirectory() as tmp:
        for phase in ("phase-1", "phase-2"):
            target = Path(tmp) / phase / wg
            target.mkdir(parents=True)
            for path in (INSTANCES / phase / wg).iterdir():
                os.symlink(path.resolve(), target / path.name)
        for row in state[wg]:
            path = Path(row["path"])
            if row["unchanged"] or INSTANCES not in path.parents:
                continue
            link = Path(tmp) / path.relative_to(INSTANCES)
            link.unlink()
            os.symlink(Path(row["exportCopy"]).resolve(), link)
        saved = cross_mod.INSTANCES, classify_mod.INSTANCES
        cross_mod.INSTANCES = classify_mod.INSTANCES = Path(tmp)
        try:
            yield
        finally:
            cross_mod.INSTANCES, classify_mod.INSTANCES = saved


def cross_source_drift(wg: str, state: dict, stored: dict) -> dict:
    """export 뒤에 바뀐 입력이 처분·목록 셈을 얼마나 바꾸는지와, 비교 결과가 바뀐 문서."""
    with export_instances(wg, state):
        before = {r["id"]: r for r in differences(wg, "allDocuments")[0]}
    after = {r["id"]: r for r in differences(wg, "allDocuments")[0]}
    current = cross_measure(wg)
    keys = ("listWithoutDisposition", "compared", "agree")
    pick = lambda r: {"listStatus": r["listStatus"], "reportCodes": r["reportCodes"],
                      "records": [{k: (v[:300] if isinstance(v, str) else v) for k, v in rec.items()
                                   if k in ("dispositionId", "code", "rule", "locator", "quote")} for rec in r["records"]]}
    return {"changedInputs": [r["path"] for r in state[wg] if not r["unchanged"]],
            "byScope": {scope: {"stored": {k: stored[wg][scope][k] for k in keys},
                                "currentInputs": {k: current[scope][k] for k in keys}} for scope in stored[wg]},
            "leftDifferences": {d: pick(before[d]) for d in sorted(set(before) - set(after))},
            "enteredDifferences": {d: pick(after[d]) for d in sorted(set(after) - set(before))},
            "differenceCellChanged": sorted(d for d in set(before) & set(after)
                                            if before[d]["reportCodes"] != after[d]["reportCodes"])}


def cmd_remainders() -> int:
    checks, memory = Checks(), []
    rerun = json.loads((OUT / "clause_link_audit_rerun.json").read_text())
    rows = [json.loads(line) for line in (OUT / "clause_link_audit_rerun_unconfirmed.jsonl").read_text().splitlines()
            if line.strip()]
    by_class = collections.Counter((row["wg"], row["class"]) for row in rows)
    t3 = table3(checks)
    for wg in WGS:
        audit = rerun["wg"][wg]["linkAudit"]
        found = {cls: n for (w, cls), n in by_class.items() if w == wg}
        checks.add(f"unconfirmedRowsMatchAudit:{wg}", found == audit["notConfirmed"])
        checks.add(f"auditLinksMatchTable3:{wg}", audit["links"] == t3[wg]["links"]
                   and audit["confirmed"] == t3[wg]["confirmed"])
    named = {"header_spec_typo_clause_listed": 649, "table_or_figure_in_clause": 530}
    class_totals = collections.Counter(row["class"] for row in rows)
    checks.add("unconfirmedTotal1238", len(rows) == 1238)
    for cls, n in named.items():
        checks.add(f"named:{cls}", class_totals[cls] == n, found=class_totals[cls])
    rest = [row for row in rows if row["class"] not in named]
    checks.add("remainder59", len(rest) == 59, found=len(rest))
    rest_cells = collections.Counter(f"{row['wg']}|{row['class']}" for row in rest)
    rest_examples = collections.defaultdict(list)
    for row in rest:
        key = f"{row['wg']}|{row['class']}"
        if len(rest_examples[key]) < 3:
            rest_examples[key].append({k: row.get(k) for k in ("cr", "section", "formSpec", "headerSpecRaw",
                                                               "fileNameSpec", "clauses", "otherSpecs")})
    unconfirmed = {"source": str(OUT / "clause_link_audit_rerun_unconfirmed.jsonl"), "rows": len(rows),
                   "byClass": dict(class_totals.most_common()), "remainder": len(rest),
                   "remainderByClass": dict(collections.Counter(row["class"] for row in rest).most_common()),
                   "remainderByWgClass": dict(sorted(rest_cells.items())), "remainderExamples": dict(rest_examples),
                   "confirmedTotal": sum(rerun["wg"][wg]["linkAudit"]["confirmed"] for wg in WGS),
                   "linksTotal": sum(rerun["wg"][wg]["linkAudit"]["links"] for wg in WGS)}
    checks.add("confirmed104125of105363", (unconfirmed["confirmedTotal"], unconfirmed["linksTotal"]) == (104125, 105363))

    ablation.require_memory(MIN_AVAILABLE_GIB, "cross-source RAN1", memory)
    stored = json.loads((FINAL / "cross_source_agreement.json").read_text())
    diff_rows, compared = differences("RAN1", "allDocuments")
    cell = stored["RAN1"]["allDocuments"]
    checks.add("ran1Compared", compared == cell["compared"] == 10385)
    checks.add("ran1Differences1583", len(diff_rows) == cell["compared"] - cell["agree"] == 1583)
    cells = collections.Counter((r["listStatus"], "+".join(r["reportCodes"])) for r in diff_rows)
    checks.add("ran1StoredTop15Matches", all(cells[(d["listStatus"], d["reportCodes"])] == d["n"]
                                             for d in cell["differences"]))
    state = export_input_state()
    drift = {}
    for wg in WGS:
        ablation.require_memory(MIN_AVAILABLE_GIB, f"cross-source {wg}", memory)
        changed = [row for row in state[wg] if not row["unchanged"]]
        restorable = all(row["exportCopy"] for row in changed)
        checks.add(f"exportCopyForEveryChangedInput:{wg}", restorable,
                   missing=[row["path"] for row in changed if not row["exportCopy"]])
        if not restorable:
            checks.add(f"crossSourceAsStoredFromExportInputs:{wg}", False, reason="export 때 입력을 복원할 수 없음")
            continue
        with export_instances(wg, state) if changed else contextlib.nullcontext():
            recomputed = cross_measure(wg)
        checks.add(f"crossSourceAsStoredFromExportInputs:{wg}", roundtrip(recomputed) == stored[wg],
                   inputsChangedSinceExport=len(changed))
        if changed:
            drift[wg] = cross_source_drift(wg, state, stored)
            scope = drift[wg]["byScope"]["allDocuments"]
            moved = len(drift[wg]["leftDifferences"]) - len(drift[wg]["enteredDifferences"])
            checks.add(f"driftExplainedByChangedDocuments:{wg}",
                       scope["stored"]["compared"] == scope["currentInputs"]["compared"]
                       and scope["currentInputs"]["agree"] - scope["stored"]["agree"] == moved,
                       agreeDelta=scope["currentInputs"]["agree"] - scope["stored"]["agree"], movedDocuments=moved)
        gc.collect()
    total = {scope: (sum(stored[wg][scope]["agree"] for wg in WGS), sum(stored[wg][scope]["compared"] for wg in WGS))
             for scope in ("allDocuments", "cr")}
    checks.add("allDocuments282336of288893", total["allDocuments"] == (282336, 288893))
    checks.add("cr117881of120743", total["cr"] == (117881, 120743))
    checks.add("ran1Share84.8", round(100 * cell["agree"] / cell["compared"], 1) == 84.8)
    named_cells = {("treated", "noted"): 628, ("revised", "noted"): 324, ("revised", "endorsed"): 221}
    for key, n in named_cells.items():
        checks.add(f"namedCell:{'|'.join(key)}", cells[key] == n, found=cells[key])
    checks.add("namedCells1173", sum(cells[k] for k in named_cells) == 1173)
    tdocs = phase1("RAN1")
    rest_rows = [r for r in diff_rows if (r["listStatus"], "+".join(r["reportCodes"])) not in named_cells]
    checks.add("remainder410", len(rest_rows) == 410, found=len(rest_rows))
    rest_out = []
    for (status, codes), n in sorted(((k, v) for k, v in cells.items() if k not in named_cells),
                                     key=lambda kv: (-kv[1], kv[0])):
        members = [r for r in rest_rows if (r["listStatus"], "+".join(r["reportCodes"])) == (status, codes)]
        rest_out.append({"listStatus": status, "reportCodes": codes, "n": n,
                         "listTypes": dict(collections.Counter(tdocs.get(r["id"], {}).get("tdoc:type", "none")
                                                               for r in members).most_common()),
                         "examples": [r["id"] for r in members[:3]]})
    by_list = collections.Counter(r["listStatus"] for r in rest_rows)
    by_report = collections.Counter("+".join(r["reportCodes"]) for r in rest_rows)
    multi = sum(len(r["reportCodes"]) > 1 for r in rest_rows)
    cross = {"source": str(FINAL / "cross_source_agreement.json"),
             "ran1": {"compared": compared, "agree": cell["agree"], "differences": len(diff_rows),
                      "namedCells": {"|".join(k): cells[k] for k in named_cells},
                      "remainder": len(rest_rows), "remainderCells": rest_out,
                      "remainderByListStatus": dict(by_list.most_common()),
                      "remainderByReportCodes": dict(by_report.most_common()),
                      "remainderWithSeveralReportCodes": multi,
                      "remainderListTypes": dict(collections.Counter(
                          tdocs.get(r["id"], {}).get("tdoc:type", "none") for r in rest_rows).most_common())},
             "totals": {scope: {"agree": a, "compared": c, "share": round(a / c, 4)} for scope, (a, c) in total.items()},
             "exportInputs": {"manifest": str(EXPORT_MANIFEST),
                              "changedSinceExport": {wg: [r for r in rows if not r["unchanged"]]
                                                     for wg, rows in state.items()},
                              "unchangedInputs": {wg: sum(r["unchanged"] for r in rows) for wg, rows in state.items()}},
             "driftSinceExport": drift}
    needles = [("Of the other 1,238, 649", 1, 2), ("1,173 of the 1,583", 0, 7), ("117,881 of 120,743", 2, 0)]
    return write("remainders", {"unconfirmedClauseLinks": unconfirmed, "crossSource": cross}, needles, checks, memory)


# --- liaison --------------------------------------------------------------------------------------------

def cmd_liaison() -> int:
    checks, memory = Checks(), []
    ablation.require_memory(MIN_AVAILABLE_GIB, "liaison RAN1", memory)
    diff_rows, _ = differences("RAN1", "allDocuments")
    cell = [r for r in diff_rows if r["listStatus"] == "treated" and r["reportCodes"] == ["noted"]]
    checks.add("treatedNoted628", len(cell) == 628, found=len(cell))
    tdocs = phase1("RAN1")
    kinds = collections.Counter((tdocs[r["id"]].get("tdoc:type"), tdocs[r["id"]].get("@type")) for r in cell)
    by_type = collections.Counter(tdocs[r["id"]].get("tdoc:type") for r in cell)
    checks.add("liaisonIn626", by_type.get("LS in") == 626, found=by_type.get("LS in"))
    others = []
    for r in cell:
        record = tdocs[r["id"]]
        if record.get("tdoc:type") == "LS in":
            continue
        others.append({"id": r["id"], "phase1": {k: (v[:200] if isinstance(v, str) else v) for k, v in record.items()
                                                 if isinstance(v, (str, int, float, bool))},
                       "dispositionRecords": [{k: (v[:300] if isinstance(v, str) else v) for k, v in rec.items()
                                               if k in ("dispositionId", "code", "rule", "path", "locator", "quote")}
                                              for rec in r["records"]]})
    checks.add("twoOthers", sorted(o["id"] for o in others) == ["tdoc:R1-160465", "tdoc:R1-160865"],
               found=[o["id"] for o in others])
    revised = {}
    for code, expected in (("noted", 324), ("endorsed", 221)):
        rows = [r for r in diff_rows if r["listStatus"] == "revised" and r["reportCodes"] == [code]]
        checks.add(f"revised{code.capitalize()}{expected}", len(rows) == expected, found=len(rows))
        revised[code] = rows
    rows = [r for code in revised for r in revised[code]]
    types = collections.Counter(tdocs[r["id"]].get("tdoc:type") for r in rows)
    successor = sum(1 for r in rows if tdocs[r["id"]].get("revisedTo"))
    summary_or_draft = types.get("discussion", 0) + types.get("draftCR", 0)
    successor_and_draft = sum(1 for r in rows if tdocs[r["id"]].get("revisedTo")
                              and tdocs[r["id"]].get("tdoc:type") in ("discussion", "draftCR"))
    checks.add("revisedMostlyDiscussionOrDraftCr", 2 * summary_or_draft > len(rows), found=summary_or_draft,
               of=len(rows))
    checks.add("revisedMostlyWithListedSuccessor", 2 * successor > len(rows), found=successor, of=len(rows))
    facts = {"cell": "RAN1 allDocuments, list treated, report noted", "documents": len(cell),
             "byListType": dict(by_type.most_common()),
             "byListTypeAndForm": [{"listType": t, "form": f, "n": n} for (t, f), n in kinds.most_common()],
             "others": others,
             "revisedCells": {
                 "cells": "RAN1 allDocuments, list revised, report noted or endorsed",
                 "documents": len(rows),
                 "byReportCode": {code: len(v) for code, v in revised.items()},
                 "byListType": dict(types.most_common()),
                 "byListTypeAndReportCode": [
                     {"listType": t, "reportCode": c, "n": n} for (t, c), n in collections.Counter(
                         (tdocs[r["id"]].get("tdoc:type"), code) for code in revised for r in revised[code]
                     ).most_common()],
                 "withRevisedTo": successor,
                 "discussionOrDraftCr": summary_or_draft,
                 "discussionOrDraftCrWithRevisedTo": successor_and_draft}}
    return write("liaison", facts, [("626 of them incoming liaison statements", 1, 1)], checks, memory)


COMMANDS = {"gate": cmd_gate, "clause-bases": cmd_clause_bases, "cr-counts": cmd_cr_counts,
            "remainders": cmd_remainders, "liaison": cmd_liaison}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=[*COMMANDS, "all"])
    args = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        raise SystemExit(f"저장소 루트에서 실행한다: {ROOT}")
    if args.command != "all":
        raise SystemExit(COMMANDS[args.command]())
    codes = {}
    for name, command in COMMANDS.items():
        codes[name] = command()
        gc.collect()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reconcile_all.json").write_text(json.dumps({"command": "all", "exitCodes": codes}, indent=2) + "\n")
    raise SystemExit(max(codes.values()))


if __name__ == "__main__":
    main()
