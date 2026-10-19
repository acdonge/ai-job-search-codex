---
name: career-rank
description: "US career rank: industry jobs, MS/PhD admissions, and academic positions. Use for rank in this career workspace."
---

Read `AGENTS.md` and `workflows/career.md` first. Confirm the user's track for this
chat, initialize private state when necessary, and load `tracks/<active_track>.md`.
Follow the **rank** stage in that runtime dispatcher and track guide.
Use the selected search run and `docs/SEARCH_PIPELINE.md` with
`tools/career_pipeline.py`. Assess every recorded lead, retaining the full
ledger and its source evidence. Use `rubric` for the selected track and academic
role; score known dimensions and preserve unknowns as null with a range and
coverage. Eligibility gates are separate from fit. Never invoke the inherited
10-candidate/5-result defaults for US work. After updates, run `complete` and
`check` to regenerate the all-results report; use `report` with an INCOMPLETE
banner when pending work or access limits prevent completion. If only legacy
records exist, import all relevant records as a documented batch, preserving
prior outcomes; do not select only the most promising records.

For industry, ordinary skill, experience, function and seniority gaps must receive
an evidenced fit score, including low/zero values when appropriate; uncertain
eligibility stays VERIFY. An unscored `excluded` row requires the structured
`hard_gate` contract in `docs/SEARCH_PIPELINE.md`: allowed kind, requirement quote,
confirmed candidate contradiction and matching source evidence. There is no generic
"other" hard gate; user-constraint and compensation exclusions also require an
exact initial scope exclusion. Never invent a gate to skip scoring.

The inherited detailed reference is `workflows/rank.md`. Read it where the dispatcher
applies it, preserving source verification, factual grounding and review.
All personal paths use the private mapping. Never write profiles into tracked
instructions. For graduate/academia, their guide controls documents, scoring,
cycle and lifecycle; industry assumptions in the inherited reference do not apply.
Use the current host's tools and invocation syntax from the shared dispatcher.
