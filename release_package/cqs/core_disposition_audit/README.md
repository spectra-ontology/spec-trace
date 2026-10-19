# Core disposition audit

This diagnostic overlay accounts for all 560 original questions: **476 contract-verified, 10 requiring clarification, and 74 with evidence verification incomplete**. The ten comprise five unresolved operational metrics and five missing required inputs. The existing current-core index remains 476 admitted and 84 nonadmitted. Reclassifying those 84 adds no solved question, model score, human review, or expert validation.

The classification uses the pinned current **question-first semantic review criteria**: derive the requested meaning from the original English and preserved source context before checking a query. This scope matters. The original queries already choose executable metrics, and the legacy query-derived contracts record their ordering and cutoffs. **If those queries are adopted as the normative task specification, the corresponding operational choice is fixed.** These diagnostics then show sensitivity to a different chosen metric, rather than multiple correct results for that fixed query. The alternative metrics here are illustrative probes, not replacement gold answers.

Run the complete portable check with Python 3 and its standard library:

```sh
python verify_package.py
```

The check loads only the bundled compressed conditional graph witnesses into an in-memory SQLite database. It compares every aggregate with a separate Python set recount, checks the expected measurements, and rebuilds the disjoint 560-item overlay from the candidate lists. It requires no private database, API, model credit, or network connection. To regenerate the overlay elsewhere:

```sh
python build_partition.py --candidates metric_classification_candidates.json --candidates missing_input_classification_candidates.json --output-dir audit-output
```

The numeric examples are:

| Original question ID | Conditional measurement |
|---|---|
| RAN3_P2_CQ3-3 | Nokia has 161 distinct cited TDocs and 54 citing Resolutions; ZTE has 181 and 52. Their relative ranks reverse. |
| RAN4_P2_CQ3-3 | Qualcomm has 40 TDocs and 15 Resolutions; LG Electronics has 36 and 17. The original top-10 cutoff also changes membership under these two metrics. |
| RAN3_P2_CQ6-2 | ZTE at RAN3#93bis → #94: Resolution count rises 16 → 19, while its share among all Resolutions falls 16/126 → 19/214. |
| RAN4_P2_CQ6-2 | Samsung at RAN4#87 → #88: Resolution count rises 5 → 9. Share among all Resolutions falls 5/51 → 9/95, while share among TDoc-linked Resolutions rises 5/40 → 9/49. |
| RAN1_P3_CQ042 | On the same direct-section/direct-table operand population, opposite positive weights change forced top-10 membership even when cutoff ties are left unresolved. The data-derived dominating weight is 144. |

The trend questions explicitly concern **Resolutions**. Their diagnostic ambiguity is normalization and its denominator; changing their unit to TDocs is not used as evidence. Company names are matched literally, without inferred corporate aliases. Recorded references and submitter metadata do not establish ownership, causal influence, actual approval, or incorporation into a standard. The area counts do not measure implementation difficulty.

`sources/five_original_question_query_and_legacy_contract_records.json` preserves the exact five English questions, original queries, and countervailing legacy contracts. `sources/preserved_source_context_excerpts.json` includes the preserved contribution-rate wording and count-sorting context. The five missing-input cases preserve their original public row keys and the retained runner excerpts. In those retained invocations, the focal TDoc/WI, the `xxx` prefix, or the own-company perspective needed for “other companies” is unbound. The company-perspective case also retains separate agenda/topic, co-submission, and cutoff questions; no focal company is invented. This does not claim that a future input-bound lookup is impossible, or that no historical fixture could ever be recovered.

The witnesses are complete emitted rows of the stated **finite diagnostic projections**: 4,160 rank paths, 18,577 trend paths, 3,942 Section-to-Spec operands, and their typed section edges. They are conditional derived data, not an independently complete transcription of all original Word/Excel/standard sources. A public-only run reproduces the bundled arithmetic; it does not independently prove extraction completeness from the archived graph. `provenance.json` pins the public source commit, immutable index, graph source hashes, and retained measurement receipts. The anonymous access check fetched only the pinned small Git files, not the archived body TTLs.

For a separate full-graph check, `reproduce_full_sqlite.py --db-dir PATH` executes the standalone queries in `sources/` against already restored immutable `RAN1.sqlite`, `RAN3.sqlite`, and `RAN4.sqlite`. Those databases are not bundled. Their reconstruction needs the separately archived body-text graphs and the released loader. This package does not claim to have freshly re-imported those public archives.

The partition is an audit of the pinned release, not a general claim that these question forms are defective or permanently unanswerable. The 476 status means the existing released answer-contract checks passed; it does not certify complete physical-source truth. The 74 evidence-pending items are not automatically classified as ambiguous. All classifications are AI research diagnostics; expert validation remains zero.
