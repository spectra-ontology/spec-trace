# Changelog

All notable changes to the SPECTRA release package are documented in this file.
Version numbers follow [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html).

## [1.0.1] — 2026-05-11 (pre-rebuttal patch; backwards-compatible)

Backwards-compatible additions in response to OOPS! P10 and pre-emptive
adversarial-review (`docs/paper/iswc/rebuttal_preparation/`) findings:

### Ontology (`ontology/spectra.ttl`)

- Introduced `tdoc:StudyItem ⊑ tdoc:WorkItem` (3GPP Study Item produces TR
  without normative TS changes; v1.0 collapsed both under WorkItem).
- Introduced `tdoc:Discussion ⊑ tdoc:Tdoc` (the most common Tdoc type;
  v1.0 left it as the implicit base case, untyped Tdoc instances remain
  valid).
- Added `owl:IrreflexiveProperty` / `owl:AsymmetricProperty` characteristics
  to lineage OPs: `replyTo`, `revisedTo`, `isRevisionOf`, `promotedTo`,
  `hasCR`, `belongsToCRPack`. Reasoner-detectable error coverage on
  these directional flow predicates is now correct.
- Added 10 conservative `owl:disjointWith` axioms among Resolution
  subclasses (Agreement ⊥ Conclusion ⊥ WorkingAssumption) and Tdoc
  subclasses (CR ⊥ {LS, Summary, SessionNotes, Discussion}; LS ⊥
  {Summary, SessionNotes, Discussion}). Closes OOPS! P10.

### Documentation (`validation/validation_manifest.md`)

- Added "Notes on inter-artefact count differences" section explaining
  the small CR/Summary deltas between the operational-KG snapshot
  (Table 6 source) and the metadata-only export, and noting the
  per-WG LS outgoing coverage range (51.9–96.6%) reproducibility
  pathway.

### Documentation (`supplement/PAPER_APPENDIX.tex` §A.dq)

- Added cross-WG LS sender-side vs receiver-side count reconciliation:
  the S2 figures "3,644 RAN1→RAN2 / 1,450 received in RAN2 KG"
  measure two different identifier spaces (sender R1-XXXXXXX vs
  receiver R2-YYYYYYY); decomposed offline against `ls_routing.ttl`,
  the 2,194-LS gap is fully accounted for (513 RAN1-incoming records
  with non-direction-filtered Cypher → corrected RAN1-out = 3,131;
  remaining 1,681 = revisedTo compression + status not_treated /
  withdrawn; additional 441 = multi-WG broadcasts where RAN2 may
  be CC rather than primary recipient).

### Documentation (`docs/usecase/evaluations/3way/summary.md`)

- Added explicit counting rule for the "11 unsupported claims" total
  (RP-* WID pairs split as 2 distinct items; speculative ASN.1 SEQUENCE
  block under hedged header counts as 1 cluster; numeric values
  attributed to RRC parameters without spec citation count as 1 even
  with 'typical' guard) — under this rule Q1=3 + Q2=1 + Q3=3 + Q4=4 = 11.
- Documented Q3 internal contradiction in Claude's answer (BFD-RS
  Rel.16+ "up to 64 RSs" vs "up to 8 or more") as a separate quality
  defect not currently double-counted.

### Documentation (`paper main.tex`)

- Reworded Table tab:scenarios S2 row to disambiguate sender-side vs
  receiver-side LS counts (3,131 RAN1-out edges with R1-XXXXXXX IDs;
  1,450 RAN2-in distinct LSs with R2-YYYYYYY IDs after compression).

### Triple count

886 → 915 (+29). pyshacl conformance against `kg/per_wg/RAN1-body.ttl`:
25,240 pre-existing minCount violations unchanged (zero new violations
introduced). All v1.0 instances remain valid.

### Pre-rebuttal verification trail

`docs/paper/iswc/rebuttal_preparation/agent_d_rp_wid_verification.md`
records the cross-check of all 9 RP-* WID numbers cited in pilot Q1-Q4
retrieval contexts against the public 3GPP plenary archive (`www.3gpp.org/
ftp/tsg_ran/TSG_RAN/TSGR_*/Docs/RP-*.zip`). All 9 RP numbers verified
correct including `RP-221799` (RAN#96 revision of NR_Mob_enh2 by MediaTek)
and `RP-182067` (RAN#81 revised Rel-16 NR_eMIMO WID by Samsung).

## [1.0.0] — 2026-05-08 (camera-ready; Zenodo DOI [10.5281/zenodo.20034872](https://doi.org/10.5281/zenodo.20034872) minted)

First public release accompanying the ISWC 2026 Resources Track submission
*"SPECTRA: A Traceability Ontology for the 3GPP RAN Standardization Process"*.

### Included

- **Ontology** (`ontology/spectra.ttl`): 26 classes, 53 object properties, 81
  data properties, 886 triples; PROV-O alignment as 6 optional
  `rdfs:subClassOf` axioms; reuses Dublin Core, DCTERMS, FOAF.
- **SHACL shapes** (`shapes/spectra-core.shacl.ttl`): 8 `sh:NodeShape`s
  covering the lifecycle classes; cardinality and range constraints captured
  portably; rationales for shape relaxations (`presentedAt`, `modifies`,
  `originatedFrom`, `sentTo`) annotated inline.
- **PyLODE HTML documentation** (`docs/spectra.html`).
- **SpectraCQ v1.0** (`cqs/spectra_cq_v1.0/`): 137 competency questions ×
  {phase, category, NL question, schema area, executable Cypher, verdict};
  separately citable under CC-BY 4.0 with its own CITATION.bib.
- **Representative queries** (`queries/`): 15 Cypher + 6 SPARQL examples
  (all 137 SpectraCQ Cypher queries are schema-level patterns directly
  translatable to SPARQL via the same schema; the 6 SPARQL examples
  illustrate this for the most-cited scenarios).
- **Synthetic and metadata-only examples**: end-to-end synthetic 4-hop
  traceability scenario (`examples/end_to_end/`); metadata-only real-world
  mini sample of one RAN1 meeting (`examples/real_world_mini/`); cross-WG
  process KG over RAN1–RAN5 (`examples/process_kg/`; LS routing 195K
  triples, CR routing 1.25M triples, RAN1 TDoc structural metadata 991K
  triples; 2.44M-triple union conforms to the SHACL shapes with zero
  violations).
- **Per-WG body-text KGs** (`kg/per_wg/`): sentence-level rendered text
  retained with 3GPP attribution per the project's Terms-of-Use note,
  following the same redistribution framing as TSpec-LLM
  (Nikbakht et al., 2024) and the GSMA `telecom-kg-rel19` release.
- **Sanitized parsing pipeline source** (`pipeline/`): 5-stage recipe
  (scrape → metadata parse → CR/TR document parse via `python-docx` →
  SHACL → bulk Neo4j load); company-internal monitoring/auth wrappers
  removed.
- **Reproducibility tests** (`tests/verify_release.py`): deterministic
  checks across all manifest-referenced claims; expected: all checks PASS on a clean release. Sections cover: TTL parse + 886 triples;
  instantiation snippet SHACL conformance; process-KG union SHACL
  conformance; end-to-end SPARQL; SpectraCQ counts/verdict; structural
  metrics; manifest references; synthetic-instantiation sanity; release directory
  inventory). Depends only on `rdflib` and `pyshacl`; runs in any
  Python 3.10+ environment with no Samsung-internal infrastructure
  required.
- **Validation evidence** (`validation/`): 11 JSON files +
  `validation_manifest.md` mapping every quantitative claim in the paper
  to its supporting evidence file.
- **Croissant metadata** (`cqs/spectra_cq_v1.0/croissant.json`):
  ML Commons Croissant 1.0 dataset description for the SpectraCQ
  competency-benchmark dataset, enabling discovery in dataset registries
  (Hugging Face, Zenodo, Google Dataset Search).
- **License**: two-tier — SPECTRA-authored components under CC-BY 4.0;
  bundled per-WG body-text KGs are 3GPP-derived literals retained with
  3GPP attribution under applicable ETSI/3GPP terms (see `LICENSE`).

### Not bundled

- **Raw Neo4j instance dumps** (`.dump`): exceed the Zenodo size cap;
  regenerable from `kg/per_wg/` plus `pipeline/`.
- **VectorDB embeddings** (used internally for retrieval-augmented CQ
  answering): planned for a subsequent minor release; regenerable
  deterministically from the bundled body-text KGs and a documented
  embedding configuration.

### Conventions

- Version numbers in this changelog refer to the release package
  (`release_package/`); SpectraCQ has its own version number tracked in
  `cqs/spectra_cq_v1.0/citation.bib`.
- Authoritative version of the ontology is in the file header of
  `ontology/spectra.ttl` (the `owl:versionInfo` triple).
