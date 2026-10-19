#!/usr/bin/env python3
"""Verify compact original-source witnesses and three refusal controls.

Default mode is portable: it checks only included bytes, identities and policies.
Optional --source-root also reopens the pinned original archives/full XML; the
legacy TR38.802 XML is a declared prior actual DOC conversion, not a new one.
This verifier does not infer complete gold, source-topic absence, normative
incorporation or human approval, and it never calls an API or database service.
"""
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def paragraph_text(p, rule):
    if rule == "w_t_only":
        return "".join(x.text or "" for x in p.iter(W + "t"))
    assert rule == "w_t_tabs_and_breaks"
    return "".join(x.text or "" if x.tag == W + "t" else "\t" if x.tag == W + "tab" else "\n" if x.tag in {W + "br", W + "cr"} else "" for x in p.iter())


def style(p):
    value = p.find(W + "pPr/" + W + "pStyle")
    return None if value is None else value.get(W + "val")


def local_path(base, relative):
    p = (base / relative).resolve()
    assert p.is_relative_to(base.resolve()), "path escaped bundle/source root"
    return p


def verify_file(pin, base):
    b = local_path(base, pin["path"]).read_bytes()
    assert len(b) == pin["bytes"] and sha(b) == pin["sha256"], "file bytes/hash mismatch"
    return b


def verify_record(row, anchor):
    assert sha(row["original_question"].encode()) == row["original_question_sha256"] == anchor["original_question_sha256"], "wrong original question SHA"
    assert sha(row["original_query"].encode()) == row["original_query_sha256"] == anchor["original_query_sha256"], "wrong original query SHA"
    source = row["source"]
    assert source["archive"]["sha256"] == anchor["archive_sha256"], "wrong original source identity"
    for field in ["member_name", "member_sha256", "full_document_XML_sha256"]:
        assert source[field] == anchor[field], "wrong original source member/XML identity"
    required = anchor["required_paragraph_indices"]
    assert [p["all_w_p_index0"] for p in row["witnesses"]] == required, "missing required title/agenda witness"
    for witness in row["witnesses"]:
        raw = verify_file(witness["XML"], HERE)
        p = ET.fromstring(raw)
        assert p.tag == W + "p", "non-paragraph witness"
        expected = anchor["required_literal_witnesses"][str(witness["all_w_p_index0"])]
        assert paragraph_text(p, witness["text_rule"]) == witness["literal_text"] == expected, "required title/agenda literal mismatch"
        assert style(p) == witness["style"], "paragraph style mismatch"
    assert row["proposed_clarification_type"] == "conflicting_entity_description"
    assert row["classification_is_conditional"] is True and row["condition"]
    assert row["ID_first_truthful_answer_counterinterpretation"] and row["separate_answer_evidence_pending"]
    assert row["description_not_topic_absence"]
    assert row["original_question_unchanged"] and row["original_query_unchanged"]
    assert row["admission"] is False and row["new_answer_gold"] is False
    assert row["expert_validation_n"] == row["model_API_calls"] == 0


def verify_actual_original(row, root):
    source = row["source"]
    archive = verify_file(source["archive"], root)
    with ZipFile(io.BytesIO(archive)) as z:
        member = z.read(source["member_name"])
    assert sha(member) == source["member_sha256"]
    legacy = source["source_root_relative_XML_if_legacy"]
    if legacy is None:
        with ZipFile(io.BytesIO(member)) as z:
            raw = z.read("word/document.xml")
    else:
        assert source["transformation"]["new_conversion_in_this_audit"] is False
        raw = verify_file(source["transformation"]["retained_derivative_XML"], root)
    assert sha(raw) == source["full_document_XML_sha256"]
    paragraphs = list(ET.fromstring(raw).iter(W + "p"))
    assert len(paragraphs) == source["all_w_p_n"]
    for witness in row["witnesses"]:
        p = paragraphs[witness["all_w_p_index0"]]
        assert paragraph_text(p, witness["text_rule"]) == witness["literal_text"]
        assert style(p) == witness["style"]
    return {"id": row["id"], "archive_sha256_verified": source["archive"]["sha256"], "member_sha256_verified": sha(member),
            "full_document_XML_sha256_verified": sha(raw), "selected_paragraphs_rechecked_n": len(row["witnesses"]),
            "legacy_prior_conversion": legacy is not None}


def controls(rows, anchors):
    tests = []
    for kind in ["wrong_original_question_SHA", "wrong_source_identity", "missing_required_title"]:
        row = copy.deepcopy(next(r for r in rows if r["id"] == "RAN1_P5_CQ5-1"))
        if kind == "wrong_original_question_SHA":
            row["original_question_sha256"] = "0" * 64
        elif kind == "wrong_source_identity":
            row["source"]["archive"]["sha256"] = next(r for r in rows if r["id"] != row["id"])["source"]["archive"]["sha256"]
        else:
            row["witnesses"] = [p for p in row["witnesses"] if p["all_w_p_index0"] != 5]
        try:
            verify_record(row, anchors[row["id"]])
        except AssertionError as ex:
            tests.append({"control": kind, "result": "REJECTED", "reason": str(ex)})
        else:
            raise AssertionError("negative control incorrectly accepted: " + kind)
    return tests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    args = parser.parse_args()
    manifest = json.loads((HERE / "manifest.json").read_text())
    assert manifest["cases_n"] == 3 and manifest["admitted_n"] == 0
    for pin in manifest["files"]:
        verify_file(pin, HERE)
    anchors = json.loads((HERE / "anchors.json").read_text())
    rows = [json.loads(line) for line in (HERE / "cases.jsonl").read_text().splitlines()]
    assert len(rows) == len(anchors) == 3 and {r["id"] for r in rows} == set(anchors)
    for row in rows:
        verify_record(row, anchors[row["id"]])
    reviews = [json.loads((HERE / "reviews" / ("primary_" + str(i) + ".json")).read_text()) for i in [1, 2]]
    first, fourth = reviews
    assert isinstance(first, list) and len(first) == 2 and isinstance(fourth, dict)
    assert {r["id"] for r in first + [fourth]} == set(anchors)
    assert all(len(r["semantic_evidence"]) == 7 and r["expert_validation_n"] == 0 for r in first + [fourth])
    provenance = json.loads((HERE / "provenance.json").read_text())
    secondary_provenance = provenance["root_secondary_review"]
    secondary_path = secondary_provenance["reserved_relative_path"]
    secondary_bytes = local_path(HERE, secondary_path).read_bytes()
    assert sha(secondary_bytes) == secondary_provenance["sha256"]
    secondary = json.loads(secondary_bytes)
    assert len(secondary) == 3 and {r["id"] for r in secondary} == set(anchors)
    required_units = {"requested answer roles and fields", "population and source context", "filters and relationship meaning",
                      "counting unit and join multiplicity", "cardinality and completeness", "ordering and ties when requested",
                      "unverified additional inputs or external interpretation"}
    row_by_id = {r["id"]: r for r in rows}
    for review in secondary:
        original = row_by_id[review["id"]]
        assert review["original_question"] == original["original_question"]
        assert review["original_question_sha256"] == original["original_question_sha256"]
        assert review["original_query_sha256"] == original["original_query_sha256"]
        assert len(review["semantic_evidence"]) == 7 and {r["unit"] for r in review["semantic_evidence"]} == required_units
        assert all(r["answer_contract_status"] == "pending" for r in review["semantic_evidence"])
        assert review["classification_is_conditional"] is True and review["condition"]
        assert review["proposed_disposition"] == "clarification_required"
        assert review["proposed_clarification_type"] == "conflicting_entity_description"
        assert review["admission"] is False and review["new_answer_gold"] is False
        assert review["expert_validation_n"] == review["model_API_calls"] == 0
        assert review["human_author_review_completed"] is False
    actual = []
    if args.source_root:
        actual = [verify_actual_original(row, args.source_root.resolve()) for row in rows]
    reserved = provenance["root_secondary_review"]["reserved_relative_path"]
    result = {"status": "PASS", "mode": "actual_original_archives_and_portable_witnesses" if args.source_root else "portable_included_evidence_only",
              "manifest_files_verified_n": len(manifest["files"]), "cases_verified_n": len(rows),
              "exact_paragraph_witnesses_n": sum(len(r["witnesses"]) for r in rows), "primary_reviews_n": 3,
              "root_secondary_seven_unit_reviews_verified_n": len(secondary),
              "negative_controls": controls(rows, anchors), "actual_original_source_replay": actual,
              "root_secondary_review_attached": (HERE / reserved).is_file(), "classification_changed_n": 0,
              "admitted_n": 0, "expert_validation_n": 0, "model_API_calls": 0, "native_calls": 0}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
