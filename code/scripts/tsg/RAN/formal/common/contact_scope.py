"""Phase-1 Contact 의 범위를 내보내는 Tdoc 의 `hasContact` 에 맞춘다.

02 는 TDoc_List 행마다 Contact 를 짓고, 03 은 같은 행에서 Tdoc 을 지어 `hasContact` 로 잇는다. 두 집합은
03 이 내보낼 인스턴스가 정해진 뒤에야 맞춰 볼 수 있어 어긋남이 두 갈래로 생긴다.

1. 02 가 지었지만 어느 내보낸 Tdoc 도 가리키지 않는 Contact. 03 은 같은 회의로 두 번 들어온 입력을 합치고
   (먼저 온 행의 연락처 번호를 남긴다) 부재 표기를 빼므로, 그 Contact ID 를 지닌 행이 모두 살아남지 못하면
   이렇게 된다. 적재하면 관계 0 노드가 된다.
2. 가리키는 Contact 가 없는 `hasContact`. 03 은 Contact ID 만 있으면 잇지만 02 는 이름(`contactName`, 필수 1)이
   빈 행으로는 Contact 를 짓지 않는다. 적재기는 Contact 를 MATCH 로 찾아 잇기 때문에 간선이 생기지 않는다.

그래서 03 이 내보내기 직전에 이 모듈로 두 쪽을 함께 맞춘다. 1 은 contacts.jsonld 에서 빼고(02 의 출력을 다시
쓴다), 2 는 그 `hasContact` 값을 뺀다 — 이름 없는 Contact 를 지으면 `contactName` 필수 1 을 어기기 때문이다.
뺀 것은 표준출력과 기록 파일에 남긴다. 02 만 다시 돌리면 contacts.jsonld 가 거르지 않은 집합으로 돌아가므로
03 을 이어 돌려야 한다(01→02→03→04 순서).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
_COMMON = _ROOT / "scripts" / "common" / "common"
if str(_COMMON) not in sys.path:
    sys.path.insert(0, str(_COMMON))
from atomic_io import write_json_atomic, write_text_atomic  # noqa: E402

REPORT_NAME = "contact_scope.txt"


def _targets(value) -> list[str]:
    items = value if isinstance(value, list) else [value] if value else []
    return [x["@id"] if isinstance(x, dict) else x for x in items]


def scope_contacts(instances: list[dict], contacts_path: Path, report_path: Path) -> dict[str, int]:
    """`instances` 의 `hasContact` 와 `contacts_path` 의 Contact 를 서로 맞춘다. 둘 다 그 자리에서 고친다."""
    if not contacts_path.exists():
        raise SystemExit(f"{contacts_path.name} 이 없습니다 — 02 를 먼저 돌려야 Contact 범위를 맞출 수 있습니다")
    with open(contacts_path, encoding="utf-8") as f:
        doc = json.load(f)
    graph = doc.get("@graph") if isinstance(doc, dict) else None
    if not isinstance(graph, list):
        raise SystemExit(f"{contacts_path.name}: @graph 목록이 필요합니다")
    known = {c["@id"] for c in graph}

    dangling: list[tuple[str, str]] = []
    referenced: set[str] = set()
    for inst in instances:
        if "hasContact" not in inst:
            continue
        keep = []
        for target in _targets(inst["hasContact"]):
            if target in known:
                keep.append(target)
                referenced.add(target)
            else:
                dangling.append((str(inst.get("tdoc:tdocNumber", inst.get("@id", ""))), target))
        if not keep:
            del inst["hasContact"]
        elif isinstance(inst["hasContact"], list):
            inst["hasContact"] = keep
        elif len(keep) != len(_targets(inst["hasContact"])):
            inst["hasContact"] = keep[0]

    unreferenced = sorted(c["@id"] for c in graph if c["@id"] not in referenced)
    if unreferenced:
        doc["@graph"] = [c for c in graph if c["@id"] in referenced]
        write_json_atomic(contacts_path, doc)

    counts = {
        "Contact(02)": len(graph),
        "Contact(내보냄)": len(graph) - len(unreferenced),
        "어느 Tdoc 도 가리키지 않아 뺀 Contact": len(unreferenced),
        "가리키는 Contact 가 없어 뺀 hasContact": len(dangling),
    }
    report = ["# 03 이 내보내는 Tdoc 의 hasContact 와 02 의 Contact 를 맞춘 기록.",
              "# 두 절이 모두 비어 있으면 맞출 것이 없었다는 뜻이고, 검사를 건너뛰었다는 뜻이 아니다.",
              "", "# 어느 내보낸 Tdoc 도 가리키지 않아 contacts.jsonld 에서 뺀 Contact (@id)"]
    report += unreferenced
    report += ["", "# 가리키는 Contact 가 없어(이름 빈 행에서만 나온 Contact ID) 뺀 hasContact (Tdoc\t@id)"]
    report += [f"{t}\t{c}" for t, c in sorted(dangling)]
    write_text_atomic(report_path, "\n".join(report) + "\n")
    print("\n  Contact 범위: " + " · ".join(f"{k} {v:,}" for k, v in counts.items()))
    return counts
