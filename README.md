# SPECTRA: the 3GPP RAN standardization-process dataset

SPECTRA organizes public contributions, meeting decisions, change requests and
specification structure across the five RAN working groups. The released graph
snapshot contains 966,859 nodes and 4,908,850 relationships. SpectraCQ contains
624 released questions with executable reference queries and graph-derived answer
sets, from 654 authored questions. See the [counts manifest](release_package/MANIFEST.md)
for the per-group totals and the distinction between graph replay and question validity.

## Start here

- [Current original Core index](release_package/cqs/current_core/README.md): 400 of 560 original questions have passed the stated repair checks; 160 remain pending. Every ID links to its current contract and evidence. Ten existing IDs use full ranking pools without adding IDs.
- [Corrected SQL interface evaluation](release_package/cqs/original_core_sql_interface_evaluation/README.md): all 378 earlier contracts reevaluated with actual value-free DDL; F1 0.609694, 215 exact outputs and 32 failures, with complete raw evidence and offline replay.
- [Saved source-access diagnostic](release_package/cqs/source_access_diagnostic/README.md): a fixed 23-item analysis separates source, corpus and retrieved-context evidence; it does not establish full corpus equivalence.
- [Preserved 371 original-question repairs](release_package/cqs/original_core_repair/REVIEW_GUIDE.md): two separate AI semantic reviews, captured native references and requested-field scoring; the frozen cohort ledger retains its original 189 pending IDs.
- [New four-method evaluation](release_package/cqs/original_core_evaluation/README.md): new predictions on all 371 admitted contracts with one model, complete denominators, raw attempt records, execution failures and offline score replay.
- [Seven additional original-question repairs](release_package/cqs/original_core_additions/README.md) and their [new four-method predictions](release_package/cqs/original_core_additional_evaluation/README.md): a preserved, separate cohort records its then-current union of 378/560 and 182 pending; the current index above includes later repairs. The earlier 371 contracts and results are preserved.
- [Revised canonical Core contracts and itemized changes](release_package/cqs/canonical_core/REVIEW_GUIDE.md): 560 explicit revised definitions and native gold; 177 substantive variants, author/expert review pending; no new model results.
- [Evaluation scopes and evidence](release_package/cqs/contract_repair_v1/README_evaluation_scopes.md): how the current analyses relate to the original benchmark.
- [Release package](release_package/README.md): ontology, schema, examples, pipeline and known data-quality issues.
- [Historical benchmark and scoring](release_package/cqs/spectra_cq_v2.0/README.md) and [baseline records](paper/baseline/README.md).
- [Reproduction commands](release_package/tests/README.md) and [artifact walkthrough](release_package/ARTIFACT.md).

## Evaluation evidence

| Analysis | What it evaluates | Scope |
| --- | --- | --- |
| [Preserved original-question repairs](release_package/cqs/original_core_repair/README.md) | 371 repaired contracts retaining the exact original English questions; 119 keep the original query and 252 repair it | AI-assisted semantic checks, 776,873 captured native rows and 3,130 scorer controls; reference evidence and scorer checks; its frozen ledger has 189 pending and 0 blocked originals |
| [New original-question evaluation](release_package/cqs/original_core_evaluation/README.md) | Generated Cypher, generated SQL, single retrieval and two-round retrieval on the disjoint frozen 350+21 cohorts | One model; all 371 IDs per method; failures retained, paired uncertainty, and separate original-attempt/transport-recovery records; SQL generation and text-access limitations apply |
| [Additional original-question evaluation](release_package/cqs/original_core_additional_evaluation/README.md) | Seven further original questions with separately fixed repairs and newly generated four-method predictions | The preserved seven-item phase recorded a then-current union of 378 IDs; all seven additional IDs per method; original SQL interface retained; AI-assisted checks, no completed human/expert validation |
| [Current original Core](release_package/cqs/current_core/README.md) | 400 unchanged original questions and all 560 dispositions; 114 retain their original queries, 286 repair queries and scoring | Separate AI reviews, pinned native references and actual scorer controls; 160 remain pending; no completed human/expert validation |
| [Eight further original questions](release_package/cqs/original_core_followup_evaluation/README.md) | A separate four-method cohort with eight repaired original questions | All IDs and failures retained; earlier SQL schema interface; source uncertainty is explicit |
| [Five source-supported questions](release_package/cqs/original_core_source_evaluation/README.md) | Three responsibility-grounded questions and two named-catalog checks | Four methods receive the same whole sources, adding 62,603 input characters; strict JSON-envelope failures are preserved; this is a separate information intervention |
| [Six natural-identifier questions](release_package/cqs/original_core_natural_evaluation/README.md) | Tables/sections whose requested natural answers agree across all five collected editions | Fresh four-method predictions with actual SQL DDL; edition invariance within the frozen graph is not full-archive validation |
| [Three final original repairs and predictions](release_package/cqs/original_core_final_evaluation/README.md) | An ordered clause breadcrumb, a complete RAN4 CR-ranking pool and approval-qualified per-meeting RAN5 specification sets | Source-linked native execution and scorer controls; all three IDs per method; a pre-API sequence adapter correction and its first calls are preserved separately |
| [SQL interface intervention](release_package/cqs/original_core_sql_interface_evaluation/README.md) | Full 378-item rerun with actual physical DDL | F1 0.609694; 215/378 exact; 32 failures; paired uncertainty and unchanged-payload operational recovery; old contracts preserved |
| [Top-k replacements](release_package/cqs/original_core_topk_replacements/README.md) | Ten existing IDs retain full eligible pools for boundary-tie scoring | Corrects known boundary-choice rejection; adds zero original IDs; [fresh predictions](release_package/cqs/original_core_topk_evaluation/README.md) retain all ten IDs per method and preserve the earlier definitions/results |
| [Revised Core contracts](release_package/cqs/canonical_core/README.md) | 560 revised definitions with complete native reference outputs and requested-field scoring | 383 proposed clarifications; 177 substantive variants; author semantic review pending; no new model results |
| [31 original questions](release_package/cqs/contract_repair_v1/original_source_aligned/README.md) | Retained predictions on unchanged questions admitted by two AI contract checks and complete saved reference execution | Nine models, legacy answer-column scoring; no multihop item or independent expert validation |
| [36 formal task variants](release_package/cqs/contract_repair_v1/matched_retrieval_measurement/README.md) | Explicit named-field, typed complete-record scoring of single-pass text, two-round text and generated Cypher | Separate tasks; unequal graph/text access and unverified source-cutoff equivalence |
| [Core 560 and historical subsets](paper/baseline/README.md) | Original scores, whole-row sensitivity and retained SQL/Cypher reanalysis | The complete original question/scoring contract remains unfinished |

The [original-question repair bundle](release_package/cqs/original_core_repair/README.md)
is the task set for a new requested-field evaluation; use its itemized comparison
and full 560-ID disposition ledger when reviewing changes. Its 371 items include
all 31 historical diagnostic IDs and 340 others, but use repaired scoring
contracts. Earlier model scores remain under their original scopes and cannot be
transferred to these contracts. Two AI judgments are required per admitted repair;
human and independent domain-expert validation have not been completed.
The frozen 350-item scientific cohort and the further 21-item extension have
separate input pins; adding repair definitions does not silently extend an
existing experiment. The repair bundle's offline verifier and 46 regression
tests check its stored evidence and scoring behavior.
The [evaluation companion](release_package/cqs/original_core_evaluation/README.md)
contains new predictions under these contracts. It reports SQL relationship-table
naming failures and unequal text/structured information access rather than treating
the observed gap as a causal advantage of graph storage. The retained scores can
be replayed offline without credentials; fresh retrieval requires the pinned corpus.

The historical 45-question diagnostic and the current 31-question diagnostic use
different criteria; they overlap on 15 IDs and neither contains the other. The
36 variants share no original-question IDs with the 31. Their scores must remain
separate. AI checks and query-derived answers do not provide independent expert
validation. Missing-information abstention and transfer outside RAN remain untested.

The [scope guide](release_package/cqs/contract_repair_v1/README_evaluation_scopes.md)
also distinguishes graph Section structure from retained text excerpts, direct
links from contextual joins, liaison-count populations, historical Table 14
results from later replays, and text-body passage limits from metadata.

## Get the data

The Git repository includes the ontology, benchmark, metadata-only process graphs,
construction code and retained evaluation inputs and outputs. The five larger
`RAN{1..5}-body.ttl` graphs are distributed separately in the
[archived release](https://doi.org/10.5281/zenodo.21504833), version 2.0.0.
The [body-graph inventory](release_package/kg/per_wg/README.md) explains placement,
counts and known data-quality issues. The full text-ranking corpus is not deposited.

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

python3 -I -B release_package/cqs/contract_repair_v1/original_source_aligned/score_source_aligned_retained_portable_v1.py \
  --bundle release_package/cqs/contract_repair_v1/original_source_aligned \
  --public-root . \
  --expected-manifest-sha256 ef37ec7f075c7d51d87406d20e6c55f050213ef9942eab6cf53cb27277f29813

python3 -B release_package/cqs/contract_repair_v1/matched_retrieval_measurement/matched_analysis.py \
  --require-complete --out /tmp/spectra-strict-record-replay.json
```

The quick gate checks the Git-only release without a database. Five additional
checks require the body-graph deposit. The score replays read retained outputs;
they make no model or database calls and do not reproduce the full text-ranking
stage. Use a new output filename for the strict-record replay, which refuses to
overwrite an existing report. Full graph replay requires a scratch database;
follow the [test guide](release_package/tests/README.md) before running it.

## Citation and license

Use [CITATION.cff](release_package/CITATION.cff),
[CodeMeta](release_package/codemeta.json) or the
[SpectraCQ citation](release_package/cqs/spectra_cq_v2.0/citation.bib).
SPECTRA-authored components are licensed under CC BY 4.0. 3GPP-derived text
retains separate source attribution and is not relicensed as SPECTRA-authored
content; see the [package license](release_package/LICENSE).

Maintainer: Sihyeon Choi, Samsung Electronics. Questions and corrections:
[repository issues](https://github.com/spectra-ontology/spec-trace/issues).
