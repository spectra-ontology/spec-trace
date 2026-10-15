# SPECTRA: the 3GPP RAN standardization-process dataset

SPECTRA organizes public contributions, meeting decisions, change requests and
specification structure across the five RAN working groups. The released graph
snapshot contains 966,859 nodes and 4,908,850 relationships. SpectraCQ contains
624 released questions with executable reference queries and graph-derived answer
sets, from 654 authored questions. See the [counts manifest](release_package/MANIFEST.md)
for the per-group totals and the distinction between graph replay and question validity.

## Start here

- [Current original Core index](release_package/cqs/current_core/README.md): 451 of 560 original questions have passed the stated repair checks; 109 remain pending. Every ID links to its current contract and evidence. Ten existing IDs use full ranking pools without adding IDs.
- [Five source-table corrections](release_package/cqs/original_core_source_table_correction5/README.md): authentic source tables, full native/SQL controls and separate CQ008/CQ041 model evaluations; a preserved cache-inventory failure has a dependency-only correction.
- [168 authored CR clause observations](release_package/cqs/original_core_source_authored_clause168/README.md) and their [separate four-method evaluation](release_package/cqs/original_core_source_authored_clause168_evaluation/README.md): exact original cover-cell strings, full434 reference tuples and 24 controls. Both generated queries omit the added source property and target-release restriction; these scores do not establish predicate correctness or causal improvement. These separate source snapshots add no frozen original-Core passes.
- [Additional 37 original-question repairs](release_package/cqs/original_core_overnight_repairs37/README.md) and their [fresh four-method evaluation](release_package/cqs/original_core_overnight_evaluation37/README.md): complete native/SQL evidence, 283 scorer controls and all 37 IDs per method. F1 is 0.4350/0.5637/0.0002/0.0000; raw responses, failures and strict replay are included. Historical 404 contracts and scores are preserved.
- [Two later original-question repairs](release_package/cqs/original_core_overnight_repairs2/README.md) and their [fresh four-method evaluation](release_package/cqs/original_core_overnight_evaluation2/README.md): a separate cohort retains both IDs, actual model responses and full execution/scoring evidence; it raises the current index to 443 original questions.
- [One Rel-19 recorded-document survey repair](release_package/cqs/original_core_overnight_repairs4/README.md) and its [fresh four-method evaluation](release_package/cqs/original_core_overnight_evaluation4/README.md): all 5,948 recorded release-associated TDocs, with the unchanged English and 20 actual scorer controls; raises the current original-question index to 448.
- [One recorded TS-comparison repair](release_package/cqs/original_core_overnight_repairs1/README.md) and its [fresh four-method evaluation](release_package/cqs/original_core_overnight_evaluation1/README.md): a separate cohort compares the top five TS families by CR count against their section counts in the original explicit domain; it raises the current index to 447 original questions.
- [Three recorded title-and-table repairs](release_package/cqs/original_core_overnight_repairs3/README.md) and their [fresh four-method evaluation](release_package/cqs/original_core_overnight_evaluation3/README.md): a separate cohort preserves all three IDs, typed nested table-ID sets and actual model responses with full execution/scoring evidence; it raises the current index to 446 original questions.
- [Two observed-trend repairs](release_package/cqs/original_core_observed_trend_repair/README.md) and their [new four-method evaluation](release_package/cqs/original_core_observed_trend_evaluation/README.md): included in the current451 questions; complete stored-meeting series and strict scoring are explicit, with errors and abstentions retained.
- [One source-enriched RAN2 repair](release_package/cqs/original_core_source_enriched_repair/README.md) and its [four-method evaluation](release_package/cqs/original_core_source_enriched_evaluation/README.md): nine official forwarding covers support nine missing CR packs and a complete 35-pack RAN2/RAN#110 reference. Its enriched snapshot remains separate from the current451-item frozen-graph scope.
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
| [Current original Core](release_package/cqs/current_core/README.md) | 451 unchanged original questions and all 560 dispositions; 117 retain their original queries, 334 repair queries and scoring | Separate AI reviews, pinned native references and actual scorer controls; 109 remain pending; no completed human/expert validation |
| [Explicit named Agreement repair](release_package/cqs/original_core_named_agreement_repairs/README.md) | One further unchanged original question with its named draft-CR agreement decision checked in the original meeting report | Two separate AI reviews, two full native rows identifying one Agreement, and seven strict scorer controls; [four-method predictions](release_package/cqs/original_core_named_agreement_evaluation/README.md) are retained separately; text identifier access differs |
| [Resolution-to-CR-to-spec ranking repair](release_package/cqs/original_core_path_top5_repairs/README.md) | One further unchanged original question with a complete 139-spec pool | The requested five spec identities agree across four counting units; numerical counts and order differ. Two separate AI reviews, complete native rows and nine scorer controls; [four-method predictions](release_package/cqs/original_core_RAN3_path_evaluation/README.md) are retained separately |
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

The preserved [original-question repair bundle](release_package/cqs/original_core_repair/README.md)
defines the earlier task set for a new requested-field evaluation. Use the
[current index](release_package/cqs/current_core/README.md) for the latest contracts
and full 560-ID disposition ledger. The preserved bundle's 371 items include
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

The separate original-question cohort 5 adds `RAN1_P3_CQ038`: Return the top 10 most-referenced sections and how many CRs modified each (stability of core sections). Its complete retained reference pool and fresh four-method evaluation are in `release_package/cqs/original_core_overnight_repairs5` and `release_package/cqs/original_core_overnight_evaluation5`. The current index is 449/560, with 111 pending. Earlier cohorts and measurements remain separate; human and expert validation remain incomplete.

The separate original-question cohort 6 adds `RAN2_P2_CQ3-2`: Rank the main contributors to spec 38.331 (RRC ownership). Its complete retained reference pool and fresh four-method evaluation are in `release_package/cqs/original_core_overnight_repairs6` and `release_package/cqs/original_core_overnight_evaluation6`. The current index is 450/560, with 110 pending. Earlier cohorts and measurements remain separate; human and expert validation remain incomplete.

The separate Qualcomm recent-ten Agreement evaluation uses retained source-reported Meeting periods and preserves all five first-call responses; all four methods abstained. Its full 1,094-Agreement reference pool, source provenance, fifteen scorer controls and offline prompt/parse/score replay are in [the separate evaluation companion](release_package/cqs/original_core_source_Meeting_calendar60_Qualcomm_Agreement_evaluation/README.md). This source snapshot does not change the frozen index of 450/560 original questions (110 pending). Reported Meeting periods do not establish approval or causal contribution.

The separate TS38.133 recent-ten CR evaluation supplies all 342 retained Word report bodies and four complete PPTX XML-text packages, together with 58 source-reported Meeting periods. Its [whole-source evaluation and replay](release_package/cqs/original_core_source_Meeting_calendar58_whole_evaluation/README.md) preserve all five first-call responses, full 16,017-CR reference, 23 controls and exact raw-input shards. Record F1 is 0/1/0/0 for Cypher/SQL/single/two-round retrieval. Both generated structured queries use uploadedDate rather than the added Meeting dates; actual NULL placement explains their different returned date groups. These saved record scores do not establish calendar-predicate correctness, approval or causal improvement. This source snapshot leaves the frozen original-question index at 450/560 with 110 pending.

The separate original-question cohort 7 adds `RAN5_P3_CQ5-2`: Show each company's CR contributions per RAN5 spec (contribution matrix). Its complete retained reference pool and fresh four-method evaluation are in `release_package/cqs/original_core_overnight_repairs7` and `release_package/cqs/original_core_overnight_evaluation7`. The current index is 451/560, with 109 pending. Earlier cohorts and measurements remain separate; human and expert validation remain incomplete.

The separate [UL Tx switching formal-source evaluation](release_package/cqs/original_core_source_UL_formal6_evaluation/README.md) preserves the unchanged Agenda5.1 at RAN1#100 question and all five first-call responses. Six complete formal Agreement bodies and the full 6,017-paragraph original report accompany 19 scorer controls. Requested-record F1 is 0.5/0/0/0 for Cypher/SQL/single/two-round retrieval. The graph query used old content (three exact matches out of six); the SQL query returned no rows. No improvement caused by the new source property is established. This separate snapshot does not change the frozen original-question index (451/560; 109 pending).
