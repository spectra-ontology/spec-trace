#!/usr/bin/env python3
"""Build the headroom split's solver packets and session prompts from its admitted items (no model calls).

Every packet is built by the repository's own builders, so the split's packets differ from the admitted set's only in
their items:
- query writers: `run_chain_eval.cypher_task` / `run_chain_eval.sql_task` with the item list of the
  `--export-packet` branch of `run_chain_eval.main` (`{"task", "items": [{id, question, fields}]}` in packet order);
- text search: `build_text_search_packets.py` run as a subprocess, then cut into parts;
- dense tool: `build_tool_condition_packets.py --condition dense` run as a subprocess on those parts.

Session prompts are rendered from the archived prompt of the same working group and language (query writers) or the
archived text-search prompt of the same working group: the archived file is turned into a template by replacing its
path, count and working-group values with slots, and the slots are filled with the split's values. Dense prompts are
written by `build_tool_condition_packets.py` itself.

Answers and evidence never reach a packet: packet items carry only the keys the repository builders write, and
`leak_check.json` reports every gold or evidence value that appears anywhere in the written packets or prompts, with
the place that explains it (the item's own question, the task text, another item's question) or `unexplained`.

Run from the repository root:
  python3 -B <this file> --items <jsonl> [<jsonl> ...] --out-dir <dir> (--parts-per-wg K | --max-part-size N)
      [--query-output-dir D] [--sql-scratch-root D] [--text-work-root D] [--dense-work-root D]
      [--cypher-task archive|bolt] [--query-runs A B C D E] [--text-runs A B] [--dense-runs A B]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path.cwd()
TRACK = "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
SCRIPTS = "scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
if not (ROOT / ".git").exists() or not (ROOT / SCRIPTS / "run_chain_eval.py").exists():
    raise SystemExit("run from the repository root")
sys.path[:0] = [str(ROOT / "scripts/common"), str(ROOT / SCRIPTS)]
import run_chain_eval as rce  # noqa: E402

CHAIN = f"{TRACK}/chain_eval"
ARCHIVE = {
    "cypherPackets": f"{CHAIN}/subagent_packets",
    "sqlPackets": f"{CHAIN}/subagent_packets_sql",
    "queryWriterPrompts": f"{CHAIN}/subagent_queries/prompts",
    "textSearchPackets": f"{CHAIN}/text_search_packets_full",
    "textSearchPrompts": f"{CHAIN}/text_search_full/prompts",
}
SQLITE = f"{TRACK}/integration/sqlite_final/{{wg}}.sqlite"
# Values carried over from the admitted set's text-search build ({CHAIN}/text_search_packets_full/sample.json:
# "seed": "text-search-full", "perCell": 100). With every cell at most --per-cell items, all items are kept;
# the builder checks that instead of trusting it.
TEXT_SEED, TEXT_PER_CELL = "text-search-full", 100
PACKET_ITEM_KEYS = {"id", "question", "fields", "family", "questionSha256"}
LANGS = {"cypher": "text2cypher", "sql": "text2sql"}

# Slots of the archived prompts. Each pattern must match the stated number of times in every archived prompt it is
# applied to; the template is the archived text with each match replaced by its slot name.
QUERY_SLOTS = {
    "cypher": [("packet", r"Read exactly one file: (\S+) \.", 1),
               ("count", r"\((\d+) questions with", 1),
               ("output", r"Write the output to (\S+) ,", 1),
               ("count", r"for all (\d+) items\.", 1)],
    "sql": [("packet", r"Read exactly one input file:\n(\S+)\n", 1),
            ("output", r"Write the result to:\n(\S+)\n", 1),
            ("scratch", r"generator script in (\S+/) to produce", 1)],
}
TEXT_SLOTS = [("root", r"Work in the repository (\S+) \(run", 1),
              ("packet", r"Read exactly one input file: (\S+) \.", 1),
              ("count", r"lists (\d+) questions\.", 1),
              ("work", r"save its printed output under (\S+)/ and", 1),
              ("cmdlog", r"as one line to (\S+)\.\n", 1),
              ("answers", r"\n1\. (\S+) — ", 1),
              ("wg", r"\"wg\" \(\"(RAN\d)\"\)", 1),
              ("trace", r"\n2\. (\S+) — ", 1),
              ("count", r"Finish all (\d+) items\.", 1)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(path: Path) -> str:
    """Repository-relative spelling when the path is inside the repository, absolute otherwise."""
    path = Path(os.path.abspath(path))
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def template_of(text: str, slots: list[tuple[str, str, int]]) -> tuple[str, dict[str, list[str]]]:
    """Replace each slot match in an archived prompt by `\\x00name\\x00`; return the template and the values."""
    values: dict[str, list[str]] = collections.defaultdict(list)
    for name, pattern, times in slots:
        matches = list(re.finditer(pattern, text))
        if len(matches) != times:
            raise ValueError(f"slot {name}: {len(matches)} matches of {pattern!r}, expected {times}")
        for match in reversed(matches):
            values[name].insert(0, match.group(1))
            text = text[:match.start(1)] + f"\x00{name}\x00" + text[match.end(1):]
    return text, dict(values)


def render(template: str, values: dict[str, str]) -> str:
    names = set(re.findall(r"\x00(\w+)\x00", template))
    if names != set(values):
        raise ValueError(f"slots {sorted(names)} but values {sorted(values)}")
    for name, value in values.items():
        template = template.replace(f"\x00{name}\x00", value)
    return template


def load_items(paths: list[Path]) -> list[dict]:
    items, seen = [], set()
    for path in paths:
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            missing = {"id", "wg", "family", "question", "fields", "gold"} - set(item)
            if missing:
                raise SystemExit(f"{path}: item without {sorted(missing)}")
            if item["id"] in seen:
                raise SystemExit(f"duplicate item id {item['id']}")
            seen.add(item["id"])
            items.append(item)
    return items


def dump_packet(packet: dict, newline: bool) -> str:
    return json.dumps(packet, ensure_ascii=False, indent=1) + ("\n" if newline else "")


def cypher_schema_from_archive(wg: str) -> str:
    """Recover the graph schema text from the archived packet task and prove the recovery by rebuilding the task."""
    archived = json.loads((ROOT / ARCHIVE["cypherPackets"] / f"{wg}_schema.json").read_text())["task"]
    sentinel = "\x00SCHEMA\x00"
    head, tail = rce.cypher_task({"fields": ["<the item's fields>"], "template": None}, sentinel).split(sentinel)
    if not (archived.startswith(head) and archived.endswith(tail)):
        raise SystemExit(f"{wg}: archived Cypher task does not have the cypher_task head and plain-template tail")
    schema = archived[len(head):len(archived) - len(tail)]
    if rce.cypher_task({"fields": ["<the item's fields>"], "template": None}, schema) != archived:
        raise SystemExit(f"{wg}: rebuilding the archived Cypher task from its schema text failed")
    return schema


def cypher_schema_from_bolt(wg: str) -> str:
    from neo4j import GraphDatabase
    from common.credentials import neo4j_auth
    # Port rule of execute_repeated_runs.sh bolt_of(): 7686 + working-group number.
    driver = GraphDatabase.driver(f"bolt://localhost:{7686 + int(wg[-1])}", auth=neo4j_auth())
    with driver.session() as session:
        schema = rce.graph_schema(session, False)
    driver.close()
    return schema


def query_writer_packets(by_wg: dict[str, list[dict]], out: Path, cypher_source: str, report: dict) -> dict:
    packets = {}
    for wg, items in sorted(by_wg.items()):
        templates = {item.get("template") in rce.SELF_RULED_TEMPLATES for item in items}
        if len(templates) > 1:
            raise SystemExit(f"{wg}: self-ruled and plain templates in one packet (run_chain_eval refuses this)")
        rce.item_ids(items)
        entries = [{"id": rce.packet_id(item), "question": item["question"], "fields": item["fields"]}
                   for item in rce.packet_order(items)]
        schema = cypher_schema_from_archive(wg) if cypher_source == "archive" else cypher_schema_from_bolt(wg)
        cypher = rce.cypher_task({"fields": ["<the item's fields>"],
                                  "template": items[0].get("template") if items else None}, schema)
        db = sqlite3.connect(f"file:{ROOT / SQLITE.format(wg=wg)}?mode=ro", uri=True)
        sql = rce.sql_task({"fields": ["<the item's fields>"]}, rce.sqlite_schema(db))
        db.close()
        for lang, task in (("cypher", cypher), ("sql", sql)):
            target = out / "query_writer" / lang / f"{wg}_schema.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(dump_packet({"task": task, "items": entries}, newline=True))
            archived = ROOT / ARCHIVE[f"{lang}Packets"] / f"{wg}_schema.json"
            same = archived.exists() and json.loads(archived.read_text())["task"] == task
            report["queryWriterPackets"].append({"wg": wg, "language": lang, "packet": rel(target),
                                                 "items": len(entries), "taskEqualsArchivedTask": same,
                                                 "taskSource": cypher_source if lang == "cypher" else "sqlite"})
            packets[(lang, wg)] = target
    return packets


def query_writer_prompts(by_wg, packets, args, out: Path, report: dict) -> None:
    for lang in LANGS:
        for wg, items in sorted(by_wg.items()):
            for run in args.query_runs:
                source = ROOT / ARCHIVE["queryWriterPrompts"] / f"{lang}_{wg}_run{run}.txt"
                if not source.exists():
                    source = ROOT / ARCHIVE["queryWriterPrompts"] / f"{lang}_{wg}_runA.txt"
                template, _ = template_of(source.read_text(), QUERY_SLOTS[lang])
                values = {"packet": str(Path(os.path.abspath(packets[(lang, wg)]))),
                          "output": str(Path(os.path.abspath(args.query_output_dir))
                                        / f"{wg}_{LANGS[lang]}_run{run}.jsonl")}
                if lang == "cypher":
                    values["count"] = str(len(items))
                else:
                    values["scratch"] = str(Path(os.path.abspath(args.sql_scratch_root))
                                            / f"sqlwriter_headroom_{wg}_{run}") + "/"
                target = out / "prompts" / "query_writer" / f"{lang}_{wg}_run{run}.txt"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(render(template, values))
                report["prompts"].append({"kind": "query_writer", "language": lang, "wg": wg, "run": run,
                                          "prompt": rel(target), "template": rel(source), "values": values})


def text_search_packets(item_paths: list[Path], items: list[dict], out: Path, report: dict) -> Path:
    target = out / "text_search"
    env = dict(os.environ, PYTHONPATH=f"scripts/common:{SCRIPTS}", PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([sys.executable, "-B", f"{SCRIPTS}/build_text_search_packets.py", "--items",
                    *[str(path) for path in item_paths], "--per-cell", str(TEXT_PER_CELL), "--seed", TEXT_SEED,
                    "--out-dir", str(target)], cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)
    sample = json.loads((target / "sample.json").read_text())
    kept = {identifier for ids in sample["byWg"].values() for identifier in ids}
    dropped = sorted({item["id"] for item in items} - kept)
    if dropped:
        raise SystemExit(f"text search: {len(dropped)} items not kept with --per-cell {TEXT_PER_CELL}: {dropped[:3]}")
    report["textSearch"] = {"builder": f"{SCRIPTS}/build_text_search_packets.py", "seed": TEXT_SEED,
                            "perCell": TEXT_PER_CELL, "kept": len(kept), "out": rel(target)}
    return target


def cut_parts(packet_dir: Path, args, report: dict) -> Path:
    parts_dir = packet_dir / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    report["parts"] = {"rule": ({"partsPerWg": args.parts_per_wg} if args.parts_per_wg
                                else {"maxPartSize": args.max_part_size}), "byPart": []}
    for source in sorted(packet_dir.glob("RAN*_packet.json")):
        wg = source.name.split("_")[0]
        packet = json.loads(source.read_text())
        entries = packet["items"]
        # Both rules cut consecutive slices of ceil(n / k) items, as the admitted set's parts were cut; they differ
        # only in k: fixed per working group, or the fewest parts whose size stays within --max-part-size.
        k_parts = args.parts_per_wg or math.ceil(len(entries) / args.max_part_size)
        size = math.ceil(len(entries) / k_parts)
        for k, start in enumerate(range(0, len(entries), max(size, 1)), start=1):
            chunk = entries[start:start + size]
            target = parts_dir / f"{wg}_part{k}.json"
            # Same bytes as the admitted set's parts: indent 1, no trailing newline.
            target.write_text(dump_packet({"task": packet["task"], "items": chunk}, newline=False))
            report["parts"]["byPart"].append({"part": target.stem, "wg": wg, "items": len(chunk)})
    return parts_dir


def text_search_prompts(parts_dir: Path, args, out: Path, report: dict) -> None:
    for part in sorted(parts_dir.glob("RAN*_part*.json"), key=lambda p: (p.name.split("_")[0], int(p.stem.split("part")[1]))):
        wg = part.name.split("_")[0]
        source = ROOT / ARCHIVE["textSearchPrompts"] / f"{wg}_part1.txt"
        template, _ = template_of(source.read_text(), TEXT_SLOTS)
        count = len(json.loads(part.read_text())["items"])
        for run in args.text_runs:
            base = Path(os.path.abspath(args.text_work_root)) / f"text_search_run{run}"
            work = base / f"work_{part.stem}"
            values = {"root": str(ROOT), "packet": rel(part), "count": str(count), "work": str(work),
                      "cmdlog": str(work / "cmdlog.jsonl"), "answers": str(base / f"{part.stem}_answers.jsonl"),
                      "wg": wg, "trace": str(base / f"{part.stem}_trace.jsonl")}
            target = out / "prompts" / "text_search" / f"run{run}" / f"{part.stem}.txt"
            target.parent.mkdir(parents=True, exist_ok=True)
            # The archived prompts end without a newline; render() keeps the template's ending.
            target.write_text(render(template, values))
            report["prompts"].append({"kind": "text_search", "wg": wg, "run": run, "part": part.stem,
                                      "prompt": rel(target), "template": rel(source), "values": values})


def dense_packets(parts_dir: Path, args, out: Path, report: dict) -> None:
    target = out / "dense"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([sys.executable, "-B", f"{SCRIPTS}/build_tool_condition_packets.py", "--parts", rel(parts_dir),
                    "--condition", "dense", "--runs", *args.dense_runs, "--out-dir", rel(target),
                    "--work-root", str(Path(os.path.abspath(args.dense_work_root)))],
                   cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)
    report["dense"] = {"builder": f"{SCRIPTS}/build_tool_condition_packets.py", "condition": "dense",
                       "runs": args.dense_runs, "out": rel(target),
                       "prompts": sorted(rel(p) for p in target.glob("run*/prompts/*.txt"))}


def leak_check(items: list[dict], out: Path) -> dict:
    """Find every gold and evidence value in the written packets and prompts and say what explains each hit."""
    files = sorted(p for p in out.rglob("*") if p.is_file() and p.suffix in (".json", ".txt")
                   and p.name not in ("build_manifest.json", "leak_check.json", "sample.json", "build_report.json"))
    texts = {rel(p): p.read_text() for p in files}
    key_problems = []
    tasks = []
    for name, text in texts.items():
        if not name.endswith(".json"):
            continue
        packet = json.loads(text)
        if set(packet) - {"task", "items"}:
            key_problems.append(f"{name}: top-level keys {sorted(set(packet))}")
        tasks.append(packet.get("task", ""))
        for entry in packet.get("items", []):
            extra = set(entry) - PACKET_ITEM_KEYS
            if extra:
                key_problems.append(f"{name}: item keys {sorted(extra)}")
    questions = {item["id"]: item["question"] for item in items}
    everything = "\n".join(texts.values())
    lowered = everything.lower()
    task_text = "\n".join(tasks)
    prompt_text = "\n".join(text for name, text in texts.items() if name.endswith(".txt"))

    def bounded(value: str) -> re.Pattern:
        return re.compile(r"(?<![A-Za-z0-9.#_-])" + re.escape(value) + r"(?![A-Za-z0-9#_]|\.\d|-[A-Za-z0-9])", re.I)

    counts = collections.Counter()
    explained = collections.defaultdict(collections.Counter)
    unexplained = []
    item_id_hits = [item["id"] for item in items if item["id"] in everything]
    for item in items:
        values = {("gold", str(cell).strip()) for row in item["gold"] for cell in row if cell is not None}
        for record in item.get("evidence") or []:
            if isinstance(record, dict):
                values |= {("evidence", str(v).strip()) for v in record.values()
                           if isinstance(v, (str, int, float)) and not isinstance(v, bool)}
        for kind, value in sorted(values):
            if not value:
                continue
            # Plain lower-case substring test first: most evidence values (hashes, paths, ids) are absent, and a
            # bounded regex over every written text for each of them would dominate the run time.
            if value.lower() not in lowered:
                counts[(kind, "absent")] += 1
                continue
            pattern = bounded(value)
            if not pattern.search(everything):
                counts[(kind, "absent")] += 1
            elif pattern.search(item["question"]):
                counts[(kind, "inOwnQuestion")] += 1
            elif pattern.search(task_text) or pattern.search(prompt_text):
                counts[(kind, "inTaskOrPromptText")] += 1
                explained[f"{kind}:inTaskOrPromptText"][value] += 1
            elif any(pattern.search(q) for i, q in questions.items() if i != item["id"]):
                counts[(kind, "inOtherQuestion")] += 1
                explained[f"{kind}:inOtherQuestion"][value] += 1
            else:
                counts[(kind, "unexplained")] += 1
                unexplained.append({"item": item["id"], "kind": kind, "value": value})
    return {"filesScanned": len(texts), "packetKeyProblems": key_problems, "itemIdsInPackets": item_id_hits,
            "valueOutcomes": {f"{kind}:{outcome}": n for (kind, outcome), n in sorted(counts.items())},
            "unexplained": unexplained,
            "explainedValues": {name: dict(values.most_common()) for name, values in sorted(explained.items())},
            "pass": not key_problems and not item_id_hits and not unexplained}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    rule = parser.add_mutually_exclusive_group(required=True)
    rule.add_argument("--parts-per-wg", type=int, help="text-search parts per working group, size ceil(n/K) "
                      "(the admitted set used 3: 37/47/47/47/46-item parts)")
    rule.add_argument("--max-part-size", type=int, help="largest text-search part; the fewest parts within it, "
                      "cut evenly (47, the admitted set's largest part, reproduces its 15 parts)")
    parser.add_argument("--query-output-dir", type=Path, default=Path(f"{TRACK}/final/next_cycle/headroom/solvers/"
                                                                     "query_writers/subagent_queries"))
    parser.add_argument("--sql-scratch-root", type=Path, required=True,
                        help="folder named in the SQL prompt for the session's generator script")
    parser.add_argument("--text-work-root", type=Path, required=True,
                        help="folder under which text-search sessions write work files, answers and traces")
    parser.add_argument("--dense-work-root", type=Path, required=True,
                        help="--work-root of build_tool_condition_packets.py")
    parser.add_argument("--cypher-task", choices=("archive", "bolt"), default="archive")
    parser.add_argument("--query-runs", nargs="+", default=list("ABCDE"))
    parser.add_argument("--text-runs", nargs="+", default=list("AB"))
    parser.add_argument("--dense-runs", nargs="+", default=list("AB"))
    args = parser.parse_args()

    items = load_items(args.items)
    by_wg: dict[str, list[dict]] = collections.defaultdict(list)
    for item in items:
        by_wg[item["wg"]].append(item)
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    report = {"items": [{"path": rel(p), "sha256": sha(p.read_bytes())} for p in args.items],
              "itemCount": len(items),
              "byWgFamily": {f"{wg}/{fam}": n for (wg, fam), n in
                             sorted(collections.Counter((i["wg"], i["family"]) for i in items).items())},
              "emptyGold": sum(not item["gold"] for item in items),
              "templates": sorted({str(item.get("template")) for item in items}),
              "queryWriterPackets": [], "prompts": []}
    packets = query_writer_packets(by_wg, out, args.cypher_task, report)
    query_writer_prompts(by_wg, packets, args, out, report)
    packet_dir = text_search_packets(args.items, items, out, report)
    parts_dir = cut_parts(packet_dir, args, report)
    text_search_prompts(parts_dir, args, out, report)
    dense_packets(parts_dir, args, out, report)
    leaks = leak_check(items, out)
    (out / "leak_check.json").write_text(json.dumps(leaks, ensure_ascii=False, indent=1) + "\n")
    report["leakCheck"] = {"pass": leaks["pass"], "valueOutcomes": leaks["valueOutcomes"]}
    report["files"] = {rel(p): sha(p.read_bytes()) for p in sorted(out.rglob("*"))
                       if p.is_file() and p.name != "build_manifest.json"}
    (out / "build_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({"items": len(items), "queryWriterPackets": len(report["queryWriterPackets"]),
                      "parts": len(report["parts"]["byPart"]), "prompts": len(report["prompts"]),
                      "densePrompts": len(report["dense"]["prompts"]), "leakCheck": leaks["pass"]}))
    if not leaks["pass"]:
        raise SystemExit("leak check failed; see leak_check.json")


if __name__ == "__main__":
    main()
