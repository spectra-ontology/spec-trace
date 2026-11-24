#!/usr/bin/env python3
"""Rehydrate disposition evidence from restored, hash-checked meeting reports.

Run after restore_sources.py. The output is a local JSON-LD document with source
passages restored. Each passage must match its producer's SHA-256 receipt before
it is emitted. The report distinguishes passage verification from a direct
target-predicate rule reread; target-identity reviews remain separate evidence.
No model calls, database servers or network requests are used by this program.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys


def stream_rows(path):
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", type=Path, required=True)
    ap.add_argument("--source-root", type=Path, required=True,
                    help="Root passed to restore_sources.py --dest")
    ap.add_argument("--wg", nargs="+", default=["RAN1", "RAN2", "RAN3", "RAN4", "RAN5"])
    ap.add_argument("--limit", type=int, default=0, help="First N records per WG; 0 checks every record")
    ap.add_argument("--out", type=Path, required=True, help="Local rehydrated JSON-LD")
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    release, root = args.release.resolve(), args.source_root.resolve()
    # The modules retain their repository-relative layout in code/. A .git
    # marker makes their existing project-root discovery independent of cwd.
    code = release / "code"
    if not (code / ".git").exists():
        raise SystemExit("Create the empty project marker first: mkdir -p RELEASE/code/.git")
    sys.path[:0] = [str(code / "scripts/tsg/RAN/formal/common"), str(code / "scripts/common")]
    import decision_disposition as d
    import document_decision_source as ds
    wanted = {}
    context = None
    for wg in args.wg:
        path = release / f"records/phase-2/{wg}/decision_dispositions.jsonld"
        if not path.exists():
            path = path.with_suffix(path.suffix + ".gz")
        for n, row in enumerate(stream_rows(path)):
            if args.limit and n >= args.limit:
                break
            wanted[row["dispositionId"]] = row
        if context is None:
            opener = gzip.open if path.suffix == ".gz" else open
            lines = []
            with opener(path, "rt", encoding="utf-8") as stream:
                for line in stream:
                    if '"@graph":' in line:
                        break
                    lines.append(line)
            context = json.loads("".join(lines).rstrip().rstrip(",") + "}")["@context"]
    recipes = {}
    with gzip.open(release / "sources/disposition_bindings.jsonl.gz", "rt") as stream:
        for line in stream:
            receipt = json.loads(line)
            if receipt["dispositionId"] in wanted:
                recipes[receipt["dispositionId"]] = receipt
    totals, per_wg, failures = collections.Counter(), collections.defaultdict(collections.Counter), []
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as output:
        output.write('{"@context":' + json.dumps(context) + ',"@graph":[\n')
        emitted = 0
        # Group by source so each parsed document is released before the next.
        by_source = collections.defaultdict(list)
        for identity, row in wanted.items():
            by_source[row["evidencePath"]].append((identity, row))
        for relative, rows in sorted(by_source.items()):
            path = (root / relative).resolve()
            path.relative_to(root)
            try:
                texts, sha, blocks = d.source_blocks(str(path))
                for identity, row in rows:
                    wg = identity.split(":", 1)[0]
                    counter = per_wg[wg]
                    counter["checked"] += 1
                    try:
                        if sha != row["evidenceSha256"]:
                            raise ValueError("source_sha256_mismatch")
                        recipe = recipes[identity]
                        match = re.fullmatch(r"word/document.xml accepted body blocks \[(\d+),(\d+)\)", row["evidenceLocator"])
                        event = None
                        if match:
                            start, end = map(int, match.groups())
                            quote = "\n".join(texts[start:end])
                        else:
                            match = re.fullmatch(r"word/document.xml accepted table block (\d+) row (\d+); governing body blocks \[(\d+),(\d+)\)", row["evidenceLocator"])
                            if not match:
                                raise ValueError("unsupported_locator")
                            table, accepted_row, start, end = map(int, match.groups())
                            record = ds._annex_source_tables(path, sha, texts, blocks, wg)[table]
                            event = ds._annex_event({"meeting_id": wg + "#restored"}, relative,
                                                    sha, record, accepted_row, record["rows"][accepted_row])
                            quote = event["content"]
                        if len(quote) != recipe["quoteChars"] or hashlib.sha256(quote.encode()).hexdigest() != recipe["quoteSha256"]:
                            raise ValueError("quote_receipt_mismatch")
                        counter["passage_verified"] += 1
                        method = json.loads(row["assessmentMethod"])
                        target = row["targetTdocNumber"]
                        if target != identity.split(":", 2)[2]:
                            raise ValueError("target_identity_mismatch")
                        method["decisionBodyBlocks"] = recipe["decisionBodyBlocks"]
                        ds_start, ds_end = recipe["decisionBodyBlocks"]
                        if not start <= ds_start < ds_end <= end:
                            raise ValueError("decision_span_outside_evidence")
                        if "documentEntry" in recipe:
                            if event is None:
                                field = dict(recipe["documentEntry"])
                                field["headerText"] = texts[field["headerBlock"]]
                                field["decisionText"] = texts[field["decisionBlock"]]
                                event = {"subject_tdoc": method.get("subject"), "document_entry": field,
                                         "meeting_id": wg + "#restored"}
                            code_read, _, rule_read = ds.classify_document_decision(event, target)
                        else:
                            code_read, _, rule_read = d.classify_statement("\n".join(texts[ds_start:ds_end]), target,
                                subject=bool(method.get("subject")), meeting_id=wg + "#restored")
                        if (code_read, rule_read) == (row["dispositionCode"], method["rule"]):
                            counter["direct_rule_agrees"] += 1
                        else:
                            counter["identity_or_other_rule_followup"] += 1
                        row["evidenceQuote"] = quote
                        row["assessmentMethod"] = json.dumps(method, sort_keys=True)
                        if emitted:
                            output.write(',\n')
                        output.write(json.dumps(row, ensure_ascii=False))
                        emitted += 1
                        counter["emitted"] += 1
                    except (ValueError, KeyError, IndexError) as error:
                        counter[str(error).strip("'")] += 1
                        failures.append({"dispositionId": identity, "reason": str(error)})
            except (OSError, ValueError, KeyError) as error:
                for identity, row in rows:
                    per_wg[identity.split(":", 1)[0]]["source_unavailable"] += 1
                    failures.append({"dispositionId": identity, "reason": str(error)})
            finally:
                d.source_blocks.cache_clear()
                ds._ANNEX_CACHE.clear()
        output.write('\n]}\n')
    for count in per_wg.values():
        totals.update(count)
    report = {"scope": "first N records per WG" if args.limit else "all selected WG records",
              "limit_per_wg": args.limit, "total": dict(totals), "per_wg": {k: dict(v) for k, v in per_wg.items()},
              "failures": failures, "emission": "Only passages whose exact producer quote hash and source hash match are emitted.",
              "rule_scope": "Direct target-predicate rule reread; identity-review and other producer conditions are reported separately."}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["total"]))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
