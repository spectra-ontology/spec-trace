# Separate source snapshot: retained four-method evaluation

This is one original question evaluated on an additive source snapshot. It is separate from the frozen 447-question index and does not change that index or inherit historical scores.

| Method | N | Requested-record F1 | Exact | Retained status |
| --- | ---: | ---: | ---: | --- |
| text2cypher | 1 | 0.000000 | 0/1 | OK |
| text2sql | 1 | 1.000000 | 1/1 | OK |
| single_retrieval | 1 | 0.000000 | 0/1 | ANSWER_PARSE_ERROR |
| iterative_retrieval | 1 | 0.000000 | 0/1 | ANSWER_PARSE_ERROR |

The five first-call requests cost $0.321420; unknown-cost responses: 0. Original responses, generated queries, parse errors, abstentions and execution receipts are retained. No answer-quality regeneration occurred.

The strict scorer measures only the requested typed output records. It does not establish generated-query semantics, source-predicate validity, documentary provenance or causality. No human/expert validation is claimed. Base graph/text cutoff and complete coverage equality are unestablished; lexical retrieval remains bounded.

The generated Text2SQL query returned the three requested TS-family identities using the retained REFERENCES and MODIFIES path. It did not use the added approved normative-incorporation observations. Its output-record score therefore must not be presented as verification that the query implemented approval/incorporation or that references alone prove decisions entered the standard.

Run offline prompt, parse and score replay with:

```bash
python -B tools/verify_retained_four_methods.py --evidence .
```

This command checks packaged hashes, reconstructs all five prompts, reproduces retained retrieval parsing (including failures), and recomputes all four strict scores. It does not call a provider, execute graph/SQL queries, or rerun full-text retrieval. The source_patch subdirectory contains separate authentic-source materialization and native/SQL/scorer validation evidence. Rebuilding that graph requires its documented baseline files; it is a separate operation.

Historical absolute source paths in receipts are preserved as provenance. Packaged pin locations are declared in evaluation_manifest.json; offline replay resolves only package-relative copies.
