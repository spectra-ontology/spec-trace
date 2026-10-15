# Separate source snapshot: retained four-method evaluation

This is one original question evaluated on an additive source snapshot. It is separate from the frozen original-question index and does not change that index or inherit historical scores.

| Method | N | Requested-record F1 | Exact | Retained status |
| --- | ---: | ---: | ---: | --- |
| text2cypher | 1 | 0.500000 | 0/1 | OK |
| text2sql | 1 | 0.000000 | 0/1 | OK |
| single_retrieval | 1 | 0.000000 | 0/1 | OK |
| iterative_retrieval | 1 | 0.000000 | 0/1 | OK |

The five first-call requests cost $0.298700; unknown-cost responses: 0. Original responses, generated queries, parse errors, abstentions and execution receipts are retained. No answer-quality regeneration occurred.

The strict scorer measures only the requested typed output records. It does not establish generated-query semantics, source-predicate validity, documentary provenance or causality. No human/expert validation is claimed. Base graph/text cutoff and complete coverage equality are unestablished; lexical retrieval remains bounded.

This is the unchanged UL Tx switching Agenda5.1 at RAN1#100 question. Its separate source snapshot adds six formalSourceContentWithTables values to existing Agreement/Resolution identities while preserving every old content value and all nodes/edges. Required output is the six complete formal source-content strings, with their Note, Case table, FFS and inline revisitable qualification. The neighboring standalone WorkingAssumption is optional source context, not an additional mandatory Agreement body.

Retrieval adds all6,017 paragraphs from the complete authentic original final-report archive member, in251 generic raw chunks. Paragraphs inside nested tables are included. No selected answer spans, gold, reference queries, reviews, source-positive labels or normalized Agreement strings enter raw augmentation. Literal w:t/m:t projection is not Word visual rendering, a final-edit-state interpretation or a whole-corpus completeness claim.

The strict literal-value scorer does not assess semantic paraphrase equivalence or truthfulness of optional commentary. The two source judgments are AI development reviews with prior-evidence exposure, human false and expert0. Named meeting/agenda scope describes the recorded formal decisions, not later normative enactment or TSG ratification.

Requested-record credit alone does not prove that a generated query used the six added formal content values. In this retained run the graph query returned the old a.content field; the SQL query imposed an AgendaItem.meetingNumber predicate and returned no rows. Generated queries, parsed records and errors remain available for this separate diagnosis. No source-correction-caused model improvement is inferred.

Run offline prompt, parse and score replay with:

```bash
python -B tools/verify_retained_four_methods.py --evidence .
```

This command checks packaged hashes, reconstructs all five prompts, reproduces retained retrieval parsing (including failures), and recomputes all four strict scores. It does not call a provider, execute graph/SQL queries, or rerun full-text retrieval. The source_patch subdirectory contains separate authentic-source materialization and native/SQL/scorer validation evidence. Rebuilding that graph requires its documented baseline files; it is a separate operation.

Historical absolute source paths in receipts are preserved as provenance. Packaged pin locations are declared in evaluation_manifest.json; offline replay resolves only package-relative copies.
