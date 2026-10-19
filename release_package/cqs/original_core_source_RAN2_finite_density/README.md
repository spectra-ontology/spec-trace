# RAN2 finite dependency source snapshot

This is a separate source experiment for `RAN2_P3_CQ5-3`. The original English question and exact `LIMIT 5` query remain unchanged. It adds eight Section identities, 107 metadata `MODIFIES` edges and 24 Section ownership/parent edges to the frozen RAN2 graph. Every old fact is retained. Original 560-question core admissions increase by **zero**.

Run the default offline saved-projection replay from any directory:

```sh
python3 -B -I /path/to/bundle/verify_bundle.py
```

The standard-library replay verifies the closed file inventory, official seven-unit criteria and two distinct reviews; derives the delta from the complete **included saved projections**; checks the current64 metadata multiset for 34,620 source-covered CRs and preserves two unknown LS-in source cases; checks 3,894 latest Section identities against 3,886 frozen identities; recomputes the four-field result and scorer controls; and compares saved native/SQL/whole-graph/corpus proofs. It does **not** freshly parse all 14 raw DOCX files or 64 raw workbooks, reconstruct historical 58 workbook versions, access a host checkout, run Neo4j, rebuild large graphs/corpus, call models, or certify complete source fidelity of the whole KG. Saved proof inspection is distinguished from rerunning those original operations.

The exact inner-match funnel is **72 CR-positive release-blind hubs → 15 with retained release links → 14 with positive Section paths**. Fifty-seven hubs have no retained release link; 38.822 has a retained latest edition but zero Section paths. These cases are excluded by the unchanged authored query. The positive latest editions are Rel-19. The current strict fifth/sixth gap is 3.35 > 2.17; no new tie-breaker is introduced.

The metadata cohort is explicitly the pinned current 64 workbooks, applied only to the frozen 34,622 CR nodes and 187 Spec nodes. Of 107 added pairs, 106 come from meeting #133 beyond the original Phase1 cutoff and one from #101bis. Six legacy target identifiers use the declared unique existing semantic-hub fallback after exact production-ID lookup fails. Two current LS-in metadata cases retain their graph labels and zero positive paths; their absent CR metadata is not certified as empty truth.

The Section repair covers identity/BELONGS query dependencies, with original Heading-style parents for the eight new Heading4 nodes. It preserves the broader current-pipeline differences: **155 properties and 395 old-only edges** remain untouched, and other source-positive hierarchy/reference/caption edges are not imported. It is not a complete current-source rebuild or a reconstruction of the historical graph. Counterpolicies and original design excerpts are included.

Optional byte verification requires explicit external paths; no fallback to recorded private paths occurs:

```sh
python3 -B -I verify_bundle.py --raw-source-root /explicit/original/input/root
python3 -B -I verify_bundle.py --base-sql /explicit/RAN2.sqlite --base-ttl /explicit/RAN2-body.ttl
python3 -B -I verify_bundle.py --source-sql /explicit/RAN2-finite-dependency.sqlite --source-ttl /explicit/RAN2-finite-dependency-body.ttl --fts /explicit/ran2.sqlite3
```

The raw-root option rehashes 78 pinned raw inputs and available pinned TS ZIP/member pairs; it does not rerun the full source parsers. Large-artifact options rehash the named artifacts only. Their full graph/corpus reconstruction remains the separately recorded actual proof unless the explicit recipes below are run. The frozen TTL is located at the public release path `release_package/kg/per_wg/RAN2-body.ttl`; its exact SHA and the relational export SHA are in the saved materialization manifest. Raw input names/pins and conventional upstream TS archive locators are in `provenance/optional_external_raw_input_inventory.json`; remote downloads were not tested during this preparation, and original #101bis archive provenance is not asserted where absent.

To construct new isolated TTL/SQLite files from explicit original base files (resource intensive, at least 26 GiB available on both Linux and Windows before starting; use an 8 GiB address-space/one CPU worker with a continuous 16 GiB reserve watchdog), run:

```sh
python3 -B -I recipes/materialize_graph.py --execute --base-ttl /explicit/RAN2-body.ttl --base-sql /explicit/RAN2.sqlite --output /new/isolated/output
```

This relocatable adapter keeps the tested generic delta and storage algorithms. It verifies every original typed row/schema across all 79 storage tables, original TTL byte prefix, all new node representations and typed/global relationships, then the whole TTL/SQL fact equality. It is not automatically run by the lightweight verifier. A larger corpus can be rebuilt/verified with `recipes/build_generic_graph_corpus.py`; use its `--help`, the included public lexical parser, the new whole TTL, and a newly named output directory. No question, answer, prefix fixture or raw cover is a corpus fact input. Saved corpus build and all-fact reconstruction receipts retain the first Windows-memory-check infrastructure failure and identical-input successful retry.

The prospective definition and primary packet keep their historical pre-execution statuses. Actual completed materialization/native/corpus receipts are separate. Secondary v1's overly broad “all15 positive-CR hubs” wording is superseded by v2 and the 72→15→14 independent recount; original bytes remain available. No model evaluation results belong to this source bundle. Expert validation count: **0**.
