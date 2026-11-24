"""문항 정답 행이 쓰는 묶음 연결·조항 연결 가운데 전수 감사가 확인하지 못한 연결을 센다 (모델 호출 없음).

전수 감사(`audit_pack_links.py`, `audit_clause_links.py`)는 묶음 연결과 조항 연결을 원문과 하나씩 대조하고
확인하지 못한 연결을 목록으로 남긴다. 이 스크립트는 채택 문항의 정답 행이 따라간 (CR, 묶음) 쌍과
(CR, 조항) 쌍을 문항 파일에서 다시 만들고, 그 쌍이 확인하지 못한 연결 목록에 들어 있는지 센다.

쌍을 만드는 규칙은 `measure_item_link_evidence.py` 의 연결 열쇠와 같다.
- pack_lookup · disposition_pack · full_chain  (기준 CR, 정답 행의 묶음). full_chain 은 (기준 CR, 정답 행의 조항 번호)도.
- revision_chain  (정답 행의 최종 문서, 묶음)
- clause_history  (정답 행의 문서, 묶음), (정답 행의 문서, 기준 조항 기록)
- pack_origin     (정답 행의 문서, 기준 묶음)
- pack_lookup_empty 는 빈 정답이라 쌍이 없다.

full_chain 의 정답 행은 조항 번호만 적는다. 이 경우 같은 CR 의 확인하지 못한 연결 가운데 조항 번호가 같은 것을
release 와 무관하게 모두 일치로 센다(일치를 놓치지 않는 쪽).
서로 다른 연결 수는 (작업반, 열쇠) 단위로 세고, `--link-evidence` 를 주면 그 결과 파일의 연결 수와 같은지 적는다.

사용: python3 measure_gold_links_in_audit_remainder.py --items <admitted.jsonl>... --pack-audit <jsonl>
      --clause-unconfirmed <jsonl> [--link-evidence <json>...] --out <json>
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re

SECTION = re.compile(r"^tdoc:section/(?P<spec>\d{2}\.\d{3}(?:-\d+)?)-(?P<release>Rel-\d+)-(?P<clause>.+)$")


def local(identifier: str) -> str:
    return identifier.rsplit("/", 1)[-1].removeprefix("tdoc:")


def fold(number: str) -> str:
    """문서·묶음 번호의 공백과 대소문자 표기만 걷어 낸 형태."""
    return re.sub(r"\s+", "", str(number)).upper()


def gold_links(item: dict):
    """(종류, 열쇠) 를 낸다. 종류는 pack · clause_record(조항 기록 식별자) · clause_number(조항 번호)."""
    family, anchor = item["family"], item["anchor"]
    for row in item["gold"]:
        named = dict(zip(item["fields"], row))
        if family in ("pack_lookup", "disposition_pack", "full_chain"):
            doc = local(anchor)
            yield "pack", (fold(doc), fold(named["cr_pack"]))
            if "clause" in named:
                yield "clause_number", (fold(doc), named["clause"])
        elif family == "revision_chain":
            yield "pack", (fold(named["final_document"]), fold(named["cr_pack"]))
        elif family == "clause_history":
            yield "pack", (fold(named["document"]), fold(named["cr_pack"]))
            yield "clause_record", (fold(named["document"]), anchor)
        elif family == "pack_origin":
            yield "pack", (fold(named["document"]), fold(local(anchor)))
        elif family != "pack_lookup_empty":
            raise ValueError(f"모르는 문항 종류: {family}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=pathlib.Path, nargs="+", required=True)
    parser.add_argument("--pack-audit", type=pathlib.Path, required=True)
    parser.add_argument("--clause-unconfirmed", type=pathlib.Path, required=True)
    parser.add_argument("--link-evidence", type=pathlib.Path, nargs="*", default=[])
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()

    items = [json.loads(line) for path in args.items for line in path.read_text(encoding="utf-8").splitlines()
             if line.strip()]
    used = collections.defaultdict(lambda: collections.defaultdict(set))
    for item in items:
        for kind, key in gold_links(item):
            used[kind][(item["wg"], key)].add(item["id"])

    pack_rest = {}
    with args.pack_audit.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("kind") == "e4Link" and row.get("class") == "notConfirmed":
                pack_rest[(fold(row["number"]), fold(row["pack"]))] = row.get("reason")
    clause_rest, clause_rest_by_number = {}, collections.defaultdict(list)
    with args.clause_unconfirmed.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            clause_rest[(fold(row["cr"]), row["section"])] = row["class"]
            match = SECTION.match(row["section"])
            if not match:
                raise ValueError(f"조항 기록 식별자를 읽지 못함: {row['section']}")
            clause_rest_by_number[(fold(row["cr"]), match["clause"])].append((row["section"], row["class"]))

    pack_hits = [{"wg": wg, "document": key[0], "pack": key[1], "reason": pack_rest[key], "items": sorted(ids)}
                 for (wg, key), ids in sorted(used["pack"].items()) if key in pack_rest]
    clause_hits = [{"wg": wg, "document": key[0], "section": key[1], "class": clause_rest[key], "items": sorted(ids)}
                   for (wg, key), ids in sorted(used["clause_record"].items()) if key in clause_rest]
    clause_hits += [{"wg": wg, "document": key[0], "section": section, "class": label, "items": sorted(ids),
                     "matchedBy": "clause_number"}
                    for (wg, key), ids in sorted(used["clause_number"].items())
                    for section, label in clause_rest_by_number.get(key, [])]

    report = {
        "items": [str(path) for path in args.items],
        "itemCount": len(items),
        "packAudit": str(args.pack_audit),
        "clauseUnconfirmed": str(args.clause_unconfirmed),
        "goldPackLinks": len(used["pack"]),
        "goldClauseLinks": {"clause_history": len(used["clause_record"]), "full_chain": len(used["clause_number"]),
                            "all": len(used["clause_record"]) + len(used["clause_number"])},
        "unconfirmedPackLinks": len(pack_rest),
        "unconfirmedClauseLinks": len(clause_rest),
        "goldPackLinksUnconfirmed": pack_hits,
        "goldClauseLinksUnconfirmed": clause_hits,
        "goldClauseLinksUnconfirmedByClass": dict(collections.Counter(hit["class"] for hit in clause_hits)),
        "itemsWithUnconfirmedLink": sorted({i for hit in pack_hits + clause_hits for i in hit["items"]}),
    }
    if args.link_evidence:
        counted = collections.Counter()
        for path in args.link_evidence:
            by_kind = json.loads(path.read_text(encoding="utf-8"))["byLinkKind"]
            counted["cr_pack"] += by_kind["cr_pack"]["links"]
            counted["cr_section"] += by_kind["cr_section"]["links"]
        report["linkEvidence"] = {
            "files": [str(path) for path in args.link_evidence],
            "cr_pack": counted["cr_pack"], "cr_section": counted["cr_section"],
            "sameCounts": counted["cr_pack"] == report["goldPackLinks"]
            and counted["cr_section"] == report["goldClauseLinks"]["all"],
        }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("itemCount", "goldPackLinks", "goldClauseLinks", "unconfirmedPackLinks",
                                             "unconfirmedClauseLinks", "goldClauseLinksUnconfirmedByClass")}))
    print("pack hits", len(pack_hits), "clause hits", len(clause_hits), report.get("linkEvidence", {}).get("sameCounts"))


if __name__ == "__main__":
    main()
