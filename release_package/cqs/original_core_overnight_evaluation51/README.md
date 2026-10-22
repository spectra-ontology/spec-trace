# Tracing URLLC study implementation with SPECTRA

SPECTRA connects the URLLC study TR38.824 through the standardization work program to detailed implementation records for TS38.211 and TS38.214. Its executable contract reconstructs the five original requested fields: study, specification, impact type, affected sections and impact description.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 1 | 0.0000 | 0/1 | 0 |
| text2sql | 1 | 0.0000 | 0/1 | 0 |
| single_retrieval | 1 | 0.0000 | 0/1 | 1 |
| iterative_retrieval | 1 | 0.0000 | 0/1 | 1 |


Five logical requests produced 5 complete responses in 5 actual attempts; returned usage sums to 0.272555 USD with 0 unknown-cost attempts. Saved prompts, raw first responses, generated queries and strict parser/scorer outputs reproduce the table above.

The complete 72-CR retained candidate census is checked alongside 41 original documents. Thirty-five CRs supply 74 source text components for the two requested specification records; independent retained-field SQL, graph interpretation and native execution agree on every requested field and all 70 CR-field records. Two separate fixed-seven-unit AI reviews and 29 distinct typed scorer controls connect study attribution, exact section membership, record order and complete-record scoring. The implementation program draws jointly on TR38.824 and TR38.825.

    python3 -B -I runtime/verify_authorized_incremental51_evaluation.py --evidence . --bundle ../original_core_overnight_repairs51

This separately registered N=1 evaluation uses anthropic/claude-opus-4.8 through Anthropic with the preserved four methods, scientific adapters, prompts, token caps and transport policy. Registration records the 521-to-522 extension; the all-560 register records release-wide question status. Review provenance records two nonblind AI judgments and human/expert review count 0.
