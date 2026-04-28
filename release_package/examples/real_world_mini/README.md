# Real-world mini sample (metadata-only)

A small SPECTRA instantiation that mirrors the structure of one
publicly-accessible 3GPP RAN1 meeting (RAN1#120) using only **metadata**
that is publicly available on the 3GPP TDoc list portal:
- TDoc number, title, type, status
- Meeting number, agenda item
- Submitting company (anonymized as CompanyA / CompanyB / CompanyC)
- Work-item code, target Release
- Cross-WG LS direction (originatedFrom / sentTo)

**This sample contains metadata only and does NOT redistribute any copyrighted 3GPP document content** (no abstract, no full body, no chairman's-note paraphrase). It is intended to demonstrate that SPECTRA's schema applies to real meeting structures, not to reproduce a 3GPP corpus.

## Contents

- `data.ttl` — 8 TDocs (5 generic + 2 CR + 1 LS), 2 Resolutions
  (Agreement, Conclusion), 1 TS, 1 Section, 3 anonymized Companies,
  2 WGs, 2 Work Items, 1 Release.
- `queries/Q1_traceability.rq` — multi-hop traceability:
  Section ← CR → Meeting ← Agreement → TDoc.
- `queries/Q2_cross_wg_ls.rq` — cross-WG LS query.
- `expected_outputs/` — verified expected query results.

## Reproducing

```bash
pip install rdflib
python3 -c "
import rdflib
g = rdflib.Graph()
g.parse('../../ontology/spectra.ttl', format='turtle')
g.parse('data.ttl', format='turtle')
print(f'Total triples: {len(g)}')  # Expected: 1019
with open('queries/Q1_traceability.rq') as f: q = f.read()
for r in g.query(q): print(dict(r.asdict()))
"
```

## Why this complements `examples/end_to_end/`

- `examples/end_to_end/` = synthetic toy scenario for toolchain bring-up
  (R1-2599998 / RAN1#121, schema sanity check).
- `examples/real_world_mini/` = realistic meeting-shaped instantiation
  with public-metadata fidelity, demonstrating that SPECTRA's
  TDoc → Resolution → CR → Section → Spec traceability and LS-based
  cross-WG impact apply to actual 3GPP meeting structures.

## License

CC-BY 4.0 (matches the parent SPECTRA release).
