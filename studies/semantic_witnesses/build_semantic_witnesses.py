#!/usr/bin/env python3
"""Enumerate released-record witnesses and execute pinned semantic controls."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import resource
import sqlite3
import time


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def normalize(rows):
    return sorted(set(tuple(str(value) if value is not None else None for value in row) for row in rows))


def display(document):
    return document.removeprefix("tdoc:")


def triple_predicate(alias, identity, release=True):
    fields = zip(("spec", "release", "clause"), identity)
    return " AND ".join(f"{alias}.{key}={literal(value)}" for key, value in fields if release or key != "release")


def sql_link(document_expression, identity, release=True):
    return ("EXISTS(SELECT 1 FROM cr_modifies_section x JOIN section s ON s.id=x.section_id "
            f"WHERE x.cr={document_expression} AND {triple_predicate('s', identity, release)})")


def section_select(document):
    return ("SELECT s.spec,s.release,s.clause FROM cr_modifies_section x "
            f"JOIN section s ON s.id=x.section_id WHERE x.cr={literal(document)}")


def data_from_connection(connection):
    members = defaultdict(set)
    member_multiplicity = Counter()
    for document, pack in connection.execute("SELECT cr,pack_id FROM cr_in_pack"):
        members[pack].add(document)
        member_multiplicity[pack, document] += 1
    sections = {row[0]: tuple(row[1:]) for row in connection.execute("SELECT id,spec,release,clause FROM section")}
    if any(any(value is None for value in identity) for identity in sections.values()):
        raise ValueError("Null typed section identity")
    links = defaultdict(set)
    raw_link_count = Counter()
    for document, section in connection.execute("SELECT cr,section_id FROM cr_modifies_section"):
        if section not in sections:
            raise ValueError(("Dangling section", document, section))
        links[document].add(sections[section])
        raw_link_count[document] += 1
    documents = {row[0]: row[1] for row in connection.execute("SELECT id,number FROM document")}
    packs = {row[0]: row[1] for row in connection.execute("SELECT id,pack_number FROM cr_pack")}
    resolutions = dict(connection.execute("SELECT id,meeting_id FROM resolution"))
    meetings = {row[0]: row[1:] for row in connection.execute("SELECT id,label,number_int,wg FROM meeting")}
    dispositions = []
    per_document = defaultdict(list)
    per_meeting = defaultdict(list)
    for identity, resolution, document, code in connection.execute(
            "SELECT id,resolution_id,target,code FROM disposition "
            "WHERE evidence_status='source_verified' AND scope='whole_target'"):
        if resolution not in resolutions:
            raise ValueError(("Dangling resolution", resolution))
        row = (identity, document, code)
        dispositions.append(row)
        per_document[document].append(row)
        per_meeting[resolutions[resolution]].append(row)
    return dict(members=members, member_multiplicity=member_multiplicity, sections=sections,
                links=links, raw_link_count=raw_link_count, documents=documents, packs=packs,
                resolutions=resolutions, meetings=meetings, dispositions=dispositions,
                per_document=per_document, per_meeting=per_meeting)


def histogram(records):
    grouped = defaultdict(set)
    raw = Counter()
    for _, document, code in records:
        grouped[code].add(document)
        raw[code] += 1
    counts = {code: len(documents) for code, documents in grouped.items()}
    return counts, {code: raw[code] - count for code, count in counts.items()}


def pack_records(data, pack, allowed=None):
    for document in sorted(data["members"][pack]):
        if allowed is None or document in allowed:
            for _ in range(data["member_multiplicity"][pack, document]):
                yield from data["per_document"][document]


def selection_digest(study, wg, stratum, candidate):
    return hashlib.sha256(canonical([study, wg, stratum, candidate]).encode()).hexdigest()


class Pools:
    def __init__(self, output, protocol, wg):
        self.output = output
        self.protocol = protocol
        self.wg = wg
        self.handles = {}
        self.counts = Counter()
        self.hashes = {}
        self.best = {}
        self.scanned = Counter()
        self.excluded = defaultdict(Counter)
        for definition in protocol["strata"]:
            stratum = definition["id"]
            self.handles[stratum] = gzip.open(output / f"pool_{wg}_{stratum}.jsonl.gz", "wt", encoding="utf-8")
            self.hashes[stratum] = hashlib.sha256()

    def consider(self, stratum, candidate, witness, conditions):
        self.scanned[stratum] += 1
        failed = [name for name, passed in conditions.items() if not passed]
        if failed:
            for name in failed:
                self.excluded[stratum][name] += 1
            return
        record = {"candidate": candidate, "witness": witness}
        line = canonical(record) + "\n"
        self.handles[stratum].write(line)
        self.hashes[stratum].update(line.encode())
        self.counts[stratum] += 1
        rank = (selection_digest(self.protocol["study"], self.wg, stratum, candidate), canonical(candidate))
        if stratum not in self.best or rank < self.best[stratum][0]:
            self.best[stratum] = (rank, record)

    def close(self):
        cells = []
        for definition in self.protocol["strata"]:
            stratum = definition["id"]
            self.handles[stratum].close()
            path = self.output / f"pool_{self.wg}_{stratum}.jsonl.gz"
            selected = self.best.get(stratum)
            cells.append({"wg": self.wg, "stratum": stratum, "family": definition["family"],
                          "candidate_universe_count": self.scanned[stratum],
                          "eligible_candidates": self.counts[stratum],
                          "failed_predicate_counts": dict(self.excluded[stratum]),
                          "pool": path.name, "pool_sha256": sha(path),
                          "pool_uncompressed_sha256": self.hashes[stratum].hexdigest(),
                          "status": "available" if selected else "unavailable",
                          "selected": selected[1] if selected else None,
                          "selection_sha256": selected[0][0] if selected else None})
        return cells


def enumerate_pools(data, pool):
    members, links = data["members"], data["links"]
    for cohort_type, cohorts in (("pack", sorted(members)), ("meeting", sorted(data["per_meeting"]))):
        for cohort in cohorts:
            records = pack_records(data, cohort) if cohort_type == "pack" else data["per_meeting"][cohort]
            counts, excess = histogram(records)
            witness = {"code_counts": counts, "raw_duplicate_excess_by_code": excess,
                       "code_groups": len(counts), "raw_duplicate_excess": sum(excess.values())}
            candidate = [cohort_type, cohort]
            multiple, duplicate = len(counts) >= 2, any(value > 0 for value in excess.values())
            pool.consider(f"{cohort_type}_multicode", candidate, witness, {"multiple_codes": multiple})
            pool.consider(f"{cohort_type}_duplicates", candidate, witness, {"duplicate_count": duplicate})
            pool.consider(f"{cohort_type}_multicode_duplicates", candidate, witness,
                          {"multiple_codes": multiple, "duplicate_count": duplicate})
    for pack, documents in sorted(members.items()):
        by_section = defaultdict(set)
        for document in documents:
            for identity in links[document]:
                by_section[identity].add(document)
        pairs = set()
        for peers in by_section.values():
            pairs.update(itertools.combinations(sorted(peers), 2))
        for first, second in sorted(pairs):
            left, right = links[first], links[second]
            common, left_only, right_only = left & right, left - right, right - left
            basic = bool(common and left_only and right_only)
            witness = {"intersection_size": len(common), "first_only_size": len(left_only),
                       "second_only_size": len(right_only)}
            right_short = {(identity[0], identity[2]) for identity in right}
            false_left = {identity for identity in left_only if (identity[0], identity[2]) in right_short}
            pool.consider("intersection", [pack, first, second], witness, {"three_nonempty_regions": basic})
            pool.consider("intersection_release", [pack, first, second],
                          dict(witness, release_blind_extra_sections=sorted(false_left)),
                          {"three_nonempty_regions": basic, "release_collision": bool(false_left)})
            for one, two in ((first, second), (second, first)):
                one_only = links[one] - links[two]
                two_short = {(identity[0], identity[2]) for identity in links[two]}
                false_one = {identity for identity in one_only if (identity[0], identity[2]) in two_short}
                directed = {"intersection_size": len(common), "first_only_size": len(one_only),
                            "second_only_size": len(links[two] - links[one])}
                pool.consider("difference", [pack, one, two], directed, {"three_nonempty_regions": basic})
                pool.consider("difference_release", [pack, one, two],
                              dict(directed, release_blind_removed_sections=sorted(false_one)),
                              {"three_nonempty_regions": basic, "release_collision": bool(false_one)})
        section_pairs = set()
        for document in documents:
            section_pairs.update(itertools.combinations(sorted(links[document]), 2))
        for one, two in sorted(section_pairs):
            both = by_section[one] & by_section[two]
            one_only = by_section[one] - by_section[two]
            two_only = by_section[two] - by_section[one]
            basic = bool(both and one_only and two_only)
            witness = {"both_documents": len(both), "first_only_documents": len(one_only),
                       "second_only_documents": len(two_only), "neither_documents": len(documents - by_section[one] - by_section[two])}
            candidate = [pack, one, two]
            pool.consider("conjunction", candidate, witness, {"three_nonempty_regions": basic})
            if basic:
                short_one, short_two = (one[0], one[2]), (two[0], two[2])
                broad = {document for document in documents if short_one in {(s[0], s[2]) for s in links[document]}
                         and short_two in {(s[0], s[2]) for s in links[document]}}
            else:
                broad = both
            pool.consider("conjunction_release", candidate, dict(witness, release_blind_extra_documents=sorted(broad - both)),
                          {"three_nonempty_regions": basic, "release_collision": broad != both})
            and_counts, _ = histogram(pack_records(data, pack, both))
            or_counts, _ = histogram(pack_records(data, pack, by_section[one] | by_section[two]))
            pool.consider("composition", candidate,
                          dict(witness, conjunction_code_counts=and_counts, or_code_counts=or_counts),
                          {"three_nonempty_regions": basic, "nonempty_histogram": bool(and_counts),
                           "or_changes_histogram": and_counts != or_counts})
        counts = {document: len(links[document]) for document in documents}
        positive_sizes = {value for value in counts.values() if value > 0}
        varied = len(positive_sizes) >= 2
        high = max(counts.values())
        winners = {document: value for document, value in counts.items() if value == high}
        short_counts = {document: len({(s[0], s[2]) for s in links[document]}) for document in documents}
        short_high = max(short_counts.values())
        short_winners = {document: value for document, value in short_counts.items() if value == short_high}
        ties, changed = len(winners) >= 2, winners != short_winners
        winner_changed = set(winners) != set(short_winners)
        witness = {"members": len(documents), "positive_count_values": sorted(positive_sizes),
                   "typed_counts": counts, "typed_maximum": high, "typed_winners": winners,
                   "release_collapsed_counts": short_counts, "release_collapsed_maximum": short_high,
                   "release_collapsed_winners": short_winners, "winner_set_changed": winner_changed,
                   "result_set_changed": changed, "ties": len(winners)}
        for stratum, conditions in (
                ("maximum_variation", {"positive_count_variation": varied}),
                ("maximum_ties", {"positive_count_variation": varied, "ties": ties}),
                ("maximum_release_count", {"positive_count_variation": varied, "release_count_result_changes": changed}),
                ("maximum_release_winner", {"positive_count_variation": varied, "release_winner_set_changes": winner_changed}),
                ("maximum_ties_release", {"positive_count_variation": varied, "ties": ties, "release_count_result_changes": changed})):
            pool.consider(stratum, [pack], witness, conditions)
        absent = {document for document in documents if not links[document]}
        pool.consider("absence", [pack], {"zero_link_members": len(absent), "positive_link_members": len(documents - absent)},
                      {"mixed_presence_absence": bool(absent and documents - absent)})


def task(data, cell):
    family, stratum = cell["family"], cell["stratum"]
    anchor = cell["selected"]["candidate"]
    members, links = data["members"], data["links"]
    mutations = {}
    if family == "pack_disposition_counts":
        kind, cohort = anchor
        if kind == "pack":
            records = pack_records(data, cohort)
            origin = "cr_in_pack m JOIN disposition d ON d.target=m.cr"
            condition = f"m.pack_id={literal(cohort)}"
            label = f"CR pack {data['packs'][cohort]}"
        else:
            records = data["per_meeting"][cohort]
            origin = "disposition d JOIN resolution r ON r.id=d.resolution_id"
            condition = f"r.meeting_id={literal(cohort)}"
            label = f"resolution meeting {cohort} ({data['meetings'][cohort][0]})"
        gold_counts, _ = histogram(records)
        gold = list(gold_counts.items())
        where = f"{condition} AND d.evidence_status='source_verified' AND d.scope='whole_target'"
        base = f"SELECT d.code,COUNT(DISTINCT d.target) FROM {origin} WHERE {where}"
        reference = base + " GROUP BY d.code"
        mutations["omit_group_by"] = base
        mutations["count_star"] = reference.replace("COUNT(DISTINCT d.target)", "COUNT(*)")
        question = (f"For {label}, group source-verified whole-document disposition records by code and return "
                    "each code with its distinct-document count. Count a document once per code. "
                    + ("Use dispositions recorded at that meeting." if kind == "meeting" else "Use pack membership and qualifying dispositions on those members."))
        fields = ["disposition", "document_count"]
    elif family in ("shared_clauses", "exclusive_clauses"):
        pack, first, second = anchor
        intersect = family == "shared_clauses"
        left, right = section_select(first), section_select(second)
        gold = links[first] & links[second] if intersect else links[first] - links[second]
        reference = left + (" INTERSECT " if intersect else " EXCEPT ") + right
        mutations.update(union=left + " UNION " + right, first_only=left, second_only=right,
                         intersection=left + " INTERSECT " + right,
                         reverse_difference=right + " EXCEPT " + left)
        join = ("SELECT DISTINCT a.spec,a.release,a.clause FROM cr_modifies_section x JOIN section a ON a.id=x.section_id "
                f"WHERE x.cr={literal(first)} AND " + ("EXISTS" if intersect else "NOT EXISTS") +
                "(SELECT 1 FROM cr_modifies_section y JOIN section b ON b.id=y.section_id "
                f"WHERE y.cr={literal(second)} AND b.spec=a.spec AND b.clause=a.clause)")
        mutations["release_blind_membership"] = join
        operation = "both documents modify" if intersect else f"{display(first)} modifies and {display(second)} does not modify in this snapshot"
        question = (f"Compare pack {data['packs'][pack]} members {display(first)} and {display(second)}. "
                    f"Return every (specification, release, clause) identity that {operation}. Preserve release distinctions.")
        fields = ["specification", "release", "clause"]
    elif family in ("both_clause_documents", "conjunction_disposition_counts"):
        pack, one, two = anchor
        one, two = tuple(one), tuple(two)
        both = {document for document in members[pack] if one in links[document] and two in links[document]}
        first_condition, second_condition = sql_link("m.cr", one), sql_link("m.cr", two)
        prefix = f"SELECT DISTINCT m.cr FROM cr_in_pack m WHERE m.pack_id={literal(pack)} AND "
        selected = prefix + f"({first_condition}) AND ({second_condition})"
        selected_or = prefix + f"(({first_condition}) OR ({second_condition}))"
        if family == "both_clause_documents":
            gold = [(display(document),) for document in both]
            transform = lambda sql: sql.replace("SELECT DISTINCT m.cr", "SELECT DISTINCT REPLACE(m.cr,'tdoc:','')", 1)
            reference = transform(selected)
            mutations["or"] = transform(selected_or)
            mutations["first_only"] = transform(prefix + first_condition)
            mutations["second_only"] = transform(prefix + second_condition)
            mutations["release_blind_membership"] = transform(prefix + sql_link("m.cr", one, False) + " AND " + sql_link("m.cr", two, False))
            fields = ["document"]
            question = f"Within CR pack {data['packs'][pack]}, return the document numbers linked to both typed sections {canonical(one)} and {canonical(two)}. Require both full identities, retaining each release."
        else:
            gold_counts, _ = histogram(pack_records(data, pack, both))
            gold = list(gold_counts.items())
            tail = (" SELECT d.code,COUNT(DISTINCT d.target) FROM eligible e JOIN disposition d ON d.target=e.cr "
                    "WHERE d.evidence_status='source_verified' AND d.scope='whole_target' GROUP BY d.code")
            reference = "WITH eligible AS (" + selected + ")" + tail
            mutations["or_before_grouping"] = "WITH eligible AS (" + selected_or + ")" + tail
            mutations["omit_section_filter"] = "WITH eligible AS (" + prefix[:-5] + ")" + tail
            fields = ["disposition", "document_count"]
            question = (f"Within CR pack {data['packs'][pack]}, first retain member documents linked to both typed sections "
                        f"{canonical(one)} and {canonical(two)}, preserving releases. For those documents, return each source-verified whole-document disposition code with its distinct-document count; count once per code.")
    elif family == "largest_clause_footprint":
        pack = anchor[0]
        counts = {document: len(links[document]) for document in members[pack]}
        high = max(counts.values())
        gold = [(display(document), count) for document, count in counts.items() if count == high]
        full = ("WITH identities AS (SELECT DISTINCT x.cr,s.spec,s.release,s.clause FROM cr_modifies_section x "
                "JOIN section s ON s.id=x.section_id), counts AS (SELECT m.cr,COUNT(i.clause) AS n "
                f"FROM (SELECT DISTINCT cr FROM cr_in_pack WHERE pack_id={literal(pack)}) m "
                "LEFT JOIN identities i ON i.cr=m.cr GROUP BY m.cr) ")
        end = "SELECT REPLACE(cr,'tdoc:',''),n FROM counts WHERE n=(SELECT MAX(n) FROM counts)"
        reference = full + end
        mutations["all_positive"] = full + "SELECT REPLACE(cr,'tdoc:',''),n FROM counts WHERE n>0"
        mutations["limit_one"] = reference + " ORDER BY cr LIMIT 1"
        mutations["release_collapsed_count"] = (full.replace("x.cr,s.spec,s.release,s.clause", "x.cr,s.spec,s.clause") + end)
        fields = ["document", "section_count"]
        question = (f"For every member of CR pack {data['packs'][pack]}, count distinct (specification, release, clause) "
                    "modified-section identities, keeping releases distinct. Return every document tied at the largest count with that count. Include zero-link members in the comparison.")
    else:
        pack = anchor[0]
        gold = [(display(document),) for document in members[pack] if not links[document]]
        prefix = f"SELECT DISTINCT REPLACE(m.cr,'tdoc:','') FROM cr_in_pack m WHERE m.pack_id={literal(pack)}"
        exists = "EXISTS(SELECT 1 FROM cr_modifies_section x WHERE x.cr=m.cr)"
        reference = prefix + " AND NOT " + exists
        mutations["exists"] = prefix + " AND " + exists
        mutations["all_members"] = prefix
        fields = ["document"]
        question = f"Which members of CR pack {data['packs'][pack]} have zero typed modified-section records in this released snapshot? Return document numbers. Interpret absence within the recorded snapshot."
    return {"id": cell["wg"] + "-witness-" + stratum, "wg": cell["wg"], "stratum": stratum,
            "family": family, "anchor": anchor, "question": question, "fields": fields,
            "authorship": "author-written semantic witness task", "gold": normalize(gold),
            "reference_sql": reference, "mutations": mutations, "data_witness": cell["selected"]["witness"],
            "selection_sha256": cell["selection_sha256"]}


def execute(connection, sql):
    start = time.monotonic()
    connection.set_progress_handler(lambda: time.monotonic() - start >= 60, 10000)
    try:
        output = normalize(connection.execute(sql).fetchall())
        return {"status": "ok", "rows": output, "seconds": time.monotonic() - start,
                "output_sha256": hashlib.sha256(canonical(output).encode()).hexdigest()}
    except sqlite3.Error as error:
        return {"status": "timeout" if "interrupted" in str(error) else "error", "error": str(error),
                "seconds": time.monotonic() - start}
    finally:
        connection.set_progress_handler(None, 0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--database-directory", type=Path, required=True)
    parser.add_argument("--original-pin", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (2 << 30, 2 << 30))
    protocol_path = Path(__file__).with_name("protocol.json")
    protocol = json.loads(protocol_path.read_text())
    original = json.loads(args.original_pin.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    definitions = {definition["id"]: definition for definition in protocol["strata"]}
    all_cells, tasks, receipts, input_pins, schemas = [], [], [], [], {}
    total_start = time.monotonic()
    for wg in protocol["working_groups"]:
        started = time.monotonic()
        pin = next(item for item in original["inputs"] if item["wg"] == wg)
        plain = args.release / "sqlite" / f"{wg}.sqlite"
        source = plain if plain.exists() else plain.with_suffix(".sqlite.gz")
        if sha(source) != pin["source_sha256"]:
            raise ValueError((wg, "Released source pin mismatch"))
        db = source if source.suffix == ".sqlite" else args.database_directory / f"{wg}.sqlite"
        if not db.exists():
            raise FileNotFoundError((wg, db))
        database_hash = sha(db)
        if database_hash != pin["database_sha256"]:
            raise ValueError((wg, "Execution database pin mismatch"))
        connection = sqlite3.connect("file:" + str(db.resolve()) + "?mode=ro&immutable=1", uri=True)
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA cache_size=-16384")
        data = data_from_connection(connection)
        schema = [row[0] for row in connection.execute("SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name")]
        domains = {field: [row[0] for row in connection.execute(f"SELECT DISTINCT {field} FROM disposition ORDER BY {field}")]
                   for field in ("code", "scope", "evidence_status")}
        schemas[wg] = {"sql": schema, "disposition_value_domains": domains}
        pools = Pools(args.output, protocol, wg)
        enumerate_pools(data, pools)
        cells = pools.close()
        all_cells.extend(cells)
        for cell in cells:
            if cell["status"] != "available":
                continue
            item = task(data, cell)
            definition = definitions[cell["stratum"]]
            reference = execute(connection, item["reference_sql"])
            reference["python_gold_equal"] = reference.get("rows") == item["gold"]
            mutated = []
            # Execute every semantically meaningful control implemented for the family.
            # Required controls define eligibility; additional controls quantify transfer.
            excluded_same_operator = {"intersection"} if cell["family"] == "shared_clauses" else set()
            if cell["family"] == "exclusive_clauses":
                excluded_same_operator.update(("first_only", "second_only"))
            for name, sql in item["mutations"].items():
                if name in excluded_same_operator:
                    continue
                outcome = execute(connection, sql)
                outcome.update(name=name, sql=sql, required=name in definition["mutations"])
                if outcome["status"] == "ok":
                    actual, expected = set(map(tuple, outcome["rows"])), set(map(tuple, item["gold"]))
                    outcome.update(discriminating=actual != expected, gold_only=sorted(expected - actual), mutant_only=sorted(actual - expected))
                else:
                    outcome["discriminating"] = False
                mutated.append(outcome)
            receipts.append({"id": item["id"], "reference": reference, "mutations": mutated,
                             "all_required_discriminating": all(row["discriminating"] for row in mutated if row["required"])})
            tasks.append(item)
            print(canonical({"wg": wg, "stratum": cell["stratum"], "eligible": cell["eligible_candidates"],
                             "reference_equal": reference["python_gold_equal"],
                             "required_controls_pass": receipts[-1]["all_required_discriminating"]}), flush=True)
        connection.close()
        source_unchanged, db_unchanged = sha(source) == pin["source_sha256"], sha(db) == database_hash
        if not (source_unchanged and db_unchanged):
            raise ValueError((wg, "Input changed"))
        input_pins.append({"wg": wg, "source_name": source.name, "source_sha256": pin["source_sha256"],
                           "database_sha256": database_hash, "source_unchanged": source_unchanged,
                           "database_unchanged": db_unchanged, "elapsed_seconds": time.monotonic() - started,
                           "row_counts": {"pack_cohorts": len(data["members"]), "resolution_meeting_cohorts": len(data["per_meeting"]),
                                          "sections": len(data["sections"]), "distinct_section_triples": len(set(data["sections"].values())),
                                          "typed_document_links": sum(map(len, data["links"].values())),
                                          "raw_typed_links": sum(data["raw_link_count"].values()),
                                          "source_verified_whole_document_dispositions": len(data["dispositions"])}})
        save(args.output / "progress.json", {"inputs": input_pins, "cells": all_cells, "completed_tasks": len(tasks)})
    summary = {"study": protocol["study"], "planned_cells": len(all_cells), "available_cells": len(tasks),
               "unavailable_cells": [{key: cell[key] for key in ("wg", "stratum", "candidate_universe_count", "failed_predicate_counts")} for cell in all_cells if cell["status"] == "unavailable"],
               "unique_family_anchors": len({canonical([item["wg"], item["family"], item["anchor"]]) for item in tasks}),
               "python_reference_equal": sum(receipt["reference"]["python_gold_equal"] for receipt in receipts),
               "reference_executions": len(receipts), "mutation_executions": sum(len(receipt["mutations"]) for receipt in receipts),
               "mutation_successes": sum(row["status"] == "ok" for receipt in receipts for row in receipt["mutations"]),
               "mutation_discriminations": sum(row["discriminating"] for receipt in receipts for row in receipt["mutations"]),
               "required_mutation_executions": sum(row["required"] for receipt in receipts for row in receipt["mutations"]),
               "required_mutation_discriminations": sum(row["required"] and row["discriminating"] for receipt in receipts for row in receipt["mutations"]),
               "all_required_controls_pass": all(receipt["all_required_discriminating"] for receipt in receipts),
               "elapsed_seconds": time.monotonic() - total_start, "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               "python_version": __import__("sys").version, "sqlite_version": sqlite3.sqlite_version,
               "new_model_responses": 0, "independent_validation_status": "pending separate checker"}
    save(args.output / "selection_and_gold.json", {"protocol_sha256": sha(protocol_path), "inputs": input_pins, "cells": all_cells, "items": tasks})
    save(args.output / "execution.json", {"summary": summary, "items": receipts})
    save(args.output / "writer_questions.json", {"questions": [{key: item[key] for key in ("id", "wg", "question", "fields", "authorship")} for item in tasks], "new_model_responses": 0})
    save(args.output / "writer_schema.json", schemas)
    save(args.output / "summary.json", summary)
    save(args.output / "freeze.json", {"protocol_sha256": sha(protocol_path), "builder_sha256": sha(Path(__file__)),
                                       "original_pin_sha256": sha(args.original_pin),
                                       "files": {path.name: sha(path) for path in sorted(args.output.iterdir()) if path.is_file()},
                                       "new_model_responses": 0})
    print(canonical(summary), flush=True)


if __name__ == "__main__":
    main()
