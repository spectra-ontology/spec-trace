# PUSCH repetition decisions: separate first evaluation

This N1 cohort evaluates the original PUSCH-repetition decision question through the ontology-linked Agreement and Meeting records. The fixed reference preserves 532 joined rows and all 16 records eligible at the original latest-meeting boundary. Source replay checks their own decision contents and 83 operative source bindings. Two separate AI reviews and 15 typed scorer controls precede this first evaluation.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 1 | 0.0000 | 0/1 | 0 |
| text2sql | 1 | 0.0000 | 0/1 | 0 |
| single_retrieval | 1 | 0.0000 | 0/1 | 1 |
| iterative_retrieval | 1 | 0.0000 | 0/1 | 0 |


Five first logical requests produced five complete successful HTTP responses in five attempts. Returned usage records total actual cost $0.29088; all actual attempt costs are known. The $1.0 operational budget and reservations are separate from actual spend.

All five call stages and four method outcomes, including errors and abstentions, are preserved. The same model, prompts, token settings, parsers, scorer and failure gates use `anthropic/claude-opus-4.8` through Anthropic, with no quality rerolls or prior-score transfers. Structured methods receive the original question, public typed contract and structural schema; retrieval methods receive their saved retrieved passages. Source proofs, gold and reviews are validation inputs. Raw requests, responses, execution statuses and actual usage are included. Human/expert validation remains zero.

Offline replay uses no API or database calls:

    python3 -B -I runtime/verify_authorized_incremental33_evaluation.py --evidence . --bundle ../original_core_overnight_repairs33

The registered counts identify the fixed 502-to-503 scope and 57 legacy nonadmitted questions; the live all-560 taxonomy is in the disposition register. Private account/key balances are omitted with hash commitments; every scientific attempt remains included.
