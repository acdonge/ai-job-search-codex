# Verification of the shared US career workspace

Date: 2026-10-19. Original source: MadsLorentzen/ai-job-search,
commit `2e90272d8d456df56c16a286eab127d2951f783c`.

## Dual-runtime checks

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

## Live runtime evidence

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

[Hosted CI on the starting snapshot](https://github.com/acdonge/ai-job-search-codex/actions/runs/39313498865)
passed Linux Python 3.10–3.14, the six portal jobs, and both LaTeX smoke jobs
(texlive-latest and debian-bookworm). Its Windows failures are described above.
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
