# Stage 04 — SHACL Validate

Validates Stage 02/03 JSON-LD records against the SPECTRA SHACL shapes
(`shapes/spectra-core.shacl.ttl`) before bulk loading into Neo4j.

| Script | Inputs | Output |
| --- | --- | --- |
| `validate_shacl.py` | Stage 02/03 JSON-LD files + `shapes/spectra-core.shacl.ttl` + `ontology/spectra.ttl` | conformance report (TXT/JSON) and exit code (0 = conforms) |

## Behaviour

* Loads each JSON-LD record set and the SPECTRA ontology TTL into a single
  rdflib graph.
* Runs `pyshacl` with the SPECTRA SHACL shapes as the shapes graph and
  the SPECTRA ontology as the optional `ont_graph` (this enables RDFS
  subclass inference during validation).
* Emits a conformance report. By default, validation errors are logged
  to a report file but the loader continues — this supports
  data-quality auditing without blocking ingest. Use `--strict` to abort
  on the first violation.

## Usage

```bash
python validate_shacl.py \
    --shapes ../../shapes/spectra-core.shacl.ttl \
    --ontology ../../ontology/spectra.ttl \
    --jsonld out/02_metadata_parse/tdocs.jsonld out/03_document_parse/cr_bodies.jsonld \
    --report-out logs/shacl_report.txt
```

Add `--strict` to fail on the first violation.

## Dependencies

`pyshacl>=0.25.0` and `rdflib>=7.0.0` (see top-level `requirements.txt`).
