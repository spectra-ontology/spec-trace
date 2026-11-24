"""추적 사슬에서 문항을 만든다 (모델 호출 없음).

문항 하나는 사슬 기록에서 정해진다. 문항 종류(family)가 요청 필드와 사슬 길이를 고정하고,
질문 문장·정답 행·근거는 모두 같은 기록에서 나온다. 정답은 인스턴스 JSON-LD를 직접 따라가 얻고,
정답 행마다 처분 기록의 원문 근거(파일·SHA·위치)를 싣는다. 별도 구현으로 정답을 다시 구해 맞대는
검사는 `verify_chain_items.py`가 한다.

사슬: 문서(개정 관계) → 작업반 처분(회의) → CR → 총회 CR 묶음(총회 회의) → 규격 절

문항 종류
- pack_lookup         CR → 묶음. 요청: cr_pack, tsg_meeting
- pack_lookup_empty   위와 같은 질문. 처분이 withdrawn 등이고 묶음 기록이 없는 CR. 정답은 빈 집합
- disposition_pack    CR → 처분·회의 → 묶음. 요청: disposition, wg_meeting, cr_pack, tsg_meeting
- full_chain          위에 절을 더한다. 요청: disposition, wg_meeting, cr_pack, tsg_meeting, clause
- revision_chain      revised 처분을 받은 문서 → 개정 후속 문서 → 처분 → 묶음.
                      요청: final_document, disposition, cr_pack
- clause_history      절 → 그 절을 고친 CR → 처분·회의 → 묶음. 요청: document, disposition, wg_meeting, cr_pack
- pack_origin         묶음 → 실린 CR → 처분·회의. 요청: document, disposition, wg_meeting

절 단위 집합 연산을 쓰는 종류(`CLAUSE_SET_FAMILIES`). 기본 선택에 들지 않고 `--families`에 이름을 주어 고른다.
CR 쪽 기록과 묶음·절 쪽 기록으로 따로 구한 정답이 같고 행이 1~`MAX_CLAUSE_SET_ROWS`개인 대상만 뽑는다.
- clause_neighbours   CR → 그 CR 이 자기 release 에서 고친 절 → 같은 절을 고친 같은 release 의 다른 CR → 처분·회의
                      → 묶음. 대상 규칙은 full_chain 과 같다. 요청: clause, document, disposition, wg_meeting, cr_pack
- first_change        묶음 → 원문 확인 처분 CR → 그 CR 이 자기 release 에서 고친 절 가운데, 같은 release 의 CR 을
                      실은 앞선 총회 회의(번호가 더 작은 회의)의 묶음이 고친 적 없는 절. 요청: document, specification, clause
- previous_pack       묶음 → 원문 확인 처분 CR → 그 CR 이 자기 release 에서 고친 절 → 같은 release 의 CR 로 그 절을
                      고친 묶음 가운데 가장 늦은 앞선 총회 회의의 묶음 전부. 앞선 묶음이 없는 절은 행을 내지 않는다.
                      요청: specification, clause, cr_pack, tsg_meeting

사용: python3 build_chain_items.py --wg RAN3 RAN4 --per-cell 20 --seed 20261111 --out-dir <dir>
이미 평가한 표본을 유지하고 현재 기록으로 정답만 다시 만들 때: 같은 명령에 --anchors-from <chain_items.jsonl>
절 단위 종류를 만들 때: 같은 명령에 --families clause_neighbours first_change previous_pack
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import re
from pathlib import Path

INSTANCES = Path("ontology/output/tsg/RAN/formal/instances")
# 묶음에 실리지 않는 것이 처분 자체에서 따라 나오는 코드.
CLOSED_WITHOUT_PACK = {"withdrawn", "not_treated", "not_pursued", "rejected", "not_agreed"}
SECTION = re.compile(r"^tdoc:section/(?P<spec>\d{2}\.\d{3}(?:-\d+)?)-(?P<release>Rel-\d+)-(?P<clause>.+)$")

FAMILIES = {
    "pack_lookup": {
        "fields": ["cr_pack", "tsg_meeting"], "hops": 1,
        "question": "In which TSG RAN CR pack was change request {doc} (CR {cr} to TS {spec}) submitted? "
                    "Give the CR pack document number and the TSG RAN meeting.",
    },
    "disposition_pack": {
        "fields": ["disposition", "wg_meeting", "cr_pack", "tsg_meeting"], "hops": 3,
        "question": "Change request {doc} (CR {cr} to TS {spec}) was handled by {wg}. What source-verified disposition "
                    "did {wg} record for the whole document and at which {wg} meeting, and in which TSG RAN CR pack was it then submitted? "
                    "Give the disposition, the {wg} meeting, the CR pack document number and the TSG RAN meeting.",
    },
    "full_chain": {
        "fields": ["disposition", "wg_meeting", "cr_pack", "tsg_meeting", "clause"], "hops": 4,
        "question": "Trace change request {doc} (CR {cr} to TS {spec}) from the {wg} decision to the "
                    "clauses it modifies. Give the source-verified disposition {wg} recorded for the whole document, the {wg} meeting, the TSG RAN CR pack document number, "
                    "the TSG RAN meeting, and each clause of TS {spec} that the CR modifies.",
    },
    "revision_chain": {
        "fields": ["final_document", "disposition", "cr_pack"], "hops": 4,
        "question": "{wg} recorded document {doc} as revised. Follow its revisions to every later version that has a "
                    "source-verified {wg} disposition for the whole document and was submitted in a TSG RAN CR pack. "
                    "Give each such document, that disposition, "
                    "and the CR pack document number.",
    },
    "clause_history": {
        "fields": ["document", "disposition", "wg_meeting", "cr_pack"], "hops": 4,
        "question": "Which {release} change requests that modify clause {clause} of TS {spec} have a source-verified "
                    "{wg} disposition for the whole document and were submitted in a TSG RAN CR pack? Give each document, its "
                    "disposition, the {wg} meeting, and the CR pack document number.",
    },
    "pack_origin": {
        "fields": ["document", "disposition", "wg_meeting"], "hops": 3,
        "question": "TSG RAN CR pack {pack} carries change requests from {wg}. For each change request in the pack "
                    "that has a source-verified {wg} disposition for the whole document, give the document, the disposition, and the {wg} meeting.",
    },
}
FAMILIES["pack_lookup_empty"] = {**FAMILIES["pack_lookup"], "empty": True}

# 같은 절을 고친 다른 CR · 앞선 총회 회의에 없던 절(차집합) · 가장 늦은 앞선 총회 회의(절마다 최댓값)를 묻는 종류.
# FAMILIES 와 따로 두어 기본 선택에 들지 않게 한다. 기록된 생성 명령은 기본 선택으로 같은 문항을 다시 만든다.
CLAUSE_SET_FAMILIES = {
    "clause_neighbours": {
        "fields": ["clause", "document", "disposition", "wg_meeting", "cr_pack"], "hops": 5,
        "question": "Change request {doc} (CR {cr} to TS {spec}) targets {release}. For each clause it modifies in {release}, "
                    "which {release} change requests other than {doc} that modify the same clause have a source-verified "
                    "{wg} disposition for the whole document and were submitted in a TSG RAN CR pack? Give the clause, "
                    "each document, its disposition, the {wg} meeting, and the CR pack document number.",
    },
    "first_change": {
        "fields": ["document", "specification", "clause"], "hops": 5,
        "question": "TSG RAN CR pack {pack} carries change requests from {wg}. Take each change request in the pack that "
                    "has a source-verified {wg} disposition for the whole document and each clause it modifies in the "
                    "release that change request targets ({releases}). Keep the clauses that the pack changes first: no "
                    "change request of that release submitted in a CR pack at an earlier TSG RAN meeting in the records "
                    "modifies the same clause. Give the document, the specification, and the clause.",
    },
    "previous_pack": {
        "fields": ["specification", "clause", "cr_pack", "tsg_meeting"], "hops": 5,
        "question": "TSG RAN CR pack {pack} carries change requests from {wg}. Take each change request in the pack that "
                    "has a source-verified {wg} disposition for the whole document and each clause it modifies in the "
                    "release that change request targets ({releases}). For each such clause, look at the change requests "
                    "of that release that modify the same clause and give every CR pack of the latest earlier TSG RAN "
                    "meeting in the records that carried such a change request; leave out clauses with no earlier pack. "
                    "Give the specification, the clause, the CR pack document number, and the TSG RAN meeting.",
    },
}
# 절 단위 문항의 정답 행 수 상한: 기존 채택 문항 가운데 가장 큰 정답의 행 수.
MAX_CLAUSE_SET_ROWS = 61
TSG_NUMBER = re.compile(r"^RAN#(\d+)$")


def local(identifier: str) -> str:
    return identifier.rsplit("/", 1)[-1].removeprefix("tdoc:")


def meeting_label(identifier: str) -> str:
    return local(identifier).replace("_", "#", 1)


def as_list(value) -> list[str]:
    return [] if value is None else value if isinstance(value, list) else [value]


def release_list(releases) -> str:
    """질문에 적는 release 이름들: 번호 순, 마지막 둘은 or 로 잇는다."""
    ordered = sorted(set(releases), key=lambda name: int(name.split("-")[1]))
    return ordered[-1] if len(ordered) == 1 else ", ".join(ordered[:-1]) + " or " + ordered[-1]


class Chain:
    """한 작업반의 사슬 기록."""

    def __init__(self, wg: str, phase2_root: Path | None = None, phase4_root: Path | None = None):
        # phase2_root에 같은 이름의 파일이 있으면 그 파일을 읽는다(재구축한 처분 기록으로 문항을 만들 때).
        # phase4_root도 같다(phase-4 인스턴스 파일이 없는 작업반의 묶음·절 기록을 그래프에서 내보내 쓸 때).
        roots = {"phase-2": phase2_root, "phase-4": phase4_root}

        def source(rel: str) -> Path:
            root = roots.get(rel.split("/", 1)[0])
            staged = root / wg / Path(rel).name if root else None
            return staged if staged and staged.exists() else INSTANCES / rel
        load = lambda rel: json.loads(source(rel).read_text())["@graph"]
        self.wg = wg
        self.load = load
        # 절 단위 종류가 쓰는 두 방향 기록·총회 회의 번호와 대상 선별 집계. 그 종류를 고를 때만 채운다.
        self.views: tuple[dict, dict] | None = None
        self.tsg_numbers: dict[str, int] = {}
        self.screened: dict[str, collections.Counter] = {}
        self.docs = {r["@id"]: r for r in load(f"phase-1/{wg}/tdocs.jsonld") if "tdoc:tdocNumber" in r}
        made_at = {}
        for path in sorted((INSTANCES / f"phase-2/{wg}").glob("resolutions_*.jsonld")):
            for record in load(f"phase-2/{wg}/{path.name}"):
                if "madeAt" in record:
                    made_at[record["@id"]] = record["madeAt"]
        self.dispositions: dict[str, dict[tuple[str, str], dict]] = collections.defaultdict(dict)
        for record in load(f"phase-2/{wg}/decision_dispositions.jsonld"):
            if (record["evidenceStatus"] != "source_verified"
                    or json.loads(record["assessmentMethod"]).get("scope") != "whole_target"
                    or record["dispositionOf"] not in made_at):
                continue
            key = (record["dispositionCode"], meeting_label(made_at[record["dispositionOf"]]))
            self.dispositions[record["dispositionTarget"]].setdefault(key, {
                "dispositionId": record["dispositionId"], "path": record["evidencePath"],
                "sha256": record["evidenceSha256"], "locator": record["evidenceLocator"]})
        self.pack_of: dict[str, list[str]] = {}
        self.sections_of: dict[str, list[str]] = {}
        for record in load(f"phase-4/{wg}/cr_extensions.jsonld"):
            self.pack_of[record["@id"]] = as_list(record.get("belongsToCRPack"))
            self.sections_of[record["@id"]] = as_list(record.get("modifiesSection"))
        self.packs = {r["@id"]: r for r in load(f"phase-4/{wg}/crpacks.jsonld")}
        self.successors: dict[str, list[str]] = collections.defaultdict(list)
        for identifier, record in self.docs.items():
            for earlier in as_list(record.get("isRevisionOf")):
                self.successors[earlier].append(identifier)

    def is_cr(self, identifier: str) -> bool:
        # 문서 목록이 유형 `CR` 로 적은 문서만 CR 로 본다. 같은 양식의 `draftCR` · `pCR` 는 묶음에 실리지 않으므로
        # 묶음을 묻는 문항(빈 정답 포함)의 대상에서 뺀다. 추적 연결률의 전체 CR 모집단과 같은 정의다.
        record = self.docs.get(identifier, {})
        return record.get("@type") == "tdoc:CR" and record.get("tdoc:type") == "CR"

    def describe(self, identifier: str) -> dict:
        record = self.docs[identifier]
        return {"doc": record["tdoc:tdocNumber"], "cr": record.get("tdoc:crNumber"),
                "spec": local(record["modifies"]).replace("_", ".") if isinstance(record.get("modifies"), str) else None,
                "wg": self.wg}

    def pack_rows(self, identifier: str) -> list[tuple[str, str]]:
        return [(local(p), self.packs[p]["tdoc:tsgMeeting"]) for p in self.pack_of.get(identifier, ())
                if p in self.packs]

    def later_versions(self, identifier: str) -> list[str]:
        seen, queue = [], list(self.successors.get(identifier, ()))
        while queue:
            current = queue.pop(0)
            if current not in seen:
                seen.append(current)
                queue.extend(self.successors.get(current, ()))
        return seen

    # 문항 종류마다 (대상 식별자, 질문 변수, 정답 행, 근거가 되는 문서들)을 낸다.
    def candidates(self, family: str):
        if family in ("pack_lookup", "disposition_pack", "full_chain"):
            for identifier in self.docs:
                packs = self.pack_rows(identifier)
                names = self.describe(identifier)
                if not (self.is_cr(identifier) and packs and names["cr"] and names["spec"]):
                    continue
                if family == "pack_lookup":
                    yield identifier, names, packs, []
                    continue
                dispositions = self.dispositions.get(identifier)
                if not dispositions:
                    continue
                rows = [(code, meeting, pack, tsg) for code, meeting in dispositions for pack, tsg in packs]
                if family == "full_chain":
                    clauses = [m["clause"] for s in self.sections_of.get(identifier, ()) if (m := SECTION.match(s))]
                    if not clauses:
                        continue
                    rows = [row + (clause,) for row in rows for clause in clauses]
                yield identifier, names, rows, [identifier]
        elif family == "pack_lookup_empty":
            for identifier, dispositions in self.dispositions.items():
                names = self.describe(identifier) if identifier in self.docs else {}
                if (self.is_cr(identifier) and names["cr"] and names["spec"]
                        and not self.pack_of.get(identifier)
                        and {code for code, _ in dispositions} <= CLOSED_WITHOUT_PACK):
                    yield identifier, names, [], [identifier]
        elif family == "revision_chain":
            for identifier, dispositions in self.dispositions.items():
                if identifier not in self.docs or {code for code, _ in dispositions} != {"revised"}:
                    continue
                rows, evidence = [], [identifier]
                for later in self.later_versions(identifier):
                    for pack, _ in self.pack_rows(later):
                        for code, _ in self.dispositions.get(later, ()):
                            rows.append((self.docs[later]["tdoc:tdocNumber"], code, pack))
                            evidence.append(later)
                if rows:
                    yield identifier, self.describe(identifier), rows, evidence
        elif family == "clause_history":
            by_section = collections.defaultdict(list)
            for identifier, sections in self.sections_of.items():
                for section in sections:
                    by_section[section].append(identifier)
            for section, members in by_section.items():
                match = SECTION.match(section)
                rows, evidence = [], []
                for identifier in members:
                    # CR 은 자신의 대상 release 판본만 고친다. 적재기가 절이 없는 release 의 CR 을 다른 release 의
                    # 절에 이어 둔 관계는 질문이 말하는 "(Rel-N) 절을 고친 CR"이 아니므로 정답에서 뺀다.
                    target = str(self.docs.get(identifier, {}).get("targetRelease", "")).rsplit("/", 1)[-1].replace("_", "-")
                    if not match or target != match["release"]:
                        continue
                    for pack, _ in self.pack_rows(identifier):
                        for code, meeting in self.dispositions.get(identifier, ()):
                            rows.append((self.docs[identifier]["tdoc:tdocNumber"], code, meeting, pack))
                            evidence.append(identifier)
                if match and rows:
                    yield section, {**match.groupdict(), "wg": self.wg}, rows, evidence
        elif family == "pack_origin":
            for pack, record in self.packs.items():
                rows, evidence = [], []
                for identifier in as_list(record.get("hasCR")):
                    for code, meeting in self.dispositions.get(identifier, ()):
                        if identifier in self.docs:
                            rows.append((self.docs[identifier]["tdoc:tdocNumber"], code, meeting))
                            evidence.append(identifier)
                if rows:
                    yield pack, {"pack": local(pack), "wg": self.wg}, rows, evidence
        elif family in CLAUSE_SET_FAMILIES:
            yield from self.clause_set_candidates(family)
        else:
            raise ValueError(family)

    def release_of(self, identifier: str) -> str:
        # clause_history 와 같은 규칙으로 CR 의 대상 release 를 절 식별자의 release 표기로 바꾼다.
        return str(self.docs.get(identifier, {}).get("targetRelease", "")).rsplit("/", 1)[-1].replace("_", "-")

    @staticmethod
    def view(packs_of: dict[str, list[str]], sections_of: dict[str, list[str]]) -> dict:
        crs_of_pack, crs_of_section = collections.defaultdict(set), collections.defaultdict(set)
        for cr, packs in packs_of.items():
            for pack in packs:
                crs_of_pack[pack].add(cr)
        for cr, sections in sections_of.items():
            for section in sections:
                crs_of_section[section].add(cr)
        return {"packs_of": {cr: set(packs) for cr, packs in packs_of.items()}, "crs_of_pack": dict(crs_of_pack),
                "sections_of": {cr: set(sections) for cr, sections in sections_of.items()},
                "crs_of_section": dict(crs_of_section)}

    def clause_set_views(self) -> tuple[dict, dict]:
        """묶음 소속·절 수정 관계를 CR 쪽 기록(`belongsToCRPack`·`modifiesSection`)과 묶음·절 쪽 기록
        (`CRPack.hasCR`·`Section.modifiedByCR`)에서 따로 모은 두 벌."""
        if self.views is None:
            for pack, record in self.packs.items():
                match = TSG_NUMBER.match(record["tdoc:tsgMeeting"])
                if not match:
                    raise ValueError(f"총회 회의 표기를 번호로 읽지 못함: {pack} {record['tdoc:tsgMeeting']}")
                self.tsg_numbers[pack] = int(match[1])
            member_packs = {cr: [p for p in packs if p in self.packs] for cr, packs in self.pack_of.items()}
            container_packs: dict[str, list[str]] = collections.defaultdict(list)
            container_sections: dict[str, list[str]] = collections.defaultdict(list)
            for pack, record in self.packs.items():
                for cr in dict.fromkeys(as_list(record.get("hasCR"))):
                    container_packs[cr].append(pack)
            for record in self.load(f"phase-4/{self.wg}/section_extensions.jsonld"):
                for cr in dict.fromkeys(as_list(record.get("modifiedByCR"))):
                    container_sections[cr].append(record["@id"])
            self.views = (self.view(member_packs, self.sections_of), self.view(container_packs, container_sections))
        return self.views

    def neighbour_answer(self, anchor: str, view: dict) -> tuple[set[tuple], list[str]]:
        """대상 CR 이 자기 release 에서 고친 절마다, 같은 절을 고친 같은 release 의 다른 CR 가운데 원문 확인 처분과
        묶음 소속이 있는 것: (절, 문서, 처분, 작업반 회의, 묶음)."""
        release, rows, evidence = self.release_of(anchor), set(), set()
        for section in view["sections_of"].get(anchor, ()):
            match = SECTION.match(section)
            if not match or match["release"] != release:
                continue
            for other in view["crs_of_section"].get(section, ()):
                if other == anchor or other not in self.docs or self.release_of(other) != release:
                    continue
                for code, meeting in self.dispositions.get(other, ()):
                    for pack in view["packs_of"].get(other, ()):
                        rows.add((match["clause"], self.docs[other]["tdoc:tdocNumber"], code, meeting, local(pack)))
                        evidence.add(other)
        return rows, sorted(evidence)

    def packed_before(self, section: str, release: str, before: int, view: dict) -> set[str]:
        """그 release 의 CR 로 절을 고친 묶음 가운데 총회 회의 번호가 before 보다 작은 것.
        앞선 묶음의 CR 에는 처분 조건을 걸지 않는다."""
        return {pack for cr in view["crs_of_section"].get(section, ())
                if cr in self.docs and self.release_of(cr) == release
                for pack in view["packs_of"].get(cr, ()) if self.tsg_numbers[pack] < before}

    def pack_answer(self, family: str, pack: str, view: dict) -> tuple[set[tuple], list[str], set[str]]:
        """묶음에 실린 원문 확인 처분 CR 이 자기 release 에서 고친 절마다 first_change · previous_pack 의 행.
        세 번째 값은 그 절들의 release 이다(질문에 적는다)."""
        rows, evidence, releases = set(), set(), set()
        before = self.tsg_numbers[pack]
        for cr in view["crs_of_pack"].get(pack, ()):
            if cr not in self.docs or not self.dispositions.get(cr):
                continue
            for section in view["sections_of"].get(cr, ()):
                match = SECTION.match(section)
                if not match or match["release"] != self.release_of(cr):
                    continue
                releases.add(match["release"])
                earlier = self.packed_before(section, match["release"], before, view)
                if family == "first_change" and not earlier:
                    rows.add((self.docs[cr]["tdoc:tdocNumber"], match["spec"], match["clause"]))
                    evidence.add(cr)
                elif family == "previous_pack" and earlier:
                    latest = max(self.tsg_numbers[p] for p in earlier)
                    rows.update((match["spec"], match["clause"], local(p), self.packs[p]["tdoc:tsgMeeting"])
                                for p in earlier if self.tsg_numbers[p] == latest)
                    evidence.add(cr)
        return rows, sorted(evidence), releases

    def clause_set_candidates(self, family: str):
        """두 방향 기록으로 구한 정답이 같고 행 수가 1~MAX_CLAUSE_SET_ROWS 인 대상. 거른 사유는 self.screened 에 센다."""
        member, container = self.clause_set_views()
        screened = self.screened[family] = collections.Counter()
        if family == "clause_neighbours":
            # 대상 규칙은 full_chain 과 같다: 묶음 소속·CR 번호·규격 번호·원문 확인 처분이 있는 CR.
            anchors = [i for i in self.docs if self.is_cr(i) and self.pack_rows(i) and self.describe(i)["cr"]
                       and self.describe(i)["spec"] and self.dispositions.get(i)]
        else:
            anchors = list(self.packs)
        for anchor in anchors:
            if family == "clause_neighbours":
                (rows, evidence), (other, _) = (self.neighbour_answer(anchor, v) for v in (member, container))
            else:
                (rows, evidence, releases), (other, _, _) = (self.pack_answer(family, anchor, v) for v in (member, container))
            screened["anchorsConsidered"] += 1
            outcome = ("empty" if not rows and not other else "sidesDisagree" if rows != other
                       else f"over{MAX_CLAUSE_SET_ROWS}" if len(rows) > MAX_CLAUSE_SET_ROWS else "eligible")
            screened[outcome] += 1
            if outcome != "eligible":
                continue
            if family == "clause_neighbours":
                names = {**self.describe(anchor), "release": self.release_of(anchor)}
            else:
                names = {"pack": local(anchor), "wg": self.wg, "releases": release_list(releases)}
            yield anchor, names, rows, evidence

    def evidence(self, identifiers: list[str]) -> list[dict]:
        out = []
        for identifier in dict.fromkeys(identifiers):
            for (code, meeting), source in sorted(self.dispositions.get(identifier, {}).items()):
                out.append({"document": self.docs[identifier]["tdoc:tdocNumber"], "disposition": code,
                            "wgMeeting": meeting, **source})
        return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wg", nargs="+", required=True)
    parser.add_argument("--per-cell", type=int, required=True, help="작업반·문항 종류마다 뽑는 문항 수")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--phase2-root", type=Path,
                        help="<root>/<WG>/ 아래에 있는 phase-2 파일을 저장된 인스턴스보다 먼저 읽는다")
    parser.add_argument("--phase4-root", type=Path,
                        help="<root>/<WG>/ 아래에 있는 phase-4 파일을 저장된 인스턴스보다 먼저 읽는다")
    parser.add_argument("--families", nargs="+", choices=[*FAMILIES, *CLAUSE_SET_FAMILIES], default=list(FAMILIES),
                        help="만들 문항 종류. 기본은 FAMILIES 의 일곱 종류이고 CLAUSE_SET_FAMILIES 의 종류는 이름을 주어 고른다")
    parser.add_argument("--anchors-from", type=Path,
                        help="이 문항 파일의 작업반·문항 종류·대상을 표본으로 그대로 쓰고, 질문·정답·근거만 현재 기록에서 "
                             "다시 만든다. 처분 기록이 바뀐 뒤 이미 평가한 표본을 유지할 때 쓴다")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    fixed = collections.defaultdict(list)
    if args.anchors_from:
        for line in args.anchors_from.read_text().splitlines():
            previous = json.loads(line)
            fixed[(previous["wg"], previous["family"])].append(previous["anchor"])
    families = list(dict.fromkeys(args.families))
    specs = {**FAMILIES, **CLAUSE_SET_FAMILIES}
    items, population, ineligible, screening = [], {}, [], {}
    for wg in args.wg:
        chain = Chain(wg, args.phase2_root, args.phase4_root)
        population[wg] = {}
        for family in families:
            spec = specs[family]
            pool = sorted(chain.candidates(family), key=lambda c: c[0])
            population[wg][family] = len(pool)
            if args.anchors_from:
                # 표본은 이전 추출을 따른다. 현재 기록에서 대상이 적격하지 않으면 문항을 만들지 않고 따로 센다.
                by_anchor = {candidate[0]: candidate for candidate in pool}
                drawn = [by_anchor[a] for a in fixed[(wg, family)] if a in by_anchor]
                ineligible += [{"wg": wg, "family": family, "anchor": a} for a in fixed[(wg, family)] if a not in by_anchor]
            else:
                # 작업반·문항 종류마다 독립된 난수열을 써서 다른 칸의 모집단 변화가 표본을 바꾸지 않게 한다.
                rng = random.Random(f"{args.seed}:{wg}:{family}")
                drawn = rng.sample(pool, min(args.per_cell, len(pool)))
            for anchor, names, rows, evidence_of in drawn:
                items.append({
                    "id": f"{wg}-{family}-{local(anchor)}", "wg": wg, "family": family,
                    "hops": spec["hops"], "anchor": anchor,
                    "question": spec["question"].format(**names),
                    "fields": spec["fields"],
                    "gold": sorted({tuple(row) for row in rows}),
                    "expectsEmpty": bool(spec.get("empty")),
                    "evidence": chain.evidence(evidence_of)})
        if chain.screened:
            screening[wg] = {family: {key: counts[key] for key in ("anchorsConsidered", "empty", "sidesDisagree",
                                                                  f"over{MAX_CLAUSE_SET_ROWS}", "eligible")}
                             for family, counts in chain.screened.items()}
    with (args.out_dir / "chain_items.jsonl").open("w") as handle:
        for item in items:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    summary = {"seed": args.seed, "perCell": args.per_cell, "items": len(items), "eligible": population,
               "itemsByFamily": dict(collections.Counter(item["family"] for item in items))}
    if args.anchors_from:
        summary["anchorsFrom"] = str(args.anchors_from)
        summary["anchorsNoLongerEligible"] = ineligible
    if families != list(FAMILIES):
        summary["families"] = families
    if screening:
        summary["clauseSetScreening"] = {"maxRows": MAX_CLAUSE_SET_ROWS, "byWg": screening}
    (args.out_dir / "chain_items_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
