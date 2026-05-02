# Stage 05 — Neo4j Bulk Load

Loads SPECTRA JSON-LD records (Stage 02/03 output, post Stage 04 SHACL
validation) into a Neo4j knowledge graph via parallel Cypher `CREATE`.

| Script | Inputs | Output |
| --- | --- | --- |
| `load_neo4j.py` | Stage 02/03 JSON-LD + Neo4j connection params | populated Neo4j graph; per-batch run log |

## Behaviour

* Reads SPECTRA JSON-LD records from one or more files.
* Maps each `@type` (e.g., `spectra:Tdoc`, `spectra:CR`, `spectra:Resolution`,
  `spectra:Section`, `spectra:TRImpact`) to a Neo4j label.
* Maps SPECTRA object properties (e.g., `spectra:submittedBy`,
  `spectra:references`, `spectra:modifiesSection`) to Neo4j relationship
  types (camelCase preserved for ontology↔Cypher correspondence —
  see paper Table 8 caption).
* Bulk loads via parallel UNWIND batches; respects SPECTRA functional
  property declarations to detect ingest-time uniqueness violations.

## Sanitization scope

* Internal Slack/incident hooks, Samsung-internal Neo4j hostnames, and
  hard-coded credentials are removed. Connection params are taken from
  CLI arguments or environment variables (`NEO4J_URI`, `NEO4J_USER`,
  `NEO4J_PASSWORD`).
* Parallel-load mechanism preserved.

## Usage

```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=<your-password>

python load_neo4j.py \
    --jsonld out/02_metadata_parse/tdocs.jsonld out/02_metadata_parse/resolutions.jsonld \
              out/03_document_parse/cr_bodies.jsonld out/03_document_parse/tr_bodies.jsonld \
    --batch-size 1000 \
    --workers 4
```

The script does **not** drop the database; it idempotently `MERGE`s nodes
on the SPECTRA functional properties (e.g., `spectra:tdocNumber` for
`Tdoc`) so re-runs are safe.

## Dependencies

`neo4j>=5.18.0` (see top-level `requirements.txt`).
