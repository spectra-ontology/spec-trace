# HARQ and BWP: separate first evaluation

This N2 cohort extends executable agreement evaluation with the original HARQ identity-list and BWP substantive-decision questions. Each reference preserves ten complete native records and all three returned columns, with source-grounded query repairs and typed scoring contracts fixed before calls.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 2 | 0.0000 | 0/2 | 0 |
| text2sql | 2 | 0.0000 | 0/2 | 0 |
| single_retrieval | 2 | 0.0000 | 0/2 | 2 |
| iterative_retrieval | 2 | 0.0000 | 0/2 | 1 |


All ten first call stages and eight method outcomes remain in this cohort, including all execution statuses and abstentions. The same model, four methods, prompts, token settings, parsers and failure gates are used with `anthropic/claude-opus-4.8` through Anthropic; no quality rerolls or earlier-score transfers are performed. HARQ accepts the original latest10 tie policy with nine mandatory identities and any one of six boundary identities; its 15 eligible source records are separately marked from the 10 actual native rows. BWP requires ten complete recorded decision contents and explicitly attributes the existing same-meeting CR text recovered by the reference query.

Structured methods receive the original question, public typed contract and structural schema; retrieval methods receive their saved retrieved passages under the same public contract. Source proofs, answer gold and reviews are outside model input. This separate N2 comparison reports observed method behavior on these two fixed contracts. Raw responses, prompts, execution statuses, actual usage and per-call costs remain replayable. Human/expert validation remains zero.

Offline replay makes no API or database calls:

    python3 -B -I runtime/verify_authorized_incremental31_evaluation.py --evidence . --bundle ../original_core_overnight_repairs31

The registered counts identify the fixed 499-to-501 evaluation scope and 59 legacy nonadmitted questions; the live all-560 taxonomy is recorded separately in the current disposition register. Private account/key balances are omitted with hash commitments; every scientific call attempt and response remains included.
