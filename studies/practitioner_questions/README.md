# Practitioner questions and traceability subqueries

This collection connects 33 recorded engineering question units with the traceability fields they request. It provides short English technical paraphrases, the two existing classifications, source-byte hashes and two executable illustrations of a record subquery followed by a remaining engineering judgment. The 33 units come from 30 cases, including three follow-ups, and provide a convenience sample of practical requests.

Start with [question_analysis.json](question_analysis.json) for all 33 paraphrases and classifications. These are paraphrases of recorded asks; the source text and contact metadata remain in the private originals. The labels are the existing first classification and existing independent agent classification. The second agent received the definitions, family examples and question files with the first classifications and measurement outputs withheld. This projection preserves their judgments.

## What the question analysis shows

The first classification contains 28 interpretation units, four mixed units and one process-trace unit. The two classifiers agree on all 33 types and on four of the five process/mixed family mappings. The five process/mixed requests are:

| Unit | Short topic | First family mapping | Second family mapping | Requested component beyond the benchmark fields |
|---|---|---|---|---|
| U003 | Emergency-services test timer, RRCRelease and R5-253194 background | none | partial: full_chain | rationale, discussion, cross-specification correspondence |
| U004 | PC1.5 wording across TS 38.101 releases | partial: clause_history | partial: clause_history | reason for the wording difference |
| U015 | NR-NTN RACH-less handover implementation and fallback | none | none | standardization debate |
| U021 | CDM2 CSI-RS per-port power interpretation | none | none | meeting discussion |
| U023 | Enhanced Type 2 CSI part 2 omission | none | none | discussion and agreement content |

U004 explicitly requests two of the six benchmark elements: clause-to-CR history and the WG meeting associated with a disposition. The other four process/mixed units request content outside those elements under the first classification. The U003 disagreement remains visible in the data. These classifications describe the requested components in this collection; they are separate from a measured ability to answer a complete engineering question.

## A question, an anchored subquery and the remaining explanation

[workflow_example.json](workflow_example.json) preserves the existing U004 derivation. The requester reports PC1.5 wording in TS 38.101 v16 and its absence in v17, and asks why and whether a meeting discussed it. The original request leaves the specification part and exact editions unspecified. The existing inspection locates the wording in TS 38.101-1 clause 6.2.1, version 16.26.0, and observes its absence in the available version 17.21.0.

The derived subquery asks for Rel-17 CRs modifying clause 6.2.1 that have a whole-target, source-verified RAN4 disposition and appear in a TSG RAN CR pack. Both SQL formulations return the same 28 rows in the released database, with fields `document`, `disposition`, `wg_meeting` and `cr_pack`. For example:

<!-- BEGIN REPLAY:clause_history -->
| document | disposition | wg_meeting | cr_pack |
|---|---|---|---|
| R4-2115103 | agreed | RAN4#100-e | RP-211901 |
<!-- END REPLAY:clause_history -->

An additional Rel-16 context lookup returns:

<!-- BEGIN REPLAY:rel16_context -->
| document | disposition | wg_meeting | cr_pack |
|---|---|---|---|
| R4-2211252 | agreed | RAN4#103-e | RP-221655 |
<!-- END REPLAY:rel16_context -->

The existing body inspection records insertion of the wording in this CR. Explaining the cross-release difference still requires source-content interpretation and the requester's exact editions. The 28 Rel-17 rows are a clause-history answer, with the original question retaining its partial mapping.

The frozen final derivation supplies the query, 28 rows and released-database hash. The root derivation additionally supplies the existing wider body inspection, including R4-2208744 and R4-2212773 as context outside those 28 rows. Their source versions are distinguished in [source_hashes.json](source_hashes.json). The source-report outcome `not_treated` for R4-2100119 remains in the rows alongside its recorded contribution-list `agreed` discrepancy. [Direct native-source inspection](row_source_binding.json) verifies that this report decision names CR0589/Rel-17 and that RP-210190 contains the matching native CR form with clause 6.2.1 affected. The row preserves both recorded facts; explaining their outcome discrepancy requires further evidence. The existing predicate controls return the same rows for this anchor.

<!-- BEGIN REPLAY:source_discrepancy -->
| document | disposition | wg_meeting | cr_pack |
|---|---|---|---|
| R4-2100119 | not_treated | RAN4#98-e | RP-210190 |
<!-- END REPLAY:source_discrepancy -->

## A separately selected coordination illustration

[posthoc_record_illustration.json](posthoc_record_illustration.json) connects an actual RAN5 coordination proposal to a record lookup. Its technical paraphrase asks for listed RAN5 CRs to be marked agreed after a reported RAN4 dependency clearance and cites `R4-2605846 → R4-2607530`.

The released RAN4 graph returns that revision edge with `revised` and `agreed` whole-target, source-verified dispositions at `RAN4#119`. Direct inspection of `Final_Report_RAN4-119.docx`, SHA-256 `d3d80891015201292655d043d2fe892cc6e3c2f9d76f6fc5f1425a7f4beb6db7`, confirms the named revision and agreement; accepted-body block locators and entry hashes are recorded in the illustration. Deciding whether the change clears each RAN5 dependency or requires another RAN5 revision remains a cross-WG engineering judgment.

<!-- BEGIN REPLAY:coordination -->
| earlier_document | later_document | earlier_disposition | earlier_wg_meeting | later_disposition | later_wg_meeting |
|---|---|---|---|---|---|
| R4-2605846 | R4-2607530 | revised | RAN4#119 | agreed | RAN4#119 |
<!-- END REPLAY:coordination -->

This illustration was selected after the question analysis for an explicit pair present in the graph. It remains outside the 33-unit collection and its rates. Its status is curated source/record inspection. Source-file and original-span hashes bind the paraphrase to the existing illustration without distributing the message's contacts or embedded nonpublic URL.

## Offline replay

From the package root, using Python 3.11 or later:

```sh
python3 studies/practitioner_questions/replay.py --out work/practitioner_questions/replay.json
```

The standard-library script verifies this folder's checksums and the released RAN4 database hash, decompresses the database into a temporary directory, recomputes the 33-unit counts and disagreement, replays both 28-row SQL formulations, checks the Rel-16 context row and replays the separate revision/disposition lookup. All four README record-example tables are generated from these query rows and checked against them during replay. It opens SQLite in read-only mode. The expected public result is [replay_receipt.json](replay_receipt.json): `PASS`, 28 rows per clause-history formulation, one separate revision/outcome row and four matching README tables.

For maintainers, `--refresh-readme-examples` regenerates the four marked tables after executing the verified queries. It reports `README_UPDATED`; refresh this folder's checksums and run the public replay afterward. Replay reports are written outside this package folder. The stored receipt records query and README checks; the separate checksum manifest covers the completed artifact files.

The stored Cypher agreement and document-body observations retain the status of the existing derivations. This command replays the public record queries; inspection of original standards content follows the package's [source restoration and reproduction guidance](../../REPRODUCING.md). The [main benchmark](../../BENCHMARK.md) and other [experimental interfaces](../../EXPERIMENTS.md) retain their own populations and procedures.

For an authorized local audit, `--private-source-root BASE --private-cases-root CASES` additionally verifies all recorded source-file hashes and the projected first/second labels against their private inputs. `BASE` contains the four practitioner JSON sources and the `final/` copies; `CASES` is the private question-case root. `--private-illustration-source FILE` also verifies the separate message and its original span hash. These optional checks emit counts and verification status.

| File | Purpose |
|---|---|
| `question_analysis.json` | 33 paraphrases, existing classifications, aggregate counts and preserved disagreement |
| `workflow_example.json` | Existing U004 derived query, 28 rows, context, source versions and remaining interpretation |
| `posthoc_record_illustration.json` | Separately selected coordination proposal, source hashes and returned revision/outcome row |
| `row_source_binding.json` | Native report/pack identity audit for the retained R4-2100119 row and its outcome discrepancy |
| `source_hashes.json` | Hashes of all available private question files and the source analyses |
| `replay.py` | Public aggregation/query replay and optional private byte/label verification |
| `replay_receipt.json` | Executed public replay result |
| `SHA256SUMS.txt` | Checksums for this folder |
