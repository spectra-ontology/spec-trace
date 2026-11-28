#!/usr/bin/env python3
"""Check the released query text, answer-set fingerprints and experimental denominators."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOLD_FILES = [
    "benchmark/items_final/gate/core/chain_items_admitted.jsonl",
    "benchmark/items_final/gate/ran5/chain_items_admitted.jsonl",
]
MATCHED = "studies/matched_domains/gold/selected_items.json"
SCORER = "studies/matched_domains/rescore.py"
IDENTITY = "studies/matched_domains/evidence/meeting_identity_source.json"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def stream(name):
    with gzip.open(HERE / name, "rt", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def fingerprint(scorer, item, rows, kept):
    if rows is None:
        return None
    canonical = {tuple(scorer.cell_key(cell) for cell in row)
                 for row in scorer.identity_rows(item, rows, kept)}
    return sha(encoded(sorted(canonical)))


def gold_inputs(release):
    module = importlib.util.spec_from_file_location("spectra_row_scores", release / SCORER)
    scorer = importlib.util.module_from_spec(module)
    module.loader.exec_module(scorer)
    items = [json.loads(line) for name in GOLD_FILES
             for line in (release / name).read_bytes().splitlines() if line]
    matched = load(release / MATCHED)
    kept = set(load(release / IDENTITY)["rules"]["keptElectronicSpellings"])
    return scorer, kept, {"full667": items, "matched50": matched}


def build_summary(check_gold=None):
    contracts = load(HERE / "items.json")
    question_labels = {}
    if check_gold is not None:
        for name, signature in contracts["inputs"].items():
            require(sha((check_gold / name).read_bytes()) == signature, "Input checksum: " + name)
        scorer, kept, gold = gold_inputs(check_gold)
        for study, items in gold.items():
            expected = {r["id"]: fingerprint(scorer, r, r["gold"], kept) for r in items}
            require(expected == contracts[study], "Gold answer sets: " + study)
            question_labels[study] = {r["id"]: (r["wg"], r["family"], r.get("suite","main"), scorer.packet_id(r)) for r in items}

    hashes = set()
    for row in stream("queries.jsonl.gz"):
        h = row["querySha256"]
        require(h == sha(row["query"].encode()) and h not in hashes, "Query dictionary hash")
        hashes.add(h)

    runs = load(HERE / "runs.json")
    require(len(runs) == 992 and len({(r["study"], r["run"]) for r in runs}) == len(runs), "Run inventory")
    index = {(r["study"], r["run"]): r for r in runs}
    counter = defaultdict(Counter)
    seen_ids = defaultdict(set)
    exact_ids = defaultdict(set)
    used = set()
    packets = load(HERE / "packet_sources.json")
    for study, entries in packets.items():
        for entry in entries.values():
            path = HERE / entry["file"] if "file" in entry else (
                check_gold / entry["releaseFile"] if check_gold is not None else None)
            if path is not None:
                require(sha(path.read_bytes()) == entry["sha256"], "Solver packet checksum: " + str(path))
    for entry in runs:
        key = entry["language"] + "_" + (entry["wg"] if entry["study"] == "full667" else entry["condition"])
        require(entry["packetSha256"] == packets[entry["study"]][key]["sha256"], "Run packet: " + entry["run"])
    counts = Counter()
    changes = {(r["study"],r["run"],r["id"]):r for r in stream("first_writes.jsonl.gz")}
    require(len(changes) == 75, "First-write comparison count")
    inspected_changes = set()
    first_deltas = Counter()
    for (study, run, identifier), pair in changes.items():
        original = pair["first"]
        delivered = pair["deliveredReplay"]
        require(sha(pair["firstQuery"].encode()) == original["querySha256"] != delivered["querySha256"], "First-write query")
        for observation in [original, delivered]:
            digest = observation["returnedIdentitySetSha256"]
            require((digest is not None) == (observation["status"] == "scored"), "First-write outcome")
            require(int(digest is not None and digest == contracts[study][identifier]) == observation["exact"], "First-write exact")
        first_deltas[study,run] += original["exact"] - delivered["exact"]
    for study in ("full667", "matched50"):
        for r in stream(study + ".jsonl.gz"):
            key = (study, r["run"])
            require(key in index and r["id"] in contracts[study], "Unknown run or question")
            if check_gold is not None:
                require((r["wg"], r["family"], r["suite"], r["packetId"]) == question_labels[study][r["id"]],
                        "Question metadata differs from public gold: " + r["id"])
            if study == "full667":
                require(r["wg"] == index[key]["wg"], "Wrong group on full-workload question")
            require(r["id"] not in seen_ids[key], "Duplicate item in " + r["run"])
            seen_ids[key].add(r["id"])
            h = r["querySha256"]
            require(h is None or h in hashes, "Query bytes unavailable")
            if h is not None:
                used.add(h)
            digest = r["returnedIdentitySetSha256"]
            exact = int(digest is not None and digest == contracts[study][r["id"]])
            require(exact == r["exact"], "Exact score disagrees with returned set: " + r["run"] + " " + r["id"])
            require((digest is not None) == (r["status"] == "scored"), "Execution outcome and rows differ")
            if exact:
                exact_ids[key].add(r["id"])
            if digest is not None:
                require(h is not None, "Scored question has no query")
            counter[key].update({"assigned": 1, "exact": exact, r["status"]: 1})
            k = (study, r["run"], r["id"])
            if k in changes:
                pair = changes[k]
                require(all(r[f] == val for f, val in pair["deliveredReplay"].items()), "Delivered version replay")
                require(index[key]["deliveredResponseSha256"] == pair["deliveredResponseSha256"], "Delivered file binding")
                inspected_changes.add(k)
            counts[study] += 1
    require(inspected_changes == set(changes), "Missing first-write comparisons")
    require(hashes == used, "Unreferenced query text")
    require(counts == {"full667": 106720, "matched50": 9600}, "Study denominators")
    groups = defaultdict(lambda: defaultdict(Counter))
    repeat_questions = defaultdict(set)
    item_exact_repeats = defaultdict(Counter)
    for key, meta in index.items():
        c = counter[key]
        require(c["assigned"] == meta["assigned"] and c["exact"] == meta["exact"], "Run totals: " + meta["run"])
        study, run = key
        group = (study, meta["cohort"], meta["model"], meta["language"], meta["condition"])
        rep_key = (*group, meta["repetition"])
        require(repeat_questions[rep_key].isdisjoint(seen_ids[key]), "Repeated question inside one repetition")
        repeat_questions[rep_key].update(seen_ids[key])
        item_exact_repeats[group].update(exact_ids[key])
        groups[group][meta["repetition"]].update(c)
    result = {"full667": [], "matched50": [], "full667FirstWriteSensitivity": []}
    for (study, cohort, model, lang, cond), repeats in sorted(groups.items()):
        repeat_count = 2 if study == "matched50" and cohort == "codex" else 10
        n = 667 if study == "full667" else 50
        require(set(repeats) == set("ABCDEFGHIJ"[:repeat_count]), "Repeat labels: " + model)
        per_repeat = {}
        for letter, c in sorted(repeats.items()):
            require(c["assigned"] == n, "Incomplete repeat")
            require(repeat_questions[(study, cohort, model, lang, cond, letter)] == set(contracts[study]),
                    "Different questions within a repetition")
            per_repeat[letter] = {"assigned": n, "exact": c["exact"], "accuracy": c["exact"] / n}
        total = sum(c["exact"] for c in repeats.values())
        rates = [r["accuracy"] for r in per_repeat.values()]
        summary = {"cohort": cohort, "model": model, "language": lang, "condition": cond,
                   "assigned": n * repeat_count, "exact": total, "accuracy": total / (n * repeat_count),
                   "perRepeat": per_repeat, "repeatRange": [min(rates), max(rates)]}
        histogram = Counter(item_exact_repeats[(study, cohort, model, lang, cond)][identifier] for identifier in contracts[study])
        summary["questionsByExactRepeatCount"] = [histogram[i] for i in range(repeat_count + 1)]
        result[study].append(summary)
        if study == "full667":
            affected = {r["repetition"] for r in runs if r["study"] == study and r["model"] == model and
                        r["language"] == lang and r["outputAssemblyDeviation"]}
            if affected:
                retained = [v for k, v in per_repeat.items() if k not in affected]
                assigned = sum(r["assigned"] for r in retained)
                exact = sum(r["exact"] for r in retained)
                result["full667FirstWriteSensitivity"].append({"model": model, "language": lang,
                    "excludedRepetitions": sorted(affected), "assigned": assigned, "exact": exact, "accuracy": exact/assigned})
    result["reconstructedFirstWrites"] = []
    for (study, run), delta in sorted(first_deltas.items()):
        meta = index[study,run]
        pairs = [p for p in changes.values() if p["study"] == study and p["run"] == run]
        require(meta["outputAssemblyDeviation"], "Undocumented rewrite")
        changed_status = Counter((p["first"]["status"],p["deliveredReplay"]["status"]) for p in pairs)
        result["reconstructedFirstWrites"].append({"study":study,"run":run,"assigned":meta["assigned"],
            "changedQueries":len(pairs),"deliveredExact":meta["exact"],"firstExact":meta["exact"]+delta,
            "statusTransitions":[{"first":a,"delivered":b,"count":c} for (a,b),c in sorted(changed_status.items())]})
    result["matched50DomainPairs"] = []
    for meta in runs:
        if meta["study"] != "matched50" or meta["condition"] != "schema_only":
            continue
        right = index[("matched50", meta["run"].replace("__schema_only__", "__schema_domains__"))]
        both = [meta, right]
        result["matched50DomainPairs"].append({
            "cohort": meta["cohort"], "model": meta["model"], "language": meta["language"],
            "repetition": meta["repetition"], "schemaExact": meta["exact"], "domainExact": right["exact"],
            "exactDifference": right["exact"] - meta["exact"],
            "gains": len(exact_ids[("matched50", right["run"])] - exact_ids[("matched50", meta["run"])]),
            "losses": len(exact_ids[("matched50", meta["run"])] - exact_ids[("matched50", right["run"])]),
            "completeInputPair": all(r["inputComplete"] for r in both),
            "conformingAssemblyPair": all(not r["outputAssemblyDeviation"] for r in both),
            "validDeliveredPair": all(r["validDeliveredSubmission"] for r in both),
        })
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release", type=Path, help="also bind question IDs and answer sets to this public artifact root")
    args = ap.parse_args()
    for line in (HERE / "SHA256SUMS").read_text().splitlines():
        h, name = line.split("  ", 1)
        require(sha((HERE / name).read_bytes()) == h, "File checksum: " + name)
    require(build_summary(args.release) == load(HERE / "summary.json"), "Summary differs")
    print("Verified 992 sessions, 106,720 full-workload positions and 9,600 matched-study positions.")
