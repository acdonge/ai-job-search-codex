"""Keep both native hosts routed through the complete US search pipeline.

The inherited workflow bodies intentionally retain old optional limits. These
checks protect the early shared overrides so an entry point cannot accidentally
route default US work back to that legacy selection/reporting path.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class SearchPipelineContractTests(unittest.TestCase):
    def test_every_native_stage_routes_to_shared_pipeline_before_legacy_reference(self):
        for skill in ("career-search", "career-rank", "career-html-report", "career-expand"):
            with self.subTest(skill=skill):
                canonical = f".agents/skills/{skill}/SKILL.md"
                text = read(canonical)
                override = text.split("The inherited detailed reference", 1)[0]
                self.assertIn("docs/SEARCH_PIPELINE.md", override)
                self.assertIn("tools/career_pipeline.py", override)
                self.assertIn(canonical, read(f".claude/skills/{skill}/SKILL.md"))

    def test_direct_scraper_invocation_cannot_bypass_shared_route(self):
        text = read(".agents/skills/job-scraper/SKILL.md")
        override = text.split("# Job Scraper", 1)[0]
        self.assertIn("docs/SEARCH_PIPELINE.md", override)
        self.assertIn("tools/career_pipeline.py", override)
        self.assertIn("`complete`", override)
        self.assertIn("`check`", override)
        self.assertIn("limits never", override)

    def test_legacy_rank_and_dashboard_have_early_pipeline_overrides(self):
        for name in ("rank", "html-report", "expand"):
            with self.subTest(workflow=name):
                override = read(f"workflows/{name}.md").split("## Step 0", 1)[0]
                self.assertIn("docs/SEARCH_PIPELINE.md", override)
                self.assertIn("tools/career_pipeline.py", override)
                self.assertIn("`complete`", override)
                self.assertIn("`check`", override)

    def test_all_tracks_share_completion_and_keep_their_own_rubric(self):
        for track in ("industry", "graduate", "academia"):
            with self.subTest(track=track):
                text = read(f"tracks/{track}.md")
                self.assertIn("docs/SEARCH_PIPELINE.md", text)
                self.assertIn("tools/career_pipeline.py", text)
                self.assertIn("All-null assessments remain pending", text)
                self.assertIn("INCOMPLETE", text)
        self.assertIn("docs/SEARCH_PIPELINE.md", read("AGENTS.md"))
        self.assertIn("docs/SEARCH_PIPELINE.md", read("workflows/career.md"))

    def test_documented_json_inputs_are_parseable_and_cover_core_stages(self):
        examples = [json.loads(block) for block in re.findall(
            r"```json\n(.*?)\n```", read("docs/SEARCH_PIPELINE.md"), re.DOTALL
        )]
        self.assertEqual(len(examples), 4)
        scope, provided, batch, assessment = examples
        self.assertEqual(scope["mode"], "open")
        self.assertEqual(scope["exclusions"], [])
        self.assertEqual(provided["mode"], "provided")
        expected = provided["expected_leads"]
        self.assertEqual(len(expected), 2)
        self.assertEqual(expected[0]["url"], expected[1]["url"])
        self.assertNotEqual(expected[0]["title"], expected[1]["title"])
        self.assertTrue(all(lead["cycle"] for lead in expected))
        self.assertEqual(len(batch["results"]), 1)
        row = assessment["assessments"][0]
        self.assertEqual(row["gates"]["eligibility"]["verdict"], "VERIFY")
        self.assertIsNone(row["dimensions"]["behavioral"]["value"])
        self.assertEqual(set(row["dimensions"]), {"technical", "experience", "behavioral", "career"})


if __name__ == "__main__":
    unittest.main()
