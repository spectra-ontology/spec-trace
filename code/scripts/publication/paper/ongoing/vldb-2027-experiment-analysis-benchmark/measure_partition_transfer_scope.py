"""선언된 파티션마다 추적 사슬 문항 생성기의 입력 파일 유무와 그 입력이 담는 기록 건수를 인스턴스 파일에서 직접 센다 (모델 호출 없음).

문항 생성기(`build_chain_items.py`)는 파티션마다 다섯 입력을 읽는다.

- `phase-1/{파티션}/tdocs.jsonld`: 문서와 CR(`@type` = `tdoc:CR`), 개정 연결(`isRevisionOf`)
- `phase-2/{파티션}/resolutions_*.jsonld`: 결정이 내려진 회의(`madeAt`)
- `phase-2/{파티션}/decision_dispositions.jsonld`: 처분 기록
- `phase-4/{파티션}/cr_extensions.jsonld`: CR의 총회 묶음 소속(`belongsToCRPack`)과 수정 절(`modifiesSection`)
- `phase-4/{파티션}/crpacks.jsonld`: 총회 CR 묶음과 그 총회 회의(`tdoc:tsgMeeting`)

이 스크립트는 다음을 기록한다.

- `scripts/common/common/axis.py`가 선언한 TSG와 파티션, 인스턴스·입력·문서 트리에 실제로 있는 TSG와 파티션 디렉터리
- 파티션마다 다섯 입력의 유무와 기록 건수, 그 파티션의 모든 인스턴스 파일에 있는 `@type`별 건수
- 판정 `generatorApplicableAsIs`: 다섯 입력이 인스턴스 트리에 모두 있을 때만 참이다(다른 조건은 두지 않는다).

`--staged-root`로 준 디렉터리에 `{파티션}/{파일이름}`이 있으면 그 파일의 유무도 함께 적는다(인스턴스 파일이 없는 파티션을 위해 저장소에 이미 내보내 둔 입력).

사용: python3 measure_partition_transfer_scope.py --out <json> [--staged-root <dir> ...]
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import sys
from pathlib import Path

AXIS = Path("scripts/common/common/axis.py")
OUTPUT_TSG, INPUT_TSG, DOCS_TSG = Path("ontology/output/tsg"), Path("ontology/input/tsg"), Path("docs/tsg")
MEASURED_WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
GENERATOR_INPUTS = {
    "tdocs": ("phase-1", "tdocs.jsonld"),
    "resolutions": ("phase-2", "resolutions_*.jsonld"),
    "decision_dispositions": ("phase-2", "decision_dispositions.jsonld"),
    "cr_extensions": ("phase-4", "cr_extensions.jsonld"),
    "crpacks": ("phase-4", "crpacks.jsonld"),
}


def load_axis():
    spec = importlib.util.spec_from_file_location("axis", AXIS)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclass가 모듈 이름으로 자신을 찾는다
    spec.loader.exec_module(module)
    return module


def graph(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    return data["@graph"] if isinstance(data, dict) else data


def subdirs(path: Path) -> list[str]:
    return sorted(p.name for p in path.iterdir() if p.is_dir()) if path.is_dir() else []


def type_names(record: dict) -> list[str]:
    value = record.get("@type")
    return [str(v) for v in value] if isinstance(value, list) else [str(value)]


def partition_report(instances: Path, partition: str, staged_roots: list[Path]) -> dict:
    phases = [phase for phase in subdirs(instances) if (instances / phase / partition).is_dir()]
    files = {name: sorted((instances / phase / partition).glob(pattern))
             for name, (phase, pattern) in GENERATOR_INPUTS.items()}
    staged = {name: sorted(p.as_posix() for root in staged_roots for p in (root / partition).glob(pattern))
              for name, (phase, pattern) in GENERATOR_INPUTS.items()}
    counts: dict[str, int | None] = {key: None for key in (
        "documents", "changeRequests", "documentsWithRevisionLink", "resolutionsWithMeeting",
        "dispositionRecords", "dispositionRecordsSourceVerifiedWholeTarget",
        "crsInPack", "crsWithModifiedClause", "crPackMemberships", "clauseModifications",
        "crPacks", "crPacksWithTsgMeeting")}
    if files["tdocs"]:
        docs = [r for r in graph(files["tdocs"][0]) if "tdoc:tdocNumber" in r]
        counts["documents"] = len(docs)
        counts["changeRequests"] = sum(r.get("@type") == "tdoc:CR" for r in docs)
        counts["documentsWithRevisionLink"] = sum(bool(r.get("isRevisionOf")) for r in docs)
    if files["resolutions"]:
        counts["resolutionsWithMeeting"] = sum("madeAt" in r for path in files["resolutions"] for r in graph(path))
    if files["decision_dispositions"]:
        records = graph(files["decision_dispositions"][0])
        counts["dispositionRecords"] = len(records)
        counts["dispositionRecordsSourceVerifiedWholeTarget"] = sum(
            r.get("evidenceStatus") == "source_verified"
            and json.loads(r.get("assessmentMethod") or "{}").get("scope") == "whole_target" for r in records)
    if files["cr_extensions"]:
        as_list = lambda v: v if isinstance(v, list) else [v] if v else []
        records = graph(files["cr_extensions"][0])
        counts["crsInPack"] = sum(bool(r.get("belongsToCRPack")) for r in records)
        counts["crsWithModifiedClause"] = sum(bool(r.get("modifiesSection")) for r in records)
        counts["crPackMemberships"] = sum(len(as_list(r.get("belongsToCRPack"))) for r in records)
        counts["clauseModifications"] = sum(len(as_list(r.get("modifiesSection"))) for r in records)
    if files["crpacks"]:
        records = graph(files["crpacks"][0])
        counts["crPacks"] = len(records)
        counts["crPacksWithTsgMeeting"] = sum(bool(r.get("tdoc:tsgMeeting")) for r in records)
    # 생성기 입력이 없는 파티션에 같은 종류의 기록이 다른 파일 이름으로 들어 있지 않은지 보기 위해 전체 유형을 센다.
    types: collections.Counter = collections.Counter()
    instance_files = []
    for phase in phases:
        for path in sorted((instances / phase / partition).glob("*.jsonld")):
            instance_files.append(path.as_posix())
            for record in graph(path):
                if isinstance(record, dict):
                    types.update(type_names(record))
    present = {name: bool(paths) for name, paths in files.items()}
    return {
        "partition": partition, "inMeasuredWorkingGroups": partition in MEASURED_WGS,
        "instancePhases": phases, "instanceFiles": len(instance_files),
        "instanceFilePaths": instance_files if partition not in MEASURED_WGS else None,
        "generatorInputPresent": present,
        "generatorInputsPresent": sum(present.values()), "generatorInputs": len(GENERATOR_INPUTS),
        "generatorApplicableAsIs": all(present.values()),
        "stagedInputPresent": {name: bool(paths) for name, paths in staged.items()} if staged_roots else None,
        "generatorApplicableWithStagedInputs": (all(present[name] or staged[name] for name in GENERATOR_INPUTS)
                                               if staged_roots else None),
        "recordCounts": counts,
        "recordsByType": dict(types.most_common()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--staged-root", type=Path, nargs="*", default=[],
                        help="{파티션}/{파일이름}으로 생성기 입력을 내보내 둔 디렉터리")
    args = parser.parse_args()
    axis = load_axis()
    declared_tsgs = list(axis.VALID_TSGS)
    declared = list(axis.ALL_PARTITIONS)
    on_disk_tsgs = {"instances": subdirs(OUTPUT_TSG), "input": subdirs(INPUT_TSG),
                    "docs": [d for d in subdirs(DOCS_TSG) if d not in axis.TSG_HEADS]}
    partitions_on_disk: dict[str, dict] = {}
    reports = []
    for tsg in sorted(set(declared_tsgs) | set(on_disk_tsgs["instances"])):
        instances = OUTPUT_TSG / tsg / "formal/instances"
        in_instances = sorted({p for phase in subdirs(instances) for p in subdirs(instances / phase)})
        in_input = sorted({p for kind in subdirs(INPUT_TSG / tsg / "formal") for p in subdirs(INPUT_TSG / tsg / "formal" / kind)})
        in_docs = subdirs(DOCS_TSG / tsg / "formal")
        partitions_on_disk[tsg] = {"instances": in_instances, "input": in_input, "docs": in_docs}
        own_declared = [p for p in declared if axis.WG_REGISTRY[p]["tsg"] == tsg]
        for partition in sorted(set(own_declared) | set(in_instances)):
            reports.append({"tsg": tsg, "declared": partition in declared,
                            **partition_report(instances, partition, args.staged_root)})
    outside = [r for r in reports if not r["inMeasuredWorkingGroups"]]
    report = {
        "axis": AXIS.as_posix(),
        "declaredTsgs": declared_tsgs, "declaredPartitions": declared,
        "declaredPartitionsOutsideMeasuredWorkingGroups": [p for p in declared if p not in MEASURED_WGS],
        "tsgDirectoriesOnDisk": on_disk_tsgs, "partitionDirectoriesOnDisk": partitions_on_disk,
        "stagedRoots": [root.as_posix() for root in args.staged_root],
        "partitionsOutsideMeasuredWorkingGroups": len(outside),
        "partitionsOutsideMeasuredWorkingGroupsApplicableAsIs": sum(r["generatorApplicableAsIs"] for r in outside),
        "measuredWorkingGroupsApplicableAsIs": sum(r["generatorApplicableAsIs"] for r in reports
                                                   if r["inMeasuredWorkingGroups"]),
        "measuredWorkingGroups": len(MEASURED_WGS),
        "partitions": reports,
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    brief = {k: v for k, v in report.items() if k != "partitions"}
    brief["partitions"] = [{k: r[k] for k in ("partition", "instancePhases", "generatorInputPresent",
                                               "generatorApplicableAsIs", "generatorApplicableWithStagedInputs",
                                               "recordCounts")} | {"recordsByType": r["recordsByType"] if not r["inMeasuredWorkingGroups"] else "(파일 참조)"}
                           for r in reports]
    print(json.dumps(brief, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
