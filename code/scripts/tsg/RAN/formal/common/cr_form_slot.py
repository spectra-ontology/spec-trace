"""CR 서식 본문 네 칸(이유 · 요약 · 미승인 결과 · 영향 절)의 값을 서식 틀의 자리로 읽는다.

`cr_form.labelled_value` 는 값을 이름 칸이 있는 행에서 읽는다. 그런데 값은 이름 칸이 아니라 서식 틀의
자리가 정한다. 이름 칸 행과 다음 이름 칸 행 사이가 그 칸의 자리이고, 저자가 이름 칸을 지우거나 망가뜨리거나
값을 아래 행에 적어도 값은 그 자리에 있다. 이름 칸으로만 읽으면 다음 서식들의 값을 잃는다.

* 마지막 칸 `Clauses affected` 의 이름 칸을 지운 서식. `cr_form._slot_value` 는 다음 이름 칸 행을
  끝 표지로 쓰므로 마지막 칸은 읽지 못한다(R2-2206883 · R4-2108478).
* 이름 칸 글자가 망가진 서식. `lauses affected:` · `Summfary of change:` 는 `cr_form.is_label` 이
  이름 칸으로 보지 않는다(R4-2012242 · R4-2012232 · R2-2006178).
* 이름 칸 행은 비워 두고 값을 바로 아래의 이름 칸 없는 행에 적은 서식(R4-2008868 · R5s220398).

읽는 법. 서식 묶음(`cr_form.form_block`)의 행을 차례로 늘어놓고, 각 이름 칸의 첫 행과 끝 표지
(`Other specs` 행이나 `Y | N` 머리 행 가운데 앞선 것)를 기둥으로 삼는다. 칸 `label` 의 자리는

* 이름 칸 행이 있으면 그 행 다음부터, 없으면 서식 틀에서 바로 앞 칸의 이름 칸 행 다음부터 시작한다. 바로 앞
  칸의 이름 칸 행이 있고 값을 가져야 한다. 값이 빈 앞 행 아래의 글은 앞 칸의 값일 수도 있고, 두 칸이 잇달아
  이름 칸을 잃었으면 한 행을 두 칸이 나눠 가질 수 없어서다.
* 시작한 뒤 처음 나오는 이름 칸 행이나 끝 표지에서 끝난다.
* 이름 칸 행이 있어도 서식 틀에서 바로 다음 칸의 이름 칸 행이 없으면 자리를 정하지 않는다. 그 자리에
  다음 칸의 값이 들 수 있어서다(R4-2108478 은 `Clauses affected` 이름 칸을 지우고 값 `6.1, 6.2` 를
  `Consequences if not approved` 행 아래에 둔다).

그 자리에 글 있는 행이 꼭 하나이고 도움말 행(`cr_form._HELP_ROW`)이 아닐 때만 그 행을 값 행으로 읽는다.
이름 칸 행이 있으면 값 행의 이름 칸 자리는 비어 있어야 하고, 없으면 그 자리가 다른 이름 칸이 아니어야 한다.
값은 이름 칸 자리 뒤 첫 글 있는 칸이다.

주의: 이 읽기는 `cr_form.labelled_value` 가 빈 값을 돌려줄 때만 쓴다. 이름 칸으로 읽은 값은 그대로 두고
빈 칸만 채우므로 이미 읽은 값은 바뀌지 않는다.
주의: 자리에 글 있는 행이 둘 이상이면 읽지 않는다. 여러 행에 걸친 값인지, 한 행만 값이고 나머지는 서식
밖의 글인지 글만으로는 가를 수 없다. 이름 칸 행만 있고 자리가 빈 서식은 원문에서도 칸이 빈 것이므로
빈 값이 맞다.
"""

from __future__ import annotations

import cr_form
import docx_text

_ORDER = list(cr_form.FORM_LABELS)


def _end_marker(cells: list[str]) -> bool:
    filled = [c for c in cells if c]
    return filled == ["Y", "N"] or any(c.startswith("Other specs") for c in cells[:2])


def slot_value(table, label: str) -> str | None:
    """서식 틀의 자리에서 읽은 `label` 칸의 값(읽는 법은 모듈 설명). 자리를 정할 수 없거나 값 행이 하나가 아니면 None."""
    rows = [[c.strip() for c in cells]
            for t in cr_form.form_block(table) for cells in docx_text.table_rows(t)]
    first: dict[str, tuple[int, int]] = {}
    for i, cells in enumerate(rows):
        hit = cr_form._row_label(cells)
        if hit and hit[0] not in first:
            first[hit[0]] = (i, hit[1])
    k = _ORDER.index(label)
    if label in first:
        start, col = first[label]
        if k + 1 < len(_ORDER) and _ORDER[k + 1] not in first:
            return None
        present = True
    else:
        if k == 0 or _ORDER[k - 1] not in first:
            return None
        start, col = first[_ORDER[k - 1]]
        if not any(rows[start][col + 1:]):
            return None
        present = False
    stops = [first[o][0] for o in first if first[o][0] > start]
    stops += [i for i in range(start + 1, len(rows)) if _end_marker(rows[i])]
    if not stops:
        return None
    content = [rows[i] for i in range(start + 1, min(stops)) if any(rows[i])]
    if len(content) != 1:
        return None
    cells = content[0]
    if col >= len(cells) or cr_form._HELP_ROW.search(" ".join(cells)):
        return None
    if present and cells[col]:
        return None
    if not present and cr_form._row_label(cells):
        return None
    return next((c for c in cells[col + 1:] if c), None)


def form_value(table, label: str) -> str | None:
    """`cr_form.labelled_value` 의 값, 그것이 비면 서식 틀의 자리에서 읽은 값(`slot_value`)."""
    return cr_form.labelled_value(table, label) or slot_value(table, label)
