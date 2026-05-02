# TUTORIAL — Instantiating SPECTRA on Your Own SDO Process

This tutorial walks through reusing the SPECTRA ontology to model a different
standardization-developing organization (SDO). The goal is to demonstrate
that SPECTRA's four-concern structure (contributions, resolutions,
specifications, cross-group communication) is a portable schema rather than
a 3GPP-specific encoding.

The walkthrough is intentionally hands-on and uses only files inside this
release package — no Neo4j, no internal data, no copyrighted text.

---

## Prerequisites

```bash
pip install rdflib pyshacl
```

Optional: Protégé for visual schema browsing; Neo4j for a queryable target.

---

## Tutorial sections

1. [Mapping your SDO to SPECTRA's four concerns](#1-mapping)
2. [Walking the synthetic example end-to-end](#2-walking-the-synthetic-example-end-to-end)
3. [Drafting your own instantiation snippet](#3-drafting-your-own-instantiation-snippet)
4. [Validating with SHACL](#4-validating-with-shacl)
5. [Extending the schema (when, and when not)](#5-extending-the-schema)
6. [Authoring competency questions](#6-authoring-competency-questions)

---

## 1. Mapping

Most standards-developing organizations share a common process backbone:

| SPECTRA concern | What it captures | 3GPP example | IETF analogue (illustrative) |
|---|---|---|---|
| Contribution | A submitted document a meeting will discuss | TDoc | Internet-Draft |
| Resolution | A working-group decision tied to a meeting + agenda | Agreement, Conclusion, Working Assumption | WG decision (mailing-list / interim minutes) |
| Specification | The normative text the lifecycle eventually changes | TS, TR, Section, Table, Figure | RFC, RFC section |
| Cross-group communication | Coordination messages between groups | LS (Liaison Statement) | Liaison statement / Last Call announcement |

Before instantiating, **list the four entity types in your SDO that fill these
roles**. If two of them collapse (e.g., your SDO does not separate
contributions from resolutions), use the `Tdoc` / `Resolution` classes
both with the same `presentedAt` link to the meeting — the schema does not
forbid the collapse.

If your SDO has a fifth concern that does not fit (e.g., conformance test
suites, distinct from the above), see Section 5 below.

---

## 2. Walking the Synthetic Example End-to-End

Open `examples/end_to_end/`:

```bash
cat examples/end_to_end/data.ttl    # 4-hop scenario
cat examples/end_to_end/query.sparql
cat examples/end_to_end/expected_output.txt
python3 tests/test_e2e_sparql.py    # runs query, prints PASS
```

The data file shows the **minimum subset of triples** needed for an S1
multi-hop trace: `Section -> belongsToSpec -> Spec`,
`CR -> modifiesSection -> Section`, `CR -> presentedAt -> Meeting`,
`Resolution -> madeAt -> Meeting`, `Resolution -> references -> Tdoc`.

If your SDO has the same lifecycle, **substitute your IRIs and re-run the
same query** — the structural pattern is identical.

---

## 3. Drafting Your Own Instantiation Snippet

Start from `examples/instantiation_snippet.ttl` (small, single-meeting
synthetic example). Make a copy:

```bash
cp examples/instantiation_snippet.ttl my_sdo_snippet.ttl
```

Replace synthetic IDs with your SDO's identifiers, keeping the **predicate
names** (`spectra:tdocNumber`, `spectra:presentedAt`, `spectra:modifies`,
etc.). The local-name shape (`my_sdo:RFC8200`, `my_sdo:WG_TLS_113`, …) is
free — only the prefixed predicate names are normative.

A useful checkpoint is to ensure each lifecycle class is exercised at least
once:

```bash
grep -c '^[^[:space:]].*a spectra:Tdoc' my_sdo_snippet.ttl
grep -c '^[^[:space:]].*a spectra:Resolution' my_sdo_snippet.ttl
grep -c '^[^[:space:]].*a spectra:Section' my_sdo_snippet.ttl
grep -c '^[^[:space:]].*a spectra:Meeting' my_sdo_snippet.ttl
```

---

## 4. Validating with SHACL

```bash
pyshacl -s shapes/spectra-core.shacl.ttl my_sdo_snippet.ttl
# Expected: "Conforms: True"
```

If pyshacl reports violations, inspect them by category:

| Violation category | Likely cause |
|---|---|
| `tdoc:tdocNumber sh:minCount 1` | A `Tdoc` instance is missing its document identifier |
| `presentedAt sh:class spectra:Meeting` | The presentedAt target is not declared as `a spectra:Meeting` |
| `modifies sh:class spectra:Spec` | The modifies target is not declared as `a spectra:Spec` |
| `LSShape ...` | A `spectra:LS` instance is missing one of the lifecycle edges |

Note that `shapes/spectra-core.shacl.ttl` is intentionally relaxed in three
places (`LSShape.originatedFrom`, `LSShape.sentTo`, `CRShape.modifies`,
`TdocShape.presentedAt` — `sh:maxCount` removed) to admit real-world
upstream-data realities; the rationale is documented inline in that file
and in Appendix G of the paper.

---

## 5. Extending the Schema

Before adding new classes, follow the cross-WG generality protocol used in
the paper:

1. **Look first.** Check `validation/per_wg_class_coverage.json` and
   `validation/cross_wg_schema_diff.json` to see whether SPECTRA already
   covers the concept under a different name.
2. **Subclass before adding a peer.** If your concept is a specialization
   of an existing lifecycle class (e.g., a particular kind of `Tdoc`),
   declare it as `rdfs:subClassOf spectra:Tdoc` rather than as a new
   top-level class.
3. **Loader-local vs ontology-level.** A property that appears in only one
   organization's loader output should remain in your own namespace — do
   not back-port it to `spectra:` unless ≥3 organizations need it.
   This mirrors the schema-diff treatment described in §6.4 and
   Table~\ref{tab:crosswg-reuse} of the paper.
4. **File an issue.** Use `.github/ISSUE_TEMPLATE/ontology-extension.md`
   to propose ontology-level changes; this is how schema evolution is
   tracked across releases.

---

## 6. Authoring Competency Questions

`cqs/spectra_cq_v1.0/questions.json` and `cqs/spectra_cq_v1.0/cypher/`
together form a 137-CQ benchmark. Each entry has:

- a natural-language question (organisation-agnostic; concrete companies
  appear as "Company X", "Company Y", …);
- an executable Cypher specification (Neo4j 4.x syntax);
- a phase tag (P1–P5);
- a per-CQ verdict on the released RAN1 KG.

To author your own CQ:

1. Express the question in plain English first.
2. Identify the lifecycle classes it touches (one CQ may legitimately span
   `Tdoc`, `Resolution`, `Section`, and `Spec`).
3. Translate the question to a Cypher MATCH pattern; keep the Neo4j syntax
   conventions used in the existing 137 cyphers (`:LABEL` for class,
   `[:RELATIONSHIP]` for object property, property dot-access for data
   property).
4. Validate the query returns at least one row on a SPECTRA-conformant
   instantiation. The bundled `examples/end_to_end/data.ttl` is the
   smallest target.
5. File the CQ via `.github/ISSUE_TEMPLATE/cq-request.md` if you would
   like it incorporated into a future SpectraCQ release.

---

## Where next

- **Schema reference:** `diagrams/schema_overview.md`, `docs/spectra.html` (PyLODE)
- **Reviewer-friendly verification path:** `ARTIFACT.md`
- **Anonymization policy:** `README.md` § "Anonymization policy (asymmetric by design)"
- **Background on the cumulative CQ practice that produced SPECTRA:**
  Section 5 and Appendix D of the paper
