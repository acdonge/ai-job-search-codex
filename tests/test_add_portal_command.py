"""New portal skills must be Codex-native, without fictional tool permissions."""
import unittest
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
class TestAddPortalCommand(unittest.TestCase):
    def test_portal_instructions_use_native_paths_and_metadata(self):
        content = (REPO / 'workflows/add-portal.md').read_text(encoding="utf-8")
        self.assertIn('.agents/skills/<name>/cli/src/cli.ts', content)
        self.assertIn('No `context: fork`, `allowed-tools`', content)
        self.assertNotIn('allowed-tools: Bash(', content)
