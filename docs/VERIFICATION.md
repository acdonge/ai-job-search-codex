# Verification of the Codex US adaptation

Date: 2026-10-19. Base: `2e90272d8d456df56c16a286eab127d2951f783c`.

## Results

| Check | Result |
|---|---|
| Full Python suite, Python 3.13 with PyYAML/openpyxl | **765 passed, no skips; rerun after English localization** |
| Six original portal TypeScript typechecks | **6 passed** |
| Six original portal mock/fixture suites, Bun 1.4.3 | **475 passed, 0 failed** |
| Native skill/workflow lint | **23 skills, 13 workflow references passed; rerun after localization** |
| Metadata/private-state/dependency guards | **Passed** |
| Local README/setup/track/documentation links and Git whitespace | **Passed** |
| Upstream version comparison using cached original layout | **Passed with path mapping; no fetch performed** |
| Mutation: disable outcome confirmation | **Regression failed as expected; original code restored** |
| Guard/source-registry mutation checks | **Detected as expected** |

Python regression evidence covers first-start no-default selection, preservation
across all three tracks, corrupted-state refusal, explicit-track isolation across
chats, admission-cycle identity, confirmed outcome preservation, malformed input,
source filtering and private template initialization. Original fetching, integrity,
CSV/archive, ranking, PDF/layout helper and salary dataset regression suites remain.
Obsolete Claude permission-contract tests were replaced by native Codex guards.

Portal counts: Freehire 116; Jobbank 56; Jobdanmark 72; Jobindex 75; Jobnet 66;
LinkedIn 90. Dependency installation disabled lifecycle scripts. These were fixture
and mock calls, not live scraping or proof of platform account access.

Independent reviews identified and resolved misleading permission claims, unknown
language/relocation gates, source-query doc hosts, cross-chat record selection,
status downgrades, reset scope, legacy FLAG mapping and upstream path comparison.

The public edition uses English documentation, startup prompts, CLI labels, and
default conversation instructions. Original source names, external API values, and
multilingual parser fixtures are preserved to maintain upstream compatibility.

## Live evidence and limits

The 54-source registry records 42 verified official pages/docs, 11 official indexed
confirmations with fetch limitations and 1 blocked source. These are **source-level
checks**, not verification of all vacancies/programs. Each real search must verify
the specific employer/program/institution, current cycle, deadline and requirements.
No applicant-specific search, eligibility ruling, login, email or submission occurred.
No unattended end-to-end LLM conversation or hosted CI matrix was executed.

Local LaTeX smoke compilation was attempted for both inherited templates. LuaLaTeX
stopped at missing `moderncv.cls`; XeLaTeX stopped at missing `titlesec.sty`. Therefore
PDF compilation/rendering is **not verified in this environment**. Both original TeX
sources, class and fonts are preserved unchanged. SETUP.md explains dependencies;
Markdown/TeX drafts remain usable, and target-specific templates need real content
and visual inspection before application submission. CI retains its TeX matrix.

## Reproduce

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -t . -v
python3 tools/lint_skills.py
python3 tools/security_guards.py
```

In each `.agents/skills/<portal>/cli`, with Bun available:

```bash
bun install --ignore-scripts
bun run typecheck
bun test --timeout 30000
```

Actual session logs were kept in the task's work directory. The distribution
contains source and this verification record; it excludes dependencies and private
workspace data. Source verification dates are in config/us_sources.json.
