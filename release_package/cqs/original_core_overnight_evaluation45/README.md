# Reproducing Resolution-to-CR traces with SPECTRA

SPECTRA connects Resolution references, CR target specifications and recorded document outcomes in an executable decision-to-change contract for TS 38.133. Complete native and independent SQL records establish 635 eligible pairs. The authored Resolution ordering selects ten pairs, with any distinct ten of the eighteen pairs at the cutoff accepted by the unchanged scorer.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 1 | 0.0000 | 0/1 | 0 |
| text2sql | 1 | 0.0000 | 0/1 | 0 |
| single_retrieval | 1 | 0.0000 | 0/1 | 1 |
| iterative_retrieval | 1 | 0.0000 | 0/1 | 1 |


Five logical requests produced 5 complete responses in 5 actual attempts; returned usage sums to 0.37087 USD with 0 unknown-cost attempts. text2cypher: F1 0.0, exact 0/1, statuses {"OK": 1}; text2sql: F1 0.0, exact 0/1, statuses {"OK": 1}; single_retrieval: F1 0.0, exact 0/1, statuses {"ANSWER_PARSE_ERROR": 1}; iterative_retrieval: F1 0.0, exact 0/1, statuses {"ANSWER_PARSE_ERROR": 1}. Saved prompts, raw responses, generated queries and strict parser/scorer outputs reproduce these first-trial measurements.

Original report paragraphs and two final-register fragments expose every one of the 28 cutoff candidates, including fourteen current affirmative outcomes, four earlier endorsed outcomes and ten excluded pairs. The source replay checks the requested identities, CR role, target Spec and recorded status. Two distinct fixed-seven-unit AI reviews, full native635, selected native10, a different valid SQL10, ten generic field controls, three boundary controls and twenty-nine source-role/tie controls reproduce the contract. Human/expert review count is 0.

    python3 -B -I runtime/verify_authorized_incremental45_evaluation.py --evidence . --bundle ../original_core_overnight_repairs45

This separately registered N=1 evaluation uses anthropic/claude-opus-4.8 through Anthropic with the preserved scientific adapters, prompts, token caps and transport policy. Registration records the 515-to-516 extension; the all-560 register records release-wide question status.
