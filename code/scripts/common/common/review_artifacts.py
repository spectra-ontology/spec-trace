"""온톨로지 검수 파일의 저장 경로를 구성하고 기록된 SHA256과 크기를 대조합니다.

Spec: docs/common/standards/naming_conventions.md §7.4·§7.5.
현재 산출물은 WG와 작업별 경로에 쓰고, 보존된 파일은 기록된 경로와 SHA256으로 찾습니다.
LLM 호출: 0건. 경로 해석과 읽기 검증만 수행합니다.

아래 이관 목록은 개발 환경에서 실제로 옮긴 파일과 디렉토리의 경로를 정의합니다.
배포본에는 현재 경로 API와 공통 루트 별칭을 포함하며, 개발 환경의 개별 이관 목록은
배포 준비 정책에 따라 제외합니다. 파일을 실행하거나 작업을 재개하기 위한 조건은
호출자가 따로 검증합니다.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
from types import MappingProxyType

from common import axis


LEGACY_REVIEW_ROOT = PurePosixPath("logs/common/verification/ontology_system_review")
REVIEW_ROOT = PurePosixPath("logs/common/verification/ontology-system-review")

# 실제로 이관한 상위 디렉토리만 등록합니다. 새 실행에는 아래 경로 API를 사용하며,
# 등록되지 않은 옛 경로는 파일 시스템을 탐색해 추정하지 않습니다.
_LEGACY_DIRECTORIES = (
    "",
    "body_source_metadata_RAN3",
    "body_source_metadata_RAN4",
    "body_source_metadata_RAN4_preflight_relative_path_attempt",
    "body_source_metadata_RAN5",
    "context_reconciliation_preimages",
    "cq_shortfall_followup",
    "cq_shortfall_followup/ts_search_display_preimages",
    "cr_lexical_cache_reconciliation",
    "jsonld_context_preimages",
    "jsonld_context_preimages/20261030T025747.629136Z",
    "jsonld_context_preimages/20261030T025747.629136Z/phase-1",
    "jsonld_context_preimages/20261030T025747.629136Z/phase-1/RAN1",
    "jsonld_context_preimages/20261030T025747.629136Z/phase-1/RAN2",
    "jsonld_context_preimages/20261030T025747.629136Z/phase-1/RAN3",
    "jsonld_context_preimages/20261030T025747.629136Z/phase-1/RAN4",
    "jsonld_context_preimages/20261030T025747.629136Z/phase-1/RAN5",
    "ran2_annex_document_metadata_applied",
    "ran2_annex_document_metadata_reconciliation",
    "ran2_annex_native_body",
    "ran2_annex_native_body/body_vectors",
    "ran2_annex_native_body/extensions",
    "ran2_annex_native_body/metadata",
    "ran2_annex_native_body/vectors",
    "ran2_annex_native_bulk",
    "ran2_annex_native_bulk/body_vectors",
    "ran2_annex_native_bulk/extensions",
    "ran2_annex_native_bulk/metadata_applied",
    "ran2_body_source_metadata_final_reconciliation",
    "ran2_body_source_metadata_tdoc_reconciliation",
    "ran2_native_conversion",
    "ran2_native_conversion/R2-164573",
    "ran2_native_conversion/R2-1702194",
    "ran2_native_conversion/R2-1803829",
    "ran2_native_conversion/R2-1813139",
    "ran2_native_conversion/R2-1813144",
    "ran3_assigned_source_metadata_reconciliation",
    "ran3_classified_source_body_reconciliation",
    "ran3_source_form_extensions_reconciliation",
    "ran3_source_metadata_reconciliation",
    "ran4_additional_classified_source_body_reconciliation",
    "ran4_additional_source_form_extensions_reconciliation",
    "ran4_additional_source_metadata_reconciliation",
    "ran4_classified_source_body_reconciliation",
    "ran4_remaining_source_form_extensions_reconciliation",
    "ran4_remaining_source_metadata_reconciliation",
    "ran4_source_form_extensions_reconciliation",
    "ran4_source_metadata_reconciliation",
    "ran5_assigned_source_metadata_reconciliation",
    "ran5_classified_source_body_reconciliation",
    "ran5_source_form_extensions_reconciliation",
    "ran5_source_metadata_reconciliation",
    "recovered_ts_sections",
    "recovered_ts_sections/preimage",
    "resolution_loader_preimages",
    "resolution_vectors",
    "resolution_vectors/20261030T001129.664887Z_RAN1",
    "resolution_vectors/20261030T001134.370033Z_RAN2",
    "resolution_vectors/20261030T001135.992194Z_RAN3",
    "resolution_vectors/20261030T001137.861551Z_RAN4",
    "resolution_vectors/20261030T001137.997774Z_RAN5",
    "resolution_vectors/20261030T001243.101388Z_RAN1",
    "resolution_vectors/20261030T001733.651789Z_RAN2",
    "resolution_vectors/20261030T001836.674455Z_RAN3",
    "resolution_vectors/20261030T001902.677083Z_RAN4",
    "resolution_vectors/20261030T001946.823328Z_RAN5",
    "resolution_vectors/20261030T002324.268303Z_RAN5",
    "resolution_vectors/20261030T002324.343461Z_RAN5_anchors",
    "resolution_vectors/20261030T002438.535429Z_RAN5",
    "resolution_vectors/20261030T002438.681606Z_RAN5_anchors",
    "resolution_vectors/20261030T002544.033503Z_RAN2",
    "resolution_vectors/20261030T002544.142718Z_RAN2_anchors",
    "resolution_vectors/20261030T002559.647334Z_RAN1",
    "resolution_vectors/20261030T002559.918840Z_RAN1_anchors",
    "resolution_vectors/20261030T003029.968523Z_RAN4",
    "resolution_vectors/20261030T003030.056920Z_RAN4_anchors",
    "resolution_vectors/20261030T003527.366253Z_RAN3",
    "resolution_vectors/20261030T003527.465002Z_RAN3_anchors",
    "resolution_vectors/20261030T003552.565856Z_RAN5",
    "resolution_vectors/20261030T003552.642424Z_RAN5_anchors",
    "resolution_vectors/20261030T012858.472863Z_RAN3",
    "resolution_vectors/20261030T013406.276923Z_RAN1",
    "resolution_vectors/20261030T013415.348762Z_RAN2",
    "resolution_vectors/20261030T013738.912993Z_RAN3",
    "resolution_vectors/20261030T013739.235404Z_RAN3_anchors",
    "resolution_vectors/20261030T014426.954966Z_RAN4",
    "resolution_vectors/20261030T021227.623474Z_RAN4",
    "resolution_vectors/20261030T021228.395860Z_RAN4_anchors",
    "resolution_vectors/20261030T023013.772560Z_RAN3",
    "resolution_vectors/20261030T023332.271723Z_RAN5",
    "resolution_vectors/20261030T023408.463986Z_RAN3",
    "resolution_vectors/20261030T023408.769628Z_RAN3_anchors",
    "resolution_vectors/20261030T030727.389362Z_RAN3",
    "resolution_vectors/20261030T030900.048545Z_RAN3",
    "resolution_vectors/20261030T030900.345592Z_RAN3_anchors",
    "resolution_vectors/20261030T031311.193410Z_RAN5",
    "resolution_vectors/20261030T031430.805482Z_RAN5",
    "resolution_vectors/20261030T031431.099467Z_RAN5_anchors",
    "resolution_vectors/20261030T042144.416812Z_RAN4",
    "resolution_vectors/20261030T042346.078442Z_RAN4",
    "resolution_vectors/20261030T042346.854300Z_RAN4_anchors",
    "resolution_vectors/20261030T060019.706802Z_RAN2",
    "resolution_vectors/20261030T060329.376168Z_RAN2",
    "resolution_vectors/20261030T060329.516115Z_RAN2_anchors",
    "tdoc_source_vectors",
    "tdoc_source_vectors/20261030T014524.761962Z_RAN5",
    "tdoc_source_vectors/20261030T021145.583695Z_RAN5",
    "tdoc_source_vectors/20261030T030015.816115Z_RAN5",
    "word_conversion_recovery",
    "word_conversion_recovery/accepted",
    "word_conversion_recovery/preimages",
    "word_conversion_recovery_followup",
    "word_conversion_recovery_followup/accepted",
    "word_conversion_recovery_followup/accepted/0e2c218399f85072",
    "word_conversion_recovery_followup/accepted/be00c7b32149b8bc",
    "word_conversion_recovery_followup/accepted/eda74313022ee05e",
    "word_conversion_recovery_followup/minimal_xml",
    "word_conversion_recovery_followup/minimal_xml/0e2c218399f85072",
    "word_conversion_recovery_followup/minimal_xml/12cbcf298232e35c",
    "word_conversion_recovery_followup/minimal_xml/1ca0dc44c074b922",
    "word_conversion_recovery_followup/minimal_xml/2c22b101ad8a4246",
    "word_conversion_recovery_followup/minimal_xml/be00c7b32149b8bc",
    "word_conversion_recovery_followup/minimal_xml/eda74313022ee05e",
    "word_conversion_recovery_followup/preimages",
    "word_conversion_recovery_indexed",
    "word_conversion_recovery_indexed/0cccad92422f3f88",
    "word_conversion_recovery_indexed/219f5ca1a7908a76",
    "word_conversion_recovery_indexed/641e174b9a92b345",
    "word_conversion_recovery_indexed/77f8fe1521f6711a",
    "word_conversion_recovery_indexed/preimages",
    "cq_shortfall_followup/agenda_context_schema_preimages",
    "cq_shortfall_followup/ie_description_math_application",
    "cq_shortfall_followup/ie_description_math_plan",
    "cq_shortfall_followup/ran4_861_proposal",
    "cq_shortfall_followup/ran4_primary_sources",
    "ran3_cq_official_followup",
    "ran3_cq_official_followup/canonical_preimages",
    "ran3_cq_official_followup/sources",
    "ran4_cq_official_followup",
    "ran4_cq_official_followup/canonical_preimages",
    "ran4_cq_official_followup/final_canonical_preimages",
    "ran4_cq_official_followup/reproduction_bytes",
    "ran4_cq_official_sources",
    "ran5_tr_followup",
    "ran5_tr_followup/application_20261030T080850724897Z",
    "ran5_tr_followup/nochange_application_20261030T082547819704Z",
    "ran5_tr_followup/sources",
    "cq_shortfall_followup/ran1_agenda_reconciliation",
    "cq_shortfall_followup/ran1_agenda_reconciliation/preimages",
    "cq_shortfall_followup/ran1_agenda_live_reconciliation",
    "cq_shortfall_followup/ran1_decision_disposition_reconciliation",
)

RECEIPT_RENAMES = MappingProxyType({
    "live_semantic_roles_ran2_final.json": "live_semantic_roles_ran2.json",
    "python_syntax_final.json": "python_syntax.json",
    "ran2_all_indexed_cr_source_strict_xml_final.json": "ran2_all_indexed_cr_source_strict_xml.json",
    "ran2_annex_all_variant_strict_xml_final.json": "ran2_annex_all_variant_strict_xml.json",
    "ran2_annex_normal_field_gate_final.json": "ran2_annex_normal_field_gate.json",
    "vector_integrity_changed_final.json": "vector_integrity_changed.json",
    "vector_integrity_final.json": "vector_integrity.json",
    "vector_integrity_ran2_cr_final.json": "vector_integrity_ran2_cr.json",
    "vector_integrity_ran2_final.json": "vector_integrity_ran2.json",
    "vector_integrity_ran2_resolution_final.json": "vector_integrity_ran2_resolution.json",
})

# WG는 파일명이 아니라 기존 산출물의 명시 scope와 입력 모집단으로 확인합니다.
# 등록된 파일 경로만 옮깁니다. 내용이 올바른지와 실행 가능한지는 별도로 검사합니다.
ROOT_FILE_LAYOUT = MappingProxyType({
    **{old: (None, new) for old, new in RECEIPT_RENAMES.items()},
    "body_source_metadata_RAN3.idempotence.json": ("RAN3", "body_source_metadata.idempotence.json"),
    "body_source_metadata_RAN3.json": ("RAN3", "body_source_metadata.json"),
    "body_source_metadata_RAN3.plan.json": ("RAN3", "body_source_metadata.plan.json"),
    "body_source_metadata_RAN4.idempotence.json": ("RAN4", "body_source_metadata.idempotence.json"),
    "body_source_metadata_RAN4.json": ("RAN4", "body_source_metadata.json"),
    "body_source_metadata_RAN4.plan.json": ("RAN4", "body_source_metadata.plan.json"),
    "body_source_metadata_RAN5.idempotence.json": ("RAN5", "body_source_metadata.idempotence.json"),
    "body_source_metadata_RAN5.json": ("RAN5", "body_source_metadata.json"),
    "body_source_metadata_RAN5.plan.json": ("RAN5", "body_source_metadata.plan.json"),
    "liaison_reference_reconciliation_RAN2_e32e174bef2faf4d_apply.json": ("RAN2", "liaison_reference_reconciliation_e32e174bef2faf4d_apply.json"),
    "liaison_reference_reconciliation_RAN2_e32e174bef2faf4d_plan.json": ("RAN2", "liaison_reference_reconciliation_e32e174bef2faf4d_plan.json"),
    "liaison_reference_reconciliation_RAN3_df808175ee34ce7e_apply.json": ("RAN3", "liaison_reference_reconciliation_df808175ee34ce7e_apply.json"),
    "liaison_reference_reconciliation_RAN3_df808175ee34ce7e_plan.json": ("RAN3", "liaison_reference_reconciliation_df808175ee34ce7e_plan.json"),
    "liaison_reference_reconciliation_RAN5_ec3d4def6d24e02d_apply.json": ("RAN5", "liaison_reference_reconciliation_ec3d4def6d24e02d_apply.json"),
    "liaison_reference_reconciliation_RAN5_ec3d4def6d24e02d_plan.json": ("RAN5", "liaison_reference_reconciliation_ec3d4def6d24e02d_plan.json"),
    "live_semantic_roles_ran2_final.json": ("RAN2", "live_semantic_roles.json"),
    "ran2_109e_tdoc_body_source_metadata_additions.json": ("RAN2", "109e_tdoc_body_source_metadata_additions.json"),
    "ran2_2002006_tdoc_minimal_xml_independent_comparison.json": ("RAN2", "2002006_tdoc_minimal_xml_independent_comparison.json"),
    "ran2_annex_62_native_cr_source_plan.json": ("RAN2", "annex_62_native_cr_source_plan.json"),
    "ran2_annex_additional_62_reviews.json": ("RAN2", "annex_additional_62_reviews.json"),
    "ran2_annex_additional_native_cr_source_plan.json": ("RAN2", "annex_additional_native_cr_source_plan.json"),
    "ran2_annex_cr_index_inventory.pre_supplement.json": ("RAN2", "annex_cr_index_inventory.pre_supplement.json"),
    "ran2_annex_document_metadata_applied.json": ("RAN2", "annex_document_metadata_applied.json"),
    "ran2_annex_document_metadata_reconciliation.json": ("RAN2", "annex_document_metadata_reconciliation.json"),
    "ran2_annex_expanded_own_source_reviews.json": ("RAN2", "annex_expanded_own_source_reviews.json"),
    "ran2_annex_header_format_native_cr_source_plan.json": ("RAN2", "annex_header_format_native_cr_source_plan.json"),
    "ran2_annex_manual_native_cr_source_plan.json": ("RAN2", "annex_manual_native_cr_source_plan.json"),
    "ran2_annex_native_cr_source_plan.json": ("RAN2", "annex_native_cr_source_plan.json"),
    "ran2_annex_normal_source_reviews.json": ("RAN2", "annex_normal_source_reviews.json"),
    "ran2_annex_own_header_format_reviews.json": ("RAN2", "annex_own_header_format_reviews.json"),
    "ran2_annex_own_label_native_cr_source_plan.json": ("RAN2", "annex_own_label_native_cr_source_plan.json"),
    "ran2_annex_phase1_identity_reconciliation.json": ("RAN2", "annex_phase1_identity_reconciliation.json"),
    "ran2_annex_residual64_tdoc_search_coverage.json": ("RAN2", "annex_residual64_tdoc_search_coverage.json"),
    "ran2_annex_substantive_title_reviews.json": ("RAN2", "annex_substantive_title_reviews.json"),
    "ran2_annex_title_source_reviews.json": ("RAN2", "annex_title_source_reviews.json"),
    "ran2_body_source_metadata_final_reconciliation.json": ("RAN2", "body_source_metadata_final_reconciliation.json"),
    "ran2_body_source_metadata_observed_grammar.json": ("RAN2", "body_source_metadata_observed_grammar.json"),
    "ran2_body_source_metadata_tdoc_plan.json": ("RAN2", "body_source_metadata_tdoc_plan.json"),
    "ran2_body_source_metadata_tdoc_reconciliation.json": ("RAN2", "body_source_metadata_tdoc_reconciliation.json"),
    "ran2_body_source_metadata_three_facts_reconciliation.json": ("RAN2", "body_source_metadata_three_facts_reconciliation.json"),
    "ran2_final_body_source_metadata_handoff_plan.json": ("RAN2", "final_body_source_metadata_handoff_plan.json"),
    "ran2_final_body_source_metadata_ledger_merge.json": ("RAN2", "final_body_source_metadata_ledger_merge.json"),
    "ran2_final_body_source_metadata_ledger_proposal.json": ("RAN2", "final_body_source_metadata_ledger_proposal.json"),
    "ran2_final_cr_body_source_metadata_plan.json": ("RAN2", "final_cr_body_source_metadata_plan.json"),
    "ran2_observed_cover_grammar_shadow_ledger_impact.json": ("RAN2", "observed_cover_grammar_shadow_ledger_impact.json"),
    "ran2_prospective_cr_body_source_metadata_plan.json": ("RAN2", "prospective_cr_body_source_metadata_plan.json"),
    "ran2_unassigned_number_tdoc_body_source_metadata_additions.json": ("RAN2", "unassigned_number_tdoc_body_source_metadata_additions.json"),
    "ran3_assigned_source_class_reconciliation.json": ("RAN3", "assigned_source_class_reconciliation.json"),
    "ran3_assigned_source_metadata_reconciliation.json": ("RAN3", "assigned_source_metadata_reconciliation.json"),
    "ran3_classified_source_body_reconciliation.json": ("RAN3", "classified_source_body_reconciliation.json"),
    "ran3_cq_official_followup.json": ("RAN3", "cq_official_followup.json"),
    "ran3_source_form_extensions_reconciliation.json": ("RAN3", "source_form_extensions_reconciliation.json"),
    "ran3_source_identity_reconciliation.json": ("RAN3", "source_identity_reconciliation.json"),
    "ran3_source_metadata_reconciliation.json": ("RAN3", "source_metadata_reconciliation.json"),
    "ran4_additional59_assigned_cr_classification_proofs.json": ("RAN4", "additional59_assigned_cr_classification_proofs.json"),
    "ran4_additional_classified_source_body_reconciliation.json": ("RAN4", "additional_classified_source_body_reconciliation.json"),
    "ran4_additional_source_classification_reconciliation.json": ("RAN4", "additional_source_classification_reconciliation.json"),
    "ran4_additional_source_form_extensions_reconciliation.json": ("RAN4", "additional_source_form_extensions_reconciliation.json"),
    "ran4_additional_source_metadata_reconciliation.json": ("RAN4", "additional_source_metadata_reconciliation.json"),
    "ran4_classified_source_body_reconciliation.json": ("RAN4", "classified_source_body_reconciliation.json"),
    "ran4_own_cover_class_correction_manifest.json": ("RAN4", "own_cover_class_correction_manifest.json"),
    "ran4_remaining_source_classification_reconciliation.json": ("RAN4", "remaining_source_classification_reconciliation.json"),
    "ran4_remaining_source_form_extensions_reconciliation.json": ("RAN4", "remaining_source_form_extensions_reconciliation.json"),
    "ran4_remaining_source_metadata_reconciliation.json": ("RAN4", "remaining_source_metadata_reconciliation.json"),
    "ran4_source_classification_reconciliation.json": ("RAN4", "source_classification_reconciliation.json"),
    "ran4_source_form_extensions_reconciliation.json": ("RAN4", "source_form_extensions_reconciliation.json"),
    "ran4_source_metadata_reconciliation.json": ("RAN4", "source_metadata_reconciliation.json"),
    "ran4_source_revision_correction_reconciliation.json": ("RAN4", "source_revision_correction_reconciliation.json"),
    "ran5_assigned_source_class_reconciliation.json": ("RAN5", "assigned_source_class_reconciliation.json"),
    "ran5_assigned_source_metadata_reconciliation.json": ("RAN5", "assigned_source_metadata_reconciliation.json"),
    "ran5_classified_source_body_reconciliation.json": ("RAN5", "classified_source_body_reconciliation.json"),
    "ran5_native_document_reconciliation.json": ("RAN5", "native_document_reconciliation.json"),
    "ran5_phase1_source_reconciliation.json": ("RAN5", "phase1_source_reconciliation.json"),
    "ran5_phase1_source_reconciliation.plan.json": ("RAN5", "phase1_source_reconciliation.plan.json"),
    "ran5_source_form_extensions_reconciliation.json": ("RAN5", "source_form_extensions_reconciliation.json"),
    "ran5_source_metadata_inventory.json": ("RAN5", "source_metadata_inventory.json"),
    "ran5_source_metadata_reconciliation.json": ("RAN5", "source_metadata_reconciliation.json"),
    "vector_integrity_ran2_cr_final.json": ("RAN2", "vector_integrity_cr.json"),
    "vector_integrity_ran2_final.json": ("RAN2", "vector_integrity.json"),
    "vector_integrity_ran2_resolution_final.json": ("RAN2", "vector_integrity_resolution.json"),
    "ran1_agreed_cr_annex_census.json": ("RAN1", "agreed_cr_annex_census.json"),
    "ran2_1706185_original_derived_vs_native_accepted_view.json": ("RAN2", "1706185_original_derived_vs_native_accepted_view.json"),
    "ran2_agreed_cr_annex_census.json": ("RAN2", "agreed_cr_annex_census.json"),
    "ran2_agreed_cr_annex_dd_coverage.json": ("RAN2", "agreed_cr_annex_dd_coverage.json"),
    "ran2_agreed_cr_annex_variant_census.json": ("RAN2", "agreed_cr_annex_variant_census.json"),
    "ran2_annex_additional_62_body_source_inventory.json": ("RAN2", "annex_additional_62_body_source_inventory.json"),
    "ran2_annex_body_source_metadata_plan_inventory.json": ("RAN2", "annex_body_source_metadata_plan_inventory.json"),
    "ran2_annex_corrupt20_source_variants.json": ("RAN2", "annex_corrupt20_source_variants.json"),
    "ran2_annex_cr_unindexed_source_exceptions.json": ("RAN2", "annex_cr_unindexed_source_exceptions.json"),
    "ran2_annex_final_unindexed_source_partition.json": ("RAN2", "annex_final_unindexed_source_partition.json"),
    "ran2_annex_five_native_source_rebinding.json": ("RAN2", "annex_five_native_source_rebinding.json"),
    "ran2_annex_followup_source_rebinding.json": ("RAN2", "annex_followup_source_rebinding.json"),
    "ran2_annex_full_cover_exceptions.json": ("RAN2", "annex_full_cover_exceptions.json"),
    "ran2_annex_full_cover_review_coverage.json": ("RAN2", "annex_full_cover_review_coverage.json"),
    "ran2_annex_identity_cover_census.json": ("RAN2", "annex_identity_cover_census.json"),
    "ran2_annex_identity_review_merge.json": ("RAN2", "annex_identity_review_merge.json"),
    "ran2_annex_native_source_validation.json": ("RAN2", "annex_native_source_validation.json"),
    "ran2_annex_new_cover_triage.json": ("RAN2", "annex_new_cover_triage.json"),
    "ran2_annex_other_own_id_adjudication_inventory.json": ("RAN2", "annex_other_own_id_adjudication_inventory.json"),
    "ran2_annex_own_label_native_view_differences.json": ("RAN2", "annex_own_label_native_view_differences.json"),
    "ran2_annex_own_label_six_conversion_validation.json": ("RAN2", "annex_own_label_six_conversion_validation.json"),
    "ran2_annex_own_label_six_source_inventory.json": ("RAN2", "annex_own_label_six_source_inventory.json"),
    "ran2_annex_own_label_six_source_reviews.json": ("RAN2", "annex_own_label_six_source_reviews.json"),
    "ran2_annex_pending_identity_review.json": ("RAN2", "annex_pending_identity_review.json"),
    "ran2_annex_producer_census.json": ("RAN2", "annex_producer_census.json"),
    "ran2_annex_remaining_own_identity_inventory.json": ("RAN2", "annex_remaining_own_identity_inventory.json"),
    "ran2_annex_root_first_six_own_label_reviews.json": ("RAN2", "annex_root_first_six_own_label_reviews.json"),
    "ran2_annex_scope_reconciliation.json": ("RAN2", "annex_scope_reconciliation.json"),
    "ran2_annex_source_events.jsonl": ("RAN2", "annex_source_events.jsonl"),
    "ran2_annex_source_events.pre_guard.jsonl": ("RAN2", "annex_source_events.pre_guard.jsonl"),
    "ran2_annex_substantive_title_watch.json": ("RAN2", "annex_substantive_title_watch.json"),
    "ran2_annex_target_alias_proofs.json": ("RAN2", "annex_target_alias_proofs.json"),
    "ran2_annex_unbound_expanded_cover_review.json": ("RAN2", "annex_unbound_expanded_cover_review.json"),
    "ran2_indexed_xml_meeting_recovery_independent_comparison.json": ("RAN2", "indexed_xml_meeting_recovery_independent_comparison.json"),
    "ran2_native_prepared_payload_independent_check.json": ("RAN2", "native_prepared_payload_independent_check.json"),
    "ran2_native_source_strict_xml_preflight.json": ("RAN2", "native_source_strict_xml_preflight.json"),
    "ran2_unassigned_cr_tdoc_source_coverage.json": ("RAN2", "unassigned_cr_tdoc_source_coverage.json"),
    "ran4_2108048_revision_direct_evidence.json": ("RAN4", "2108048_revision_direct_evidence.json"),
    "ran4_2108319_assigned_cr_variants.json": ("RAN4", "2108319_assigned_cr_variants.json"),
    "ran4_2206585_spec_adjudication.json": ("RAN4", "2206585_spec_adjudication.json"),
    "ran4_additional_class_inventory.json": ("RAN4", "additional_class_inventory.json"),
    "ran4_additional_revision67_cover_census.json": ("RAN4", "additional_revision67_cover_census.json"),
    "ran4_additional_revision67_receipt_reconciliation.json": ("RAN4", "additional_revision67_receipt_reconciliation.json"),
    "ran4_all1506_report_cover_revision_census.json": ("RAN4", "all1506_report_cover_revision_census.json"),
    "ran4_document_identity_cover_census.json": ("RAN4", "document_identity_cover_census.json"),
    "ran4_document_identity_no_docx_archive_inventory.json": ("RAN4", "document_identity_no_docx_archive_inventory.json"),
    "ran4_document_identity_report_span_verification.json": ("RAN4", "document_identity_report_span_verification.json"),
    "ran4_document_identity_review_final_validation.json": ("RAN4", "document_identity_review_final_validation.json"),
    "ran4_document_identity_review_initial_validation.json": ("RAN4", "document_identity_review_initial_validation.json"),
    "ran4_document_identity_slide_source_evidence.json": ("RAN4", "document_identity_slide_source_evidence.json"),
    "ran4_missing_actual_document_tuple_candidates.json": ("RAN4", "missing_actual_document_tuple_candidates.json"),
    "ran4_original1506_revision_legacy_recensus.json": ("RAN4", "original1506_revision_legacy_recensus.json"),
    "ran4_report_cover_revision_differences.json": ("RAN4", "report_cover_revision_differences.json"),
    "ran4_report_matched_revision_accepted_body_comparison.json": ("RAN4", "report_matched_revision_accepted_body_comparison.json"),
    "ran4_report_revision_receipt_rebinding.json": ("RAN4", "report_revision_receipt_rebinding.json"),
    "ran4_source_classification_inventory.json": ("RAN4", "source_classification_inventory.json"),
    "ran5_additional_document_master_census.json": ("RAN5", "additional_document_master_census.json"),
    "ran5_additional_document_source_proofs.json": ("RAN5", "additional_document_source_proofs.json"),
    "tr_ran5_native_error_source_discovery.json": ("RAN5", "tr_native_error_source_discovery.json"),
    "ran2_annex_full_retained_cover_census.log": ("RAN2", "annex_full_retained_cover_census.log"),
    "ran2_annex_native_cr_source_plan.log": ("RAN2", "annex_native_cr_source_plan.log"),
    "ran2_annex_producer_census.log": ("RAN2", "annex_producer_census.log"),
    "ran2_annex_producer_census.pre_guard.log": ("RAN2", "annex_producer_census.pre_guard.log"),
    "ran2_annex_scope_reconciliation.log": ("RAN2", "annex_scope_reconciliation.log"),
    "ran2_body_source_metadata_three_facts_before.json.gz": ("RAN2", "body_source_metadata_three_facts_before.json.gz"),
    "ran2_final_body_source_metadata_handoff_before_numeric_e2bda6d65757.json.gz": ("RAN2", "final_body_source_metadata_handoff_before_numeric_e2bda6d65757.json.gz"),
    "ran2_final_body_source_metadata_ledger_before.json.gz": ("RAN2", "final_body_source_metadata_ledger_before.json.gz"),
    "ran2_resolution_final_anchors.log": ("RAN2", "resolution_final_anchors.log"),
    "ran2_resolution_final_apply.log": ("RAN2", "resolution_final_apply.log"),
    "ran4_assigned_cr_receipt_preimage-8b7dea9a38880e7b.json.gz": ("RAN4", "assigned_cr_receipt_preimage-8b7dea9a38880e7b.json.gz"),
    "ran4_document_identity_initial1084_preimage.json.gz": ("RAN4", "document_identity_initial1084_preimage.json.gz"),
    "ran4_revision67_receipt_preimage-0538526d635a5dbe.json.gz": ("RAN4", "revision67_receipt_preimage-0538526d635a5dbe.json.gz"),
    "ran4_revision_receipt_preimage-9f1de61a1645c1d5.json.gz": ("RAN4", "revision_receipt_preimage-9f1de61a1645c1d5.json.gz"),
    "ran5_document_supplement_manifest_preimage.json.gz": ("RAN5", "document_supplement_manifest_preimage.json.gz"),
    "resolution_anchors_RAN4.log": ("RAN4", "resolution_anchors.log"),
    "resolution_document_anchors_RAN3.log": ("RAN3", "resolution_document_anchors.log"),
    "resolution_document_vectors_RAN3.log": ("RAN3", "resolution_document_vectors.log"),
    "resolution_document_vectors_RAN4.log": ("RAN4", "resolution_document_vectors.log"),
    "ts_release_integrity_RAN1.log": ("RAN1", "ts_release_integrity.log"),
    "ts_release_integrity_RAN2.log": ("RAN2", "ts_release_integrity.log"),
    "ts_release_integrity_RAN3.log": ("RAN3", "ts_release_integrity.log"),
    "ts_release_integrity_RAN4.log": ("RAN4", "ts_release_integrity.log"),
    "ts_release_integrity_RAN5.log": ("RAN5", "ts_release_integrity.log"),
    "ran2_annex_phase1_identity_reconciliation.canonical-preimage.jsonld.gz": ("RAN2", "annex_phase1_identity_reconciliation.canonical-preimage.jsonld.gz"),
    "ran3_assigned_source_class_reconciliation.canonical-preimage.jsonld.gz": ("RAN3", "assigned_source_class_reconciliation.canonical-preimage.jsonld.gz"),
    "ran3_source_identity_reconciliation.canonical-preimage.jsonld.gz": ("RAN3", "source_identity_reconciliation.canonical-preimage.jsonld.gz"),
    "ran4_additional_source_classification_reconciliation.canonical-preimage.jsonld.gz": ("RAN4", "additional_source_classification_reconciliation.canonical-preimage.jsonld.gz"),
    "ran4_remaining_source_classification_reconciliation.canonical-preimage.jsonld.gz": ("RAN4", "remaining_source_classification_reconciliation.canonical-preimage.jsonld.gz"),
    "ran4_source_classification_reconciliation.canonical-preimage.jsonld.gz": ("RAN4", "source_classification_reconciliation.canonical-preimage.jsonld.gz"),
    "ran4_source_revision_correction_reconciliation.canonical-preimage.jsonld.gz": ("RAN4", "source_revision_correction_reconciliation.canonical-preimage.jsonld.gz"),
    "ran5_assigned_source_class_reconciliation.canonical-preimage.jsonld.gz": ("RAN5", "assigned_source_class_reconciliation.canonical-preimage.jsonld.gz"),
    "ran5_native_document_reconciliation.canonical-preimage.jsonld.gz": ("RAN5", "native_document_reconciliation.canonical-preimage.jsonld.gz"),
    "ran5_phase1_source_reconciliation.canonical-preimage.jsonld.gz": ("RAN5", "phase1_source_reconciliation.canonical-preimage.jsonld.gz"),
    "liaison_reference_reconciliation_RAN2_e32e174bef2faf4d_apply.preimage.jsonld.gz": ("RAN2", "liaison_reference_reconciliation_e32e174bef2faf4d_apply.preimage.jsonld.gz"),
    "liaison_reference_reconciliation_RAN3_df808175ee34ce7e_apply.preimage.jsonld.gz": ("RAN3", "liaison_reference_reconciliation_df808175ee34ce7e_apply.preimage.jsonld.gz"),
    "liaison_reference_reconciliation_RAN5_ec3d4def6d24e02d_apply.preimage.jsonld.gz": ("RAN5", "liaison_reference_reconciliation_ec3d4def6d24e02d_apply.preimage.jsonld.gz"),
    "feature_grounding_transaction_RAN1_20261030T002548790407Z.json": ("RAN1", "feature_grounding_transaction_20261030T002548790407Z.json"),
    "feature_grounding_transaction_RAN1_20261030T011328232767Z.json": ("RAN1", "feature_grounding_transaction_20261030T011328232767Z.json"),
    "feature_grounding_transaction_RAN2_20261030T002548790407Z.json": ("RAN2", "feature_grounding_transaction_20261030T002548790407Z.json"),
    "feature_grounding_transaction_RAN2_20261030T002846024668Z.json": ("RAN2", "feature_grounding_transaction_20261030T002846024668Z.json"),
    "feature_grounding_transaction_RAN2_20261030T011328232767Z.json": ("RAN2", "feature_grounding_transaction_20261030T011328232767Z.json"),
    "feature_grounding_transaction_RAN3_20261030T002548790407Z.json": ("RAN3", "feature_grounding_transaction_20261030T002548790407Z.json"),
    "feature_grounding_transaction_RAN3_20261030T011328232767Z.json": ("RAN3", "feature_grounding_transaction_20261030T011328232767Z.json"),
    "feature_grounding_transaction_RAN4_20261030T002548790407Z.json": ("RAN4", "feature_grounding_transaction_20261030T002548790407Z.json"),
    "feature_grounding_transaction_RAN4_20261030T011328232767Z.json": ("RAN4", "feature_grounding_transaction_20261030T011328232767Z.json"),
    "feature_grounding_transaction_RAN5_20261030T002548790407Z.json": ("RAN5", "feature_grounding_transaction_20261030T002548790407Z.json"),
    "feature_grounding_transaction_RAN5_20261030T011328232767Z.json": ("RAN5", "feature_grounding_transaction_20261030T011328232767Z.json"),
    "token_metadata_preimage_ran2_ts_sections_20261030T004145.872692Z.json": ("RAN2", "token_metadata_preimage_ts_sections_20261030T004145.872692Z.json"),
    "token_metadata_preimage_ran5_ts_sections_20261030T004147.177857Z.json": ("RAN5", "token_metadata_preimage_ts_sections_20261030T004147.177857Z.json"),
    "token_metadata_preimage_ran5_ts_sections_p12_20261030T004147.517539Z.json": ("RAN5", "token_metadata_preimage_ts_sections_p12_20261030T004147.517539Z.json"),
    "ran2_annex_native_bulk_targets.json": ("RAN2", "annex_native_bulk_targets.json"),
    "ran4_additional_source_classification_targets.json": ("RAN4", "additional_source_classification_targets.json"),
    "ran4_all_additional_source_classification_targets.json": ("RAN4", "all_additional_source_classification_targets.json"),
    "ran4_remaining_source_classification_targets.json": ("RAN4", "remaining_source_classification_targets.json"),
    "ran2_all_indexed_cr_source_strict_xml_final.json": ("RAN2", "all_indexed_cr_source_strict_xml.json"),
    "ran2_annex_all_variant_strict_xml_census.json": ("RAN2", "annex_all_variant_strict_xml_census.json"),
    "ran2_annex_all_variant_strict_xml_final.json": ("RAN2", "annex_all_variant_strict_xml.json"),
    "ran2_annex_full_retained_cover_census.json": ("RAN2", "annex_full_retained_cover_census.json"),
    "ran2_annex_full_retained_cover_evidence.jsonl": ("RAN2", "annex_full_retained_cover_evidence.jsonl"),
    "ran2_annex_expanded_source_field_gate_check.json": ("RAN2", "annex_expanded_source_field_gate_check.json"),
    "ran2_annex_normal_identity_field_validation.json": ("RAN2", "annex_normal_identity_field_validation.json"),
    "ran2_final_cr_body_source_metadata_field_status.json": ("RAN2", "final_cr_body_source_metadata_field_status.json"),
    "ran2_final_cr_metadata_view_artifact_coverage.json": ("RAN2", "final_cr_metadata_view_artifact_coverage.json"),
    "ran4_revision_final_receipt_status.json": ("RAN4", "revision_final_receipt_status.json"),
    "ran4_revision_final_consumer_validation.json": ("RAN4", "revision_final_consumer_validation.json"),
    "ran4_revision_receipt_consumer_validation.json": ("RAN4", "revision_receipt_consumer_validation.json"),
    "ran2_annex_normal_field_gate_final.json": ("RAN2", "annex_normal_field_gate.json"),
    "ran4_cq_official_followup.json": ("RAN4", "cq_official_followup.json"),
    "ran5_native_document_reconciliation.log": ("RAN5", "native_document_reconciliation.log"),
    "ran5_phase1_source_prediction.json": ("RAN5", "phase1_source_prediction.json"),
    "ran5_phase1_source_review.md": ("RAN5", "phase1_source_review.md"),
    "asn1_identifier_semantics.json": ("RAN2", "asn1_identifier_semantics.json"),
    "ie_version_release_audit.json": ("RAN2", "ie_version_release_audit.json"),
    "mobility_concept_evidence.json": ("RAN2", "mobility_concept_evidence.json"),
    "tr38903_independent_target_dependency.json": ("RAN5", "tr38903_independent_target_dependency.json"),
    "tr_independent_additional_source_validation.json": ("RAN4", "tr_independent_additional_source_validation.json"),
    "tr_source_identity_official.json": ("RAN4", "tr_source_identity_official.json"),
    "tr_source_identity_reconciliation.json": ("RAN4", "tr_source_identity_reconciliation.json"),
    "tr_identity_verdict_reconciliation.json": ("RAN4", "tr_identity_verdict_reconciliation.json"),
    "vector_auxiliary_reference_reconciliation.json": ("RAN5", "vector_auxiliary_reference_reconciliation.json"),
    "vector_integrity_changed_final2.json": ("RAN4", "vector_integrity_changed.json"),
    "vector_integrity_changed_final2.log": ("RAN4", "vector_integrity_changed.log"),
    "vector_integrity_changed_final2_execution.json": ("RAN4", "vector_integrity_changed_execution.json"),
    "tsgran_topical_rdf_validation.json": ("TSG_RAN", "topical_rdf_validation.json"),
    "tsgran_topical_reconciliation.json": ("TSG_RAN", "topical_reconciliation.json"),
    "tsgran_topical_preimage_20261030T003807.510343Z.json": ("TSG_RAN", "topical_preimage_20261030T003807.510343Z.json"),
    "tdoc_document_vectors_plan.log": ("RAN5", "tdoc_document_vectors_plan.log"),
    "tdoc_supplement_vectors_plan.log": ("RAN5", "tdoc_supplement_vectors_plan.log"),
    "tdoc_supplement_vectors_apply.log": ("RAN5", "tdoc_supplement_vectors_apply.log"),
    "tdoc_supplement_source_parse.log": ("RAN5", "tdoc_supplement_source_parse.log"),
})


# 이 디렉토리에 등록되지 않은 다른 파일의 이동 경로는 추정하지 않습니다.
FILE_ONLY_PARENTS = frozenset(("cq_shortfall_followup/agenda_heading_census",))

# 파일별 WG와 경로가 등록되어 있으면 상위 디렉토리의 공통 설정보다 우선합니다.
NESTED_FILE_LAYOUT = MappingProxyType({
    "cq_shortfall_followup/agenda_heading_census/ran2_document_agenda_impact.json":
        ("RAN2", "cq-shortfall-followup/agenda-heading-census/document_agenda_impact.json"),
    "cq_shortfall_followup/agenda_heading_census/ran2_source_heading_census.json":
        ("RAN2", "cq-shortfall-followup/agenda-heading-census/source_heading_census.json"),
    "cq_shortfall_followup/agenda_heading_census/ran3_source_heading_census.json":
        ("RAN3", "cq-shortfall-followup/agenda-heading-census/source_heading_census.json"),
    "cq_shortfall_followup/agenda_heading_census/ran4_source_heading_census.json":
        ("RAN4", "cq-shortfall-followup/agenda-heading-census/source_heading_census.json"),
    "cq_shortfall_followup/agenda_heading_census/ran5_document_agenda_impact.json":
        ("RAN5", "cq-shortfall-followup/agenda-heading-census/document_agenda_impact.json"),
    "cq_shortfall_followup/agenda_heading_census/ran5_source_heading_census.json":
        ("RAN5", "cq-shortfall-followup/agenda-heading-census/source_heading_census.json"),
    "cq_shortfall_followup/agenda_heading_census/source_heading_review.json":
        (None, "cq-shortfall-followup/agenda-heading-census/source_heading_review.json"),
    "cq_shortfall_followup/capability_column_header_shadow.json":
        ("RAN2", "cq-shortfall-followup/capability_column_header_shadow.json"),
    "cq_shortfall_followup/capability_suffix_independent_review.json":
        ("RAN2", "cq-shortfall-followup/capability_suffix_independent_review.json"),
    "cq_shortfall_followup/docx_search_text_independent_review.json":
        ("RAN4", "cq-shortfall-followup/docx_search_text_independent_review.json"),
    "ran4_cq_official_sources/RP-171485 revised WID_NR_clean_v6.docx":
        ("RAN4", "cq-official-sources/RP-171485.docx"),
    "ran4_cq_official_sources/RP-171485 revised WID_NR_clean_v6.accepted.docx":
        ("RAN4", "cq-official-sources/RP-171485.accepted.docx"),
    "ran4_cq_official_sources/RP-171485 revised WID_NR_clean_v6.conversion.json":
        ("RAN4", "cq-official-sources/RP-171485.conversion.json"),
    "cq_shortfall_followup/ran1_agenda_guard_independent_review.json":
        ("RAN1", "cq-shortfall-followup/agenda_guard_independent_review.json"),
    "cq_shortfall_followup/ran1_registered_reported_owl_proof.json":
        ("RAN1", "cq-shortfall-followup/registered_reported_owl_proof.json"),
    "cq_shortfall_followup/ts_scientific_exponent_source_evidence.json":
        ("RAN1", "cq-shortfall-followup/ts_scientific_exponent_source_evidence.json"),
    "cq_shortfall_followup/ran1_fresh_agenda_closure_equivalence.json":
        ("RAN1", "cq-shortfall-followup/fresh_agenda_closure_equivalence.json"),
    "cq_shortfall_followup/ran1_authored_agenda_delta_decomposition.json":
        ("RAN1", "cq-shortfall-followup/authored_agenda_delta_decomposition.json"),
    "cq_shortfall_followup/ran1_agenda_preservation_readback.json":
        ("RAN1", "cq-shortfall-followup/agenda_preservation_readback.json"),
    "cq_shortfall_followup/ran1_agenda_header_contract.json":
        ("RAN1", "cq-shortfall-followup/agenda_header_contract.json"),
    "cq_shortfall_followup/agenda_heading_census/ran1_source_closure_independent_review.json":
        ("RAN1", "cq-shortfall-followup/agenda-heading-census/source_closure_independent_review.json"),
    "cq_shortfall_followup/capability_row_extent_independent_review.json":
        ("RAN2", "cq-shortfall-followup/capability_row_extent_independent_review.json"),
    "cq_shortfall_followup/capability_remaining_outliers_independent_review.json":
        ("RAN2", "cq-shortfall-followup/capability_remaining_outliers_independent_review.json"),
    "cq_shortfall_followup/capability_consumer_identity_review.json":
        ("RAN2", "cq-shortfall-followup/capability_consumer_identity_review.json"),
    "cq_shortfall_followup/capability_suffix_body_coverage_review.json":
        ("RAN2", "cq-shortfall-followup/capability_suffix_body_coverage_review.json"),
    "cq_shortfall_followup/agenda_heading_census/additional_source_heading_review.json":
        (None, "cq-shortfall-followup/agenda-heading-census/additional_source_heading_review.json"),
    "cq_shortfall_followup/cr_section_wrong_topic_independent_review.json":
        ("RAN5", "cq-shortfall-followup/cr_section_wrong_topic_independent_review.json"),
    "cq_shortfall_followup/ts_fused_clause_source_evidence.json":
        ("RAN5", "cq-shortfall-followup/ts_fused_clause_source_evidence.json"),
    "cq_shortfall_followup/capability_polluted_row_coverage_plan.json":
        ("RAN2", "cq-shortfall-followup/capability_polluted_row_coverage_plan.json"),
    "cq_shortfall_followup/ran2_cr_2002409_wrong_topic_independent_review.json":
        ("RAN2", "cq-shortfall-followup/cr_2002409_wrong_topic_independent_review.json"),
    "cq_shortfall_followup/capability_physical_row_identity_review.json":
        ("RAN2", "cq-shortfall-followup/capability_physical_row_identity_review.json"),
    "cq_shortfall_followup/caption_search_role_runtime_review.json":
        ("RAN4", "cq-shortfall-followup/caption_search_role_runtime_review.json"),
    "cq_shortfall_followup/external_ls_reference_followup.json":
        ("RAN4", "cq-shortfall-followup/external_ls_reference_followup.json"),
    "cq_shortfall_followup/ts_recovered_source_fragment_renderer_validation.json":
        ("RAN5", "cq-shortfall-followup/ts_recovered_source_fragment_renderer_validation.json"),
    "cq_shortfall_followup/ts_p12_single_sentence_source_evidence.json":
        ("RAN5", "cq-shortfall-followup/ts_p12_single_sentence_source_evidence.json"),
    "cq_shortfall_followup/ts_search_renderer_shadow_RAN4_38.101-5_Rel-19.json":
        ("RAN4", "cq-shortfall-followup/ts_search_renderer_shadow_38.101-5_Rel-19.json"),
    "cq_shortfall_followup/review_tool_ran3_roundtrip_counterexample.json":
        ("RAN3", "cq-shortfall-followup/review_tool_roundtrip_counterexample.json"),
    "cq_shortfall_followup/ran1_role_agenda_source_adjudication.json":
        ("RAN1", "cq-shortfall-followup/role_agenda_source_adjudication.json"),
    "cq_shortfall_followup/ts_fused_clause_independent_review.json":
        ("RAN5", "cq-shortfall-followup/ts_fused_clause_independent_review.json"),
    "cq_shortfall_followup/ran3_revision_inverse_source_review.json":
        ("RAN3", "cq-shortfall-followup/revision_inverse_source_review.json"),
    "cq_shortfall_followup/ran3_revision_inverse_semantic_review.json":
        ("RAN3", "cq-shortfall-followup/revision_inverse_semantic_review.json"),
    "cq_shortfall_followup/docx_search_fragment_independent_review.json":
        ("RAN5", "cq-shortfall-followup/docx_search_fragment_independent_review.json"),
    "cq_shortfall_followup/capability_full_physical_row_coverage.json":
        ("RAN2", "cq-shortfall-followup/capability_full_physical_row_coverage.json"),
    "cq_shortfall_followup/capability_full_physical_row_coverage.json.gz":
        ("RAN2", "cq-shortfall-followup/capability_full_physical_row_coverage.json.gz"),
    "cq_shortfall_followup/capability_physical_row_owner_bindings.json":
        ("RAN2", "cq-shortfall-followup/capability_physical_row_owner_bindings.json"),
    "cq_shortfall_followup/capability_physical_row_owner_bindings.json.gz":
        ("RAN2", "cq-shortfall-followup/capability_physical_row_owner_bindings.json.gz"),
    "cq_shortfall_followup/capability_native_row_source_contract.json":
        ("RAN2", "cq-shortfall-followup/capability_native_row_source_contract.json"),
    "cq_shortfall_followup/capability_native_row_repair_proposal.json":
        ("RAN2", "cq-shortfall-followup/capability_native_row_repair_proposal.json"),
    "cq_shortfall_followup/capability_native_row_repair_proposal.json.gz":
        ("RAN2", "cq-shortfall-followup/capability_native_row_repair_proposal.json.gz"),
    "cq_shortfall_followup/capability_source_row_consumer_design_review.json":
        ("RAN2", "cq-shortfall-followup/capability_source_row_consumer_design_review.json"),
    "cq_shortfall_followup/ts_caption_release_convergence_independent_review.json":
        ("RAN4", "cq-shortfall-followup/ts_caption_release_convergence_independent_review.json"),

    "cq_shortfall_followup/ran5_fused_section_hierarchy_repair_plan.json":
        ("RAN5", "cq-shortfall-followup/fused_section_hierarchy_repair_plan.json"),
    "cq_shortfall_followup/ran5_fused_section_phase3_runtime_review.json":
        ("RAN5", "cq-shortfall-followup/fused_section_phase3_runtime_review.json"),
    "cq_shortfall_followup/ran5_fused_section_structural_closure_review.json":
        ("RAN5", "cq-shortfall-followup/fused_section_structural_closure_review.json"),
    "cq_shortfall_followup/ts_fused_clause_section_live_preflight.json":
        ("RAN5", "cq-shortfall-followup/ts_fused_clause_section_live_preflight.json"),
    "cq_shortfall_followup/ts_p12_single_sentence_repair_proposal.json":
        ("RAN5", "cq-shortfall-followup/ts_p12_single_sentence_repair_proposal.json"),
    "cq_shortfall_followup/ts_caption_branch_overlap_independent_review.json":
        ("RAN4", "cq-shortfall-followup/ts_caption_branch_overlap_independent_review.json"),
    "cq_shortfall_followup/non_ts_purpose_family_script_role_followup.json":
        ("RAN5", "cq-shortfall-followup/non_ts_purpose_family_script_role_followup.json"),
    "cq_shortfall_followup/ts_search_source_fence_final.json":
        (None, "cq-shortfall-followup/ts_search_source_fence.json"),
    "cq_shortfall_followup/ts_p12_single_sentence_independent_review.json":
        ("RAN5", "cq-shortfall-followup/ts_p12_single_sentence_independent_review.json"),
    "cq_shortfall_followup/tr_self_reference_semantic_review.json":
        ("RAN4", "cq-shortfall-followup/tr_self_reference_semantic_review.json"),
    "cq_shortfall_followup/ran5_native142_numeric_preflight.json":
        ("RAN5", "cq-shortfall-followup/native142_numeric_preflight.json"),
    "cq_shortfall_followup/vector_numeric_ran5_tdoc_current.json":
        ("RAN5", "cq-shortfall-followup/vector_numeric_tdoc_current.json"),
})

_DIRECTORY_LAYOUT_OVERRIDES = {
    "recovered_ts_sections": ("RAN5", "recovered-ts-sections"),
    "recovered_ts_sections/preimage": ("RAN5", "recovered-ts-sections/preimage"),
    'word_conversion_recovery': ("RAN2", 'word-conversion-recovery'),
    'word_conversion_recovery/accepted': ("RAN2", 'word-conversion-recovery/accepted'),
    'word_conversion_recovery/preimages': ("RAN2", 'word-conversion-recovery/preimages'),
    'word_conversion_recovery_followup': ("RAN2", 'word-conversion-recovery-followup'),
    'word_conversion_recovery_followup/accepted': ("RAN2", 'word-conversion-recovery-followup/accepted'),
    'word_conversion_recovery_followup/accepted/0e2c218399f85072': ("RAN2", 'word-conversion-recovery-followup/accepted/0e2c218399f85072'),
    'word_conversion_recovery_followup/accepted/be00c7b32149b8bc': ("RAN2", 'word-conversion-recovery-followup/accepted/be00c7b32149b8bc'),
    'word_conversion_recovery_followup/accepted/eda74313022ee05e': ("RAN2", 'word-conversion-recovery-followup/accepted/eda74313022ee05e'),
    'word_conversion_recovery_followup/minimal_xml': ("RAN2", 'word-conversion-recovery-followup/minimal-xml'),
    'word_conversion_recovery_followup/minimal_xml/0e2c218399f85072': ("RAN2", 'word-conversion-recovery-followup/minimal-xml/0e2c218399f85072'),
    'word_conversion_recovery_followup/minimal_xml/12cbcf298232e35c': ("RAN2", 'word-conversion-recovery-followup/minimal-xml/12cbcf298232e35c'),
    'word_conversion_recovery_followup/minimal_xml/1ca0dc44c074b922': ("RAN2", 'word-conversion-recovery-followup/minimal-xml/1ca0dc44c074b922'),
    'word_conversion_recovery_followup/minimal_xml/2c22b101ad8a4246': ("RAN2", 'word-conversion-recovery-followup/minimal-xml/2c22b101ad8a4246'),
    'word_conversion_recovery_followup/minimal_xml/be00c7b32149b8bc': ("RAN2", 'word-conversion-recovery-followup/minimal-xml/be00c7b32149b8bc'),
    'word_conversion_recovery_followup/minimal_xml/eda74313022ee05e': ("RAN2", 'word-conversion-recovery-followup/minimal-xml/eda74313022ee05e'),
    'word_conversion_recovery_followup/preimages': ("RAN2", 'word-conversion-recovery-followup/preimages'),
    'word_conversion_recovery_indexed': ("RAN2", 'word-conversion-recovery-indexed'),
    'word_conversion_recovery_indexed/0cccad92422f3f88': ("RAN2", 'word-conversion-recovery-indexed/0cccad92422f3f88'),
    'word_conversion_recovery_indexed/219f5ca1a7908a76': ("RAN2", 'word-conversion-recovery-indexed/219f5ca1a7908a76'),
    'word_conversion_recovery_indexed/641e174b9a92b345': ("RAN2", 'word-conversion-recovery-indexed/641e174b9a92b345'),
    'word_conversion_recovery_indexed/77f8fe1521f6711a': ("RAN2", 'word-conversion-recovery-indexed/77f8fe1521f6711a'),
    'word_conversion_recovery_indexed/preimages': ("RAN2", 'word-conversion-recovery-indexed/preimages'),
    "cq_shortfall_followup/ran4_861_proposal": ("RAN4", "cq-shortfall-followup/861-proposal"),
    "cq_shortfall_followup/ran4_primary_sources": ("RAN4", "cq-shortfall-followup/primary-sources"),
    "cq_shortfall_followup/ran1_agenda_reconciliation":
        ("RAN1", "cq-shortfall-followup/agenda-reconciliation"),
    "cq_shortfall_followup/ran1_agenda_reconciliation/preimages":
        ("RAN1", "cq-shortfall-followup/agenda-reconciliation/preimages"),
    "cq_shortfall_followup/ran1_agenda_live_reconciliation":
        ("RAN1", "cq-shortfall-followup/agenda-live-reconciliation"),
    "cq_shortfall_followup/ran1_decision_disposition_reconciliation":
        ("RAN1", "cq-shortfall-followup/decision-disposition-reconciliation"),
}


# 공유 경로로 기록된 WG 전용 파일은 등록된 현재 WG 경로로 연결합니다.
RECORDED_FILE_RELOCATIONS = MappingProxyType({
    **{
        str(REVIEW_ROOT / "cq-shortfall-followup" / name):
            (axis.tree_path("logs_common", wg="RAN5", root=Path("."))
             / "verification" / "ontology-system-review" / "cq-shortfall-followup" / name).as_posix()
        for name in (
            'cr_tracked_script_presentation_scope_review.json',
            'native_pptx_two_point_repair_proposal.json',
            'native_pptx_search_presentation_shadow.json',
            'native_pptx_search_representation_readback.json.gz',
            'native_pptx_repair_artifact.before.json.gz',
            'native_pptx_shadow_source_independent_review.json',
            'native_pptx_search_representation_review.json',
            'native_pptx_style_math_independent_census.json',
        )
    },
    "logs/common/RAN1/verification/ontology-system-review/cq-shortfall-followup/agenda_current_readonly_20261031/source_generation.json":
        "logs/common/RAN1/verification/ontology-system-review/cq-shortfall-followup/agenda-current-readonly-20261031/source_generation.json",
    "logs/common/RAN1/verification/ontology-system-review/cq-shortfall-followup/agenda_current_readonly_20261031/status.json":
        "logs/common/RAN1/verification/ontology-system-review/cq-shortfall-followup/agenda-current-readonly-20261031/status.json",
    "logs/common/RAN1/verification/ontology-system-review/cq-shortfall-followup/agenda_current_readonly_20261031/live_preimage.json.gz":
        "logs/common/RAN1/verification/ontology-system-review/cq-shortfall-followup/agenda-current-readonly-20261031/live_preimage.json.gz",
    "logs/common/RAN2/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_applied/result.json":
        "logs/common/RAN2/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-applied/result.json",
    "logs/common/RAN2/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_applied/plan.json":
        "logs/common/RAN2/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-applied/plan.json",
    "logs/common/RAN2/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_applied/tdocs.before.jsonld.gz":
        "logs/common/RAN2/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-applied/tdocs.before.jsonld.gz",
    "logs/common/RAN2/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_applied/progress.json":
        "logs/common/RAN2/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-applied/progress.json",
    "logs/common/RAN2/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_preflight/plan.json":
        "logs/common/RAN2/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-preflight/plan.json",
    "logs/common/RAN3/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_applied/result.json":
        "logs/common/RAN3/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-applied/result.json",
    "logs/common/RAN3/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_applied/plan.json":
        "logs/common/RAN3/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-applied/plan.json",
    "logs/common/RAN3/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_applied/tdocs.before.jsonld.gz":
        "logs/common/RAN3/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-applied/tdocs.before.jsonld.gz",
    "logs/common/RAN3/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_applied/progress.json":
        "logs/common/RAN3/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-applied/progress.json",
    "logs/common/RAN3/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_preflight/plan.json":
        "logs/common/RAN3/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-preflight/plan.json",
    "logs/common/RAN3/verification/ontology-system-review/cq-shortfall-followup/revision_native_source_163112/conversion.json":
        "logs/common/RAN3/verification/ontology-system-review/cq-shortfall-followup/revision-native-source-163112/conversion.json",
    "logs/common/RAN3/verification/ontology-system-review/cq-shortfall-followup/revision_native_source_163112/accepted.docx":
        "logs/common/RAN3/verification/ontology-system-review/cq-shortfall-followup/revision-native-source-163112/accepted.docx",
    "logs/common/RAN4/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_applied/result.json":
        "logs/common/RAN4/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-applied/result.json",
    "logs/common/RAN4/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_applied/plan.json":
        "logs/common/RAN4/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-applied/plan.json",
    "logs/common/RAN4/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_applied/tdocs.before.jsonld.gz":
        "logs/common/RAN4/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-applied/tdocs.before.jsonld.gz",
    "logs/common/RAN4/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_applied/progress.json":
        "logs/common/RAN4/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-applied/progress.json",
    "logs/common/RAN4/verification/ontology-system-review/cq-shortfall-followup/revision_immediate_qualification_preflight/plan.json":
        "logs/common/RAN4/verification/ontology-system-review/cq-shortfall-followup/revision-immediate-qualification-preflight/plan.json",
    "logs/common/RAN5/verification/ontology-system-review/cq-shortfall-followup/fused_section_hierarchy_reconciliation/result.json":
        "logs/common/RAN5/verification/ontology-system-review/cq-shortfall-followup/fused-section-hierarchy-reconciliation/result.json",
    "logs/common/RAN5/verification/ontology-system-review/cq-shortfall-followup/fused_section_hierarchy_reconciliation/plan.json":
        "logs/common/RAN5/verification/ontology-system-review/cq-shortfall-followup/fused-section-hierarchy-reconciliation/plan.json",
    "logs/common/RAN5/verification/ontology-system-review/cq-shortfall-followup/fused_section_hierarchy_reconciliation/parsed.before.json.gz":
        "logs/common/RAN5/verification/ontology-system-review/cq-shortfall-followup/fused-section-hierarchy-reconciliation/parsed.before.json.gz",
    "logs/common/verification/ontology-system-review/cq-shortfall-followup/tr_bibliographic_referent_reconciliation/result.json":
        "logs/common/verification/ontology-system-review/cq-shortfall-followup/tr-bibliographic-referent-reconciliation/result.json",
    "logs/common/verification/ontology-system-review/cq-shortfall-followup/tr_bibliographic_referent_reconciliation/RAN4_tr_documents.json.before.gz":
        "logs/common/verification/ontology-system-review/cq-shortfall-followup/tr-bibliographic-referent-reconciliation/RAN4_tr_documents.json.before.gz",
    "logs/common/verification/ontology-system-review/cq-shortfall-followup/tr_bibliographic_referent_reconciliation/plan.json":
        "logs/common/verification/ontology-system-review/cq-shortfall-followup/tr-bibliographic-referent-reconciliation/plan.json",
    "logs/common/verification/ontology-system-review/cq-shortfall-followup/tr_bibliographic_referent_reconciliation/RAN4_tr_ontology.jsonld.before.gz":
        "logs/common/verification/ontology-system-review/cq-shortfall-followup/tr-bibliographic-referent-reconciliation/RAN4_tr_ontology.jsonld.before.gz",
    "logs/common/RAN3/verification/ontology-system-review/retained-docx-repair/R3-163112/R3-163112_v04.docx":
        "logs/common/RAN3/verification/ontology-system-review/retained-docx-repair/R3-163112/repaired_candidate.docx",
    "logs/common/RAN2/verification/ontology-system-review/capability-source-row-repair/20261030T222516Z/vector_numeric_final.json":
        "logs/common/RAN2/verification/ontology-system-review/capability-source-row-repair/20261030T222516Z/vector_numeric_validation.json",
    "logs/common/RAN2/verification/ontology-system-review/capability-source-row-repair/20261030T222516Z/verify_final.py":
        "logs/common/RAN2/verification/ontology-system-review/capability-source-row-repair/20261030T222516Z/verify_source_readback.py",
})

def _legacy_directory_layout(parent):
    """등록된 과거 디렉토리명에서 WG와 현재 실행 경로를 구합니다."""
    if parent in _DIRECTORY_LAYOUT_OVERRIDES:
        return _DIRECTORY_LAYOUT_OVERRIDES[parent]
    parts = parent.split("/")
    if parts[0] in {"resolution_vectors", "tdoc_source_vectors"} and len(parts) > 1:
        stamp, marker, identity = parts[1].partition("Z_")
        wg = identity.removesuffix("_anchors")
        if marker and wg in axis.WG_REGISTRY:
            run_name = stamp + "Z" + ("-anchors" if identity.endswith("_anchors") else "")
            return wg, "/".join([parts[0].replace("_", "-"), run_name,
                                 *[part.replace("_", "-") for part in parts[2:]]])
    for wg in axis.WG_REGISTRY:
        prefix = "body_source_metadata_" + wg
        if parts[0] == prefix or parts[0].startswith(prefix + "_"):
            suffix = parts[0][len(prefix):].strip("_")
            role = "body-source-metadata" + ("-" + suffix.replace("_", "-") if suffix else "")
            return wg, "/".join([role, *[part.replace("_", "-") for part in parts[1:]]])
        prefix = wg.lower() + "_"
        if parts[0].startswith(prefix):
            return wg, "/".join([parts[0][len(prefix):].replace("_", "-"),
                                 *[part.replace("_", "-") for part in parts[1:]]])
    return None, parent.replace("_", "-")


_DIRECTORY_LAYOUT = {old: _legacy_directory_layout(old) for old in _LEGACY_DIRECTORIES}
DIRECTORY_RENAMES = MappingProxyType({old: layout[1] for old, layout in _DIRECTORY_LAYOUT.items()})
DIRECTORY_WORKGROUPS = MappingProxyType({old: layout[0] for old, layout in _DIRECTORY_LAYOUT.items()})


def _relative(value):
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise ValueError("canonical repository-relative path required")
    if re.match(r"^[A-Za-z]:", value):
        raise ValueError("repository-relative path required")
    relative = PurePosixPath(value)
    if (relative.is_absolute() or any(part in {".", ".."} for part in value.split("/"))
            or str(relative) != value):
        raise ValueError("canonical repository-relative path required")
    return relative


def _validate_layout(directories, receipts, workgroups=None, root_files=None, nested_files=None,
                     file_only_parents=()):
    workgroups = workgroups or {}
    if len({(workgroups.get(old), new) for old, new in directories.items()}) != len(directories):
        raise ValueError("legacy directory relocation collision")
    if len(set(receipts.values())) != len(receipts):
        raise ValueError("legacy receipt relocation collision")
    if set(receipts) & set(receipts.values()):
        raise ValueError("legacy receipt names overlap current receipt names")
    root_files = root_files or {}
    for parent in file_only_parents:
        _relative(parent)
        if parent in directories:
            raise ValueError("mixed artifact parent must not have a directory fallback")
    targets = []
    for old, (wg, name) in root_files.items():
        for component in (old, name):
            if (not isinstance(component, str) or component in {"", ".", ".."}
                    or any(mark in component for mark in ("/", "\\", "\x00"))):
                raise ValueError("root artifact basename required")
        if wg is not None and wg not in axis.WG_REGISTRY:
            raise ValueError("declared root artifact workgroup required")
        targets.append((wg, PurePosixPath(name)))
    for old, (wg, name) in (nested_files or {}).items():
        old_path, target_path = _relative(old), _relative(name)
        if len(old_path.parts) < 2 or len(target_path.parts) < 2:
            raise ValueError("nested artifact coordinate required")
        if wg is not None and wg not in axis.WG_REGISTRY:
            raise ValueError("declared nested artifact workgroup required")
        targets.append((wg, target_path))
    if len(targets) != len(set(targets)):
        raise ValueError("legacy artifact relocation collision")
    directory_targets = {(workgroups.get(old), PurePosixPath(new))
                         for old, new in directories.items()}
    for wg, path in targets:
        if any(group == wg and directory.is_relative_to(path)
               for group, directory in directory_targets):
            raise ValueError("legacy file and directory relocation collision")
        if any(group == wg and other != path and other.is_relative_to(path)
               for group, other in targets):
            raise ValueError("legacy artifact ancestor relocation collision")


_validate_layout(DIRECTORY_RENAMES, RECEIPT_RENAMES, DIRECTORY_WORKGROUPS,
                 ROOT_FILE_LAYOUT, NESTED_FILE_LAYOUT, FILE_ONLY_PARENTS)


def _without_symlinks(path):
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError("recorded path crosses a symlink boundary")


def _root(root):
    root = Path(root).absolute()
    _without_symlinks(root)
    if not root.is_dir():
        raise ValueError("repository root must be an existing directory")
    return root


def _workgroup(wg):
    if (not isinstance(wg, str)
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*", wg)
            or wg not in axis.WG_REGISTRY
            or axis.tsg_of(wg) not in axis.TSG_REGISTRY):
        raise ValueError("declared workgroup identity required")
    return wg


def review_root(root, wg=None):
    """공유 또는 WG 전용 검수 디렉토리 경로를 반환합니다. 디렉토리는 생성하지 않습니다."""
    root = _root(root)
    path = (root.joinpath(*REVIEW_ROOT.parts) if wg is None else
            axis.tree_path("logs_common", wg=_workgroup(wg), root=root)
            / "verification" / "ontology-system-review")
    _without_symlinks(path)
    return path


def review_role(root, role, wg=None):
    """새 실행에 사용할 역할 디렉토리를 구성합니다."""
    if not isinstance(role, str) or not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", role):
        raise ValueError("kebab-case review role required")
    path = review_root(root, wg) / role
    _without_symlinks(path)
    return path


def review_run_name(stamp, wg=None, *, variant=None):
    """UTC 시각과 선택한 WG·변형 이름으로 실행 디렉토리명을 구성합니다."""
    if (not isinstance(stamp, str)
            or not re.fullmatch(r"\d{8}T\d{6}\.\d{6}Z", stamp)):
        raise ValueError("UTC run stamp required")
    try:
        datetime.strptime(stamp, "%Y%m%dT%H%M%S.%fZ")
    except ValueError as exc:
        raise ValueError("valid UTC run stamp required") from exc
    pieces = [stamp]
    if wg is not None:
        pieces.append(_workgroup(wg).replace("_", "-"))
    if variant is not None:
        if not isinstance(variant, str) or not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", variant):
            raise ValueError("kebab-case run variant required")
        pieces.append(variant)
    return "-".join(pieces)


def review_run(root, role, stamp, wg=None, *, variant=None):
    """WG별 작업 경로 아래에 UTC 시각과 변형 이름을 반영한 실행 경로를 반환합니다."""
    path = review_role(root, role, wg) / review_run_name(stamp, variant=variant)
    _without_symlinks(path)
    return path


def relocated_coordinate(recorded_path):
    """등록된 옛 경로를 현재 경로로 변환합니다. 파일을 열거나 생성하지 않습니다."""
    relative = _relative(recorded_path)
    if recorded_path in RECORDED_FILE_RELOCATIONS:
        return _relative(RECORDED_FILE_RELOCATIONS[recorded_path])
    if not relative.is_relative_to(LEGACY_REVIEW_ROOT):
        return relative
    suffix = relative.relative_to(LEGACY_REVIEW_ROOT)
    if not suffix.parts:
        raise ValueError("recorded artifact file required")
    parent = str(suffix.parent)
    parent = "" if parent == "." else parent
    if str(suffix) in NESTED_FILE_LAYOUT:
        wg, name = NESTED_FILE_LAYOUT[str(suffix)]
        base = (REVIEW_ROOT if wg is None else PurePosixPath(
            axis.tree_path("logs_common", wg=wg, root=Path(".")).as_posix())
            / "verification" / "ontology-system-review")
        return base / name
    if parent not in DIRECTORY_RENAMES:
        raise ValueError("unknown legacy review directory")
    target_parent = DIRECTORY_RENAMES[parent]
    wg = DIRECTORY_WORKGROUPS[parent]
    name = suffix.name
    if not parent and name in ROOT_FILE_LAYOUT:
        wg, name = ROOT_FILE_LAYOUT[name]
    base = (REVIEW_ROOT if wg is None else PurePosixPath(
        axis.tree_path("logs_common", wg=wg, root=Path(".")).as_posix())
        / "verification" / "ontology-system-review")
    return base / target_parent / name


def current_review_input(root, relative_name, *, wg=None):
    """현재 입력의 이관 전후 주소를 선택합니다. 과거 바이트 증명은 하지 않습니다.

    이 함수는 현재 경로와 이관 목록에 등록된 옛 경로 중 하나를 선택합니다.
    두 경로에 파일이 함께 있으면 거절합니다. SHA256 대조는 resolve_recorded_path가 수행합니다.
    양쪽 모두 없으면 현재 주소를 반환하여 기존 선택 입력의 존재 검사와 필수
    입력의 일반적인 읽기 실패를 유지합니다. 파일이나 디렉토리는 생성하지 않습니다.
    """
    relative = _relative(relative_name)
    parent = str(relative.parent)
    parent = "" if parent == "." else parent
    if not parent and relative.name in ROOT_FILE_LAYOUT:
        if ROOT_FILE_LAYOUT[relative.name] != (wg, relative.name):
            raise ValueError("current artifact coordinate required instead of legacy alias")
    if str(relative) in NESTED_FILE_LAYOUT:
        if NESTED_FILE_LAYOUT[str(relative)] != (wg, str(relative)):
            raise ValueError("current artifact coordinate required instead of legacy alias")
    root = _root(root)
    current = review_root(root, wg).joinpath(*relative.parts)
    original = None
    reverse_directories = {(DIRECTORY_WORKGROUPS[old], new): old
                           for old, new in DIRECTORY_RENAMES.items()}
    reverse_files = {new: old for old, new in ROOT_FILE_LAYOUT.items()}
    reverse_nested = {new: old for old, new in NESTED_FILE_LAYOUT.items()}
    if (wg, str(relative)) in reverse_nested:
        original = root.joinpath(*LEGACY_REVIEW_ROOT.parts, reverse_nested[wg, str(relative)])
    elif not parent and (wg, relative.name) in reverse_files:
        original = root.joinpath(*LEGACY_REVIEW_ROOT.parts, reverse_files[wg, relative.name])
    elif (wg, parent) in reverse_directories:
        old_parent = reverse_directories[wg, parent]
        old_suffix = str(PurePosixPath(old_parent) / relative.name)
        if (old_suffix in NESTED_FILE_LAYOUT
                and NESTED_FILE_LAYOUT[old_suffix] != (wg, str(relative))):
            raise ValueError("current artifact scope and coordinate must match its exact declaration")
        original = root.joinpath(*LEGACY_REVIEW_ROOT.parts, old_suffix)
    for path in (current, original):
        if path is not None:
            _without_symlinks(path)
    current_exists = os.path.lexists(current)
    original_exists = original is not None and os.path.lexists(original)
    if current_exists and original_exists:
        raise ValueError("ambiguous old and current input coordinates")
    selected = original if original_exists else current
    if os.path.lexists(selected) and not stat.S_ISREG(selected.lstat().st_mode):
        raise ValueError("current input must be a regular file")
    return selected


def _verified_file(path, expected_sha256, expected_bytes):
    _without_symlinks(path)
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("recorded artifact must be a regular file")
    # A path may change to a FIFO after lstat. Open without blocking so fstat
    # can reject that replacement; regular-file reads retain their usual behavior.
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("recorded artifact must be a regular file")
        digest = hashlib.sha256()
        size = 0
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
        after = os.fstat(descriptor)
        _without_symlinks(path)
        named = path.lstat()
        identity = lambda value: (
            value.st_dev, value.st_ino, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns,
        )
        if identity(before) != identity(after) or identity(after) != identity(named):
            raise ValueError("recorded artifact changed while reading")
        if digest.hexdigest() != expected_sha256:
            raise ValueError("recorded artifact SHA256 mismatch")
        if expected_bytes is not None and size != expected_bytes:
            raise ValueError("recorded artifact byte count mismatch")
    finally:
        os.close(descriptor)
    return path


def resolve_recorded_path(root, recorded_path, expected_sha256, *, expected_bytes=None):
    """원래 또는 이관된 동일 바이트 파일을 찾습니다. 실행 재개를 허가하지 않습니다.

    옛 주소와 새 주소가 함께 존재하면 어느 쪽도 선택하지 않습니다. 기존 주소의
    변조를 다른 사본으로 회피하지 않으며, 등록되지 않은 옛 디렉토리는 이동 경로를
    추정하지 않습니다. 현재 코드 등 일반 파일은 기록된 경로에서 그대로 검증합니다.
    반환값은 이 함수가 읽은 시점의 바이트 검증 결과입니다. 이후 경로를 다시 여는
    호출까지 원자적으로 묶지 않으며, 실행/재개 계약은 호출자가 따로 검증합니다.
    """
    relative = _relative(recorded_path)
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_sha256):
        raise ValueError("lowercase SHA256 binding required")
    if expected_bytes is not None and (type(expected_bytes) is not int or expected_bytes < 0):
        raise ValueError("nonnegative integer byte count required")
    root = _root(root)
    original = root.joinpath(*relative.parts)
    _without_symlinks(original)
    try:
        relocated = relocated_coordinate(recorded_path)
    except ValueError:
        if os.path.lexists(original):
            return _verified_file(original, expected_sha256, expected_bytes)
        raise
    target = root.joinpath(*relocated.parts)
    _without_symlinks(target)
    original_exists = os.path.lexists(original)
    target_exists = os.path.lexists(target)
    if original != target and original_exists and target_exists:
        raise ValueError("ambiguous old and relocated artifact coordinates")
    selected = original if original_exists else target
    if not os.path.lexists(selected):
        raise FileNotFoundError("bound recorded artifact is absent")
    return _verified_file(selected, expected_sha256, expected_bytes)
