# Source-enriched RAN3 graph experiment

This bundle reproduces an additive source repair for the original question
`RAN3_P4_CQ2-3`: “List CRs that name spec 38.473 as an affected spec (incoming
cross-spec impact).” It is a separate graph experiment. It adds **zero**
validated questions to the original 560-question frozen-graph benchmark.
The original frozen graph remains unchanged and source-disproved for this
question. No model improvement is claimed by this source bundle.

The exact authored query retains both return columns, the three affected-spec
roles, `tdocNumber DESC`, and `LIMIT 10`. The requested-field contract requires
the CR identity, `tdocNumber`, as a set of exactly ten strings. Both original
query columns are nevertheless retained in the recorded independent SQL and
native comparisons. Copied `summaryOfChange` prose is not source-certified.
Two separate AI judgments cover seven semantic units each; neither is human
author or expert endorsement. Their original opposing interpretations remain
in `reviews/`.

## Source evidence and bounded completeness

The original frozen population contains 19,974 CR identities. All 38 CRs at or
above the original tenth-result lexical boundary have their own original cover
reopened from six preserved ZIP archives, including negative cases. All 114
own affected-role fields are checked. The parser inserts token boundaries only
inside identified affected-role cells, so `TS38.473CR 1676` names spec 38.473.
It does not infer an affected specification from normative body text, a
modified-spec field, an unrelated cover, deleted text, or a different CR's
approval. In particular, a CR modifying 38.423 and naming 38.473 as affected
retains these distinct roles.

Reparsing all three roles across the complete tail derives 48 source role
edges, compared with 46 existing role edges: exactly two additions and no
removals. No answer-ID whitelist is used to construct these additions. The
full baseline has 87,980 nodes and 481,498 edges; the separate graph retains
every original label, property, identity and edge and has 481,500 edges. All
matching Spec nodes remain included in original-query execution. The canonical
new-edge target follows the original schema's abstract Spec hub and original
JSON-LD identity rule. The older indexed native linker used number-only Spec
matching; its ambiguity and the rejected missing-hub-ID attempt are retained
in `history/`. This repair is not described as execution of that linker
unchanged.

The completeness proof covers the selected prefix within the entire frozen
CR population. It does not certify older source fields, all unobserved external
CRs, present-day approval, or standards incorporation. Recorded source URLs
and metadata rows are in `source/original_recorded_source_URL_attribution.json`.
They attribute the preserved archives; URL reachability was not remeasured.
Blank recorded FTP fields remain blank. Original source rights and attribution
remain with 3GPP and the contributing authors.

## Verify the portable source bundle

Use Python 3 with `lxml` installed. All default inputs are relative to this
directory. There is no network, API, model, database or Neo4j operation in the
default verifier.

```sh
python3 -B -I verify_portable.py
```

Four additional controls corrupt the question hash, own-source identity,
required role and source delta in temporary copies, repin the internal
manifest, and require semantic or binding rejection:

```sh
python3 -B -I negative_controls.py --receipt /path/to/new-negative-receipt.json
```

The verifier checks every bundled file pin, original English/query bytes,
both seven-unit review records, original-function lineage, all six archives,
38 DOCX member/XML/style identities, every own affected-role field and source
position, the full 19,974-identity bound, all-role edge difference, the selected
prefix and 24 lexical/structural controls. The review-schema check validates
the review record, not the truth of an AI's semantic judgment. Full baseline
reparsing is an optional additional check:

```sh
python3 -B -I verify_portable.py --base-ttl /path/to/RAN3-body.ttl
```

The required existing public baseline SHA-256 is
`d9791c08773a0e38b89869b3882d3098d879a37ddd7109630c346200d6776e95`.
The exact public Turtle lexer is bundled. The baseline Turtle and generated
Turtle/SQLite/FTS copies are intentionally not duplicated in this bundle.

## Rebuild separate full-graph artifacts

Each output directory must be new. The first command only reads the baseline
and source archives and writes a separate Turtle artifact. It reopens all
source fields, reparses the entire original graph, derives the additions,
checks all original facts, and reproduces the pinned enriched graph hash.

```sh
python3 -B -I recipes/graph_source_recipe.py ttl \
  --base-ttl /path/to/RAN3-body.ttl --output /path/to/new-ttl-stage
```

Expected enriched Turtle SHA-256:
`5fac3bb2adf9f8ea5ac632700a9bebaf9c753c90e388783f82ad10c6dface589`.
For an optional separate SQLite clone, use the existing original database
with SHA-256
`ff55fe57ee9435c25b59e1d90c5ee09ee0ff167696c4afeb05f21e367f4c6a29`:

```sh
python3 -B -I recipes/graph_source_recipe.py sqlite \
  --base-db /path/to/original-RAN3.sqlite \
  --ttl-stage /path/to/new-ttl-stage --output /path/to/new-sqlite-stage
```

The clone recipe preserves the source database, compares all table schemas
and original rows, adds the two derived edges, and executes both original
return columns. Native read-only execution is recorded in `proof/`; the
portable verifier does not start a database or re-execute native queries.

The generic retrieval corpus is rebuilt from the entire enriched graph. It
does not ingest a question, query, target filter, positive-ID list, answer
fixture, raw cover or source-prefix fixture. Every node label/property and
directed edge is serialized in deterministic node order. Large documents use
4,000-character chunks and a 200-character overlap without losing text.

```sh
python3 -B -I recipes/build_generic_graph_corpus.py build \
  --ttl /path/to/new-ttl-stage/RAN3-source-enriched-full.ttl \
  --ttl-sha256 5fac3bb2adf9f8ea5ac632700a9bebaf9c753c90e388783f82ad10c6dface589 \
  --lexer runtime/load_released_kg.py --output /path/to/new-corpus-stage
python3 -B -I recipes/build_generic_graph_corpus.py verify \
  --ttl /path/to/new-ttl-stage/RAN3-source-enriched-full.ttl \
  --ttl-sha256 5fac3bb2adf9f8ea5ac632700a9bebaf9c753c90e388783f82ad10c6dface589 \
  --lexer runtime/load_released_kg.py --output /path/to/new-corpus-stage
```

The recorded corpus contains 87,980 node documents, 147,393 chunks and all
481,500 directed edges. It uses a new FTS corpus, not the previous retrieval
cache. The separate evaluation protocol caps candidates at 160 and context
at twelve 4,000-character chunks, 48,000 characters total. The recorded
fact-reconstruction and independent root checks are retained. Corpus
reconstruction and retrieval performance are distinct checks.

The separate evaluation package retains the first paid responses, failures,
cost accounting and infrastructure-only supplemental run. This source
bundle neither replaces those records nor pools them with the frozen-graph
cohort. No evaluation or paid call is performed by these replay commands.
