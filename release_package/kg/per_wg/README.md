# Per-WG Body-Text Knowledge Graphs (RAN1-RAN5)

The per-WG body-text TTL files materialize lifecycle-class node literals
(TDoc titles, Resolution `content`, CR rationale, Section structure, etc.)
and inter-entity relationships from each RAN Working Group's Neo4j
snapshot, using the released SPECTRA schema.

## ⚠️ Where to download

These TTL files are **not tracked in the Git repository** because
RAN1/2/4/5 each exceed GitHub's 100 MB-per-file limit. They are
deposited on **Zenodo** as the archival distribution channel:

> **Zenodo DOI:** `10.5281/zenodo.20034871` *(concept DOI; it always
> resolves to the newest published deposit, which carries these files.
> See top-level `README.md` and the paper's Resource Availability
> Statement.)*

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

| File | WG | Nodes | Relationships | Size (bytes) |
|---|---|---:|---:|---:|
| `RAN1-body.ttl` | RAN1 | 165,418 |   848,228 | 163,305,588 |
| `RAN2-body.ttl` | RAN2 | 156,288 |   939,037 | 166,688,978 |
| `RAN3-body.ttl` | RAN3 |  87,980 |   481,498 |  81,735,967 |
| `RAN4-body.ttl` | RAN4 | 342,161 | 1,592,845 | 295,732,831 |
| `RAN5-body.ttl` | RAN5 | 215,012 | 1,047,242 | 195,847,852 |
| **Total** | | **966,859** | **4,908,850** | **903,311,216** |

Nodes and relationships are the counts the shipped loader reports after
loading each file, recorded in
`../../validation/cq_replay/graph_counts.json`; for every WG they equal
what the shipped parser sees in the TTL (`nodes_eq_parse`,
`rels_eq_parse`). `../../MANIFEST.md` §1 is the authoritative record and
adds the RDF-triple counts.

Snapshot date: 2026-05-04. Stable IRI scheme:
`https://w3id.org/spectra/inst/<wg>/<class>/<id>`. Each file carries an
ontology-level header with `dcterms:created`, `dcterms:rightsHolder=3GPP`,
`dcterms:source=<https://www.3gpp.org/ftp/>`, and the redistribution
clause described below.

## Known defect: duplicated `Contact` nodes in RAN3, RAN4 and RAN5

An automated audit of the deposited TTL files found that **634 of the
4,935 `Contact` nodes are duplicates**: the five graphs carry only 4,301
distinct contact identifiers.

| WG | `Contact` nodes | Distinct contact ids | Duplicate nodes |
|---|---:|---:|---:|
| RAN1 | 1,000 | 1,000 | 0 |
| RAN2 | 1,759 | 1,759 | 0 |
| RAN3 |   572 |   391 | 181 |
| RAN4 | 1,133 |   842 | 291 |
| RAN5 |   471 |   309 | 162 |
| **Total** | **4,935** | **4,301** | **634** |

**Cause.** The contact identifier was read from the source spreadsheet
column into a pandas float64 series in the RAN3/RAN4/RAN5 reference-class
export, so the same contact reaches the IRI builder as `105754` along one
path and as `105754.0` along another. The IRI sanitizer turns the second
spelling into `…/Contact/tdoc:contact%2F105754_0`, which is a different
IRI from `…/Contact/tdoc:contact%2F105754`, so one contact becomes two
nodes. RAN1 and RAN2 are unaffected because their source columns never
took the float path. 744 identifiers across the three affected WGs carry
the `_0` suffix; 110 of those have no unsuffixed twin, so they are not
duplicate nodes, but they do carry an identifier produced by the same
defect and their `contactId` is not the identifier printed on the source
document.

**What the duplicate pairs contain.** In 621 of the 634 pairs the two
nodes carry a byte-identical `contactName`. In the remaining 13 the two
literals differ: one pair differs only in case and whitespace, and 12
are different literals, 11 of which share at least one name token with
their twin. No pair has a missing name. The audit did not attempt to
decide, for those 13, which literal is correct or whether the shared
numeric identifier was reused for two different people.

**Effect on the statistics this release reports.**

- The node counts above, in `graph_counts.json` and in `MANIFEST.md` §1
  include the duplicates: RAN3 is inflated by 181, RAN4 by 291, RAN5 by
  162, and the 966,859 total by 634 (0.066% of all nodes). The
  relationship counts are affected to whatever extent edges attach to the
  duplicate copies; this audit did not quantify that.
- The `Contact` entry of the label census in `graph_counts.json` reads
  4,935 and should be read as 4,301 distinct contacts.
- Two released benchmark items count `Contact` nodes directly:
  `RAN4_P1_CQ6-5` with gold `1133` and `RAN5_P1_CQ6-5` with gold `471`.
  Those gold values are **not** being corrected: gold in SpectraCQ v2.0
  is defined as full result-set re-execution against the released graph,
  and both are the correct answer for the graph as deposited. They are
  not the number of distinct contacts, which is 842 and 309.
- Any query that counts `Contact` nodes or groups by `contactId` in the
  three affected WGs over-counts by the amounts above. Grouping by
  `contactName` collapses the 621 identical-name pairs but leaves the 13
  differing pairs split.
- No other released count is derived from `Contact`.

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

The deposited TTL files are the authoritative artifact. They are produced
by an exporter that reads the five source Neo4j instances directly; that
exporter belongs to the authors' build pipeline and is **not part of this
release package**, because it is meaningless without those instances.

What a third party can run against the deposit is the reverse direction —
load the TTLs into a store of their own and re-derive the published
answer sets:

```bash
python3 release_package/pipeline/load_released_kg.py \
    --ttl release_package/kg/per_wg/RAN3-body.ttl \
    --bolt bolt://HOST:PORT --user neo4j --password PASSWORD

python3 release_package/tests/verify_benchmark.py --full --wg all \
    --bolt bolt://HOST:PORT --user neo4j --password PASSWORD
```

The loader writes into the store it connects to and `--full` wipes it
first, so point both at a scratch instance. See `../../tests/README.md`.

## Schema-only verification (no body text needed)

For the cross-WG generality numbers reported in the paper (§6 E4), use
the schema-instantiation TTLs in `../per_wg_schema/RAN{1..5}-schema.ttl`
(in this Git repo) and OWL-diff them against `../../ontology/spectra.ttl`.

## Contact

Issues and corrections: <https://github.com/spectra-ontology/spec-trace/issues>.
