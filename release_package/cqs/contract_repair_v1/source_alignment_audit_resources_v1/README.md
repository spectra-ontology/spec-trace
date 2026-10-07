# Verify the original-question alignment audit

The adjacent `source_alignment_audit_v1` directory contains the fixed 560 original questions, reference queries, declared scored fields, value-free native field metadata, 112 closed AI audit receipts and the complete-denominator report. Its 345-file manifest is immutable. The audit diagnoses agreement between artifacts; it does not certify semantic truth, source completeness or expert-reviewed gold. Human/domain-expert validation remains zero.

From `release_package/cqs/contract_repair_v1`, run:

```sh
python3 -I source_alignment_audit_resources_v1/verify_semantic_alignment_audit_export_v1.py source_alignment_audit_v1
```

The verifier checks every listed public byte hash, all 112 fixed calls, output structure, exact frozen source spans, derived diagnostics and all 560 dispositions per rater. It makes no model calls or database queries. Private CLI stdout/stderr and event transcripts are excluded; their producer-verified binding and byte hashes are retained, and this offline verifier explicitly does not recompute that private binding.

This separate appendix preserves the authorized resource changes from four workers to an additional four-worker tail pool and then a four-worker burst pool. The scientific inputs, prompts, model request, medium reasoning, 600-second timeout and 112 fixed attempt slots stayed unchanged; invalid batches were neither salvaged nor retried. The last resource phase permitted at most 12 concurrent workers, while the existing tail admission guard could pause future tail jobs. Sustained concurrency or a quantitative speedup is not claimed. RSS observations are sampled; three independent 8GiB soft budgets are neither a shared limit nor a hard cap. Historical dispatcher source is supplied for provenance; the quickstart above performs only offline verification.

The included local verification receipt records PASS for all 345 primary files, 104 format/provenance-valid calls and 8 invalid calls. Each rater still has all 560 item dispositions; 480 items have both valid audit receipts, and 80 retain an unavailable rater. Validity and agreement are separate from successful alignment. This is a local export; repository publication is recorded separately.
