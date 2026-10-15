# Separate source snapshot: retained four-method evaluation

This is one original question evaluated on an additive source snapshot. It is separate from the frozen original-question index and does not change that index or inherit historical scores.

| Method | N | Requested-record F1 | Exact | Retained status |
| --- | ---: | ---: | ---: | --- |
| text2cypher | 1 | 1.000000 | 1/1 | OK |
| text2sql | 1 | 0.700000 | 0/1 | OK |
| single_retrieval | 1 | 0.000000 | 0/1 | ABSTAINED |
| iterative_retrieval | 1 | 0.000000 | 0/1 | ABSTAINED |

The five first-call requests cost $0.121630; unknown-cost responses: 0. Original responses, generated queries, parse errors, abstentions and execution receipts are retained. No answer-quality regeneration occurred.

The strict scorer measures only the requested typed output records. It does not establish generated-query semantics, source-predicate validity, documentary provenance or causality. No human/expert validation is claimed. Base graph/text cutoff and complete coverage equality are unestablished; lexical retrieval remains bounded.

The unchanged FFS-marker Agreement question retains the complete 4,635-record native pool, all five returned fields and the full source-date/Agenda/sequence groups. The requested answer role is Agreement identity; content and ranking keys are auxiliary. Original list10 and AgendaASC/sequenceASC defaults apply after authentic event-date recency. Equal complete-key boundary records are interchangeable. The147 older missing-sequence records remain in the pool and cannot affect the requested top10; no general NULL placement rule was inferred.

FFS denotes recorded marker presence, not present-world issue finality. Own reported Meeting dates do not assert upload, approval or intra-meeting chronology. Retrieval reuses exactly eight authored paragraphs from each of192 retained report members; complete report-body equivalence is unestablished. No parsed ISO date, canonical-period, gold, reference-query or review annotation was added to retrieval.

Requested-record credit alone does not prove that a generated query used added Meeting dates, applied the FFS marker or original Agenda/sequence ranking. Actual generated queries and execution receipts are retained for separate inspection. Optional content/commentary truth is unscored. No correction-caused improvement or causal source validity is inferred.

Before these first calls, a separately versioned runtime made the already declared source_order_keys visible in all five method prompts. Only source column names and directions were added; no answer values were exposed. The isolated runtime and pre-call difference receipt are retained. This prompt correction differs from earlier source60 contracts and does not establish a controlled source-medium effect.

Run offline prompt, parse and score replay with:

```bash
python -B tools/verify_retained_four_methods.py --evidence .
```

This command checks packaged hashes, reconstructs all five prompts, reproduces retained retrieval parsing (including failures), and recomputes all four strict scores. It does not call a provider, execute graph/SQL queries, or rerun full-text retrieval. The source_patch subdirectory contains separate authentic-source materialization and native/SQL/scorer validation evidence. Rebuilding that graph requires its documented baseline files; it is a separate operation.

Historical absolute source paths in receipts are preserved as provenance. Packaged pin locations are declared in evaluation_manifest.json; offline replay resolves only package-relative copies.
