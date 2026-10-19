---
name: career-search
description: "US career search: industry jobs, MS/PhD admissions, and academic positions. Use for search in this career workspace."
---

Read `AGENTS.md` and `workflows/career.md` first. Confirm the user's track for this
chat, initialize private state when necessary, and load `tracks/<active_track>.md`.
Follow the **search** stage in that runtime dispatcher and track guide.
Run the complete shared search pipeline in `docs/SEARCH_PIPELINE.md` using
`tools/career_pipeline.py`: start the run, record every discovery batch before fit
filtering, assess every lead, record a supported stop reason, then `complete` and
`check`. Search already includes scoring and the all-results HTML/JSON report; do
not stop after a shortlist or ask the user to invoke rank/report separately.
No candidate quotas, top-N caps or hidden default filters. Keep provisional,
excluded, closed, duplicate and unreachable leads visible with reasons. Unknown
dimensions stay null with score range and coverage, independently of eligibility.
Any pending assessment or blocked search yields an explicitly INCOMPLETE report.

For industry, ordinary skill, experience, function and seniority gaps must receive
an evidenced fit score, including low/zero values when appropriate; uncertain
eligibility stays VERIFY. An unscored `excluded` row requires the structured
`hard_gate` contract in `docs/SEARCH_PIPELINE.md`: allowed kind, requirement quote,
confirmed candidate contradiction and matching source evidence. There is no generic
"other" hard gate; user-constraint and compensation exclusions also require an
exact initial scope exclusion. Never invent a gate to skip scoring.

The inherited detailed reference is `.agents/skills/job-scraper/SKILL.md`. Read it where the dispatcher
applies it, preserving source verification, factual grounding and review.
All personal paths use the private mapping. Never write profiles into tracked
instructions. For graduate/academia, their guide controls documents, scoring,
cycle and lifecycle; industry assumptions in the inherited reference do not apply.
Use the current host's tools and invocation syntax from the shared dispatcher.
