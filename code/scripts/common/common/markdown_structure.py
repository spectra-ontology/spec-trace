"""마크다운 코드 울타리의 줄 범위를 읽는 순수 구조 파서."""

import re


FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def fence_mask(lines: list) -> list:
    """코드 울타리 안의 줄과 울타리 자체에 True를 반환한다."""
    out, inside, marker = [], False, ""
    for ln in lines:
        m = FENCE_RE.match(ln)
        if m and not inside and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            inside, marker = True, m.group(1)
            out.append(True)
            continue
        if (m and inside and m.group(1)[0] == marker[0]
                and len(m.group(1)) >= len(marker) and not m.group(2).strip()):
            inside = False
            out.append(True)
            continue
        out.append(inside)
    return out
