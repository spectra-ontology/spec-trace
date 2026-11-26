#!/usr/bin/env python3
"""Adversarial CQ input and projection checks, using a supplied release fixture."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

parser = argparse.ArgumentParser()
parser.add_argument("--release", type=Path, required=True)
args, unittest_args = parser.parse_known_args()
fixture = args.release.resolve()
sys.path.insert(0, str(fixture / "restore/competency_queries"))
from runner import verify, classify, canonical_digest
from graph_snapshot import dependencies, encode, decode


class ContractChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="spectra-cq-contract-")
        self.root = Path(self.temporary.name)
        source = fixture / "sources/competency_queries/contract.json"
        self.contract = json.loads(source.read_text())
        paths = ["sources/competency_queries/contract.json", *[a["path"] for a in self.contract["artifacts"]]]
        for path in paths:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fixture / path, target)

    def tearDown(self):
        self.temporary.cleanup()

    def test_complete_contract(self):
        _, _, summary = verify(self.root)
        self.assertEqual(summary["questions"], 654)
        self.assertEqual(summary["historical_query_bindings"], {"exact_text_match": 149, "query_text_unrecorded": 505})

    def test_missing_definition_fails(self):
        (self.root / self.contract["datasets"][0]["definition_path"]).unlink()
        with self.assertRaisesRegex(ValueError, "Missing CQ artifact"):
            verify(self.root)

    def test_guard_edit_fails(self):
        path = self.root / self.contract["guard"]["path"]
        path.write_text(path.read_text() + "\n# changed guard\n")
        with self.assertRaisesRegex(ValueError, "digest/size differs"):
            verify(self.root)

    def test_assertion_edit_fails_even_after_file_repin(self):
        item = self.contract["datasets"][0]
        path = self.root / item["definition_path"]
        data = json.loads(path.read_text())
        data["questions"][0]["expected_min_rows"] = 1000000
        path.write_text(json.dumps(data))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        item["definition_sha256"] = digest
        item["historical_dataset_binding"] = {"recorded_sha256_prefix": digest[:16], "status": "recorded_prefix_matches"}
        # Keep the old receipt pin intact: a definition edit must not silently rewrite historical evidence.
        for artifact in self.contract["artifacts"]:
            if artifact["path"] == item["definition_path"]:
                artifact.update(sha256=digest, bytes=path.stat().st_size)
        (self.root / "sources/competency_queries/contract.json").write_text(json.dumps(self.contract))
        with self.assertRaisesRegex(ValueError, "Historical dataset digest binding differs|declared assertions differ"):
            verify(self.root)

    def test_projection_rejects_dynamic_property(self):
        contract, datasets, _ = verify(self.root)
        datasets = copy.deepcopy(datasets)
        datasets[0][1][0]["cypher"] = "MATCH (n) RETURN n[$property] AS value"
        with self.assertRaisesRegex(ValueError, "Dynamic graph property access"):
            dependencies(self.root, contract, datasets)

    def test_projection_rejects_whole_properties(self):
        contract, datasets, _ = verify(self.root)
        datasets = copy.deepcopy(datasets)
        datasets[0][1][0]["cypher"] = "MATCH (n) RETURN properties(n) AS value"
        with self.assertRaisesRegex(ValueError, "Whole-property"):
            dependencies(self.root, contract, datasets)

    def test_projection_rejects_entity_alias_return(self):
        contract, datasets, _ = verify(self.root)
        for query in ("MATCH (n) WITH n AS x RETURN x",
                      "MATCH (n) WITH n AS x WITH x AS y RETURN y",
                      "MATCH (n) WITH collect(n)[0] AS x RETURN x",
                      "MATCH ()-[r]->() WITH r AS x RETURN x"):
            with self.subTest(query=query):
                changed = copy.deepcopy(datasets)
                changed[0][1][0]["cypher"] = query
                with self.assertRaisesRegex(ValueError, "Whole graph entity"):
                    dependencies(self.root, contract, changed)

    def test_projection_rejects_nested_entity_map(self):
        contract, datasets, _ = verify(self.root)
        for query in ("MATCH (n) RETURN {entity:n} AS value",
                      "MATCH (n) WITH {entity:n} AS value RETURN value"):
            with self.subTest(query=query):
                changed = copy.deepcopy(datasets)
                changed[0][1][0]["cypher"] = query
                with self.assertRaisesRegex(ValueError, "Whole graph entity"):
                    dependencies(self.root, contract, changed)

    def test_projection_rejects_nested_entity_list(self):
        contract, datasets, _ = verify(self.root)
        for query in ("MATCH (n) RETURN [n] AS value",
                      "MATCH p=(n)-->(m) RETURN [x IN nodes(p) | x] AS value",
                      "MATCH (n) UNWIND [n] AS x RETURN x",
                      "MATCH (n) RETURN *"):
            with self.subTest(query=query):
                changed = copy.deepcopy(datasets)
                changed[0][1][0]["cypher"] = query
                with self.assertRaisesRegex(ValueError, "Whole graph entity"):
                    dependencies(self.root, contract, changed)

    def test_projection_rejects_alias_dynamic_property(self):
        contract, datasets, _ = verify(self.root)
        changed = copy.deepcopy(datasets)
        changed[0][1][0]["cypher"] = "MATCH (n) WITH n AS x RETURN x['unlistedProperty'] AS value"
        with self.assertRaisesRegex(ValueError, "Dynamic graph property access"):
            dependencies(self.root, contract, changed)

    def test_current_projection_matches_every_captured_view(self):
        contract, datasets, _ = verify(self.root)
        actual = dependencies(self.root, contract, datasets)
        for view in contract["graph_views"]:
            with self.subTest(working_group=view["working_group"]):
                captured = json.loads((self.root / view["manifest_path"]).read_text())
                self.assertEqual(actual, captured["dependency"])

    def test_projection_retains_explicit_alias_and_path_properties(self):
        contract, datasets, _ = verify(self.root)
        for query, expected in (("MATCH (n) WITH n AS x RETURN x.title AS value", ["title"]),
                                ("MATCH p=(n)-->(m) RETURN [x IN nodes(p) | x.sectionId] AS value", ["sectionId"])):
            with self.subTest(query=query):
                changed = copy.deepcopy(datasets)
                changed[0][1][0]["cypher"] = query
                actual = dependencies(self.root, contract, changed)
                self.assertEqual(actual["questions"][0]["properties"], expected)

    def test_projection_rejects_unproven_text_property_forms(self):
        contract, datasets, _ = verify(self.root)
        for query in ("MATCH (c:Company) RETURN c . content AS value",
                      "MATCH (c:Company) RETURN c . `contentWithEquations` AS value",
                      "MATCH (c:Company {content:'x'}) RETURN c.companyName AS value",
                      "MATCH ()-[r:TYPE {`content`:'x'}]->() RETURN count(r) AS value"):
            with self.subTest(query=query):
                changed = copy.deepcopy(datasets)
                changed[0][1][0]["cypher"] = query
                with self.assertRaisesRegex(ValueError, "[Tt]ext property"):
                    dependencies(self.root, contract, changed)

    def test_projection_retains_proven_text_property_forms(self):
        contract, datasets, _ = verify(self.root)
        for query, expected in (("MATCH (r:Resolution) RETURN r . `content` AS value", ["content"]),
                                ("MATCH (r:Resolution {`content`:'x'}) RETURN r.resolutionId AS value", ["content", "resolutionId"])):
            with self.subTest(query=query):
                changed = copy.deepcopy(datasets)
                changed[0][1][0]["cypher"] = query
                actual = dependencies(self.root, contract, changed)
                self.assertEqual(actual["questions"][0]["properties"], expected)

    def test_sidecar_missing_fails(self):
        (self.root / self.contract["graph_views"][0]["definition_binding_path"]).unlink()
        with self.assertRaisesRegex(ValueError, "Missing CQ artifact"):
            verify(self.root)

    def test_recorded_queries_cannot_be_repinned_to_different_inputs(self):
        view = self.contract["graph_views"][0]
        path = self.root / view["manifest_path"]
        manifest = json.loads(path.read_text())
        manifest["dependency"]["questions"][0]["query_sha256"] = "0" * 64
        path.write_text(json.dumps(manifest))
        view["manifest_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        sidecar_path = self.root / view["definition_binding_path"]
        sidecar = json.loads(sidecar_path.read_text())
        sidecar["snapshot_manifest_sha256"] = view["manifest_sha256"]
        sidecar["dependency_sha256"] = canonical_digest(manifest["dependency"])
        sidecar["captured_query_identity_sha256"] = canonical_digest([
            {key: row[key] for key in ("key", "query_sha256")}
            for row in manifest["dependency"]["questions"]])
        sidecar_path.write_text(json.dumps(sidecar))
        view["definition_binding_sha256"] = hashlib.sha256(sidecar_path.read_bytes()).hexdigest()
        for artifact in self.contract["artifacts"]:
            if artifact["path"] in (view["manifest_path"], view["definition_binding_path"]):
                changed = self.root / artifact["path"]
                artifact.update(sha256=hashlib.sha256(changed.read_bytes()).hexdigest(), bytes=changed.stat().st_size)
        (self.root / "sources/competency_queries/contract.json").write_text(json.dumps(self.contract))
        with self.assertRaisesRegex(ValueError, "graph/definition dependency binding differs"):
            verify(self.root)

    def test_known_schema_tokens_require_recorded_observations(self):
        view = self.contract["graph_views"][0]
        sidecar_path = self.root / view["definition_binding_path"]
        sidecar = json.loads(sidecar_path.read_text())
        observation_path = self.root / sidecar["schema_token_observations"]["path"]
        observation = json.loads(observation_path.read_text())
        observation["known_tokens"]["labels"].append("InventedToken")
        observation_path.write_text(json.dumps(observation))
        sidecar["schema_token_observations"]["sha256"] = hashlib.sha256(observation_path.read_bytes()).hexdigest()
        sidecar_path.write_text(json.dumps(sidecar))
        view["definition_binding_sha256"] = hashlib.sha256(sidecar_path.read_bytes()).hexdigest()
        for artifact in self.contract["artifacts"]:
            if artifact["path"] in (view["definition_binding_path"], sidecar["schema_token_observations"]["path"]):
                changed = self.root / artifact["path"]
                artifact.update(sha256=hashlib.sha256(changed.read_bytes()).hexdigest(), bytes=changed.stat().st_size)
        (self.root / "sources/competency_queries/contract.json").write_text(json.dumps(self.contract))
        with self.assertRaisesRegex(ValueError, "schema-token observation binding differs"):
            verify(self.root)

    def test_typed_property_roundtrip(self):
        from neo4j.time import Date, DateTime, Time, Duration
        from neo4j.spatial import CartesianPoint, WGS84Point
        values = [True, 3, 2.5, "x", [1, 2], Date(2026, 1, 2), Time(1, 2, 3),
                  DateTime(2026, 1, 2, 3, 4, 5), Duration(months=1, days=2, seconds=3, nanoseconds=4),
                  CartesianPoint((1, 2)), WGS84Point((127, 37)), b"abc"]
        for value in values:
            with self.subTest(kind=type(value).__name__):
                restored = decode(encode(value))
                self.assertEqual(type(restored), type(value))
                self.assertEqual(restored, value)

    def test_empty_result_obeys_declared_minimum(self):
        self.assertEqual(classify(0, {"expected_min_rows": 0, "allow_zero": True}, []), "PASS")
        self.assertEqual(classify(0, {}, []), "NO_DATA")
        self.assertEqual(classify(0, {"expected_min_rows": 1}, []), "FAIL")
        self.assertEqual(classify(1, {"expected_min_rows": 2}, []), "FAIL")
        self.assertEqual(classify(0, {"expected_min_rows": 0}, ["guard defect"]), "FAIL")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0], *unittest_args])
