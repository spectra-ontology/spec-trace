# Process requirements and the released schema

SPECTRA organizes contributions, meeting outcomes and specification changes
so they can be queried together. This page connects those tasks to specific
representation choices and identifies the files that exercise them. It
describes the resource's design and supported access; it does not establish
that this schema is uniquely necessary or better than another representation.

The declarations are in [spectra.ttl](../ontology/spectra.ttl). The complete
corpus is in the [per-WG deposit](../kg/per_wg/README.md); the three
[process metadata exports](process_kg/SCHEMA.md) contain a smaller set of
properties. A property declaration alone is not evidence of population.

| Process task and representation requirement | Declared classes and properties | Released query or example, and its scope |
|---|---|---|
| Identify a submitted document, its meeting and its revision separately. A document identifier need not imply exactly one meeting placement. | `Tdoc`, `Meeting`, `Company`; `tdocNumber`, `presentedAt`, `submittedBy`, `isRevisionOf`. `CR` and `LS` are subclasses of `Tdoc`. | `process_kg/ran1_tdoc_metadata.ttl` retains these relations; the export has 123,678 TDoc records and 123,677 distinct identifiers, including one re-tabled record. |
| Retrieve an outcome under its meeting and agenda while preserving whether it is an Agreement, Conclusion or WorkingAssumption. | `Resolution` and its three subclasses; `madeAt`, `resolutionBelongsTo`, `references`. | [Phase-2 SPARQL](../queries/sparql/CQ2-1_agreements_by_agenda_item.rq) retrieves Agreements by meeting and agenda. The released RDF represents Agreement content and Resolution placement on distinct IRIs sharing `resolutionId`; the query joins on that key. |
| Separate a CR's target specification, release and affected clause. A specification number alone cannot identify a release-specific clause edition. | `CR`, `Spec`, `Release`, `Section`; `modifies`, `targetRelease`, `modifiesSection`, `belongsToSpec`. | [Phase-3 SPARQL](../queries/sparql/CQ3-1_crs_modifying_section.rq) uses the RAN1 body graph. The metadata CR export retains `modifies` and `targetRelease`, but omits `modifiesSection`. |
| Keep the sender and recipient of a liaison statement as distinct roles, including multiple WG endpoints. | `LS`, `WorkingGroup`; `originatedFrom`, `sentTo`. Both relations allow multiple endpoints. | `process_kg/ls_routing.ttl` supports routing counts; [mini-sample Q2](real_world_mini/queries/Q2_cross_wg_ls.rq) illustrates the directional join. An LS routing edge is evidence of an addressed recipient, not proof of downstream influence. |
| Query a Technical Report's recorded impact targets and their attributes through a distinct impact record. | `TechnicalReport`, `TRImpact`, `Spec`, `Section`; `hasTRImpact`, `impactOfTR`, `impactsSpec`, `impactsSection`. | [Phase-5 SPARQL](../queries/sparql/CQ5-1_trs_impacting_spec.rq) exercises the RAN1 body graph. Follow its realization note: the deposited predicate is spelled `impactOfTr`, whereas the OWL declaration is `impactOfTR`. |
| Scope documents and Technical Reports by Work Item without conflating the two subject types. | `Tdoc` → `relatedTo` → `WorkItem`; `TechnicalReport` → `relatedToWorkItem` → `WorkItem`. | [Phase-1 SPARQL](../queries/sparql/CQ1-1_tdocs_by_meeting_and_workitem.rq) uses `relatedTo` in the RAN1 body graph. Neither Work Item predicate is populated in the metadata-only export. |
| Represent a WorkingAssumption becoming an Agreement if that transition is recorded. | `WorkingAssumption` → `promotedTo` → `Agreement`. | This is a declared capability, **unpopulated in the released and deployed corpus snapshots**. The edge in [end_to_end/](end_to_end/README.md) is synthetic and demonstrates the pattern only. |

The representation preserves typed records, role direction and edition
scope for joins and aggregation. These requirements also admit relational
tables. The SQL comparison addresses structured access to the same stored
reference-query answer sets; it does not isolate a benefit caused by the graph schema.
No schema ablation or matched comparison with another telecom KG was run.

## References and meeting context

`Resolution references Tdoc` and `CR modifiesSection Section` encode different
source relations. A CR may be the target of a Resolution's `references`
edge because `CR` is a subclass of `Tdoc`. There is no separate declared
Resolution-to-CR predicate.

The small [meeting sample](real_world_mini/README.md) and
[synthetic lifecycle](end_to_end/README.md) instead associate an Agreement
and a CR through a shared Meeting. Their query results identify documents
referenced by an Agreement at that meeting. This association does not show
that those documents motivated that CR or the clause it modifies.

The released [multi-hop query](../queries/sparql/MULTI_HOP_traceability.rq)
joins CR/Section and TRImpact/Spec paths using the shared `specNumber`.
It does not reconstruct the entire contribution-to-decision-to-CR chain.
Recoverable document references and clause targets are partial, so the
absence of an edge is not evidence that no underlying connection exists.

## What the released process records support

The [scenario mapping](USE_SCENARIOS.md) distinguishes corpus measurements
from illustrations. The saved
[released-graph recount](../validation/released_graph_scenario_counts.json)
finds 3,644 RAN1 LSs sent to RAN2, and 2,039 RAN2 plus 1,249 RAN3 CR instances
modifying TS 38.300. The RAN3 count includes `draftCR` and `pCR` instances.
These are queries over process records, not measurements of causal influence.

The separate [release-overlap analysis](../validation/release_overlap_analysis.json)
groups dated formal CRs by WG, upload year, target release and category.
It defines each WG/year's leader as the release receiving the most category-B
(feature) formal CRs, breaking ties toward the newer release. In RAN1–RAN4,
31,422 of 73,465 included formal CRs target a release older than that leader
(42.8%). This describes concurrent maintenance across release generations;
the comparator is not an official release freeze date.

RAN5 is reported separately because missing dates and years without category-B
CRs limit its usable denominator. These fields also exist in the 3GPP CR
register. Their analysis does not establish an insight unique to graph
links, nor which process relation is essential. The graph makes these
records available alongside meeting, document and specification records;
this statistic itself uses the CR fields.

To reproduce it from the deposited body files, run from the repository root:

```bash
python3 release_package/pipeline/analyse_release_overlap.py \
  --ttl-dir /path/to/deposited/body/files --output /tmp/release_overlap.json
```

The offline runner checks the five fixed input SHA-256 values and requires
agreement between a subject-block parser and a separate line-state parser.
It reports exclusions, yearly leaders and the separate RAN5 denominator.
Without the files it exits with status 2 and writes no result.
