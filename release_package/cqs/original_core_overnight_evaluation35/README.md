# Recent TS 38.213 and Qualcomm agreement tracing: first evaluation

This N2 cohort evaluates two original questions through ontology-linked Agreement, TDoc, Company, CR, Specification and Meeting records. One contract traces ten recent recorded agreements affecting TS 38.213; the other identifies Qualcomm-associated recent agreements with the original source attribution preserved. Source replay binds all four native context columns to independent SQL and original records. Two separate AI reviews per question and sixteen typed scorer controls precede this first evaluation.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 2 | 0.0000 | 0/2 | 2 |
| text2sql | 2 | 0.0000 | 0/2 | 2 |
| single_retrieval | 2 | 0.0000 | 0/2 | 1 |
| iterative_retrieval | 2 | 0.0000 | 0/2 | 1 |


Ten first logical requests produced ten complete successful HTTP responses in ten attempts. Returned usage records total actual cost $0.48645499999999997; all actual attempt costs are known. The $1.0 operational budget and reservations are separate from actual spend.

All ten call stages and eight method outcomes, including errors and abstentions, are preserved. The same model, prompts, token settings, parsers, scorer and failure gates use `anthropic/claude-opus-4.8` through Anthropic, with no quality rerolls or prior-score transfers. Structured methods receive the original question, public typed contract and structural schema; retrieval methods receive their saved retrieved passages. Source proofs, gold and reviews are validation inputs. Raw requests, responses, execution statuses and actual usage are included. Human/expert validation remains zero.

Offline replay uses no API or database calls:

    python3 -B -I runtime/verify_authorized_incremental35_evaluation.py --evidence . --bundle ../original_core_overnight_repairs35

The registered counts identify the fixed 504-to-506 scope and 54 legacy nonadmitted questions; the live all-560 taxonomy is in the disposition register. Private account/key balances are omitted with hash commitments; every scientific attempt remains included.
