# Additional original-question evidence

`original_core_observed_trend_repair` contains two additional unchanged original questions on the original frozen working-group graphs. Its verifier reports the union with the historical 371-item parent; the current global union is recorded separately in `current_core`.

`original_core_source_enriched_repair` contains one unchanged RAN2 question on a separately source-enriched graph. Nine original 3GPP cover ZIPs and register-derived records support nine added CRPack nodes. The original graph and current frozen-graph cohort are preserved. This supplement is not merged into their same-snapshot model results. Its reconstruction recipe takes the existing public base graph and a small additive patch.

The included 3GPP-derived cover documents retain their original attribution and terms; authorship and CC BY claims apply to SPECTRA-authored code and annotations, not ownership of those source documents. Source URLs, SHA256 hashes, and extraction positions are recorded in the repair bundle.

Completed semantic checks are separate nonblind AI reviews and source/execution/scorer checks. No completed independent human or domain-expert review is claimed. Model results, where present, have separate frozen experiment packages.

- [Frozen-graph trend repair](original_core_observed_trend_repair/README.md) and [its actual four-method evaluation](original_core_observed_trend_evaluation/README.md).
- [Source-enriched RAN2 repair](original_core_source_enriched_repair/README.md) and [its actual four-method evaluation](original_core_source_enriched_evaluation/README.md).
- [Source-enriched RAN3 incoming-impact repair](original_core_source_RAN3_incoming38473/README.md) and [its first-attempt evaluation with separate infrastructure diagnosis](original_core_source_RAN3_incoming38473_evaluation/README.md). This separate experiment adds zero questions to the original frozen-graph count; the primary failures and SQL input limitation remain visible.

- [Common ten-report RAN1 source evidence](original_core_source_RAN1_common3176/README.md) and [its three-question first-attempt evaluation](original_core_source_RAN1_common3176_evaluation/README.md). This separate cohort adds zero original admissions. All primary failures, the distinct unchanged-query environment diagnostic, known source-window counterexamples and nonblind AI review limits are preserved.

- [RAN4 meeting93 original-DESC source evidence](original_core_source_RAN4_source93_exact_DESC/README.md) and [its one-question first-attempt evaluation](original_core_source_RAN4_source93_exact_DESC_evaluation/README.md). Each answer record requires TDoc identity and its own nonnull summary. This separate N=1 cohort adds zero original admissions; the two successful structured-query results, partial retrieval answer and strict parsing failure are all preserved. Documentary acceptance, source rendering and nonblind AI review limits remain explicit.

- [TS38.213 recent-Agreement source evidence](original_core_source_RAN1_CQ024_capture2/README.md) and [its saved first-attempt evaluation](original_core_source_RAN1_CQ024_capture2_evaluation/README.md). Two generic source-recovered reference edges and a calendar-aware tie distinction define a separate N=1 cohort, with zero original admissions. All five first calls and four zero-F1 outcomes are retained; wrong query paths, an empty SQL result and both strict retrieval parsing failures remain visible. Recorded CR targets do not establish approval or normative incorporation.

- [Bounded DCI boundary and equation diagnostics](source_DCI_boundary_equation_diagnostics/README.md). Offline replay reconstructs 93 original OLE equation objects and a specific false boundary cut. A prospective renderer change affects 1 object and leaves 92 unchanged; five AST controls preserve real empty fences. Preview agreement does not certify formula semantics, and the DCI question remains evidence-pending. No model calls, original-Core admissions or installed graph/parser changes are claimed.

The two trend tasks use stored numeric meeting ordinals, with any order allowed within equal ordinals; this does not certify calendar chronology. Their registered strict ordered-output scorer rejects incomplete meeting series. The new model outputs therefore receive zero under that rule even when some returned counts are correct. Execution errors, abstentions and parsing failures are retained. These measurements establish neither improved model performance nor a general advantage of graph storage.

- [RAN2 finite density source evidence](original_core_source_RAN2_finite_density/README.md) and [its saved first-five evaluation](original_core_source_RAN2_finite_density_evaluation/README.md). A separate current64 metadata and finite Section-dependency repair preserves the original four-field query and every old graph fact. Its N=1 outcomes all retain F1 zero: five wrong Cypher records, empty SQL, strict single-retrieval parse failure and a valid two-round abstention. Five first calls cost $0.497470; zero original-Core admissions, quality retries and human experts. Saved-projection replay is distinct from fresh raw-source extraction and full native/SQL/FTS rebuilding.

From this cqs directory, replay the two RAN2 packages with:

```sh
python3 -B -I original_core_source_RAN2_finite_density/verify_bundle.py
python3 -B -I original_core_source_RAN2_finite_density_evaluation/verify_package.py --output /tmp/ran2-density-replay-new --source-evidence original_core_source_RAN2_finite_density
```

Choose a new output path and sibling receipt. The three large derived TTL/SQL/FTS artifacts are omitted with pins and explicit reconstruction procedures.

- [Four RAN2 own-Agreement FFS source witnesses](source_RAN2_FFS_four_witness_diagnostics/README.md). The original report ZIP contains four active FFS passages under their own Agreements headings whose full normalized paragraphs are absent from all 3,413 preserved Agreement content/note records. The portable replay checks original XML, formatting, source neighborhoods and this bounded literal-absence claim. It does not establish semantic paraphrase absence, a complete source population, present unresolved status or top-ten membership. The original question remains evidence-pending; no graph repair, model calls, original-Core admissions or human expert validations are added.

Replay this diagnostic offline with `python3 -B -I source_RAN2_FFS_four_witness_diagnostics/verify_diagnostic.py`.
