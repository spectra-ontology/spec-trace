# Tracing approved CR change reasons and summaries with SPECTRA

SPECTRA links Agreement approval evidence to the complete change reasons and summaries recorded in CR cover metadata. This case reproduces five complete three-field records under the original captured-metadata gate, DISTINCT CR, tdoc ordering and LIMIT 5. Eight original archives, ten cover fields and five active approval outcomes accompany the native output and the complete 162-record selection population. Two separate seven-unit AI reviews and twenty-seven typed answer-role controls verify the contract.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 1 | 0.0000 | 0/1 | 0 |
| text2sql | 1 | 0.0000 | 0/1 | 0 |
| single_retrieval | 1 | 0.0000 | 0/1 | 1 |
| iterative_retrieval | 1 | 0.0000 | 0/1 | 0 |


Five first requests produced five complete responses at actual cost 0.36345000000000005 USD. Saved prompts, raw responses, generated queries, execution statuses and complete-record scores reproduce every outcome. The four methods are evaluated on recovery of the same complete CR reason-and-summary records and original selection boundary.

The model is anthropic/claude-opus-4.8 through Anthropic. Original prompts, token caps, parsers, transport policy and nine scientific runtime files are byte-preserved. Original top-k groups are preserved in both the original and explicit optional-default reader. Structured methods receive the original question, typed contract and structural schema; retrieval methods receive saved passages. Review provenance records two nonblind AI reviews and human/expert count 0.

Replay the saved evaluation locally:

    python3 -B -I runtime/verify_authorized_incremental41_evaluation.py --evidence . --bundle ../original_core_overnight_repairs41

The registration records the 511-to-512 extension. The current all-560 index and disposition register provide release-wide accounting.
