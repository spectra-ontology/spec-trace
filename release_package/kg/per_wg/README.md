# Per-WG Body-Text Knowledge Graphs (RAN1-RAN5)

The per-WG body-text TTL files materialize lifecycle-class node literals
(TDoc titles, Resolution `content`, CR rationale, Section structure, etc.)
and inter-entity relationships from each RAN Working Group's Neo4j
snapshot, using the released SPECTRA schema.

## ⚠️ Where to download

These TTL files are **not tracked in the Git repository** because
RAN1/2/4/5 each exceed GitHub's 100 MB-per-file limit. They are
deposited on **Zenodo** as the archival distribution channel:

> **Zenodo DOI:** `10.5281/zenodo.20034872` *(populated when the v1.0.0
> deposit is published; see top-level `README.md` and the paper's
> Resource Availability Statement.)*

If you obtained `release_package/` from a Git checkout, this directory
will contain only this README; if you obtained it from the Zenodo
archive, it will contain the five `RAN{1..5}-body.ttl` files listed
below. Either layout is supported by `tests/verify_release.py` (it
reports `[SKIP]` for files absent in a Git checkout).

The Git repository always keeps the schema-only counterparts in
`kg/per_wg_schema/RAN{1..5}-schema.ttl` (~14 KB each) so reviewers can
verify the cross-WG schema-fit numbers from §6 of the paper without
downloading the body-text deposit.

## File inventory (Zenodo deposit)

| File | WG | Nodes | Relationships | Size |
|---|---|---:|---:|---:|
| `RAN1-body.ttl` | RAN1 |  206,471 |    830,026 | 185 MB |
| `RAN2-body.ttl` | RAN2 |  188,814 |    894,560 | 186 MB |
| `RAN3-body.ttl` | RAN3 |   97,159 |    436,629 |  85 MB |
| `RAN4-body.ttl` | RAN4 |  314,359 |  1,302,216 | 279 MB |
| `RAN5-body.ttl` | RAN5 |  188,096 |    855,701 | 186 MB |
| **Total** | | **994,899** | **4,319,132** | **923 MB** |

Snapshot date: 2026-05-04. Stable IRI scheme:
`https://w3id.org/spectra/inst/<wg>/<class>/<id>`. Each file carries an
ontology-level header with `dcterms:created`, `dcterms:rightsHolder=3GPP`,
`dcterms:source=<https://www.3gpp.org/ftp/>`, and the redistribution
clause described below.

## License and attribution

The text literals are **3GPP-derived content** redistributed with explicit
3GPP source attribution (see top-level `LICENSE`, Tier 2). They are NOT
relicensed under CC-BY 4.0. Re-users must preserve 3GPP source
attribution. Original 3GPP documents remain freely accessible at
<https://www.3gpp.org/ftp/>.

The schema, structure, and parsing/encoding work that materializes 3GPP
text into RDF is SPECTRA-authored and falls under CC-BY 4.0 (Tier 1).

This release follows the academic redistribution practice of TSpec-LLM
(Nikbakht et al., 2024) and the GSMA telecom-kg-rel19 release.

## Reproducibility

```bash
# Re-export locally from the five Neo4j RAN instances (ports 7687-7691):
python3 scripts/paper/export_per_wg_body_kg.py
```

The script is read-only against Neo4j and emits files identical (up to
RDF triple ordering) to those on Zenodo. Set `NEO4J_PASSWORD` if your
local password differs from `password123`.

## Schema-only verification (no body text needed)

For the cross-WG generality numbers reported in the paper (§6 E4), use
the schema-instantiation TTLs in `../per_wg_schema/RAN{1..5}-schema.ttl`
(in this Git repo) and OWL-diff them against `../../ontology/spectra.ttl`.

## Contact

Issues and corrections: <https://github.com/spectra-ontology/spec-trace/issues>.
