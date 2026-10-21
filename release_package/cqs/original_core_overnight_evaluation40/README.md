# Source-verified CR-approval tracing

SPECTRA connects meeting Agreements to the CR proposals they approve. This contract reproduces the first fifteen requested Agreement identities at RAN1#115 under the original sequence/identity ordering. Original source review covers the complete unfiltered selection prefix of 44 Agreements and an additional 55-role comparison; seven original reports and their formatting preserve each selected approval role. The full native 156-row lexical population retains the selection-order evidence. Both native columns, independent SQL equality, two separate nonblind AI reviews and fourteen typed and source-role controls accompany the contract.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 1 | 0.0667 | 0/1 | 0 |
| text2sql | 1 | 0.2000 | 0/1 | 0 |
| single_retrieval | 1 | 0.0000 | 0/1 | 1 |
| iterative_retrieval | 1 | 0.0000 | 0/1 | 1 |


Five first requests produced five complete responses at actual cost 0.26759 USD. Saved prompts, raw responses, generated queries, execution statuses and complete-record scores reproduce every outcome.

The evaluation distinguishes returning plausible Agreement identities from recovering the source-certified CR-approval set: Cypher recovers one of fifteen requested identities and SQL three of fifteen, while both retrieval methods abstain. These outcomes identify concrete process-role and selection requirements for future systems. Each method retains the same frozen first-response protocol.

The model is anthropic/claude-opus-4.8 through Anthropic. Original prompts, token caps, parsers, transport policy and nine scientific runtime files are byte-preserved. Original top-k order groups are preserved in both original and optional-default readers. Structured methods receive the original question, typed contract and structural schema; retrieval methods receive saved passages. Review provenance records two nonblind AI reviews and human/expert count 0.

Replay the saved evaluation locally:

    python3 -B -I runtime/verify_authorized_incremental40_evaluation.py --evidence . --bundle ../original_core_overnight_repairs40

The registration records the 510-to-511 extension. The current all-560 index and disposition register provide release-wide accounting.
