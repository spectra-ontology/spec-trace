"""Score responses with and without the electronic-meeting `-e` suffix on meeting cells.

The 3GPP CR database writes an electronic plenary as `RAN#97-e`; the benchmark gold
writes the same meeting as `RAN#97`. This script reports, next to the exact match of
`score_chain_eval.py`, a secondary match in which a trailing `-e` is removed from every
`tsg_meeting` and `wg_meeting` cell on both sides after `cell_key()`. All other cells are
compared exactly as `score_chain_eval.py` compares them.

Usage:
    python3 score_meeting_suffix_insensitive.py --items ITEMS... --responses RESP... --out OUT
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

from score_chain_eval import cell_key

E_SUFFIX = re.compile(r"-e$")
MEETING_FIELDS = {"tsg_meeting", "wg_meeting"}


def row_key(fields: list[str], row, strip: bool) -> tuple[str, ...]:
    cells = []
    for index, cell in enumerate(row):
        value = cell_key(cell)
        if strip and index < len(fields) and fields[index] in MEETING_FIELDS:
            value = E_SUFFIX.sub("", value)
        cells.append(value)
    return tuple(cells)


def matches(item: dict, rows, strip: bool) -> bool:
    if rows is None:
        return False
    return ({row_key(item["fields"], row, strip) for row in item["gold"]}
            == {row_key(item["fields"], row, strip) for row in rows})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--items", nargs="+", type=Path, required=True)
    parser.add_argument("--responses", nargs="+", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    items = {}
    for path in args.items:
        for line in path.open():
            item = json.loads(line)
            items[item["id"]] = item
    table: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    seen = set()
    for path in args.responses:
        for line in path.open():
            response = json.loads(line)
            item = items[response["id"]]
            seen.add(item["id"])
            rows = response.get("rows")
            exact = matches(item, rows, strip=False)
            relaxed = matches(item, rows, strip=True)
            scope = "empty" if item["expectsEmpty"] else "answerable"
            for key in ("all", f"wg:{item['wg']}", f"family:{item['family']}", f"scope:{scope}"):
                table[key]["n"] += 1
                table[key]["exact"] += exact
                table[key]["meetingSuffixInsensitive"] += relaxed
    result = {
        "rule": "trailing '-e' removed from tsg_meeting and wg_meeting cells on both sides after cell_key()",
        "items": [str(path) for path in args.items],
        "responses": [str(path) for path in args.responses],
        "missingResponses": len(set(items) - seen),
        "groups": {key: dict(counter) for key, counter in sorted(table.items())},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result["groups"], indent=1))


if __name__ == "__main__":
    main()
