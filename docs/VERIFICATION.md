# Verification of the shared US career workspace

Date: 2026-10-19. Original source: MadsLorentzen/ai-job-search,
commit `2e90272d8d456df56c16a286eab127d2951f783c`.

## Full search, scoring and all-results verification

The previous startup checks below did not test a full search. This change adds a
shared executable discovery ledger, assessment/scoring validator, complete HTML/JSON
report and completion check for both hosts. It retains every recorded lead, including
exclusions and unavailable postings, and refuses completion with pending assessments,
missing provided identities, unattempted declared sources at saturation, or altered
reports. A short conversational summary cannot replace the all-results report.

- **872 Python tests: 865 passed, 7 existing upstream-only checks skipped** on
  Python 3.13.11 with PyYAML/openpyxl. No new skips or weakened assertions.
- **87 new regressions:** 26 pipeline, 34 scoring, 22 report, 5 instruction contracts.
- **23 Codex skills / 23 Claude adapters / 14 workflow references** passed lint and
  synchronization checks. Private-state/dependency guards and Git whitespace passed.
- Independent review and failure-path tests covered missing evaluations, a corpus
  cut to three, lost export records, tampered HTML, same-URL MS/PhD identities,
  historical-run preservation, stale completed reports and incomplete source coverage.
  Two scratch mutation checks failed as expected when completion guards were disabled.
- Browser checks: Claude's generated 16-row report and Codex's live 17-row report
  showed every row by default. Filtering and reset updated counts correctly; the
  three London roles remained visible as out of scope. An 18-row incomplete
  fixture retained every row and showed INCOMPLETE. No browser console errors/warnings.

### Actual native-host runs

**17 scenarios passed after the fixes and documented retries below**, using authenticated Codex CLI 0.163.0 and Claude Code 2.1.291
with their normally configured models, in disposable source snapshots and synthetic
candidate profiles. Final-source checks used implementation commit
`5f4f3a896fe44b8dab405de7c9b9e20a268fc8d6`; this verification update changes only
documentation. These were actual host executions, not mocked agent responses.
Both hosts generated assessments from candidate/source evidence; the harness did not
supply score answers. Every case had zero pending assessments and equal discovered,
assessed and displayed counts. Table cells are **discovered / scored / justified
unscored / displayed**. Unknown dimensions produce partial ranges, not invented values.

| Scenario | Codex | Claude Code |
|---|---|---|
| Synthetic industry corpus | **16 / 11 / 5 / 16** | **16 / 11 / 5 / 16** |
| Synthetic graduate corpus | **16 / 11 / 5 / 16** | **16 / 11 / 5 / 16** |
| Synthetic academia corpus | **16 / 11 / 5 / 16** | **16 / 11 / 5 / 16** |
| Live industry, three official boards (final checked run) | **17 / 14 / 3 / 17** | **17 / 14 / 3 / 17** |
| Live graduate, Michigan Robotics MS and PhD | **2 / 2 / 0 / 2** | **2 / 2 / 0 / 2** |
| Live academia, UCI two postdoc topics | **2 / 2 / 0 / 2** | **2 / 2 / 0 / 2** |
| Live recruiter regression after the fixes | **1 / 1 / 0 / 1** | **1 / 1 / 0 / 1** |
| Search-only native command, without rank/report instructions | **16 / 11 / 5 / 16** | See natural-language case |
| Natural-language search, without skill/score/report instructions | **16 / 11 / 5 / 16** | **16 / 11 / 5 / 16** |

Each synthetic case had 17 observations resolving to 16 unique leads, including
one deliberately repeated observation, a partial fit, unknown eligibility and five
evidenced unscored dispositions. Both hosts preserved all observations. The natural-
language and native-command probes asked only for search; scoring and reporting still
ran without a separate instruction.

Both hosts independently fetched current official pages for the live cases and
saved source snapshots. The industry scope was every title containing "robotics"
on the official [Applied](https://jobs.ashbyhq.com/applied),
[Persona AI](https://jobs.ashbyhq.com/persona.ai), and
[One Robot](https://jobs.ashbyhq.com/onerobot) boards. Independent board parsing found
17 unique matches; both hosts retained all 17, including three London roles, and
recorded 34 observations after a verification pass. Public posting API requests could
return 403; normal public board/posting HTML was used without bypassing access controls.

The finite graduate case used the distinct [Michigan Robotics MS and PhD
programs](https://robotics.umich.edu/academics/graduate/admissions/) on one URL.
The requested Fall 2027 cycle remained unverified where the official source gave
only recurring month/day deadlines. The academia case used the two distinct research
topics in [UCI recruitment JPF10447](https://recruit.ap.uci.edu/JPF10447), also on one
URL. Both identities remained separately assessed and displayed; a visible application
page did not establish that a position remained unfilled after its review date.
These finite scopes are test corpora, not default candidate limits for user searches.

### Findings and interruptions retained in the evidence

The first broad industry runs exposed a real wording ambiguity. Codex treated a
recruiter's stated five years of experience as a hard exclusion; Claude gave a low
fit range. Both retained and assessed the lead, so this was not a dropped result.
The industry guide now distinguishes ordinary skill/seniority/experience gaps from
explicit, non-negotiable eligibility conditions. Ambiguous qualifications remain
VERIFY while known fit is scored. The first prose-only clarification was insufficient: a fresh Claude replay still
excluded that recruiter without a fit score. That behavioral regression was recorded
as a failure even though the row count was correct. The shared scorer now requires
a structured `hard_gate` with a supported category, source quote, confirmed candidate
fact and cited URL before an industry exclusion can omit fit scoring. Experience,
skills, seniority and generic "other" are not supported exclusion categories; user
constraints must also match the initial scope. Old unsupported exclusions remain
visible as pending and can be repaired with normal assessment commands.
The fresh Claude retry passed; Codex's successful targeted replay was rechecked
with the final helper. Native continuation checks then passed in both hosts: the
recruiter remained scored, with unknown working-environment fit preserved.
Original and failed-run artifacts were retained separately.
Fit values may still differ because the dimension judgments are made by each model.

The long-lived outer test process ended with SIGTERM while Claude was performing its
final industry report audit, after source retrieval, assessments and the report had
been saved. That interrupted invocation was not counted as a pass. A fresh native
Claude invocation resumed the saved work, audited the evidence and all 17 rows, ran
the completion check and returned successfully. Original logs and outputs were kept.
The precise external cause of the termination was not established.

The evaluator was also corrected to find a valid nested private workspace chosen
by Codex. Earlier output snapshots were first checked against their own source;
where the final renderer differed only in scope-count wording, reports were refreshed
with the final helper and rechecked. Stored industry exclusions from the draft schema
were subsequently repaired in actual native continuation runs: old unsupported exclusions
were first displayed as pending, then reassessed through the supported commands.
The original observations and source snapshots were preserved. Native source hashes were unchanged, generated
files stayed private, and final-source completion checks passed. Raw agent logs,
candidate fixtures created during execution and fetched source archives remain private
scratch artifacts; only reusable synthetic test fixtures and this summary are published.

### Reproduce and interpret the checks

Run the commands in the Reproduce section below. For a native pipeline check, use a
disposable checkout and ask Codex or Claude to find industry opportunities using the
candidate and entire corpus in `tests/fixtures/career_pipeline/industry.json`, with
no further intake and no external browsing. Repeat with `graduate.json` and
`academia.json` (postdoc). A plain search request must generate the scored all-results
report. Inspect `results.json`, every HTML lead ID, and the helper's successful
`check`; an agent's final message alone is not proof. The fixture README and
[pipeline guide](SEARCH_PIPELINE.md) describe the schema and executable commands.

These tests validate arithmetic, required evidence fields, recorded-result accounting
and display. They cannot establish the truth of invented evidence, detect a result
the assistant never recorded, prevent arbitrary manual edits, prove an exhaustive
Internet search or guarantee future host behavior. Scores are not admission/offer
probabilities or proof of eligibility. No applications, messages, payments or referee
contacts were made.

## Earlier startup and workspace checks (historical)

| Check | Result |
|---|---|
| Full Python suite, Python 3.13 with PyYAML/openpyxl | **785 run: 778 passed, 7 upstream-only template checks skipped** |
| Native skill/workflow lint | **23 Codex skills, 23 Claude skills, 14 workflow references passed** |
| Shared instruction entrypoints | **AGENTS.md present; CLAUDE.md imports it; missing imports fail validation** |
| Claude adapter synchronization | **23 adapters match their canonical skills; --check passed** |
| Metadata/private-state/dependency guards | **Passed** |
| Local documentation/adapter links and Git whitespace | **Passed** |
| Independent integration review | **No blocking findings** |
| Live native startup/setup: Codex CLI 0.163.0 | **4/4 passed** |
| Live native startup/setup: Claude Code 2.1.291 | **4/4 passed; all 23 project skills discovered** |
| Resume a Codex-created graduate workspace in Claude Code | **Passed; 20-source plan with 12 cycle-specific queries** |
| Resume a Claude-created industry workspace in Codex | **Passed; 24-source plan with 18 queries** |

The seven skips are existing guards for the pristine upstream template, gated by
repository identity. They are not disabled dual-runtime tests. Python regressions
cover first-start selection, all three tracks, corrupt-state refusal, cross-chat
track isolation, admission-cycle identity, outcome confirmation, source filtering,
and private template initialization. New fixture tests exercise adapter creation,
drift detection, missing and removed skills, user-file preservation, symlink
refusal, both native skill trees, and active instruction imports.

The prior Windows CI failure was caused by two tests reading UTF-8 documentation
with the machine's default encoding. Those reads now explicitly request UTF-8.

## Earlier startup/runtime evidence (historical)

Both authenticated CLIs were exercised on isolated repository snapshots with their
normal configured models. Each host received four native skill requests: an
unselected start, US industry robotics jobs, robotics PhD admissions for Fall 2027,
and US robotics postdoc positions. Both asked for a path before initialization
when none was selected. For explicit paths, both read the matching track guide,
created the correct private profile/scaffold, and returned relevant intake questions.
Each selected case verified 33 private scaffold files and 15 directories. Source
file hashes were unchanged, and no unexpected files appeared outside the private
workspace or Git metadata. Claude's initialization events listed all 23 project
skills, including the 14 `career-*` skills.

Two additional cross-host checks reused the saved graduate and industry workspaces
in the opposite host. Both ran the shared `tools/career.py search-plan` command,
preserved the active track and every existing workspace file byte-for-byte, and
saved new plans only under private reports. The generated plans retained source
URLs; the graduate queries included Fall 2027. Codex could not start an independent
reviewer in that isolated session and correctly disclosed its self-review fallback.
All ten live setup/resume scenarios passed.

These are real LLM startup/setup and saved-workspace checks, not claims that all external services or
all application stages have been exercised. Tests prohibited web research,
messages, payments and submissions. An initial Claude OAuth refresh lock resolved
on retry without changing credentials or settings.

## Inherited verification

Before the dual-runtime change, all six portal TypeScript typechecks and 475 Bun
fixture/mock tests passed. The portal implementation and fixtures are unchanged.
Counts: Freehire 116; Jobbank 56; Jobdanmark 72; Jobindex 75; Jobnet 66; LinkedIn 90.
These checks do not establish live platform access.

[CI before this pipeline change](https://github.com/acdonge/ai-job-search-codex/actions/runs/39315583262)
passed Linux Python 3.10–3.14, Windows Python 3.14, the six portal jobs, and both
LaTeX smoke jobs (texlive-latest and debian-bookworm). The earlier Windows encoding
failure had been fixed before this pipeline change.
Local TeX compilation still needs packages such as moderncv and titlesec;
target-specific documents require actual content and visual inspection.

Earlier migration checks verified posting integrity, private state, ranking and
outcome rules. Disabling the outcome-confirmation guard made its regression fail;
the guard was restored. The English edition preserves source names, external API
values, multilingual parser fixtures, the original copyright, and the MIT license.

## Source verification limits

The shared 54-source registry records 42 verified official pages/docs, 11 official
indexed confirmations with fetch limitations, and 1 blocked source. These are
source-level checks, not verification of every vacancy or program. Each real search
must verify the specific employer, program or institution, current cycle, deadline,
funding and requirements. No real application, payment, email or referee contact
was made during verification. Live connector behavior depends on the selected
host's tools and account access.

## Reproduce

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -t . -v
python3 tools/sync_claude_skills.py --check
python3 tools/lint_skills.py
python3 tools/security_guards.py
```

For each `.agents/skills/<portal>/cli`, when Bun is available:

```bash
bun install --ignore-scripts
bun run typecheck
bun test --timeout 30000
```

For an interactive runtime smoke check, use a disposable copy of the repository:
launch `codex` and invoke `$career-setup`, or launch `claude` and invoke
`/career-setup`. Start without a saved track, then explicitly select each track.
Check that the first prompt offers all three paths, the matching guide is used,
and personal state stays under `workspace/`. Resume the same workspace in the
other host and check the saved profile before generating a source/search plan.
Raw session logs and test workspaces are private scratch artifacts, not distributed.
