# SpectraCQ v1.0 — 137 Competency Questions for the SPECTRA Ontology

This dataset packages the 137 competency questions (CQs) used to design and
validate the SPECTRA ontology, together with their executable Cypher
translations against a SPECTRA-conformant Neo4j knowledge graph.

## Distribution

- `questions.json` — 137 CQ entries with English question text, phase
  (P1..P5), category, schema area (classes + relationship types
  exercised), and a pointer to the Cypher file.
- `cypher/P{phase}_{id}.cypher` — 137 executable Cypher files (one per
  CQ).
- `sparql/P{phase}_{id}.rq` — 137 SPARQL translations (one per CQ,
  translated from the reference Cypher; each carries the CQ text and a
  pointer to its Cypher source, and parses under rdflib).
  Class-membership guards default to `FILTER EXISTS` so greedy join
  planners do not form class-enumeration cross products; positive
  `rdf:type` triples appear only where the type pattern is itself the
  query, is anchored to a constant, or (two queries, with engine
  notes) replaces a per-row `FILTER EXISTS` rdflib evaluates too
  slowly. Row-count parity against the Cypher replay: 137/137 match
  (`../../validation/cq_replay/sparql_parity_results.json`).
- `LICENSE` — CC-BY 4.0.
- `citation.bib` — BibTeX citation entry for this dataset.

## Company-name policy

The 14 of 137 CQs that mention companies retain the **verbatim** public
3GPP identifiers (Huawei, Samsung, Qualcomm, ...) as they appear on the
public per-meeting `TDOC_List.xlsx`. The other 123 CQs reference no
specific company. The legacy mapping
is intentionally not published in v1.0.

## Phase distribution

| Phase | Domain                | CQs |
|-------|-----------------------|----:|
| P1    | TDoc metadata         | 25  |
| P2    | Meeting resolutions   | 34  |
| P3    | TS structure          | 45  |
| P4    | CR documents          | 15  |
| P5    | Technical Reports     | 18  |
| **Total** |                   | **137** |

## How to use

```bash
# Inspect questions
jq '.cqs[0]' questions.json

# Run a single CQ against a SPECTRA-conformant Neo4j (example: P1_CQ1-1)
cypher-shell -u neo4j -p <pass> < cypher/P1_CQ1-1.cypher

# Run the SPARQL translation against the released RDF (rdflib)
python3 -c "import rdflib; g=rdflib.Graph(); g.parse('../../kg/per_wg/RAN1-body.ttl');
print(len(list(g.query(open('sparql/P1_CQ1-1.rq').read()))))"
```

## Companion releases

- SPECTRA OWL ontology (this dataset's schema): https://w3id.org/spectra
- Paper: "SPECTRA: A Traceability Ontology for the 3GPP RAN Standardization
  Process" (citation will be added upon publication).

## Citation

See `citation.bib`. To cite this dataset:

```
Choi, S., Lee, J. (2026). SpectraCQ: 137 Competency Questions
for the SPECTRA Ontology (v1.0) [Data set]. Zenodo.
DOI: <to be assigned upon Zenodo mint>
```

## License

CC-BY 4.0. You are free to share and adapt; please cite.
