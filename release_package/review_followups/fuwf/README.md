# Source checks and reproducible process views

This directory is an additive evidence release in the existing public repository.
It preserves the frozen graph and separates original-source checks, source-derived
views and retained model outputs. No OpenReview comment has been posted by this work.

- Relationship cases and counting units: [review_units.json](refinement/review_units.json) and [all fixed outcomes](refinement/latest_audit_summary.json).
- One agreement-to-normative-incorporation example: [original-source excerpts, hashes and locators](refinement/normative-trace/evidence-excerpt.json), [frozen graph boundary](refinement/review-evidence/trace_boundary.json), and [official PDF access](refinement/review-evidence/external_document_access.json).
- Reusable data: [47 liaison records](verified-routing-slice/records.csv), [62 recipient memberships](verified-routing-slice/addressed_recipients.csv), and [45 CR records / 112 declarations](refinement/source-derived-cr-declarations/manifest.json).
- Executable reuse: [37 paired query definitions and expected rows](refinement/executable-source-views/queries_and_gold.json), [retained results](refinement/executable-source-views/query_results.json), and [comparator scope](refinement/review-evidence/comparator_scope.json).
- Controlled routing diagnostic: [all 75 retained trial scores](matched/analysis.json). It does not establish KG superiority; full text and SQL access47 records, capped text accesses10.
- Current original-Core scope: [pinned402/560 index](refinement/current-public-index/README.md), with158 pending. The earlier371-item cutoff-tie investigation is retained as historical evidence; its proposal-publication fields are not current status.
- [Detailed guide](REVIEW_GUIDE.txt), [short inspection route](REVIEW_ENTRY_POINT.txt), [comment draft](response_draft.txt), and [proposed manuscript claim changes](manuscript_claim_revisions.txt).

From this directory, using Python3.10+ and rdflib7.6.0:

```sh
python3 -B verify_refinement.py
```

The verifier checks every packaged file hash, sampling identities and counts,
rebuilds SQLite/RDF views, executes37 SQL and37 SPARQL queries, and rescores75
retained attempts. It makes no model calls or operational database connections.
It does not download or reauthenticate all native originals. Full native documents
are linked to their official sources and are not redistributed here.

The491/500 cases include unresolved cases and nine unfilled slots. Query consistency
is distinct from independent extraction accuracy. Domain-expert assessments: zero.
The incorporation example is one source-investigated chain, not automated full-KG
execution. General completeness, practitioner benefit and representation superiority
remain unestablished. Earlier preparation and delivery metadata are retained as
historical snapshots; this entry and the detailed guide govern the current scope.

Current Core index pin: `05c59042597c8cc707f12c883a8ea882fea96b06`.
