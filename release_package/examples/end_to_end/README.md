# SPECTRA end-to-end example

A small synthetic traceability scenario, runnable against an in-memory rdflib graph (Python) or a Neo4j instance loaded with the `data.cypher` script. Use this to verify that your toolchain understands the SPECTRA schema before instantiating it against your own data.

## Files

| File | Purpose |
|---|---|
| `data.ttl` | Synthetic instances expressed in Turtle (extends `examples/instantiation_snippet.ttl` with one full traceability scenario) |
| `data.cypher` | Same instances as Cypher CREATE statements for Neo4j |
| `query.cypher` | Query returning a referenced TDoc through the synthetic meeting-context and promotion joins |
| `query.sparql` | Same query in SPARQL |
| `expected_output.txt` | Result row(s) the query should return when run on `data.ttl` / `data.cypher` |

## Scenario

A fictional company submits a TDoc to RAN1#120 proposing a tweak to the
PDSCH definition. The meeting agrees the proposal as a working assumption,
which is later promoted to an Agreement at RAN1#121. A CR (R1-2599999)
implementing the agreed change is approved and modifies TS 38.214 §5.1.3.

The end-to-end example records this lifecycle and provides the query that
returns the TDoc referenced by a WorkingAssumption linked to an Agreement
at the CR's meeting, starting from the affected TS section. The lifecycle
is fictional; the query joins the Agreement and CR through meeting context,
not a direct evidence link showing which contribution caused the clause change.

## Scenario coverage (paper §6.5)

This synthetic example exercises:

- **S1 Multi-hop traceability illustration** — a TDoc/Resolution path
  associated with the CR/Section path through a shared Meeting.
- **S4 Working Assumption promotion illustration** —
  `WA_120_PTRS promotedTo Agreement_121_PTRS` is synthetic. The property
  is unpopulated in the released and deployed corpus snapshots.
- **S3 Release-scoped CR analytics** — partial (CR with `targetRelease` and `submittedBy`).

The metadata-only `examples/real_world_mini/` example complements this with **S2 Cross-WG LS** (a Liaison Statement from RAN1 to RAN2). **S5 TR-to-TS impact** is exercised at the schema level (TRImpact class + `hasTRImpact`/`impactsSection` properties declared in `ontology/spectra.ttl`); a runnable TR-impact instantiation is illustrated by the Cypher pattern in `queries/cypher/MULTI_HOP_traceability.cypher`.

## How to run

### Python (rdflib + SHACL)
```bash
pip install rdflib pyshacl
python3 - <<'PY'
import rdflib
g = rdflib.Graph()
g.parse('../../ontology/spectra.ttl', format='turtle')
g.parse('data.ttl', format='turtle')
print(f"Total triples (ontology + data): {len(g)}")

# Validate against SHACL shapes
from pyshacl import validate
ok, _, msg = validate(g, shacl_graph=rdflib.Graph().parse('../../shapes/spectra-core.shacl.ttl'))
print(f"SHACL conforms: {ok}")

# Run the SPARQL query
results = list(g.query(open('query.sparql').read()))
print(f"SPARQL result rows: {len(results)}")
for r in results: print(r)
PY
```

### Neo4j
```bash
# In a Neo4j browser or cypher-shell:
:source data.cypher
:source query.cypher
```

## Expected output

See `expected_output.txt`.
