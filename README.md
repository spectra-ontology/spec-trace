# SPECTRA: tracing the 3GPP standardization process

SPECTRA connects technical contributions, recorded meeting decisions, change
requests, and specification structure across all five 3GPP RAN working groups.
Its shared process model makes relationships spread across document registers,
meeting reports, and specification metadata available to executable queries.

The released snapshot contains **966,859 nodes, 4,908,850 relationships, and
12,931,842 RDF triples**. SpectraCQ supplies **624 released questions** with
executable references, including a **560-question Core register** and **514
audited original-question contracts**. The [counts manifest](release_package/MANIFEST.md)
links dataset totals to their artifacts and measurement procedures.

## What the release provides

- **A queryable process model.** The [32-class ontology](release_package/ontology/spectra.ttl)
  represents submissions, resolutions, liaison routing, CR metadata, and
  specification targets. Explicit document references, shared-meeting context,
  and declared clause targets retain their distinct meanings.
- **Executable process questions.** The [current Core index](release_package/cqs/current_core/README.md)
  links each admitted question to its original wording, requested fields and
  types, collection and ranking rules, reference records, and verification evidence.
- **Reproducible method evaluation.** Released cohorts preserve model inputs,
  generated Cypher and SQL, retrieval responses, execution results, and
  complete-record scoring. Offline tools replay saved results without model calls.

The verified contracts make process-level operations concrete: a Work Item
query returns five nested company-ranking records with top-boundary ties; a
decision trace links 2,351 recorded paths to ten requested Specification
identities; and a CR-approval query reproduces fifteen Agreement identities
from an original-source-checked selection prefix. The current index connects
these tasks to their full reference records, source witnesses, independent
SQL/native comparisons and saved four-method evaluations. Source-verified CR
approval tracing links eight requested Resolution identities to ten complete
Resolution/CR witness pairs and an auditable source-selection frontier, with a
[saved four-method replay](release_package/cqs/original_core_overnight_evaluation42/README.md). The approved-change
metadata case links five CR identifiers to complete reasons and summaries, with
eight original source archives, ten cover fields and a
[saved four-method replay](release_package/cqs/original_core_overnight_evaluation41/README.md).

A [decision-to-Spec replay](release_package/cqs/original_core_overnight_evaluation43/README.md)
connects ten requested Spec identities to active same-CR source outcomes and
formal-register targets. Complete native output, the 57-Spec selection frontier
and all five saved first responses make identity recovery and selection
precision directly reproducible.

## Start with the current benchmark

Use [current_tasks.jsonl](release_package/cqs/current_core/current_tasks.jsonl)
to select the 514 current contracts and their pinned evidence bundles. The
[index manifest](release_package/cqs/current_core/index_manifest.json) connects
the active definitions to their original repair and evaluation cohorts.

The [all-560 disposition register](release_package/cqs/core_disposition_audit/README.md)
accounts for every original Core ID: **514 contract-verified, 21 requiring
clarification, 11 unsupported by the pinned frozen data, and 14 awaiting completed
evidence checks**. Historical definitions and results remain available alongside
the current register.

| Explore | Released resource |
| --- | --- |
| Ontology, graph data, and construction | [Release package](release_package/README.md), [body graphs](release_package/kg/per_wg/README.md), [pipeline](release_package/pipeline/README.md) |
| Question contracts and reference answers | [Current Core](release_package/cqs/current_core/README.md), [original collection](release_package/cqs/spectra_cq_v2.0/README.md) |
| Four-method evaluation | [Twelve-question cohort](release_package/cqs/original_core_overnight_evaluation15/README.md), [named-record cohort](release_package/cqs/original_core_overnight_evaluation24/README.md), cohort links in the [current index](release_package/cqs/current_core/index_manifest.json) |
| Source-linked extensions and diagnostics | [Source evidence guide](release_package/cqs/source_supplements_README.md), [RAN2 summaries](release_package/cqs/original_core_source_RAN2_CR_summary240_evaluation/README.md), [RAN3 summaries](release_package/cqs/original_core_source_RAN3_CR_summary202_evaluation/README.md) |
| Retained experiments and scoring definitions | [Evaluation scope guide](release_package/cqs/contract_repair_v1/README_evaluation_scopes.md), [historical analyses](paper/baseline/README.md) |
| Run and inspect the artifacts | [Reproduction guide](release_package/tests/README.md), [artifact walkthrough](release_package/ARTIFACT.md) |

## Evaluation examples

The four-method protocol compares generated queries over SPECTRA's structured
records with single and two-round retrieval over bounded text contexts. The
following two separately registered cohorts illustrate the released evaluation;
each retains its own questions, inputs, and denominator.

| Method | Twelve-question macro F1 | Named-record macro F1 (N=3) |
| --- | ---: | ---: |
| Text2Cypher | 0.5833 | 1.0000 |
| Text2SQL | 0.4333 | 1.0000 |
| Single retrieval | 0.0000 | 0.0000 |
| Two-round retrieval | 0.0833 | 0.3333 |

In the named-record cohort, both structured methods return the complete requested
records for all three questions. The twelve-question cohort has exact outputs
on five questions for Cypher and four for SQL. Every method retains all cohort
items in its denominator, including errors and abstentions. The linked packages
provide the actual prompts, source access, reference contracts, first responses,
and score replays. These are cohort results; the 514-contract index records
benchmark definitions and their evidence.

## Get the data

The Git repository includes the ontology, benchmark, metadata-only process graphs,
construction code and retained evaluation inputs and outputs. The five larger
`RAN{1..5}-body.ttl` graphs are distributed separately in the
[archived release](https://doi.org/10.5281/zenodo.21504833), version 2.0.0.
The [body-graph inventory](release_package/kg/per_wg/README.md) documents graph placement,
counts, and source-quality annotations. Evaluation cohorts preserve selected retrieval
passages and source identifiers.

The [concept DOI](https://doi.org/10.5281/zenodo.20034871) locates the latest
archived version. Later Git additions are separate from those frozen archives;
cite the Git commit used for an evaluation. The ontology is version 1.1.1;
its persistent identifier is [w3id.org/spectra](https://w3id.org/spectra).

## Reproduce from a Git checkout

Run from the repository root. The release checks need `rdflib` and `pyshacl`;
the two retained-score replays below need only Python 3.10 or later.

```bash
pip install rdflib pyshacl
python3 -B release_package/tests/verify_benchmark.py --quick --out /tmp/spectra-quick-check

python3 -B -I release_package/cqs/verify_current_release.py

python3 -I -B release_package/cqs/contract_repair_v1/original_source_aligned/score_source_aligned_retained_portable_v1.py \
  --bundle release_package/cqs/contract_repair_v1/original_source_aligned \
  --public-root . \
  --expected-manifest-sha256 ef37ec7f075c7d51d87406d20e6c55f050213ef9942eab6cf53cb27277f29813

python3 -B release_package/cqs/contract_repair_v1/matched_retrieval_measurement/matched_analysis.py \
  --require-complete --out /tmp/spectra-strict-record-replay.json
```

The quick gate checks the Git-only release without a database. Five additional
checks require the body-graph deposit. The score replays use retained outputs and
saved contexts and make no model or database calls. Re-running passage ranking
requires the original full-text corpus, which is outside the deposited artifacts.
Use a new output filename for the strict-record replay, which refuses to overwrite
an existing report. Full graph replay requires a scratch database; follow the
[test guide](release_package/tests/README.md) before running it.

## Citation and license

Use [CITATION.cff](release_package/CITATION.cff),
[CodeMeta](release_package/codemeta.json) or the
[SpectraCQ citation](release_package/cqs/spectra_cq_v2.0/citation.bib).
SPECTRA-authored components are licensed under CC BY 4.0. 3GPP-derived text
retains separate source attribution and is not relicensed as SPECTRA-authored
content; see the [package license](release_package/LICENSE).

Maintainer: Sihyeon Choi, Samsung Electronics. Questions and corrections:
[repository issues](https://github.com/spectra-ontology/spec-trace/issues).
