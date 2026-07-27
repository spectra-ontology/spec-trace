#!/usr/bin/env python3
"""sparql_row_equivalence.py — row-level (not merely cardinality-level) equivalence
between the Cypher reference queries and their SPARQL translations for the RAN1
SpectraCQ subset.

Motivation
----------
`release_package/pipeline/validate_sparql_parity.py` establishes *cardinality*
parity: for each RAN1 CQ the SPARQL result has the same number of rows as the
Cypher reference. Cardinality is weak evidence — two queries can return the same
row count and different rows. This harness upgrades the evidence to full-row
equality, and reports honestly where full-row equality cannot be established.

Engines
-------
  Cypher : live Neo4j RAN1 (bolt, read-only), which supplies real types.
  SPARQL : rdflib over the released kg/per_wg/RAN1-body.ttl.
  A third, frozen reference (cqs/spectra_cq_v2.0/gold/RAN1_gold.json) is compared
  too, so the claim can be reproduced from released artifacts without a Neo4j.

Two comparison levels
---------------------
  L1 relation equivalence — the trailing LIMIT is removed from *both* queries and
     the full row multisets are compared. This is the substantive claim: the two
     queries denote the same relation. It is immune to tie-break order, so it does
     not silently credit a query whose top-k happens to coincide.
  L2 top-k ordered equality — the queries are run as written (LIMIT retained) and
     compared as ordered sequences. Strictly stronger than L1 but only meaningful
     when the ORDER BY induces a total order on the result; where it does not, the
     top-k row *set* is under-determined and no engine can be called wrong. Those
     CQs are reported as their own class rather than passed or failed.

Normalization ladder
--------------------
Each stage states exactly what it equates. Nothing here folds case, trims
interior whitespace, rounds numbers, or coerces unequal values together; the
negative-control pass (--negative-controls) demonstrates the comparator still
rejects perturbed rows after every stage is applied.

  N0 projection alignment   Cypher column label <-> SPARQL variable name.
  N1 datatype               same value across two type systems.
  N2 IRI <-> identifier     an entity's IRI <-> its identifier literal.
  N3 aggregate list         Cypher collect() list <-> SPARQL GROUP_CONCAT string.
  N4 row order              order only where the query does not specify one.

Usage
-----
  python3 sparql_row_equivalence.py [--out PATH] [--ttl PATH] [--bolt URI]
                                    [--only CQ_ID[,CQ_ID...]] [--timeout SECONDS]
                                    [--skip-unbounded] [--no-negative-controls]
  python3 sparql_row_equivalence.py --classify-untranslated-only
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import signal
import time
from decimal import Decimal, InvalidOperation

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PKG = os.path.join(REPO, "release_package")
SPECTRA_NS = "https://w3id.org/spectra#"

# ---------------------------------------------------------------------------
# NULL / value sentinels
# ---------------------------------------------------------------------------
NULL = ("null",)


class QueryTimeout(Exception):
    pass


def _alarm(_sig, _frm):
    raise QueryTimeout()


# ---------------------------------------------------------------------------
# N0 — projection alignment
# ---------------------------------------------------------------------------
# Equates: the *label* of a Cypher output column with the *name* of a SPARQL
# result variable, so that row tuples can be built in a common column order.
# Does NOT equate values, and does not permit reordering columns to manufacture a
# match: the mapping is positional (Cypher RETURN order <-> SPARQL SELECT order)
# and the local-name agreement is recorded as an independent cross-check.
_SELECT_RE = re.compile(r"\bSELECT\b(?:\s+(?:DISTINCT|REDUCED))?(.*?)\bWHERE\b", re.S | re.I)


def sparql_select_vars(query: str) -> list[str] | None:
    """Ordered SELECT variable names, or None if the projection is SELECT *."""
    m = _SELECT_RE.search(query)
    if not m:
        return None
    body = m.group(1)
    if body.strip() == "*":
        return None
    out: list[str] = []
    depth = 0
    i = 0
    # Walk the projection so that ?vars inside (EXPR AS ?alias) are not mistaken
    # for projected variables; only the alias is projected.
    while i < len(body):
        ch = body[i]
        if ch == "(":
            j, d = i, 0
            while j < len(body):
                if body[j] == "(":
                    d += 1
                elif body[j] == ")":
                    d -= 1
                    if d == 0:
                        break
                j += 1
            grp = body[i:j + 1]
            am = re.search(r"\bAS\s+\?(\w+)\s*\)\s*$", grp, re.I)
            if am:
                out.append(am.group(1))
            i = j + 1
            continue
        if ch == "?":
            vm = re.match(r"\?(\w+)", body[i:])
            if vm:
                out.append(vm.group(1))
                i += vm.end()
                continue
        i += 1
    return out or None


def cypher_local_names(cols: list[str]) -> list[str]:
    """`t.tdocNumber` -> `tdocNumber`; a bare alias is returned unchanged."""
    return [c.split(".")[-1] for c in cols]


def align_projection(cypher_cols: list[str], sparql_vars: list[str] | None) -> dict:
    """Positional alignment plus an independent local-name cross-check."""
    info: dict = {"cypher_cols": cypher_cols, "sparql_vars": sparql_vars}
    if sparql_vars is None:
        info["status"] = "sparql_select_star"
        return info
    if len(cypher_cols) != len(sparql_vars):
        info["status"] = "arity_mismatch"
        info["arity"] = [len(cypher_cols), len(sparql_vars)]
        return info
    local = cypher_local_names(cypher_cols)
    info["name_agreement"] = (local == sparql_vars)
    if local == sparql_vars:
        info["status"] = "positional_and_name"
    else:
        # Legitimate when the Cypher projection carries duplicate local names
        # (a self-join such as tr.trNumber + tr2.trNumber), which SPARQL must
        # disambiguate. Recorded so it is never a silent reinterpretation.
        info["status"] = "positional_only"
        info["name_diff"] = [[a, b] for a, b in zip(local, sparql_vars) if a != b]
        info["cypher_local_dupes"] = sorted(
            n for n, c in collections.Counter(local).items() if c > 1)
    return info


# ---------------------------------------------------------------------------
# N1 — datatype normalization  /  N2 — IRI <-> identifier  /  N3 — aggregate list
# ---------------------------------------------------------------------------
def _num(v) -> tuple:
    """Exact numeric value; 5, 5.0 and "5" are the same number, 5.1 is not."""
    return ("num", Decimal(str(v)))


def norm_scalar(v, *, uri_log: list | None = None, gold_str_mode: bool = False) -> tuple:
    """N1+N2: canonicalize one cell to a comparable, type-system-neutral token.

    Equates
      * the integer 5, the double 5.0 and (in gold_str_mode) the string "5"
        — identical numeric values differently serialized;
      * xsd:date/dateTime and neo4j temporal values with the same instant,
        via their canonical ISO 8601 form;
      * a plain literal, an xsd:string literal and a language-tagged literal with
        the same lexical form (the language tag is dropped and recorded);
      * a spectra IRI and the identifier that is its IRI local part (N2);
      * Cypher NULL and a SPARQL unbound variable.
    Does NOT equate: different numbers, differently-cased or differently-spaced
    strings, or two distinct IRIs (injectivity is checked by the caller).
    """
    # rdflib terms ------------------------------------------------------------
    try:
        from rdflib.term import BNode, Literal, URIRef
    except Exception:  # pragma: no cover
        Literal = URIRef = BNode = ()  # type: ignore

    if v is None:
        return NULL
    if URIRef and isinstance(v, URIRef):
        s = str(v)
        if s.startswith(SPECTRA_NS):
            local = s[len(SPECTRA_NS):]
            # N2: strip a leading `ClassName_` minting prefix, if present, to
            # recover the identifier literal Neo4j returns.
            m = re.match(r"^([A-Z][A-Za-z0-9]*)_(.+)$", local)
            ident = m.group(2) if m else local
            if uri_log is not None:
                uri_log.append((s, ident))
            return ("str", ident)
        return ("iri", s)
    if BNode and isinstance(v, BNode):
        return ("bnode",)
    if Literal and isinstance(v, Literal):
        try:
            py = v.toPython()
        except Exception:
            py = str(v)
        if isinstance(py, Literal):  # unparsed custom datatype
            return ("str", str(v))
        return norm_scalar(py, uri_log=uri_log, gold_str_mode=gold_str_mode)

    # python / neo4j values ---------------------------------------------------
    if isinstance(v, bool):
        return ("bool", v)
    if isinstance(v, (int, float, Decimal)):
        return _num(v)
    if isinstance(v, (list, tuple)):
        # N3: a list value is compared as a multiset — Cypher collect() has no
        # defined element order, so element order carries no information.
        return ("list", tuple(sorted(
            (norm_scalar(x, uri_log=uri_log, gold_str_mode=gold_str_mode) for x in v),
            key=repr)))
    if isinstance(v, str):
        if gold_str_mode:
            # The released gold file was written with str() over every cell, so
            # None, lists and numbers arrive as their Python reprs. This mode
            # undoes exactly that damage and is used only for the frozen-gold
            # comparison, never for the live-Neo4j one.
            s = v.strip()
            if s == "None":
                return NULL
            if s.startswith("[") and s.endswith("]"):
                try:
                    return norm_scalar(json.loads(s), uri_log=uri_log, gold_str_mode=True)
                except Exception:
                    pass
            if s.lower() in ("true", "false"):
                return ("bool", s.lower() == "true")
            try:
                return _num(s)
            except (InvalidOperation, ValueError):
                pass
        return ("str", v)
    # neo4j.time.* and anything else with a canonical ISO/str form
    return ("str", str(v))


_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)?")


def _elem_str(e: tuple) -> str:
    """Render a normalized list element as the string a GROUP_CONCAT would emit."""
    if e[0] == "null":
        return ""
    return str(e[1])


def _kinds(col: list[tuple]) -> set[str]:
    """Encoding tags present in a column, ignoring nulls."""
    return {c[0] for c in col if c[0] != "null"}


def _all_numeric_lexical(col: list[tuple]) -> bool:
    vals = [c for c in col if c[0] == "str"]
    if not vals:
        return False
    for c in vals:
        try:
            Decimal(str(c[1]).strip())
        except (InvalidOperation, ValueError):
            return False
    return True


def _temporal_facts(col: list[tuple]) -> tuple[bool, bool, bool]:
    """(all ISO temporal, any date-only, all time-of-day zero where present)."""
    vals = [str(c[1]) for c in col if c[0] == "str"]
    if not vals:
        return False, False, True
    date_only = False
    zero_time = True
    for s in vals:
        if not _ISO_DATE.match(s):
            return False, False, True
        rest = s.replace(" ", "T")
        if "T" not in rest:
            date_only = True
        else:
            tod = rest.split("T", 1)[1]
            if re.sub(r"[0:.]", "", tod.split("+")[0].rstrip("Z")) != "":
                zero_time = False
    return True, date_only, zero_time


def decide_column_rule(col_a: list[tuple], col_b: list[tuple]) -> str | None:
    """Choose the normalization for one column from the two sides' encodings alone.

    The decision deliberately never inspects whether the columns agree. A rule that
    fires only when it produces a match would raise the reported match rate by
    construction; here a rule is selected by encoding shape, applied to every cell
    in the column, and equality is decided afterwards. A column whose encodings do
    not fit any listed equation is left untouched, so a genuine difference survives.
    """
    ka, kb = _kinds(col_a), _kinds(col_b)
    # N3: Cypher collect() list  <->  SPARQL GROUP_CONCAT string.
    if (ka == {"list"} and kb == {"str"}) or (kb == {"list"} and ka == {"str"}):
        return "N3_group_concat_split"
    # N1: same number, typed on one side and lexical on the other.
    if ka == {"num"} and kb == {"str"} and _all_numeric_lexical(col_b):
        return "N1_numeric_string"
    if kb == {"num"} and ka == {"str"} and _all_numeric_lexical(col_a):
        return "N1_numeric_string"
    # N1: xsd:date vs xsd:dateTime naming the same day. Only when the dateTime side
    # carries no time-of-day information to lose.
    if ka <= {"str"} and kb <= {"str"}:
        ta, da, za = _temporal_facts(col_a)
        tb, db, zb = _temporal_facts(col_b)
        if ta and tb and (da != db) and za and zb:
            return "N1_date_canonical"
    return None


def apply_column_rule(cell: tuple, rule: str, concat_sep: str) -> tuple:
    """Apply a decided column rule to one cell, unconditionally."""
    if rule == "N3_group_concat_split":
        if cell[0] == "list":
            return ("mset", tuple(sorted(_elem_str(e) for e in cell[1])))
        if cell[0] == "str":
            s = cell[1] or ""
            parts = [p.strip() for p in s.split(concat_sep)] if s.strip() else []
            return ("mset", tuple(sorted(parts)))
        if cell[0] == "null":
            return ("mset", ())
        return cell
    if rule == "N1_numeric_string":
        if cell[0] == "str":
            try:
                return ("num", Decimal(str(cell[1]).strip()))
            except (InvalidOperation, ValueError):
                return cell
        return cell
    if rule == "N1_date_canonical":
        if cell[0] == "str":
            return ("date", str(cell[1]).replace(" ", "T")[:10])
        return cell
    return cell


# ---------------------------------------------------------------------------
# N4 — row order
# ---------------------------------------------------------------------------
# Equates: nothing but *position*. A query that does not specify an order gets a
# multiset comparison (which still preserves multiplicity, so duplicate rows are
# not collapsed); a query with ORDER BY additionally gets an ordered comparison.
_LIMIT_TAIL = re.compile(r"\s*LIMIT\s+\d+\s*;?\s*$", re.IGNORECASE)


def brace_depth_before(query: str, end: int) -> int:
    """Net brace depth of ``query[:end]``, skipping comments, literals and IRIs.

    The scan has to be literal-aware. A ``#`` inside a quoted value (Cypher
    ``'RAN1#121'``, SPARQL ``"RAN1#121"``) or inside an IRI (``<https://w3id.org/
    spectra#>``) is data, not a comment; treating it as a comment swallows the rest of
    the line together with its closing brace and makes a top-level LIMIT look nested.
    """
    depth = 0
    i = 0
    while i < end:
        ch = query[i]
        if ch in "'\"`":
            q = ch
            i += 1
            while i < end:
                if query[i] == "\\":
                    i += 2
                    continue
                if query[i] == q:
                    i += 1
                    break
                i += 1
            continue
        if ch == "<":
            j = query.find(">", i, end)
            if j != -1 and "\n" not in query[i:j] and " " not in query[i:j]:
                i = j + 1
                continue
        if ch == "#" or (ch == "/" and i + 1 < end and query[i + 1] == "/"):
            nl = query.find("\n", i, end)
            i = end if nl == -1 else nl + 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    return depth


def strip_trailing_limit(query: str) -> tuple[str, int | None]:
    """Remove an outermost trailing LIMIT, which truncates the answer to a top-k.

    A LIMIT nested inside a subquery (Cypher ``CALL {}``, SPARQL sub-SELECT) is part
    of what the question asks and must survive: it is only stripped when it sits at
    brace depth zero, i.e. it governs the final result set.
    """
    m = re.search(r"LIMIT\s+(\d+)\s*;?\s*$", query, re.IGNORECASE)
    if not m:
        return query, None
    if brace_depth_before(query, m.start()) != 0:
        return query, None  # nested LIMIT: governs a subquery, not the answer
    return _LIMIT_TAIL.sub("\n", query), int(m.group(1))


def trailing_limit_is_nested(query: str) -> bool:
    """True when the query ends in a LIMIT that belongs to a subquery.

    Such a LIMIT cannot be removed, so a side carrying one is not comparable at the
    relation level against a side whose LIMIT was removed; the caller reports that
    rather than silently comparing a truncated relation with a full one.
    """
    m = re.search(r"LIMIT\s+(\d+)\s*;?\s*$", query, re.IGNORECASE)
    if not m:
        return False
    return brace_depth_before(query, m.start()) != 0


def rows_to_tuples(rows: list[list], cols: int) -> list[tuple]:
    return [tuple(r[:cols]) for r in rows]


def multiset(rows: list[tuple]) -> collections.Counter:
    return collections.Counter(repr(r) for r in rows)


def diagnose_mismatch(cy: list[tuple], sp: list[tuple]) -> dict:
    """Attribute a row-level mismatch to a column and to one failure class.

    Two failures are not the same kind of finding. ``normalization_gap`` means the
    two sides encode a column in shapes for which the ladder holds no equation, so
    equality could not even be posed — a limitation of the comparison. ``result
    mismatch`` means the encodings line up and the rows genuinely disagree — a
    limitation of the translation. Keeping them apart is what stops a reported
    mismatch from being blamed on the wrong party.
    """
    if not cy or not sp:
        return {"failure_class": ("result_mismatch_one_side_empty"),
                "mismatching_columns": [], "column_diagnostics": []}
    ncol = len(cy[0])
    cols: list[dict] = []
    gap = False
    for c in range(ncol):
        a = [r[c] for r in cy]
        b = [r[c] for r in sp]
        ka, kb = _kinds(a), _kinds(b)
        disjoint = bool(ka and kb and not (ka & kb))
        gap = gap or disjoint
        cols.append({
            "col": c,
            "kinds_cypher": sorted(ka),
            "kinds_sparql": sorted(kb),
            "multiset_equal": (collections.Counter(map(repr, a))
                               == collections.Counter(map(repr, b))),
            "kind_disjoint": disjoint,
        })
    cls = ("normalization_gap_encoding" if gap
           else "result_mismatch_cardinality" if len(cy) != len(sp)
           else "result_mismatch_values")
    return {"failure_class": cls,
            "mismatching_columns": [c["col"] for c in cols if not c["multiset_equal"]],
            "column_diagnostics": cols}


def compare_rows(cy: list[tuple], sp: list[tuple], *, ordered: bool,
                 concat_sep: str = ", ") -> dict:
    """Full-row comparison after per-cell cross-engine reconciliation."""
    out: dict = {"n_cypher": len(cy), "n_sparql": len(sp), "rules_applied": {}}
    if len(cy) and len(sp) and len(cy[0]) != len(sp[0]):
        out["verdict"] = "arity_mismatch"
        out["failure_class"] = "normalization_gap_arity"
        return out

    rules: collections.Counter = collections.Counter()

    def reconcile(rows_a: list[tuple], rows_b: list[tuple]) -> tuple[list[tuple], list[tuple]]:
        """Normalize encodings column by column, then let equality be decided later.

        Each column gets at most one rule, chosen by ``decide_column_rule`` from the
        encodings on the two sides; the rule is then applied to every cell of that
        column on both sides. No step consults whether the result matches, so the
        ladder cannot inflate its own pass rate.
        """
        if not rows_a or not rows_b:
            return rows_a, rows_b
        ncol = len(rows_a[0])
        A = [list(r) for r in rows_a]
        B = [list(r) for r in rows_b]
        for c in range(ncol):
            rule = decide_column_rule([r[c] for r in A], [r[c] for r in B])
            if rule is None:
                continue
            rules[rule] += 1
            for r in A:
                r[c] = apply_column_rule(r[c], rule, concat_sep)
            for r in B:
                r[c] = apply_column_rule(r[c], rule, concat_sep)
        return [tuple(r) for r in A], [tuple(r) for r in B]

    cy2, sp2 = reconcile(cy, sp)
    out["rules_applied"] = dict(rules)
    mc, ms = multiset(cy2), multiset(sp2)
    out["multiset_equal"] = (mc == ms)
    out["ordered_equal"] = (cy2 == sp2)
    if not out["multiset_equal"]:
        only_cy = mc - ms
        only_sp = ms - mc
        out["rows_only_cypher"] = sum(only_cy.values())
        out["rows_only_sparql"] = sum(only_sp.values())
        out["sample_only_cypher"] = list(only_cy)[:2]
        out["sample_only_sparql"] = list(only_sp)[:2]
    out["verdict"] = ("ordered_equal" if out["ordered_equal"]
                      else "multiset_equal" if out["multiset_equal"]
                      else "mismatch")
    if ordered and out["multiset_equal"] and not out["ordered_equal"]:
        out["verdict"] = "set_equal_order_differs"
    if out["verdict"] == "mismatch":
        out.update(diagnose_mismatch(cy2, sp2))
    return out


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------
def negative_controls(cy: list[tuple], sp: list[tuple], *, ordered: bool,
                      baseline_equal: bool, concat_sep: str = ", ") -> dict:
    """Mutate the SPARQL side and require the comparator to reject each mutation.

    A normalization ladder is only trustworthy if it still discriminates. Each
    mutation below changes the result in a way that must be caught; the harness
    records detection per mutation, and any undetected mutation is a defect in the
    comparator, not a pass for the CQ.

    Controls are scored only where the unmutated comparison passes. On a CQ that
    already mismatches, every mutation would be "caught" for free, and counting
    those would let a comparator that rejects everything post a perfect control
    score.
    """
    res: dict = {}
    if not sp:
        return {"skipped": "empty result"}
    if not baseline_equal:
        return {"skipped": "baseline_not_equal"}

    def caught(mutated: list[tuple], *, use_ordered: bool) -> bool:
        c = compare_rows(cy, mutated, ordered=use_ordered, concat_sep=concat_sep)
        return not (c["ordered_equal"] if use_ordered else c["multiset_equal"])

    # M1 — perturb one cell (first cell that is a string or number).
    m1 = [list(r) for r in sp]
    tgt = None
    for ci in range(len(m1[0])):
        if m1[0][ci][0] in ("str", "num", "iri", "date"):
            tgt = ci
            break
    if tgt is None:
        res["M1_cell_perturbation"] = "no_perturbable_cell"
    else:
        cell = m1[0][tgt]
        m1[0][tgt] = (("str", str(cell[1]) + "_MUTANT") if cell[0] != "num"
                      else ("num", cell[1] + Decimal(1)))
        res["M1_cell_perturbation"] = caught([tuple(r) for r in m1], use_ordered=ordered)

    # M2 — delete one row.
    res["M2_row_deletion"] = caught(sp[1:], use_ordered=ordered)

    # M3 — duplicate one row (multiplicity must matter).
    res["M3_row_duplication"] = caught(sp + [sp[0]], use_ordered=ordered)

    # M4 — swap two adjacent rows. Detected only under ordered comparison; under a
    # multiset comparison non-detection is the correct behaviour, recorded as such.
    if len(sp) >= 2 and sp[0] != sp[1]:
        sw = list(sp)
        sw[0], sw[1] = sw[1], sw[0]
        if ordered:
            res["M4_adjacent_row_swap"] = caught(sw, use_ordered=True)
        else:
            res["M4_adjacent_row_swap"] = ("not_applicable_unordered"
                                           if not caught(sw, use_ordered=False)
                                           else "unexpectedly_detected")
    else:
        res["M4_adjacent_row_swap"] = "no_distinct_adjacent_pair"

    # M5 — swap two column values inside one row: catches a comparator that has
    # lost the column identity established by N0.
    if len(sp[0]) >= 2:
        done = False
        for i in range(len(sp[0])):
            for j in range(i + 1, len(sp[0])):
                if sp[0][i] != sp[0][j]:
                    sw = [list(r) for r in sp]
                    sw[0][i], sw[0][j] = sw[0][j], sw[0][i]
                    res["M5_column_swap"] = caught([tuple(r) for r in sw], use_ordered=ordered)
                    done = True
                    break
            if done:
                break
        if not done:
            res["M5_column_swap"] = "no_distinct_column_pair"
    else:
        res["M5_column_swap"] = "single_column"

    # M6 — substitute one row for a copy of another, leaving the row count intact.
    # This is the mutation a cardinality-only check cannot see, and it is the exact
    # failure a reviewer has in mind when objecting that two queries can return the
    # same number of different rows.
    distinct = {repr(r): r for r in sp}
    if len(distinct) >= 2:
        sub = list(sp)
        victim = next(i for i, r in enumerate(sub) if repr(r) != repr(sub[0]))
        sub[victim] = sub[0]
        res["M6_row_substitution_same_count"] = caught(sub, use_ordered=ordered)
        res["M6_row_count_preserved"] = (len(sub) == len(sp))
    else:
        res["M6_row_substitution_same_count"] = "fewer_than_two_distinct_rows"
    return res


# ---------------------------------------------------------------------------
# Untranslated-query classification (the non-RAN1 remainder of the benchmark)
# ---------------------------------------------------------------------------
# Each pattern names a Cypher construct that a SPARQL translation must realize
# somehow. The point of the table is not to declare constructs impossible: it is
# to separate constructs already *demonstrated* translatable by the RAN1 subset
# (which ships working SPARQL) from constructs that appear only outside it and are
# therefore unproven. That distinction is what a limitations paragraph can honestly
# rest on.
CYPHER_CONSTRUCTS: list[tuple[str, str]] = [
    # A bounded repetition (*1..3) is the harder of the two: SPARQL 1.1 property
    # paths have no {n,m} form, so a faithful translation must either enumerate the
    # lengths as a UNION or drop the upper bound. The unbounded form (*) maps
    # directly onto a SPARQL transitive path.
    ("var_length_path_bounded", r"\[[^\]]*\*\s*\d*\s*\.\.\s*\d+[^\]]*\]"),
    ("var_length_path_unbounded", r"\[[^\]]*\*\s*(?:\d+\s*\.\.\s*)?\]"),
    ("shortest_path", r"\b(?:all)?shortestPath\s*\("),
    ("apoc_procedure", r"\bapoc\.[A-Za-z]"),
    ("call_subquery", r"\bCALL\s*\{"),
    ("union", r"\bUNION\b"),
    ("unwind", r"\bUNWIND\b"),
    ("optional_match", r"\bOPTIONAL\s+MATCH\b"),
    ("with_pipeline", r"\bWITH\b"),
    ("exists_subquery", r"\bEXISTS\s*\{"),
    ("rel_type_alternation", r"\[[^\]]*:[A-Z_]+\s*\|"),
    ("list_slice", r"\[\s*\.\."),
    ("list_comprehension", r"\[\s*\w+\s+IN\b"),
    ("reduce", r"\breduce\s*\("),
    ("collect_aggregate", r"\bcollect\s*\("),
    ("count_aggregate", r"\bcount\s*\("),
    ("sum_avg_aggregate", r"\b(?:sum|avg)\s*\("),
    ("minmax_aggregate", r"\b(?:min|max)\s*\("),
    ("stats_aggregate", r"\b(?:stDev|stDevP|percentileCont|percentileDisc)\s*\("),
    ("case_expression", r"\bCASE\b"),
    ("coalesce", r"\bCOALESCE\s*\("),
    ("size_function", r"\bsize\s*\("),
    ("type_cast", r"\bto(?:Integer|Float|String|Boolean)\s*\("),
    ("string_function", r"\b(?:toLower|toUpper|split|substring|replace|trim|left|right)\s*\("),
    ("regex_match", r"=~"),
    ("string_predicate", r"\b(?:CONTAINS|STARTS\s+WITH|ENDS\s+WITH)\b"),
    ("internal_id", r"\bid\s*\(\s*\w+\s*\)"),
    ("distinct", r"\bDISTINCT\b"),
    ("order_by", r"\bORDER\s+BY\b"),
    ("limit_skip", r"\b(?:LIMIT|SKIP)\b"),
    ("property_exists_null", r"\bIS\s+(?:NOT\s+)?NULL\b"),
    ("label_predicate", r":\s*[A-Z]\w*\s*\{"),
    ("arithmetic_expr", r"[\w\)]\s*[/*+]\s*[\w\(]"),
    ("path_variable", r"\b\w+\s*=\s*\(\w*:"),
]
_CONSTRUCT_RE = [(n, re.compile(p, re.I)) for n, p in CYPHER_CONSTRUCTS]

# For a Cypher construct that the translated subset never exercises, the honest
# question is whether SPARQL 1.1 offers a counterpart at all, and whether the
# shipped translations already use that counterpart for some other purpose. Both
# are measured against the released .rq files rather than asserted.
SPARQL_COUNTERPART: dict[str, tuple[str, str]] = {
    "exists_subquery": ("FILTER EXISTS", r"FILTER\s+(?:NOT\s+)?EXISTS"),
    "var_length_path_unbounded": ("transitive property path", r"spectra:\w+\s*[*+]"),
    "var_length_path_bounded": ("UNION over fixed lengths / unbounded path",
                                r"spectra:\w+\s*[*+]"),
    "minmax_aggregate": ("MIN()/MAX() aggregate", r"\b(?:MIN|MAX)\s*\("),
    "stats_aggregate": ("no SPARQL 1.1 counterpart", r"(?!x)x"),
    "internal_id": ("no SPARQL counterpart (engine-internal identifier)", r"(?!x)x"),
    "apoc_procedure": ("no SPARQL counterpart (vendor procedure library)", r"(?!x)x"),
    "shortest_path": ("no SPARQL 1.1 counterpart (path length not exposed)", r"(?!x)x"),
    "reduce": ("no SPARQL 1.1 counterpart (list fold)", r"(?!x)x"),
    "path_variable": ("no SPARQL counterpart (paths are not first-class)", r"(?!x)x"),
}


def counterpart_evidence(sparql_dir: str, construct: str) -> dict:
    """Does a SPARQL counterpart exist, and do the shipped translations use it?"""
    label, pat = SPARQL_COUNTERPART.get(construct, ("unclassified", r"(?!x)x"))
    rx = re.compile(pat, re.I)
    hits = [os.path.basename(p)[:-3] for p in sorted(glob.glob(os.path.join(sparql_dir, "*.rq")))
            if rx.search(open(p).read())]
    return {"sparql_counterpart": label,
            "counterpart_exercised_in_shipped_translations": len(hits),
            "example": hits[:2]}


def constructs_of(cypher: str) -> set[str]:
    return {n for n, rx in _CONSTRUCT_RE if rx.search(cypher)}


def classify_untranslated(benchmark_path: str) -> dict:
    """Classify every benchmark question by translation status and constructs."""
    ran1, others = [], []
    for line in open(benchmark_path):
        d = json.loads(line)
        (ran1 if d["wg"] == "RAN1" else others).append(d)

    translated_ids = {os.path.splitext(os.path.basename(p))[0]
                      for p in glob.glob(os.path.join(PKG, "cqs/spectra_cq_v2.0/sparql/*.rq"))}
    # Constructs exercised by queries that DO ship a working SPARQL translation.
    proven: set[str] = set()
    proven_examples: dict[str, list[str]] = collections.defaultdict(list)
    for d in ran1:
        if re.sub(r"^RAN\d+_", "", d["id"]) in translated_ids:
            for c in constructs_of(d["cypher"]):
                proven.add(c)
                if len(proven_examples[c]) < 2:
                    proven_examples[c].append(d["id"])

    per_construct: collections.Counter = collections.Counter()
    novel_per_construct: collections.Counter = collections.Counter()
    buckets: collections.Counter = collections.Counter()
    novel_examples: dict[str, list[str]] = collections.defaultdict(list)
    for d in others:
        cons = constructs_of(d["cypher"])
        for c in cons:
            per_construct[c] += 1
        novel = cons - proven
        if not novel:
            buckets["no_novel_construct"] += 1
        else:
            buckets["has_novel_construct"] += 1
            for c in novel:
                novel_per_construct[c] += 1
                if len(novel_examples[c]) < 4:
                    novel_examples[c].append(d["id"])
    return {
        "total_benchmark_questions": len(ran1) + len(others),
        "translated_wg": "RAN1",
        "translated_count": len(translated_ids),
        "untranslated_count": len(others),
        "untranslated_by_wg": dict(collections.Counter(d["wg"] for d in others)),
        "reason_untranslated": (
            "Scope, not capability. The SPARQL translation effort covered the RAN1 "
            "partition only. The classification below measures whether the "
            "untranslated questions need any Cypher construct that the translated "
            "subset has not already realized in SPARQL."),
        "constructs_proven_translatable": sorted(proven),
        "constructs_proven_examples": {k: v for k, v in sorted(proven_examples.items())},
        "constructs_never_exercised_by_translated_subset": sorted(
            set(per_construct) - proven),
        "constructs_absent_from_entire_benchmark": sorted(
            {n for n, _ in CYPHER_CONSTRUCTS} - proven - set(per_construct)),
        "untranslated_construct_frequency": dict(per_construct.most_common()),
        "novel_construct_frequency": dict(novel_per_construct.most_common()),
        "novel_construct_examples": {k: v for k, v in novel_examples.items()},
        "novel_construct_sparql_counterpart": {
            c: counterpart_evidence(os.path.join(PKG, "cqs/spectra_cq_v2.0/sparql"), c)
            for c in novel_per_construct},
        "buckets": dict(buckets),
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def run_cypher(session, query: str, timeout: int) -> tuple[list[str], list[list]]:
    signal.alarm(timeout)
    try:
        res = session.run(query)
        keys = list(res.keys())
        rows = [[r.get(k) for k in keys] for r in res]
    finally:
        signal.alarm(0)
    return keys, rows


def run_sparql(graph, query: str, timeout: int) -> tuple[list[str], list[list]]:
    signal.alarm(timeout)
    try:
        res = graph.query(query)
        vs = [str(v) for v in (res.vars or [])]
        rows = [[row[v] for v in (res.vars or [])] for row in res]
    finally:
        signal.alarm(0)
    return vs, rows


def subclass_closure(schema_ttl: str) -> dict[str, set[str]]:
    """Transitive rdfs:subClassOf map read from the released ontology.

    The body graph asserts only a resource's most specific class, while the property
    graph gives a node every label in its subclass chain. Comparing the two is only
    meaningful once it is stated which entailment regime is in force, so the axioms are
    read from the shipped ontology rather than guessed.
    """
    from rdflib import Graph, RDFS
    sg = Graph()
    sg.parse(schema_ttl, format="turtle")
    direct: dict[str, set[str]] = collections.defaultdict(set)
    for s, _, o in sg.triples((None, RDFS.subClassOf, None)):
        direct[str(s)].add(str(o))
    closure: dict[str, set[str]] = {}

    def supers(c: str, seen: set[str]) -> set[str]:
        out: set[str] = set()
        for p in direct.get(c, ()):
            if p in seen:
                continue
            seen.add(p)
            out.add(p)
            out |= supers(p, seen)
        return out

    for c in direct:
        closure[c] = supers(c, {c})
    return closure


def type_census(graph, classes: list[str]) -> dict[str, int]:
    """Extent size of each class as asserted in the graph, counted by rdflib.

    Counting classes with a line-oriented text search is unsound on a pretty-printed
    Turtle file, where one subject's type list is wrapped across lines
    (``a spectra:Resolution,\\n    spectra:WorkingAssumption ;``): the superclass looks
    absent and an entailment gap appears that does not exist. The count therefore comes
    from the parsed graph.
    """
    from rdflib import RDF, URIRef
    return {c.rsplit("#", 1)[-1]: sum(1 for _ in graph.subjects(RDF.type, URIRef(c)))
            for c in classes}


def neo4j_label_census(session, classes: list[str]) -> dict[str, int]:
    """Extent size of the same class names as node labels, for cross-store comparison."""
    labels = {r["label"] for r in session.run(
        "CALL db.labels() YIELD label RETURN label")}
    out: dict[str, int] = {}
    for c in classes:
        local = c.rsplit("#", 1)[-1]
        if local not in labels:
            out[local] = None  # label absent from the property graph schema
            continue
        out[local] = session.run(
            f"MATCH (n:`{local}`) RETURN count(n) AS c").single()["c"]
    return out


def materialize_subclass_types(graph, closure: dict[str, set[str]]) -> int:
    """Assert the superclass types the ontology entails. Returns triples added."""
    from rdflib import RDF, URIRef
    pending = []
    for s, _, o in graph.triples((None, RDF.type, None)):
        for sup in closure.get(str(o), ()):
            pending.append((s, RDF.type, URIRef(sup)))
    added = 0
    for t in pending:
        if t not in graph:
            graph.add(t)
            added += 1
    return added


def entailment_sensitive(query: str, affected: set[str]) -> bool:
    """True if materializing superclass types could change this query's answer.

    Only rdf:type triples are added, so an answer can move only when the query
    constrains or projects a type that has subclasses, or reads types into a variable.
    Everything else is provably unchanged and is not re-executed.
    """
    if re.search(r"(\ba\b|rdf:type)\s+\?", query):
        return True
    for cls in affected:
        local = cls.rsplit("#", 1)[-1]
        # Matches both a prefixed name (spectra:Tdoc) and a full IRI (<...#Tdoc>).
        if re.search(r"[#:]%s\b" % re.escape(local), query):
            return True
    return False


def evaluate_cq(cq: str, gold: dict | None, sparql_q: str, session, g,
                args) -> dict:
    """Run one CQ on both engines and compare, from cardinality up to ordered rows."""
    t1 = time.time()
    entry: dict = {"id": cq}
    cypher_q = gold["cypher"] if gold else None
    if cypher_q is None:
        entry["error"] = "no cypher reference in gold"
        return entry

    cy_nolimit, cy_limit = strip_trailing_limit(cypher_q)
    sp_nolimit, sp_limit = strip_trailing_limit(sparql_q)
    cy_nested_limit = trailing_limit_is_nested(cypher_q)
    sp_nested_limit = trailing_limit_is_nested(sparql_q)
    entry["cypher_limit"] = cy_limit
    entry["sparql_limit"] = sp_limit
    entry["limit_symmetry"] = (
        "both" if cy_limit is not None and sp_limit is not None else
        "cypher_only" if cy_limit is not None else
        "sparql_only" if sp_limit is not None else "none")
    entry["cypher_has_order_by"] = bool(re.search(r"\bORDER\s+BY\b", cypher_q, re.I))
    entry["sparql_has_order_by"] = bool(re.search(r"\bORDER\s+BY\b", sparql_q, re.I))

    try:
        cy_keys, cy_rows_raw = run_cypher(session, cypher_q, args.timeout)
        sp_vars, sp_rows_raw = run_sparql(g, sparql_q, args.timeout)
    except QueryTimeout:
        entry["error"] = f"timeout>{args.timeout}s"
        return entry
    except Exception as e:  # noqa: BLE001
        entry["error"] = f"{type(e).__name__}: {e}"[:250]
        return entry

    # ---- N0 projection alignment ------------------------------------------
    declared_vars = sparql_select_vars(sparql_q)
    entry["projection"] = align_projection(cy_keys, declared_vars or sp_vars or None)
    # Use the executed variable order (rdflib preserves SELECT order).
    ncol = min(len(cy_keys), len(sp_vars))
    entry["projection"]["compared_columns"] = ncol
    entry["projection"]["executed_sparql_vars"] = sp_vars

    # ---- N1 + N2 (+N3 inside) cell normalization --------------------------
    uri_log: list = []
    cy_rows = [[norm_scalar(v) for v in r[:ncol]] for r in cy_rows_raw]
    sp_rows = [[norm_scalar(v, uri_log=uri_log) for v in r[:ncol]] for r in sp_rows_raw]
    # N2 injectivity guard: distinct IRIs must not collapse to one id.
    back: dict[str, set[str]] = collections.defaultdict(set)
    for u, ident in uri_log:
        back[ident].add(u)
    entry["n2_iri_localnames"] = len(uri_log)
    entry["n2_iri_collisions"] = {k: sorted(v) for k, v in back.items() if len(v) > 1}

    cy_t = [tuple(r) for r in cy_rows]
    sp_t = [tuple(r) for r in sp_rows]

    ordered = entry["cypher_has_order_by"] and entry["sparql_has_order_by"]
    entry["L2_topk"] = compare_rows(cy_t, sp_t, ordered=ordered)
    entry["L0_cardinality_equal"] = (len(cy_t) == len(sp_t))

    # ---- L1 relation equivalence (LIMIT removed from both sides) ----------
    nc_pair = (cy_t, sp_t, ordered)
    if args.skip_unbounded or (cy_limit is None and sp_limit is None):
        entry["L1_relation"] = dict(entry["L2_topk"])
        entry["L1_relation"]["source"] = "same as L2 (no trailing LIMIT)"
    elif cy_nested_limit != sp_nested_limit:
        # One side's truncation is inside a subquery and cannot be removed,
        # so a full relation would be compared against a truncated one.
        entry["L1_relation"] = {
            "verdict": "not_comparable_asymmetric_limit",
            "failure_class": "normalization_gap_limit_asymmetry",
            "cypher_limit_nested": cy_nested_limit,
            "sparql_limit_nested": sp_nested_limit}
    else:
        try:
            _, cyu = run_cypher(session, cy_nolimit, args.timeout)
            _, spu = run_sparql(g, sp_nolimit, args.timeout)
            cyu_t = [tuple(norm_scalar(v) for v in r[:ncol]) for r in cyu]
            spu_t = [tuple(norm_scalar(v) for v in r[:ncol]) for r in spu]
            entry["L1_relation"] = compare_rows(cyu_t, spu_t, ordered=False)
            entry["L1_relation"]["source"] = "trailing LIMIT stripped from both"
            entry["limit_binding"] = (cy_limit is not None
                                      and len(cyu_t) > (cy_limit or 0))
            nc_pair = (cyu_t, spu_t, False)
        except QueryTimeout:
            entry["L1_relation"] = {"verdict": "timeout"}
        except Exception as e:  # noqa: BLE001
            entry["L1_relation"] = {"verdict": f"error: {type(e).__name__}"}

    # ---- frozen-gold cross-check (released-artifact reproducibility) ------
    if gold and gold.get("rows") is not None:
        gcols = gold.get("columns", cy_keys)
        gt = [tuple(norm_scalar(r.get(k), gold_str_mode=True) for k in gcols[:ncol])
              for r in gold["rows"]]
        entry["gold_vs_sparql"] = compare_rows(gt, sp_t, ordered=ordered)
        entry["gold_vs_live_cypher"] = compare_rows(gt, cy_t, ordered=ordered)

    # ---- negative controls -------------------------------------------------
    # Run against the relation-level pair, which carries the substantive claim,
    # and score only where that comparison passes.
    if not args.no_negative_controls:
        nc_cy, nc_sp, nc_ord = nc_pair
        base = entry["L1_relation"]
        base_eq = bool(base.get("ordered_equal") if nc_ord
                       else base.get("multiset_equal"))
        entry["negative_controls"] = negative_controls(
            nc_cy, nc_sp, ordered=nc_ord, baseline_equal=base_eq)

    entry["elapsed_s"] = round(time.time() - t1, 1)
    return entry


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ttl", default=os.path.join(PKG, "kg/per_wg/RAN1-body.ttl"))
    ap.add_argument("--sparql-dir", default=os.path.join(PKG, "cqs/spectra_cq_v2.0/sparql"))
    ap.add_argument("--gold", default=os.path.join(PKG, "cqs/spectra_cq_v2.0/gold/RAN1_gold.json"))
    ap.add_argument("--benchmark", default=os.path.join(PKG, "cqs/spectra_cq_v2.0/benchmark.jsonl"))
    ap.add_argument("--bolt", default="bolt://localhost:7687")
    ap.add_argument("--user", default="neo4j")
    ap.add_argument("--password", default="password123")
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "results/analysis/sparql_row_equivalence.json"))
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--only", default=None)
    ap.add_argument("--schema", default=os.path.join(PKG, "ontology/spectra.ttl"),
                    help="ontology supplying the rdfs:subClassOf axioms (read-only)")
    ap.add_argument("--skip-unbounded", action="store_true")
    ap.add_argument("--no-entailment-pass", action="store_true")
    ap.add_argument("--no-negative-controls", action="store_true")
    ap.add_argument("--classify-untranslated-only", action="store_true")
    args = ap.parse_args()

    untranslated = classify_untranslated(args.benchmark)
    if args.classify_untranslated_only:
        print(json.dumps({k: v for k, v in untranslated.items()
                          if k != "novel_construct_examples"}, indent=1))
        return

    signal.signal(signal.SIGALRM, _alarm)

    gold_entries = json.load(open(args.gold))["gold"]
    GOLD = {"P%s_%s" % (e["phase"], e["id"]): e for e in gold_entries}

    cq_ids = sorted(os.path.splitext(os.path.basename(p))[0]
                    for p in glob.glob(os.path.join(args.sparql_dir, "*.rq")))
    if args.only:
        want = set(args.only.split(","))
        cq_ids = [c for c in cq_ids if c in want]

    from rdflib import Graph
    from neo4j import GraphDatabase

    t0 = time.time()
    g = Graph()
    g.parse(args.ttl, format="turtle")
    load_s = time.time() - t0
    print(f"[ttl] {len(g):,} triples in {load_s:.0f}s", flush=True)

    driver = GraphDatabase.driver(args.bolt, auth=(args.user, args.password))
    results: list[dict] = []
    results_rdfs: list[dict] = []
    entail: dict = {}
    queries = {cq: open(os.path.join(args.sparql_dir, cq + ".rq")).read()
               for cq in cq_ids}

    def show(tag: str, e: dict) -> None:
        print(f"[{tag}] {e['id']}: L1={(e.get('L1_relation') or {}).get('verdict')} "
              f"L2={(e.get('L2_topk') or {}).get('verdict')} "
              f"({e.get('elapsed_s')}s){' ' + e['error'] if 'error' in e else ''}",
              flush=True)

    closure = subclass_closure(args.schema)
    hierarchy = sorted(set(closure) | {c for v in closure.values() for c in v})

    with driver.session() as session:
        # Do the two stores agree on how much of the subclass chain is materialized?
        # This decides whether an entailment regime can matter at all, and it has to
        # be read off the parsed graph rather than the Turtle text.
        extent = {
            "classes_in_hierarchy": [c.rsplit("#", 1)[-1] for c in hierarchy],
            "rdf_asserted": type_census(g, hierarchy),
            "neo4j_labels": neo4j_label_census(session, hierarchy),
        }
        extent["agree"] = {k: (extent["rdf_asserted"][k] == extent["neo4j_labels"][k])
                           for k in extent["rdf_asserted"]}

        # ---- pass 1: simple entailment (the released TTL exactly as shipped) ----
        for cq in cq_ids:
            entry = evaluate_cq(cq, GOLD.get(cq), queries[cq], session, g, args)
            results.append(entry)
            show("simple", entry)

        # ---- pass 2: RDFS subclass closure materialized in memory --------------
        # The property graph gives a node every label in its subclass chain, while
        # the body TTL asserts only the most specific class and rdflib infers
        # nothing. Which regime is in force decides whether a superclass pattern in
        # the SPARQL translation can match at all, so both are measured instead of
        # picking whichever scores better.
        if not args.no_entailment_pass:
            affected = set(hierarchy)
            t2 = time.time()
            added = materialize_subclass_types(g, closure)
            entail = {
                "schema": os.path.relpath(args.schema, REPO),
                "subclass_axioms": {k.rsplit("#", 1)[-1]: sorted(
                    x.rsplit("#", 1)[-1] for x in v) for k, v in sorted(closure.items())},
                "type_triples_added": added,
                "triples_after": len(g),
                "materialize_seconds": round(time.time() - t2),
                "rdf_asserted_after_materialization": type_census(g, hierarchy),
            }
            print(f"[rdfs] +{added:,} rdf:type triples "
                  f"({entail['materialize_seconds']}s)", flush=True)
            for cq in cq_ids:
                if not entailment_sensitive(queries[cq], affected):
                    # Only rdf:type triples were added and this query neither
                    # constrains an affected class nor reads a type into a
                    # variable, so its answer cannot have moved.
                    prev = next(e for e in results if e["id"] == cq)
                    clone = dict(prev)
                    clone["unchanged_by_entailment"] = True
                    results_rdfs.append(clone)
                    continue
                entry = evaluate_cq(cq, GOLD.get(cq), queries[cq], session, g, args)
                results_rdfs.append(entry)
                show("rdfs", entry)
            entail["reexecuted"] = sum(1 for e in results_rdfs
                                       if not e.get("unchanged_by_entailment"))
            entail["provably_unchanged"] = sum(1 for e in results_rdfs
                                               if e.get("unchanged_by_entailment"))
    driver.close()

    out = {
        "purpose": ("row-level equivalence between the Cypher reference queries and "
                    "their SPARQL translations for the RAN1 SpectraCQ subset"),
        "normalization_ladder": {
            "N0_projection_alignment": (
                "Equates a Cypher output column label with a SPARQL result variable "
                "name so rows can be tupled in a common order. Mapping is positional "
                "(RETURN order <-> SELECT order); local-name agreement is recorded as "
                "an independent cross-check. Equates names only, never values."),
            "N1_datatype": (
                "Equates encodings of the same value across the two type systems: "
                "integer 5 / double 5.0, typed vs plain numeric literal, xsd:date vs "
                "dateTime with the same date, language-tagged vs plain literal with the "
                "same lexical form, Cypher NULL vs SPARQL unbound. Does not fold case, "
                "trim interior whitespace, or round."),
            "N2_iri_identifier": (
                "Equates an entity IRI in the spectra namespace with the identifier "
                "literal that forms its IRI local part, after stripping a leading "
                "`ClassName_` minting prefix. Guarded by an injectivity check: two "
                "distinct IRIs collapsing to one identifier is reported, not accepted."),
            "N3_aggregate_list": (
                "Equates a Cypher collect() list with a SPARQL GROUP_CONCAT string "
                "split on its declared separator, compared as multisets because "
                "collect() has no defined element order."),
            "N4_row_order": (
                "Equates row order only where the query does not specify one. "
                "Multiplicity is preserved, so duplicate rows are never collapsed."),
        },
        "comparison_levels": {
            "L0_cardinality": "row counts agree (the pre-existing, weak claim)",
            "L1_relation_equivalence": ("trailing LIMIT removed from both queries; full "
                                        "row multisets compared. Immune to tie-break."),
            "L2_topk_ordered": ("queries as written; ordered sequence comparison where "
                                "both sides declare ORDER BY."),
        },
        "engines": {
            "cypher": args.bolt + " (live Neo4j RAN1, read-only)",
            "sparql": os.path.relpath(args.ttl, REPO) + " via rdflib",
            "frozen_reference": os.path.relpath(args.gold, REPO),
        },
        "entailment_regimes": {
            "simple": ("the released body TTL as shipped, loaded into rdflib, which "
                       "performs no inference. This is what a reviewer reproducing "
                       "the artifact gets by default."),
            "rdfs_subclass": ("the same graph plus the superclass rdf:type triples "
                              "entailed by the shipped ontology's rdfs:subClassOf "
                              "axioms, materialized in memory. This is the regime the "
                              "multi-label property graph already represents."),
        },
        "ttl_triples_simple": len(g) - (entail.get("type_triples_added") or 0),
        "ttl_load_seconds": round(load_s),
        "class_extent_agreement": extent,
        "rdfs_entailment": entail,
        "untranslated_classification": untranslated,
        "results": results,
        "results_rdfs_entailment": results_rdfs,
    }
    out["summary"] = summarize(results)
    if results_rdfs:
        out["summary_rdfs_entailment"] = summarize(results_rdfs)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(out, open(args.out, "w"), indent=1, default=str)
    print(json.dumps({k: out[k] for k in
                      ("summary", "summary_rdfs_entailment") if k in out},
                     indent=1, default=str), flush=True)
    print("wrote", args.out, flush=True)


def summarize(results: list[dict]) -> dict:
    def v(e, lvl):
        return (e.get(lvl) or {}).get("verdict")

    n = len(results)
    s: dict = {
        "total": n,
        "errors": [e["id"] for e in results if "error" in e],
        "L0_cardinality_equal": sum(1 for e in results if e.get("L0_cardinality_equal")),
        "L1_relation_equal": sum(1 for e in results
                                 if v(e, "L1_relation") in ("multiset_equal", "ordered_equal")),
        "L1_mismatch": [e["id"] for e in results if v(e, "L1_relation") == "mismatch"],
        "L1_other": {e["id"]: v(e, "L1_relation") for e in results
                     if v(e, "L1_relation") not in
                     ("multiset_equal", "ordered_equal", "mismatch", None)},
        "L2_ordered_equal": sum(1 for e in results if v(e, "L2_topk") == "ordered_equal"),
        "L2_set_equal_order_differs": [e["id"] for e in results
                                       if v(e, "L2_topk") == "set_equal_order_differs"],
        "L2_multiset_equal_no_order_declared": sum(
            1 for e in results if v(e, "L2_topk") == "multiset_equal"),
        "L2_mismatch": [e["id"] for e in results if v(e, "L2_topk") == "mismatch"],
        "L2_arity_mismatch": [e["id"] for e in results if v(e, "L2_topk") == "arity_mismatch"],
        "projection_status": dict(collections.Counter(
            (e.get("projection") or {}).get("status") for e in results)),
        "n2_iri_collision_cqs": [e["id"] for e in results if e.get("n2_iri_collisions")],
        "limit_binding_cqs": sum(1 for e in results if e.get("limit_binding")),
        "gold_vs_sparql_equal": sum(1 for e in results if v(e, "gold_vs_sparql") in
                                    ("multiset_equal", "ordered_equal")),
        "gold_vs_live_cypher_equal": sum(1 for e in results if v(e, "gold_vs_live_cypher") in
                                         ("multiset_equal", "ordered_equal")),
        "normalization_rules_applied": dict(sum(
            (collections.Counter((e.get("L1_relation") or {}).get("rules_applied") or {})
             for e in results), collections.Counter())),
        "limit_symmetry": dict(collections.Counter(
            e.get("limit_symmetry") for e in results)),
    }
    # Failure taxonomy, kept on the axis the reviewer asked for:
    #   untranslated  — no SPARQL file exists at all (counted separately, per-WG)
    #   normalization_gap — the ladder has no equation for the encodings met
    #   result_mismatch   — encodings align, rows disagree
    for lvl in ("L1_relation", "L2_topk"):
        s[lvl + "_failure_classes"] = dict(collections.Counter(
            (e.get(lvl) or {}).get("failure_class") for e in results
            if (e.get(lvl) or {}).get("failure_class")))
    s["L1_failure_detail"] = {
        e["id"]: {"class": (e["L1_relation"]).get("failure_class"),
                  "n_cypher": (e["L1_relation"]).get("n_cypher"),
                  "n_sparql": (e["L1_relation"]).get("n_sparql"),
                  "cols": (e["L1_relation"]).get("mismatching_columns")}
        for e in results
        if (e.get("L1_relation") or {}).get("failure_class")}
    # Rows agree as a relation but the truncated top-k does not: the LIMIT boundary
    # does not determine which of the equally-ranked rows survives (ORDER BY ties, or
    # an engine-specific comparator). Neither engine is wrong; the question is.
    s["topk_under_determined"] = [
        e["id"] for e in results
        if v(e, "L1_relation") in ("multiset_equal", "ordered_equal")
        and v(e, "L2_topk") in ("mismatch", "set_equal_order_differs")]
    # Independent corroboration: the frozen released gold is a separate execution of
    # the same Cypher against a separately loaded database.
    s["gold_vs_live_cypher_mismatch"] = [
        e["id"] for e in results
        if v(e, "gold_vs_live_cypher") not in ("multiset_equal", "ordered_equal", None)]
    # negative controls
    nc: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    undetected: dict[str, list[str]] = collections.defaultdict(list)
    for e in results:
        for k, val in (e.get("negative_controls") or {}).items():
            nc[k][str(val)] += 1
            if val is False and k != "M6_row_count_preserved":
                undetected[k].append(e["id"])
    s["negative_controls"] = {k: dict(c) for k, c in nc.items()}
    s["negative_controls_undetected"] = {k: v for k, v in undetected.items()}
    s["negative_controls_scored_on"] = sum(
        1 for e in results
        if "skipped" not in (e.get("negative_controls") or {"skipped": 1}))
    return s


if __name__ == "__main__":
    main()
