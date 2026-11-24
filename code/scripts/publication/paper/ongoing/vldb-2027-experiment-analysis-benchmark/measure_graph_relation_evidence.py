"""그래프 전체에서 추적 관계가 원문 근거와 함께 실려 있는 비율을 작업반별로 센다 (모델 호출 없음).

세 가지를 잰다.
1. 관계 전수 조사: 인스턴스 JSON-LD 의 모든 기록에서 IRI 를 값으로 갖는 관계(파일의 `@context` 가 `@id` 로 선언한 키)를
   (기록 유형, 관계)마다 세고, 그 관계를 실은 기록이 근거 속성(`evidencePath`·`evidenceSha256`·`evidenceLocator`·
   `evidenceQuote`)을 함께 갖는지 센다. 근거 속성을 가진 기록이 하나도 없는 관계를 따로 열거한다.
   주장 기록(`EvidenceAssertion`)은 술어와 판정 상태별로 센다.
2. 결정 기록 → 문서 참조: 결정 기록의 `references` 쌍마다 결정문 본문이 그 문서 번호를 적는지,
   그 쌍을 가리키는 원문 대조 통과 처분 기록(근거 네 값 완비)이 있는지 센다. 처분 기록은 근거 파일의 SHA-256 일치,
   인용문의 대상 번호 표기, 그 조각의 근거 파일 내 위치 확인, 근거 파일이 결정 기록 회의의 보고서인지를 센다.
3. 근거 속성이 없는 추적 관계를 따로 둔 원자료로 다시 확인: CR → 묶음, 묶음 → TSG 회의, CR → 절, 개정 연결.
   판정 기준은 `measure_item_link_evidence.py` 와 같다.

사용 (저장소 루트에서 실행):
  python3 measure_graph_relation_evidence.py [--wg RAN1 ...] [--phase2-root <dir>] [--phase4-root <dir>] --out <json>
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_chain_items import INSTANCES, as_list, local  # noqa: E402
from measure_item_link_evidence import (  # noqa: E402
    EVIDENCE_KEYS, Dispositions, ListCells, PackSources, WgMeetings, docx_squashed, file_sha256, names, number,
    quote_located,
)


def id_keys(context) -> set[str]:
    """`@context` 가 IRI 값으로 선언한 키. 접두사 `tdoc:` 가 붙은 표기도 같은 관계다."""
    found = set()
    for part in as_list(context):
        if isinstance(part, dict):
            found.update(key for key, value in part.items() if isinstance(value, dict) and value.get("@type") == "@id")
    return found


def instance_files(wg: str, overrides: list[Path]):
    """(읽을 경로, 인스턴스 트리 안의 자리). 같은 자리의 대체 파일이 주어졌으면 그것을 읽는다."""
    seen = set()
    for phase in sorted(INSTANCES.glob("phase-*")):
        for path in sorted((phase / wg).rglob("*.jsonld")) if (phase / wg).is_dir() else ():
            staged = next((root / wg / path.name for root in overrides if (root / wg / path.name).exists()), None)
            seen.add(path.name)
            yield staged or path, f"{phase.name}/{path.relative_to(phase / wg)}"
    for root in overrides:
        for path in sorted((root / wg).glob("*.jsonld")) if (root / wg).is_dir() else ():
            if path.name not in seen:
                yield path, f"(인스턴스 트리에 없음)/{path.name}"


def census(wg: str, overrides: list[Path]) -> dict:
    relations: dict[tuple[str, str], collections.Counter] = collections.defaultdict(collections.Counter)
    assertions: dict[tuple[str, str], collections.Counter] = collections.defaultdict(collections.Counter)
    files = {}
    for path, place in instance_files(wg, overrides):
        document = json.loads(path.read_text())
        keys = id_keys(document.get("@context"))
        files[place] = {"path": str(path), "records": len(document["@graph"]), "contextDeclaresRelations": bool(keys)}
        for record in document["@graph"]:
            kind = as_list(record.get("@type") or "untyped")[0].removeprefix("tdoc:")
            evidenced = all(record.get(key) for key in EVIDENCE_KEYS)
            if kind == "EvidenceAssertion":
                predicate = str(record.get("assertionPredicateIRI", "")).rsplit("#", 1)[-1]
                cell = assertions[(predicate, str(record.get("evidenceStatus")))]
                cell["assertions"] += 1
                cell["withEvidenceFragment"] += bool(record.get("hasEvidence"))
            for key in record:
                if key in keys:
                    cell = relations[(kind, key.removeprefix("tdoc:"))]
                    count = len(as_list(record[key]))
                    cell["links"] += count
                    cell["linksOnRecordsWithEvidenceAttributes"] += count * evidenced
        del document
    rows = [{"recordType": kind, "relation": relation, **dict(cell)}
            for (kind, relation), cell in sorted(relations.items())]
    for row in rows:
        row.setdefault("linksOnRecordsWithEvidenceAttributes", 0)
    return {
        "files": files,
        "relations": rows,
        "relationsWithoutEvidenceAttributes": [f"{r['recordType']}.{r['relation']}" for r in rows
                                               if not r["linksOnRecordsWithEvidenceAttributes"]],
        "assertions": [{"predicate": predicate, "evidenceStatus": status, **dict(cell)}
                       for (predicate, status), cell in sorted(assertions.items())],
    }


def resolution_references(wg: str, dispositions: Dispositions, meetings: WgMeetings, phase2_roots: list[Path]) -> dict:
    verified_pairs = set()
    records = [r for group in dispositions.by_id.values() for r in group]
    status = collections.Counter(str(r.get("evidenceStatus")) for r in records)
    checks = collections.Counter()
    report = collections.Counter()
    rules = collections.Counter()
    located = collections.Counter()
    files = {}
    # 근거 파일별로 묶어 읽는다. 본문 글자열을 파일마다 한 번만 만든다.
    for record in sorted(records, key=lambda r: str(r.get("evidencePath"))):
        if record.get("evidenceStatus") != "source_verified":
            continue
        doc = number(local(record["dispositionTarget"]))
        complete = all(record.get(key) for key in EVIDENCE_KEYS)
        path = record.get("evidencePath") or ""
        if path not in files:
            files[path] = file_sha256(path)
        sha_same = files[path] is not None and files[path] == record.get("evidenceSha256")
        named = names(doc, record.get("evidenceQuote") or "")
        found = quote_located(path, record.get("evidenceQuote") or "", doc) if sha_same else None
        method = json.loads(record.get("assessmentMethod") or "{}")
        checks["sourceVerified"] += 1
        checks["evidenceAttributesComplete"] += complete
        checks["evidenceFileSha256Same"] += sha_same
        checks["quoteNamesTarget"] += named
        checks["allThree"] += complete and sha_same and named
        located[{None: "not_checked", True: "located", False: "not_located"}[found]] += 1
        report[meetings.report_matches(path, dispositions.made_at.get(record["dispositionOf"]))] += 1
        rules[f"{method.get('scope')}|{method.get('rule')}"] += 1
        if complete and sha_same and named:
            verified_pairs.add((record["dispositionOf"], record["dispositionTarget"]))
    docx_squashed.cache_clear()

    groups = collections.defaultdict(collections.Counter)
    for path in sorted((INSTANCES / f"phase-2/{wg}").glob("resolutions_*.jsonld")):
        staged = next((root / wg / path.name for root in phase2_roots if (root / wg / path.name).exists()), None)
        for record in json.loads((staged or path).read_text())["@graph"]:
            if "Resolution" not in as_list(record.get("@type")):
                continue
            group = groups[record.get("resolutionScope") or path.stem.removeprefix("resolutions_")]
            references = as_list(record.get("references"))
            group["resolutions"] += 1
            group["resolutionsWithReference"] += bool(references)
            backed = [(record["@id"], target) in verified_pairs for target in references]
            group["resolutionsWithEvidencedReference"] += any(backed)
            group["referencePairs"] += len(references)
            group["referencePairsEvidencedByDispositionRecord"] += sum(backed)
            group["referencePairsNamedInResolutionText"] += sum(
                names(number(local(target)), record.get("content") or "") for target in references)
    total = sum(groups.values(), collections.Counter())
    return {
        "dispositionRecords": {
            "path": str(dispositions.path), "records": len(records), "byEvidenceStatus": dict(status.most_common()),
            **dict(checks), "evidenceFiles": len(files),
            "evidenceFilesMissing": sum(v is None for v in files.values()),
            "quoteNumberSegmentInEvidenceFile": dict(located.most_common()),
            "evidenceFileVersusDecisionMeeting": dict(report.most_common()),
            "byScopeAndRule": dict(rules.most_common()),
        },
        "resolutionReferences": {"all": dict(total), **{name: dict(group) for name, group in sorted(groups.items())}},
    }


def independent_sources(wg: str, dispositions: Dispositions, phase4_roots: list[Path]) -> dict:
    def phase4(name: str) -> Path:
        staged = next((root / wg / name for root in phase4_roots if (root / wg / name).exists()), None)
        return staged or INSTANCES / f"phase-4/{wg}/{name}"

    lists = ListCells(wg)
    packs = PackSources(wg, lists)
    membership, section = collections.Counter(), collections.Counter()
    for record in json.loads(phase4("cr_extensions.jsonld").read_text())["@graph"]:
        doc = number(local(record["@id"]))
        for pack in as_list(record.get("belongsToCRPack")):
            found = [name for name in packs.membership(doc, local(pack)) if name != "pack_directory_file"]
            membership["+".join(found) or ("pack_directory_file_only" if (doc, local(pack)) in packs.directory else "no_source")] += 1
        for target in as_list(record.get("modifiesSection")):
            section[packs.section(doc, target)] += 1
    meeting = collections.Counter()
    for record in json.loads(phase4("crpacks.jsonld").read_text())["@graph"]:
        gold = record.get("tdoc:tsgMeeting")
        direct, other = packs.meeting(local(record["@id"]), gold)
        meeting[("cover_header_same" if direct else "cover_header_differs_or_absent") + "|" + other] += 1
    revision = collections.Counter()
    for record in json.loads((INSTANCES / f"phase-1/{wg}/tdocs.jsonld").read_text())["@graph"]:
        later = number(local(record["@id"]))
        for target in as_list(record.get("isRevisionOf")):
            earlier = number(local(target))
            basis = [f"list_cell[{name}]" for name in sorted(lists.revision(later, earlier))]
            if any(names(later, r.get("evidenceQuote") or "") for r in dispositions.by_target.get(f"tdoc:{earlier}", ())
                   if r.get("evidenceStatus") == "source_verified" and r.get("dispositionCode") == "revised"):
                basis.append("report_revised_to_quote")
            revision["+".join(basis) or "no_written_source"] += 1

    def table(counter: collections.Counter, direct) -> dict:
        return {"links": sum(counter.values()), "linksWithWrittenSource": sum(n for k, n in counter.items() if direct(k)),
                "byBasis": dict(counter.most_common())}

    return {
        "sources": {"packAndSection": str(phase4("cr_extensions.jsonld")), "packs": str(phase4("crpacks.jsonld")),
                    "packCoverRows": packs.cover_source, "packCoversUnread": len(packs.cover_unread),
                    "wgTdocListFiles": lists.files, "wgTdocListUnreadable": lists.unreadable},
        "crPack": table(membership, lambda k: k not in ("pack_directory_file_only", "no_source")),
        "packTsgMeeting": table(meeting, lambda k: k.startswith("cover_header_same")),
        "crSection": table(section, lambda k: k.startswith("clause_written")),
        "revision": table(revision, lambda k: k != "no_written_source"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wg", nargs="+", default=["RAN1", "RAN2", "RAN3", "RAN4", "RAN5"])
    parser.add_argument("--phase2-root", type=Path, help="재구축 처분 기록의 뿌리. 파일이 있는 작업반만 그 파일을 쓴다")
    parser.add_argument("--phase4-root", type=Path, help="Phase-4 파일의 뿌리. 파일이 있는 작업반만 그 파일을 쓴다")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    phase2 = [args.phase2_root] if args.phase2_root else []
    phase4 = [args.phase4_root] if args.phase4_root else []
    result = {}
    for wg in args.wg:
        dispositions = Dispositions(wg, args.phase2_root)
        result[wg] = {
            **resolution_references(wg, dispositions, WgMeetings(wg), phase2),
            "independentSources": independent_sources(wg, dispositions, phase4),
            "relationCensus": census(wg, phase2 + phase4),
        }
        del dispositions
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(wg, json.dumps(result[wg]["resolutionReferences"]["all"]))
        print(wg, json.dumps({k: (v["linksWithWrittenSource"], v["links"]) for k, v in
                              result[wg]["independentSources"].items() if k != "sources"}))
        print(wg, "근거 속성 없는 관계", len(result[wg]["relationCensus"]["relationsWithoutEvidenceAttributes"]),
              "/", len(result[wg]["relationCensus"]["relations"]))


if __name__ == "__main__":
    main()
