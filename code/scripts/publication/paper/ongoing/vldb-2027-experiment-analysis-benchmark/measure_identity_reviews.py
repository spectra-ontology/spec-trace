"""공개 패키지의 identity review 기록을 세고, 처분 기록과 벤치마크 정답이 그 기록에 얼마나 기대는지 잰다 (모델 호출 없음).

세는 것은 다음 넷이다.

1. 공개 패키지 `receipts/RAN{1..5}/` 의 파일마다 기록 수와 값 분포.
   문서 판정 기록(`document_decision_identity_reviews.json`)은 `identityStatus` · `classification`(글자일 때) ·
   `sourceDispositionCode` 를, 처분 판정 기록(`decision_disposition_identity_reviews.json`)은 `assessment` 를 센다.
   같은 이름의 빌드 입력 파일(`ontology/input/tsg/RAN/formal/meetings/RAN*/`)과 열쇠 · 상태가 같은지도 맞댄다.
2. 기록마다 남은 글(`reason`)의 종류와 빈도를 세고, 알려진 빌드 템플릿과 일치하는 사유문을 구분한다.
3. 처분 기록(`phase-2/RAN*/decision_dispositions.jsonld`, 레코드 단위로 읽는다)의 `assessmentMethod` 안에 든
   `identityReview` 를 열쇠로 기록과 잇는다. 문서 판정은 (meetingId, targetTdocNumber, decisionEvidence.locator),
   처분 판정은 dispositionId 가 열쇠다. 이은 처분 기록을 (판정 값, 규칙, evidenceStatus) 로 센다.
   부속서 CR 표 행인데 판정 기록이 없어 보류된 처분(`annex_target_identity_requires_own_source_review`)도 센다.
   `identityReview` 로 이어지지 않은 문서 판정 기록은 처분 기록의 (회의, 대상 문서, `evidenceLocator`) 로 다시 찾아
   그 처분의 규칙과 상태를 센다(기록은 읽혔으나 처분에 남지 않은 경우를 가린다).
4. 벤치마크 문항 667개(`items_final/gate/{core,ran5}/chain_items_admitted.jsonl`)의 `evidence[].dispositionId` 가
   3 에서 이은 처분 기록을 가리키는 정답 근거 행 수와 문항 수를 판정 값별로 센다.
   정답이 기대는 판정 기록은 `reason` 글이 `build_annex_identity_reviews.REASONS` 의 틀 글과 같은지로도 가른다
   (일치하는 사유문은 `buildScriptTemplate`, 그 밖의 사유문은 `otherReasonText`로 분류한다).

사용 (저장소 루트에서 실행):
  .venv/bin/python3 -I scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_identity_reviews.py \
      --out logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/next_cycle/analysis/identity_reviews.json
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(HERE))
import measure_locator_recompute as mlr  # noqa: E402  처분 기록을 레코드 단위로 읽는 함수

WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
RECEIPTS = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/release_preparation/vldb_release/receipts"
INPUTS = ROOT / "ontology/input/tsg/RAN/formal/meetings"
ITEMS = [ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/integration/items_final/gate/core/chain_items_admitted.jsonl",
         ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/integration/items_final/gate/ran5/chain_items_admitted.jsonl"]
DOC = "document_decision_identity_reviews.json"
DISP = "decision_disposition_identity_reviews.json"
ALIAS = "document_decision_target_aliases.json"
sys.path.insert(0, str(ROOT / "scripts/tsg/RAN/formal/common"))
import build_annex_identity_reviews as builder  # noqa: E402  부속서 행 판정 기록을 찍는 결정적 스크립트(틀 글 REASONS)

SCRIPT_REASONS = set(builder.REASONS.values())
DOC_ID = re.compile(r"RAN\d:DOC-(.+?)-R\d-")  # 문서 판정 처분 id 의 회의 부분(`RAN4:DOC-78-R4-...` → `78`)


def doc_key(review: dict) -> tuple:
    return (review["meetingId"], review["targetTdocNumber"], review["decisionEvidence"]["locator"])


def counter(values) -> dict:
    return dict(collections.Counter(values).most_common())


REASON_INDEX: dict = {}  # (wg, 회의, 대상, 위치) → reason 글


def receipt_counts() -> tuple[dict, dict, dict]:
    """패키지 기록을 세고 빌드 입력과 맞댄다. (파일별 수, 문서 판정 열쇠 → 값, 처분 판정 id → 값)"""
    per_file: dict = {}
    doc_index: dict = {}
    disp_index: dict = {}
    for wg in WGS:
        for name in (DOC, DISP, ALIAS):
            path = RECEIPTS / wg / name
            if not path.exists():
                continue
            payload = json.loads(path.read_text())
            rows = payload.get("reviews", payload.get("aliases", []))
            entry: dict = {"path": str(path.relative_to(ROOT)), "records": len(rows)}
            source = INPUTS / wg / name
            if source.exists():
                original = json.loads(source.read_text())
                original_rows = original.get("reviews", original.get("aliases", []))
                entry["buildInputRecords"] = len(original_rows)
            if name == DOC:
                entry["identityStatus"] = counter(r["identityStatus"] for r in rows)
                entry["classification"] = counter(r["classification"] for r in rows if isinstance(r.get("classification"), str))
                entry["classificationIsObject"] = sum(isinstance(r.get("classification"), dict) for r in rows)
                entry["sourceDispositionCode"] = counter(r["sourceDispositionCode"] for r in rows if "sourceDispositionCode" in r)
                keys = {doc_key(r): r["identityStatus"] for r in rows}
                entry["duplicateKeys"] = len(rows) - len(keys)
                if source.exists():
                    original_keys = {doc_key(r): r["identityStatus"] for r in original_rows}
                    entry["sameKeysAndStatusAsBuildInput"] = keys == original_keys
                    reasons = collections.Counter(r.get("reason") or "" for r in original_rows)
                    entry["buildInputDistinctReasonTexts"] = len(reasons)
                    entry["buildInputReasonTextsUsedOnce"] = sum(1 for v in reasons.values() if v == 1)
                    entry["buildInputScopeOrPurpose"] = {k: original[k] for k in ("purpose", "scope") if k in original}
                for key, status in keys.items():
                    doc_index[(wg,) + key] = status
                # 공개 패키지 기록에는 reason 글이 없으므로 글은 같은 열쇠의 빌드 입력 기록에서 읽는다.
                for r in original_rows if source.exists() else []:
                    REASON_INDEX[(wg,) + doc_key(r)] = r.get("reason") or ""
                entry["buildInputReasonIsBuildScriptTemplate"] = sum(
                    (r.get("reason") or "") in SCRIPT_REASONS for r in (original_rows if source.exists() else []))
            elif name == DISP:
                entry["contract"] = payload.get("contract")
                entry["assessment"] = counter(r["assessment"] for r in rows)
                for r in rows:
                    disp_index[r["dispositionId"]] = r["assessment"]
                if source.exists():
                    entry["sameIdsAsBuildInput"] = ({r["dispositionId"] for r in rows}
                                                    == {r["dispositionId"] for r in original_rows})
            per_file.setdefault(wg, {})[name] = entry
    return per_file, doc_index, disp_index


def gold_index() -> tuple[dict, int, int]:
    by_disposition: dict = collections.defaultdict(list)
    items = rows = 0
    for path in ITEMS:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                item = json.loads(line)
                items += 1
                for evidence in item.get("evidence", []):
                    rows += 1
                    if evidence.get("dispositionId"):
                        by_disposition[evidence["dispositionId"]].append(item["id"])
    return by_disposition, items, rows


def unlinked_report(doc_index: dict, matched: set, by_record_key: dict) -> dict:
    """identityReview 로 이어지지 않은 문서 판정 기록을 처분 기록의 (회의, 대상, 위치) 열쇠로 다시 찾는다.
    찾은 처분이 identityReview 를 품지 않았으면 그 기록은 읽혔으나 처분에 남지 않은 것이다."""
    unlinked = set(doc_index) - matched
    found = collections.Counter()
    missing = collections.Counter()
    gold_rows = 0
    gold_items: set = set()
    for key in unlinked:
        rows = by_record_key.get(key)
        if not rows:
            missing[(key[0], doc_index[key])] += 1
            continue
        for embeds, rule, status, golds in rows:
            found[f"{key[0]}|{doc_index[key]}|embedsReview={embeds}|{rule}|{status}"] += 1
            gold_rows += len(golds)
            gold_items.update(golds)
    return {"unlinked": len(unlinked), "dispositionsFoundByKey": dict(found.most_common()),
            "noDispositionWithKey": {f"{wg}|{status}": n for (wg, status), n in sorted(missing.items())},
            "goldRowsOnFoundDispositions": gold_rows, "goldItemsOnFoundDispositions": sorted(gold_items)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    per_file, doc_index, disp_index = receipt_counts()
    gold, item_count, gold_rows = gold_index()

    linked = collections.Counter()          # (kind, value, rule, evidenceStatus)
    unreviewed_annex = collections.Counter()
    matched_doc_keys: set = set()
    matched_disp_ids: set = set()
    gold_by_value: dict = collections.defaultdict(lambda: {"goldRows": 0, "items": set(), "dispositions": 0})
    gold_by_origin: dict = collections.defaultdict(
        lambda: {"goldRows": 0, "items": set(), "dispositions": 0, "reasons": collections.Counter()})
    gold_pending_by_rule: dict = collections.defaultdict(lambda: {"goldRows": 0, "items": set()})
    records = 0
    by_record_key: dict = collections.defaultdict(list)  # 열쇠 → (identityReview 를 품었는가, 규칙, 상태, 문항 수)
    for wg in WGS:
        for r in mlr.stream_dispositions(wg):
            records += 1
            text = r.get("assessmentMethod") or ""
            found = DOC_ID.match(r["dispositionId"])
            if found:
                key = (wg, f"{wg}#{found[1]}", r["targetTdocNumber"], r.get("evidenceLocator"))
                if key in doc_index:
                    rule = json.loads(text).get("rule") if text else None
                    by_record_key[key].append(('"identityReview"' in text, rule, r["evidenceStatus"],
                                               gold.get(r["dispositionId"], [])))
            reviewed = '"identityReview"' in text
            annex_pending = "annex_target_identity_requires_own_source_review" in text
            if not reviewed and not annex_pending:
                continue
            method = json.loads(text)
            if annex_pending and method.get("rule") == "annex_target_identity_requires_own_source_review":
                unreviewed_annex[(wg, r["evidenceStatus"])] += 1
                if r["dispositionId"] in gold:
                    g = gold_pending_by_rule["annex_target_identity_requires_own_source_review"]
                    g["goldRows"] += len(gold[r["dispositionId"]])
                    g["items"].update(gold[r["dispositionId"]])
            review = method.get("identityReview")
            if not review:
                continue
            if "dispositionId" in review:
                kind, value = "disposition", disp_index.get(review["dispositionId"], "NOT_IN_PACKAGE")
                matched_disp_ids.add(review["dispositionId"])
            else:
                key = (wg,) + doc_key(review)
                kind, value = "document", doc_index.get(key, "NOT_IN_PACKAGE")
                matched_doc_keys.add(key)
            linked[(wg, kind, value, method.get("rule"), r["evidenceStatus"])] += 1
            if r["dispositionId"] in gold:
                g = gold_by_value[f"{kind}:{value}:{r['evidenceStatus']}"]
                g["goldRows"] += len(gold[r["dispositionId"]])
                g["items"].update(gold[r["dispositionId"]])
                g["dispositions"] += 1
                reason = REASON_INDEX.get(key, "") if kind == "document" else ""
                origin = "buildScriptTemplate" if reason in SCRIPT_REASONS else "otherReasonText"
                o = gold_by_origin[f"{wg}:{kind}:{value}:{origin}"]
                o["goldRows"] += len(gold[r["dispositionId"]])
                o["items"].update(gold[r["dispositionId"]])
                o["dispositions"] += 1
                if origin == "otherReasonText":
                    o["reasons"][reason[:120]] += 1

    all_items = set()
    for g in gold_by_value.values():
        all_items |= g["items"]
    result = {
        "script": Path(__file__).name,
        "receipts": per_file,
        "totals": {
            "documentReviews": sum(e[DOC]["records"] for e in per_file.values() if DOC in e),
            "dispositionReviews": sum(e[DISP]["records"] for e in per_file.values() if DISP in e),
            "targetAliases": sum(e[ALIAS]["records"] for e in per_file.values() if ALIAS in e),
            "documentReviewsPerWg": {wg: e[DOC]["records"] for wg, e in per_file.items() if DOC in e},
        },
        "dispositionRecordsRead": records,
        "linkedDispositions": [list(k) + [v] for k, v in sorted(linked.items())],
        "linkedDispositionsByValueAndStatus": counter(
            f"{k[1]}:{k[2]}:{k[4]}" for k, v in linked.items() for _ in range(v)),
        "documentReviewsWithoutDisposition": len(set(doc_index) - matched_doc_keys),
        "documentReviewsWithoutDispositionByStatus": counter(doc_index[k] for k in set(doc_index) - matched_doc_keys),
        "unlinkedDocumentReviewsFoundByRecordKey": unlinked_report(doc_index, matched_doc_keys, by_record_key),
        "dispositionReviewsWithoutDisposition": sorted(set(disp_index) - matched_disp_ids),
        "annexRowsPendingForLackOfReview": [list(k) + [v] for k, v in sorted(unreviewed_annex.items())],
        "gold": {
            "itemFiles": [str(p.relative_to(ROOT)) for p in ITEMS],
            "items": item_count,
            "goldEvidenceRows": gold_rows,
            "matchingRule": "item.evidence[].dispositionId == disposition.dispositionId (exact)",
            "byReviewValueAndEvidenceStatus": {k: {"goldRows": v["goldRows"], "items": len(v["items"]),
                                                   "dispositions": v["dispositions"]}
                                               for k, v in sorted(gold_by_value.items())},
            "itemsDependingOnAnyReview": len(all_items),
            "goldRowsDependingOnAnyReview": sum(v["goldRows"] for v in gold_by_value.values()),
            "pendingWithoutReview": {k: {"goldRows": v["goldRows"], "items": len(v["items"])}
                                     for k, v in gold_pending_by_rule.items()},
            "byWgReviewValueAndReasonOrigin": {k: {"goldRows": v["goldRows"], "items": len(v["items"]),
                                                   "dispositions": v["dispositions"],
                                                   "reasonTexts": dict(v["reasons"].most_common())}
                                               for k, v in sorted(gold_by_origin.items())},
            "itemsByReasonOrigin": {origin: len(set().union(*[v["items"] for k, v in gold_by_origin.items()
                                                              if k.endswith(origin)] or [set()]))
                                    for origin in ("buildScriptTemplate", "otherReasonText")},
            "itemIdsDependingOnAnyReview": sorted(all_items),
        },
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(json.dumps({"totals": result["totals"], "linked": result["linkedDispositionsByValueAndStatus"],
                      "gold": {k: v for k, v in result["gold"].items() if k != "itemIdsDependingOnAnyReview"}},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
