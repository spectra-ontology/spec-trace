# Reproducing the source-defined CR census with SPECTRA

SPECTRA connects the CR-count question to the original author-defined metadata census, full frozen memberships and a reproducible native/SQL result. The original query preserves the complete TDoc and CR counts; the requested answer is the integer CR count.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 1 | 0.0000 | 0/1 | 0 |
| text2sql | 1 | 1.0000 | 1/1 | 0 |
| single_retrieval | 1 | 0.0000 | 0/1 | 1 |
| iterative_retrieval | 1 | 0.0000 | 0/1 | 1 |


Five logical requests produced 5 complete responses in 5 actual attempts; returned usage sums to 0.24148999999999998 USD with 0 unknown-cost attempts. Saved prompts, raw first responses, generated queries and strict parser/scorer outputs reproduce the table above.

The source replay checks all 167,442 frozen TDoc-or-CR memberships, seven original authority and counterauthority spans, and five byte-exact source witnesses. The complete native record retains 167,017 TDocs and 74,350 CRs, with the requested CR count scored under a singleton set contract. Twenty-one child typed controls and seven outer generic checks preserve strict integer type and requested-field fidelity; their generic cases overlap. Two distinct fixed-seven-unit AI reviews are retained; human/expert review count is 0.

    python3 -B -I runtime/verify_authorized_incremental47_evaluation.py --evidence . --bundle ../original_core_overnight_repairs47

This separately registered N=1 evaluation uses anthropic/claude-opus-4.8 through Anthropic with the preserved scientific adapters, prompts, token caps and transport policy. Registration records the 517-to-518 extension; the all-560 register records release-wide question status. Source-role witnesses retain the distinction between initial Type formation and the final represented class census.
