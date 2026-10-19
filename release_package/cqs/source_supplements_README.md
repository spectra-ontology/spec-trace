# Additional original-question evidence

`original_core_observed_trend_repair` contains two additional unchanged original questions on the original frozen working-group graphs. Its verifier reports the union with the historical 371-item parent; the current global union is recorded separately in `current_core`.

`original_core_source_enriched_repair` contains one unchanged RAN2 question on a separately source-enriched graph. Nine original 3GPP cover ZIPs and register-derived records support nine added CRPack nodes. The original graph and current frozen-graph cohort are preserved. This supplement is not merged into their same-snapshot model results. Its reconstruction recipe takes the existing public base graph and a small additive patch.

The included 3GPP-derived cover documents retain their original attribution and terms; authorship and CC BY claims apply to SPECTRA-authored code and annotations, not ownership of those source documents. Source URLs, SHA256 hashes, and extraction positions are recorded in the repair bundle.

Completed semantic checks are separate nonblind AI reviews and source/execution/scorer checks. No completed independent human or domain-expert review is claimed. Model results, where present, have separate frozen experiment packages.

- [Frozen-graph trend repair](original_core_observed_trend_repair/README.md) and [its actual four-method evaluation](original_core_observed_trend_evaluation/README.md).
- [Source-enriched RAN2 repair](original_core_source_enriched_repair/README.md) and [its actual four-method evaluation](original_core_source_enriched_evaluation/README.md).
- [Source-enriched RAN3 incoming-impact repair](original_core_source_RAN3_incoming38473/README.md) and [its first-attempt evaluation with separate infrastructure diagnosis](original_core_source_RAN3_incoming38473_evaluation/README.md). This separate experiment adds zero questions to the original frozen-graph count; the primary failures and SQL input limitation remain visible.

The two trend tasks use stored numeric meeting ordinals, with any order allowed within equal ordinals; this does not certify calendar chronology. Their registered strict ordered-output scorer rejects incomplete meeting series. The new model outputs therefore receive zero under that rule even when some returned counts are correct. Execution errors, abstentions and parsing failures are retained. These measurements establish neither improved model performance nor a general advantage of graph storage.
