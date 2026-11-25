"""보존된 파일의 이관 경로와 새 실행 경로를 검증합니다.

Spec: docs/common/standards/naming_conventions.md §7.4·§7.5.
임시 디렉토리에 원본과 이관 사본을 만들고 경로·SHA256·크기를 대조합니다.
LLM 호출: 0건. 실제 프로젝트 자료는 변경하지 않습니다.
"""

from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import axis
from common.review_artifacts import (
    DIRECTORY_RENAMES, DIRECTORY_WORKGROUPS, LEGACY_REVIEW_ROOT, RECEIPT_RENAMES, REVIEW_ROOT,
    FILE_ONLY_PARENTS, NESTED_FILE_LAYOUT, ROOT_FILE_LAYOUT, RECORDED_FILE_RELOCATIONS,
    _validate_layout, current_review_input, relocated_coordinate, resolve_recorded_path,
    review_role, review_root, review_run, review_run_name,
)


_SHARED_RAN5_RECEIPTS = ('cr_tracked_script_presentation_scope_review.json', 'native_pptx_two_point_repair_proposal.json', 'native_pptx_search_presentation_shadow.json', 'native_pptx_search_representation_readback.json.gz', 'native_pptx_repair_artifact.before.json.gz', 'native_pptx_shadow_source_independent_review.json', 'native_pptx_search_representation_review.json', 'native_pptx_style_math_independent_census.json')


class RecordedArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.raw = b'{"state":"complete","observed":7}\n'
        self.digest = hashlib.sha256(self.raw).hexdigest()

    def write(self, relative, raw=None):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.raw if raw is None else raw)
        return path

    def original(self, suffix="feature_source_population.json"):
        return str(LEGACY_REVIEW_ROOT / suffix)

    def moved(self, suffix="feature_source_population.json", wg=None):
        base = REVIEW_ROOT if wg is None else Path("logs/common") / wg / "verification/ontology-system-review"
        return str(base / suffix)

    def test_original_identity_is_verified_before_any_move(self):
        recorded = self.original()
        path = self.write(recorded)
        self.assertEqual(resolve_recorded_path(self.root, recorded, self.digest,
                                              expected_bytes=len(self.raw)), path)
        self.assertEqual(path.read_bytes(), self.raw)

    def test_approved_run_is_resolved_with_stamp_and_workgroup_preserved(self):
        recorded = self.original("resolution_vectors/20261030T030727.389362Z_RAN3/status.json")
        expected = self.moved("resolution-vectors/20261030T030727.389362Z/status.json", "RAN3")
        self.assertEqual(str(relocated_coordinate(recorded)), expected)
        path = self.write(expected)
        self.assertEqual(resolve_recorded_path(self.root, recorded, self.digest), path)

    def test_approved_nested_conversion_parent_is_resolved(self):
        recorded = self.original(
            "word_conversion_recovery_followup/minimal_xml/eda74313022ee05e/accepted.docx")
        expected = self.moved(
            "word-conversion-recovery-followup/minimal-xml/eda74313022ee05e/accepted.docx", "RAN2")
        path = self.write(expected)
        self.assertEqual(resolve_recorded_path(self.root, recorded, self.digest), path)

    def test_every_declared_directory_has_one_injective_current_coordinate(self):
        targets = []
        for old, new in DIRECTORY_RENAMES.items():
            with self.subTest(old=old):
                coordinate = relocated_coordinate(str(LEGACY_REVIEW_ROOT / old / "artifact.json"))
                self.assertEqual(str(coordinate), self.moved(new + "/artifact.json" if new else "artifact.json",
                                                           DIRECTORY_WORKGROUPS[old]))
                targets.append(str(coordinate))
        self.assertEqual(len(targets), len(set(targets)))

    def test_declared_runs_keep_identity_in_wg_slot_and_stamp_variant_only_leaf(self):
        targets = []
        for old in DIRECTORY_RENAMES:
            parts = old.split("/")
            if len(parts) != 2 or parts[0] not in {"resolution_vectors", "tdoc_source_vectors"}:
                continue
            stamp, _, identity = parts[1].partition("Z_")
            stamp += "Z"
            wg = DIRECTORY_WORKGROUPS[old]
            variant = "anchors" if identity.endswith("_anchors") else None
            self.assertEqual(identity, wg + ("_anchors" if variant else ""))
            role = parts[0].replace("_", "-")
            relative = role + "/" + stamp + ("-anchors" if variant else "") + "/status.json"
            with self.subTest(old=old):
                recorded = self.original(old + "/status.json")
                expected = self.moved(relative, wg)
                self.assertEqual(str(relocated_coordinate(recorded)), expected)
                self.assertEqual(review_run(self.root, role, stamp, wg, variant=variant)
                                 / "status.json", self.root / expected)
                original = self.write(recorded)
                self.assertEqual(current_review_input(self.root, relative, wg=wg), original)
                original.unlink()
                moved = self.write(expected)
                self.assertEqual(current_review_input(self.root, relative, wg=wg), moved)
                self.assertEqual(resolve_recorded_path(self.root, recorded, self.digest,
                                                      expected_bytes=len(self.raw)), moved)
                moved.unlink()
                targets.append(expected)
        self.assertTrue(targets)
        self.assertEqual(len(targets), len(set(targets)))

    def test_redundant_wg_leaf_is_not_an_alias_for_a_moved_run(self):
        old = self.original("resolution_vectors/20261030T030727.389362Z_RAN3/status.json")
        self.write(self.moved("resolution-vectors/20261030T030727.389362Z-RAN3/status.json", "RAN3"))
        with self.assertRaises(FileNotFoundError):
            resolve_recorded_path(self.root, old, self.digest)

    def test_exact_receipt_renames_resolve_all_declared_root_files(self):
        for old, new in RECEIPT_RENAMES.items():
            with self.subTest(old=old):
                wg, new = ROOT_FILE_LAYOUT[old]
                path = self.write(self.moved(new, wg))
                self.assertEqual(resolve_recorded_path(
                    self.root, self.original(old), self.digest), path)

    def test_same_receipt_basename_inside_a_run_is_not_renamed(self):
        suffix = "resolution_vectors/20261030T030727.389362Z_RAN3/vector_integrity_final.json"
        target = self.moved(
            "resolution-vectors/20261030T030727.389362Z/vector_integrity_final.json", "RAN3")
        self.assertEqual(str(relocated_coordinate(self.original(suffix))), target)

    def test_unknown_final_name_does_not_borrow_a_declared_alias(self):
        self.write(self.moved("unknown_receipt.json"))
        with self.assertRaises(FileNotFoundError):
            resolve_recorded_path(self.root, self.original("unknown_receipt_final.json"),
                                  self.digest)

    def test_unknown_branch_cannot_gain_a_relocated_coordinate(self):
        old = self.original("unknown_branch/receipt.json")
        self.write(self.moved("unknown-branch/receipt.json"))
        with self.assertRaisesRegex(ValueError, "unknown legacy"):
            resolve_recorded_path(self.root, old, self.digest)

    def test_unknown_run_beneath_a_known_role_is_not_inferred(self):
        old = self.original("resolution_vectors/20261030T235959.999999Z_RAN3/status.json")
        self.write(self.moved("resolution-vectors/20261030T235959.999999Z/status.json", "RAN3"))
        with self.assertRaisesRegex(ValueError, "unknown legacy"):
            resolve_recorded_path(self.root, old, self.digest)

    def test_unknown_original_branch_can_only_be_read_at_its_original_address(self):
        recorded = self.original("unknown_branch/receipt.json")
        path = self.write(recorded)
        self.assertEqual(resolve_recorded_path(self.root, recorded, self.digest), path)

    def test_similarly_named_root_has_no_relocation_fallback(self):
        self.write(self.moved())
        with self.assertRaises(FileNotFoundError):
            resolve_recorded_path(self.root,
                "logs/common/verification/ontology_system_review-extra/feature_source_population.json",
                self.digest)

    def test_ordinary_current_source_fence_remains_an_exact_identity_check(self):
        recorded = "scripts/common/fixed_source.py"
        path = self.write(recorded)
        self.assertEqual(resolve_recorded_path(self.root, recorded, self.digest), path)
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            resolve_recorded_path(self.root, recorded, "0" * 64)

    def test_original_hash_drift_is_rejected(self):
        recorded = self.original()
        self.write(recorded, b"changed")
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            resolve_recorded_path(self.root, recorded, self.digest)

    def test_relocated_hash_drift_is_rejected(self):
        self.write(self.moved(), b"changed")
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            resolve_recorded_path(self.root, self.original(), self.digest)

    def test_byte_count_drift_is_rejected(self):
        self.write(self.moved())
        with self.assertRaisesRegex(ValueError, "byte count"):
            resolve_recorded_path(self.root, self.original(), self.digest,
                                  expected_bytes=len(self.raw) + 1)

    def test_old_and_new_copies_are_ambiguous_even_when_both_hashes_match(self):
        self.write(self.original())
        self.write(self.moved())
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            resolve_recorded_path(self.root, self.original(), self.digest)

    def test_changed_original_is_not_evaded_using_a_good_relocated_copy(self):
        self.write(self.original(), b"changed")
        self.write(self.moved())
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            resolve_recorded_path(self.root, self.original(), self.digest)

    def test_directory_at_a_bound_file_address_is_rejected_without_opening(self):
        path = self.root / self.original()
        path.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "regular"):
            resolve_recorded_path(self.root, self.original(), self.digest)

    def test_fifo_at_a_bound_file_address_is_rejected_without_blocking(self):
        path = self.root / self.original()
        path.parent.mkdir(parents=True)
        os.mkfifo(path)
        with self.assertRaisesRegex(ValueError, "regular"):
            resolve_recorded_path(self.root, self.original(), self.digest)

    def test_file_replaced_with_fifo_before_open_is_rejected_and_descriptor_closed(self):
        recorded = self.original()
        path = self.write(recorded)
        original_open = os.open
        opened = []

        def replace_before_open(selected, flags, *args):
            self.assertTrue(flags & os.O_NONBLOCK)
            path.unlink()
            os.mkfifo(path)
            descriptor = original_open(selected, flags, *args)
            opened.append(descriptor)
            return descriptor

        with patch("common.review_artifacts.os.open", side_effect=replace_before_open):
            with self.assertRaisesRegex(ValueError, "regular"):
                resolve_recorded_path(self.root, recorded, self.digest)
        self.assertEqual(len(opened), 1)
        with self.assertRaises(OSError):
            os.fstat(opened[0])
        path.unlink()
        path.write_bytes(self.raw)
        self.assertEqual(resolve_recorded_path(self.root, recorded, self.digest), path)

    def test_leaf_symlink_is_rejected_even_if_target_hash_matches(self):
        actual = self.write("actual.json")
        path = self.root / self.original()
        path.parent.mkdir(parents=True)
        path.symlink_to(actual)
        with self.assertRaisesRegex(ValueError, "symlink"):
            resolve_recorded_path(self.root, self.original(), self.digest)

    def test_broken_original_symlink_cannot_be_ignored_for_a_good_new_copy(self):
        self.write(self.moved())
        path = self.root / self.original()
        path.parent.mkdir(parents=True)
        path.symlink_to(self.root / "absent.json")
        with self.assertRaisesRegex(ValueError, "symlink"):
            resolve_recorded_path(self.root, self.original(), self.digest)

    def test_relocated_symlink_is_rejected(self):
        actual = self.write("actual.json")
        path = self.root / self.moved()
        path.parent.mkdir(parents=True)
        path.symlink_to(actual)
        with self.assertRaisesRegex(ValueError, "symlink"):
            resolve_recorded_path(self.root, self.original(), self.digest)

    def test_original_parent_symlink_is_rejected(self):
        actual = self.root / "actual"
        actual.mkdir()
        (actual / "feature_source_population.json").write_bytes(self.raw)
        parent = self.root / LEGACY_REVIEW_ROOT
        parent.parent.mkdir(parents=True)
        parent.symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            resolve_recorded_path(self.root, self.original(), self.digest)

    def test_relocated_parent_symlink_is_rejected(self):
        actual = self.root / "actual"
        actual.mkdir()
        (actual / "feature_source_population.json").write_bytes(self.raw)
        parent = self.root / REVIEW_ROOT
        parent.parent.mkdir(parents=True)
        parent.symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            resolve_recorded_path(self.root, self.original(), self.digest)

    def test_repository_root_symlink_is_rejected(self):
        actual = self.root / "actual"
        actual.mkdir()
        link = self.root / "root-link"
        link.symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            resolve_recorded_path(link, self.original(), self.digest)

    def test_repository_ancestor_symlink_is_rejected(self):
        actual = self.root / "actual"
        (actual / "repository").mkdir(parents=True)
        link = self.root / "ancestor-link"
        link.symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            resolve_recorded_path(link / "repository", self.original(), self.digest)

    def test_noncanonical_coordinates_are_rejected(self):
        for recorded in ("", "../outside", "logs/../outside", "./logs/file", "/tmp/file",
                         "logs//file", "logs/file/", "C:/outside", "logs\\file", "logs/./file",
                         "logs/\x00file", None, 3):
            with self.subTest(recorded=recorded), self.assertRaises(ValueError):
                resolve_recorded_path(self.root, recorded, self.digest)

    def test_invalid_bindings_are_rejected(self):
        for digest in ("0" * 63, "0" * 65, "A" * 64, None, 3):
            with self.subTest(digest=digest), self.assertRaises(ValueError):
                resolve_recorded_path(self.root, self.original(), digest)
        for size in (-1, True, 1.0, "3"):
            with self.subTest(size=size), self.assertRaises(ValueError):
                resolve_recorded_path(self.root, self.original(), self.digest, expected_bytes=size)

    def test_artifact_change_during_hash_read_is_rejected(self):
        recorded = self.original()
        path = self.write(recorded)
        original_read = os.read
        changed = False
        def replace_after_first_read(descriptor, count):
            nonlocal changed
            chunk = original_read(descriptor, count)
            if not changed:
                changed = True
                path.unlink()
                path.write_bytes(self.raw)
            return chunk
        with patch("common.review_artifacts.os.read", side_effect=replace_after_first_read):
            with self.assertRaisesRegex(ValueError, "changed while reading"):
                resolve_recorded_path(self.root, recorded, self.digest)

    def test_large_artifact_hashing_is_chunked(self):
        raw = b"x" * (3 * 1024 * 1024 + 11)
        path = self.write(self.moved(), raw)
        original_read = os.read
        counts = []
        def observed_read(descriptor, count):
            counts.append(count)
            return original_read(descriptor, count)
        with patch("common.review_artifacts.os.read", side_effect=observed_read):
            self.assertEqual(resolve_recorded_path(self.root, self.original(),
                hashlib.sha256(raw).hexdigest(), expected_bytes=len(raw)), path)
        self.assertGreater(len(counts), 3)
        self.assertLessEqual(max(counts), 1024 * 1024)

    def test_directory_and_receipt_collisions_are_rejected(self):
        for directories, receipts in (
            ({"a_b": "a-b", "a-b": "a-b"}, {}),
            ({}, {"first_final.json": "receipt.json", "other_final.json": "receipt.json"}),
            ({}, {"first_final.json": "other_final.json", "other_final.json": "current.json"}),
        ):
            with self.subTest(directories=directories, receipts=receipts):
                with self.assertRaisesRegex(ValueError, "collision|overlap"):
                    _validate_layout(directories, receipts)

    def test_missing_artifact_is_not_treated_as_a_valid_record(self):
        with self.assertRaises(FileNotFoundError):
            resolve_recorded_path(self.root, self.original(), self.digest)

    def test_current_selector_reads_existing_original_without_claiming_an_old_sha(self):
        path = self.write(self.original(), b'current input bytes, no historical receipt')
        self.assertEqual(current_review_input(self.root, "feature_source_population.json"), path)

    def test_current_selector_reads_relocated_current_input(self):
        path = self.write(self.moved())
        self.assertEqual(current_review_input(self.root, "feature_source_population.json"), path)

    def test_current_selector_known_receipt_alias_uses_its_exact_original_name(self):
        path = self.write(self.original("vector_integrity_final.json"))
        self.assertEqual(current_review_input(self.root, "vector_integrity.json"), path)
        with self.assertRaisesRegex(ValueError, "current artifact coordinate"):
            current_review_input(self.root, "vector_integrity_final.json")

    def test_current_selector_keeps_optional_missing_and_required_read_failure(self):
        path = current_review_input(self.root, "feature_source_population.json")
        self.assertEqual(path, self.root / self.moved())
        self.assertFalse(path.exists())
        with self.assertRaises(FileNotFoundError):
            path.read_bytes()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_current_selector_rejects_old_and_new_ambiguity_without_comparing_content(self):
        self.write(self.original(), b'old input')
        self.write(self.moved(), b'new input')
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            current_review_input(self.root, "feature_source_population.json")

    def test_current_selector_rejects_old_and_new_ambiguity_for_a_wg_run(self):
        old = "resolution_vectors/20261030T030727.389362Z_RAN3/status.json"
        new = "resolution-vectors/20261030T030727.389362Z/status.json"
        self.write(self.original(old))
        path = current_review_input(self.root, new, wg="RAN3")
        self.assertEqual(path, self.root / self.original(old))
        self.write(self.moved(new, "RAN3"))
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            current_review_input(self.root, new, wg="RAN3")

    def test_current_selector_does_not_infer_unknown_legacy_branches(self):
        self.write(self.original("unknown_branch/input.json"))
        target = current_review_input(self.root, "unknown-branch/input.json")
        self.assertEqual(target, self.root / self.moved("unknown-branch/input.json"))
        self.assertFalse(target.exists())

    def test_current_selector_does_not_infer_unknown_run_identity(self):
        self.write(self.original("resolution_vectors/20261030T235959.999999Z_RAN3/status.json"))
        name = "resolution-vectors/20261030T235959.999999Z/status.json"
        self.assertFalse(current_review_input(self.root, name, wg="RAN3").exists())

    def test_current_selector_rejects_symlink_leaf_and_ancestor(self):
        actual = self.write("actual.json")
        path = self.root / self.original()
        path.parent.mkdir(parents=True)
        path.symlink_to(actual)
        with self.assertRaisesRegex(ValueError, "symlink"):
            current_review_input(self.root, "feature_source_population.json")
        path.unlink()
        current_parent = self.root / REVIEW_ROOT
        current_parent.symlink_to(path.parent, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            current_review_input(self.root, "feature_source_population.json")

    def test_current_selector_does_not_ignore_a_broken_original_symlink(self):
        self.write(self.moved())
        path = self.root / self.original()
        path.parent.mkdir(parents=True)
        path.symlink_to(self.root / "absent.json")
        with self.assertRaisesRegex(ValueError, "symlink"):
            current_review_input(self.root, "feature_source_population.json")

    def test_current_selector_rejects_directory_and_fifo_inputs(self):
        path = self.root / self.original()
        path.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "regular"):
            current_review_input(self.root, "feature_source_population.json")
        path.rmdir()
        os.mkfifo(path)
        with self.assertRaisesRegex(ValueError, "regular"):
            current_review_input(self.root, "feature_source_population.json")

    def test_current_selector_rejects_traversal_and_unsafe_workgroups(self):
        for name in ("../outside", "/tmp/outside", "a//b", "a/./b", "a\\b", "", None):
            with self.subTest(name=name), self.assertRaises(ValueError):
                current_review_input(self.root, name)
        with self.assertRaises(ValueError):
            current_review_input(self.root, "input.json", wg="../RAN3")

    def test_wg_role_mapping_does_not_leave_a_function_workgroup_suffix(self):
        for wg in ("RAN3", "RAN4", "RAN5"):
            self.assertEqual(str(relocated_coordinate(self.original(
                "body_source_metadata_" + wg + "/receipt.json"))),
                self.moved("body-source-metadata/receipt.json", wg))

    def test_different_workgroups_share_role_names_without_colliding(self):
        _validate_layout({"old_RAN3": "body-source-metadata", "old_RAN4": "body-source-metadata"},
                         {}, {"old_RAN3": "RAN3", "old_RAN4": "RAN4"})
        with self.assertRaisesRegex(ValueError, "collision"):
            _validate_layout({"old_RAN3": "body-source-metadata", "old_RAN4": "body-source-metadata"},
                             {}, {"old_RAN3": "RAN3", "old_RAN4": "RAN3"})

    def test_root_file_scope_uses_declared_workgroup_and_exact_basename(self):
        for old, wg, new in (
            ("body_source_metadata_RAN3.json", "RAN3", "body_source_metadata.json"),
            ("ran2_annex_identity_cover_census.json", "RAN2", "annex_identity_cover_census.json"),
            ("vector_integrity_ran2_final.json", "RAN2", "vector_integrity.json"),
            ("tr_ran5_native_error_source_discovery.json", "RAN5", "tr_native_error_source_discovery.json"),
        ):
            with self.subTest(old=old):
                self.assertEqual(str(relocated_coordinate(self.original(old))), self.moved(new, wg))

    def test_declared_root_files_read_before_and_after_byte_preserving_move(self):
        for old, (wg, new) in ROOT_FILE_LAYOUT.items():
            with self.subTest(old=old):
                original = self.write(self.original(old))
                self.assertEqual(current_review_input(self.root, new, wg=wg), original)
                self.assertEqual(resolve_recorded_path(self.root, self.original(old), self.digest), original)
                original.unlink()
                moved = self.write(self.moved(new, wg))
                self.assertEqual(current_review_input(self.root, new, wg=wg), moved)
                self.assertEqual(resolve_recorded_path(self.root, self.original(old), self.digest,
                                                      expected_bytes=len(self.raw)), moved)
                moved.unlink()

    def test_same_root_basename_in_different_workgroups_selects_distinct_originals(self):
        first = self.write(self.original("body_source_metadata_RAN3.json"))
        second = self.write(self.original("body_source_metadata_RAN4.json"), b"other observation")
        self.assertEqual(current_review_input(self.root, "body_source_metadata.json", wg="RAN3"), first)
        self.assertEqual(current_review_input(self.root, "body_source_metadata.json", wg="RAN4"), second)

    def test_workgroup_root_file_old_and_current_ambiguity_is_rejected(self):
        old = self.original("ran2_annex_62_native_cr_source_plan.json")
        self.write(old)
        self.write(self.moved("annex_62_native_cr_source_plan.json", "RAN2"))
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            current_review_input(self.root, "annex_62_native_cr_source_plan.json", wg="RAN2")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            resolve_recorded_path(self.root, old, self.digest)

    def test_wrong_or_omitted_workgroup_cannot_borrow_a_scoped_original(self):
        self.write(self.original("ran2_annex_62_native_cr_source_plan.json"))
        for wg in (None, "RAN1", "RAN3"):
            with self.subTest(wg=wg):
                path = current_review_input(self.root, "annex_62_native_cr_source_plan.json", wg=wg)
                self.assertFalse(path.exists())
                self.assertEqual(path, self.root / self.moved("annex_62_native_cr_source_plan.json", wg))

    def test_current_selector_rejects_scoped_legacy_root_names(self):
        self.write(self.original("ran2_annex_62_native_cr_source_plan.json"))
        for wg in (None, "RAN2", "RAN3"):
            with self.subTest(wg=wg), self.assertRaisesRegex(ValueError, "current artifact coordinate"):
                current_review_input(self.root, "ran2_annex_62_native_cr_source_plan.json", wg=wg)

    def test_scoped_root_name_is_not_rewritten_inside_a_run(self):
        old = self.original("resolution_vectors/20261030T030727.389362Z_RAN3/body_source_metadata_RAN3.json")
        expected = self.moved("resolution-vectors/20261030T030727.389362Z/body_source_metadata_RAN3.json", "RAN3")
        self.assertEqual(str(relocated_coordinate(old)), expected)
        path = self.write(expected)
        self.assertEqual(resolve_recorded_path(self.root, old, self.digest), path)

    def test_unknown_workgroup_looking_filename_has_no_scoped_inference(self):
        name = "ran2_unknown_observation.json"
        self.assertEqual(str(relocated_coordinate(self.original(name))), self.moved(name))
        self.write(self.moved("unknown_observation.json", "RAN2"))
        with self.assertRaises(FileNotFoundError):
            resolve_recorded_path(self.root, self.original(name), self.digest)

    def test_mixed_observation_with_ran2_in_its_name_remains_shared(self):
        name = "vector_integrity_final_before_ran2_a93e2801d80b.json"
        self.assertNotIn(name, ROOT_FILE_LAYOUT)
        self.assertEqual(str(relocated_coordinate(self.original(name))), self.moved(name))

    def test_scoped_root_file_byte_drift_is_rejected(self):
        self.write(self.moved("annex_identity_cover_census.json", "RAN2"), b"changed")
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            resolve_recorded_path(self.root, self.original("ran2_annex_identity_cover_census.json"), self.digest)

    def test_scoped_root_file_mapping_rejects_symlink_and_broken_original(self):
        old = self.original("ran2_annex_identity_cover_census.json")
        self.write(self.moved("annex_identity_cover_census.json", "RAN2"))
        original = self.root / old
        original.parent.mkdir(parents=True, exist_ok=True)
        original.symlink_to(self.root / "absent.json")
        with self.assertRaisesRegex(ValueError, "symlink"):
            resolve_recorded_path(self.root, old, self.digest)
        with self.assertRaisesRegex(ValueError, "symlink"):
            current_review_input(self.root, "annex_identity_cover_census.json", wg="RAN2")

    def test_root_file_relocation_collisions_are_checked_with_workgroup_scope(self):
        _validate_layout({}, {}, root_files={"a.json": ("RAN3", "result.json"),
                                            "b.json": ("RAN4", "result.json")})
        for directories, groups, files in (
            ({}, {}, {"a.json": ("RAN3", "result.json"), "b.json": ("RAN3", "result.json")}),
            ({"old": "result.json"}, {"old": "RAN3"}, {"a.json": ("RAN3", "result.json")}),
        ):
            with self.subTest(files=files), self.assertRaisesRegex(ValueError, "collision"):
                _validate_layout(directories, {}, groups, files)

    def test_root_file_layout_rejects_unsafe_names_and_unknown_workgroup(self):
        for old, target in (
            ("../source.json", ("RAN2", "source.json")),
            ("source.json", ("RAN2", "../target.json")),
            ("source.json", ("RAN2", "nested/target.json")),
            ("source.json", ("RAN2", "nested\\target.json")),
            ("source.json", ("UNKNOWN", "target.json")),
        ):
            with self.subTest(old=old, target=target), self.assertRaises(ValueError):
                _validate_layout({}, {}, root_files={old: target})

    def test_scope_bound_plenary_root_file_uses_registry_partition(self):
        old = self.original("tsgran_topical_reconciliation.json")
        expected = self.moved("topical_reconciliation.json", "TSG_RAN")
        self.assertEqual(str(relocated_coordinate(old)), expected)
        path = self.write(expected)
        self.assertEqual(resolve_recorded_path(self.root, old, self.digest), path)
        self.assertEqual(current_review_input(self.root, "topical_reconciliation.json", wg="TSG_RAN"), path)

    def test_exact_second_terminal_name_does_not_create_a_generic_final_alias(self):
        for suffix in (".json", ".log", "_execution.json"):
            old = "vector_integrity_changed_final2" + suffix
            new = "vector_integrity_changed" + suffix
            with self.subTest(old=old):
                expected = self.moved(new, "RAN4")
                self.assertEqual(str(relocated_coordinate(self.original(old))), expected)
                path = self.write(expected)
                self.assertEqual(resolve_recorded_path(self.root, self.original(old), self.digest), path)
        unknown = "vector_integrity_changed_final3.json"
        self.assertEqual(str(relocated_coordinate(self.original(unknown))), self.moved(unknown))
        with self.assertRaises(FileNotFoundError):
            resolve_recorded_path(self.root, self.original(unknown), self.digest)

    def test_compressed_preimage_name_keeps_raw_byte_identity(self):
        old = self.original("ran4_revision_receipt_preimage-9f1de61a1645c1d5.json.gz")
        raw = b"opaque compressed source bytes"
        path = self.write(self.moved("revision_receipt_preimage-9f1de61a1645c1d5.json.gz", "RAN4"), raw)
        self.assertEqual(resolve_recorded_path(self.root, old, hashlib.sha256(raw).hexdigest(),
                                              expected_bytes=len(raw)), path)
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            resolve_recorded_path(self.root, old, self.digest)

    def test_mixed_parent_exact_files_roundtrip_without_changing_scope(self):
        targets = []
        for old, (wg, new) in NESTED_FILE_LAYOUT.items():
            with self.subTest(old=old, wg=wg):
                recorded = self.original(old)
                expected = self.moved(new, wg)
                self.assertEqual(str(relocated_coordinate(recorded)), expected)
                original = self.write(recorded)
                self.assertEqual(current_review_input(self.root, new, wg=wg), original)
                self.assertEqual(resolve_recorded_path(self.root, recorded, self.digest,
                                                      expected_bytes=len(self.raw)), original)
                original.unlink()
                moved = self.write(expected)
                self.assertEqual(current_review_input(self.root, new, wg=wg), moved)
                self.assertEqual(resolve_recorded_path(self.root, recorded, self.digest,
                                                      expected_bytes=len(self.raw)), moved)
                moved.unlink()
                targets.append(expected)
        self.assertEqual(len(targets), 63)
        self.assertEqual(len(targets), len(set(targets)))

    def test_mixed_parent_does_not_give_unknown_siblings_a_relocation(self):
        old = "cq_shortfall_followup/agenda_heading_census/unknown_review.json"
        target = "cq-shortfall-followup/agenda-heading-census/unknown_review.json"
        for wg in (None, "RAN1", "RAN2", "RAN3", "RAN4", "RAN5"):
            with self.subTest(wg=wg):
                moved = self.write(self.moved(target, wg))
                with self.assertRaisesRegex(ValueError, "unknown legacy"):
                    relocated_coordinate(self.original(old))
                with self.assertRaisesRegex(ValueError, "unknown legacy"):
                    resolve_recorded_path(self.root, self.original(old), self.digest)
                moved.unlink()
                original = self.write(self.original(old))
                self.assertFalse(current_review_input(self.root, target, wg=wg).exists())
                self.assertEqual(resolve_recorded_path(self.root, self.original(old),
                                                      self.digest), original)
                original.unlink()

    def test_nested_current_selector_rejects_legacy_aliases(self):
        for old in NESTED_FILE_LAYOUT:
            for wg in (None, "RAN1", "RAN2", "RAN3", "RAN4", "RAN5"):
                with self.subTest(old=old, wg=wg), self.assertRaisesRegex(ValueError, "legacy alias"):
                    current_review_input(self.root, old, wg=wg)

    def test_nested_file_wrong_workgroup_cannot_borrow_an_original(self):
        for old, (wg, new) in NESTED_FILE_LAYOUT.items():
            original = self.write(self.original(old))
            for other in (None, "RAN1", "RAN2", "RAN3", "RAN4", "RAN5", "TSG_RAN"):
                if other == wg:
                    continue
                with self.subTest(old=old, other=other):
                    if (other is None and str(Path(old).parent) in DIRECTORY_RENAMES
                            and DIRECTORY_WORKGROUPS[str(Path(old).parent)] is None
                            and Path(old).name == Path(new).name):
                        with self.assertRaisesRegex(ValueError, "exact declaration"):
                            current_review_input(self.root, new, wg=other)
                    else:
                        self.assertFalse(current_review_input(self.root, new, wg=other).exists())
            original.unlink()

    def test_nested_exact_filename_does_not_apply_in_another_parent(self):
        old = "cq_shortfall_followup/another_census/ran2_source_heading_census.json"
        target = self.moved("cq-shortfall-followup/agenda-heading-census/source_heading_census.json",
                            "RAN2")
        self.write(target)
        with self.assertRaisesRegex(ValueError, "unknown legacy"):
            resolve_recorded_path(self.root, self.original(old), self.digest)

    def test_nested_old_and_new_copies_remain_ambiguous(self):
        for old, (wg, new) in NESTED_FILE_LAYOUT.items():
            with self.subTest(old=old):
                original = self.write(self.original(old), b"changed original")
                moved = self.write(self.moved(new, wg))
                with self.assertRaisesRegex(ValueError, "ambiguous"):
                    current_review_input(self.root, new, wg=wg)
                with self.assertRaisesRegex(ValueError, "ambiguous"):
                    resolve_recorded_path(self.root, self.original(old), self.digest)
                original.unlink()
                moved.unlink()

    def test_nested_identity_checks_sha_bytes_and_original_drift(self):
        old, (wg, new) = next(iter(NESTED_FILE_LAYOUT.items()))
        original = self.write(self.original(old), b"changed original")
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            resolve_recorded_path(self.root, self.original(old), self.digest)
        original.unlink()
        self.write(self.moved(new, wg))
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            resolve_recorded_path(self.root, self.original(old), "0" * 64)
        for size in (len(self.raw) + 1, True):
            with self.subTest(size=size), self.assertRaises(ValueError):
                resolve_recorded_path(self.root, self.original(old), self.digest,
                                      expected_bytes=size)

    def test_nested_broken_original_symlink_cannot_be_hidden_by_good_new_copy(self):
        old, (wg, new) = next(iter(NESTED_FILE_LAYOUT.items()))
        original = self.root / self.original(old)
        original.parent.mkdir(parents=True)
        original.symlink_to(self.root / "absent.json")
        self.write(self.moved(new, wg))
        with self.assertRaisesRegex(ValueError, "symlink"):
            current_review_input(self.root, new, wg=wg)
        with self.assertRaisesRegex(ValueError, "symlink"):
            resolve_recorded_path(self.root, self.original(old), self.digest)

    def test_nested_relocated_parent_symlink_is_rejected(self):
        old, (wg, new) = next(iter(NESTED_FILE_LAYOUT.items()))
        path = self.root / self.moved(new, wg)
        outside = self.root / "elsewhere"
        outside.mkdir()
        (outside / path.name).write_bytes(self.raw)
        path.parent.parent.mkdir(parents=True)
        path.parent.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            current_review_input(self.root, new, wg=wg)
        with self.assertRaisesRegex(ValueError, "symlink"):
            resolve_recorded_path(self.root, self.original(old), self.digest)

    def test_nested_layout_rejects_unsafe_or_root_only_coordinates(self):
        for old, target in (
            ("../mixed/input.json", ("RAN2", "role/input.json")),
            ("mixed//input.json", ("RAN2", "role/input.json")),
            ("mixed/input.json", ("RAN2", "../role/input.json")),
            ("mixed/input.json", ("RAN2", "C:/role/input.json")),
            ("mixed/input.json", ("RAN2", "role\\input.json")),
            ("input.json", ("RAN2", "role/input.json")),
            ("mixed/input.json", ("RAN2", "input.json")),
            ("mixed/input.json", ("UNKNOWN", "role/input.json")),
        ):
            with self.subTest(old=old, target=target), self.assertRaises(ValueError):
                _validate_layout({}, {}, nested_files={old: target})

    def test_nested_layout_targets_are_injective_per_workgroup(self):
        _validate_layout({}, {}, nested_files={
            "mixed/a.json": ("RAN2", "role/result.json"),
            "mixed/b.json": ("RAN3", "role/result.json"),
        })
        for directories, groups, roots, nested in (
            ({}, {}, {}, {"mixed/a.json": ("RAN2", "role/result.json"),
                          "mixed/b.json": ("RAN2", "role/result.json")}),
            ({"old_dir": "role/result.json"}, {"old_dir": "RAN2"}, {},
             {"mixed/a.json": ("RAN2", "role/result.json")}),
            ({"old_dir": "role/result.json/child"}, {"old_dir": "RAN2"}, {},
             {"mixed/a.json": ("RAN2", "role/result.json")}),
            ({}, {}, {"root.json": ("RAN2", "role")},
             {"mixed/a.json": ("RAN2", "role/result.json")}),
            ({}, {}, {}, {"mixed/a.json": ("RAN2", "role/result.json"),
                          "mixed/b.json": ("RAN2", "role/result.json/child")}),
        ):
            with self.subTest(nested=nested), self.assertRaisesRegex(ValueError, "collision"):
                _validate_layout(directories, {}, groups, roots, nested)

    def test_nested_mixed_parent_cannot_gain_a_general_directory_fallback(self):
        with self.assertRaisesRegex(ValueError, "directory fallback"):
            _validate_layout({"mixed": "role"}, {}, {"mixed": "RAN2"}, nested_files={
                "mixed/input.json": ("RAN2", "role/input.json"),
            }, file_only_parents={"mixed"})
        self.assertEqual(FILE_ONLY_PARENTS, {"cq_shortfall_followup/agenda_heading_census"})

    def test_exact_scoped_file_can_override_a_shared_parent_without_borrowing_it(self):
        _validate_layout({"shared": "role"}, {}, {"shared": None}, nested_files={
            "shared/input.json": ("RAN2", "role/input.json"),
        })
        for leaf, wg in (
            ("capability_column_header_shadow.json", "RAN2"),
            ("capability_suffix_independent_review.json", "RAN2"),
            ("docx_search_text_independent_review.json", "RAN4"),
        ):
            old = "cq_shortfall_followup/" + leaf
            new = "cq-shortfall-followup/" + leaf
            with self.subTest(leaf=leaf):
                original = self.write(self.original(old))
                self.assertEqual(current_review_input(self.root, new, wg=wg), original)
                with self.assertRaisesRegex(ValueError, "exact declaration"):
                    current_review_input(self.root, new)
                self.assertFalse(current_review_input(self.root, new, wg="RAN3").exists())
                with self.assertRaisesRegex(ValueError, "legacy alias"):
                    current_review_input(self.root, old, wg=wg)
                original.unlink()
                moved = self.write(self.moved(new, wg))
                self.assertEqual(current_review_input(self.root, new, wg=wg), moved)
                with self.assertRaisesRegex(ValueError, "exact declaration"):
                    current_review_input(self.root, new)
                moved.unlink()

    def test_general_shared_siblings_keep_their_existing_current_input_contract(self):
        for leaf in ("ie_description_math_summary.json", "unknown_shared_observation.json"):
            old = "cq_shortfall_followup/" + leaf
            new = "cq-shortfall-followup/" + leaf
            with self.subTest(leaf=leaf):
                original = self.write(self.original(old))
                self.assertEqual(current_review_input(self.root, new), original)
                self.assertEqual(resolve_recorded_path(self.root, self.original(old),
                                                      self.digest), original)
                original.unlink()
                moved = self.write(self.moved(new))
                self.assertEqual(current_review_input(self.root, new), moved)
                self.assertEqual(resolve_recorded_path(self.root, self.original(old),
                                                      self.digest), moved)
                moved.unlink()

    def test_shared_current_copy_cannot_hide_an_exact_scoped_old_file(self):
        leaf = "capability_column_header_shadow.json"
        old = self.write(self.original("cq_shortfall_followup/" + leaf))
        self.write(self.moved("cq-shortfall-followup/" + leaf))
        with self.assertRaisesRegex(ValueError, "exact declaration"):
            current_review_input(self.root, "cq-shortfall-followup/" + leaf)
        self.assertEqual(current_review_input(self.root, "cq-shortfall-followup/" + leaf,
                                             wg="RAN2"), old)

    def test_file_only_parent_declarations_require_safe_relative_coordinates(self):
        for parent in ("../mixed", "mixed//child", "C:/mixed", "mixed\\child"):
            with self.subTest(parent=parent), self.assertRaises(ValueError):
                _validate_layout({}, {}, file_only_parents={parent})

    def test_local_conversion_aliases_keep_the_original_zip_member_identity(self):
        for extension in (".docx", ".accepted.docx", ".conversion.json"):
            old_name = "RP-171485 revised WID_NR_clean_v6" + extension
            old = "ran4_cq_official_sources/" + old_name
            new = "cq-official-sources/RP-171485" + extension
            with self.subTest(extension=extension):
                self.assertEqual(NESTED_FILE_LAYOUT[old], ("RAN4", new))
                original = self.write(self.original(old))
                self.assertEqual(current_review_input(self.root, new, wg="RAN4"), original)
                self.assertEqual(resolve_recorded_path(self.root, self.original(old),
                                                      self.digest), original)
                with self.assertRaisesRegex(ValueError, "exact declaration"):
                    current_review_input(self.root, "cq-official-sources/" + old_name,
                                         wg="RAN4")
                original.unlink()
                moved = self.write(self.moved(new, "RAN4"))
                self.assertEqual(current_review_input(self.root, new, wg="RAN4"), moved)
                self.assertEqual(resolve_recorded_path(self.root, self.original(old),
                                                      self.digest), moved)
                with self.assertRaisesRegex(ValueError, "exact declaration"):
                    current_review_input(self.root, "cq-official-sources/" + old_name,
                                         wg="RAN4")
                moved.unlink()

    def test_exact_conversion_alias_does_not_rename_other_source_versions(self):
        old = "ran4_cq_official_sources/RP-171485_other_v6.docx"
        new = "cq-official-sources/RP-171485_other_v6.docx"
        original = self.write(self.original(old))
        self.assertEqual(current_review_input(self.root, new, wg="RAN4"), original)
        self.assertEqual(str(relocated_coordinate(self.original(old))), self.moved(new, "RAN4"))
        self.assertFalse(current_review_input(self.root, "cq-official-sources/RP-171485_other.docx",
                                             wg="RAN4").exists())

    def test_legacy_conversion_name_cannot_select_an_unrelated_current_copy(self):
        old_name = "RP-171485 revised WID_NR_clean_v6.accepted.docx"
        old = "ran4_cq_official_sources/" + old_name
        original = self.write(self.original(old), b"changed original")
        self.write(self.moved("cq-official-sources/" + old_name, "RAN4"))
        with self.assertRaisesRegex(ValueError, "exact declaration"):
            current_review_input(self.root, "cq-official-sources/" + old_name, wg="RAN4")
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            resolve_recorded_path(self.root, self.original(old), self.digest)
        self.assertTrue(original.is_file())

    def test_closed_ran4_nested_roles_preserve_identity_before_and_after_move(self):
        for old_parent, current_parent in (
            ("cq_shortfall_followup/ran4_861_proposal", "cq-shortfall-followup/861-proposal"),
            ("cq_shortfall_followup/ran4_primary_sources", "cq-shortfall-followup/primary-sources"),
        ):
            with self.subTest(old_parent=old_parent):
                old = self.original(old_parent + "/artifact.json")
                new = current_parent + "/artifact.json"
                self.assertEqual(DIRECTORY_WORKGROUPS[old_parent], "RAN4")
                self.assertEqual(DIRECTORY_RENAMES[old_parent], current_parent)
                original = self.write(old)
                self.assertEqual(current_review_input(self.root, new, wg="RAN4"), original)
                self.assertFalse(current_review_input(self.root, new).exists())
                original.unlink()
                moved = self.write(self.moved(new, "RAN4"))
                self.assertEqual(resolve_recorded_path(self.root, old, self.digest), moved)
                self.assertEqual(current_review_input(self.root, new, wg="RAN4"), moved)
                moved.unlink()

    def test_nested_role_override_does_not_infer_unknown_descendants(self):
        old = self.original("cq_shortfall_followup/ran4_primary_sources/unregistered/source.json")
        self.write(self.moved("cq-shortfall-followup/primary-sources/unregistered/source.json", "RAN4"))
        with self.assertRaisesRegex(ValueError, "unknown legacy"):
            resolve_recorded_path(self.root, old, self.digest)

    def test_ran1_closed_workflow_parents_keep_preimages_in_the_same_scope(self):
        for old_role, new_role in (
            ("ran1_agenda_reconciliation", "agenda-reconciliation"),
            ("ran1_agenda_reconciliation/preimages", "agenda-reconciliation/preimages"),
            ("ran1_agenda_live_reconciliation", "agenda-live-reconciliation"),
            ("ran1_decision_disposition_reconciliation", "decision-disposition-reconciliation"),
        ):
            old = "cq_shortfall_followup/" + old_role + "/receipt.json"
            new = "cq-shortfall-followup/" + new_role + "/receipt.json"
            with self.subTest(old_role=old_role):
                original = self.write(self.original(old))
                self.assertEqual(current_review_input(self.root, new, wg="RAN1"), original)
                for wrong_scope in (None, "RAN2", "TSG_RAN"):
                    self.assertFalse(current_review_input(self.root, new, wg=wrong_scope).exists())
                original.unlink()
                moved = self.write(self.moved(new, "RAN1"))
                self.assertEqual(resolve_recorded_path(self.root, self.original(old),
                                                      self.digest), moved)
                with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                    resolve_recorded_path(self.root, self.original(old), "0" * 64)
                self.write(self.original(old))
                with self.assertRaisesRegex(ValueError, "ambiguous"):
                    resolve_recorded_path(self.root, self.original(old), self.digest)
                (self.root / self.original(old)).unlink()
                moved.unlink()

    def test_closed_agenda_workflow_does_not_infer_a_new_nested_parent(self):
        old = self.original("cq_shortfall_followup/ran1_agenda_reconciliation/new_run/receipt.json")
        self.write(self.moved("cq-shortfall-followup/agenda-reconciliation/new-run/receipt.json",
                              "RAN1"))
        with self.assertRaisesRegex(ValueError, "unknown legacy"):
            resolve_recorded_path(self.root, old, self.digest)

    def test_workgroup_named_shared_census_is_not_reclassified_by_its_basename(self):
        for basename in ("ran1_registered_agenda_crossartifact_readback.json",
                         "ran1_agenda_probe_sources.json.gz", "ran1_agenda_probe_cleanup.json"):
            old = "cq_shortfall_followup/" + basename
            new = "cq-shortfall-followup/" + basename
            with self.subTest(basename=basename):
                original = self.write(self.original(old))
                self.assertEqual(str(relocated_coordinate(self.original(old))), self.moved(new))
                self.assertEqual(current_review_input(self.root, new), original)
                self.assertFalse(current_review_input(self.root, new, wg="RAN1").exists())
                original.unlink()

    def test_mixed_heading_parent_has_separate_shared_and_ran1_exact_inputs(self):
        for old_name, wg, new_name in (
            ("additional_source_heading_review.json", None, "additional_source_heading_review.json"),
            ("ran1_source_closure_independent_review.json", "RAN1", "source_closure_independent_review.json"),
        ):
            old = "cq_shortfall_followup/agenda_heading_census/" + old_name
            new = "cq-shortfall-followup/agenda-heading-census/" + new_name
            with self.subTest(old_name=old_name):
                original = self.write(self.original(old))
                self.assertEqual(current_review_input(self.root, new, wg=wg), original)
                for other in (None, "RAN1", "RAN2"):
                    if other != wg:
                        self.assertFalse(current_review_input(self.root, new, wg=other).exists())
                original.unlink()

    def test_additional_source_reviews_keep_their_proven_workgroup_and_recorded_bytes(self):
        for old_name, wg, new_name in (
            ("cr_section_wrong_topic_independent_review.json", "RAN5",
             "cr_section_wrong_topic_independent_review.json"),
            ("ts_fused_clause_source_evidence.json", "RAN5",
             "ts_fused_clause_source_evidence.json"),
            ("capability_polluted_row_coverage_plan.json", "RAN2",
             "capability_polluted_row_coverage_plan.json"),
            ("ran2_cr_2002409_wrong_topic_independent_review.json", "RAN2",
             "cr_2002409_wrong_topic_independent_review.json"),
        ):
            old = "cq_shortfall_followup/" + old_name
            new = "cq-shortfall-followup/" + new_name
            with self.subTest(old_name=old_name):
                self.assertEqual(NESTED_FILE_LAYOUT[old], (wg, new))
                original = self.write(self.original(old))
                self.assertEqual(current_review_input(self.root, new, wg=wg), original)
                self.assertEqual(str(relocated_coordinate(self.original(old))), self.moved(new, wg))
                original.unlink()
                moved = self.write(self.moved(new, wg))
                self.assertEqual(current_review_input(self.root, new, wg=wg), moved)
                self.assertEqual(resolve_recorded_path(self.root, self.original(old), self.digest,
                                                      expected_bytes=len(self.raw)), moved)
                with self.assertRaisesRegex(ValueError, "byte count mismatch"):
                    resolve_recorded_path(self.root, self.original(old), self.digest,
                                          expected_bytes=len(self.raw) + 1)
                moved.write_bytes(b"changed current source")
                with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                    resolve_recorded_path(self.root, self.original(old), self.digest)
                moved.unlink()

    def test_scoped_source_reviews_cannot_be_borrowed_by_shared_or_other_workgroups(self):
        for leaf, wg in (
            ("cr_section_wrong_topic_independent_review.json", "RAN5"),
            ("ts_fused_clause_source_evidence.json", "RAN5"),
            ("capability_polluted_row_coverage_plan.json", "RAN2"),
        ):
            with self.subTest(leaf=leaf):
                original = self.write(self.original("cq_shortfall_followup/" + leaf))
                self.write(self.moved("cq-shortfall-followup/" + leaf))
                with self.assertRaisesRegex(ValueError, "exact declaration"):
                    current_review_input(self.root, "cq-shortfall-followup/" + leaf)
                other = "RAN2" if wg == "RAN5" else "RAN5"
                self.assertFalse(current_review_input(self.root, "cq-shortfall-followup/" + leaf,
                                                     wg=other).exists())
                self.assertEqual(current_review_input(self.root, "cq-shortfall-followup/" + leaf,
                                                     wg=wg), original)
                original.unlink()

    def test_renamed_source_review_legacy_alias_cannot_select_a_shared_copy(self):
        old_name = "ran2_cr_2002409_wrong_topic_independent_review.json"
        old = self.original("cq_shortfall_followup/" + old_name)
        original = self.write(old, b"changed original")
        new = "cq-shortfall-followup/cr_2002409_wrong_topic_independent_review.json"
        with self.assertRaisesRegex(ValueError, "legacy alias"):
            current_review_input(self.root, "cq_shortfall_followup/" + old_name, wg="RAN2")
        self.write(self.moved("cq-shortfall-followup/" + old_name))
        with self.assertRaisesRegex(ValueError, "exact declaration"):
            current_review_input(self.root, "cq-shortfall-followup/" + old_name)
        self.assertFalse(current_review_input(self.root, new).exists())
        moved = self.write(self.moved(new, "RAN2"))
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            current_review_input(self.root, new, wg="RAN2")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            resolve_recorded_path(self.root, old, self.digest)
        original.unlink()
        self.assertEqual(resolve_recorded_path(self.root, old, self.digest), moved)

    def test_unregistered_source_review_does_not_inherit_a_nearby_exact_scope(self):
        leaf = "ran2_cr_2002410_wrong_topic_independent_review.json"
        original = self.write(self.original("cq_shortfall_followup/" + leaf))
        relative = "cq-shortfall-followup/" + leaf
        self.assertEqual(current_review_input(self.root, relative), original)
        self.assertEqual(str(relocated_coordinate(self.original("cq_shortfall_followup/" + leaf))),
                         self.moved(relative))
        for wg in ("RAN2", "RAN5"):
            self.assertFalse(current_review_input(self.root, relative, wg=wg).exists())

    def test_independent_source_reports_use_the_actual_source_scope_not_the_tool_scope(self):
        for old_name, wg, new_name in (
            ("capability_physical_row_identity_review.json", "RAN2",
             "capability_physical_row_identity_review.json"),
            ("caption_search_role_runtime_review.json", "RAN4",
             "caption_search_role_runtime_review.json"),
            ("external_ls_reference_followup.json", "RAN4",
             "external_ls_reference_followup.json"),
            ("ts_recovered_source_fragment_renderer_validation.json", "RAN5",
             "ts_recovered_source_fragment_renderer_validation.json"),
            ("ts_p12_single_sentence_source_evidence.json", "RAN5",
             "ts_p12_single_sentence_source_evidence.json"),
            ("ts_search_renderer_shadow_RAN4_38.101-5_Rel-19.json", "RAN4",
             "ts_search_renderer_shadow_38.101-5_Rel-19.json"),
            ("review_tool_ran3_roundtrip_counterexample.json", "RAN3",
             "review_tool_roundtrip_counterexample.json"),
            ("ran1_role_agenda_source_adjudication.json", "RAN1",
             "role_agenda_source_adjudication.json"),
            ("ts_fused_clause_independent_review.json", "RAN5",
             "ts_fused_clause_independent_review.json"),
        ):
            old = "cq_shortfall_followup/" + old_name
            new = "cq-shortfall-followup/" + new_name
            with self.subTest(old_name=old_name):
                self.assertEqual(NESTED_FILE_LAYOUT[old], (wg, new))
                original = self.write(self.original(old))
                self.assertEqual(current_review_input(self.root, new, wg=wg), original)
                self.assertFalse(current_review_input(self.root, new, wg="TSG_RAN").exists())
                with self.assertRaisesRegex(ValueError, "legacy alias"):
                    current_review_input(self.root, old, wg=wg)
                if old_name != new_name:
                    self.assertFalse(current_review_input(self.root, new).exists())
                    with self.assertRaisesRegex(ValueError, "exact declaration"):
                        current_review_input(self.root, "cq-shortfall-followup/" + old_name)
                else:
                    with self.assertRaisesRegex(ValueError, "exact declaration"):
                        current_review_input(self.root, new)
                original.unlink()

    def test_mixed_scope_search_and_schema_records_keep_the_shared_coordinate(self):
        for leaf in ("ts_search_generation_method_archive.json.gz",
                     "ts_search_presentation_current_manifest.json.gz",
                     "functional_property_source_review.json",
                     "ts_search_release_partition_plan.json",
                     "revision_inverse_functional_census.json"):
            old = self.original("cq_shortfall_followup/" + leaf)
            new = "cq-shortfall-followup/" + leaf
            with self.subTest(leaf=leaf):
                original = self.write(old)
                self.assertEqual(current_review_input(self.root, new), original)
                self.assertEqual(str(relocated_coordinate(old)), self.moved(new))
                for wg in ("RAN1", "RAN4", "RAN5"):
                    self.assertFalse(current_review_input(self.root, new, wg=wg).exists())
                original.unlink()
                moved = self.write(self.moved(new))
                self.assertEqual(resolve_recorded_path(self.root, old, self.digest), moved)
                moved.unlink()


    def test_native_row_and_source_review_additions_have_exact_workgroup_scope(self):
        for old_name, wg, new_name in (
            ("ran3_revision_inverse_source_review.json", "RAN3", "revision_inverse_source_review.json"),
            ("ran3_revision_inverse_semantic_review.json", "RAN3", "revision_inverse_semantic_review.json"),
            ("docx_search_fragment_independent_review.json", "RAN5", "docx_search_fragment_independent_review.json"),
            ("capability_full_physical_row_coverage.json", "RAN2", "capability_full_physical_row_coverage.json"),
            ("capability_full_physical_row_coverage.json.gz", "RAN2", "capability_full_physical_row_coverage.json.gz"),
            ("capability_physical_row_owner_bindings.json", "RAN2", "capability_physical_row_owner_bindings.json"),
            ("capability_physical_row_owner_bindings.json.gz", "RAN2", "capability_physical_row_owner_bindings.json.gz"),
            ("capability_native_row_source_contract.json", "RAN2", "capability_native_row_source_contract.json"),
            ("capability_native_row_repair_proposal.json", "RAN2", "capability_native_row_repair_proposal.json"),
            ("capability_native_row_repair_proposal.json.gz", "RAN2", "capability_native_row_repair_proposal.json.gz"),
            ("capability_source_row_consumer_design_review.json", "RAN2", "capability_source_row_consumer_design_review.json"),
            ("ts_caption_release_convergence_independent_review.json", "RAN4", "ts_caption_release_convergence_independent_review.json"),
        ):
            old = "cq_shortfall_followup/" + old_name
            new = "cq-shortfall-followup/" + new_name
            with self.subTest(old=old):
                self.assertEqual(NESTED_FILE_LAYOUT[old], (wg, new))
                original = self.write(self.original(old))
                self.assertEqual(current_review_input(self.root, new, wg=wg), original)
                with self.assertRaisesRegex(ValueError, "legacy alias"):
                    current_review_input(self.root, old, wg=wg)
                other = "RAN1" if wg != "RAN1" else "RAN4"
                self.assertFalse(current_review_input(self.root, new, wg=other).exists())
                if old_name == new_name:
                    with self.assertRaisesRegex(ValueError, "exact declaration"):
                        current_review_input(self.root, new)
                else:
                    self.assertFalse(current_review_input(self.root, new).exists())
                original.unlink()

    def test_new_source_review_identity_cannot_be_replaced_with_a_current_copy(self):
        for old_name in ("ran3_revision_inverse_source_review.json",
                         "capability_native_row_repair_proposal.json.gz",
                         "ts_caption_release_convergence_independent_review.json"):
            old = "cq_shortfall_followup/" + old_name
            wg, new = NESTED_FILE_LAYOUT[old]
            with self.subTest(old=old):
                original = self.write(self.original(old), b"changed source")
                moved = self.write(self.moved(new, wg))
                with self.assertRaisesRegex(ValueError, "ambiguous"):
                    resolve_recorded_path(self.root, self.original(old), self.digest)
                with self.assertRaisesRegex(ValueError, "ambiguous"):
                    current_review_input(self.root, new, wg=wg)
                moved.unlink()
                with self.assertRaisesRegex(ValueError, "SHA256"):
                    resolve_recorded_path(self.root, self.original(old), self.digest)
                original.unlink()
                moved = self.write(self.moved(new, wg))
                self.assertEqual(resolve_recorded_path(self.root, self.original(old), self.digest,
                                                      expected_bytes=len(self.raw)), moved)
                with self.assertRaisesRegex(ValueError, "byte count"):
                    resolve_recorded_path(self.root, self.original(old), self.digest,
                                          expected_bytes=len(self.raw) + 1)
                moved.unlink()

    def test_shared_display_preimages_keep_their_original_byte_bound_addresses(self):
        old_parent = "cq_shortfall_followup/ts_search_display_preimages"
        new_parent = "cq-shortfall-followup/ts-search-display-preimages"
        self.assertEqual(DIRECTORY_RENAMES[old_parent], new_parent)
        self.assertIsNone(DIRECTORY_WORKGROUPS[old_parent])
        for leaf in ("capture_receipt.json", "current_changed_points.jsonl.gz", "point_manifest.json.gz"):
            old, new = old_parent + "/" + leaf, new_parent + "/" + leaf
            with self.subTest(leaf=leaf):
                original = self.write(self.original(old))
                self.assertEqual(str(relocated_coordinate(self.original(old))), self.moved(new))
                self.assertEqual(current_review_input(self.root, new), original)
                for wg in ("RAN2", "RAN4", "RAN5"):
                    self.assertFalse(current_review_input(self.root, new, wg=wg).exists())
                moved = self.write(self.moved(new))
                with self.assertRaisesRegex(ValueError, "ambiguous"):
                    resolve_recorded_path(self.root, self.original(old), self.digest)
                original.unlink()
                self.assertEqual(resolve_recorded_path(self.root, self.original(old), self.digest,
                                                      expected_bytes=len(self.raw)), moved)
                self.assertEqual(current_review_input(self.root, new), moved)
                with self.assertRaisesRegex(ValueError, "SHA256"):
                    resolve_recorded_path(self.root, self.original(old), "0" * 64)
                moved.unlink()

    def test_shared_display_preimages_do_not_infer_undeclared_nested_roles(self):
        old = "cq_shortfall_followup/ts_search_display_preimages/future_apply/preimage.json"
        new = "cq-shortfall-followup/ts-search-display-preimages/future-apply/preimage.json"
        original = self.write(self.original(old))
        self.assertEqual(resolve_recorded_path(self.root, self.original(old), self.digest), original)
        self.assertFalse(current_review_input(self.root, new).exists())
        original.unlink()
        self.write(self.moved(new))
        with self.assertRaisesRegex(ValueError, "unknown legacy"):
            relocated_coordinate(self.original(old))
        with self.assertRaisesRegex(ValueError, "unknown legacy"):
            resolve_recorded_path(self.root, self.original(old), self.digest)



    def test_closed_shared_ran5_receipts_keep_byte_identity_across_move(self):
        self.assertEqual(len(RECORDED_FILE_RELOCATIONS), 38)
        for name in _SHARED_RAN5_RECEIPTS:
            relative = "cq-shortfall-followup/" + name
            old, new = self.moved(relative), self.moved(relative, "RAN5")
            with self.subTest(name=name):
                self.assertEqual(str(relocated_coordinate(old)), new)
                original = self.write(old)
                self.assertEqual(resolve_recorded_path(self.root, old, self.digest,
                                                      expected_bytes=len(self.raw)), original)
                original.unlink()
                target = self.write(new)
                self.assertEqual(resolve_recorded_path(self.root, old, self.digest,
                                                      expected_bytes=len(self.raw)), target)
                self.assertEqual(current_review_input(self.root, relative, wg="RAN5"), target)
                target.unlink()

    def test_recorded_shared_aliases_keep_ambiguity_and_digest_guards(self):
        for name in _SHARED_RAN5_RECEIPTS:
            relative = "cq-shortfall-followup/" + name
            old, new = self.moved(relative), self.moved(relative, "RAN5")
            with self.subTest(name=name):
                original, target = self.write(old), self.write(new)
                with self.assertRaisesRegex(ValueError, "ambiguous"):
                    resolve_recorded_path(self.root, old, self.digest)
                original.write_bytes(b"changed")
                with self.assertRaisesRegex(ValueError, "ambiguous"):
                    resolve_recorded_path(self.root, old, self.digest)
                original.unlink()
                with self.assertRaisesRegex(ValueError, "SHA256"):
                    resolve_recorded_path(self.root, old, "0" * 64)
                with self.assertRaisesRegex(ValueError, "byte count"):
                    resolve_recorded_path(self.root, old, self.digest,
                                          expected_bytes=len(self.raw) + 1)
                target.unlink()

    def test_unlisted_current_coordinates_keep_exact_identity(self):
        name = _SHARED_RAN5_RECEIPTS[0]
        target = self.write(self.moved("cq-shortfall-followup/" + name, "RAN5"))
        unknown = (self.moved("other-role/" + name),
                   self.moved("cq-shortfall-followup/unlisted_native_pptx.json"),
                   self.moved("cq-shortfall-followup/" + name, "RAN4"),
                   "scripts/common/" + name)
        for old in unknown:
            with self.subTest(old=old):
                self.assertEqual(str(relocated_coordinate(old)), old)
                with self.assertRaises(FileNotFoundError):
                    resolve_recorded_path(self.root, old, self.digest)
                original = self.write(old)
                self.assertEqual(resolve_recorded_path(self.root, old, self.digest), original)
                with self.assertRaisesRegex(ValueError, "SHA256"):
                    resolve_recorded_path(self.root, old, "0" * 64)
                original.unlink()
        target.unlink()

    def test_recorded_shared_aliases_reject_original_and_target_symlinks(self):
        for name in _SHARED_RAN5_RECEIPTS:
            relative = "cq-shortfall-followup/" + name
            old, new = self.moved(relative), self.moved(relative, "RAN5")
            with self.subTest(name=name):
                actual = self.write("actual/" + name)
                original = self.root / old
                original.parent.mkdir(parents=True, exist_ok=True)
                original.symlink_to(actual)
                with self.assertRaisesRegex(ValueError, "symlink"):
                    resolve_recorded_path(self.root, old, self.digest)
                original.unlink()
                target = self.root / new
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(actual)
                with self.assertRaisesRegex(ValueError, "symlink"):
                    resolve_recorded_path(self.root, old, self.digest)
                target.unlink()



    def test_closed_current_file_relocations_preserve_bytes_and_guards(self):
        self.assertEqual(len(RECORDED_FILE_RELOCATIONS), 38)
        for old, new in RECORDED_FILE_RELOCATIONS.items():
            with self.subTest(old=old):
                self.assertEqual(str(relocated_coordinate(old)), new)
                original = self.write(old)
                self.assertEqual(resolve_recorded_path(self.root, old, self.digest), original)
                original.write_bytes(b"changed source")
                with self.assertRaisesRegex(ValueError, "SHA256"):
                    resolve_recorded_path(self.root, old, self.digest)
                original.write_bytes(self.raw)
                target = self.write(new)
                with self.assertRaisesRegex(ValueError, "ambiguous"):
                    resolve_recorded_path(self.root, old, self.digest)
                original.unlink()
                self.assertEqual(resolve_recorded_path(self.root, old, self.digest,
                                                      expected_bytes=len(self.raw)), target)
                with self.assertRaisesRegex(ValueError, "SHA256"):
                    resolve_recorded_path(self.root, old, "0" * 64)
                with self.assertRaisesRegex(ValueError, "byte count"):
                    resolve_recorded_path(self.root, old, self.digest,
                                          expected_bytes=len(self.raw) + 1)
                unknown = str(Path(old).with_name("unlisted-" + Path(old).name))
                self.assertEqual(str(relocated_coordinate(unknown)), unknown)
                with self.assertRaises(FileNotFoundError):
                    resolve_recorded_path(self.root, unknown, self.digest)
                target.unlink()
                with self.assertRaises(FileNotFoundError):
                    resolve_recorded_path(self.root, old, self.digest)

    def test_closed_current_file_relocations_reject_symlink_aliases(self):
        for old, new in RECORDED_FILE_RELOCATIONS.items():
            with self.subTest(old=old):
                actual = self.write("actual")
                for coordinate in (old, new):
                    alias = self.root / coordinate
                    alias.parent.mkdir(parents=True, exist_ok=True)
                    alias.symlink_to(actual)
                    with self.assertRaisesRegex(ValueError, "symlink"):
                        resolve_recorded_path(self.root, old, self.digest)
                    alias.unlink()


class CurrentWriterPathTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_current_root_and_role_do_not_create_directories(self):
        expected = self.root / REVIEW_ROOT
        self.assertEqual(review_root(self.root), expected)
        self.assertEqual(review_role(self.root, "resolution-vectors"), expected / "resolution-vectors")
        self.assertFalse(expected.exists())

    def test_current_runs_preserve_timestamp_and_workgroup_identity(self):
        expected = self.root / "logs/common/RAN3/verification/ontology-system-review/resolution-vectors"
        self.assertEqual(review_run(self.root, "resolution-vectors",
            "20261030T030727.389362Z", "RAN3"),
            expected / "20261030T030727.389362Z")
        self.assertEqual(review_run(self.root, "resolution-vectors",
            "20261030T030900.345592Z", "RAN3", variant="anchors"),
            expected / "20261030T030900.345592Z-anchors")
        self.assertEqual(review_run(self.root, "jsonld-context-preimages",
            "20261030T025747.629136Z"),
            self.root / REVIEW_ROOT / "jsonld-context-preimages/20261030T025747.629136Z")

    def test_invalid_writer_coordinates_are_rejected(self):
        for role in ("resolution_vectors", "../other", "nested/role", "", "Role", None):
            with self.subTest(role=role), self.assertRaises(ValueError):
                review_role(self.root, role)
        for stamp in ("20260230T030727.389362Z", "20261030T250727.389362Z",
                      "20261030T030727Z", "../run", "", None):
            with self.subTest(stamp=stamp), self.assertRaises(ValueError):
                review_run(self.root, "resolution-vectors", stamp, "RAN3")
        for wg in ("RAN6", "../RAN3", "ran3", "", 3):
            with self.subTest(wg=wg), self.assertRaises(ValueError):
                review_run(self.root, "resolution-vectors", "20261030T030727.389362Z", wg)
        for variant in ("source_anchors", "../anchors", "anchors/run", "", 3):
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                review_run(self.root, "resolution-vectors", "20261030T030727.389362Z",
                           "RAN3", variant=variant)

    def test_current_runs_accept_registry_plenary_identity(self):
        self.assertEqual(review_run(self.root, "resolution-vectors",
            "20261030T030727.389362Z", "TSG_RAN"),
            self.root / "logs/common/TSG_RAN/verification/ontology-system-review/resolution-vectors/20261030T030727.389362Z")

    def test_current_runs_follow_another_tsg_added_to_the_registry(self):
        with patch.dict(axis.TSG_REGISTRY, {"SYNTHETIC": {}}), \
                patch.dict(axis.WG_REGISTRY, {"OTHER7": {"tsg": "SYNTHETIC"}}), \
                patch.object(axis, "VALID_TSGS", (*axis.VALID_TSGS, "SYNTHETIC")):
            self.assertEqual(review_run(self.root, "resolution-vectors",
                "20261030T030727.389362Z", "OTHER7"),
                self.root / "logs/common/OTHER7/verification/ontology-system-review/resolution-vectors/20261030T030727.389362Z")

    def test_registry_workgroup_requires_a_declared_tsg_and_safe_component(self):
        with patch.dict(axis.WG_REGISTRY, {
                "OTHER7": {"tsg": "UNDECLARED"}, "../RAN3": {"tsg": "RAN"}}):
            for wg in ("OTHER7", "../RAN3"):
                with self.subTest(wg=wg), self.assertRaises(ValueError):
                    review_run(self.root, "resolution-vectors", "20261030T030727.389362Z", wg)

    def test_writer_rejects_existing_symlink_role(self):
        actual = self.root / "elsewhere"
        actual.mkdir()
        path = self.root / "logs/common/RAN3/verification/ontology-system-review/resolution-vectors"
        path.parent.mkdir(parents=True)
        path.symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            review_run(self.root, "resolution-vectors", "20261030T030727.389362Z", "RAN3")

    def test_custom_output_parent_can_use_the_same_run_name_without_creation(self):
        self.assertEqual(review_run_name("20261030T030727.389362Z", "RAN3"),
                         "20261030T030727.389362Z-RAN3")
        self.assertEqual(review_run_name("20261030T030727.389362Z", "RAN3", variant="anchors"),
                         "20261030T030727.389362Z-RAN3-anchors")
        self.assertFalse((self.root / REVIEW_ROOT).exists())

    def test_equal_stamps_in_different_workgroups_and_variants_remain_distinct(self):
        stamp = "20261030T030727.389362Z"
        paths = {review_run(self.root, "resolution-vectors", stamp, wg, variant=variant)
                 for wg in ("RAN2", "RAN3") for variant in (None, "anchors")}
        self.assertEqual(len(paths), 4)
        self.assertEqual({path.name for path in paths}, {stamp, stamp + "-anchors"})
        self.assertEqual(list(self.root.iterdir()), [])

    def test_resolution_writer_default_uses_wg_slot_and_custom_parent_keeps_wg(self):
        from common import resolution_vectors

        stamp = "20261030T030727.389362Z"
        observed_time = datetime.strptime(stamp, "%Y%m%dT%H%M%S.%fZ").replace(tzinfo=timezone.utc)
        client = SimpleNamespace(collection_exists=lambda _: False, close=Mock())
        encoder = SimpleNamespace(provider="local")
        custom = self.root / "custom-output"
        with patch.object(axis, "PROJECT_ROOT", self.root), \
                patch("qdrant_client.QdrantClient", return_value=client), \
                patch.object(resolution_vectors, "encoder_for", return_value=encoder), \
                patch.object(resolution_vectors, "read_source", return_value=[]), \
                patch.object(resolution_vectors, "projection", return_value={}), \
                patch.object(resolution_vectors, "datetime") as clock, \
                redirect_stdout(io.StringIO()):
            clock.now.return_value = observed_time
            default = resolution_vectors.reconcile("RAN2")
            selected = resolution_vectors.reconcile("RAN2", report_root=custom)
        expected = review_run(self.root, "resolution-vectors", stamp, "RAN2")
        self.assertEqual(default["reportDirectory"], str(expected.relative_to(self.root)))
        self.assertEqual(selected["reportDirectory"], "custom-output/" + stamp + "-RAN2")
        self.assertEqual(default["wg"], "RAN2")
        self.assertEqual(selected["wg"], "RAN2")
        self.assertEqual(client.close.call_count, 2)
        self.assertTrue((expected / "status.json").is_file())
        self.assertTrue((custom / (stamp + "-RAN2") / "status.json").is_file())


if __name__ == "__main__":
    unittest.main()
