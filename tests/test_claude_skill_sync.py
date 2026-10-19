"""Claude registration must stay aligned without overwriting local user skills."""

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "sync_claude_skills.py"


class ClaudeSkillSync(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / ".agents/skills/job-scraper/SKILL.md"
        self.source.parent.mkdir(parents=True)
        self.source.write_text(
            "---\nname: scrape\ndescription: >\n  Search US roles: industry,\n"
            "  graduate, and academia.\nframework_version: 1.2.3\n---\n\n"
            "Shared workflow body. Read sibling guide.md.\n",
            encoding="utf-8",
        )
        self.target = self.root / ".claude/skills/job-scraper/SKILL.md"

    def run_sync(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *args],
            capture_output=True, text=True,
        )

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_sync_creates_regular_wrapper_with_exact_metadata_and_working_link(self):
        self.assert_ok(self.run_sync())
        self.assertFalse(self.target.is_symlink())
        content = self.target.read_text(encoding="utf-8")
        metadata = yaml.safe_load(content.split("---", 2)[1])
        self.assertEqual(metadata, {
            "name": "scrape",
            "description": "Search US roles: industry, graduate, and academia.\n",
        })
        link = re.search(r"\]\(([^)]+SKILL\.md)\)", content).group(1)
        self.assertEqual((self.target.parent / link).resolve(), self.source.resolve())
        self.assertIn("canonical skill directory", content)
        self.assertNotIn("Shared workflow body", content)
        self.assert_ok(self.run_sync("--check"))
        self.assert_ok(self.run_sync())
        self.assertEqual(self.target.read_text(encoding="utf-8"), content)

    def test_check_reports_missing_without_writing(self):
        result = self.run_sync("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing", result.stdout)
        self.assertFalse(self.target.exists())

    def test_check_detects_description_and_wrapper_drift_without_repairing(self):
        self.assert_ok(self.run_sync())
        original = self.target.read_text(encoding="utf-8")
        self.source.write_text(self.source.read_text().replace("Search US", "Discover US"))
        result = self.run_sync("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stale", result.stdout)
        self.assertEqual(self.target.read_text(encoding="utf-8"), original)
        self.assert_ok(self.run_sync())
        self.target.write_text(self.target.read_text() + "Unshared procedure.\n")
        self.assertNotEqual(self.run_sync("--check").returncode, 0)
        self.assert_ok(self.run_sync())
        self.assertNotIn("Unshared procedure", self.target.read_text())

    def test_removed_source_reports_extra_then_removes_only_managed_file(self):
        self.assert_ok(self.run_sync())
        survivor = self.target.parent / "notes.md"
        survivor.write_text("Personal notes")
        # Keep a valid source so an accidentally empty source tree is not accepted.
        other = self.source.parent.parent / "career-search/SKILL.md"
        other.parent.mkdir()
        other.write_text("---\nname: career-search\ndescription: Search\n---\nBody\n")
        self.source.unlink()
        result = self.run_sync("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("extra", result.stdout)
        self.assertTrue(self.target.exists())
        self.assert_ok(self.run_sync())
        self.assertFalse(self.target.exists())
        self.assertEqual(survivor.read_text(), "Personal notes")

    def test_unrelated_user_skill_and_dependencies_are_preserved(self):
        user_skill = self.root / ".claude/skills/custom/SKILL.md"
        user_skill.parent.mkdir(parents=True)
        user_skill.write_text("My personal skill")
        dependency = self.root / ".claude/skills/job-scraper/cli/node_modules/data"
        dependency.parent.mkdir(parents=True)
        dependency.write_text("Installed dependency")
        self.assert_ok(self.run_sync())
        self.assert_ok(self.run_sync("--check"))
        self.assertEqual(user_skill.read_text(), "My personal skill")
        self.assertEqual(dependency.read_text(), "Installed dependency")

    def test_unmanaged_collision_is_not_overwritten(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_text("My personal replacement")
        for args in ((), ("--check",)):
            result = self.run_sync(*args)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unmanaged", result.stdout + result.stderr)
            self.assertEqual(self.target.read_text(), "My personal replacement")

    def test_invalid_source_does_not_modify_existing_adapter(self):
        self.assert_ok(self.run_sync())
        original = self.target.read_bytes()
        self.source.write_text("---\nname: scrape\ndescription: []\n---\nBody\n")
        self.assertNotEqual(self.run_sync().returncode, 0)
        self.assertEqual(self.target.read_bytes(), original)

    def test_empty_source_tree_does_not_remove_existing_adapters(self):
        self.assert_ok(self.run_sync())
        original = self.target.read_bytes()
        self.source.unlink()
        self.assertNotEqual(self.run_sync().returncode, 0)
        self.assertEqual(self.target.read_bytes(), original)

    def test_symlink_target_is_not_followed(self):
        self.assert_ok(self.run_sync())
        external = self.root / "external.md"
        external.write_bytes(self.target.read_bytes())
        original = external.read_bytes()
        self.target.unlink()
        try:
            self.target.symlink_to(external)
        except OSError as exc:
            self.skipTest(f"OS does not allow test symlink creation: {exc}")
        self.assertNotEqual(self.run_sync().returncode, 0)
        self.assertEqual(external.read_bytes(), original)
        self.assertTrue(self.target.is_symlink())


if __name__ == "__main__":
    unittest.main()
