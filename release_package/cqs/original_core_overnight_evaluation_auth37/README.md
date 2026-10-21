# Work-item company rankings: first four-method evaluation

SPECTRA connects recorded Resolution references with TDoc submitting companies and Work Items. This contract makes the resulting company rankings executable and reproducible: each answer record contains one Work Item and its complete top-company set. Source replay, two separate AI reviews, independent SQL/native equality and 56 production answer controls support the five requested records. The scorer checks the full 1,939-group eligibility population and accepts all five lawful boundary-tie selections.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 1 | 0.0000 | 0/1 | 1 |
| text2sql | 1 | 0.0000 | 0/1 | 1 |
| single_retrieval | 1 | 0.0000 | 0/1 | 1 |
| iterative_retrieval | 1 | 0.0000 | 0/1 | 1 |


The first responses yielded no complete requested Work Item records under this protocol. The released contract and saved outputs make the nested aggregation and boundary choices inspectable at the complete-record level. All four method outcomes remain in this N=1 cohort.

Five first logical requests produced 5 complete responses; actual returned usage totals $0.298. The model is anthropic/claude-opus-4.8 through Anthropic. Original prompts, token caps, parsers, transport-only retry policy and nine scientific runtime files are preserved. The partitioned complete-Work-Item scorer is explicitly declared in the frozen protocol, and the separate analysis entry imports that scorer. The same first responses are used throughout.

Structured methods receive the original question, typed public contract and schema; retrieval methods receive saved passages. Source proof and gold support contract validation. The included provenance records two nonblind AI reviews and zero human/expert reviews.

Replay the saved inputs, prompts, parsers, costs, scores and failure gates without API or database calls:

    python3 -B -I runtime/verify_authorized_incremental37_evaluation.py --evidence . --bundle ../original_core_overnight_repairs_auth37

The original 507-to-508 registration and every first response are retained. Operational receipts also preserve the pre-call filename correction and missing auxiliary-receipt recovery. These fixes reused the generated responses; quality regeneration is zero.
