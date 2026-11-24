"""Measure which answer identifiers the raw chunk text carries for each question.

The text-only search route (`search_records_text.py --text-only`) sees only the chunk
body. A CR pack number can be found from a question only when some chunk body names it
next to an identifier the question gives. This script counts, per working group and
question family, the answerable questions whose gold CR pack numbers (RP-nnnnnn)

* appear in any chunk body (`anywhere`),
* appear in one chunk body together with the anchor TDoc number (`withAnchor`),
* appear in one chunk body together with the CR number the question states (`withCR`),
* appear together with that CR number and the specification number (`withCRandSpec`),

and records the collection of the first chunk that satisfies `withCRandSpec`. The
search uses the FTS5 `text` column only, the same column `--text-only` searches.
For every working group with a text-only answer file it then cross-tabulates exact
match against `withCRandSpec`.

Usage:
    python3 measure_text_only_cooccurrence.py [--out PATH]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sqlite3
from pathlib import Path

ROOT = next(path for path in Path(__file__).resolve().parents if (path / ".git").exists())
TRACK = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
ITEM_FILES = (TRACK / "integration/items_final/gate/core/chain_items_admitted.jsonl",
              TRACK / "integration/items_final/gate/ran5/chain_items_admitted.jsonl")
INDEX_DIR = TRACK / "text_route_ceiling/index"
DEFAULT_OUT = TRACK / "chain_eval/text_only_full/cooccurrence.json"
PACK = re.compile(r"RP-\d{6}")


def phrase(value: str) -> str:
    """FTS5 phrase for an identifier, split the way the unicode61 tokenizer splits it."""
    return '"' + " ".join(re.findall(r"[A-Za-z0-9]+", value)) + '"'


def first_hit(con: sqlite3.Connection, query: str) -> str | None:
    row = con.execute("select d.collection from search s join docs d on d.id = s.rowid "
                      "where search match ? limit 1", (query,)).fetchone()
    return row[0] if row else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    items = [json.loads(line) for path in ITEM_FILES for line in path.open()]
    cons: dict[str, sqlite3.Connection] = {}
    counts: dict[tuple[str, str], collections.Counter] = collections.defaultdict(collections.Counter)
    collections_hit: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    rows = []
    for item in items:
        if item["expectsEmpty"]:
            continue
        packs = sorted({cell for row in item["gold"] for cell in row
                        if isinstance(cell, str) and PACK.fullmatch(cell)})
        key = (item["wg"], item["family"])
        counts[key]["answerable"] += 1
        if not packs:
            continue
        wg = item["wg"]
        if wg not in cons:
            cons[wg] = sqlite3.connect(f"file:{INDEX_DIR / (wg.lower() + '.sqlite3')}?mode=ro", uri=True)
        con = cons[wg]
        anchor = item["anchor"].split(":", 1)[1]
        cr = re.search(r"CR (\d{3,4})\b", item["question"])
        spec = re.search(r"TS (\d{2}\.\d{3})", item["question"])
        row = {"id": item["id"], "packs": packs}
        row["anywhere"] = all(first_hit(con, f"text : {phrase(p)}") for p in packs)
        row["withAnchor"] = all(first_hit(con, f"text : {phrase(p)} AND text : {phrase(anchor)}")
                                for p in packs)
        counts[key]["withPack"] += 1
        counts[key]["anywhere"] += row["anywhere"]
        counts[key]["withAnchor"] += row["withAnchor"]
        if cr:
            counts[key]["questionStatesCR"] += 1
            row["withCR"] = all(first_hit(con, f'text : {phrase(p)} AND text : "{cr.group(1)}"') for p in packs)
            counts[key]["withCR"] += row["withCR"]
            if spec:
                hits = [first_hit(con, f'text : {phrase(p)} AND text : "{cr.group(1)}" AND text : {phrase(spec.group(1))}')
                        for p in packs]
                row["withCRandSpec"] = all(hits)
                counts[key]["withCRandSpec"] += row["withCRandSpec"]
                if row["withCRandSpec"]:
                    collections_hit[wg][hits[0]] += 1
        rows.append(row)

    by_wg: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for (wg, _family), counter in counts.items():
        by_wg[wg].update(counter)

    # Cross-tabulate the text-only answers with `withCRandSpec` for the questions that state a CR number.
    from score_chain_eval import score
    by_id = {item["id"]: item for item in items}
    flags = {row["id"]: row.get("withCRandSpec") for row in rows}
    crosstab: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for wg in sorted({item["wg"] for item in items}):
        responses = TRACK / f"chain_eval/text_only_full/{wg}_text_search_text_only_claude_subagent.jsonl"
        if not responses.exists():
            continue
        for line in responses.open():
            response = json.loads(line)
            item = by_id[response["id"]]
            flag = flags.get(item["id"])
            if item["expectsEmpty"] or flag is None:
                continue
            exact = bool(response.get("rows") is not None and score(item["gold"], response["rows"])["exact"])
            crosstab[wg][f"cooccurs={flag}|exact={exact}"] += 1
    result = {
        "indexDir": str(INDEX_DIR.relative_to(ROOT)),
        "itemFiles": [str(path.relative_to(ROOT)) for path in ITEM_FILES],
        "searchedColumn": "text",
        "byWg": {wg: dict(counter) for wg, counter in sorted(by_wg.items())},
        "byWgFamily": {f"{wg}|{family}": dict(counter) for (wg, family), counter in sorted(counts.items())},
        "withCRandSpecFirstChunkCollection": {wg: dict(c) for wg, c in sorted(collections_hit.items())},
        "textOnlyExactByCooccurrence": {wg: dict(c) for wg, c in sorted(crosstab.items())},
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result["byWg"], indent=1))
    print(json.dumps(result["withCRandSpecFirstChunkCollection"], indent=1))
    print(json.dumps(result["textOnlyExactByCooccurrence"], indent=1))


if __name__ == "__main__":
    main()
