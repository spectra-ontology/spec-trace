# Separate source snapshot: retained four-method evaluation

This is one original question evaluated on an additive source snapshot. It is separate from the frozen original-question index and does not change that index or inherit historical scores.

| Method | N | Requested-record F1 | Exact | Retained status |
| --- | ---: | ---: | ---: | --- |
| text2cypher | 1 | 0.000000 | 0/1 | ABSTAIN |
| text2sql | 1 | 0.000000 | 0/1 | ABSTAIN |
| single_retrieval | 1 | 0.000000 | 0/1 | ABSTAINED |
| iterative_retrieval | 1 | 0.000000 | 0/1 | ABSTAINED |

The five first-call requests cost $0.111190; unknown-cost responses: 0. Original responses, generated queries, parse errors, abstentions and execution receipts are retained. No answer-quality regeneration occurred.

The strict scorer measures only the requested typed output records. It does not establish generated-query semantics, source-predicate validity, documentary provenance or causality. No human/expert validation is claimed. Base graph/text cutoff and complete coverage equality are unestablished; lexical retrieval remains bounded.

This is the unchanged Qualcomm recent-ten Agreement question. Its separate source-calendar contract retains the complete 1,094-Agreement native pool and all date boundary groups: four Agreements are strictly newer than the boundary, and any six of the twenty-eight cutoff-meeting Agreements complete the requested ten. Required output is Agreement identity; content and date are auxiliary. The earlier source60 patch and CQ017 task are preserved as a distinct dependency under source_patch/calendar_source_patch/.

Attribution follows retained Agreement references to submitted TDocs; it does not establish leadership, ownership, approval or causal contribution. Date fields describe own reported Meeting periods, not upload times, approval or intra-meeting chronology. Retrieval reuses exactly eight authored paragraphs from each of 192 retained report members; complete report body equivalence is unestablished. No ISO-date, canonical-period, gold or reference-query annotation was added to retrieval.

Requested-record credit alone does not prove that a generated query used the added Meeting period fields or implemented the source-calendar ranking. The generated queries and execution receipts are preserved for that separate inspection; no improvement caused by the added source dates is inferred.

Run offline prompt, parse and score replay with:

```bash
python -B tools/verify_retained_four_methods.py --evidence .
```

This command checks packaged hashes, reconstructs all five prompts, reproduces retained retrieval parsing (including failures), and recomputes all four strict scores. It does not call a provider, execute graph/SQL queries, or rerun full-text retrieval. The source_patch subdirectory contains separate authentic-source materialization and native/SQL/scorer validation evidence. Rebuilding that graph requires its documented baseline files; it is a separate operation.

Historical absolute source paths in receipts are preserved as provenance. Packaged pin locations are declared in evaluation_manifest.json; offline replay resolves only package-relative copies.
