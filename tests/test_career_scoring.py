"""Evidence and arithmetic contracts for the shared US search pipeline."""

import copy
import math
import unittest

from tools.career_scoring import assess, rubric_for


INDUSTRY = {"technical": 30, "experience": 25, "behavioral": 15, "career": 30}
GRADUATE = {"preparation": 25, "program_fit": 30, "potential": 20,
            "resources": 15, "goals": 10}
ACADEMIA = {
    "faculty": {"agenda": 30, "contribution": 25, "teaching": 20,
                "environment": 15, "career": 10},
    "postdoc": {"agenda": 30, "contribution": 25, "teaching": 10,
                "environment": 25, "career": 10},
    "research_staff": {"agenda": 25, "contribution": 25, "teaching": 10,
                       "environment": 30, "career": 10},
}


def assessment(weights=INDUSTRY, value=80):
    return {
        "disposition": "eligible",
        "reason": "The current posting and supplied profile support this comparison.",
        "evidence": [{"url": "https://careers.example.org/robotics/42",
                      "note": "Current posting lists robotics experience.",
                      "checked_on": "2026-10-19"}],
        "gates": {key: {"verdict": "PASS", "reason": "Confirmed by posting and profile."}
                  for key in ("availability", "eligibility", "constraints")},
        "dimensions": {key: {"value": value, "reason": "Supported by candidate projects."}
                       for key in weights},
    }


class RubricTests(unittest.TestCase):
    def test_all_three_tracks_and_academic_roles_have_the_documented_weights(self):
        self.assertEqual(rubric_for("industry"), INDUSTRY)
        self.assertEqual(rubric_for("graduate"), GRADUATE)
        for role, weights in ACADEMIA.items():
            with self.subTest(role=role):
                self.assertEqual(rubric_for("academia", role), weights)
                self.assertEqual(sum(weights.values()), 100)

    def test_academia_does_not_silently_default_to_faculty(self):
        for role in (None, "", "research", [], {}):
            with self.subTest(role=role), self.assertRaises(ValueError):
                rubric_for("academia", role)

    def test_unknown_tracks_cannot_inherit_industry_weights(self):
        for track in ("unknown", None, [], {}):
            with self.subTest(track=track), self.assertRaises(ValueError):
                rubric_for(track)

    def test_callers_cannot_change_future_rubrics(self):
        changed = rubric_for("industry")
        changed["technical"] = 99
        self.assertEqual(rubric_for("industry"), INDUSTRY)


class ArithmeticTests(unittest.TestCase):
    def test_full_score_uses_weights_and_keeps_evidence_and_input_unchanged(self):
        item = assessment()
        for key, value in {"technical": 90, "experience": 70,
                           "behavioral": 40, "career": 80}.items():
            item["dimensions"][key]["value"] = value
        before = copy.deepcopy(item)
        result = assess("industry", item)
        self.assertEqual(result["score"], {
            "lower": 74.5, "upper": 74.5, "coverage": 100,
            "overall": 74.5, "band": "Good Fit", "weights": INDUSTRY})
        self.assertEqual(result["evidence"], item["evidence"])
        result["gates"]["eligibility"]["verdict"] = "FAIL"
        self.assertEqual(item, before)

    def test_unknown_fifteen_percent_stays_null_with_an_interval(self):
        item = assessment()
        item["dimensions"]["behavioral"] = {
            "value": None, "reason": "The posting does not describe the working environment."}
        score = assess("industry", item)["score"]
        self.assertEqual((score["lower"], score["upper"], score["coverage"]), (68, 83, 85))
        self.assertIsNone(score["overall"])
        self.assertIsNone(score["band"])
        self.assertIsNone(assess("industry", item)["dimensions"]["behavioral"]["value"])

    def test_all_unknown_dimensions_become_pending_and_never_a_zero_score(self):
        item = assessment(value=None)
        for dimension in item["dimensions"].values():
            dimension["reason"] = "Candidate evidence has not yet been supplied."
        result = assess("industry", item)
        self.assertEqual(result["disposition"], "pending")
        self.assertIsNone(result["score"])

    def test_zero_is_known_evidence_and_does_not_mean_missing(self):
        result = assess("industry", assessment(value=0))["score"]
        self.assertEqual(result["coverage"], 100)
        self.assertEqual(result["overall"], 0)
        self.assertEqual(result["band"], "Poor Fit")

    def test_full_scores_use_documented_band_boundaries(self):
        for value, band in ((100, "Strong Fit"), (75, "Strong Fit"),
                            (74.9, "Good Fit"), (60, "Good Fit"),
                            (59.9, "Moderate Fit"), (45, "Moderate Fit"),
                            (44.9, "Weak Fit"), (30, "Weak Fit"), (29.9, "Poor Fit")):
            with self.subTest(value=value):
                score = assess("industry", assessment(value=value))["score"]
                self.assertEqual(score["overall"], value)
                self.assertEqual(score["band"], band)

    def test_every_track_calculates_using_its_own_rubric(self):
        for track, role, weights in (("graduate", None, GRADUATE), *(
                ("academia", role, weights) for role, weights in ACADEMIA.items())):
            with self.subTest(track=track, role=role):
                item = assessment(weights, value=0)
                key = next(iter(weights))
                item["dimensions"][key]["value"] = 100
                score = assess(track, item, role)["score"]
                self.assertEqual(score["overall"], weights[key])
                self.assertEqual(score["weights"], weights)

    def test_supplied_scores_are_recomputed_instead_of_trusted(self):
        item = assessment(value=20)
        item["score"] = {"overall": 100, "band": "Strong Fit"}
        self.assertEqual(assess("industry", item)["score"]["overall"], 20)


class ScoredEvidenceTests(unittest.TestCase):
    def test_missing_dimension_is_not_treated_as_an_explicit_unknown(self):
        item = assessment()
        del item["dimensions"]["behavioral"]
        with self.assertRaisesRegex(ValueError, "dimension"):
            assess("industry", item)

    def test_missing_value_is_not_treated_as_an_explicit_null(self):
        item = assessment()
        del item["dimensions"]["behavioral"]["value"]
        with self.assertRaisesRegex(ValueError, "value"):
            assess("industry", item)

    def test_dimension_typo_does_not_disappear(self):
        item = assessment()
        item["dimensions"]["behavioural"] = {"value": 80, "reason": "A typo."}
        with self.assertRaisesRegex(ValueError, "dimension"):
            assess("industry", item)

    def test_values_must_be_finite_numbers_and_not_booleans_or_numeric_strings(self):
        for value in (True, False, "80", [], {}, -1, 101, math.inf, -math.inf, math.nan):
            with self.subTest(value=value):
                item = assessment()
                item["dimensions"]["technical"]["value"] = value
                with self.assertRaises(ValueError):
                    assess("industry", item)

    def test_each_known_and_unknown_dimension_requires_a_reason(self):
        for value in (80, None):
            for reason in (None, "", "   ", 80):
                with self.subTest(value=value, reason=reason):
                    item = assessment()
                    item["dimensions"]["behavioral"] = {"value": value, "reason": reason}
                    with self.assertRaises(ValueError):
                        assess("industry", item)

    def test_missing_gate_is_not_assumed_to_pass(self):
        item = assessment()
        del item["gates"]["eligibility"]
        with self.assertRaisesRegex(ValueError, "gate"):
            assess("industry", item)

    def test_gate_verdict_and_reason_must_be_explicit(self):
        for gate in ({}, {"verdict": "PASS"}, {"reason": "Unknown"},
                     {"verdict": "yes", "reason": "Available"},
                     {"verdict": "PASS", "reason": "  "}):
            with self.subTest(gate=gate):
                item = assessment()
                item["gates"]["availability"] = gate
                with self.assertRaises(ValueError):
                    assess("industry", item)

    def test_verify_gate_requires_provisional_even_with_a_high_fit_score(self):
        item = assessment(value=95)
        item["gates"]["eligibility"] = {
            "verdict": "VERIFY", "reason": "Role-specific sponsorship is not stated."}
        with self.assertRaises(ValueError):
            assess("industry", item)
        item["disposition"] = "provisional"
        result = assess("industry", item)
        self.assertEqual(result["score"]["overall"], 95)
        self.assertEqual(result["gates"]["eligibility"]["verdict"], "VERIFY")

    def test_a_failed_gate_cannot_be_weighted_away(self):
        for disposition in ("eligible", "provisional"):
            with self.subTest(disposition=disposition):
                item = assessment(value=100)
                item["disposition"] = disposition
                item["gates"]["constraints"]["verdict"] = "FAIL"
                with self.assertRaises(ValueError):
                    assess("industry", item)

    def test_provisional_with_all_passing_gates_needs_incomplete_fit_evidence(self):
        item = assessment()
        item["disposition"] = "provisional"
        with self.assertRaises(ValueError):
            assess("industry", item)
        item["dimensions"]["behavioral"] = {"value": None, "reason": "Work environment unknown."}
        self.assertEqual(assess("industry", item)["score"]["coverage"], 85)

    def test_scores_need_at_least_one_valid_source(self):
        for evidence in (None, [], {}, "https://example.org"):
            with self.subTest(evidence=evidence):
                item = assessment()
                item["evidence"] = evidence
                with self.assertRaises(ValueError):
                    assess("industry", item)

    def test_evidence_requires_http_url_nonempty_note_and_real_iso_date(self):
        for field, bad in (("url", "javascript:alert(1)"), ("url", "https:///missing"),
                           ("url", "https://example.org/a b"), ("url", None),
                           ("note", ""), ("checked_on", "2026-02-30"),
                           ("checked_on", "20261019"), ("checked_on", "2026-W42-1"),
                           ("checked_on", "2026-10-19T00:00:00Z")):
            with self.subTest(field=field, bad=bad):
                item = assessment()
                item["evidence"][0][field] = bad
                with self.assertRaises(ValueError):
                    assess("industry", item)


class UnscoredDispositionTests(unittest.TestCase):
    def terminal(self, disposition):
        item = assessment()
        item["disposition"] = disposition
        del item["dimensions"]
        del item["gates"]
        return item

    def test_excluded_requires_an_explicit_failed_gate_and_stays_unscored(self):
        item = self.terminal("excluded")
        with self.assertRaises(ValueError):
            assess("industry", item)
        item["gates"] = {"eligibility": {"verdict": "FAIL", "reason": "Required license absent."}}
        item['hard_gate'] = {'kind': 'required_license',
                             'requirement_quote': 'A Professional Engineer license is mandatory.',
                             'candidate_fact': 'Candidate confirms no Professional Engineer license.',
                             'source_url': item['evidence'][0]['url']}
        self.assertIsNone(assess("industry", item)["score"])

    def test_industry_exclusion_needs_structured_hard_gate_not_an_experience_gap(self):
        item = self.terminal('excluded')
        item['gates'] = {'eligibility': {'verdict': 'FAIL', 'reason': 'Five years wanted; candidate has none.'}}
        with self.assertRaisesRegex(ValueError, 'hard_gate'):
            assess('industry', item)
        for kind in ('experience', 'skills', 'seniority', 'mandatory_qualification', 'other'):
            item['hard_gate'] = {'kind': kind, 'requirement_quote': '5+ years of recruiting experience.',
                                 'candidate_fact': 'No recruiting experience.',
                                 'source_url': item['evidence'][0]['url']}
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'hard_gate'):
                assess('industry', item)

    def test_hard_gate_requires_quote_confirmed_fact_and_cited_source(self):
        item = self.terminal('excluded')
        item['gates'] = {'eligibility': {'verdict': 'FAIL', 'reason': 'Required license absent.'}}
        proof = {'kind': 'required_license', 'requirement_quote': 'Professional Engineer license required.',
                 'candidate_fact': 'Candidate explicitly has no such license.',
                 'source_url': item['evidence'][0]['url']}
        for key in proof:
            item['hard_gate'] = {k: v for k, v in proof.items() if k != key}
            with self.subTest(missing=key), self.assertRaises(ValueError):
                assess('industry', item)
        item['hard_gate'] = {**proof, 'source_url': 'https://uncited.example.org'}
        with self.assertRaisesRegex(ValueError, 'source'):
            assess('industry', item)

    def test_hard_gate_kind_must_match_failed_gate_and_user_constraint_is_explicit(self):
        item = self.terminal('excluded')
        item['gates'] = {'availability': {'verdict': 'FAIL', 'reason': 'Unavailable.'}}
        item['hard_gate'] = {'kind': 'required_degree', 'requirement_quote': 'Doctorate required.',
                             'candidate_fact': 'No doctorate.', 'source_url': item['evidence'][0]['url']}
        with self.assertRaisesRegex(ValueError, 'eligibility'):
            assess('industry', item)
        item['gates'] = {'constraints': {'verdict': 'FAIL', 'reason': 'Below confirmed minimum.'}}
        item['hard_gate']['kind'] = 'hard_compensation'
        with self.assertRaisesRegex(ValueError, 'user_constraint'):
            assess('industry', item)
        item['hard_gate']['user_constraint'] = 'Exclude salaries below my confirmed minimum.'
        self.assertIsNone(assess('industry', item)['score'])

    def test_ordinary_experience_gap_can_receive_a_zero_fit_without_a_hard_exclusion(self):
        item = assessment(value=0)
        item['disposition'] = 'provisional'
        item['gates']['eligibility'] = {'verdict': 'VERIFY', 'reason': 'Desired experience wording is not a verified hard screen.'}
        item['dimensions']['behavioral'] = {'value': None, 'reason': 'Working environment unknown.'}
        score = assess('industry', item)['score']
        self.assertEqual((score['lower'], score['upper'], score['coverage']), (0, 15, 85))

    def test_closed_requires_failed_availability_not_a_fetch_error(self):
        item = self.terminal("closed")
        for verdict in ("VERIFY", "PASS"):
            item["gates"] = {"availability": {"verdict": verdict, "reason": "Status checked."}}
            with self.subTest(verdict=verdict), self.assertRaises(ValueError):
                assess("industry", item)
        item["gates"]["availability"]["verdict"] = "FAIL"
        self.assertIsNone(assess("industry", item)["score"])

    def test_unreachable_requires_unverified_availability(self):
        item = self.terminal("unreachable")
        item["gates"] = {"availability": {"verdict": "VERIFY", "reason": "Login wall."}}
        self.assertIsNone(assess("industry", item)["score"])
        item["gates"]["availability"]["verdict"] = "FAIL"
        with self.assertRaises(ValueError):
            assess("industry", item)

    def test_duplicate_and_out_of_scope_need_a_specific_target_or_scope_criterion(self):
        for disposition, key in (("duplicate", "duplicate_of"),
                                 ("out_of_scope", "scope_exclusion")):
            with self.subTest(disposition=disposition):
                item = self.terminal(disposition)
                with self.assertRaises(ValueError):
                    assess("industry", item)
                item[key] = "lead-42" if disposition == "duplicate" else "Contract roles"
                self.assertIsNone(assess("industry", item)["score"])

    def test_every_terminal_disposition_requires_evidence_and_a_reason(self):
        for disposition in ("excluded", "closed", "unreachable", "duplicate", "out_of_scope"):
            for key in ("evidence", "reason"):
                with self.subTest(disposition=disposition, missing=key):
                    item = self.terminal(disposition)
                    item["duplicate_of"] = "lead-42"
                    item["scope_exclusion"] = "Contract roles"
                    item["gates"] = {"availability": {"verdict": "VERIFY" if disposition == "unreachable"
                                                     else "FAIL", "reason": "Checked posting."}}
                    del item[key]
                    with self.assertRaises(ValueError):
                        assess("industry", item)

    def test_pending_can_preserve_a_reason_without_fake_gates_evidence_or_score(self):
        result = assess("industry", {"disposition": "pending", "reason": "Profile not supplied."})
        self.assertEqual(result["disposition"], "pending")
        self.assertIsNone(result["score"])
        self.assertNotIn("gates", result)

    def test_unknown_dispositions_or_malformed_assessments_are_errors(self):
        for item in (None, [], "eligible", {}, {"disposition": "shortlisted", "reason": "Fit"},
                     {"disposition": [], "reason": "Fit"}):
            with self.subTest(item=item), self.assertRaises(ValueError):
                assess("industry", item)


if __name__ == "__main__":
    unittest.main()
