"""Prediction endpoint regressions using 560 synthetic local records.

All command-line files are temporary. No synthetic measurement is evidence of
model performance, domain truth, or completion of the actual Core benchmark.
"""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
import score_predictions


def synthetic_fixture():
    tasks, gold, predictions = [], [], []
    for index in range(560):
        identity = f"RAN5_SYNTHETIC_{index:03d}"
        definition = hashlib.sha256(f"synthetic-definition-{index}".encode()).hexdigest()
        tasks.append({"id": identity, "definition_sha256": definition,
                      "validation_status": "validated",
                      "required_fields": [{"name": "count", "type": "integer"}],
                      "collection": {"kind": "set"}, "cardinality_policy": {"mode": "all"}})
        gold.append({"id": identity, "definition_sha256": definition,
                     "validation_status": "validated", "records": [{"count": 1}]})
        predictions.append({"id": identity, "definition_sha256": definition,
                            "status": "answer", "records": [{"count": 1}]})
    return tasks, gold, predictions


class PredictionPopulationTests(unittest.TestCase):
    def setUp(self):
        self.tasks, self.gold, self.predictions = synthetic_fixture()

    def evaluate(self):
        return score_predictions.evaluate(self.tasks, self.gold, self.predictions)

    def test_matching_full_population_is_scored_without_expert_claims(self):
        result = self.evaluate()
        self.assertEqual(result["n"], 560)
        self.assertEqual(result["exact"], 1.0)
        self.assertEqual(result["macro_f1"], 1.0)
        self.assertFalse(result["external_truth_or_expert_validation"])
        self.assertFalse(result["prediction_generation_provenance_certified"])

    def test_duplicate_task_gold_or_prediction_is_rejected(self):
        for source in [self.tasks, self.gold, self.predictions]:
            source.append(copy.deepcopy(source[0]))
            with self.subTest(population=source[0].keys()), self.assertRaises(ValueError):
                self.evaluate()
            source.pop()

    def test_foreign_prediction_or_gold_identity_is_rejected(self):
        for source in [self.gold, self.predictions]:
            saved = source[0]["id"]
            source[0]["id"] = "RAN5_FOREIGN"
            with self.subTest(population=source[0].keys()), self.assertRaises(ValueError):
                self.evaluate()
            source[0]["id"] = saved

    def test_missing_prediction_is_rejected(self):
        self.predictions.pop()
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_matching_but_incomplete_populations_are_rejected(self):
        self.tasks.pop(); self.gold.pop(); self.predictions.pop()
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_stale_gold_or_prediction_definition_is_rejected(self):
        for source in [self.gold, self.predictions]:
            saved = source[0]["definition_sha256"]
            source[0]["definition_sha256"] = "0" * 64
            with self.subTest(population=source[0].keys()), self.assertRaises(ValueError):
                self.evaluate()
            source[0]["definition_sha256"] = saved

    def test_missing_prediction_definition_is_rejected(self):
        del self.predictions[0]["definition_sha256"]
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_missing_or_pending_task_and_reference_status_is_rejected(self):
        for source in [self.tasks, self.gold]:
            for state in [None, "pending", "quarantined"]:
                if state is None:
                    source[0].pop("validation_status", None)
                else:
                    source[0]["validation_status"] = state
                with self.subTest(population=source[0].keys(), state=state), self.assertRaises(ValueError):
                    self.evaluate()
                source[0]["validation_status"] = "validated"

    def test_missing_or_unknown_prediction_status_is_rejected(self):
        for state in [None, "missing", "ANSWER"]:
            if state is None:
                self.predictions[0].pop("status", None)
            else:
                self.predictions[0]["status"] = state
            with self.subTest(state=state), self.assertRaises(ValueError):
                self.evaluate()

    def test_answer_requires_records_list(self):
        for value in [None, {}, "[]"]:
            self.predictions[0]["records"] = value
            with self.subTest(records=value), self.assertRaises(ValueError):
                self.evaluate()
        self.predictions[0].pop("records")
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_abstain_requires_explicit_null_not_empty_or_nonempty_records(self):
        self.predictions[0]["status"] = "abstain"
        for value in [[], [{"count": 1}], {}]:
            self.predictions[0]["records"] = value
            with self.subTest(records=value), self.assertRaises(ValueError):
                self.evaluate()
        self.predictions[0].pop("records")
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_formal_empty_answer_and_empty_reference_abstention_differ(self):
        self.gold[0]["records"] = []
        self.predictions[0]["records"] = []
        self.assertTrue(self.evaluate()["items"][0]["exact"])
        self.predictions[0].update(status="abstain", records=None)
        result = self.evaluate()
        self.assertFalse(result["items"][0]["exact"])
        self.assertEqual(result["items"][0]["f1"], 0.0)
        self.assertEqual(result["explicit_abstentions"], 1)
        self.assertEqual(result["exact"], 559 / 560)

    def test_abstention_does_not_hide_invalid_reference(self):
        self.gold[0]["records"] = [{"count": "1"}]
        self.predictions[0].update(status="abstain", records=None)
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_abstention_does_not_hide_invalid_reference_cardinality(self):
        self.tasks[0]["cardinality_policy"] = {"mode": "exact", "value": 2}
        self.predictions[0].update(status="abstain", records=None)
        with self.assertRaises(ValueError):
            self.evaluate()


class PredictionCommandTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="spectracq-cli-test-")
        self.addCleanup(self.scratch.cleanup)
        self.base = Path(self.scratch.name)
        self.tasks, self.gold, self.predictions = synthetic_fixture()
        (self.base / "scorer.py").write_bytes((score_predictions.BASE / "scorer.py").read_bytes())
        self.prediction_path = self.base / "predictions.jsonl"
        self.output_path = self.base / "results.json"
        context = patch.object(score_predictions, "BASE", self.base)
        context.start()
        self.addCleanup(context.stop)

    def write_inputs(self):
        for path, records in [(self.base / "canonical_tasks.jsonl", self.tasks),
                              (self.base / "canonical_reference_gold.jsonl", self.gold),
                              (self.prediction_path, self.predictions)]:
            path.write_text("".join(json.dumps(record) + "\n" for record in records))

    def run_cli(self, smoke=False, output=None):
        self.write_inputs()
        argv = ["score_predictions.py", "--predictions", str(self.prediction_path),
                "--output", str(output or self.output_path)]
        if smoke:
            argv.append("--reference-contract-check")
        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            score_predictions.main()

    def test_reference_smoke_is_explicitly_labelled_not_model_performance(self):
        self.run_cli(smoke=True)
        result = json.loads(self.output_path.read_text())
        self.assertIn("not model performance", result["kind"])
        self.assertEqual(result["n"], 560)
        self.assertFalse(result["prediction_generation_provenance_certified"])
        self.assertEqual(result["input_sha256"], hashlib.sha256(self.prediction_path.read_bytes()).hexdigest())
        self.assertEqual(result["canonical_tasks_sha256"], hashlib.sha256(
            (self.base / "canonical_tasks.jsonl").read_bytes()).hexdigest())
        self.assertEqual(result["canonical_reference_gold_sha256"], hashlib.sha256(
            (self.base / "canonical_reference_gold.jsonl").read_bytes()).hexdigest())

    def test_snapshot_hash_describes_the_parsed_bytes(self):
        raw = b'{"id":"synthetic-one","value":1}\n'
        self.prediction_path.write_bytes(raw)
        parsed, digest = score_predictions.load_snapshot(self.prediction_path)
        self.prediction_path.write_bytes(b'{"id":"different-after-load","value":2}\n')
        self.assertEqual(parsed, [{"id": "synthetic-one", "value": 1}])
        self.assertEqual(digest, hashlib.sha256(raw).hexdigest())
        self.assertNotEqual(digest, hashlib.sha256(self.prediction_path.read_bytes()).hexdigest())

    def test_ordinary_supplied_scores_do_not_certify_generation_provenance(self):
        self.run_cli()
        result = json.loads(self.output_path.read_text())
        self.assertIn("generation provenance", result["kind"])
        self.assertFalse(result["prediction_generation_provenance_certified"])

    def test_reference_smoke_rejects_nonreference_answer_and_abstention(self):
        self.predictions[0]["records"] = [{"count": 2}]
        with self.assertRaises(ValueError):
            self.run_cli(smoke=True)
        self.predictions[0].update(status="abstain", records=None)
        with self.assertRaises(ValueError):
            self.run_cli(smoke=True)
        self.assertFalse(self.output_path.exists())

    def test_reference_smoke_does_not_confuse_boolean_with_integer(self):
        self.predictions[0]["records"] = [{"count": True}]
        with self.assertRaises(ValueError):
            self.run_cli(smoke=True)
        self.assertFalse(self.output_path.exists())

    def test_cli_rejects_duplicate_json_keys(self):
        self.write_inputs()
        self.prediction_path.write_text(self.prediction_path.read_text().replace(
            '"status": "answer"', '"status": "answer", "status": "abstain"', 1))
        argv = ["score_predictions.py", "--predictions", str(self.prediction_path),
                "--output", str(self.output_path)]
        with patch.object(sys, "argv", argv), self.assertRaises(ValueError):
            score_predictions.main()
        self.assertFalse(self.output_path.exists())

    def test_cli_cannot_overwrite_predictions_tasks_or_reference(self):
        for output in [self.prediction_path, self.base / "canonical_tasks.jsonl",
                       self.base / "canonical_reference_gold.jsonl"]:
            with self.subTest(output=output.name), self.assertRaises(ValueError):
                self.run_cli(output=output)


if __name__ == "__main__":
    unittest.main()
