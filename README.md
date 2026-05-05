# SPECTRA — A Traceability Ontology for 3GPP RAN Standardization

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Ontology: OWL 2](https://img.shields.io/badge/Ontology-OWL_2-blue.svg)](https://www.w3.org/TR/owl2-overview/)
[![Persistent IRI](https://img.shields.io/badge/IRI-w3id.org%2Fspectra-success.svg)](https://w3id.org/spectra)
<!-- [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20034872.svg)](https://doi.org/10.5281/zenodo.20034872) -->

**License**: CC-BY 4.0 (SPECTRA-authored components); 3GPP-derived literal content carries explicit 3GPP attribution (see `LICENSE` Tier 2)
**Version**: v1.0.0 (see `ontology/spectra.ttl` header for authoritative version)
**Persistent identifier**: `https://w3id.org/spectra` (registration **pending**; PR template at `w3id/PR_DESCRIPTION.md`, target `perma-id/w3id.org`)
**Zenodo DOI**: `10.5281/zenodo.20034872` *(populated when the v1.0.0 deposit is published; see `PUBLISHING.md`)*
**Repository**: https://github.com/spectra-ontology/spec-trace

## Two-channel distribution

To accommodate GitHub's 100 MB-per-file limit, this release is split:

- **GitHub repository (this repo)** — small files: ontology, SHACL, SpectraCQ v1.0, schema-instantiation TTLs, validation JSONs, scripts, supplement, parsing pipeline. Total ~5 MB.
- **Zenodo deposit** — large files: per-WG body-text Knowledge Graphs (`RAN{1..5}-body.ttl`, ~922 MB total). See `kg/per_wg/README.md` for the inventory and the DOI link.

This follows the academic two-tier distribution pattern of TSpec-LLM and GSMA telecom-kg-rel19. The `verify_release.py` test accepts either layout (Git checkout: body files absent by design; Zenodo download: body files present).

## What this package releases

This is the **publicly released** component of the SPECTRA ontology resource described in a paper submitted to the ISWC Resources Track *"SPECTRA: A Traceability Ontology for 3GPP Standardization"* (under review).

```
release_package/
├── README.md                          # this file
├── ontology/
│   └── spectra.ttl                    # SPECTRA OWL 2 ontology (Turtle, 886 triples incl. PROV-O alignment)
├── docs/
│   └── spectra.html                   # PyLODE-generated HTML documentation
├── shapes/
│   └── spectra-core.shacl.ttl         # SHACL shapes (8 NodeShapes, core cardinality/range)
├── diagrams/
│   ├── schema_overview.md             # high-level schema summary
│   └── cq_distribution.png            # category-by-phase distribution of 137 CQs
├── cqs/
│   ├── cq_index.md                    # index of all 137 CQs (verbatim 3GPP company names where present)
│   │                                  # (id, phase, category, schema area)
│   ├── representative_cqs.md          # 14 representative CQs with full text + Cypher
│   └── spectra_cq_v1.0/               # ★ SpectraCQ v1.0 — 137-CQ companion dataset
│       ├── README.md                  # dataset description + how to use
│       ├── LICENSE                    # CC-BY 4.0
│       ├── citation.bib               # BibTeX for citing SpectraCQ
│       ├── questions.json             # 137 CQ × {id, phase, category, question_en, schema_area, verdict}
│       └── cypher/                    # 137 executable Cypher files (one per CQ)
├── queries/
│   ├── cypher/                        # 15 Cypher translations (incl. MULTI_HOP_traceability)
│   └── sparql/                        # 6 SPARQL examples (incl. MULTI_HOP_traceability)
├── examples/
│   ├── instantiation_snippet.ttl      # small synthetic instantiation
│   ├── end_to_end/                    # full E2E synthetic example (data + queries + expected)
│   │   ├── README.md
│   │   ├── data.ttl                   # synthetic 4-hop scenario (Turtle)
│   │   ├── data.cypher                # same data as Neo4j Cypher CREATE
│   │   ├── query.sparql               # multi-hop traceability query (SPARQL)
│   │   ├── query.cypher               # same query in Cypher
│   │   └── expected_output.txt        # expected result row(s)
│   ├── real_world_mini/               # ★ metadata-only mini sample (1 RAN1 meeting structure)
│   │   ├── README.md                  # explains: metadata only, no copyrighted body content
│   │   ├── data.ttl                   # 8 TDocs + 2 Resolutions + 1 TS + 1 Section
│   │   ├── queries/                   # Q1 traceability + Q2 cross-WG LS (SPARQL)
│   │   └── expected_outputs/          # verified expected query rows
│   └── process_kg/                    # ★ cross-WG process KG (metadata-only, body stripped)
│       ├── README.md                  # describes scope and anonymization policy
│       ├── SCHEMA.md                  # field-level schema for the three TTL files
│       ├── ls_routing.ttl             # RAN1–RAN5 LS routing (~26.8K LSs, ~195K triples)
│       ├── cr_routing.ttl             # RAN1–RAN5 CR routing (~193K CRs, ~1.25M triples)
│       ├── ran1_tdoc_metadata.ttl     # full RAN1 TDoc structural metadata (~124K TDocs, ~991K triples)
│       └── _export_summary.txt        # entity counts per file
├── kg/                                 # ★ per-WG knowledge graph deposits (paper §6.4, §7)
│   ├── per_wg/                        # body-text TTLs (RAN{1..5}-body.ttl, ~922 MB) — Zenodo deposit only
│   │   └── README.md                  # explains where to download + IRI scheme
│   └── per_wg_schema/                 # schema-instantiation TTLs (RAN{1..5}-schema.ttl, ~14 KB each)
│       ├── README.md                  # cross-WG schema-fit verification recipe
│       └── RAN1-schema.ttl ... RAN5-schema.ttl
├── pipeline/                           # ★ sanitized parsing pipeline (5 stages)
│   ├── 01_extract/   02_metadata_parse/   03_document_parse/
│   ├── 04_shacl_validate/             05_neo4j_load/
│   └── README.md
├── supplement/                         # ★ paper companion (trimmed from main PDF for page limit)
│   ├── README.md                      # what is here and why
│   ├── PAPER_APPENDIX.tex             # original Appendix A-G (TTL/SHACL/SPARQL excerpts, etc.)
│   └── LLM_EVAL_PILOT.tex             # single-evaluator LLM-baseline pilot (was §6.6 in body draft)
├── usecase/                            # ★ Q&A evaluation data (4 questions × 3 systems)
│   ├── answers/                       # tracer / gpt / claude answer texts
│   ├── evaluations/                   # per-question + 3-way comparisons + summary v2
│   └── README.md
├── validation/                         # ★ JSON evidence for paper's quantitative claims (11 JSONs)
│   ├── validation_manifest.md         # paper claim → JSON file mapping
│   ├── structural_metrics.json        # class/property/axiom counts
│   ├── oops_summary.json              # OOPS! pitfall scanner result
│   ├── cq_coverage.json               # 137-CQ × ontology coverage matrix
│   ├── cypher_to_sparql_portability.json # 136/137 SPARQL-equivalent classification
│   ├── cross_wg_schema_diff.json      # RAN1 vs RAN2-5 schema diff
│   ├── cross_wg_use_evidence.json     # cross-WG query counts on deployed KGs
│   ├── per_wg_class_coverage.json     # per-WG class instantiation coverage
│   ├── ran1_instance_counts.json      # RAN1 KG per-class counts + integrity stats
│   ├── ran1_relation_integrity.json   # per-relation domain coverage + integrity %
│   └── cq_results.json                # 137 CQ × {id, phase, status} per-CQ pass/fail evidence
├── tests/                              # ★ reproducibility scripts (rdflib + pyshacl)
│   ├── README.md
│   ├── reproduce_structural_metrics.py # recompute Table 4 numbers from spectra.ttl
│   ├── test_e2e_sparql.py              # run multi-hop traceability against synthetic data
│   └── verify_release.py               # deterministic per-claim verifier
├── w3id/
│   ├── htaccess                       # to be submitted to perma-id/w3id.org
│   └── PR_DESCRIPTION.md              # PR text for w3id registration
├── ARTIFACT.md                         # full artifact narrative (Tier 1 / Tier 2 boundary)
├── CITATION.cff                       # citation metadata (machine-readable)
├── CHANGELOG.md                       # release history
├── PUBLISHING.md                      # day-by-day release checklist (Mon→Fri timeline)
├── TUTORIAL.md                        # short walkthrough for new users
├── codemeta.json                      # software/data metadata
└── LICENSE                            # CC-BY 4.0 (Tier 1) + 3GPP attribution (Tier 2)
```

## What is *not* in this package

The following artifacts are part of the paper's **internal validation evidence** and are *not* redistributed:

- Internal cumulative-regression run logs and per-phase intermediate KG snapshots used during the five-phase development. The full 137-CQ dataset (English text + Cypher specifications + per-CQ verdict) is publicly released at `cqs/spectra_cq_v1.0/`; only the regression run-history is retained internally.
- Neo4j instance dumps (`.dump`) and VectorDB embeddings: regenerable from the released per-WG body-text KGs (`kg/per_wg/`) and sanitized parsing pipeline (`pipeline/`); not bundled because raw dumps exceed the archival package's size budget. Original 3GPP TDocs remain publicly accessible via the 3GPP portal: https://www.3gpp.org
- Internal operational deployment glue: company-specific monitoring, authentication, and Slack/incident hooks around the parsing pipeline; the deterministic parser logic itself is released at `pipeline/`.

## Anonymization policy (asymmetric by design)

Different artifact tiers follow different policies, each driven by what 3GPP itself publishes:

| Artifact tier | Companies | Rationale |
|---|---|---|
| `examples/process_kg/` (LS/CR routing + RAN1 TDoc metadata) | **verbatim** | Redistributes metadata that is already public on every TDoc cover page and on 3GPP's per-meeting `TDOC_List.xlsx`; anonymization would discard recoverable information without adding privacy. |
| `cqs/spectra_cq_v1.0/` (NL questions, Cypher) | **verbatim** (real 3GPP company names from public `TDOC_List.xlsx`, where present in 14 of 137 CQs) | The 14 CQs that name companies cite contributors who are already public on every TDoc cover sheet; anonymizing would damage CQ portability against the released KG. The other 123 CQs reference no specific company. |
| `examples/real_world_mini/`, `examples/end_to_end/` | **synthetic** | Templates for instantiation; no real-world data is implied. |
| Body content (CR/TR/TS text, `discussionText` *values*) | **verbatim under 3GPP attribution** | Sentence-level rendered text retained with explicit 3GPP attribution per the project's Terms-of-Use note, following the same redistribution framing as TSpec-LLM and GSMA telecom-kg-rel19. |

The `tests/verify_release.py` anonymization check (Section 7 of the script) targets the SpectraCQ files only, making this policy boundary a syntactic invariant.

## Ontology summary

- **26 classes** organized around: contributions (`Tdoc` and its subclasses `CR`, `LS`, `Summary`, `SessionNotes`), resolutions (`Resolution` → `Agreement`, `Conclusion`, `WorkingAssumption`), specifications (`Spec`, `Section`, `TSTable`, `TSFigure`, `TechnicalReport`, `TRImpact`), organizational entities (`Meeting`, `Company`, `Contact`, `WorkItem`, `AgendaItem`, `Release`, `WorkingGroup`), and artefacts (`Figure`, `Table`, `Chart`, `CRPack`).
- **53 object properties** + **81 data properties** (134 total).
- Reuses **Dublin Core** (`dc:title`, `dc:description`, `dc:creator`, `dc:date`, `dc:rights`), **DCTERMS** (`dcterms:license`), and **FOAF** (`foaf:Person`, `foaf:Organization`).
- Axiomatization: 20 `owl:FunctionalProperty`, 2 `owl:InverseFunctionalProperty`, 15 inverse property pairs, 6 `owl:IrreflexiveProperty`, 2 `owl:AsymmetricProperty`.

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

No public SPARQL endpoint is operated. To run the bundled queries locally:

**Option 1 — RDFLib (single Python process, no server):**
```python
import rdflib
g = rdflib.Graph()
g.parse('ontology/spectra.ttl', format='turtle')
g.parse('examples/end_to_end/data.ttl', format='turtle')
q = open('examples/end_to_end/query.sparql').read()
for row in g.query(q): print(row)
```
Or use the bundled wrapper: `python3 tests/test_e2e_sparql.py` (asserts the expected R1-2599998 / RAN1#121 row).

**Option 2 — Apache Jena Fuseki (local server):**
```bash
fuseki-server --file=ontology/spectra.ttl --file=examples/end_to_end/data.ttl /spectra
# then in another terminal:
curl -G --data-urlencode "query=$(cat examples/end_to_end/query.sparql)" \
     http://localhost:3030/spectra/sparql
```

**Option 3 — load the larger metadata-only process KG (~2.44M triples)** for graph-analytics queries (e.g., LS routing, CR-pack analytics):
```bash
fuseki-server --file=ontology/spectra.ttl \
              --file=examples/process_kg/ls_routing.ttl \
              --file=examples/process_kg/cr_routing.ttl \
              --file=examples/process_kg/ran1_tdoc_metadata.ttl \
              /spectra-process
```

See `queries/sparql/` for additional example queries.

### Reproducibility tests (rdflib + pyshacl)
```bash
pip install rdflib pyshacl
python3 tests/reproduce_structural_metrics.py   # exit 0 on agreement with validation/structural_metrics.json
python3 tests/test_e2e_sparql.py                # exit 0 on returning the expected R1-2599998 / RAN1#121 row
```

### SpectraCQ companion dataset
The full 137-CQ corpus with English question text, executable Cypher, and per-CQ verdicts is at `cqs/spectra_cq_v1.0/`. It is independently citable via `cqs/spectra_cq_v1.0/citation.bib` and licensed CC-BY 4.0.

## Citation

If you reuse SPECTRA, please cite the accompanying paper (currently under review at ISWC 2026 Resources Track; BibTeX will be added once the venue assigns a citation key) and this software/data record via the metadata in `CITATION.cff` (machine-readable) or `codemeta.json`.

## Contact

- Author (first author and corresponding author): Sihyeon Choi (System LSI Business, Device Solutions Division, Samsung Electronics)
- Email: shyun12.choi@samsung.com

## License

SPECTRA-authored components (the ontology, SHACL shapes, SpectraCQ, queries, synthetic/metadata-only examples, validation scripts, parsing pipeline source, and PyLODE documentation) are released under Creative Commons Attribution 4.0 (CC-BY 4.0). 3GPP-derived text literals included in the per-WG body-text KGs are retained with explicit 3GPP attribution under the applicable ETSI/3GPP terms and are not relicensed as original SPECTRA-authored content. See `LICENSE` for the full CC-BY 4.0 text.
