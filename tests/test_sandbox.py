"""Acceptance 6: answer_key/ and gen/ are demonstrably unreachable from the sandbox."""
import tempfile
import unittest
from pathlib import Path

from harness import config
from harness.sandbox import Sandbox, SandboxAccessError

UNIVERSE = config.UNIVERSES_ROOT / "alma-botanica"


class TestSandbox(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.sb = Sandbox(UNIVERSE, Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_answer_key_not_copied(self):
        files = self.sb.list_files()
        self.assertTrue(files)
        for f in files:
            self.assertNotIn("answer_key", f)
            self.assertNotIn("gen/", f)

    def test_answer_key_read_blocked(self):
        for path in ("answer_key/computed_values.json", "answer_key/answer_key.md",
                     "gen/gen_alma.py"):
            with self.assertRaises((SandboxAccessError, FileNotFoundError)):
                self.sb.read_file(path)

    def test_escape_blocked(self):
        for path in ("../../universes/alma-botanica/answer_key/computed_values.json",
                     "../sandbox/../../x", "/etc/passwd",
                     "flows/../../../universes/alma-botanica/answer_key/answer_key.md"):
            with self.assertRaises((SandboxAccessError, FileNotFoundError)):
                self.sb.read_file(path)

    def test_reads_logged(self):
        self.sb.read_file("flows/flows.json")
        self.assertEqual(self.sb.access_log[-1]["path"], "flows/flows.json")
        self.assertTrue(self.sb.access_log[-1]["ok"])

    def test_allowed_read_works(self):
        content = self.sb.read_file("crm/segments.json")
        self.assertIn("seg_vips", content)


if __name__ == "__main__":
    unittest.main()
