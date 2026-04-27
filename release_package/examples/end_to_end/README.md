# SPECTRA end-to-end example

A small synthetic 4-hop traceability scenario, fully runnable against an in-memory rdflib graph (Python) or any Neo4j instance loaded with the `data.cypher` script. Use this to verify that your toolchain understands the SPECTRA schema before instantiating it against your own data.

## Files

| File | Purpose |
|---|---|
| `data.ttl` | Synthetic instances expressed in Turtle (extends `examples/instantiation_snippet.ttl` with one full traceability scenario) |
| `data.cypher` | Same instances as Cypher CREATE statements for Neo4j |
| `query.cypher` | Multi-hop traceability query that recovers the originating TDoc from a TS section |
| `query.sparql` | Same query in SPARQL |
| `expected_output.txt` | Result row(s) the query should return when run on `data.ttl` / `data.cypher` |

## Scenario

A fictional company submits a TDoc to RAN1#120 proposing a tweak to the
PDSCH definition. The meeting agrees the proposal as a working assumption,
which is later promoted to an Agreement at RAN1#121. A CR (R1-2599999)
implementing the agreed change is approved and modifies TS 38.214 §5.1.3.

The end-to-end example records this lifecycle and provides the query that
recovers the originating TDoc when starting from the affected TS section.

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
