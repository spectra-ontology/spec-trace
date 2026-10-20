# One original question: saved first evaluation with explicit compatibility recovery

This N1 cohort evaluates contributor rankings within each specification's recorded resolutions. Registration starts from494 active contracts; prospective495/14/51 is not a publication claim. Earlier cohorts and scores remain separate.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 1 | 0.0000 | 0/1 | 1 |
| text2sql | 1 | 0.0000 | 0/1 | 1 |
| single_retrieval | 1 | 0.0000 | 0/1 | 1 |
| iterative_retrieval | 1 | 0.0000 | 0/1 | 1 |


Five first response stages are retained, with all four methods abstaining and scoring zero. Original structured calls were reused byte for byte. The original retrieval adapter rejected the valid nested array mode sequence before any retrieval model call. Both original adapter failures, the original protocol and original adapter bytes are preserved in compatibility_recovery/. The single compatibility change accepts sequence; the previously uncalled three retrieval stages then received their first responses. No answer-based prompt, definition or source changes and no quality rerolls occurred. This is an explicitly repaired adapter execution.

The contract counts distinct source Tdocs per company and specification, with company-name tie order. Source-own boundaries remove later foreign Tdoc bodies. These are documentary reference/contribution relationships, without an approval, acceptance or causal-credit claim. Three complete saved native gold records and fresh SQL were checked before model calls. No new native answer query ran after the two structured methods abstained.

Human/expert validation0. Source verification does not enrich model inputs. Raw request, response, cost, retrieval context, parser, failure and score evidence remain public. Offline replay calls no API or database:

    python3 -B -I runtime/verify_authorized_incremental28_evaluation.py --evidence . --bundle ../original_core_overnight_repairs28

Large graphs, databases and retrieval indexes are omitted. Local paths are provenance rather than offline dependencies. No whole-graph factuality or expert certification is claimed.
