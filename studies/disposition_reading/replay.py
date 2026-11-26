#!/usr/bin/env python3
"""Validate and recompute the archived two-reader disposition study offline.

Python 3.11+ standard library suffices for label/statistic replay. Source-packet
reconstruction additionally uses the release's Word reader and source dependencies.
No model calls or network requests are made.
"""
from __future__ import annotations

import argparse
import ast
import collections
import copy
import functools
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys
import tempfile
import types


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def json_file(path):
    return json.loads(path.read_text(encoding="utf-8"))


def json_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def index(rows, field):
    result = {}
    for row in rows:
        require(row[field] not in result, f"duplicate {field}: {row[field]}")
        result[row[field]] = row
    return result


def manifests(base):
    lines = (base / "SHA256SUMS").read_text().splitlines()
    expected = {}
    for line in lines:
        digest, relative = line.split("  ", 1)
        require(relative not in expected, "duplicate checksum path")
        path = (base / relative).resolve()
        path.relative_to(base.resolve())
        require(path.is_file(), f"missing bundle file: {relative}")
        require(sha(path.read_bytes()) == digest, f"bundle hash mismatch: {relative}")
        expected[relative] = digest
    actual = {str(p.relative_to(base)) for p in base.rglob("*")
              if p.is_file() and p.name != "SHA256SUMS" and "__pycache__" not in p.parts}
    require(actual == set(expected), "bundle checksum coverage differs from file inventory")
    return len(expected)


def stream_dispositions(path):
    opener = gzip.open if path.suffix == ".gz" else open
    buf = None
    with opener(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if line.rstrip("\n") == "    {":
                buf = [line]
            elif buf is not None:
                buf.append(line)
                if line.startswith("    }"):
                    row = json.loads("".join(buf).rstrip().rstrip(","))
                    buf = None
                    if "dispositionId" in row:
                        yield row


def audit_sampling(release, keys, sampling, summary):
    wanted = {row["dispositionId"] for row in keys.values()}
    records, checked, seed = {}, {}, sampling["seed"]
    for wg in ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5"):
        path = release / f"records/phase-2/{wg}/decision_dispositions.jsonld"
        if not path.exists():
            path = path.with_suffix(path.suffix + ".gz")
        candidates = {"source_verified": [], "pending": []}
        counts = collections.Counter()
        for row in stream_dispositions(path):
            status, ident = row.get("evidenceStatus"), row["dispositionId"]
            if status in candidates:
                counts[status] += 1
                tag = "" if status == "source_verified" else "pending|"
                candidates[status].append((sha(f"{seed}|{tag}{ident}".encode()), ident))
            if ident in wanted:
                records[ident] = row
        require(dict(counts) == sampling["populationFromReleasedRecords"][wg] == summary["census"][wg]["population"],
                f"population differs: {wg}")
        chosen = {status: [ident for _, ident in sorted(values)[:200 if status == "source_verified" else 20]]
                  for status, values in candidates.items()}
        require(chosen == sampling["selectedFromReleasedRecords"][wg], f"sample ranks differ: {wg}")
        for status, name in (("source_verified", "random_verified"), ("pending", "random_pending")):
            actual = {r["dispositionId"] for r in keys.values() if r["wg"] == wg and name in r["sets"]}
            require(actual == set(chosen[status]), f"sample membership differs: {wg}/{name}")
        checked[wg] = {"population": dict(counts), "verified": 200, "pending": 20}
    require(set(records) == wanted, "sample records missing from released population")
    reread_path = release / sampling["rereadFile"]
    require(sha(reread_path.read_bytes()) == sampling["rereadFileSha256"], "reread-cohort file hash differs")
    reread = {r["dispositionId"] for g in json_file(reread_path)["workingGroups"] for r in g.get("rows", [])}
    actual = {r["dispositionId"] for r in keys.values() if "reread_differences" in r["sets"]}
    require(reread == set(sampling["rereadDispositionIds"]) == actual, "reread membership differs")
    return records, checked


def audit_rows(keys, packets, readings, records, sources):
    packet_index = index(packets, "packetId")
    require(set(packet_index) == set(keys), "packet/sample ID coverage differs")
    digest = re.compile(r"[0-9a-f]{64}")
    codes = {"agreed", "conditionally_agreed", "partially_agreed", "endorsed", "revised", "merged", "noted",
             "withdrawn", "rejected", "not_agreed", "not_pursued", "not_treated", "postponed", "not_concluded",
             "replied_to", "ambiguous", "cannot_tell"}
    for reader, rows in readings.items():
        table = index(rows, "packetId")
        require(set(table) == set(keys), f"reader {reader} ID coverage differs")
        for row in rows:
            require(set(row) == {"packetId", "code", "scope", "evidenceSha256", "evidenceChars"}, "reader fields differ")
            require(row["code"] in codes and row["scope"] in {"whole_target", "subdocument", "undetermined"}, "reader code/scope invalid")
            require(digest.fullmatch(row["evidenceSha256"]) and row["evidenceChars"] >= 0, "reader evidence digest invalid")
    seed = "m4-source-adjudication"
    for pid, key in keys.items():
        p, r = packet_index[pid], records[key["dispositionId"]]
        require(pid == sha(f"{seed}|packet|{key['dispositionId']}".encode())[:12], "packet pseudonym differs")
        require(p["wg"] == key["wg"] == key["dispositionId"].split(":", 1)[0], "WG differs")
        require(p["target"] == r["targetTdocNumber"], "target differs")
        require(p["report"] == Path(r["evidencePath"]).name, "report name differs")
        require(p["source"]["path"] == r["evidencePath"] and p["source"]["sha256"] == r["evidenceSha256"]
                and p["source"]["locator"] == r["evidenceLocator"], "packet source binding differs from released record")
        require(sources[p["source"]["path"]]["sha256"] == p["source"]["sha256"], "source restoration hash differs")
        require(digest.fullmatch(p["packetSha256"]), "packet digest invalid")
        require(len({b["block"] for b in p["blocks"]}) == len(p["blocks"]), "duplicate packet block")
        require(any(b["cited"] for b in p["blocks"]), "packet has no cited blocks")
        for block in p["blocks"]:
            require(set(block) == {"block", "cited", "textSha256", "textChars"}, "packet block fields differ")
            require(digest.fullmatch(block["textSha256"]) and block["textChars"] > 0, "block digest invalid")
        method = json.loads(r.get("assessmentMethod") or "{}")
        require(key["code"] == r["dispositionCode"] and key["scope"] == method.get("scope")
                and key["status"] == r["evidenceStatus"], "archived labels differ from released record")
    return packet_index


@functools.lru_cache(maxsize=None)
def log_choose(n):
    return [math.lgamma(n + 1) - math.lgamma(j + 1) - math.lgamma(n - j + 1) for j in range(n + 1)]


def binomial_cdf(k, n, p):
    if k < 0:
        return 0.0
    if p == 0:
        return 1.0
    if p == 1:
        return float(k >= n)
    logp, logq = math.log(p), math.log1p(-p)
    return math.fsum(math.exp(log_choose(n)[j] + j * logp + (n - j) * logq) for j in range(k + 1))


def clopper_pearson(k, n):
    if n == 0:
        return [0.0, 1.0]
    bounds = []
    for cutoff, target in ((k - 1, 0.975), (k, 0.025)):
        lo, hi = 0.0, 1.0
        for _ in range(70):
            mid = (lo + hi) / 2
            if binomial_cdf(cutoff, n, mid) > target:
                lo = mid
            else:
                hi = mid
        bounds.append((lo + hi) / 2)
    return [0.0 if k == 0 else bounds[0], 1.0 if k == n else bounds[1]]


def kappa(pairs):
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[c] * cb[c] for c in ca) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


def score(keys, readings, summary):
    a, b = (index(readings[r], "packetId") for r in ("A", "B"))
    rows = []
    for pid, key in keys.items():
        ra, rb = a[pid], b[pid]
        ca, cb = ra["code"], rb["code"]
        contradicted = ca == cb and ca != "cannot_tell" and ca != key["code"]
        supported = (ca == key["code"] or cb == key["code"]) and not contradicted
        rows.append({"packetId": pid, **key, "A": ca, "B": cb, "scopeA": ra["scope"], "scopeB": rb["scope"],
                     "evidenceASha256": ra["evidenceSha256"], "evidenceAChars": ra["evidenceChars"],
                     "evidenceBSha256": rb["evidenceSha256"], "evidenceBChars": rb["evidenceChars"],
                     "missing": False, "contradicted": contradicted, "supported": supported,
                     "split": (ca == key["code"]) != (cb == key["code"])})
    report = {"readers": ["A", "B"], "packets": len(keys), "bySet": {}}
    scope_counts = {}
    for name in ("random_verified", "random_pending", "reread_differences"):
        sub = [row for row in rows if name in row["sets"]]
        by_wg = {}
        for wg in sorted({row["wg"] for row in sub}) + ["all"]:
            group = [row for row in sub if wg == "all" or row["wg"] == wg]
            n = len(group)
            contradicted = sum(row["contradicted"] for row in group)
            supported = [row for row in group if row["supported"]]
            scope_n = sum(row["scope"] in (row["scopeA"], row["scopeB"]) for row in supported)
            by_wg[wg] = {"n": n, "read": n,
                         "readerAgreement": sum(row["A"] == row["B"] for row in group) / n if n else None,
                         "kappa": kappa([(row["A"], row["B"]) for row in group]),
                         "supported": len(supported), "contradicted": contradicted,
                         "contradictedCI95": clopper_pearson(contradicted, n),
                         "split": sum(row["split"] for row in group),
                         "cannotTellAny": sum("cannot_tell" in (row["A"], row["B"]) for row in group),
                         "recordCodes": dict(collections.Counter(row["code"] for row in group)),
                         "scopeAgreementOnSupported": scope_n / len(supported) if supported else None}
            if wg == "all":
                scope_counts[name] = {"matched": scope_n, "supported": len(supported)}
        report["bySet"][name] = by_wg
    rv = report["bySet"]["random_verified"]
    pops = {wg: summary["census"][wg]["population"]["source_verified"] for wg in summary["census"]}
    total = sum(pops[wg] for wg in rv if wg != "all")
    report["weightedContradictedShare"] = sum(pops[wg] / total * rv[wg]["contradicted"] / rv[wg]["read"]
                                                for wg in rv if wg != "all" and rv[wg]["read"])
    report["toReread"] = [row for row in rows if row["contradicted"] or row["split"] or row["missing"]]
    return report, scope_counts


def compare(actual, expected, path="comparison"):
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and set(actual) == set(expected), f"keys differ: {path}")
        for key in expected:
            compare(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), f"list differs: {path}")
        for i, (left, right) in enumerate(zip(actual, expected)):
            compare(left, right, f"{path}[{i}]")
    elif isinstance(expected, float):
        require(math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-12), f"number differs: {path}")
    else:
        require(actual == expected, f"value differs: {path}")


def load_word_reader(code, provenance):
    """Bind only the archived reader's project root to the explicit code tree.

    The reader file remains byte-identical. Its historical .git-based root
    discovery is a packaging detail, replaced in memory by the supplied root;
    all parsing functions compile from the archived source unchanged.
    """
    path = code / "scripts/tsg/RAN/formal/common/docx_text.py"
    source = path.read_bytes()
    require(sha(source) == provenance["wordReaderSha256"], "archived Word reader hash differs")
    tree = ast.parse(source, filename=str(path))
    assignments = [i for i, node in enumerate(tree.body) if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "_ROOT" for target in node.targets)]
    require(len(assignments) == 1, "Word reader root binding is not unique")
    position = assignments[0]
    original = ast.unparse(tree.body[position].value)
    require(".git" in original and "parents" in original, "unexpected archived reader root expression")
    replacement = ast.parse(f"_ROOT = Path({str(code)!r})").body[0]
    tree.body[position] = ast.copy_location(replacement, tree.body[position])
    ast.fix_missing_locations(tree)
    sys.path[:0] = [str(code / "scripts/tsg/RAN/formal/common"), str(code / "scripts/common/common")]
    module = types.ModuleType("docx_text")
    module.__file__ = str(path)
    sys.modules["docx_text"] = module
    exec(compile(tree, str(path), "exec"), module.__dict__)
    return module


def reconstruct_packets(release, root, packets, provenance):
    code = release / "code"
    docx_text = load_word_reader(code, provenance)

    def read_blocks(path):
        document = docx_text.open_document(path)
        def read(paragraph):
            return docx_text.chunk_text(paragraph, deleted=docx_text.DROP)
        blocks = []
        for block in docx_text.body_blocks(document):
            if docx_text.is_table(block):
                blocks.append("\n".join(docx_text.table_line_rows(block, para=read, deleted=docx_text.DROP)))
            else:
                box = docx_text.box_text(block, read=read)
                blocks.append(read(block) + ("\n" + box if box else ""))
        return blocks

    by_source = collections.defaultdict(list)
    for packet in packets:
        by_source[packet["source"]["path"]].append(packet)
    part_packets = collections.defaultdict(list)
    block_count = 0
    for relative, group in sorted(by_source.items()):
        source = (root / relative).resolve()
        source.relative_to(root.resolve())
        require(source.is_file(), f"missing restored source: {relative}")
        require(sha(source.read_bytes()) == group[0]["source"]["sha256"], f"source hash differs: {relative}")
        blocks = read_blocks(source)
        for packet in group:
            match = re.search(r"body blocks \[(\d+),\s*(\d+)\)", packet["source"]["locator"])
            require(match is not None, "unsupported original packet locator")
            start, end = map(int, match.groups())
            shown, cut = [], False
            for i in range(max(0, start - 4), min(len(blocks), end + 4)):
                text = blocks[i]
                if len(text) > 4000:
                    at = text.find(packet["target"])
                    offset = 0 if at < 0 else max(0, min(at - 2000, len(text) - 4000))
                    text = ("[cut] " if offset else "") + text[offset:offset + 4000] + " [cut]"
                    cut = True
                if text.strip():
                    shown.append({"block": i, "cited": start <= i < end, "text": text})
            actual = {"packetId": packet["packetId"], "wg": packet["wg"], "target": packet["target"],
                      "report": packet["report"], "blocks": shown}
            require(set(actual) == set(provenance["packetShownFields"]), "restored packet fields differ")
            require(sha(canonical(actual)) == packet["packetSha256"], f"original packet digest differs: {packet['packetId']}")
            projected = [{"block": b["block"], "cited": b["cited"], "textSha256": sha(b["text"].encode()),
                          "textChars": len(b["text"])} for b in shown]
            require(projected == packet["blocks"], f"original block hashes differ: {packet['packetId']}")
            part_packets[packet["part"]].append(actual)
            block_count += len(shown)
    for part, rows in part_packets.items():
        rows.sort(key=lambda row: row["packetId"])
        original_bytes = json.dumps({"packets": rows}, ensure_ascii=False, indent=1).encode()
        require(sha(original_bytes) == provenance["originalPacketPartSha256"][part + ".json"], f"original packet part differs: {part}")
    return {"reports": len(by_source), "packets": len(packets), "blocks": block_count,
            "originalPartFilesMatched": len(part_packets), "withheldFieldContract": "matched original packet field set and exact part hashes"}


def mutation_checks(base, keys, packets, readings, records, sources):
    results = []
    variants = []
    bad = copy.deepcopy(readings)
    bad["A"].append(copy.deepcopy(bad["A"][0]))
    variants.append(("duplicate_reader_id", packets, bad))
    variants.append(("missing_packet", packets[:-1], readings))
    bad_packets = copy.deepcopy(packets)
    bad_packets[0]["source"]["sha256"] = "0" * 64
    variants.append(("forged_source_hash", bad_packets, readings))
    for name, packet_rows, reader_rows in variants:
        try:
            audit_rows(keys, packet_rows, reader_rows, records, sources)
        except ValueError as error:
            results.append({"mutation": name, "rejected": True, "reason": str(error)})
        else:
            raise ValueError(f"mutation unexpectedly accepted: {name}")
    # Exercise the actual file-checksum gate with a changed evidence hash in a
    # temporary copy; the released bundle remains untouched.
    with tempfile.TemporaryDirectory(prefix="disposition-reading-mutation-") as temporary:
        copied = Path(temporary) / "bundle"
        shutil.copytree(base, copied)
        path = copied / "readings/A.jsonl"
        rows = json_lines(path)
        rows[0]["evidenceSha256"] = "0" * 64 if rows[0]["evidenceSha256"] != "0" * 64 else "1" * 64
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        try:
            manifests(copied)
        except ValueError as error:
            require("hash mismatch" in str(error), "forged hash failed for an unrelated reason")
            results.append({"mutation": "forged_evidence_hash", "rejected": True, "reason": str(error)})
        else:
            raise ValueError("forged evidence hash unexpectedly accepted")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--source-root", type=Path, help="Root containing restored ontology/input paths; enables exact original packet reconstruction")
    parser.add_argument("--mutation-checks", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    release = args.release.resolve()
    base = release / "studies/disposition_reading"
    checked_files = manifests(base)
    keys, summary = json_file(base / "keys.json"), json_file(base / "build_summary.json")
    packets, sampling = json_lines(base / "packets.jsonl"), json_file(base / "sampling.json")
    readings = {reader: json_lines(base / f"readings/{reader}.jsonl") for reader in ("A", "B")}
    sources = index(json_lines(base / "sources.jsonl"), "path")
    records, sample_check = audit_sampling(release, keys, sampling, summary)
    audit_rows(keys, packets, readings, records, sources)
    comparison, scope_counts = score(keys, readings, summary)
    compare(comparison, json_file(base / "comparison.json"))
    followups = json_file(base / "followups.json")["cases"]
    contradicted = {row["packetId"]: row for row in comparison["toReread"]
                    if row["contradicted"] and "random_verified" in row["sets"]}
    require({row["packetId"] for row in followups} == set(contradicted) and len(followups) == 3, "follow-up cases differ")
    for row in followups:
        original = contradicted[row["packetId"]]
        require(row["recordCode"] == original["code"] and row["recordScope"] == original["scope"]
                and row["sharedReaderCode"] == original["A"] == original["B"], "follow-up join differs")
        require(row["followupActor"] == "unrecorded", "unrecorded follow-up actor changed")
    set_counts = {name: sum(name in row["sets"] for row in keys.values())
                  for name in ("random_verified", "random_pending", "reread_differences")}
    require(set_counts == {"random_verified": 1000, "random_pending": 100, "reread_differences": 35}, "set counts differ")
    require(len(keys) == 1134 and sum(len(row["sets"]) > 1 for row in keys.values()) == 1, "set overlap differs")
    result = {"status": "PASS", "bundleFilesHashChecked": checked_files,
              "packets": len(keys), "setCounts": set_counts, "overlapPackets": 1,
              "readerRows": {reader: len(rows) for reader, rows in readings.items()},
              "samplingRecomputedFromReleasedPopulation": sample_check,
              "scopeCountsOnSupported": scope_counts, "followupsJoined": len(followups),
              "comparison": comparison,
              "sourcePacketReconstruction": "Run with --source-root to check exact historical packet bytes"}
    if args.source_root:
        result["sourcePacketReconstruction"] = reconstruct_packets(release, args.source_root.resolve(), packets, json_file(base / "provenance.json"))
    if args.mutation_checks:
        result["mutationChecks"] = mutation_checks(base, keys, packets, readings, records, sources)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "comparison"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
