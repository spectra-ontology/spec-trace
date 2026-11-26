#!/usr/bin/env python3
"""Replay the finite Codex source-inspection comparison and packet bindings."""
import argparse
import collections
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import zipfile
from xml.etree import ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    release = args.release.resolve()
    base = release / "studies/disposition_reading"
    spec = importlib.util.spec_from_file_location("reading_replay", base / "replay.py")
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)
    replay.manifests(base)
    finite = base / "finite_identity"
    protocol = replay.json_file(finite / "protocol.json")
    readings = replay.json_lines(finite / "readings.jsonl")
    comparison = replay.json_file(finite / "comparison.json")
    freeze = replay.json_file(finite / "reading_freeze.json")
    prepared = replay.json_lines(finite / "packets.jsonl")
    replay.require(replay.sha((finite / "protocol.json").read_bytes()) == freeze["protocolSha256"], "finite protocol freeze hash differs")
    replay.require(replay.sha((finite / "readings.jsonl").read_bytes()) == freeze["readingFileSha256"], "finite reading freeze hash differs")
    replay.require(freeze["actuallyReadCases"] == len(readings) and freeze["readingsSavedBeforeHistoricalLabelJoin"] is True,
                   "finite reading-freeze declaration differs")
    by_id = replay.index(readings, "dispositionId")
    packets = replay.index(prepared, "dispositionId")
    trace_path = release / protocol["cohort"]["tracePath"]
    replay.require(replay.sha(trace_path.read_bytes()) == protocol["cohort"]["traceSha256"], "finite cohort trace hash differs")
    trace = replay.index(replay.json_lines(trace_path), "dispositionId")
    replay.require(set(by_id) == set(packets) == set(trace) == set(protocol["cohort"]["dispositionIds"]), "finite cohort differs")
    replay.require(len(by_id) == 233, "finite cohort count differs")
    records = {}
    for wg in ("RAN1", "RAN2"):
        path = release / f"records/phase-2/{wg}/decision_dispositions.jsonld"
        if not path.exists():
            path = path.with_suffix(path.suffix + ".gz")
        for row in replay.stream_dispositions(path):
            if row["dispositionId"] in by_id:
                records[row["dispositionId"]] = row
    joins = []
    for reading in readings:
        ident = reading["dispositionId"]
        old, cohort, packet = records[ident], trace[ident], packets[ident]
        scope = json.loads(old.get("assessmentMethod") or "{}").get("scope")
        replay.require(reading["packetSha256"] == packet["packetSha256"], "finite reading/packet digest differs")
        replay.require(reading["report"]["path"] == cohort["evidencePath"] and reading["report"]["sha256"] == cohort["evidenceSha256"]
                       and reading["report"]["locator"] == cohort["evidenceLocator"], "finite report binding differs")
        expected_target = {(row["path"], row["sha256"]) for row in cohort["identityReview"]["actualDocumentEvidence"]}
        replay.require({(row["path"], row["sha256"]) for row in reading["targetDocuments"]} == expected_target, "finite target binding differs")
        joins.append({"caseId": reading["caseId"], "dispositionId": ident, "freshCode": reading["codeJudgment"],
                      "recordCode": old["dispositionCode"], "codeMatched": reading["codeJudgment"] == old["dispositionCode"],
                      "freshScope": reading["scopeJudgment"], "recordScope": scope, "scopeMatched": reading["scopeJudgment"] == scope,
                      "freshIdentity": reading["identityJudgment"], "oldIdentityStatus": cohort["identityReview"]["identityStatus"],
                      "goldEvidenceReferences": cohort["goldEvidenceReferences"]})
    replay.compare(joins, comparison["comparison"], "finite.comparison")
    result = {"status": "PASS", "reviewer": comparison["reviewer"], "caseReadings": len(readings),
              "sourceIdentitySupported": sum(row["identityJudgment"] == "same_document_supported" for row in readings),
              "codeMatches": sum(row["codeMatched"] for row in joins), "scopeMatches": sum(row["scopeMatched"] for row in joins),
              "freshCodes": dict(collections.Counter(row["codeJudgment"] for row in readings)),
              "observationsPreserved": sum(row["observation"] is not None for row in readings),
              "evidenceUses": sum(len(row["goldEvidenceReferences"]) for row in joins),
              "affectedItems": len({ref["itemId"] for row in joins for ref in row["goldEvidenceReferences"]}),
              "sourcePacketReconstruction": "Use --source-root for local source reconstruction"}
    if args.source_root:
        word = replay.load_word_reader(release / "code", replay.json_file(base / "provenance.json"))
        import document_decision_source as source_tables

        def source_blocks(path, expected):
            data = path.read_bytes()
            replay.require(replay.sha(data) == expected, f"finite source hash differs: {path}")
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                archive.filename = str(path)
                tree = ET.fromstring(word.zip_part(archive, "word/document.xml"))
            body = tree.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body")
            blocks = list(word.iter_blocks(body))
            texts = [("\n".join(word.table_line_rows(block, para=word.final_text)) if word.is_table(block)
                      else word.final_text(block)) for block in blocks]
            return texts, blocks

        grouped = collections.defaultdict(list)
        for packet in prepared:
            grouped[packet["report"]["path"]].append(packet)
        restored = []
        source_root = args.source_root.resolve()
        target_paths = set()
        for relative, group in sorted(grouped.items()):
            path = (source_root / relative).resolve()
            path.relative_to(source_root)
            report_sha = group[0]["report"]["sha256"]
            texts, blocks = source_blocks(path, report_sha)
            wg = group[0]["dispositionId"].split(":", 1)[0]
            tables = source_tables._annex_source_tables(path, report_sha, texts, blocks, wg)
            for packet in group:
                table_index, row_index = map(int, re.search(r"accepted table block (\d+) row (\d+)", packet["report"]["locator"]).groups())
                table = tables[table_index]
                report = {"path": relative, "sha256": report_sha, "locator": packet["report"]["locator"],
                          "governingContext": table["governingContext"], "headerCells": table["headerCells"], "targetRowCells": table["rows"][row_index]}
                targets = []
                for target in packet["targetIdentityExcerpts"]:
                    target_path = (source_root / target["path"]).resolve()
                    target_path.relative_to(source_root)
                    target_texts, _ = source_blocks(target_path, target["sha256"])
                    targets.append({"path": target["path"], "sha256": target["sha256"],
                                    "blocks": [{"block": block["block"], "text": target_texts[block["block"]]} for block in target["blocks"]]})
                    target_paths.add(target["path"])
                actual = {"caseId": packet["caseId"], "dispositionId": packet["dispositionId"], "target": packet["target"],
                          "report": report, "targetIdentityExcerpts": targets}
                replay.require(replay.sha(replay.canonical(actual)) == packet["packetSha256"], "finite original packet differs: " + packet["caseId"])
                restored.append(actual)
        original_bytes = "".join(json.dumps(packet, ensure_ascii=False) + "\n" for packet in restored).encode("utf-8")
        replay.require(replay.sha(original_bytes) == freeze["sourcePacketFileSha256"], "finite source-packet file freeze hash differs")
        result["sourcePacketReconstruction"] = {"reports": len(grouped), "targetDocuments": len(target_paths),
                                                 "exactPacketDigestsMatched": len(restored),
                                                 "originalSourcePacketFileSha256Matched": True}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
