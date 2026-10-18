# RAN2#132: separate source-summary evaluation

One unchanged original question asks for all 240 authored summary occurrences at the named WG meeting. This additive source snapshot remains separate from the frozen original560 index; it changes that index by zero questions.

| Method | N | Requested-record F1 | Exact | Status |
| --- | ---: | ---: | ---: | --- |
| text2cypher | 1 | 0.000000 | 0/1 | OK |
| text2sql | 1 | 0.000000 | 0/1 | OK |
| single_retrieval | 1 | 0.000000 | 0/1 | ABSTAINED |
| iterative_retrieval | 1 | 0.000000 | 0/1 | ABSTAINED |

The 5 first requests have 5 retained HTTP responses and cost $0.289140; unknown-cost responses: 0. Raw responses, generated queries, execution failures, parse errors and abstentions are retained. No answer-quality retry or model fallback occurred.

Unchanged bounded lexical retrieval over the retained base corpus plus 84251 generic raw records from every physical Docs/Report file at RAN2#132. Full inventory and available text projections are distinct: all DOCX text parts and workbook worksheets are read, and workbook rows with no authored literal value or formula are excluded from text indexing while their physical inventory is preserved; only exact-member-hash authenticated existing binary-DOC conversions are reused. Unsupported formats, failed text access and tracked text states are explicitly retained in the source-access manifest. No selected answer cells, reference queries, gold, source-positive labels or review judgments enter the raw augmentation.

A/B access one additive sourceAuthoredSummary property on 240 final WG-accepted CRs; C/D receive the complete physical report/document inventory's actually accessible raw text, including nonanswers. No physical/temporal whole graph-text equality or identical renderer view is claimed. Literal output scoring is separate from source/provenance correctness; WG meeting acceptance does not establish TSG ratification.

The input inventory includes supported and unsupported source files. Inventory completeness does not establish complete accessible text, identical graph/text cutoffs, or the same Word rendering. The two development judgments are AI reviews, with human/expert review count zero.

Both generated structured queries select the legacy `summaryOfChange` property and omit the added `sourceAuthoredSummary` property. All four requested-record F1 scores are zero; these measurements do not demonstrate successful use of the additive source summaries. The retained query text is available under `results/arm_outputs`.

Strict exact typed-string multiset scoring checks requested summary records and occurrence frequencies. It does not accept every whitespace-equivalent rendering or semantic paraphrase, certify generated-query predicates/provenance, judge optional explanations, or establish later TSG ratification/TS enactment. No source-correction-caused model improvement is inferred.

Offline retained prompt/parser/score replay:

```bash
python -B tools/verify_retained_four_methods.py --evidence .
python -B source_patch/verify_summary_source_patch.py --patch source_patch
```

These commands verify exact package hashes, reconstruct five prompts, reparse saved responses, recompute four strict scores and replay the source contract with saved native/SQL/source values and 21 scorer controls. Large raw JSONL inputs use lossless gzip export; the verifier streams decompression and compares the complete original SHA256 and byte count. They do not call a provider, rerun full-text retrieval or a database, or re-render the original Word archives. External graph/SQL build inputs and original archive/member/renderer pins remain in source_patch. Historical absolute paths are preserved as provenance; offline replay resolves package-relative copies.
