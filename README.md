# SPECTRA — A Traceability Ontology for 3GPP RAN Standardization

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Ontology: OWL 2](https://img.shields.io/badge/Ontology-OWL_2-blue.svg)](https://www.w3.org/TR/owl2-overview/)
[![Persistent IRI](https://img.shields.io/badge/IRI-w3id.org%2Fspectra-success.svg)](https://w3id.org/spectra)
<!-- [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX) -->

**License**: CC-BY 4.0
**Version**: v1.0.0 (see `ontology/spectra.ttl` header for authoritative version)
**Persistent identifier**: `https://w3id.org/spectra` (registration via [perma-id/w3id.org](https://github.com/perma-id/w3id.org); see `w3id/PR_DESCRIPTION.md`)
**DOI**: minted by Zenodo upon GitHub release (see `PUBLISHING.md`)
**Repository**: https://github.com/spectra-ontology/spec-trace

## What this package releases

This is the **publicly released** component of the SPECTRA ontology resource described in a paper submitted to the ISWC Resources Track *"SPECTRA: A Traceability Ontology for 3GPP Standardization"* (under review).

```
release_package/
├── README.md                          # this file
├── ontology/
│   └── spectra.ttl                    # SPECTRA OWL 2 ontology (Turtle)
├── docs/
│   └── spectra.html                   # PyLODE-generated HTML documentation
├── shapes/
│   └── spectra-core.shacl.ttl         # SHACL shapes (core cardinality / range)
├── diagrams/
│   └── schema_overview.md             # high-level schema summary
├── cqs/
│   ├── cq_index.md                    # anonymized index of all 137 CQs
│   │                                  # (id, phase, category, persona, schema area)
│   └── representative_cqs.md          # representative CQs with full text + Cypher/SPARQL
├── queries/
│   ├── cypher/                        # executable Cypher translations
│   └── sparql/                        # SPARQL translations (representative)
├── examples/
│   └── instantiation_snippet.ttl      # small synthetic instantiation
├── w3id/
│   ├── htaccess                       # to be submitted to perma-id/w3id.org
│   └── PR_DESCRIPTION.md              # PR text for w3id registration
├── CITATION.cff                       # citation metadata (machine-readable)
├── codemeta.json                      # software/data metadata
├── PUBLISHING.md                      # release checklist
└── LICENSE                            # CC-BY 4.0
```

## What is *not* in this package

The following artifacts are part of the paper's **internal validation evidence** and are *not* redistributed:

- The complete 137-CQ validation suite and the full executable query set used for cumulative regression testing. Representative CQs and queries are included in `cqs/` and `queries/` so that the schema can be inspected and reused; the full suite is retained as internal validation material.
- The instantiated RAN1 knowledge graph (123,677 Technical Documents) and the equivalent instantiations of RAN2–RAN5. The graphs are not redistributable because the underlying 3GPP Technical Documents are subject to 3GPP copyright. The original TDocs remain publicly accessible via the 3GPP portal: https://www.3gpp.org
- The operational parsing and knowledge-graph population pipeline (internal project code).

## Ontology summary

- **26 classes** organized around: contributions (`Tdoc` and its subclasses `CR`, `LS`, `Summary`, `SessionNotes`), resolutions (`Resolution` → `Agreement`, `Conclusion`, `WorkingAssumption`), specifications (`Spec`, `Section`, `TSTable`, `TSFigure`, `TechnicalReport`, `TRImpact`), organizational entities (`Meeting`, `Company`, `Contact`, `WorkItem`, `AgendaItem`, `Release`, `WorkingGroup`), and artefacts (`Figure`, `Table`, `Chart`, `CRPack`).
- **53 object properties** + **81 data properties** (134 total).
- Reuses **Dublin Core** (`dc:title`, `dc:description`, `dc:creator`, `dc:date`) and **FOAF** (`foaf:Person`, `foaf:Organization`).
- Axiomatization: 23 `owl:FunctionalProperty`, 2 `owl:InverseFunctionalProperty`, 15 inverse property pairs, 6 `owl:IrreflexiveProperty`, 2 `owl:AsymmetricProperty`.

## Quick start

### Load with RDFLib (Python)
```python
import rdflib
g = rdflib.Graph()
g.parse("ontology/spectra.ttl", format="turtle")
print(f"Triples: {len(g)}")
```

### Open in Protégé
File → Open → select `ontology/spectra.ttl`.

### Validate an instance with SHACL (pySHACL)
```bash
pip install pyshacl
pyshacl -s shapes/spectra-core.shacl.ttl examples/instantiation_snippet.ttl
# Expected: "Conforms: True"
```

### Browse the HTML documentation
Open `docs/spectra.html` in any browser (PyLODE-generated; no server required).

### Run a representative Cypher query
See `queries/cypher/` for examples executable against any Neo4j instance conforming to the SPECTRA schema.

### Run a representative SPARQL query
See `queries/sparql/`. Translations exercise the same CQs against a triple-store loaded with the TTL and your own instantiation.

## Citation

If you reuse SPECTRA, please cite the accompanying paper (currently under review at ISWC 2026 Resources Track; BibTeX will be added once the venue assigns a citation key) and this software/data record via the metadata in `CITATION.cff` (machine-readable) or `codemeta.json`.

## Contact

- Author (first author and corresponding author): Sihyeon Choi (Samsung System LSI)
- Email: shyun12.choi@samsung.com

## License

The SPECTRA ontology and all artifacts in this package are released under Creative Commons Attribution 4.0 (CC-BY 4.0). See `LICENSE` for the full text.
