"""Validate evidence and calculate fit without inventing unknown information.

This module has no network or filesystem access. The caller validates run-specific
duplicate targets and user scope exclusions. Evidence records support an assessment;
their truth and relevance still require checking the source against the profile.
"""

from copy import deepcopy
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import math
from urllib.parse import urlsplit


_RUBRICS = {
    "industry": {"technical": 30, "experience": 25, "behavioral": 15, "career": 30},
    "graduate": {"preparation": 25, "program_fit": 30, "potential": 20,
                 "resources": 15, "goals": 10},
    "faculty": {"agenda": 30, "contribution": 25, "teaching": 20,
                "environment": 15, "career": 10},
    "postdoc": {"agenda": 30, "contribution": 25, "teaching": 10,
                "environment": 25, "career": 10},
    "research_staff": {"agenda": 25, "contribution": 25, "teaching": 10,
                       "environment": 30, "career": 10},
}
_GATES = {"availability", "eligibility", "constraints"}
_SCORED = {"eligible", "provisional"}
_DISPOSITIONS = _SCORED | {"excluded", "closed", "unreachable", "duplicate",
                          "out_of_scope", "pending"}
_BANDS = ((75, "Strong Fit"), (60, "Good Fit"), (45, "Moderate Fit"),
          (30, "Weak Fit"), (0, "Poor Fit"))
_INDUSTRY_HARD_GATES = {
    'work_authorization': 'eligibility', 'citizenship_clearance_export': 'eligibility',
    'required_degree': 'eligibility', 'required_license': 'eligibility',
    'required_language': 'eligibility', 'explicit_user_constraint': 'constraints',
    'hard_compensation': 'constraints',
}


class IndustryExclusionError(ValueError):
    """An exclusion lacks the structured proof needed to omit numeric fit."""


def validate_industry_exclusion(assessment):
    proof = assessment.get('hard_gate')
    advice = ('Ordinary experience, skills and seniority gaps require fit scoring; '
              'use provisional/VERIFY when eligibility wording is ambiguous.')
    if (not isinstance(proof, dict) or not isinstance(proof.get('kind'), str)
            or proof['kind'] not in _INDUSTRY_HARD_GATES):
        raise IndustryExclusionError('industry excluded requires hard_gate.kind from: ' +
                                     ', '.join(_INDUSTRY_HARD_GATES) + '. ' + advice)
    for key in ('requirement_quote', 'candidate_fact', 'source_url'):
        if not isinstance(proof.get(key), str) or not proof[key].strip():
            raise IndustryExclusionError(f'hard_gate.{key} must contain explicit evidence. ' + advice)
    if proof['source_url'] not in {source['url'] for source in assessment.get('evidence', [])}:
        raise IndustryExclusionError('hard_gate.source_url must match a cited evidence source.')
    gate = _INDUSTRY_HARD_GATES[proof['kind']]
    if assessment.get('gates', {}).get(gate, {}).get('verdict') != 'FAIL':
        raise IndustryExclusionError(f'hard_gate.kind requires a matching {gate} FAIL.')
    if gate == 'constraints' and (not isinstance(proof.get('user_constraint'), str)
                                  or not proof['user_constraint'].strip()):
        raise IndustryExclusionError('hard_gate.user_constraint must identify an explicit initial user criterion.')


def rubric_for(track, academic_role=None):
    """Return an independent weight mapping; academia always requires a role."""
    if not isinstance(track, str) or track not in {"industry", "graduate", "academia"}:
        raise ValueError("track must be industry, graduate, or academia")
    key = track
    if track == "academia":
        if not isinstance(academic_role, str) or academic_role not in {
                "faculty", "postdoc", "research_staff"}:
            raise ValueError("academia requires academic_role: faculty, postdoc, or research_staff")
        key = academic_role
    return dict(_RUBRICS[key])


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")


def _evidence(items, required):
    if not isinstance(items, list) or (required and not items):
        raise ValueError("evidence must be a list with at least one source for a completed assessment")
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each evidence source must be an object")
        _text(item.get("url"), "evidence url")
        url = item["url"]
        try:
            parsed = urlsplit(url)
            valid = (parsed.scheme in {"http", "https"} and parsed.hostname
                     and parsed.username is None and parsed.password is None
                     and not any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in url))
            # Accessing port validates its syntax and range.
            parsed.port
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("evidence url must be an absolute HTTP(S) URL without credentials")
        _text(item.get("note"), "evidence note")
        checked = item.get("checked_on")
        try:
            valid_date = isinstance(checked, str) and date.fromisoformat(checked).isoformat() == checked
        except ValueError:
            valid_date = False
        if not valid_date:
            raise ValueError("evidence checked_on must be a real date in YYYY-MM-DD format")


def _gates(gates, required):
    if not isinstance(gates, dict) or set(gates) - _GATES:
        raise ValueError("gates must be an object containing only availability, eligibility, and constraints")
    if required and set(gates) != _GATES:
        raise ValueError("scored assessments require all three gates; missing gates are not PASS")
    for key, gate in gates.items():
        if not isinstance(gate, dict):
            raise ValueError(f"gate {key} must be an object")
        verdict = gate.get("verdict")
        if not isinstance(verdict, str) or verdict not in {"PASS", "FAIL", "VERIFY"}:
            raise ValueError(f"gate {key} requires an explicit PASS, FAIL, or VERIFY verdict")
        _text(gate.get("reason"), f"gate {key} reason")


def _dimensions(dimensions, weights, required):
    if not isinstance(dimensions, dict) or set(dimensions) - set(weights):
        raise ValueError("dimensions must be an object containing only the selected rubric keys")
    if required and set(dimensions) != set(weights):
        raise ValueError("scored assessments require every dimension; use explicit null for unknown evidence")
    for key, dimension in dimensions.items():
        if not isinstance(dimension, dict) or "value" not in dimension:
            raise ValueError(f"dimension {key} requires an explicit value or null")
        value = dimension["value"]
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                  or not 0 <= value <= 100 or not math.isfinite(value)):
            raise ValueError(f"dimension {key} value must be a finite number from 0 to 100, or null")
        _text(dimension.get("reason"), f"dimension {key} evidence or unknown reason")


def _score(dimensions, weights):
    known = {key: dimensions[key]["value"] for key in weights
             if dimensions[key]["value"] is not None}
    coverage = sum(weights[key] for key in known)
    total = sum((Decimal(str(value)) * weights[key] / 100 for key, value in known.items()), Decimal(0))

    def rounded(value):
        return float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

    lower = rounded(total)
    upper = rounded(total + 100 - coverage)
    overall = lower if coverage == 100 else None
    band = next(label for minimum, label in _BANDS if overall >= minimum) if overall is not None else None
    return {"lower": lower, "upper": upper, "coverage": coverage,
            "overall": overall, "band": band, "weights": weights}


def assess(track, assessment, academic_role=None):
    """Return a validated copy with a computed score, or raise ValueError.

    Eligibility gates and fit are independent. Eligible requires three PASS
    gates, but may have partial fit evidence. Provisional requires VERIFY or
    partial fit evidence and no FAIL. Entirely unknown fit becomes pending so
    it cannot satisfy completion. No unscored disposition receives a fake zero.
    """
    weights = rubric_for(track, academic_role)
    if not isinstance(assessment, dict):
        raise ValueError("assessment must be an object")
    disposition = assessment.get("disposition")
    if not isinstance(disposition, str) or disposition not in _DISPOSITIONS:
        raise ValueError("unknown assessment disposition")
    _text(assessment.get("reason"), "assessment reason")
    scored = disposition in _SCORED
    _evidence(assessment.get("evidence", []), required=disposition != "pending")
    gates = assessment.get("gates", {})
    dimensions = assessment.get("dimensions", {})
    _gates(gates, required=scored)
    _dimensions(dimensions, weights, required=scored)
    verdicts = {key: gate["verdict"] for key, gate in gates.items()}
    result = deepcopy(assessment)
    result["score"] = None

    if scored:
        if "FAIL" in verdicts.values():
            raise ValueError("a FAIL gate cannot receive a fit score; use an evidenced unscored disposition")
        if disposition == "eligible" and any(value != "PASS" for value in verdicts.values()):
            raise ValueError("eligible requires all gates PASS; use provisional for VERIFY")
        score = _score(dimensions, weights)
        if disposition == "provisional" and "VERIFY" not in verdicts.values() and score["coverage"] == 100:
            raise ValueError("provisional requires a VERIFY gate or incomplete fit evidence")
        if score["coverage"] == 0:
            result["disposition"] = "pending"
        else:
            result["score"] = score
    elif disposition == "excluded" and "FAIL" not in verdicts.values():
        raise ValueError("excluded requires an explicit FAIL gate")
    elif disposition == "closed" and verdicts.get("availability") != "FAIL":
        raise ValueError("closed requires availability FAIL; an inaccessible page is not closed")
    elif disposition == "unreachable" and verdicts.get("availability") != "VERIFY":
        raise ValueError("unreachable requires availability VERIFY")
    elif disposition == "duplicate":
        _text(assessment.get("duplicate_of"), "duplicate_of")
    elif disposition == "out_of_scope":
        _text(assessment.get("scope_exclusion"), "scope_exclusion")
    if disposition == 'excluded' and track == 'industry':
        validate_industry_exclusion(assessment)
    return result
