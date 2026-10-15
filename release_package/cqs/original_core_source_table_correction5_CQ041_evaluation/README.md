# Separate source snapshot: retained four-method evaluation

This is one original question evaluated on an additive source snapshot. It is separate from the frozen 447-question index and does not change that index or inherit historical scores.

| Method | N | Requested-record F1 | Exact | Retained status |
| --- | ---: | ---: | ---: | --- |
| text2cypher | 1 | 1.000000 | 1/1 | OK |
| text2sql | 1 | 1.000000 | 1/1 | OK |
| single_retrieval | 1 | 0.000000 | 0/1 | ABSTAINED |
| iterative_retrieval | 1 | 0.000000 | 0/1 | ABSTAINED |

The five first-call requests cost $0.234395; unknown-cost responses: 0. Original responses, generated queries, parse errors, abstentions and execution receipts are retained. No answer-quality regeneration occurred.

The strict scorer measures only the requested typed output records. It does not establish generated-query semantics, source-predicate validity, documentary provenance or causality. No human/expert validation is claimed. Base graph/text cutoff and complete coverage equality are unestablished; lexical retrieval remains bounded.

The five added actual source tables are supported by two complete authored source members. CQ008 retains four required fields (TS identity and three integer counts); CQ041 requires the complete uncapped set of Section identities passing the inclusive five-table direct-containment threshold. This is a graph-relative recorded-snapshot contract, not a claim that every physical table in every authored source has been extracted. Four mathematical captions retain OMML/XML provenance; their W:t-only tableCaption strings remain explicitly partial.

Run offline prompt, parse and score replay with:

```bash
python -B tools/verify_retained_four_methods.py --evidence .
```

This command checks packaged hashes, reconstructs all five prompts, reproduces retained retrieval parsing (including failures), and recomputes all four strict scores. It does not call a provider, execute graph/SQL queries, or rerun full-text retrieval. The source_patch subdirectory contains separate authentic-source materialization and native/SQL/scorer validation evidence. Rebuilding that graph requires its documented baseline files; it is a separate operation.

Historical absolute source paths in receipts are preserved as provenance. Packaged pin locations are declared in evaluation_manifest.json; offline replay resolves only package-relative copies.
