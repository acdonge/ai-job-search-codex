---
name: career-html-report
description: "US career html-report: industry jobs, MS/PhD admissions, and academic positions. Use for html-report in this career workspace."
---

Read `AGENTS.md` and `workflows/career.md` first. Confirm the user's track for this
chat, initialize private state when necessary, and load `tracks/<active_track>.md`.
Follow the **html-report** stage in that runtime dispatcher and track guide.
Generate the selected run's full report using `tools/career_pipeline.py` and
`docs/SEARCH_PIPELINE.md`. Run `complete` and `check` when all stages are valid;
otherwise use `report` and label it INCOMPLETE with unresolved IDs/reasons.
Every discovered lead must appear, including all dispositions, with no default
hidden filter, pagination or top-N cap. Reconcile all counts and link the HTML
and machine-readable results. A legacy application-history dashboard is optional
only when requested; it is not a substitute for this search-results report.

The inherited detailed reference is `workflows/html-report.md`. Read it where the dispatcher
applies it, preserving source verification, factual grounding and review.
All personal paths use the private mapping. Never write profiles into tracked
instructions. For graduate/academia, their guide controls documents, scoring,
cycle and lifecycle; industry assumptions in the inherited reference do not apply.
Use the current host's tools and invocation syntax from the shared dispatcher.
