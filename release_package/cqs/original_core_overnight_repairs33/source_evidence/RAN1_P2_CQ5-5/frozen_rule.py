"""Byte-preserved frozen inference definitions; no host/source loader."""
import copy
import re

HEADER = re.compile(
    r"^(?P<adopt>Adopt|Approve|Agree)\b[^\n]*?\bTS\s*(?P<spec>\d{2}\.\d{3})"
    r"\s+V(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)\s*,?\s*"
    r"Clause\s*(?P<clause>\d+(?:\.\d+)*)\b(?P<suffix>[^\n]*)", re.I)

PARAM = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+(?![A-Za-z0-9_-])")

GAP = re.compile(r"^[\s\[\]()]*$")

NAME_HINT = re.compile(r"\bparameter\b.*\b(?:correct\s+name|name\s+(?:is\s+)?correct|renam\w*)\b", re.I | re.S)

def header_of(content):
    match = HEADER.search(content or "")
    if not match:
        return None
    d = match.groupdict()
    d["sectionId"] = f"{d['spec']}-Rel-{d['major']}-{d['clause']}"
    topic = re.search(r"\bregarding\s+(.+?)\s*[.]?\s*$", d["suffix"], re.I)
    d["topic"] = re.sub(r"\s+", " ", topic.group(1)).strip(" .").casefold() if topic else None
    d["header"] = match.group(0)
    return d

def adjacent_pairs(content):
    # Bracketed old names and unbracketed names receive the same operation.
    # An explicit 'or', 'and' or non-whitespace prose prevents adjacency.
    body = (content or "").partition("\n")[2]
    tokens = list(PARAM.finditer(body))
    out = []
    for left, right in zip(tokens, tokens[1:]):
        gap = body[left.end():right.start()]
        if left.group() != right.group() and GAP.fullmatch(gap):
            out.append({"left": left.group(), "right": right.group(),
                        "body_offsets": [left.start(), right.end()], "surface": body[left.start():right.end()]})
    return out

def infer(agreements, sections):
    """One two-stage rule: local same-clause anchor, then exact event/topic sibling.

    The two-stage policy is fixed for all input Agreements. Local anchoring
    requires exactly one member of an adjacent pair to occur in a table
    caption of the header's exact Section and a name-correction hint from a
    CR linked to that exact Section. An unanchored Agreement may use a
    sibling anchor only if meeting, agenda and full literal header topic
    agree, the topic is present, and a unique anchor name occurs in its
    adjacent pair. No inferred replacement is added back to the inputs.
    """
    headers = []
    for a in agreements:
        h = header_of(a["content"])
        if h:
            headers.append({**a, "parsed_header": h, "adjacent_parameter_pairs": adjacent_pairs(a["content"])})
    local = []
    diagnostics = []
    for a in headers:
        sec = sections.get(a["parsed_header"]["sectionId"])
        d = {"node_id": a["node_id"], "resolutionId": a["resolutionId"],
             "parsed_header": a["parsed_header"], "contexts": a["contexts"],
             "adjacent_parameter_pairs": a["adjacent_parameter_pairs"],
             "exact_section": copy.deepcopy(sec), "candidates": []}
        if sec:
            cap_names = {token for t in sec["tables"] for token in PARAM.findall(t.get("tableCaption") or "")}
            hints = [cr for cr in sec["crs"] if NAME_HINT.search(cr.get("reasonForChange") or "")]
            d["caption_parameter_names"] = sorted(cap_names)
            d["name_correction_CR_hints"] = hints
            for pair in a["adjacent_parameter_pairs"]:
                present = [name for name in (pair["left"], pair["right"]) if name in cap_names]
                if len(present) == 1 and hints:
                    new = present[0]
                    old = pair["right"] if new == pair["left"] else pair["left"]
                    candidate = {"old_candidate": old, "new_candidate": new,
                                 "basis": "exact_clause_caption_plus_exact_clause_CR_name_hint",
                                 "pair": pair,
                                 "support_table_nodes": [t["node_id"] for t in sec["tables"] if new in PARAM.findall(t.get("tableCaption") or "")],
                                 "support_CR_nodes": [cr["node_id"] for cr in hints]}
                    d["candidates"].append(candidate)
                    local.append({"node_id": a["node_id"], "resolutionId": a["resolutionId"],
                                  "contexts": a["contexts"], "topic": a["parsed_header"]["topic"], **candidate})
        diagnostics.append(d)
    by_node = {d["node_id"]: d for d in diagnostics}
    propagated = []
    for a in headers:
        if by_node[a["node_id"]]["candidates"] or not a["parsed_header"]["topic"]:
            continue
        support = [b for b in local if b["node_id"] != a["node_id"]
                   and b["topic"] == a["parsed_header"]["topic"]
                   and set(map(tuple, b["contexts"])) & set(map(tuple, a["contexts"]))]
        for pair in a["adjacent_parameter_pairs"]:
            possible = {b["new_candidate"] for b in support if b["new_candidate"] in (pair["left"], pair["right"])}
            if len(possible) == 1:
                new = next(iter(possible))
                old = pair["right"] if new == pair["left"] else pair["left"]
                propagated.append({"node_id": a["node_id"], "resolutionId": a["resolutionId"],
                                   "old_candidate": old, "new_candidate": new, "pair": pair,
                                   "basis": "same_meeting_same_agenda_exact_header_topic_sibling",
                                   "support_agreement_nodes": sorted({b["node_id"] for b in support if b["new_candidate"] == new}),
                                   "topic": a["parsed_header"]["topic"], "contexts": a["contexts"]})
    return {"all_header_matches": diagnostics, "direct_candidates": local, "propagated_candidates": propagated}

def controls(agreements, sections, result):
    # These synthetic controls inspect this rule's dependencies, not any
    # historical source state. All source input objects remain unchanged.
    direct = result["direct_candidates"]
    if not direct:
        raise AssertionError("No direct positive available for controls")
    anchor = direct[0]
    anchor_a = next(a for a in agreements if a["node_id"] == anchor["node_id"])
    section_id = header_of(anchor_a["content"])["sectionId"]
    output = []

    def check(name, a, sec, predicate, expectation):
        got = infer(a, sec)
        ok = predicate(got)
        output.append({"name": name, "expected": expectation, "passed": ok,
                       "direct_occurrences": len(got["direct_candidates"]),
                       "propagated_occurrences": len(got["propagated_candidates"])})
        assert ok, name

    # Positive: no parameter name is hardcoded in the algorithm.
    replacement = "synthetic-CanonicalParameter"
    a2 = copy.deepcopy(agreements)
    s2 = copy.deepcopy(sections)
    actual = anchor["new_candidate"]
    for a in a2:
        a["content"] = a["content"].replace(actual, replacement)
    for sec in s2.values():
        for table in sec["tables"]:
            table["tableCaption"] = (table.get("tableCaption") or "").replace(actual, replacement)
    check("parameter_renaming_equivariance", a2, s2,
          lambda x: any(c["new_candidate"] == replacement for c in x["direct_candidates"]), "a synthetic renamed canonical parameter is inferred from renamed frozen inputs")
    s2 = copy.deepcopy(sections)
    s2[section_id]["crs"] = []
    check("no_exact_clause_CR_hint_no_direct_replacement", agreements, s2,
          lambda x: not any(c["node_id"] == anchor["node_id"] for c in x["direct_candidates"]), "anchor candidate is withheld")
    s2 = copy.deepcopy(sections)
    s2[section_id]["tables"] = []
    check("no_exact_clause_caption_no_direct_replacement", agreements, s2,
          lambda x: not any(c["node_id"] == anchor["node_id"] for c in x["direct_candidates"]), "anchor candidate is withheld")
    s2 = copy.deepcopy(sections)
    moved = s2.pop(section_id)
    s2[section_id + ".999"] = moved
    check("other_clause_is_not_an_exact_clause_anchor", agreements, s2,
          lambda x: not any(c["node_id"] == anchor["node_id"] for c in x["direct_candidates"]), "anchor candidate is withheld")
    a2 = copy.deepcopy(agreements)
    for a in a2:
        if a["node_id"] == anchor["node_id"]:
            a["content"] = re.sub(r"^Adopt", "Discuss", a["content"])
    check("non_adopted_header_is_not_an_anchor", a2, sections,
          lambda x: not any(c["node_id"] == anchor["node_id"] for c in x["direct_candidates"]), "anchor candidate is withheld")
    if result["propagated_candidates"]:
        target = result["propagated_candidates"][0]["node_id"]
        a2 = copy.deepcopy(agreements)
        for a in a2:
            if a["node_id"] == target:
                a["contexts"] = [["synthetic-other-meeting", "synthetic-other-agenda"]]
        check("other_event_does_not_inherit_sibling_caption", a2, sections,
              lambda x: not any(c["node_id"] == target for c in x["propagated_candidates"]), "propagated candidate is withheld")
        a2 = copy.deepcopy(agreements)
        for a in a2:
            if a["node_id"] == target:
                a["content"] = re.sub(r"\bregarding\s+[^\n]+", "regarding synthetic different topic.", a["content"], count=1)
        check("different_literal_topic_does_not_inherit_sibling_caption", a2, sections,
              lambda x: not any(c["node_id"] == target for c in x["propagated_candidates"]), "propagated candidate is withheld")
    return output
