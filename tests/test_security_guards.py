"""Codex port guard regressions replace the obsolete Claude allowlist fixtures.

The executable guards protect source and ignored private data. They do not test
or claim host-level tool isolation: that is owned by the user's Codex runtime.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD_SCRIPT = REPO_ROOT / "tools" / "security_guards.py"
spec = importlib.util.spec_from_file_location("security_guards", GUARD_SCRIPT)
security_guards = importlib.util.module_from_spec(spec)
spec.loader.exec_module(security_guards)


class CodexGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "tools").mkdir()
        shutil.copy(GUARD_SCRIPT, self.root / "tools" / "security_guards.py")
        self.gitignore = self.root / ".gitignore"
        self.write_gitignore(security_guards.REQUIRED_IGNORE_RULES)
        self.manifest = self.root / ".agents" / "skills" / "example-search" / "cli" / "package.json"
        self.manifest.parent.mkdir(parents=True)
        self.write_manifest({"name": "example", "scripts": {"test": "bun test"}})
        self.skill = self.manifest.parent.parent / "SKILL.md"
        self.skill.write_text("---\nname: example-search\ndescription: Search examples\n---\n", encoding="utf-8")
        self.agent = self.root / "agents" / "posting-fetcher.md"
        self.agent.parent.mkdir()
        self.agent.write_text("# Posting fetcher\nReturn retrieved content to the parent.\n", encoding="utf-8")
        self.workflow = self.root / "workflows" / "setup.md"
        self.workflow.parent.mkdir()
        self.workflow.write_text("# /setup - Setup\n", encoding="utf-8")

    def write_gitignore(self, rules):
        self.gitignore.write_text("\n".join(rules) + "\n", encoding="utf-8")

    def write_manifest(self, value):
        self.manifest.write_text(json.dumps(value), encoding="utf-8")

    def run_guards(self):
        return subprocess.run([sys.executable, str(self.root / "tools" / "security_guards.py")], capture_output=True, text=True)

    def assert_fails(self, message):
        result = self.run_guards()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(message, result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_clean_tree_passes_without_settings_or_tool_grants(self):
        result = self.run_guards()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("security_guards: OK", result.stdout)

    def test_every_personal_data_exclusion_is_required(self):
        for rule in security_guards.REQUIRED_IGNORE_RULES:
            with self.subTest(rule=rule):
                self.write_gitignore([r for r in security_guards.REQUIRED_IGNORE_RULES if r != rule])
                self.assert_fails(f"required personal-data rule missing: {rule!r}")

    def test_private_workspace_cannot_be_reincluded(self):
        for rule in ("!workspace/", "!workspace/industry/profile.md", "!salary_data.json", "!documents/cv/**"):
            with self.subTest(rule=rule):
                self.write_gitignore(security_guards.REQUIRED_IGNORE_RULES + [rule])
                self.assert_fails("negation rule not in the reviewed allowlist")

    def test_intentional_template_exceptions_are_allowed(self):
        self.write_gitignore(security_guards.REQUIRED_IGNORE_RULES + sorted(security_guards.ALLOWED_IGNORE_NEGATIONS))
        result = self.run_guards()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_legacy_settings_are_rejected(self):
        legacy = self.root / ".claude" / "settings.json"
        legacy.parent.mkdir()
        legacy.write_text('{"permissions":{"allow":["Bash(*)"]}}', encoding="utf-8")
        self.assert_fails("obsolete runtime configuration")

    def test_skill_workflow_and_agent_permission_fields_are_rejected(self):
        for path in (self.skill, self.workflow, self.agent):
            original = path.read_text(encoding="utf-8")
            for key in security_guards.UNSUPPORTED_PERMISSION_KEYS:
                with self.subTest(path=path.name, key=key):
                    path.write_text(f"---\nname: example\n{key}: Read\n---\n", encoding="utf-8")
                    self.assert_fails(f"unsupported permission key '{key}'")
            path.write_text(original, encoding="utf-8")

    def test_quoted_key_and_block_list_are_rejected(self):
        self.skill.write_text("---\n'allowed-tools':\n  - Read\n---\n", encoding="utf-8")
        self.assert_fails("unsupported permission key 'allowed-tools'")

    def test_frontmatter_description_mentioning_tools_is_not_permission(self):
        self.skill.write_text("---\nname: example\ndescription: >\n  tools: are documented here\n---\n", encoding="utf-8")
        result = self.run_guards()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_each_install_lifecycle_script_is_rejected(self):
        for script in security_guards.FORBIDDEN_SCRIPTS:
            with self.subTest(script=script):
                self.write_manifest({"scripts": {script: "echo executed"}})
                self.assert_fails("lifecycle script(s)")

    def test_dependency_lifecycle_opt_in_is_rejected_even_when_empty(self):
        self.write_manifest({"trustedDependencies": []})
        self.assert_fails("trustedDependencies is forbidden")

    def test_new_portal_manifests_are_discovered(self):
        extra = self.root / ".agents" / "skills" / "new-search" / "cli" / "package.json"
        extra.parent.mkdir(parents=True)
        extra.write_text('{"scripts":{"postinstall":"echo bad"}}', encoding="utf-8")
        self.assert_fails("new-search")

    def test_installed_dependency_manifests_are_not_checked_as_project_source(self):
        installed = self.manifest.parent / "node_modules" / "dependency" / "package.json"
        installed.parent.mkdir(parents=True)
        installed.write_text('{"scripts":{"postinstall":"echo installed"}}', encoding="utf-8")
        result = self.run_guards()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_invalid_manifest_shapes_fail_cleanly(self):
        for value in ([], None, {"scripts": []}):
            with self.subTest(value=value):
                self.write_manifest(value)
                self.assert_fails("must be an object")

    def test_invalid_manifest_json_fails_cleanly(self):
        self.manifest.write_text("{broken", encoding="utf-8")
        self.assert_fails("unreadable or invalid JSON")

    def test_missing_manifest_tree_fails(self):
        self.manifest.unlink()
        self.assert_fails("no package.json files found")

    @unittest.skipUnless(shutil.which("git"), "requires git")
    def test_private_paths_are_ignored_by_git(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        for path in ("workspace/industry/profile.md", "workspace/graduate/job_search_tracker.csv", "workspace/academic/documents/research.pdf", "workspace/session.json"):
            with self.subTest(path=path):
                proc = subprocess.run(["git", "check-ignore", "--quiet", path], cwd=self.root)
                self.assertEqual(proc.returncode, 0)

    @unittest.skipUnless(shutil.which("git"), "requires git")
    def test_force_added_dependencies_are_rejected(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        installed = self.root / "node_modules" / "package" / "index.js"
        installed.parent.mkdir(parents=True)
        installed.write_text("// installed\n", encoding="utf-8")
        subprocess.run(["git", "add", "-f", "node_modules/package/index.js"], cwd=self.root, check=True)
        self.assert_fails("tracked path inside node_modules")


if __name__ == "__main__":
    unittest.main()
