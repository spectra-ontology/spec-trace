# Executable competency queries

The CQ contract provides 25 authored definition files containing 654 executable
questions, their declared row and value assertions, the ontology-backed guard,
and bindings to the 25 preserved execution receipts. Definitions retain their
original bytes, including question wording used by the approval guard.

Run input verification from the release root with Python 3.10 or later:

```bash
python3 -B restore/competency_queries/runner.py --release . --mode verify
```

Verification checks every artifact digest, all 654 composite CQ identities,
question and query digests, expected assertions, historical outcomes, and the
recorded query or dataset bindings. The historical receipts contain 149 query
texts and three dataset digest prefixes. The contract records those matches and
identifies the remaining unrecorded bindings. Current definition files provide
the complete executable input set.

`definition_contract.json` identifies the authored definitions, complete question
records, guard and ontology independently of package metadata. Each graph view's
`definition_binding.json` links its preserved snapshot manifest to that input
contract and checks every captured query hash. This binding records a
post-capture input comparison. The snapshot's original `cq_contract_sha256`
records its capture-time package metadata; the standalone definition contract
supplies the executable input identity.

For a new execution, install `neo4j==5.28.3` and `rdflib==7.6.0`. The supplied
adversarial regression checks cover definition omissions, guard and assertion
edits, coherently repinned query changes, typed properties and empty-row rules:

```bash
python3 -B restore/competency_queries/test_contract.py --release .
```

Then provide connection details
for the explicitly selected full process graphs. For example, `connections.json`
may contain an entry for a scratch graph:

```json
{
  "RAN4": {
    "uri": "bolt://localhost:17687",
    "user": "neo4j",
    "password_env": "SPECTRA_CQ_PASSWORD",
    "database": "neo4j"
  }
}
```

Set that environment variable using your local credential manager, then run:

```bash
python3 -B restore/competency_queries/runner.py --release . --mode run \
  --connections connections.json --working-group RAN4 \
  --graph-identity 'scratch graph restored from the supplied snapshot manifest' \
  --out cq-fresh-execution.json
```

Omit `--working-group` to execute all five groups with five connection entries.
The runner uses read access and rolls back each CQ transaction after its guard
checks. Each output identifies fresh results separately from the historical
statuses, records minimum-row checks and guard defects, and reports whether all
654 questions executed. Exit codes are 0 for completed operational checks,
1 for query/guard/minimum failures, and 2 for input or contract errors.

The input graph for these questions covers phase 1–5 process records, including
companies, contacts, agenda items, work items, TS/TR structure and domain
entities. The chain-question benchmark's query projection has a separate
scope. `contract.json` records the restoration status for the original CQ graph;
a fresh execution identifies its own graph input. Prose `expected`, claim,
reference and approval annotations accompany the executable checks and remain
available for interpretation.

## Restoring the CQ graph view

`graph_snapshot.py` retains every node, label and relationship occurrence of
each process graph. Its dependency manifest lists the properties consumed by
all 654 questions and by their guards. Report passages used through `content`
and `contentWithEquations` are preserved for the Resolution class family.
Other graph properties follow the explicit whitelist. The dependency gate checks
dynamic property access, whole-property reads and whole-entity returns before
capture. The one CQ using relative native node IDs is supported by preserving
and checking the complete source node order during restoration. The pinned
Neo4j 5.26.0 restore also reproduces and checks every observed ordered
`labels(n)` population signature. These signatures retain the label sequences
consumed by the original queries.

Capture uses sequential read transactions, two complete projected-content
fingerprints, and population/schema inventories before and after the reads.
The snapshot records the checked consistency conditions. Gzip shards each
remain below 50 MB; their byte hashes and logical record fingerprints are pinned
by the snapshot manifest. Temporal, spatial, byte and numeric property types
use explicit tags, with unsupported values causing capture to fail.

Restore a selected snapshot into a dedicated empty Neo4j 5.26.0 database:

```bash
python3 -B restore/competency_queries/graph_snapshot.py --release . \
  --mode restore --connections connections.json --working-group RAN4 \
  --snapshot sources/competency_queries/graph_view/RAN4 \
  --output cq-restore-receipts --confirm-empty-target
```

The target must contain zero nodes and relationships. Restoration verifies the
selected manifest's definition binding, recomputes the query/guard dependency
projection, verifies every input shard, and rebuilds the source structure. It
then fingerprints the actual restored nodes and edges, checks relative node ID
order and ordered-label populations, and records final counts. Repeat the
procedure for each working group using a dedicated empty target.

`schema_token_observations.json` supplies repeated source `EXPLAIN` observations
for the names referenced by the questions. It includes source-known labels and
relationship types with empty current populations. Restoration creates those
tokens and checks all recorded known/unknown outcomes after removing its
temporary records. The definition sidecar pins these observations as part of
the executable input contract.

Run the CQ runner against that graph, then compare its receipt with a separately
executed source-graph receipt:

```bash
python3 -B restore/competency_queries/compare_executions.py \
  --source cq-source.json --restored cq-fresh-execution.json \
  --out cq-comparison.json
```

The comparison reports query identity, statuses, row counts, minimum checks,
guard defects, row multiset hashes and ordered-row hashes separately. Queries
with a `LIMIT` across equal sort keys or an unordered `collect()` sample can
produce different valid selections. The strict comparison retains each actual
hash difference for inspection against the unchanged query and observed rows.
Neo4j documents [row ordering and collection order](https://neo4j.com/docs/cypher-manual/5/clauses/order-by/)
and [the implementation-dependent order of `labels()`](https://neo4j.com/docs/cypher-manual/5/functions/list/#functions-labels).

Report text in the view is source-derived; the release's source provenance and
rights records apply.
