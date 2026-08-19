"""Run/grade phase split: re-grading a saved run reproduces the score without re-running
the agent, and pre-split runs (report.json only) can still be re-graded."""
import json
import tempfile
import unittest
from pathlib import Path

from harness.runner import execute_task, grade_run, run_task


class TestRegrade(unittest.TestCase):
    def test_execute_persists_grading_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = execute_task("A1", "replay:good", out_dir=Path(tmp))
            self.assertTrue((run_dir / "deliverable.json").exists())
            self.assertTrue((run_dir / "access_log.json").exists())
            self.assertFalse((run_dir / "report.json").exists())  # grading hasn't happened yet
            saved = json.loads((run_dir / "deliverable.json").read_text())
            self.assertEqual(saved["task_id"], "A1")
            self.assertIn("memo.md", saved["parts"])

    def test_regrade_reproduces_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = run_task("F1", "replay:bad", out_dir=Path(tmp), offline=True)
            again = grade_run(Path(tmp), offline=True)
            self.assertEqual(first["score"], again["score"])
            self.assertEqual(again["score"]["failed_gates"], ["f1_exit"])
            self.assertIsNotNone(again["graded_at"])

    def test_regrade_from_legacy_report_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_task("A1", "replay:good", out_dir=Path(tmp), offline=True)
            (Path(tmp) / "deliverable.json").unlink()
            (Path(tmp) / "access_log.json").unlink()
            report = grade_run(Path(tmp), offline=True)
            self.assertTrue(report["score"]["shippable"])

    def test_regrade_missing_run_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                grade_run(Path(tmp) / "nope")


if __name__ == "__main__":
    unittest.main()
