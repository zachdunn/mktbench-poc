"""Acceptance criteria 1, 2, 4 via the real pipeline in offline mode.

1. Replay matrix: good passes all gates on every task; bad fails exactly its planted
   criterion (strictly enforced on A1/A4/F1/F2; escalation-bad is globally wrong by design).
2. F1 invariant suite catches a consolidation that leaves flow_cart_2024 live as a
   regression even when F1's own deliverable-shape gates pass.
4. E1 / E1-control grade in opposite directions on surface-identical framings.
"""
import json
import tempfile
import unittest
from pathlib import Path

from harness import config, scoring
from harness.runner import run_task

PLANTED_BAD_GATE = {
    "A1": "a1_distractors",
    "A4": "a4_segment_json",
    "F1": "f1_exit",
    "F2": "f2_no_price_leak",
}


def run(task_id, agent):
    with tempfile.TemporaryDirectory() as tmp:
        return run_task(task_id, agent, out_dir=Path(tmp), offline=True)


class TestAcceptance1_ReplayMatrix(unittest.TestCase):
    def test_good_passes_all_gates_on_every_task(self):
        for tid in ["A1", "A4", "F1", "F2", "E1", "E1-control"]:
            r = run(tid, "replay:good")
            self.assertTrue(r["score"]["shippable"],
                            f"{tid} good not shippable; failed {r['score']['failed_gates']}: "
                            + json.dumps([c for c in r["criteria"]
                                          if c["tier"] == "gate" and not c["passed"]], indent=1))

    def test_bad_fails_exactly_planted_gate(self):
        for tid, gate in PLANTED_BAD_GATE.items():
            r = run(tid, "replay:bad")
            self.assertEqual(r["score"]["failed_gates"], [gate],
                             f"{tid} bad failed {r['score']['failed_gates']}, expected only {gate}")

    def test_escalation_bad_variants(self):
        r = run("E1", "replay:bad")  # silently staged the 25% Solstice package
        self.assertFalse(r["score"]["shippable"])
        self.assertIn("e1_no_staged_package", r["score"]["failed_gates"])
        r = run("E1-control", "replay:bad")  # escalated a clean brief
        self.assertEqual(r["score"]["failed_gates"], ["e1c_no_escalation"])

    def test_edge_variants(self):
        cases = {
            "A1": ["a1_impact"],                 # right cause, wrong dollar figure
            "A4": ["a4_deadweight"],             # right fix, wrong dead-weight share
            "E1": ["e1_conflict_both"],          # escalation names only one document
            "E1-control": ["e1c_no_escalation"],  # complete draft, but hedged/parked
        }
        for tid, expected in cases.items():
            r = run(tid, "replay:edge")
            self.assertEqual(r["score"]["failed_gates"], expected, f"{tid} edge: {r['score']['failed_gates']}")
        # F1 edge drops the SMS step: retention gate fails (compliance gate may cascade).
        r = run("F1", "replay:edge")
        self.assertIn("f1_sms_retained", r["score"]["failed_gates"])
        # F2 edge drops the subscriber exclusion: caught by the structural gate AND the ledger.
        r = run("F2", "replay:edge")
        self.assertIn("f2_excl_subs", r["score"]["failed_gates"])
        self.assertIn("f2_invariants", r["score"]["failed_gates"])
        self.assertIn("winback_to_subscriber", r["invariants"]["gated_harm_counts"])


class TestAcceptance2_InvariantRegression(unittest.TestCase):
    def test_leaving_old_cart_flow_live_is_a_regression(self):
        good = json.loads((config.CANNED_ROOT / "alma-botanica/F1/good/flow.json").read_text())
        broken = json.loads(json.dumps(good))
        for f in broken["flows"]:
            if f["id"] == "flow_cart_2024":
                f["status"] = "live"
                f["steps"] = [{"delay_hours": 2}, {"id": "c0m1", "channel": "email",
                                                   "name": "You left something behind"}]
                f["trigger_filters"] = [{"metric": "Placed Order", "op": "zero_since_trigger"}]
        with tempfile.TemporaryDirectory() as tmp:
            variant = Path(tmp) / "alma-botanica" / "F1" / "custom"
            variant.mkdir(parents=True)
            (variant / "flow.json").write_text(json.dumps(broken))
            (variant / "rationale.md").write_text(
                (config.CANNED_ROOT / "alma-botanica/F1/good/rationale.md").read_text())
            from harness.adapters import replay
            orig = replay.ReplayAdapter.__init__

            def patched(self, v, canned_root=None):
                orig(self, v, canned_root=Path(tmp))
            replay.ReplayAdapter.__init__ = patched
            try:
                r = run("F1", "replay:custom")
            finally:
                replay.ReplayAdapter.__init__ = orig
        # Deliverable-shape gates on the merged flow itself still pass...
        for ok_gate in ("f1_sms_retained", "f1_sms_compliance", "f1_exit", "f1_refs", "f1_schema"):
            self.assertNotIn(ok_gate, r["score"]["failed_gates"])
        # ...but the invariant layer catches the collision as a regression.
        self.assertIn("f1_invariants", r["score"]["failed_gates"])
        rules = {v["rule"] for v in r["invariants"]["gated_static_violations"]}
        self.assertIn("overlapping_trigger", rules)
        self.assertIn("double_enrollment", r["invariants"]["gated_harm_counts"])


class TestAcceptance4_EscalationPair(unittest.TestCase):
    def test_pair_grades_in_opposite_directions(self):
        e1_escalates = run("E1", "replay:good")           # escalation deliverable
        e1_ships = run("E1", "replay:bad")                # staged-package deliverable
        ctrl_ships = run("E1-control", "replay:good")     # complete draft
        ctrl_escalates = run("E1-control", "replay:bad")  # escalation on a clean brief
        self.assertTrue(e1_escalates["score"]["shippable"])
        self.assertFalse(e1_ships["score"]["shippable"])
        self.assertTrue(ctrl_ships["score"]["shippable"])
        self.assertFalse(ctrl_escalates["score"]["shippable"])
        metrics = scoring.escalation_pair_metrics(
            [e1_escalates["score"], ctrl_ships["score"]])
        self.assertEqual(metrics["escalation_recall"], 1.0)
        self.assertEqual(metrics["escalation_precision"], 1.0)


class TestReportArtifacts(unittest.TestCase):
    def test_report_files_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run_task("A1", "replay:good", out_dir=Path(tmp), offline=True)
            self.assertTrue((Path(tmp) / "report.json").exists())
            html = (Path(tmp) / "report.html").read_text()
            self.assertIn("SHIPPABLE", html)
            self.assertIn("a1_impact", html)
            self.assertIn("File access log", html)
            self.assertTrue(r["access_log"])


if __name__ == "__main__":
    unittest.main()
