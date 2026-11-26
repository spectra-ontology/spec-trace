#!/usr/bin/env python3
"""cq_anchor_guard.py — formal CQ의 식별자·스키마·집계 조건을 검사한다.

Spec: docs/tsg/build/standards/cq_validation_workflow.md.
Ontology: CQ의 고정 식별자 값과 Spec의 문서 단위·릴리스별 노드를 구분한다.
Cycle: CQ 데이터셋 → 읽기 전용 KG 검사 → 검증기 판정.
배경: 결과 행 수와 별개로 식별자 값의 존재·스키마·조인 조건을 검사한다.
사용: formal 5 WG CQ 검증기에서 guard_defects를 호출한다.
LLM 호출: 없음.

노드 속성 맵, WHERE 등호, IN 목록의 고정 문자열 값을 각각 KG에서 확인한다.
예를 들어 22개 회의를 지정해도 12개 회의만 존재하면 결과 행은 남을 수 있으므로
행 수만으로 요청한 식별자 값의 존재를 판단하지 않는다. 재적재 때 회의 번호의
-e 접미 등 표기가 바뀐 경우도 고정 값과 현재 노드가 일치하는지 확인한다.

확인하는 표현은 작은따옴표·큰따옴표 문자열 리터럴이며 파라미터 $x는 제외한다.
  (v:Label {prop: 'lit'})          노드 속성 맵
  v.prop = 'lit' / 'lit' = v.prop   WHERE 등호
  v.prop IN ['a', 'b', …]          IN 목록의 각 값
  'lit' IN v.prop                 목록 속성의 원소
쿼리에 변수의 레이블이 없으면 해당 값의 존재를 모든 노드에서 검색한다.
evidenceStatus 등 _SEMANTIC_QUALIFIERS의 값은 필터 조건으로 취급해 제외한다.

schema_unknowns는 Neo4j EXPLAIN의 알 수 없는 레이블·관계 타입·속성 경고를
수집한다. 현재 온톨로지에 선언된 선택적 필터 속성은 적재된 값이 없어도 허용한다.
집계가 0·[]·false를 담은 한 행을 반환하는 경우도 있어 행 수와 별도로 검사한다.

spec_identity_defects는 specRelease가 없는 문서 단위 Spec과 specRelease가 있는
릴리스별 Spec의 관계를 구분한다. nonzero_defects와 nonnull_defects는 CQ가
선언한 반환 열의 0·null·누락 조건을 검사한다. equal_columns는 모든 행의
숫자 두 열을 비교하고 true_columns는 모든 행의 명시적인 True를 요구한다.
승인·문서 역할 조건도 함께 검사한다.
"""

from __future__ import annotations

import math
import re
import weakref
from functools import lru_cache
from pathlib import Path

_ONTOLOGY_PATH = None

_UNKNOWN_CODES = {
    "Neo.ClientNotification.Statement.UnknownLabelWarning": "label",
    "Neo.ClientNotification.Statement.UnknownRelationshipTypeWarning": "relationship",
    "Neo.ClientNotification.Statement.UnknownPropertyKeyWarning": "property",
}
_UNKNOWN_NAME = re.compile(r"\(the missing \w+(?: \w+)? is: (.+)\)\s*$")

_IDENT = r"[A-Za-z_]\w*"
_STR = r"'((?:[^'\\]|\\.)*)'"

_LABELED_VAR = re.compile(rf"\(\s*({_IDENT})\s*((?::\s*`?{_IDENT}`?\s*)+)")
_NODE_MAP = re.compile(rf"\(\s*({_IDENT})?\s*((?::\s*`?{_IDENT}`?\s*)*)\{{([^{{}}]*)\}}\s*\)")
_MAP_PAIR = re.compile(rf"({_IDENT})\s*:\s*{_STR}")
_WHERE_EQ = re.compile(rf"(?<![\w.])({_IDENT})\.({_IDENT})\s*=(?!~)\s*{_STR}")
_WHERE_EQ_REV = re.compile(rf"{_STR}\s*=\s*({_IDENT})\.({_IDENT})(?!\w)")
_WHERE_IN = re.compile(rf"(?<![\w.])({_IDENT})\.({_IDENT})\s+IN\s+\[([^\]]*)\]", re.IGNORECASE)
_MEMBER_IN = re.compile(rf"{_STR}\s+IN\s+({_IDENT})\.({_IDENT})(?!\w)", re.IGNORECASE)
_LIST_ELEM = re.compile(_STR)

# Semantic qualification selects a population that may legitimately be empty.
# Unlike a document/meeting identifier, a disposition/evidence state is not a
# entity identifier that must exist. The predicate is still checked by EXPLAIN and used
# unchanged by the actual query.
_SEMANTIC_QUALIFIERS = {"evidenceStatus", "dispositionCode", "granularity", "verifiedImpactScope"}


@lru_cache(maxsize=2)
def _declared_semantic_qualifiers(path_string, mtime, size):
    """Only core-declared datatype qualifiers may lack a current DB token.

    Neo4j's observed property-key inventory is empty for an optional property
    when no loaded node in this WG currently qualifies. That population fact
    does not invalidate a property declared by the ontology. Misspelled keys,
    entity identifiers, labels and relationship types remain EXPLAIN defects.
    The file fingerprint invalidates this cache when the core changes.
    """
    from rdflib import Graph, Namespace
    from rdflib.namespace import OWL, RDF
    graph = Graph().parse(path_string)
    ns = Namespace('https://w3id.org/spectra#')
    return frozenset(name for name in _SEMANTIC_QUALIFIERS
                     if (ns[name], RDF.type, OWL.DatatypeProperty) in graph)


def _current_declared_semantic_qualifiers():
    path = _ONTOLOGY_PATH
    stat = path.stat()
    return _declared_semantic_qualifiers(str(path), stat.st_mtime_ns, stat.st_size)


def _labels(spec: str) -> tuple[str, ...]:
    return tuple(x.strip().strip("`") for x in spec.split(":") if x.strip())


def _literal_value(raw: str) -> str:
    """Cypher escape를 실제 $v 값으로 푼다 (Neo4j Cypher Manual, string literals)."""
    escapes = {"t": "\t", "b": "\b", "n": "\n", "r": "\r", "f": "\f",
               "'": "'", '"': '"', "\\": "\\"}
    def decode(match):
        code = match.group(0)[1:]
        if code.startswith("u") and len(code) == 5:
            return chr(int(code[1:], 16))
        if code not in escapes:
            raise ValueError(f"지원하지 않는 Cypher 문자열 escape: {match.group(0)!r}")
        return escapes[code]
    value = re.sub(r"\\(?:u[0-9a-fA-F]{4}|.)", decode, raw)
    return value.encode("utf-16-le", "surrogatepass").decode("utf-16-le", "surrogatepass")


_LEXICAL = re.compile(
    r"//[^\r\n]*|/\*[\s\S]*?\*/|'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|`(?:[^`]|``)*`"
)


def _query_syntax(cypher: str) -> tuple[str, dict[str, str]]:
    """주석과 문자열 내부를 문법으로 오인하지 않도록 리터럴을 임시 식별 키로 바꾼다."""
    values: dict[str, str] = {}
    def replace(match):
        token = match.group(0)
        if token.startswith(("//", "/*")):
            return " "
        if token.startswith("`"):
            return token
        key = f"__cq_literal_{len(values)}"
        # Regex·반환용 문자열은 문법을 숨기는 데만 쓰인다. 고정 식별자 검사에 사용되는
        # 문자열만 extract_anchors에서 디코딩해야 regex escape가 고정 식별자 검사에 섞이지 않는다.
        values[key] = token[1:-1]
        return "'" + key + "'"
    return _LEXICAL.sub(replace, cypher), values


def extract_anchors(cypher: str) -> list[dict]:
    """쿼리의 고정 식별자 값을 추출한다. 같은 (레이블, 속성, 값, 형식)은 한 번만 반환한다."""
    cypher, literals = _query_syntax(cypher)
    var_labels: dict[str, tuple[str, ...]] = {}
    for m in _LABELED_VAR.finditer(cypher):
        var_labels.setdefault(m.group(1), _labels(m.group(2)))

    raw: list[tuple[str | None, tuple[str, ...], str, str, str]] = []
    for m in _NODE_MAP.finditer(cypher):
        var, labels = m.group(1), _labels(m.group(2) or "")
        if not labels and var:
            labels = var_labels.get(var, ())
        for p in _MAP_PAIR.finditer(m.group(3)):
            raw.append((var, labels, p.group(1), p.group(2), "eq"))
    for m in _WHERE_EQ.finditer(cypher):
        raw.append((m.group(1), var_labels.get(m.group(1), ()), m.group(2), m.group(3), "eq"))
    for m in _WHERE_EQ_REV.finditer(cypher):
        raw.append((m.group(2), var_labels.get(m.group(2), ()), m.group(3), m.group(1), "eq"))
    for m in _WHERE_IN.finditer(cypher):
        for e in _LIST_ELEM.finditer(m.group(3)):
            raw.append((m.group(1), var_labels.get(m.group(1), ()), m.group(2), e.group(1), "in"))
    for m in _MEMBER_IN.finditer(cypher):
        raw.append((m.group(2), var_labels.get(m.group(2), ()), m.group(3), m.group(1), "member"))

    seen, out = set(), []
    for var, labels, prop, value, form in raw:
        if prop in _SEMANTIC_QUALIFIERS:
            continue
        value = _literal_value(literals[value])
        key = (labels, prop, value, form)
        if key in seen:
            continue
        seen.add(key)
        out.append({"var": var, "labels": list(labels), "prop": prop, "value": value, "form": form})
    return out


def check_anchors(session, cypher: str) -> list[dict]:
    """고정 식별자 값마다 KG 존재 여부를 exists 필드에 기록한다."""
    anchors = extract_anchors(cypher)
    for a in anchors:
        label = "".join(f":`{x}`" for x in a["labels"])
        cond = f"$v IN n.`{a['prop']}`" if a["form"] == "member" else f"n.`{a['prop']}` = $v"
        rec = session.run(f"MATCH (n{label}) WHERE {cond} RETURN 1 AS hit LIMIT 1", v=a["value"]).single()
        a["exists"] = rec is not None
    return anchors


def schema_unknowns(session, cypher: str) -> list[dict]:
    """EXPLAIN unknowns, allowing declared qualifiers with an empty population."""
    notes = session.run("EXPLAIN " + cypher).consume().notifications or []
    declared_qualifiers = _current_declared_semantic_qualifiers()
    seen, out = set(), []
    for n in notes:
        kind = _UNKNOWN_CODES.get(n.get("code"))
        if not kind:
            continue
        m = _UNKNOWN_NAME.search(n.get("description", ""))
        key = (kind, m.group(1) if m else None)
        if kind == 'property' and key[1] in declared_qualifiers:
            continue
        if key not in seen:
            seen.add(key)
            out.append({"kind": kind, "name": key[1]})
    return out


def audit(session, cypher: str, absent_by_design=()) -> dict:
    """한 CQ의 고정 식별자 값·스키마를 검사해 항목과 결함 목록을 반환한다.
    absent_by_design의 label:X·relationship:X·property:X는 해당 WG에서
    설계상 사용하지 않는 요소다. 선언과 일치하는 스키마 경고와 해당 레이블의
    값 부재는 결함에서 제외한다. 선언한 요소가 KG에 존재하면 결함으로 기록한다."""
    declared = set(absent_by_design)
    anchors = check_anchors(session, cypher)
    unknown = schema_unknowns(session, cypher)
    found = {f"{u['kind']}:{u['name']}" for u in unknown}
    absent_labels = {d.split(":", 1)[1] for d in declared if d.startswith("label:")}
    defects = [f"schema {u['kind']} '{u['name']}' 없음" for u in unknown
               if f"{u['kind']}:{u['name']}" not in declared]
    defects += [f"고정 식별자 {describe([a])} 없음" for a in missing(anchors)
                if not absent_labels.intersection(a["labels"])]
    defects += [f"설계상 부재로 선언된 {d} 가 KG 에 있음" for d in sorted(declared - found)]
    return {"anchors": anchors, "schema_unknown": unknown, "defects": defects}


def missing(anchors: list[dict]) -> list[dict]:
    """exists가 False인 고정 식별자 항목을 반환한다."""
    return [a for a in anchors if not a["exists"]]


def describe(anchors: list[dict]) -> str:
    return ", ".join(f"{':'.join(a['labels']) or '*'}.{a['prop']}='{a['value']}'" for a in anchors)


def nonzero_defects(cq: dict, rows) -> list[str]:
    """nonzero_columns에 선언한 열이 모든 결과 행에서 거짓으로 평가되면 결함을 반환한다.
    열 누락 또는 rows=None도 결함이다. 선언이 없거나 결과 행이 비었으면
    빈 목록을 반환한다. 빈 결과 자체는 별도의 행 수 판정에서 확인한다."""
    cols = cq.get("nonzero_columns") or ()
    if not cols:
        return []
    if rows is None:
        return [f"nonzero_columns {list(cols)} 를 선언했지만 검증기가 결과 행을 넘기지 않음"]
    if not rows:
        return []
    out = []
    for c in cols:
        if not any(c in r for r in rows):
            out.append(f"nonzero_columns 열 '{c}' 이 결과에 없음")
        elif all(not r.get(c) for r in rows):
            out.append(f"nonzero_columns 열 '{c}' 이 결과 {len(rows)} 행 모두 0")
    return out


def nonnull_defects(cq: dict, rows) -> list[str]:
    """선언한 반환 열은 모든 행에 존재하며 값이 None이 아니어야 한다."""
    cols = cq.get("nonnull_columns", ())
    if not isinstance(cols, (list, tuple)) or any(not isinstance(c, str) or not c for c in cols):
        return ["nonnull_columns 는 비어 있지 않은 열 이름 목록이어야 함"]
    if not cols:
        return []
    if rows is None:
        return [f"nonnull_columns {list(cols)} 를 선언했지만 검증기가 결과 행을 넘기지 않음"]
    defects = []
    for column in cols:
        missing = sum(column not in row for row in rows)
        null = sum(column in row and row[column] is None for row in rows)
        if missing or null:
            defects.append(f"nonnull_columns 열 '{column}': 누락 {missing}행, null {null}행")
    return defects


def equal_column_defects(cq: dict, rows) -> list[str]:
    """equal_columns에 선언한 두 숫자 열은 모든 행에서 같은 타입·값이어야 한다.

    집계 열의 비교에 사용한다. bool·문자열·null·비유한 실수·누락을 거절하며,
    빈 결과는 별도의 행 수 조건이 판정한다. 불일치 행을 쿼리에서 제거하지 않는다.
    """
    pairs = cq.get('equal_columns', ())
    if not isinstance(pairs, (list, tuple)) or any(
            not isinstance(pair, (list, tuple)) or len(pair) != 2 or
            any(not isinstance(column, str) or not column for column in pair) or
            pair[0] == pair[1] for pair in pairs):
        return ['equal_columns 는 서로 다른 숫자 열 이름 두 개씩의 목록이어야 함']
    if not pairs:
        return []
    identifier = cq.get('id', '<unknown>')
    if rows is None:
        return [f'CQ {identifier}: equal_columns 를 선언했지만 검증기가 결과 행을 넘기지 않음']
    defects = []
    for left, right in pairs:
        invalid = []
        for index, row in enumerate(rows, 1):
            if not isinstance(row, dict) or left not in row or right not in row:
                invalid.append(index)
                continue
            a, b = row[left], row[right]
            if (type(a) not in (int, float) or type(b) is not type(a) or
                    (type(a) is float and (not math.isfinite(a) or not math.isfinite(b))) or a != b):
                invalid.append(index)
        if invalid:
            defects.append(f"CQ {identifier}: equal_columns '{left}'/'{right}' 조건 위반 행 {invalid}")
    return defects


def true_column_defects(cq: dict, rows) -> list[str]:
    """true_columns에 선언한 열은 모든 결과 행에서 bool True여야 한다."""
    columns = cq.get('true_columns', ())
    if not isinstance(columns, (list, tuple)) or any(not isinstance(c, str) or not c for c in columns):
        return ['true_columns 는 비어 있지 않은 열 이름 목록이어야 함']
    if not columns:
        return []
    identifier = cq.get('id', '<unknown>')
    if rows is None:
        return [f'CQ {identifier}: true_columns 를 선언했지만 검증기가 결과 행을 넘기지 않음']
    defects = []
    for column in columns:
        invalid = [index for index, row in enumerate(rows, 1)
                   if not isinstance(row, dict) or row.get(column) is not True]
        if invalid:
            defects.append(f"CQ {identifier}: true_columns '{column}' 조건 위반 행 {invalid}")
    return defects


# 문서 단위 Spec(specRelease 없음)는 CR MODIFIES·TS REFERENCES_SPEC의 대상 노드이고,
# 릴리스별 Spec(specRelease 있음)은 Section BELONGS_TO_SPEC의 대상이다. 둘은 IN_RELEASE_OF로 연결된다.
# 관계 타입·방향별 Spec의 종류는 현재 그래프에서 조회한다.
# 같은 관계 타입·방향에 두 종류가 모두 있으면 해당 항목으로 Spec 종류를 판정하지 않는다.
_SPEC_IDENTITY_Q = (
    "MATCH (s:Spec)-[r]-() "
    "RETURN type(r) AS t, startNode(r) = s AS specIsStart, s.specRelease IS NOT NULL AS isRelease, count(*) AS n"
)
_NODE_PAT = rf"\(\s*({_IDENT})?\s*((?::\s*`?{_IDENT}`?\s*)*)(?:\{{[^{{}}]*\}})?\s*\)"
_REL_PAT = r"(<)?-\s*\[\s*(?:[A-Za-z_]\w*)?\s*(?::\s*([^\]\s{*]+))?\s*(\*[^\]{]*)?(?:\{[^{}]*\})?\s*\]\s*-(>)?"
_STEP = re.compile(rf"{_NODE_PAT}\s*{_REL_PAT}\s*(?={_NODE_PAT})")
_NODE_AT = re.compile(_NODE_PAT)
_ALIAS = re.compile(rf"([^,]*?)\s+AS\s+({_IDENT})\b", re.IGNORECASE)


_IDENTITY_CACHE: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def spec_identity_map(session) -> dict[tuple[str, bool], str]:
    """(관계 타입, Spec이 시작 노드인가)별 Spec 종류('hub'·'release')를 조회한다.
    두 종류가 모두 관측된 키는 제외하고 세션별로 결과를 캐시한다."""
    if session in _IDENTITY_CACHE:
        return _IDENTITY_CACHE[session]
    seen: dict[tuple[str, bool], set[str]] = {}
    for r in session.run(_SPEC_IDENTITY_Q):
        seen.setdefault((r["t"], r["specIsStart"]), set()).add("release" if r["isRelease"] else "hub")
    imap = {k: next(iter(v)) for k, v in seen.items() if len(v) == 1}
    _IDENTITY_CACHE[session] = imap
    return imap


def spec_roles(cypher: str, imap: dict) -> dict[str, dict[str, set[str]]]:
    """쿼리 변수별로 관계 타입·방향에서 추론한 Spec 종류와 관계 타입 집합을 반환한다."""
    cypher, _ = _query_syntax(cypher)
    var_labels: dict[str, set[str]] = {}
    for m in _NODE_AT.finditer(cypher):
        if m.group(1) and m.group(2):
            var_labels.setdefault(m.group(1), set()).update(_labels(m.group(2)))
    roles: dict[str, dict[str, set[str]]] = {}
    for m in _STEP.finditer(cypher):
        a, left, types, star, right = m.group(1), m.group(3), m.group(4), m.group(5), m.group(6)
        if star or not types:
            continue  # 가변 길이 또는 타입 없는 관계는 Spec 종류 추론에서 제외한다.
        b = _NODE_AT.match(cypher, m.end()).group(1)
        if right and not left:
            ends = [(a, True), (b, False)]
        elif left and not right:
            ends = [(a, False), (b, True)]
        else:
            ends = [(a, None), (b, None)]
        for t in (x.strip().strip("`") for x in types.split("|")):
            for v, start in ends:
                if not v:
                    continue
                if start is None:
                    cand = {imap[k] for k in ((t, True), (t, False)) if k in imap}
                    if len(cand) != 1 or "Spec" not in var_labels.get(v, set()):
                        continue
                    role = cand.pop()
                else:
                    role = imap.get((t, start))
                    if role is None:
                        continue
                roles.setdefault(v, {}).setdefault(role, set()).add(t)
    return roles


def _release_pinned(cypher: str, names) -> set[str]:
    """specRelease 로 고정 · 구분된 변수. 그런 변수에서 `… AS x` 로 만든 별칭(collect(rk)[0] AS latest 등)도 포함한다."""
    cypher, _ = _query_syntax(cypher)
    pinned = {v for v in names
              if re.search(rf"(?<![\w.]){re.escape(v)}\s*\.\s*specRelease\b", cypher)
              or re.search(rf"\(\s*{re.escape(v)}\b[^()]*\{{[^{{}}]*\bspecRelease\s*:", cypher)}
    changed = True
    while changed:
        changed = False
        for m in _ALIAS.finditer(cypher):
            expr, alias = m.group(1), m.group(2)
            if alias not in pinned and any(re.search(rf"(?<![\w.]){re.escape(p)}\b", expr) for p in pinned):
                pinned.add(alias)
                changed = True
    return pinned


def spec_identity_defects(cypher: str, imap: dict, unpinned_by_design=()) -> list[str]:
    """문서 단위 Spec 과 릴리스 Spec 의 신원을 혼동한 쿼리.

    1. 한 변수에서 문서 단위 Spec과 릴리스별 Spec에 해당하는 관계가 모두 추론되면 결함으로 기록한다.
    2. 문서 단위 값(CR 수 · 참조 대상)과 specRelease 로 고정 · 구분하지 않은 릴리스 변수가 한 쿼리에 있으면,
       릴리스별 값이 여러 판을 포함할 수 있으므로 별도 선언이 있는지 검사한다.
    `unpinned_by_design` 은 모든 릴리스에 걸친 집계가 질문의 뜻이라고 CQ 가 선언한 변수다. 선언한 변수가 두 번째 조건에 해당하지
    않으면(변수가 없거나 이미 고정됨) 불필요한 선언으로 기록한다.
    """
    roles = spec_roles(cypher, imap)
    out = [f"Spec 변수 '{v}' 가 문서 단위 Spec의 관계({','.join(sorted(r['hub']))})와 "
           f"릴리스별 Spec의 관계({','.join(sorted(r['release']))})를 모두 사용함"
           for v, r in sorted(roles.items()) if "hub" in r and "release" in r]
    hubs = sorted(v for v, r in roles.items() if "hub" in r and "release" not in r)
    releases = [v for v, r in roles.items() if "release" in r and "hub" not in r]
    pinned = _release_pinned(cypher, releases)
    loose = sorted(v for v in releases if v not in pinned) if hubs else []
    declared = set(unpinned_by_design)
    flagged = [v for v in loose if v not in declared]
    if flagged:
        out.append(f"문서 단위 Spec 변수 {hubs} 와 specRelease 로 고정 · 구분하지 않은 릴리스 Spec 변수 {flagged} 가 "
                   f"한 쿼리에 있음(릴리스별 값의 판 범위를 명시해야 함)")
    out += [f"release_unpinned_by_design 으로 선언한 '{v}' 가 고정되지 않은 릴리스 변수로 쓰이지 않음"
            for v in sorted(declared - set(loose))]
    return out


@lru_cache(maxsize=2)
def _document_decision_classes(path_string, mtime, size):
    """Use the current core's subclass closure rather than a subtype shortlist."""
    from rdflib import Graph, Namespace
    from rdflib.namespace import RDFS
    graph = Graph().parse(path_string)
    ns = Namespace('https://w3id.org/spectra#')
    def closure(base):
        found, pending = {ns[base]}, [ns[base]]
        while pending:
            for child in graph.subjects(RDFS.subClassOf, pending.pop()):
                if child not in found:
                    found.add(child)
                    pending.append(child)
        return {str(value).removeprefix(str(ns)) for value in found}
    return closure('Tdoc'), closure('Resolution')


def document_role_defects(cypher: str) -> list[str]:
    """Check document/decision provenance roles, including reversed patterns.

    The current core defines the class families. Only the direct provenance
    relations below are checked; this is not general OWL query typing.
    """
    path = _ONTOLOGY_PATH
    stat = path.stat()
    document_classes, decision_classes = _document_decision_classes(str(path), stat.st_mtime_ns, stat.st_size)
    syntax, _ = _query_syntax(cypher)
    labels = {}
    for node in _NODE_AT.finditer(syntax):
        if node.group(1):
            labels.setdefault(node.group(1), set()).update(_labels(node.group(2)))
    wrong_document = {'MADE_AT': 'PRESENTED_AT', 'RESOLUTION_BELONGS_TO': 'BELONGS_TO'}
    wrong_decision = {'PRESENTED_AT': 'MADE_AT', 'BELONGS_TO': 'RESOLUTION_BELONGS_TO'}
    defects = []
    for step in _STEP.finditer(syntax):
        a, left, types, star, right = (step.group(i) for i in (1, 3, 4, 5, 6))
        other = _NODE_AT.match(syntax, step.end())
        b = other.group(1)
        if star or not types or bool(left) == bool(right):
            continue
        a_labels = labels.get(a, set()) | set(_labels(step.group(2)))
        b_labels = labels.get(b, set()) | set(_labels(other.group(2)))
        (start, start_labels), (end, end_labels) = (((a, a_labels), (b, b_labels))
            if right else ((b, b_labels), (a, a_labels)))
        for relation in types.replace('`', '').split('|'):
            relation = relation.lstrip(':')
            if start_labels & document_classes and relation in wrong_document:
                defects.append(f"문서 변수 '{start}'의 {relation}는 결정 역할 관계입니다; {wrong_document[relation]}를 사용해야 합니다")
            if start_labels & decision_classes and relation in wrong_decision:
                defects.append(f"결정 변수 '{start}'의 {relation}는 문서 역할 관계입니다; {wrong_decision[relation]}를 사용해야 합니다")
            if end_labels & document_classes and relation == 'HAS_RESOLUTIONS':
                defects.append(f"문서 변수 '{end}'는 HAS_RESOLUTIONS의 결정 대상이 아닙니다; 문서 BELONGS_TO 경로를 사용해야 합니다")
    return list(dict.fromkeys(defects))


def approval_contract_defects(cq: dict) -> list[str]:
    """An authored approval claim requires a target-qualified source assertion.

    Explicit reference-tracing questions retain REFERENCES and may return the
    disposition alongside it. This check applies to approval/incorporation
    predicates, rather than words in an explanatory parenthesis.
    """
    question = re.sub(r'\([^)]*\)', '', cq.get('question', ''))
    syntax, literals = _query_syntax(cq['cypher'])
    approval = bool(re.search(r'승인|반영|변경하는\s+Resolution|\bapproved?\b', question, re.I))
    decision = bool(re.search(r':\s*(?:Agreement|Resolution)\b', syntax))
    if not (approval and decision):
        return []
    labels = {}
    for node in _NODE_AT.finditer(syntax):
        labels.setdefault(node.group(1), set()).update(_labels(node.group(2)))
    decisions = {v for v, ls in labels.items() if ls & {'Agreement', 'Resolution'}}
    dispositions = {v for v, ls in labels.items() if 'DecisionDisposition' in ls}
    incoming, outgoing = set(), set()
    for step in _STEP.finditer(syntax):
        a, left, types, star, right = (step.group(i) for i in (1, 3, 4, 5, 6))
        b = _NODE_AT.match(syntax, step.end()).group(1)
        if star or not types or bool(left) == bool(right):
            continue
        start, end = (a, b) if right else (b, a)
        if types.strip('`') == 'HAS_DISPOSITION' and start in decisions and end in dispositions:
            incoming.add(end)
        if types.strip('`') == 'DISPOSITION_TARGET' and start in dispositions:
            outgoing.add(start)
    bound = incoming & outgoing
    if not bound:
        return ['승인/반영 CQ에 대상별 DecisionDisposition 경로가 필요합니다']

    # Only a property map or a conjunctive WHERE equality on that same variable
    # constrains the assertion. Comments, RETURN expressions and other nodes do
    # not establish the disposition's status. Literal values remain opaque until
    # the matched predicate consumes them.
    predicates = {v: {} for v in bound}
    def retain(variable, prop, key):
        if variable in predicates:
            predicates[variable].setdefault(prop, set()).add(_literal_value(literals[key]))
    for node in _NODE_MAP.finditer(syntax):
        for prop in _MAP_PAIR.finditer(node.group(3)):
            retain(node.group(1), prop.group(1), prop.group(2))
    for where in re.finditer(r'\bWHERE\b(.*?)(?=\b(?:RETURN|WITH|MATCH|OPTIONAL|UNWIND|CALL|ORDER|SKIP|LIMIT|UNION)\b|$)', syntax, re.I | re.S):
        clause = where.group(1)
        if re.search(r'\b(?:OR|NOT|XOR|CASE)\b', clause, re.I):
            continue  # Such predicates need an explicit, unconditional property map.
        for match in _WHERE_EQ.finditer(clause):
            retain(match.group(1), match.group(2), match.group(3))
        for match in _WHERE_EQ_REV.finditer(clause):
            retain(match.group(2), match.group(3), match.group(1))
    if any(props.get('dispositionCode') != {'agreed'} or
           props.get('evidenceStatus') != {'source_verified'} for props in predicates.values()):
        return ['승인 CQ는 source_verified/agreed 처분을 명시해야 합니다']
    return []


def guard_defects(session, cq: dict, rows=None) -> list[str]:
    """CQ 하나의 식별자·스키마·역할·승인·반환 열 조건을 검사한다.
    비어 있지 않은 결함 목록은 행 수와 별개로 FAIL 사유로 사용한다.
    rows는 nonzero_columns·nonnull_columns·equal_columns·true_columns에 사용하는
    결과 행 dict 목록이다."""
    defects = audit(session, cq["cypher"], cq.get("absent_by_design", ()))["defects"]
    defects += spec_identity_defects(cq["cypher"], spec_identity_map(session),
                                     cq.get("release_unpinned_by_design", ()))
    return (defects + document_role_defects(cq["cypher"]) + approval_contract_defects(cq) +
            nonzero_defects(cq, rows) + nonnull_defects(cq, rows) +
            equal_column_defects(cq, rows) + true_column_defects(cq, rows))
