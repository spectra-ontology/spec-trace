# Source-enriched RAN2 single-question evaluation

This is a separate source-enriched snapshot evaluation of the preserved original English question RAN2_P4_CQ3-3: the RAN2-context plenary submission list for RAN#110. It does not change or merge the earlier frozen graph cohorts or their model results. The source repair adds nine documented CRPack nodes and no relationships; the retained full source selection has 240 CRDB rows and 35 pack identities, checked against nine original forwarding covers and the new native/SQL outputs. Two AI semantic reviews and seven scorer controls are retained; human/expert review count is zero.

Five first-generation requests to `anthropic/claude-opus-4.8`, with Anthropic pinned and one worker, received HTTP 200. Recorded cost is $0.356490 with no unknown-cost response and no quality regeneration. Each method has one item. Requested-field strict F1/exact are 1/true for Text2Cypher, 0/false for Text2SQL, 0/false for single retrieval, and 0/false for iterative retrieval. The SQL model generated an executable indirect HAS_CR/PRESENTED_AT query that returned no rows; it was retained without regeneration. Both retrieval methods abstained. These are one-question observations, not evidence of a general graph advantage.

A/B use the enriched graph and its graph-equivalent SQL snapshot with value-free schemas. C/D use unchanged lexical retrieval over the retained base corpus plus all 240 original register rows as individual source documents. No pack answer list, reference query, gold, repair rationale or review record is appended to model inputs. The old graph/text cutoff and content equality remain unverified, and bounded retrieval does not establish full requested-population coverage.

The companion includes the source bundle, original proposal, frozen protocol and code, all five requests/responses, contexts, generated queries, execution receipts, strict metrics, and cost receipts. Full live databases and the 6.5 GB retrieval index are not duplicated here; hashes identify those locally executed assets. The separately published source repair provides the additive patch and reconstruction recipe.

```bash
python3 -B runtime/verify_source_enriched_evaluation.py --evidence . --out /tmp/source-enriched-verification.json
```

The offline command reconstructs all five prompts from original question/schema/retained source passages, checks actual responses and denominator/pin consistency, verifies the source bundle, and reruns all four strict scores in a fresh temporary copy. It does not call a provider or rerun live database queries or lexical retrieval. All earlier scientific artifacts are preserved.
