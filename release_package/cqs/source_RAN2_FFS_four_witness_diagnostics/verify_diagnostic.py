#!/usr/bin/env python3
"""Offline four-witness diagnostic; zero admission and no graph/API execution."""
import collections
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as E
import zipfile

sys.dont_write_bytecode = True
INVENTORY_SHA256 = "4ade86a4ad1a940353a5759eb75e4177e298e7b7f7d8915f1651674a82cd78ed"
META = {"README.md", "manifest.json", "verify_diagnostic.py", "immutable_inventory.json"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
FORMAT = ("strike", "dstrike", "vanish", "webHidden")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def no_symlinks(path):
    path = Path(path).absolute()
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise ValueError("Symlink entry or ancestor rejected")
    return path


def read_json(path):
    return json.loads(path.read_text())


def norm(value):
    return re.sub(r"\s+", " ", value or "").strip()


def raw_text(element):
    # Final ordinary Word text only. No equation/drawing rendering claim.
    if element.tag in {W + 'del', W + 'moveFrom', W + 'drawing', W + 'pict', W + 'object'}:
        return ''
    if element.tag == W + 't':
        return element.text or ''
    if element.tag == W + 'tab':
        return '\t'
    if element.tag in {W + 'br', W + 'cr'}:
        return '\n'
    return ''.join(raw_text(child) for child in element)

def iter_blocks(container):
    for child in container:
        if child.tag in {W + 'p', W + 'tbl'}:
            yield child
        elif child.tag in {W + 'sdt', W + 'sdtContent', W + 'customXml'}:
            yield from iter_blocks(child)

def paragraphs(root):
    out = []

    def visit(container, coordinate):
        for bi, block in enumerate(iter_blocks(container)):
            here = f'{coordinate}/b{bi}'
            if block.tag == W + 'p':
                out.append({'coordinate': here, 'text': raw_text(block), 'element': block})
            else:
                for ri, row in enumerate(block.findall(W + 'tr')):
                    for ci, cell in enumerate(row.findall(W + 'tc')):
                        visit(cell, f'{here}/r{ri}/c{ci}')
    body = root.find(W + 'body')
    assert body is not None
    visit(body, 'body')
    return out

def onoff(node):
    return node is not None and node.get(W + "val", "true").lower() not in ("0", "false", "off")

def props(node):
    return {key: (None if node is None or node.find(W + key) is None else onoff(node.find(W + key))) for key in FORMAT}

def effective_format(paragraph, run, styles, defaults):
    state = {key: bool(defaults[key]) for key in FORMAT}
    chains, unknown = [], []
    ps = paragraph.find(f"{W}pPr/{W}pStyle")
    rs = run.find(f"{W}rPr/{W}rStyle")
    for style_id in [ps.get(W + "val") if ps is not None else "Normal", rs.get(W + "val") if rs is not None else None]:
        chain, seen = [], set()
        while style_id:
            assert style_id not in seen
            seen.add(style_id)
            style = styles.get(style_id)
            if style is None:
                unknown.append(style_id)
                break
            chain.append(style)
            based = style.find(W + "basedOn")
            style_id = based.get(W + "val") if based is not None else None
        for style in reversed(chain):
            values = props(style.find(W + "rPr"))
            chains.append({"id": style.get(W + "styleId"), "values": values})
            for key, value in values.items():
                if value:
                    state[key] = not state[key]
    direct = props(run.find(W + "rPr"))
    for key, value in direct.items():
        if value is not None:
            state[key] = value
    return {"effective": state, "style_chain": chains, "direct": direct, "unknown_styles": unknown}

def occurrences(paragraph, styles, defaults):
    parent = {child: node for node in paragraph.iter() for child in node}
    segments, chunks, cursor = [], [], 0
    for run in paragraph.iter(W + "r"):
        value = "".join((n.text or "") if n.tag in (W + "t", W + "delText") else ("\t" if n.tag == W + "tab" else "\n") for n in run.iter() if n.tag in (W + "t", W + "delText", W + "tab", W + "br", W + "cr"))
        segments.append((cursor, cursor + len(value), run))
        chunks.append(value)
        cursor += len(value)
    raw = "".join(chunks)
    result = []
    for match in re.finditer("FFS", raw):
        evidence, statuses = [], []
        for start, end, run in segments:
            if end <= match.start() or start >= match.end():
                continue
            ancestors, node = [], run
            while node in parent:
                node = parent[node]
                ancestors.append(node.tag)
            excluded = any(W + tag in ancestors for tag in ("del", "moveFrom", "drawing", "pict", "object"))
            fmt = effective_format(paragraph, run, styles, defaults)
            active = not excluded and not any(fmt["effective"].values()) and not fmt["unknown_styles"]
            statuses.append(active)
            evidence.append({"deleted_or_excluded_object": excluded, **fmt, "run_xml": E.tostring(run, encoding="unicode")})
        result.append({"raw_offset": match.start(), "all_marker_characters_active": bool(statuses) and all(statuses), "some_marker_characters_active": any(statuses), "run_evidence": evidence})
    return raw, result

def physical_paths(root):
    result = {id(root): "document"}
    def visit(parent):
        counts = collections.Counter()
        for child in parent:
            local = child.tag.rsplit("}", 1)[-1]
            counts[local] += 1
            result[id(child)] = result[id(parent)] + "/" + local + "[" + str(counts[local]) + "]"
            visit(child)
    visit(root)
    return result


def all_text_runs_active(paragraph, styles, defaults):
    parent = {child: node for node in paragraph.iter() for child in node}
    count = 0
    for run in paragraph.iter(W + "r"):
        value = "".join(node.text or "" for node in run.iter() if node.tag in {W + "t", W + "delText"})
        if not value:
            continue
        count += 1
        node = run
        while node in parent:
            node = parent[node]
            assert node.tag not in {W + "del", W + "moveFrom", W + "drawing", W + "pict", W + "object"}
        fmt = effective_format(paragraph, run, styles, defaults)
        assert not fmt["unknown_styles"] and not any(fmt["effective"].values())
    return count > 0


def verify():
    # The lexical entry/ancestor boundary is checked before the first file read.
    root = no_symlinks(Path(__file__).absolute()).parent
    actual_paths = set()
    actual_dirs = set()
    for path in root.rglob("*"):
        no_symlinks(path)
        name = path.relative_to(root).as_posix()
        if path.is_dir():
            actual_dirs.add(name)
        elif path.is_file():
            actual_paths.add(name)
        else:
            raise ValueError("Non-regular payload")
    inventory_path = root / "immutable_inventory.json"
    assert sha(inventory_path.read_bytes()) == INVENTORY_SHA256, "immutable inventory hardpin"
    inventory = read_json(inventory_path)
    assert inventory["schema"] == "spectra-four-source-witnesses-v1"
    expected_paths = set(inventory["files"]) | META
    assert actual_paths == expected_paths, "closed file set"
    expected_dirs = {p.as_posix() for name in expected_paths for p in Path(name).parents if p.as_posix() != "."}
    assert actual_dirs == expected_dirs, "closed directory set"
    for name, pin in inventory["files"].items():
        data = (root / name).read_bytes()
        assert {"bytes": len(data), "sha256": sha(data)} == pin, name
    manifest = read_json(root / "manifest.json")
    assert set(manifest["files"]) == actual_paths - {"manifest.json"}
    for name, pin in manifest["files"].items():
        data = (root / name).read_bytes()
        assert {"bytes": len(data), "sha256": sha(data)} == pin, name
    assert set(manifest) == {"id", "artifact_type", "admitted", "original560_increment", "expert_validation_n", "files"}
    assert manifest["id"] == "RAN2_P2_CQ2-6"
    assert manifest["artifact_type"] == "source_diagnostic_not_an_admission_or_model_cohort"
    assert manifest["admitted"] is False
    assert type(manifest["original560_increment"]) is int and manifest["original560_increment"] == 0
    assert type(manifest["expert_validation_n"]) is int and manifest["expert_validation_n"] == 0
    question = read_json(root / "contract/original_question.json")
    assert question["id"] == "RAN2_P2_CQ2-6"
    assert sha(question["question_en"].encode()) == question["question_sha256"] == "2b736ce55c67dfeab41b9ed482cec8edc47c51415331744a2c5ed4eb73ce3bb6"
    assert sha(question["original_query"].encode()) == question["original_query_sha256"] == "31c7143d5c6c6c77114324fa3794aa1e07bd1a3d9e7273b4f83656d3558c391c"
    assert question["original560_increment"] == 0 and question["admitted"] is False
    evidence = read_json(root / "source/four_witnesses.json")
    locator = evidence["source_locator"]
    archive_bytes = (root / "source/R2-2600002.zip").read_bytes()
    assert sha(archive_bytes) == evidence["archive_sha256"] == locator["original_archive_pin"]["sha256"]
    assert len(archive_bytes) == evidence["archive_bytes"] == locator["original_archive_pin"]["bytes"]
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as outer:
        inventory_actual = []
        for member in outer.infolist():
            if member.is_dir():
                continue
            data = outer.read(member)
            inventory_actual.append({"name": member.filename, "bytes": len(data), "CRC32": f"{member.CRC:08x}", "sha256": sha(data)})
        assert inventory_actual == locator["all_member_inventory"]
        info = outer.getinfo(locator["exact_report_member"]["name"])
        docx = outer.read(info)
    assert len(docx) == locator["exact_report_member"]["bytes"]
    assert sha(docx) == evidence["member_sha256"] == locator["exact_report_member"]["sha256"]
    assert f"{info.CRC:08x}" == evidence["member_info"]["CRC32"]
    with zipfile.ZipFile(io.BytesIO(docx)) as inner:
        xml, styles_xml = inner.read("word/document.xml"), inner.read("word/styles.xml")
    assert sha(xml) == evidence["document_XML_sha256"] == locator["word_document_XML"]["sha256"]
    assert sha(styles_xml) == evidence["styles_XML_sha256"]
    document, styles_root = E.fromstring(xml), E.fromstring(styles_xml)
    ps = paragraphs(document)
    assert len(ps) == locator["protected_body_table_paragraphs_n"]
    paths = physical_paths(document)
    styles = {s.get(W + "styleId"): s for s in styles_root.findall(W + "style")}
    defaults = props(styles_root.find(f"{W}docDefaults/{W}rPrDefault/{W}rPr"))
    frozen_bytes = (root / "frozen/whole_frozen3413_neutral_rank_inputs.jsonl.gz").read_bytes()
    assert sha(frozen_bytes) == evidence["frozen_capture"]["sha256"]
    frozen = [json.loads(line) for line in gzip.decompress(frozen_bytes).splitlines() if line.strip()]
    assert len(frozen) == evidence["frozen_capture"]["rows"] == 3413
    assert len({r["resolutionId"] for r in frozen}) == 3413
    assert all(r["resolutionId"].startswith("AGR-") for r in frozen)
    assert sum(r["meetingNumberInt"] >= 131 for r in frozen) == 147
    assert len(evidence["witnesses"]) == 4
    assert len({w["marker_paragraph_index"] for w in evidence["witnesses"]}) == 4
    xml_neighborhoods_checked = 0
    marker_count = 0
    for witness in evidence["witnesses"]:
        assert witness["meeting"] == "RAN2#132" and witness["aligned_original_resolutionIds"] == []
        start = witness["marker_paragraph_index"]
        assert ps[start]["text"] == witness["own_Agreements_label"]
        assert norm(ps[start]["text"]).startswith("Agreements")
        assert all_text_runs_active(ps[start]["element"], styles, defaults)
        assert witness["heading_all_text_active"] is True
        for paragraph in witness["exact_XML_neighborhood_and_run_formatting"]:
            i = paragraph["paragraph_index"]
            actual = ps[i]
            assert actual["coordinate"] == paragraph["coordinate"]
            assert paths[id(actual["element"])] == paragraph["physical_element_path"]
            assert actual["text"] == paragraph["final_text"]
            assert sha(E.tostring(actual["element"])) == paragraph["paragraph_XML_sha256"]
            assert E.tostring(E.fromstring(paragraph["paragraph_XML"])) == E.tostring(actual["element"])
            value, found = occurrences(actual["element"], styles, defaults)
            assert value == paragraph["raw_text"] and found == paragraph["FFS_occurrences"]
            xml_neighborhoods_checked += 1
        for marker in witness["FFS_source_and_frozen_absence_evidence"]:
            i = marker["paragraph_index"]
            assert start < i < witness["retained_candidate_end_exclusive"]
            query = norm(ps[i]["text"])
            assert query == marker["whole_FFS_paragraph_normalized"] and "FFS" in query
            found = occurrences(ps[i]["element"], styles, defaults)[1]
            assert found and all(x["all_marker_characters_active"] for x in found)
            assert all_text_runs_active(ps[i]["element"], styles, defaults)
            assert not any(query in norm((row["content"] or "") + " " + (row["note"] or "")) for row in frozen)
            assert not any(query.casefold() in norm((row["content"] or "") + " " + (row["note"] or "")).casefold() for row in frozen)
            assert marker["all_frozen3413_content_and_note_whole_paragraph_exact_matches"] == []
            assert marker["all_frozen3413_casefold_whole_paragraph_matches"] == []
            marker_count += len(found)
    assert marker_count == 4
    assert (root / "reviews/root_source_review.json").read_bytes() != (root / "reviews/independent_source_review.json").read_bytes()
    receipt = {"status": "OFFLINE_FOUR_SOURCE_WITNESSES_REPRODUCED_NO_ADMISSION", "source_meeting": "RAN2#132", "confirmed_own_label_marker_witnesses": 4, "active_literal_FFS_occurrences": marker_count, "raw_XML_neighborhood_paragraphs_checked": xml_neighborhoods_checked, "frozen_Agreement_content_and_note_records_searched": 3413, "exact_normalized_and_casefold_whole_sentence_matches": 0, "current_lifecycle_established": False, "complete_source_population_established": False, "original560_increment": 0, "expert_validation_n": 0, "API_calls": 0, "network_calls": 0, "DB_calls": 0, "native_calls": 0, "admitted": False}
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    verify()
