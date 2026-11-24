"""CR이 참조한 TS 절을 release와 절 번호로 해석한다.

Spec: scripts/tsg/RAN/formal/common/README.md (WG별 진입점과 공통 구현).
Ontology: ontology/schema/tdoc-ontology.ttl; CR의 대상 TS 절을 연결한다.
Cycle: 절 색인 구성, release 우선순위에 따른 조회, 선택·실패 통계 누적.
배경: WG별 CR 입력 형식과 무관하게 같은 절 선택 규칙을 사용한다.
사용: RAN1~4의 phase-4 CR JSON-LD 생성기와 RAN5 CR 적재기가 호출한다.
LLM 호출: 없음.

지정 release의 절을 우선하고, 없으면 해당 release 이하 중 가장 최신의 절,
그다음 실제로 존재하는 최신 절을 선택한다. release 미지정 시 최신 판본을
사용하며, 선택 방식과 해석 실패 수는 stats에 누적한다.
"""
import re

_REL_NUM_RE = re.compile(r"Rel-(\d+)")


def rel_num(rel: str | None) -> int:
    m = _REL_NUM_RE.search(rel or "")
    return int(m.group(1)) if m else -1



class SectionIndex:
    """release-키 Section 조회: (spec, release, sectionNumber) → sectionId.

    Section은 release-키(`{spec}-Rel-{N}-{secnum}`)로만 존재하므로 CR의
    clausesAffected를 CR target release 기준으로 해소한다. resolve 규칙은
    phase-3 migrate_to_release_aware.py와 동일: exact → fallback-le(≤target
    최신) → fallback-fwd → drop; release 미상이면 latest.
    """

    def __init__(self, entries) -> None:
        # entries: iterable of (sectionId, sectionNumber)
        self.sid_by: dict[tuple[str, str, str], str] = {}
        rels: dict[str, set[str]] = {}
        for sid, secnum in entries:
            secnum = str(secnum)
            if not sid or not sid.endswith("-" + secnum):
                continue
            stem = sid[: -(len(secnum) + 1)]
            if "-Rel-" not in stem:
                continue
            spec, rel_tail = stem.rsplit("-Rel-", 1)
            rel = f"Rel-{rel_tail}"
            self.sid_by[(spec, rel, secnum)] = sid
            rels.setdefault(spec, set()).add(rel)
        self.releases_by_spec: dict[str, list[str]] = {
            spec: sorted(rs, key=rel_num, reverse=True) for spec, rs in rels.items()
        }
        self.stats: dict[str, int] = {}

    def resolve(self, spec: str, secnum: str, target_rel: str | None) -> str | None:
        secnum = str(secnum)
        rels = self.releases_by_spec.get(spec)
        if not rels:
            self.stats["drop-nospec"] = self.stats.get("drop-nospec", 0) + 1
            return None
        if target_rel is None or rel_num(target_rel) < 0:
            target_rel = rels[0]
            base_method = "latest"
        else:
            base_method = "exact"
        sid = self.sid_by.get((spec, target_rel, secnum))
        if sid:
            self.stats[base_method] = self.stats.get(base_method, 0) + 1
            return sid
        tnum = rel_num(target_rel)
        for r in rels:  # descending
            if rel_num(r) <= tnum and (spec, r, secnum) in self.sid_by:
                self.stats["fallback-le"] = self.stats.get("fallback-le", 0) + 1
                return self.sid_by[(spec, r, secnum)]
        for r in rels:
            if (spec, r, secnum) in self.sid_by:
                self.stats["fallback-fwd"] = self.stats.get("fallback-fwd", 0) + 1
                return self.sid_by[(spec, r, secnum)]
        self.stats["drop-nosec"] = self.stats.get("drop-nosec", 0) + 1
        return None
