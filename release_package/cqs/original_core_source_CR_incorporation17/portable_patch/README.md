# Separate documentary incorporation source snapshot

This preserves the original CQ045 English and adds 17 documentary observations, 34 directed relationships and 765 RDF triples to a separately rebuilt RAN1 snapshot. All frozen nodes, properties, relationships, 89 SQL tables and original RDF prefix remain unchanged. Frozen CQ045 and its old query are not silently admitted or replaced.

Each observation binds an individual approved CR to its actual normative TS change-history incorporation. CR base version 17.2.0 and incorporated new version 17.3.0 remain distinct. Existing Resolution references are preserved, including two CRs without a recorded reference. Citation alone does not imply approval; the documentary relationship does not imply sole causal influence.

The source archive inventory contains authentic original ZIP bytes. The legacy DOC cover is retained as binary; exact XML identity is not claimed for it. Serialized XML is ElementTree structural serialization, not a raw XML byte slice. Historical evidence preserves its original local paths; the verifier resolves authentic archive bytes by hashes, using only portable package paths.

Run `python verify_rebuild.py --package . --base-sql RAN1.sqlite --base-ttl RAN1-body.ttl --out-dir NEWDIR` with the hash-pinned frozen baselines. The verifier checks all source witnesses, reproduces the additive SQL/RDF snapshot and compares every frozen SQL table in both directions. This script runs no containers, models or network calls. Source-enriched model evaluations are separately registered; no model performance is implied by source verification. Reviews are two AI judgments; human expert validation is zero.
