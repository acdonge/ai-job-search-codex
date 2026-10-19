"""Codex onboarding must personalize ignored copies rather than tracked sources."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

class OnboardingPrivacy(unittest.TestCase):
    def test_default_workspace_and_each_track_are_ignored(self):
        for name in ('profile.json', 'industry/profile/candidate-profile.md',
                     'graduate/documents/transcript.pdf', 'academia/opportunities.json'):
            result = subprocess.run(['git', 'check-ignore', '--no-index', 'workspace/' + name],
                                    cwd=REPO, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_initializing_all_tracks_does_not_mutate_templates(self):
        sources = [REPO / 'AGENTS.md', REPO / 'templates/candidate-profile.md']
        sources += list((REPO / '.agents/skills/job-application-assistant').glob('*.md'))
        before = {p: p.read_bytes() for p in sources}
        with tempfile.TemporaryDirectory() as directory:
            for track in ('industry', 'graduate', 'academia'):
                result = subprocess.run([sys.executable, str(REPO / 'tools/career.py'),
                    '--workspace', directory, 'init', '--track', track], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, {p: p.read_bytes() for p in sources})

    def test_setup_points_to_private_runtime_before_writes(self):
        text = (REPO / 'workflows/setup.md').read_text(encoding="utf-8")
        self.assertLess(text.index('workflows/career.md'), text.index('## Step 3: Generate Profile Files'))
        self.assertIn('do not personalize tracked templates', text)
        for name in ('README.md', 'SETUP.md'):
            self.assertIn('workspace/', (REPO / name).read_text(encoding="utf-8"))

if __name__ == '__main__':
    unittest.main()
