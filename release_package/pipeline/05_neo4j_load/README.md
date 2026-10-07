# Stage 05 — JSON-LD Loader

Loads supported SPECTRA JSON-LD records using per-record Cypher `MERGE`
operations dispatched by a thread pool. To restore the deposited body-text
graphs for benchmark replay, use [load_released_kg.py](../load_released_kg.py).
That separate TTL loader preserves the deposited node IRIs, multiple labels,
literal properties and escaped relationship types. Its use is described in
the [isolated restoration guide](../../cqs/contract_repair_v1/README_frozen_ttl_import.md).

| Script | Inputs | Output |
| --- | --- | --- |
| `load_neo4j.py` | Stage 02/03 JSON-LD + Neo4j connection params | populated Neo4j graph; per-batch run log |

## Behaviour

* Reads SPECTRA JSON-LD records from one or more files.
* Maps the single expanded `@type` values listed in `TYPE_TO_LABEL` to
  labels. Unknown types are skipped. The generic `Resolution` type is not
  in that map; Agreement, Conclusion and WorkingAssumption are supported.
* Maps SPECTRA object properties (e.g., `spectra:submittedBy`,
  `spectra:references`, `spectra:modifiesSection`) to Neo4j relationship
  types in upper snake case.
* `--batch-size` bounds the buffer of submitted record jobs. The script
  does not use `UNWIND` batches or implement an OWL functional-property
  violation detector.
* Attempts edges when each source record is loaded. A target that is not
  yet present can therefore leave an edge unmatched. This script has not
  been certified to reconstruct the deposited benchmark graph.

## Sanitization scope

* Internal Slack/incident hooks, Samsung-internal Neo4j hostnames, and
  hard-coded credentials are removed. Connection params are taken from
  CLI arguments or environment variables (`NEO4J_URI`, `NEO4J_USER`,
  `NEO4J_PASSWORD`).
* Worker count is controlled by `--workers`.

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

The script does not drop the database. Node `MERGE` keys include the IRI
and, for some labels, a property value; changed values can therefore
create a different match. Test new source ingestion in a separate store.

## Dependencies

`neo4j>=5.18.0` (see top-level `requirements.txt`).
