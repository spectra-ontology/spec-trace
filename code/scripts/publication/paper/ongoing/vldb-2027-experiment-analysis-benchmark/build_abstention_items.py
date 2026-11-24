"""질문 틀 하나로 CR 묶음을 묻되 정답이 세 갈래로 갈리는 보조 문항을 만든다 (모델 호출 없음).

`pack_lookup_empty` 는 없음이 확정된 경우만 시험한다. 이 문항 묶음은 같은 질문 틀(`pack_status3`)에서
답이 있는 경우, 없음이 확정된 경우, 기록이 답을 정하지 못하는 경우를 함께 낸다. 질문은 판정 차례를 함께 준다.
1) CR 묶음 기록이 이 변경 요청을 싣고 있으면 묶음마다 한 행을 낸다 (answer).
2) 아니고, 작업반 회의 보고서가 문서 전체를 승인 없이 닫는 결정(withdrawn · not treated · not pursued · rejected ·
   not agreed)을 적었으면 TSG RAN 에 올라가지 않았으므로 행 없이 답한다 (none).
3) 둘 다 아니면 기록이 묶음을 정하지 못하므로 두 칸이 모두 `INSUFFICIENT_RECORDS` 인 행 하나를 낸다 (insufficient).

정해지지 않음을 행 하나로 적는 까닭: 채점기(`score_chain_eval.py`)를 고치지 않고 행 집합 일치로 채점하려면 이 답도
행 집합이어야 한다. 행 너비를 요청 필드 수와 같게 두어야 행 너비 검사와 질의형 풀이(내는 열 수가 필드 수와 같아야
한다)가 그대로 통한다. 이 낱말은 묶음 번호(RP-…)나 회의 이름(RAN#…)과 겹치지 않는다.
갈래는 `family`(`pack_status3_answer` · `pack_status3_none` · `pack_status3_insufficient`)에 적는다. 채점기가 family 별로
정확도를 따로 내기 때문이다. 문항 id 에는 갈래를 적지 않는다(`{WG}-pack_status3-{문서 번호}`). 풀이 주체에게 가는
묶음에는 id·질문·필드가 실리므로 id 에 갈래가 있으면 답이 샌다.

갈래마다 넣는 문서. 모두 CR 번호와 대상 규격이 있는 변경 요청(tdoc:CR)이다.
- answer: CR 묶음 기록이 싣는다. 처분이 원문 확인 전이어도 1) 로 답이 정해지므로 여기에 든다.
- none: 원문으로 확인한 문서 전체 처분이 있고 모두 닫는 처분이며, 묶음 기록이 싣지 않는다.
- insufficient: 묶음 기록이 싣지 않고 닫는 처분도 없다. 기록이 답을 정하지 못한다는 것이 기록에서 바로 서는 두 경우만 쓴다.
  - agreed_outside_pack_records: 작업반이 문서 전체를 agreed 로 승인했는데 그 회의가 묶음 기록이 덮는 기간 밖에 있다.
    기간은 날짜가 아니라 기록으로 정한다. agreed 로 승인한 CR 이 하나라도 묶음 기록에 실린 작업반 회의 가운데 차례가
    가장 이른 회의부터 가장 늦은 회의까지다. 그 밖의 회의에서 승인한 CR 은 하나도 묶음 기록에 없으므로, 승인된 CR 이
    어느 묶음으로 올라갔는지 기록으로 알 수 없다.
  - no_decision_recorded: 이 문서를 대상으로 하는 처분 기록이 상태·범위를 가리지 않고 하나도 없고, 작업반 회의 보고서
    본문 어디에도 이 문서 번호의 숫자가 나오지 않으며, 문서 목록 상태가 결정을 담지 않는다(available 또는 빈 값).
    승인 여부조차 기록에 없으므로 TSG RAN 에 올라갔는지 정할 수 없다.
  덮는 기간 안의 회의에서 agreed 로 승인했는데 묶음 기록에 없는 CR 은 넣지 않는다. 묶음 기록이 빠뜨린 것인지 실제로
  올라가지 않은 것인지 기록이 갈라 주지 않아, 꼼꼼한 풀이도 "없음"과 "정해지지 않음" 사이에서 갈릴 수 있다. 원문 확인 전
  처분만 있는 문서도 넣지 않는다. 그 처분은 보고서 문장이 문서를 적었다는 뜻이라 문장을 읽는 풀이가 결정으로 읽을 수 있다.
  두 수는 요약에 남긴다.

기록끼리 어긋나 답이 판정 차례가 아니라 어느 기록을 믿느냐에 달리는 문서는 뺀다.
- 모든 갈래: 묶음 기록의 두 방향(CR → 묶음, 묶음 → CR)이 다르다. 문서 목록의 묶음 칸(`tsgCRPack`)에 값이 있는데
  정답 묶음이 아니다(정답이 없는 갈래에서는 값이 있기만 하면 뺀다. `-` 도 "묶음 없음"으로 읽힐 수 있어 같이 뺀다).
  규격과 CR 번호가 같은 다른 문서가 정답 밖의 묶음에 실렸거나 그 문서의 묶음 칸이 정답 밖 묶음을 댄다.
- answer: 처분이 닫는 처분뿐이거나 문서 목록 상태가 닫힘이다.
- none: 원문 확인 전이거나 일부만 다룬 처분 기록이 함께 있다. 문서 목록 상태가 닫힘·available·reserved·빈 값이 아니다.
  뒤 판(isRevisionOf · revisedTo 를 따라간 후속 문서)이 묶음에 실렸거나 묶음 칸에 값이 있다.
- insufficient: 뒤 판이 있다(내용이 뒤 판으로 옮겨 가 그 판의 처분이 답을 정할 수 있다). agreed 갈래는 문서 목록 상태가
  agreed·available·빈 값이 아니다.
질문은 문서 번호와 함께 "CR {cr} to TS {spec}" 를 대므로, 풀이는 "이 변경 요청"을 문서로도 같은 CR 의 판 전체로도 읽을 수
있다. 두 읽기의 답이 같은 문서만 쓴다. 같은 CR 은 규격과 CR 번호(앞 0을 걷은 값)가 같은 문서들이다.
- none: 같은 CR 의 다른 문서와 뒤 판이 모두 원문 확인한 처분만 가지며 그 처분이 닫는 처분 · revised · noted · merged 가운데
  하나다. 승인(agreed · endorsed · conditionally agreed)이나 열린 처분(postponed 등), 원문 확인 전 기록, 처분 기록이 없는
  판이 있으면 CR 로 읽는 풀이에게는 CR 이 닫혔다고 정해지지 않는다.
- agreed_outside_pack_records: 같은 CR 의 다른 문서에 원문 확인 전 기록이 없고, 승인 처분이 있으면 모두 덮는 기간 밖 회의다.
- no_decision_recorded: 같은 CR 의 다른 문서에 처분 기록이 상태를 가리지 않고 하나도 없다.
지금 채택된 문항(`--exclude-items`)의 기준 문서·근거 문서·정답 칸에 나온 문서는 뺀다.
갈래마다 `--per-class` 개를 seed 로 뽑는다. 기존 문항 종류가 칸(작업반 × 종류)마다 20개라 같은 수를 기본값으로 둔다.
모집단이 더 작으면 모두 쓴다. 뽑기는 문서 id 차례로 늘어놓은 모집단에서 `random.Random(f"{seed}:{WG}:{갈래}").sample` 로 한다.
갈래·정답을 따로 다시 구하는 검사는 `verify_abstention_items.py` 가 한다.

사용: python3 build_abstention_items.py --wg RAN3 --out-dir <dir> --exclude-items <jsonl> [<jsonl> ...]
재구축한 처분 기록은 `--phase2-root`, 그래프에서 내보낸 묶음 기록은 `--phase4-root` 로 준다(RAN5 는 phase-4 인스턴스가 없어 필수).
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import re
import zipfile
from pathlib import Path

INSTANCES = Path("ontology/output/tsg/RAN/formal/instances")
MEETINGS = Path("ontology/input/tsg/RAN/formal/meetings")
CLOSING = {"withdrawn", "not_treated", "not_pursued", "rejected", "not_agreed"}
CLOSING_STATUS = {code.replace("_", " ") for code in CLOSING}
# 닫는 처분과 어긋나지 않는 문서 목록 상태: 닫힘 그 자체와 결정을 담지 않는 상태.
NONE_STATUS = CLOSING_STATUS | {"available", "reserved", ""}
AGREED_STATUS = {"agreed", "available", ""}
SILENT_STATUS = {"available", ""}
APPROVING = {"agreed", "endorsed", "conditionally_agreed"}
# 같은 CR 의 다른 판이 이 처분만 가지면 CR 로 읽어도 승인 없이 끝났다.
SETTLED = CLOSING | {"revised", "noted", "merged"}
TOKEN = "INSUFFICIENT_RECORDS"
FIELDS = ["cr_pack", "tsg_meeting"]
QUESTION = (
    "In which TSG RAN CR pack was change request {doc} (CR {cr} to TS {spec}) submitted? "
    "Give the CR pack document number and the TSG RAN meeting. Decide from the records in this order. "
    "First, if a CR pack record lists this change request, give one row for each such CR pack. "
    "Otherwise, if a {wg} meeting report records a decision on the whole document that closed it without approval "
    "(withdrawn, not treated, not pursued, rejected or not agreed), the change request was not submitted to TSG RAN: "
    "answer with no rows. "
    "Otherwise the records do not determine the CR pack: answer with exactly one row that has "
    f"{TOKEN} in both fields, not with an empty answer.")
CLASSES = ("answer", "none", "insufficient")
# 작업 지시가 정한 멈춤 기준. 처분 파일은 수백 MB 이고 읽으면 그 몇 배를 쓴다.
MEMORY_FLOOR_GIB = 8
PARAGRAPH = re.compile(r"<w:p[\s>/]|</w:p>")
# 문단 안에서 글자를 그리는 자리. `w:t` 글, 줄 안 하이픈(`w:noBreakHyphen`, "-" 로 읽는다), 탭·줄바꿈·기호 요소
# (`w:tab` · `w:ptab` · `w:br` · `w:cr` · `w:sym`, 공백으로 읽는다). 기호·탭 자리를 경계로 두어 그 앞뒤 숫자를 잇지 않는다.
GLYPH = re.compile(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>|<w:(noBreakHyphen)\b[^>]*>|<w:(?:tab|ptab|br|cr|sym)\b[^>]*>")


def available_gib() -> float:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 2 ** 20
    raise RuntimeError("MemAvailable not found")


def graph(path: Path) -> list[dict]:
    return json.loads(path.read_text())["@graph"]


def as_list(value) -> list:
    return [] if value is None else value if isinstance(value, list) else [value]


def local(identifier: str) -> str:
    return identifier.rsplit("/", 1)[-1].removeprefix("tdoc:")


def label(meeting: str) -> str:
    return local(meeting).replace("_", "#", 1)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def tsg_number(meeting: str) -> int:
    return int(re.search(r"\d+", meeting).group())


class Records:
    """한 작업반의 문서·처분·묶음 기록과 회의 보고서 본문에 나온 숫자."""

    def __init__(self, wg: str, phase2_root: Path | None, phase4_root: Path | None):
        self.wg = wg
        self.inputs: list[Path] = []

        def source(phase: str, name: str, root: Path | None) -> Path:
            override = root / wg / name if root else None
            path = override if override and override.exists() else INSTANCES / phase / wg / name
            self.inputs.append(path)
            return path

        self.docs = {r["@id"]: r for r in graph(source("phase-1", "tdocs.jsonld", None)) if "tdoc:tdocNumber" in r}
        # 회의 차례: (회의 번호, bis 회의인가). bis 는 RAN1 이 `RAN1_100b-e`, 나머지가 `RAN3_101bis` 로 적는다.
        self.order = {r["@id"]: (r["tdoc:meetingNumberInt"], bool(re.search(r"_\d+b", local(r["@id"]))))
                      for r in graph(source("phase-1", "meetings.jsonld", None))
                      if isinstance(r.get("tdoc:meetingNumberInt"), int)}
        names = sorted({p.name for d in (INSTANCES / "phase-2" / wg, phase2_root / wg if phase2_root else None)
                        if d and d.exists() for p in d.glob("resolutions_*.jsonld")})
        made_at = {r["@id"]: r["madeAt"] for name in names
                   for r in graph(source("phase-2", name, phase2_root)) if "madeAt" in r}
        self.decisions: dict[str, list[dict]] = collections.defaultdict(list)
        self.unverified: collections.Counter[str] = collections.Counter()
        for r in graph(source("phase-2", "decision_dispositions.jsonld", phase2_root)):
            meeting = made_at.get(r["dispositionOf"])
            whole = json.loads(r["assessmentMethod"]).get("scope") == "whole_target"
            if r["evidenceStatus"] == "source_verified" and whole and meeting:
                self.decisions[r["dispositionTarget"]].append({
                    "code": r["dispositionCode"], "meeting": meeting, "dispositionId": r["dispositionId"],
                    "path": r["evidencePath"], "sha256": r["evidenceSha256"], "locator": r["evidenceLocator"]})
            else:
                self.unverified[r["dispositionTarget"]] += 1
        self.forward = {r["@id"]: set(as_list(r.get("belongsToCRPack")))
                        for r in graph(source("phase-4", "cr_extensions.jsonld", phase4_root))}
        self.packs = {}
        self.backward: dict[str, set[str]] = collections.defaultdict(set)
        for pack in graph(source("phase-4", "crpacks.jsonld", phase4_root)):
            self.packs[pack["@id"]] = pack["tdoc:tsgMeeting"]
            for cr in as_list(pack.get("hasCR")):
                self.backward[cr].add(pack["@id"])
        self.later: dict[str, set[str]] = collections.defaultdict(set)
        self.same_identity: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
        for identifier, r in self.docs.items():
            for earlier in as_list(r.get("isRevisionOf")):
                self.later[earlier].add(identifier)
            for successor in as_list(r.get("revisedTo")):
                self.later[identifier].add(successor)
            if self.change(identifier):
                self.same_identity[self.change(identifier)].append(identifier)
        self.coverage = self.pack_record_period()
        self.reports = sorted((MEETINGS / wg / "Final_Report").glob("*.docx"))
        self.digits = self.report_digits()

    def change(self, identifier: str) -> tuple[str, str] | None:
        """(앞 0을 걷은 CR 번호, 규격). CR 번호나 대상 규격이 없으면 None."""
        r = self.docs[identifier]
        cr = str(r.get("tdoc:crNumber") or "").strip()
        if not cr or not isinstance(r.get("modifies"), str):
            return None
        return (cr.lstrip("0") or "0") if cr.isdigit() else cr, local(r["modifies"]).replace("_", ".")

    def packs_of(self, identifier: str) -> set[str]:
        return self.forward.get(identifier, set()) | self.backward.get(identifier, set())

    def column(self, identifier: str) -> str:
        return str(self.docs[identifier].get("tdoc:tsgCRPack") or "").strip()

    def status(self, identifier: str) -> str:
        return str(self.docs[identifier].get("tdoc:status") or "").strip().lower()

    def descendants(self, identifier: str) -> set[str]:
        seen, stack = set(), [identifier]
        while stack:
            for successor in self.later.get(stack.pop(), ()):
                if successor not in seen:
                    seen.add(successor)
                    stack.append(successor)
        return seen - {identifier}

    def pack_record_period(self) -> dict:
        """agreed 로 승인한 변경 요청이 묶음 기록에 실린 작업반 회의의 차례 범위와 회의마다의 승인·실림 수."""
        agreed: dict[str, set[str]] = collections.defaultdict(set)
        for target, decided in self.decisions.items():
            # CR 번호와 대상 규격이 있는 변경 요청만 센다. tdoc:CR 로 적힌 TR 글 제안(TP)은 CR 묶음에 오르지 않는다.
            if self.docs.get(target, {}).get("@type") != "tdoc:CR" or not self.change(target):
                continue
            for decision in decided:
                if decision["code"] == "agreed":
                    agreed[decision["meeting"]].add(target)
        packed = {meeting: {cr for cr in crs if self.packs_of(cr)} for meeting, crs in agreed.items()}
        covered = [meeting for meeting, crs in packed.items() if crs and meeting in self.order]
        first = min(covered, key=self.order.__getitem__)
        last = max(covered, key=self.order.__getitem__)
        return {"first": first, "last": last, "agreed": {m: len(c) for m, c in agreed.items()},
                "packed": {m: len(c) for m, c in packed.items()},
                "firstTsg": min((self.packs[p] for cr in packed[first] for p in self.packs_of(cr)), key=tsg_number),
                "lastTsg": max((self.packs[p] for cr in packed[last] for p in self.packs_of(cr)), key=tsg_number),
                "allTsg": [min(self.packs.values(), key=tsg_number), max(self.packs.values(), key=tsg_number)]}

    def outside(self, meeting: str) -> bool:
        if meeting not in self.order:
            return False
        key = self.order[meeting]
        return key < self.order[self.coverage["first"]] or key > self.order[self.coverage["last"]]

    def report_digits(self) -> set[str]:
        """회의 보고서 본문(word/*.xml 의 w:t 글과 글자 요소, `GLYPH`)에서 문단마다 나온 숫자열."""
        found: set[str] = set()
        for report in self.reports:
            with zipfile.ZipFile(report) as archive:
                for name in archive.namelist():
                    if name.startswith("word/") and name.endswith(".xml"):
                        xml = archive.read(name).decode("utf-8", errors="replace")
                        for segment in PARAGRAPH.split(xml):
                            text = "".join(m.group(1) if m.group(1) is not None else "-" if m.group(2) else " "
                                           for m in GLYPH.finditer(segment))
                            found.update(re.findall(r"\d+", text))
        return found

    def assign(self, identifier: str) -> tuple[str, str]:
        """변경 요청 하나의 (갈래, 근거) 또는 ("excluded", 뺀 까닭)."""
        if not self.change(identifier):
            return "excluded", "cr_without_number_or_spec"
        packs = self.packs_of(identifier)
        if self.forward.get(identifier, set()) != self.backward.get(identifier, set()):
            return "excluded", "pack_directions_disagree"
        named = {local(pack) for pack in packs}
        column = self.column(identifier)
        if column and column not in named:
            return "excluded", "document_list_pack_column_disagrees"
        # 같은 CR 의 다른 문서가 정답 밖 묶음에 실렸으면 "CR {cr} to TS {spec}" 로 찾는 풀이가 그 묶음을 낼 수 있다.
        # 다른 문서의 묶음 칸 `-` 는 그 문서가 묶음에 없다는 말일 뿐 묶음을 대지 않으므로 걸지 않는다.
        for other in self.same_identity[self.change(identifier)]:
            if other != identifier and ({local(p) for p in self.packs_of(other)} - named
                                        or self.column(other) not in named | {"", "-"}):
                return "excluded", "same_cr_identity_packed_elsewhere"
        decided = self.decisions.get(identifier, [])
        codes = {decision["code"] for decision in decided}
        status = self.status(identifier)
        siblings = [other for other in self.same_identity[self.change(identifier)] if other != identifier]
        if packs:
            if (codes and codes <= CLOSING) or status in CLOSING_STATUS:
                return "excluded", "packed_but_closed"
            return "answer", "pack_record"
        if codes and codes <= CLOSING:
            if self.unverified[identifier]:
                return "excluded", "closed_with_unverified_records"
            if status not in NONE_STATUS:
                return "excluded", "closed_but_document_list_status_differs"
            later = self.descendants(identifier)
            if any(self.packs_of(other) or (other in self.docs and self.column(other)) for other in later):
                return "excluded", "closed_but_later_revision_packed"
            for other in set(siblings) | later:
                other_codes = {decision["code"] for decision in self.decisions.get(other, [])}
                if self.unverified[other] or not other_codes or other_codes - SETTLED:
                    return "excluded", "closed_but_same_cr_or_later_revision_not_settled"
            return "none", "closed_without_pack"
        if self.later.get(identifier):
            return "excluded", "undecided_with_later_revision"
        if codes == {"agreed"}:
            if self.unverified[identifier]:
                return "excluded", "agreed_with_unverified_records"
            if status not in AGREED_STATUS:
                return "excluded", "agreed_but_document_list_status_differs"
            if not all(self.outside(decision["meeting"]) for decision in decided):
                return "excluded", "agreed_inside_pack_records"
            if any(self.unverified[other] or any(d["code"] in APPROVING and not self.outside(d["meeting"])
                                                 for d in self.decisions.get(other, []))
                   for other in siblings):
                return "excluded", "agreed_outside_but_same_cr_approved_inside_or_unverified"
            return "insufficient", "agreed_outside_pack_records"
        if not codes:
            if self.unverified[identifier]:
                return "excluded", "only_unverified_records"
            if status not in SILENT_STATUS:
                return "excluded", "no_decision_but_document_list_status"
            if local(identifier).split("-", 1)[-1] in self.digits:
                return "excluded", "no_decision_but_number_in_report"
            if any(self.decisions.get(other) or self.unverified[other] for other in siblings):
                return "excluded", "no_decision_but_same_cr_has_records"
            return "insufficient", "no_decision_recorded"
        return "excluded", "other_decision"

    def item(self, identifier: str, answer_class: str, basis: str) -> dict:
        r = self.docs[identifier]
        number = local(identifier)
        cr = str(r["tdoc:crNumber"]).strip()
        spec = local(r["modifies"]).replace("_", ".")
        decided = sorted(self.decisions.get(identifier, []), key=lambda d: (self.order.get(d["meeting"], (0, 0)), d["dispositionId"]))
        gold = {"answer": sorted({(local(p), self.packs[p]) for p in self.packs_of(identifier)}),
                "none": [], "insufficient": [(TOKEN, TOKEN)]}[answer_class]
        support: dict = {"documentListStatus": self.status(identifier), "documentListPackColumn": self.column(identifier),
                         "presentedAt": label(r["presentedAt"]) if isinstance(r.get("presentedAt"), str) else None}
        if basis == "agreed_outside_pack_records":
            support["agreedAt"] = [{"wgMeeting": label(d["meeting"]), "agreedCRs": self.coverage["agreed"][d["meeting"]],
                                    "agreedCRsInPackRecords": self.coverage["packed"].get(d["meeting"], 0)}
                                   for d in decided]
            support["packRecordPeriod"] = [label(self.coverage["first"]), label(self.coverage["last"])]
        if basis == "no_decision_recorded":
            support["reportsScanned"] = len(self.reports)
        return {"id": f"{self.wg}-pack_status3-{number}", "wg": self.wg, "family": f"pack_status3_{answer_class}",
                "template": "pack_status3", "answerClass": answer_class, "basis": basis, "hops": 1,
                "anchor": identifier, "question": QUESTION.format(doc=number, cr=cr, spec=spec, wg=self.wg),
                "fields": FIELDS, "gold": [list(row) for row in gold], "expectsEmpty": answer_class == "none",
                "evidence": [{"document": number, "disposition": d["code"], "wgMeeting": label(d["meeting"]),
                              **{key: d[key] for key in ("dispositionId", "path", "sha256", "locator")}} for d in decided],
                "support": support}


def excluded_documents(paths: list[Path]) -> set[str]:
    """채택 문항의 기준 문서·근거 문서·정답 칸에 나온 문서 번호."""
    numbers = set()
    for path in paths:
        for item in map(json.loads, path.read_text().splitlines()):
            numbers.add(local(item["anchor"]))
            numbers.update(source["document"] for source in item.get("evidence", []) if source.get("document"))
            numbers.update(str(cell).strip() for row in item["gold"] for cell in row)
    return numbers


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wg", required=True, choices=("RAN1", "RAN2", "RAN3", "RAN4", "RAN5"))
    parser.add_argument("--per-class", type=int, default=20, help="갈래마다 뽑을 문항 수 (기존 종류의 칸당 수와 같다)")
    parser.add_argument("--seed", type=int, default=20261112)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--exclude-items", type=Path, nargs="+", required=True, help="지금 채택된 문항 파일")
    parser.add_argument("--phase2-root", type=Path, help="재구축한 phase-2 파일이 WG별로 놓인 디렉토리")
    parser.add_argument("--phase4-root", type=Path, help="그래프에서 내보낸 phase-4 파일이 WG별로 놓인 디렉토리")
    args = parser.parse_args()
    if available_gib() < MEMORY_FLOOR_GIB:
        raise SystemExit(f"available memory {available_gib():.1f} GiB is below {MEMORY_FLOOR_GIB} GiB; stopped")
    records = Records(args.wg, args.phase2_root, args.phase4_root)
    excluded = excluded_documents(args.exclude_items)
    pools: dict[str, list[str]] = collections.defaultdict(list)
    before: collections.Counter[str] = collections.Counter()
    reasons: collections.Counter[str] = collections.Counter()
    before_basis: collections.Counter[str] = collections.Counter()
    basis_of = {}
    for identifier in sorted(i for i, r in records.docs.items() if r.get("@type") == "tdoc:CR"):
        answer_class, basis = records.assign(identifier)
        if answer_class == "excluded":
            reasons[basis] += 1
            continue
        before[answer_class] += 1
        before_basis[basis] += 1
        if local(identifier) in excluded:
            reasons["in_current_items"] += 1
            continue
        pools[answer_class].append(identifier)
        basis_of[identifier] = basis
    items = []
    for answer_class in CLASSES:
        pool = pools[answer_class]
        chosen = random.Random(f"{args.seed}:{args.wg}:{answer_class}").sample(pool, min(args.per_class, len(pool)))
        items += [records.item(identifier, answer_class, basis_of[identifier]) for identifier in sorted(chosen)]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "abstention_items.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items))
    coverage = records.coverage
    summary = {
        "wg": args.wg, "seed": args.seed, "perClass": args.per_class, "template": "pack_status3",
        "items": len(items), "itemsByClass": dict(collections.Counter(item["answerClass"] for item in items)),
        "itemsByBasis": dict(collections.Counter(item["basis"] for item in items)),
        "population": {c: len(pools[c]) for c in CLASSES},
        "populationBeforeExcludingCurrentItems": {c: before[c] for c in CLASSES},
        "populationByBasis": dict(collections.Counter(basis_of.values())),
        "populationByBasisBeforeExcludingCurrentItems": dict(before_basis),
        "changeRequests": sum(r.get("@type") == "tdoc:CR" for r in records.docs.values()),
        "excludedByReason": dict(sorted(reasons.items())),
        "packRecordPeriod": {"firstWgMeeting": label(coverage["first"]), "lastWgMeeting": label(coverage["last"]),
                             "tsgMeetingsOfFirstAndLast": [coverage["firstTsg"], coverage["lastTsg"]],
                             "tsgMeetingRangeOfAllPacks": coverage["allTsg"],
                             "meetingsOutside": [{"wgMeeting": label(m), "agreedCRs": n}
                                                 for m, n in sorted(coverage["agreed"].items(), key=lambda kv: records.order.get(kv[0], (0, 0)))
                                                 if records.outside(m)],
                             "meetingsInsideWithoutPackedAgreedCR": [
                                 {"wgMeeting": label(m), "agreedCRs": n}
                                 for m, n in sorted(coverage["agreed"].items(), key=lambda kv: records.order.get(kv[0], (0, 0)))
                                 if m in records.order and not records.outside(m) and not coverage["packed"].get(m)]},
        "reportsScanned": [{"path": str(p), "sha256": sha256(p)} for p in records.reports],
        "inputs": [{"path": str(p), "sha256": sha256(p)} for p in records.inputs],
        "excludeItems": [{"path": str(p), "sha256": sha256(p)} for p in args.exclude_items],
    }
    (args.out_dir / "abstention_items_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: summary[key] for key in ("wg", "items", "itemsByClass", "itemsByBasis", "population",
                                                     "populationByBasis")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
