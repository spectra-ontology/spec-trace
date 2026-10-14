# Original-preserving repair evidence

371 of 560 original English questions are admitted: 119 scorer-only and 252 query-and-scorer repairs. 189 remain pending; 0 are blocked. This is a contract/native/scorer result, not model accuracy or complete original-Core validation.

The admitted contracts retain 776,873 native rows and 3,130 actual scorer controls. Human author semantic review and independent domain-expert review remain 0.

The frozen 350 source-main audit inspected 3 targeted questions in 7 original archive files. Only one requested-ID source population was reconstructed; the other two checks support returned fields/text. The separate 21 handoff includes one actually inspected fixed-CR DOCX source form in one additional archive. These source checks do not establish raw-source factual completeness across 371.

The exact original questions, old/repaired queries, answer fields, execution files and SHA256 links are in `repair_case_evidence.json`.

| Error type | Original item | Observed issue and repair |
| --- | --- | --- |
| wrong_first_column_answer_role | RAN5_P3_CQ4-4 | The released answer contract selects resCount although the English question asks the number of CRs. The query itself returns both counts. Keep the original query; require integer crCount mapped to the returned crCount column, not the first column. |
| dropped_requested_distribution_counts | RAN3_P5_TR-CQ-1-4 | The released scalar-set contract grades tr.trStatus only. It cannot check the count associated with each requested status. Keep the original query; require named status and integer trCount together in each distribution record. |
| unasked_limit_omits_requested_spec_union | RAN5_P4_CQ4-4 | The question has no quota, but the original query imposes ORDER BY spec LIMIT 10 on the full declared OtherSpecs union. Remove the cap while preserving the original Samsung CONTAINS filter and all three declared affected-Spec relationship roles. |
| mandatory_presented_tdoc_proxy_omits_covered_agenda | RAN3_P1_CQ1-9 | The original query demands a PRESENTED_AT TDoc and caps the result at10. The full uncapped TDoc proxy still covers42 source AgendaItem nodes; a Summary-covered agenda2.5 is omitted. Use the direct AgendaItem meetingNumber130 source population with no cap. The existing Summary2.5 and its Meeting130 MADE_AT relation support covered scope. |
| unstated_top10_replaces_maximum_all_ties | RAN5_P3_CQ2-4 | The English asks most frequent with no k. The original LIMIT10 returns the ranked positive pair pool rather than only maximum-frequency pairs. Count distinct directed reference relationships per spec-number pair, compute the maximum over the complete eligible pair pool, and return every maximum tie. |
| spec_filter_on_source_instead_of_returned_target | RAN3_P3_CQ2-3 | The original query constrains source s1 to38.413 and returns s2 without that target-membership clause. It also imposes an unasked top10. An actual out-of-spec returned row is not inferred from this code defect. Place38.413 membership on the requested target Section, include zero-reference targets, count all recorded incoming Section references, and return all maximum ties. |
| topk_boundary_membership_hidden_by_fixed_reference_subset | RAN3_P2_CQ1-8 | The original query groups by reusable agendaNumber and truncates with LIMIT 10; its scalar-set reference cannot represent the complete entity rank pool and boundary alternatives. In the corrected full source pool, the top 10 boundary has five tied agenda identities for two remaining slots. Group by the actual AgendaItem entity and capture the complete 3,582-item pool including zeros. Require exactly 10 eligible identities, all eight higher-ranked identities, and any two of the five boundary ties; do not require an unasked count field or lexical tie-break. |
| declared_contract_ignored_by_first_column_scoring | RAN5_P4_CQ2-1 | The released answer contract correctly names s.specNumber, but benchmark gold_primary_column/gold_primary_values and the legacy first-column scoring path select c.tdocNumber. The query already follows the declared OtherSpecs relationship roles. Keep the original query and map requested spec to native s.specNumber. The original archived R5-255419 DOCX declares Test specifications TR36.903; the primary modified Spec is36.521-3, a separate form role. |

The nullable-AgendaItem-id merge is an intermediate continuation-candidate error. It is not presented as an error in the submitted original query.

`../expert_review_extension21/` contains 21 unfilled independent inputs/forms and 21 procedurally sealed reference links. Supply original questions and sources first, then fix independent interpretations and answers before opening references. The existing 350 expert pack is preserved. Prepared forms are not completed expert validation.

The main 350 original attempt, transport recovery and additional 21 empirical phase have separate denominators and protocols. Native/scorer evidence does not transfer old 31/36 or historical nine-model scores. Raw archive text and frozen graph cutoff/content equality remain unverified.

Local preparation, public publication and external download verification are separate states; this new handoff artifact records local preparation only.
