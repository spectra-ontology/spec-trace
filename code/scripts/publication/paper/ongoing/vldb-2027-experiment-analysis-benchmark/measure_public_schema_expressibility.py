"""추적 사슬 문항이 요구하는 기록 요소를 공개 통신 자원의 스키마가 갖고 있는지 판정한다 (모델 호출 없음).

문항 종류마다 정답을 구하는 데 필요한 기록 요소가 정해져 있다. 공개 자원마다 그 스키마가 싣는 요소를
아래 `RESOURCES`에 출처와 함께 적었다. 문항은 필요한 요소가 모두 그 스키마에 있을 때 그 자원으로 표현 가능하다.
판정은 스키마에 칸이 있는지만 보며, 그 자원이 실제로 값을 채웠는지는 보지 않는다(표현 가능성의 상한).

요소
- disposition: 문서에 내려진 처분 값
- wg_meeting: 문서가 다뤄진 WG 회의
- revision_link: 문서와 그 개정본 사이의 연결
- pack_membership: CR이 실린 총회 CR 묶음
- pack_tsg_meeting: 묶음이 제출된 총회 회의
- cr_clause: CR이 고친 규격 절

`--with-cr-db` 를 주면 3GPP 가 공개하는 CR 데이터베이스와 통신 QA·검색 말뭉치를 비교 대상에 더하고, 공개 자료로 칸을 판정할 수
없는 자원은 표현 가능 문항 수를 정하지 않은 값(null)으로 둔다. 이때 자원마다 모든 문항 종류가 요구하는데
스키마에 없는 요소(그 하나만으로 표현 가능 문항이 0 이 되는 요소)와, 칸의 범위가 좁은 요소를 빼고 센 문항 수도
함께 적는다. 이 옵션을 주지 않으면 출력은 옵션이 생기기 전과 같다.

사용: python3 measure_public_schema_expressibility.py --items <jsonl> [<jsonl> ...] --out <json> [--with-cr-db]
      (저장소 루트에서 실행)
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

NEEDS = {
    "pack_lookup": {"pack_membership", "pack_tsg_meeting"},
    # 빈 정답은 묶음 칸이 비어 있다는 사실이 아니라 CR 의 처분이 정당화한다(제거 실험과 같은 판정).
    "pack_lookup_empty": {"pack_membership", "pack_tsg_meeting", "disposition"},
    "disposition_pack": {"disposition", "wg_meeting", "pack_membership", "pack_tsg_meeting"},
    "pack_origin": {"pack_membership", "disposition", "wg_meeting"},
    "full_chain": {"disposition", "wg_meeting", "pack_membership", "pack_tsg_meeting", "cr_clause"},
    "clause_history": {"cr_clause", "disposition", "wg_meeting", "pack_membership"},
    "revision_chain": {"revision_link", "disposition", "pack_membership"},
}

# 각 자원의 스키마를 원문(논문의 스키마 표·본문, 도구의 모델 정의)에서 읽어 적은 것이다.
RESOURCES = [
    {"name": "3gpp-crawler", "form": "relational model (SQLite)",
     "source": "forge.3gpp.org/rep/reimes/3gpp-crawler, src/tdoc_crawler/database/oxyde_models.py",
     "has": ["disposition", "wg_meeting", "revision_link", "pack_tsg_meeting"],
     "basis": "TDocMetadata.status, TDocMetadata.meeting_id + MeetingMetadata, TDocMetadata.is_revision_of; "
              "a TSG CR pack is an RP TDoc row whose tdoc_type is 'CR pack', and its meeting_id is the plenary "
              "meeting (SubWorkingGroup.RP); the TDoc list columns read in doclist.py have no CR pack or "
              "clause column"},
    {"name": "DeepSpecs", "form": "three retrieval databases (SpecDB, ChangeDB, TDocDB)",
     "source": "arXiv:2511.01305", "has": [],
     "basis": "TDocDB holds chunks of approved CRs (summary, reason, consequences); ChangeDB holds "
              "line-level version diffs; candidate CRs for a change are matched by spec ID only"},
    {"name": "3GPP Rel-19 Telecom KG (GSMA Open Telco)", "form": "knowledge graph (GraphML)",
     "source": "huggingface.co/datasets/GSMA/telecom-kg-rel19, tkg/rel19_3gpp_telecom_kg.graphml", "has": [],
     "basis": "concept, parameter, identifier, protocol and reference entities with chunk provenance; "
              "TR 21.900 gives concept nodes for change request, CR pack and status, and the graph has no "
              "TDoc, meeting or pack instance"},
    {"name": "SpecReasoning KG (CellularSpecSec-Bench)", "form": "knowledge graph",
     "source": "arXiv:2601.12716, Tables 2-3", "has": [],
     "basis": "Procedure, Message, Information Element, Timer, State; has_step, contains_IE, defined_in"},
    {"name": "Tele-KG", "form": "knowledge graph", "source": "arXiv:2210.11298", "has": [],
     "basis": "product and fault knowledge under Event and Resource root classes"},
    {"name": "KG-RAG telecom KG", "form": "knowledge graph", "source": "arXiv:2602.17529", "has": [],
     "basis": "slice and QoS entities; suitable for, mapped to, identified by"},
    {"name": "SEM-RAG", "form": "typed document graph", "source": "arXiv:2605.08997, Table II", "has": [],
     "basis": "section, paragraph, term, table cell and formula primitives"},
    {"name": "TelcoAgent 3GPP KG", "form": "knowledge graph", "source": "arXiv:2606.19821", "has": [],
     "basis": "KPM definitions, causal chains and physical-layer constraints (Section III-A, Fig. 2)"},
    {"name": "KG2QA", "form": "knowledge graph", "source": "arXiv:2506.07037, Tables 2-3", "has": [],
     "basis": "ITU-T Recommendation entities and ten relation types"},
]

ELEMENTS = ["disposition", "wg_meeting", "revision_link", "pack_membership", "pack_tsg_meeting", "cr_clause"]

# 3GPP 지원팀이 관리하는 CR 데이터베이스. 열 이름은 공개 내려받기 파일의 표(Query1)에서 읽었다.
# `--with-cr-db` 를 줄 때만 비교 대상에 들어간다.
CR_DATABASE = {
    "name": "3GPP CR database", "form": "relational table (MS Access database, Excel export)",
    "source": "www.3gpp.org/ftp/Information/Databases/Change_Request/ (CRDB_*.zip, sheet Query1); "
              "TR 21.900 clause 4.6; portal.3gpp.org/ChangeRequests.aspx",
    "has": ["disposition", "wg_meeting", "revision_link", "pack_membership", "pack_tsg_meeting"],
    "basis": "one row per CR revision (Spec number, CR number, Revision) and plenary placement: WG-level status, "
             "Meeting WG-level, TSG Tdoc (the CR pack presented to the plenary), Meeting TSG-level and "
             "TSG-level status; the 18 columns (also the portal CR list and the per-specification CR page) "
             "have no clause column",
    "limits": {"revision_link": "the Revision column orders the revisions of one CR number; a revision into "
                                "a new CR number or from an unnumbered draftCR has no slot"},
}

# DeepSpecs 의 공개 자료(arXiv 판과 ACL Findings 판 논문, 프로젝트 페이지, 공개 데이터 파일)로는 어느 요소의
# 칸 유무도 정해지지 않는다. `--with-cr-db` 를 줄 때는 위 목록의 DeepSpecs 항목 대신 이 항목을 쓴다.
DEEPSPECS_PUBLIC = {
    "name": "DeepSpecs", "form": "three retrieval databases (SpecDB, ChangeDB, TDocDB)",
    "source": "arXiv:2511.01305; doi:10.18653/v1/2026.findings-acl.1343; metro.cs.ucla.edu/deepspecs.html",
    "has": [], "undetermined": list(ELEMENTS),
    "basis": "TDocDB chunks carry summary, reason and consequence of each change with spec, version and date "
             "metadata; CRs are collected with their TSG documentation package and the QA prompt reads "
             "'Clauses Affected'; the paper gives spec ID and timestamp as examples of filter metadata "
             "and publishes no full field list; the project page says TDocDB records "
             "which specs and clauses were affected; the code is shared after registration and the public "
             "data file real_world_qas.json holds question, ground_truth and source only",
}


# 통신 QA·검색 말뭉치. 공개된 레코드 필드를 읽어 적었다. `--with-cr-db` 를 줄 때만 비교 대상에 들어간다.
QA_CORPORA = [
    {"name": "TeleQnA", "form": "QA dataset (JSON)", "source": "arXiv:2310.15051", "has": [],
     "basis": "question, options, answer, explanation and category fields"},
    {"name": "TSpec-LLM", "form": "specification corpus (Markdown)", "source": "arXiv:2406.01768", "has": [],
     "basis": "3GPP specification files converted to Markdown, without typed record fields"},
    {"name": "SPEC5G", "form": "text and classification datasets", "source": "github.com/Imtiazkarimik23/SPEC5G",
     "has": [], "basis": "corpus, summarisation pairs and security classes"},
    {"name": "Telco-DPR", "form": "retrieval dataset", "source": "arXiv:2410.19790", "has": [],
     "basis": "passage metadata: document source, release number and section title"},
    {"name": "TeleCom-Bench", "form": "QA benchmark", "source": "arXiv:2605.18025", "has": [],
     "basis": "entity types and semantic edges of network functions, interfaces and KPIs; "
              "no TDoc or meeting record source"},
]


def extended_report(families: collections.Counter, item_sets: list[dict]) -> dict:
    """CR 데이터베이스를 더하고 판정할 수 없는 칸을 구분한 보고서를 만든다."""
    every = set.intersection(*(NEEDS[name] for name in families))
    report = {"items": sum(families.values()), "itemSets": item_sets,
              "needs": {name: sorted(NEEDS[name]) for name in sorted(families)},
              "elementsEveryFamilyNeeds": sorted(every), "resources": []}
    resources = ([DEEPSPECS_PUBLIC if r["name"] == "DeepSpecs" else r for r in RESOURCES]
                 + QA_CORPORA + [CR_DATABASE])

    def count(has: set, undetermined: set) -> tuple[int | None, int]:
        known = undecided = 0
        for name, items in families.items():
            if NEEDS[name] - has - undetermined:
                continue
            if NEEDS[name] & undetermined:
                undecided += items
            else:
                known += items
        return (None if undecided else known), undecided

    for resource in resources:
        has, undetermined = set(resource["has"]), set(resource.get("undetermined", ()))
        by_family = {}
        for name, items in sorted(families.items()):
            missing = sorted(NEEDS[name] - has - undetermined)
            open_ = sorted(NEEDS[name] & undetermined)
            by_family[name] = {"items": items, "expressible": False if missing else (None if open_ else True),
                               "missing": missing, "undetermined": open_}
        expressible, undecided = count(has, undetermined)
        row = {**resource, "expressibleItems": expressible, "undeterminedItems": undecided}
        forcing = sorted(every - has - undetermined)
        if forcing:
            # 모든 문항 종류가 요구하는데 없는 요소다. 이 요소 하나만으로 표현 가능 문항은 0 이다.
            row["forcingMissing"] = forcing
            row["expressibleWithForcingAdded"] = count(has | set(forcing), undetermined)[0]
        if resource.get("limits"):
            row["expressibleItemsWithoutLimited"] = count(has - set(resource["limits"]), undetermined)[0]
        row["byFamily"] = by_family
        report["resources"].append(row)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--with-cr-db", action="store_true",
                        help="CR 데이터베이스를 더하고 공개 자료로 판정할 수 없는 칸을 구분한다")
    args = parser.parse_args()
    families = collections.Counter()
    item_sets = []
    for path in args.items:
        rows = [json.loads(line)["family"] for line in path.read_text().splitlines()]
        families.update(rows)
        item_sets.append({"path": str(path), "items": len(rows)})
    unknown = set(families) - set(NEEDS)
    if unknown:
        raise SystemExit(f"문항 종류의 필요 요소가 정의되지 않았다: {sorted(unknown)}")
    if args.with_cr_db:
        report = extended_report(families, item_sets)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        for resource in report["resources"]:
            print(resource["name"], resource["expressibleItems"], "/", report["items"],
                  "forcing", resource.get("forcingMissing", []))
        return
    report = {"items": sum(families.values()), "needs": {name: sorted(NEEDS[name]) for name in sorted(families)},
              "resources": []}
    for resource in RESOURCES:
        has = set(resource["has"])
        by_family = {name: {"items": count, "expressible": NEEDS[name] <= has,
                            "missing": sorted(NEEDS[name] - has)} for name, count in sorted(families.items())}
        report["resources"].append({
            **resource, "expressibleItems": sum(row["items"] for row in by_family.values() if row["expressible"]),
            "byFamily": by_family})
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    for resource in report["resources"]:
        print(resource["name"], resource["expressibleItems"], "/", report["items"], "has", resource["has"])


if __name__ == "__main__":
    main()
