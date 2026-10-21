# Reproducing source-grounded Agreement activity counts with SPECTRA

SPECTRA connects technical Agreements, directly referenced change requests and specification targets to an executable process-activity count. The source-grounded contract identifies current adoption of the same CR or a concrete component of its current amendment, then counts distinct Agreements.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 1 | 0.0000 | 0/1 | 0 |
| text2sql | 1 | 0.0000 | 0/1 | 0 |
| single_retrieval | 1 | 0.0000 | 0/1 | 1 |
| iterative_retrieval | 1 | 0.0000 | 0/1 | 1 |


Five logical requests produced 5 complete responses in 5 actual attempts; returned usage sums to 0.37181 USD with 0 unknown-cost attempts. Saved prompts, raw first responses, generated queries and strict parser/scorer outputs reproduce the table above.

The complete original 407-Agreement referenced-CR population is traced through 35 meeting reports and 21 current CR/proposal originals. Source review establishes 368 qualifying Agreements. The retained-field query, independent SQLite replay, complete native membership and native integer answer agree on the same count. Two separate fixed-seven-unit AI reviews, seven generic typed controls and ten scalar controls connect original meaning, source identity, aggregation and complete-record scoring. The 368-member output remains a verification diagnostic; the requested answer is one nonnull integer agrCount record.

    python3 -B -I runtime/verify_authorized_incremental50_evaluation.py --evidence . --bundle ../original_core_overnight_repairs50

This separately registered N=1 evaluation uses anthropic/claude-opus-4.8 through Anthropic with the preserved four methods, scientific adapters, prompts, token caps and transport policy. Registration records the 520-to-521 extension; the all-560 register records release-wide question status. Review provenance records two nonblind AI judgments and human/expert review count 0.
