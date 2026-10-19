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
class DualRuntimeSkillLintTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.agents_entrypoint = self.root / "AGENTS.md"
        self.agents_entrypoint.write_text("# Shared career guidance\n", encoding="utf-8")
        self.claude_entrypoint = self.root / "CLAUDE.md"
        self.claude_entrypoint.write_text("@AGENTS.md\n", encoding="utf-8")
        (self.root / "tools").mkdir()
        shutil.copy(LINTER_SCRIPT, self.root / "tools" / "lint_skills.py")
        self.command = self.root / "workflows" / "setup.md"
        self.command.parent.mkdir()
        self.command.write_text("# /setup - Setup reference\n", encoding="utf-8")
        self.skill = self.root / ".agents" / "skills" / "setup" / "SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.write_skill("name: setup\ndescription: Set up your application profile")
        self.claude_skill = self.root / ".claude" / "skills" / "setup" / "SKILL.md"
        self.claude_skill.parent.mkdir(parents=True)
        self.claude_skill.write_text(
            "---\nname: setup\ndescription: Set up your application profile\n---\n"
            "Read `.agents/skills/setup/SKILL.md` from the repository root.\n",
            encoding="utf-8",
        )

    def write_skill(self, frontmatter, body="Read `workflows/setup.md`.\n"):
        self.skill.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")

    def run_linter(self):
        return subprocess.run([sys.executable, str(self.root / "tools" / "lint_skills.py")], capture_output=True, text=True)

    def assert_fails(self, message):
        result = self.run_linter()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(message, result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_both_native_skill_trees_pass_without_runtime_settings(self):
        result = self.run_linter()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 Codex skills, 1 Claude skills", result.stdout)

    def test_project_permission_metadata_is_rejected_in_all_shapes(self):
        for value in ("Bash(*)", "[]", "\n  - Read", "null"):
            with self.subTest(value=value):
                self.write_skill(f"name: setup\ndescription: Setup\nallowed-tools: {value}")
                self.assert_fails("unsupported permission key 'allowed-tools'")

    def test_missing_agents_entrypoint_fails(self):
        self.agents_entrypoint.unlink()
        self.assert_fails("AGENTS.md: missing or unreadable project entrypoint")

    def test_empty_agents_entrypoint_fails(self):
        self.agents_entrypoint.write_text(" \n\t", encoding="utf-8")
        self.assert_fails("AGENTS.md: project entrypoint must not be empty")

    def test_missing_claude_entrypoint_fails(self):
        self.claude_entrypoint.unlink()
        self.assert_fails("CLAUDE.md: missing or unreadable project entrypoint")

    def test_claude_entrypoint_requires_active_import(self):
        inactive_examples = (
            "Read AGENTS.md for shared guidance.\n",
            "<!-- @AGENTS.md -->\n",
            "<!--\n@AGENTS.md\n-->\n",
            "```markdown\n@AGENTS.md\n```\n",
            "~~~\n@AGENTS.md\n~~~\n",
            "Use `@AGENTS.md` to import shared guidance.\n",
            "Use ``the `@AGENTS.md` import`` in this file.\n",
        )
        for content in inactive_examples:
            with self.subTest(content=content):
                self.claude_entrypoint.write_text(content, encoding="utf-8")
                self.assert_fails("CLAUDE.md: missing active @AGENTS.md import")

    def test_active_import_after_code_and_comments_passes(self):
        self.claude_entrypoint.write_text(
            "<!-- Shared instructions -->\n```text\nExample only\n```\n"
            "Some `inline code` followed by the actual import:\n@AGENTS.md\n",
            encoding="utf-8",
        )
        result = self.run_linter()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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

    def test_shared_and_compatibility_dispatchers_accept_plain_titles(self):
        for name in ("career.md", "codex.md"):
            with self.subTest(name=name):
                dispatcher = self.root / "workflows" / name
                dispatcher.write_text("# Career workflow reference\n", encoding="utf-8")
                result = self.run_linter()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_dispatchers_still_require_titles(self):
        for name in ("career.md", "codex.md"):
            with self.subTest(name=name):
                dispatcher = self.root / "workflows" / name
                dispatcher.write_text("missing title\n", encoding="utf-8")
                self.assert_fails("dispatcher reference must start with a Markdown title")
                dispatcher.unlink()

    def test_claude_wrapper_frontmatter_is_validated(self):
        self.claude_skill.write_text("---\nname: setup\n---\n", encoding="utf-8")
        self.assert_fails(".claude/skills/setup/SKILL.md: frontmatter missing required key 'description'")

    def test_claude_wrapper_cannot_grant_tools(self):
        self.claude_skill.write_text(
            "---\nname: setup\ndescription: Setup\nallowed-tools: Bash(*)\n---\n",
            encoding="utf-8",
        )
        self.assert_fails(".claude/skills/setup/SKILL.md: unsupported permission key 'allowed-tools'")

    def test_broken_canonical_reference_fails(self):
        self.claude_skill.write_text(
            "---\nname: setup\ndescription: Setup\n---\n"
            "Read `.agents/skills/missing/SKILL.md`.\n",
            encoding="utf-8",
        )
        self.assert_fails("references a missing skill: .agents/skills/missing/SKILL.md")

    def test_missing_claude_skill_tree_fails(self):
        self.claude_skill.unlink()
        self.assert_fails("no SKILL.md files found under .claude/skills/")

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
