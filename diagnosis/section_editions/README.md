# Clause-link edition census

A change request (CR) records its target release. A linked Section identifies
the indexed edition that supplies the affected-clause label. The common
[Section resolver](../../code/scripts/tsg/RAN/formal/common/phase-4/cr_section_index.py)
prefers the requested edition for the same specification and clause label, then
the latest indexed edition at or before it, then the latest available edition
with that label. An unknown target starts with the latest indexed release.
The RAN5 [loader](../../code/scripts/tsg/RAN/formal/RAN5/phase-4/neo4j/01_load_cr_ontology.py)
records the relation and its inverse. The original CR target release remains
the field to use for the release that a CR targets.

The census compares `document.target_release` with `section.release` for each
row in the released `cr_modifies_section` table. It counts missing endpoint rows
before comparing releases and reports missing release fields for joined rows.
In this snapshot the 259 unjoined links have Section rows and lack document
rows in the SQLite projection. The 352 joined links with an unrecorded release
have a NULL CR target release in RAN4.

| Working group | Stored links | No document row | Joined links | Same release | Different release | Release unrecorded |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| RAN1 | 6,141 | 61 | 6,080 | 6,076 | 4 | 0 |
| RAN2 | 12,732 | 0 | 12,732 | 12,729 | 3 | 0 |
| RAN3 | 10,064 | 46 | 10,018 | 9,928 | 90 | 0 |
| RAN4 | 38,102 | 0 | 38,102 | 37,578 | 172 | 352 |
| RAN5 | 38,324 | 152 | 38,172 | 16,394 | 21,778 | 0 |
| Total | 105,363 | 259 | 105,104 | 82,705 | 22,047 | 352 |

The [source-link audit](../../restore/source_links/README.md) measures
agreement with the specification and affected-clause label recorded in CR
forms. That audit reports 104,125 of 105,363 links. The edition census measures
agreement between two stored release fields and has 105,104 joined links.
The released links carry the chosen Section identifier. Release comparison
uses these stored endpoints and does not reconstruct resolver branch history.

From the release root, run the following command to reproduce [the receipt](receipt.json).

```sh
python3 -B diagnosis/section_editions/audit.py --check diagnosis/section_editions/receipt.json
```

The standard-library script verifies the shipped SQLite archives and unpacked
databases against `sqlite/SHA256SUMS.txt`. It opens the pinned SQLite inputs in
read-only mode, decompresses each archive into a temporary directory in turn
and prints the counts as JSON.
