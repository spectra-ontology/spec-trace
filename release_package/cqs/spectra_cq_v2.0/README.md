# SpectraCQ v2.0 — Scored Competency-Question Benchmark for the SPECTRA KG

SpectraCQ packages the competency questions (CQs) authored to design and
validate the SPECTRA ontology across all five 3GPP RAN working groups, now
released as a **scored benchmark**: each released CQ pairs a natural-language
question with an executable Cypher reference query and a **deterministic gold
answer set** obtained by executing that query against the released per-WG
knowledge graphs. No LLM and no human annotation is in the gold path.

Canonical counts for every number below: `../../MANIFEST.md`.

## Benchmark composition

| WG | Authored | Released (scored) | Held-out |
|----|---------:|------------------:|---------:|
| RAN1 | 145 | 142 | 3 |
| RAN2 | 132 | 128 | 4 |
| RAN3 | 129 | 123 | 6 |
| RAN4 | 125 | 117 | 8 |
| RAN5 | 123 | 114 | 9 |
| **Total** | **654** | **624** | **30** |

Released CQs by design phase:

| Phase | Domain | Released CQs |
|-------|---------------------|-------------:|
| P1 | TDoc metadata | 123 |
| P2 | Meeting resolutions | 112 |
| P3 | TS structure | 233 |
| P4 | CR documents | 75 |
| P5 | Technical Reports | 81 |
| **Total** | | **624** |

The 30 held-out CQs are those whose gold answer against the current graph is
empty or uniformly zero/false; they are excluded from scoring to avoid
degenerate set-comparison and shipped under `held/` with their Cypher and
status.

## Gold answer definition

Each released CQ's gold is the **set of values in the first RETURN column**
obtained by executing its reference Cypher against the released graph, plus a
row count. Reference queries whose ranking is truncated by `LIMIT` carry a
data-intrinsic tie-break so the top-k set is reload-stable. Reproducibility
evidence (scratch-reload self-replay, 624/624 gold match) lives at
`../../validation/cq_replay/ran{1..5}_replay_results.json`.

## Distribution

- `questions.json` — 624 released CQ entries: `{id, wg, phase, category,
  question_en, schema_area, cypher_file, gold_file, gold}`, where `gold`
  carries the answer-set summary (`status`, `row_count`, `columns`,
  `primary_column`, preview of primary values).
- `benchmark.jsonl` — the scored benchmark, one JSON object per line
  (624 rows): question + gold answer set + row count.
- `answer_contract.jsonl` — one line per SpectraCQ-Core item (a `_header`
  line plus 560 items): the graded `answer_type` and `answer_columns`, the
  `ordering_key` and `cardinality` read from the clauses that govern the
  reference query's final `RETURN` (null where none is imposed), and a
  `contract_disposition` recording what would have to change for the item
  to hold exactly as asked.
- `splits/` — the four canonical splits as identifier lists, with their
  per-track and per-group composition, the leakage audit, and a
  deterministic rebuild script. See `splits/README.md`.
- `cypher/{WG}_P{phase}_{id}.cypher` — 624 executable Cypher reference
  queries (one per released CQ).
- `sparql/P{phase}_{id}.rq` — 142 SPARQL translations covering **all
  released RAN1 CQs** (translated from the reference Cypher; each carries
  the CQ text and a pointer to its Cypher source, and parses under rdflib).
  Class-membership guards default to `FILTER EXISTS` so greedy join
  planners do not form class-enumeration cross products; positive
  `rdf:type` triples are used where the type pattern is itself the
  query, is anchored to a constant, or (with an engine note in the
  query) replaces a pattern rdflib evaluates too slowly. Row-count
  parity against the Cypher replay: 142/142 match
  (`../../validation/cq_replay/sparql_parity_results.json`). The 142 is
  the RAN1 portability slice, distinct from the 624-query full Cypher
  benchmark (see `../../MANIFEST.md` §2.1).
- `gold/RAN{1..5}_gold.json` — gold answer sets for all 654 authored CQs
  (the authored superset is kept intact), plus `gold/_gold_summary.json`
  recording the 654 / 624 / 30 split.
- `held/held_cqs.json` — the 30 held-out CQs with Cypher and status.
- `croissant.json` — Croissant ML dataset metadata.
- `CITATION.cff` / `citation.bib` — citation metadata.
- `LICENSE` — CC-BY 4.0.

## Company-name policy

The 49 of the 624 released reference queries that mention companies retain
the **verbatim** public 3GPP identifiers (Huawei, Samsung, Qualcomm, ...) as
they appear on the public per-meeting `TDOC_List.xlsx`. The other 575
reference queries name no specific company. The legacy mapping is
intentionally not published in v1.0.

## How to use

```bash
# Inspect questions
jq '.cqs[0]' questions.json

# Inspect one scored benchmark row
head -1 benchmark.jsonl | jq .

# Run a single CQ against a SPECTRA-conformant Neo4j (example: RAN1 P1 CQ1-1)
cypher-shell -u neo4j -p <pass> < cypher/RAN1_P1_CQ1-1.cypher

# Run a SPARQL translation against the released RDF (rdflib; RAN1 subset)
python3 -c "import rdflib; g=rdflib.Graph(); g.parse('../../kg/per_wg/RAN1-body.ttl');
print(len(list(g.query(open('sparql/P1_CQ1-1.rq').read()))))"
```

Scoring convention: compare a system's predicted answer set against the gold
set (`benchmark.jsonl`) over the primary column with set-level exact match
and set precision / recall / F1 on normalised values.

## Companion releases

- SPECTRA OWL ontology (this benchmark's schema): https://w3id.org/spectra
- Paper: "SPECTRA: A Traceability Ontology for the 3GPP RAN Standardization
  Process" (currently under review).

## Citation

See `CITATION.cff` / `citation.bib`. The 624-CQ scored benchmark is **not yet
deposited** on Zenodo; no DOI should be cited for it until a public record is
minted (the existing SPECTRA DOI identifies the prior ontology-centric
release — see `../../MANIFEST.md` §5).

## License

CC-BY 4.0. You are free to share and adapt; please cite.
