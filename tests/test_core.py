"""Task loading, segment engine vs answer key, ledger determinism (acceptance 3)."""
import json
import unittest

from harness import config, segment_engine
from harness.endstate import materialize, parse_flow_deliverable
from harness.ledger import simulate
from harness.taskspec import TaskSpecError, load_task, load_task_by_id
from harness.universe import Universe

UNIVERSE = Universe(config.UNIVERSES_ROOT / "alma-botanica")
ALL_TASKS = ["A1", "A4", "F1", "F2", "E1", "E1-control"]


class TestTaskSpecs(unittest.TestCase):
    def test_all_tasks_load(self):
        for tid in ALL_TASKS:
            task = load_task_by_id(tid)
            self.assertEqual(task.id, tid)
            self.assertTrue(task.gate_criteria(), f"{tid} has no gate criteria")

    def test_evidence_files_exist_outside_blocked_dirs(self):
        for tid in ALL_TASKS:
            task = load_task_by_id(tid)
            for c in task.criteria:
                for rel in c.evidence_files:
                    self.assertFalse(rel.startswith(("answer_key", "gen")), f"{tid}/{c.id}: {rel}")
                    self.assertTrue((UNIVERSE.root / rel).exists(), f"{tid}/{c.id}: missing {rel}")
            for rel in task.files_in_scope:
                self.assertTrue((UNIVERSE.root / rel).exists(), f"{tid}: missing in-scope {rel}")

    def test_invalid_tier_rejected(self):
        import tempfile
        from pathlib import Path
        bad = {"id": "X", "universe": "u", "instructions": "i",
               "deliverable": {"kind": "memo"},
               "criteria": [{"id": "c1", "tier": "sorta", "method": "computed"}]}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(bad, f)
        with self.assertRaises(TaskSpecError):
            load_task(Path(f.name))


class TestSegmentEngine(unittest.TestCase):
    def test_vip_counts_match_answer_key(self):
        key = UNIVERSE.answer_key()
        vips = segment_engine.audience(UNIVERSE.segment_by_id("seg_vips")["definition"], UNIVERSE.profiles)
        self.assertEqual(len(vips), key["vip_sample_count"])
        rot = [p for p in vips if p.engagement_tier == "unengaged_12m" or p.suppressed]
        self.assertEqual(len(rot), key["vip_rot_count"])

    def test_naive_winback_count_matches_answer_key(self):
        key = UNIVERSE.answer_key()
        naive = [p for p in UNIVERSE.profiles
                 if segment_engine.eval_condition(
                     {"metric": "last_onetime_order_date", "op": "older_than_days", "value": 90}, p)
                 and p.engagement_tier != "unengaged_12m" and not p.suppressed]
        self.assertEqual(len(naive), key["winback_naive_audience_sample"])


class TestLedger(unittest.TestCase):
    def test_deterministic(self):
        """Acceptance 3: same end-state ⇒ byte-identical ledger."""
        a = simulate(UNIVERSE.flows, UNIVERSE)
        b = simulate(UNIVERSE.flows, UNIVERSE)
        self.assertEqual(a.fingerprint(), b.fingerprint())
        self.assertTrue(a.sends)

    def test_baseline_carries_planted_harms(self):
        led = simulate(UNIVERSE.flows, UNIVERSE)
        counts = led.counts_by_type()
        self.assertIn("double_enrollment", counts)       # cart collision (issue #1)
        self.assertIn("winback_to_subscriber", counts)   # issue #2
        self.assertIn("sms_quiet_hours", counts)         # issue #5 (account-tz basis)

    def test_consolidation_removes_double_enrollment(self):
        good = parse_flow_deliverable(
            (config.CANNED_ROOT / "alma-botanica" / "F1" / "good" / "flow.json").read_text())
        end = materialize(UNIVERSE.flows, good)
        led = simulate(end, UNIVERSE)
        cart_doubles = [e for e in led.harm_events
                        if e.type == "double_enrollment" and "cart" in e.flow_id]
        self.assertEqual(cart_doubles, [])


if __name__ == "__main__":
    unittest.main()
