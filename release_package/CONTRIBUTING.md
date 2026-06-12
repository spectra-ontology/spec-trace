# Contributing to SPECTRA

SPECTRA is maintained as a living resource (see `RELEASE_PROCESS.md` for
the release cadence and versioning policy). Contributions are welcome in
four areas.

## 1. Competency questions (SpectraCQ)

The CQ benchmark (`cqs/spectra_cq_v1.0/`) is designed to grow beyond its
current 137 entries. To propose a CQ:

1. Open a **CQ request** issue (template provided in the repository) with
   the natural-language question, the lifecycle phase it targets
   (P1 contribution / P2 decision / P3 spec structure / P4 CR / P5 TR),
   and — if you can — a candidate Cypher or SPARQL formulation.
2. A CQ is accepted when (a) it is answerable from SPECTRA-conformant
   data, (b) it is not a duplicate of an existing CQ, and (c) its
   reference query returns a non-empty result on the released per-WG KGs.
3. Accepted CQs are added to `questions.json` with both a Cypher file
   (`cypher/`) and a SPARQL translation (`sparql/`), and enter the
   regression suite run by `pipeline/run_cq_suite.py`.

## 2. Ontology extensions

Schema changes follow semantic versioning (`ontology/spectra.ttl` header):

- **Patch** — comments, labels, typos.
- **Minor** — new classes/properties that do not alter existing semantics.
- **Major** — removals, domain/range narrowing, IRI changes.

Open an **ontology extension** issue describing the standardization
phenomenon the current schema cannot express, ideally with a real 3GPP
document instance that motivates it. Extensions must keep the 137-CQ
regression green (`pipeline/run_cq_suite.py` against a loaded release KG)
and pass SHACL (`shapes/spectra-core.shacl.ttl`).

## 3. Instantiations for other working groups or SDOs

The pipeline under `pipeline/` parses 3GPP meeting artifacts into
SPECTRA-conformant RDF. Ports to other WGs (or other SDOs with a
contribution → decision → change-request → versioned-spec lifecycle) are
welcome; please share a schema diff (see
`validation/cross_wg_schema_diff.json` for the format we use) so the
generality evidence stays measurable.

## 4. Bug reports

Use the **bug report** issue template. For data bugs, include the
affected IRI(s) and the source 3GPP document (TDoc number / meeting) so
the parser fix can be regression-tested.

## Verification before submitting a PR

```bash
python3 tests/verify_release.py            # deterministic release checks
python3 pipeline/run_cq_suite.py --help    # CQ regression (needs a loaded KG)
```

Licensing: SPECTRA-authored contributions are accepted under CC-BY 4.0
(`LICENSE` Tier 1). Do not contribute 3GPP body text beyond what the
Tier 2 attribution terms already cover.
