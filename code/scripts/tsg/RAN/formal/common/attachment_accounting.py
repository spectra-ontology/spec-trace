"""관계 적재기의 선언 수와 실제 MATCH/MERGE 결과 행 수를 집계한다.

Spec: Phase-2 관계 적재와 누락 관계 보고.
Ontology: 각 적재기가 expect()에 등록한 관계 이름을 사용한다.
Cycle: 선언 수 → 질의 결과 count(*) → 관계별 누락·중복 보고.
LLM 호출: 없음. 호출자가 전달한 트랜잭션으로 질의를 실행한다.
"""


class AttachAccounting:
    """MATCH 실패와 여러 끝점에 붙은 관계를 선언 수와 함께 보고한다.

    UNWIND 한 호출에서 누락과 중복이 상쇄될 수 있어 누락 수는 하한이다.
    """

    def __init__(self):
        self._rows = {}
        self._expected = ()

    def expect(self, *names):
        """관계 이름을 등록해 선언이 없는 관계도 보고하고 오타를 차단한다."""
        self._expected = tuple(names)

    @staticmethod
    def _declared(query, params):
        head = query.find("UNWIND $")
        if head == -1:
            return 1
        name = query[head + len("UNWIND $"):].split()[0]
        value = params.get(name)
        return len(value) if isinstance(value, list) else 1

    def run(self, tx, rel, query, **params):
        if self._expected and rel not in self._expected:
            raise KeyError(f"계측 목록에 없는 관계 이름: {rel} (expect: {self._expected})")
        declared = self._declared(query, params)
        attached = tx.run(query, **params).single()["n"]
        slot = self._rows.setdefault(rel, [0, 0, 0, 0])
        slot[0] += declared
        slot[1] += attached
        if attached < declared:
            slot[2] += declared - attached
        elif attached > declared:
            slot[3] += attached - declared
        return attached

    def report(self, prefix="  "):
        for rel in sorted(set(self._rows) | set(self._expected)):
            declared, attached, missing, excess = self._rows.get(rel, (0, 0, 0, 0))
            line = f"{prefix}[{rel}] 선언 {declared}건 → 부착 {attached}행"
            if rel not in self._rows:
                line += " (호출 0회 — 이 관계를 선언한 산출물이 없었다)"
            elif missing or excess:
                line += f" (짝 없음 {missing}건 이상 · 여럿에 걸려 늘어난 행 {excess})"
            print(line)
