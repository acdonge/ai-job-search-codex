"""Offline contracts for the US source catalog and native search entry point.

These checks validate maintained metadata, not website availability or vacancies.
Live verification remains an explicit research step recorded per opportunity.
"""

import json
import re
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


REPO_ROOT = Path(__file__).resolve().parents[1]
TRACKS = {"industry", "graduate", "academia"}


class USSourceRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(
            (REPO_ROOT / "config/us_sources.json").read_text(encoding="utf-8")
        )
        cls.sources = cls.registry["sources"]

    def test_registry_version_and_sources_are_present(self):
        self.assertIs(type(self.registry["schema_version"]), int)
        self.assertEqual(self.registry["schema_version"], 1)
        self.assertIsInstance(self.sources, list)
        self.assertTrue(self.sources, "The US search plan must have source metadata.")

    def test_sources_have_required_fields_and_nonempty_text(self):
        text_fields = {
            "id", "name", "url", "category", "authority", "access", "notes",
            "verification_url", "checked_on", "check_status",
        }
        for source in self.sources:
            with self.subTest(source=source.get("id")):
                self.assertTrue(text_fields | {"tracks"} <= source.keys())
                for field in text_fields:
                    self.assertIsInstance(source[field], str, field)
                    self.assertTrue(source[field].strip(), field)

    def test_source_ids_are_unique_and_stable_identifiers(self):
        identifiers = [source["id"] for source in self.sources]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for identifier in identifiers:
            with self.subTest(source=identifier):
                self.assertRegex(identifier, r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$")

    def test_source_enums_and_track_memberships_are_valid(self):
        allowed = {
            "authority": {"primary", "discovery", "context"},
            "access": {
                "public_web", "manual_or_login", "api_key_optional", "api_key_required",
            },
            "check_status": {"verified", "blocked", "search_verified"},
        }
        for source in self.sources:
            with self.subTest(source=source["id"]):
                self.assertIsInstance(source["tracks"], list)
                self.assertTrue(source["tracks"])
                self.assertEqual(len(source["tracks"]), len(set(source["tracks"])))
                self.assertLessEqual(set(source["tracks"]), TRACKS)
                for field, values in allowed.items():
                    self.assertIn(source[field], values, field)

    def test_check_dates_are_iso_dates_within_registry_review(self):
        reviewed_on = self.registry["reviewed_on"]
        self.assertRegex(reviewed_on, r"^\d{4}-\d{2}-\d{2}$")
        reviewed_date = date.fromisoformat(reviewed_on)
        for source in self.sources:
            with self.subTest(source=source["id"]):
                self.assertRegex(source["checked_on"], r"^\d{4}-\d{2}-\d{2}$")
                self.assertLessEqual(date.fromisoformat(source["checked_on"]), reviewed_date)

    def test_source_and_verification_urls_are_https_without_credentials(self):
        for source in self.sources:
            for field in ("url", "verification_url"):
                with self.subTest(source=source["id"], field=field):
                    value = source[field]
                    parsed = urlsplit(value)
                    self.assertEqual(parsed.scheme, "https")
                    self.assertTrue(parsed.hostname)
                    self.assertIsNone(parsed.username)
                    self.assertIsNone(parsed.password)
                    self.assertIsNone(re.search(r"\s", value))

    def test_every_track_has_a_primary_source(self):
        for track in TRACKS:
            with self.subTest(track=track):
                self.assertTrue(
                    any(source["authority"] == "primary" and track in source["tracks"]
                        for source in self.sources),
                    f"{track} needs official sources, not only discovery boards or context.",
                )

    def test_closed_apa_psyccareers_is_not_an_active_source(self):
        # APA's official closure notice dates the job-board retirement to 2026-07-31.
        for source in self.sources:
            with self.subTest(source=source["id"]):
                identity = " ".join(source[key] for key in ("id", "name", "url"))
                self.assertNotIn("psyccareers", identity.lower())


class NativeUSSearchRouteTests(unittest.TestCase):
    def test_native_search_loads_dispatcher_and_selected_track(self):
        skill = REPO_ROOT / ".agents/skills/career-search/SKILL.md"
        text = skill.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^name: career-search$")
        self.assertIn("workflows/career.md", text)
        self.assertIn("tracks/<active_track>.md", text)
        self.assertTrue((REPO_ROOT / "workflows/career.md").is_file())
        for track in TRACKS:
            with self.subTest(track=track):
                self.assertTrue((REPO_ROOT / "tracks" / f"{track}.md").is_file())


if __name__ == "__main__":
    unittest.main()
