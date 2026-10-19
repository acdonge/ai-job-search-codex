"""Exercise the actual native-skill linter against isolated repository fixtures."""
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LINTER_SCRIPT = REPO_ROOT / "tools" / "lint_skills.py"


@unittest.skipUnless(importlib.util.find_spec("yaml"), "requires PyYAML (installed by CI)")
class CodexSkillLintTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "tools").mkdir()
        shutil.copy(LINTER_SCRIPT, self.root / "tools" / "lint_skills.py")
        self.command = self.root / "workflows" / "setup.md"
        self.command.parent.mkdir()
        self.command.write_text("# /setup - Setup reference\n", encoding="utf-8")
        self.skill = self.root / ".agents" / "skills" / "setup" / "SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.write_skill("name: setup\ndescription: Set up your application profile")

    def write_skill(self, frontmatter, body="Read `workflows/setup.md`.\n"):
        self.skill.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")

    def run_linter(self):
        return subprocess.run([sys.executable, str(self.root / "tools" / "lint_skills.py")], capture_output=True, text=True)

    def assert_fails(self, message):
        result = self.run_linter()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(message, result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_native_skill_and_workflow_pass_without_claude_settings(self):
        result = self.run_linter()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Codex skills", result.stdout)

    def test_claude_permission_metadata_is_rejected_in_all_shapes(self):
        for value in ("Bash(*)", "[]", "\n  - Read", "null"):
            with self.subTest(value=value):
                self.write_skill(f"name: setup\ndescription: Setup\nallowed-tools: {value}")
                self.assert_fails("unsupported permission key 'allowed-tools'")

    def test_other_permission_metadata_cannot_imply_isolation(self):
        for key in ("tools", "permissions", "hooks"):
            with self.subTest(key=key):
                self.write_skill(f"name: setup\ndescription: Setup\n{key}: Read")
                self.assert_fails(f"unsupported permission key '{key}'")

    def test_missing_required_field_fails(self):
        for field in ("name", "description"):
            with self.subTest(field=field):
                self.write_skill("\n".join(f"{key}: {'Setup' if key != field else ''}" for key in ("name", "description")))
                self.assert_fails(f"missing required key '{field}'")

    def test_non_string_required_field_fails(self):
        self.write_skill("name: [setup]\ndescription: Setup")
        self.assert_fails("missing required key 'name'")

    def test_folded_description_passes(self):
        self.write_skill("name: setup\ndescription: >\n  Ask which US application track\n  and collect the candidate profile.")
        result = self.run_linter()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_invalid_yaml_fails_cleanly(self):
        self.write_skill("name: [unterminated\ndescription: Setup")
        self.assert_fails("not valid YAML")

    def test_non_mapping_frontmatter_fails_cleanly(self):
        self.write_skill("- setup")
        self.assert_fails("did not parse to a mapping")

    def test_missing_frontmatter_fails(self):
        self.skill.write_text("# Setup\n", encoding="utf-8")
        self.assert_fails("missing YAML frontmatter")

    def test_missing_workflow_reference_fails(self):
        self.write_skill("name: setup\ndescription: Setup", "Read workflows/missing.md.\n")
        self.assert_fails("references a missing workflow: workflows/missing.md")

    def test_shared_codex_dispatcher_does_not_require_a_fake_slash_title(self):
        dispatcher = self.root / "workflows" / "codex.md"
        dispatcher.write_text("# Codex workflow dispatcher\n", encoding="utf-8")
        result = self.run_linter()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_dispatcher_still_requires_a_title(self):
        dispatcher = self.root / "workflows" / "codex.md"
        dispatcher.write_text("missing title\n", encoding="utf-8")
        self.assert_fails("dispatcher reference must start with a Markdown title")

    def test_workflow_without_slash_title_fails(self):
        self.command.write_text("# setup\n", encoding="utf-8")
        self.assert_fails("must start with a '# /<name>' title")

    def test_empty_skill_tree_fails(self):
        self.skill.unlink()
        self.assert_fails("no SKILL.md files found")

    def test_empty_workflow_tree_fails(self):
        self.command.unlink()
        self.assert_fails("no workflow files found")


if __name__ == "__main__":
    unittest.main()
