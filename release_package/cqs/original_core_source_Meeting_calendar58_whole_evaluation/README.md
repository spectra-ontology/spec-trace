# Separate source snapshot: retained four-method evaluation

This is one original question evaluated on an additive source snapshot. It is separate from the original 560-question frozen-index accounting and does not change that index or inherit historical scores.

| Method | N | Requested-record F1 | Exact | Retained status |
| --- | ---: | ---: | ---: | --- |
| text2cypher | 1 | 0.000000 | 0/1 | OK |
| text2sql | 1 | 1.000000 | 1/1 | OK |
| single_retrieval | 1 | 0.000000 | 0/1 | ABSTAINED |
| iterative_retrieval | 1 | 0.000000 | 0/1 | OK |

The five first-call requests cost $0.273835; unknown-cost responses: 0. Original responses, generated queries, parse errors, abstentions and execution receipts are retained. No answer-quality regeneration occurred.

The strict scorer measures only the requested typed output records. It does not establish generated-query semantics, source-predicate validity, documentary provenance or causality. No human/expert validation is claimed. Base graph/text cutoff and complete coverage equality are unestablished; lexical retrieval remains bounded.

The unchanged question requests ten recent CR document identities for TS 38.133. The source-calendar reference retains the full 16,017-record native population and complete date groups; any ten identities from the latest 563-record date group satisfy the cutoff. Source-reported meeting end dates define meeting-presentation recency, not upload, approval or normative enactment time. All 342 retained Word report bodies and four complete PPTX XML-text packages enter the frozen lexical corpus: 6,755,948 Word-body paragraphs plus 1,686 PPTX XML paragraphs are represented by 61,730 consecutive raw chunks. All original member packages and the exact 376,969,857-byte raw model input are retained in ordered binary shards below the repository file limit. Raw projection preserves w:t/m:t/a:t and tabs/breaks, including empty paragraphs; OCR, embedded binary-object semantics, deleted-text decoding, font-symbol decoding and final-visible document interpretation are not established. The 23 legacy DOC access derivatives are explicitly pinned and were not freshly reconverted.

Both retained structured queries order CR.uploadedDate and do not use the added source-reported Meeting calendar dates. Text2SQL attains requested-record F1=1 for this saved output, while Text2Cypher attains 0; this does not validate calendar-recency semantics for either generated query. The explicit source-predicate limitation receipt is retained under completed_verification. A separate read-only diagnostic joins all twenty actually returned document identities to the immutable source SQL properties: all ten Cypher output values have NULL uploadedDate, while all ten SQL output values are non-NULL and equal the full non-NULL population's descending top ten. The complete relevant population has 1,734 NULL and 14,283 non-NULL uploadedDate values. This directly corroborates the different NULL placement in these retained outputs; ordering within the Cypher NULL tie group is unspecified. See [actual 20-output diagnostic](completed_verification/actual20_uploadedDate_NULL_order_diagnostic.json) and its packaged reader. No generated query, response, score or reference was repaired or rerolled.

Run offline prompt, parse and score replay with:

```bash
python -B tools/verify_retained_four_methods.py --evidence .
```

This command checks packaged hashes, reconstructs all five prompts, reproduces retained retrieval parsing (including failures), and recomputes all four strict scores. It does not call a provider, execute graph/SQL queries, or rerun full-text retrieval. The source_patch subdirectory contains separate authentic-source materialization and native/SQL/scorer validation evidence. Rebuilding that graph requires its documented baseline files; it is a separate operation.

Historical absolute source paths in receipts are preserved as provenance. Packaged pin locations are declared in evaluation_manifest.json; offline replay resolves only package-relative copies.
