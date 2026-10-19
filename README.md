<p align="center"><img src="assets/mascot/pip_flight_loop.gif" alt="Pip, the courier bird" width="160"></p>

# AI Job Search — Codex & Claude Code · United States

Adapted from [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search)
to work with Codex and Claude Code for US industry jobs, MS/PhD admissions, and academic jobs.

## Quick start

```bash
git clone https://github.com/acdonge/ai-job-search-codex.git
cd ai-job-search-codex
```

Start **`codex`** or **`claude`** from this folder, or open it in Codex desktop.
Say **“Help me get started with my applications”** in either host. For explicit
invocation, use **`$career-setup` in Codex** or **`/career-setup` in Claude Code**.
At the first career interaction in each new chat, the assistant asks which path to use,
unless you have already explicitly selected one:

1. **US industry jobs** — roles, experience, location, work arrangements, eligibility,
   resumes, cover letters, and interviews.
2. **US MS/PhD admissions** — research or professional master's programs and PhDs,
   field, entry cycle, prerequisites, advisors, funding, statements, and interviews.
3. **US academic jobs** — faculty, postdoctoral, and research positions, research and
   teaching fit, funding and appointments, academic CVs, statements, and job talks.

It then asks for your field or subfield and any missing information. Conversation
and application materials default to English; an explicit user preference or a
target institution's requirements can override that default. The selection is saved
in `workspace/profile.json`. Profiles and outputs are separated into
`workspace/industry`, `workspace/graduate`, and `workspace/academia`.
Switching tracks preserves existing work. **Personal data stays in the Git-ignored
`workspace/`; tracked source templates are never personalized.**

You can also select a track from the terminal:

```bash
python3 tools/career.py init
# Explicit selection: industry | graduate | academia
python3 tools/career.py init --track graduate
```

Python 3.10+ is required. Live research requires available web search or browsing
tools. Without them, either assistant can prepare search plans and work from supplied source
text while clearly reporting what has not been verified. Sign in to your chosen
host normally; this project needs no separate API integration or project-specific key.
Both hosts use the same source registry, track guides, templates, and private
`workspace/`. You can switch hosts without converting your saved profile. Avoid
simultaneous edits to the same track from two sessions.

## Workflow

| Stage | Skill name | Purpose |
|---|---|---|
| Start or switch tracks | `career-setup` | Select a track, import documents, fill information gaps |
| Search, score and report | `career-search` | Record all discoveries, assess every lead, validate the complete results report |
| Reassess and prioritize | `career-rank` | Resume or update every assessment and regenerate the full report |
| Prepare materials | `career-apply` | Tailor documents, verify facts, review, and record drafts |
| Interview | `career-interview` | Prepare from the actual application materials and target requirements |
| Record outcomes | `career-outcome` | Record confirmed submissions, interviews, offers, and decisions |

A search automatically continues through scoring and the all-results HTML report.
It does not need a separate rank/report request. Every discovered lead stays in the
run, including provisional, excluded, closed, duplicate and unreachable entries;
all rows are visible by default. Fit scores and unknown-dimension ranges are
separate from eligibility. There is no default candidate quota or top-N cutoff.

The [shared pipeline](docs/SEARCH_PIPELINE.md) records batches, validates every
assessment and reconciles discovered/assessed/scored/unscored/pending/displayed
counts before issuing a completion receipt. Missing work yields an explicitly
**INCOMPLETE** report. This validates the recorded run, not exhaustive internet
coverage or the truth of evidence the assistant failed to collect.

Prefix each skill name with `$` in Codex or `/` in Claude Code.
Additional skills: `career-expand`, `career-upskill`, `career-html-report`,
`career-add-template`, `career-add-portal`, `career-reset`, `career-gmail-sync`,
and `career-notion-sync`. Gmail and Notion are optional and require connected tools
in the host you are using. Inherited labels such as `/setup` and `/apply` name
workflow references; use the registered `career-*` commands above.

## US sources and verification

The [source guide](docs/US_SOURCES.md) and
[machine-readable registry](config/us_sources.json) cover **54 sources** across
industry hiring, graduate admissions, and academic employment. Each entry records
access restrictions, verification evidence, a checked date, and the level of
verification. Sources include job boards, applicant tracking systems, universities,
departments, scholarly societies, laboratories, and public agencies. Add relevant
field-specific and institution-specific sources as the candidate's goals become clear.

- **Discover, verify, recheck:** a search result or aggregator listing alone does
  not establish that an opportunity is currently open.
- **Keep unknowns explicit:** never infer visa sponsorship, faculty availability,
  guaranteed funding, or admission requirements from incomplete evidence.
- **Check the correct cycle:** preserve the deadline wording, timezone, checked
  date, and application term or year.
- **Report access limits:** do not bypass login, robots restrictions, or CAPTCHAs;
  list unverified leads separately.
- **Distinguish drafting from submission:** sending messages, submitting
  applications, contacting referees, or paying fees requires explicit authorization.

```bash
python3 tools/career.py sources --track academia
python3 tools/career.py search-plan --track graduate --query "robotics control" --cycle "Fall 2027"
```

These commands produce source lists and query **plans**. The active assistant performs the actual
web research. The registry is not a claim that 54 automatic scrapers are implemented.
Original Danish portal adapters remain available for explicit optional use and are
excluded from the default US search workflow.

## Documentation and verification

- [Setup and usage](SETUP.md), [search pipeline and JSON examples](docs/SEARCH_PIPELINE.md), [verification results and limits](docs/VERIFICATION.md)
- [Shared instructions](AGENTS.md), [Claude entry point](CLAUDE.md), [runtime paths and workflow dispatch](workflows/career.md)
- [Industry](tracks/industry.md), [MS/PhD](tracks/graduate.md), [Academia](tracks/academia.md)
- [Migration map](docs/MIGRATION.md), [security and privacy](SECURITY.md)

The inherited LaTeX toolchain is optional. When available, compile PDFs and inspect
them with the original `verify_pdf.py` and `verify_layout.py` helpers. Otherwise,
provide Markdown or TeX drafts and state that PDF export is pending. The target's
current length, format, and AI-use requirements take precedence over templates.

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -t .
python3 tools/sync_claude_skills.py --check
python3 tools/lint_skills.py
python3 tools/security_guards.py
```

Skill instructions are maintained in `.agents/skills/`. The committed
`.claude/skills/` adapters point to those same instructions. After editing a skill,
run `python3 tools/sync_claude_skills.py`; CI checks that the adapters stay in sync.

Licensed under the [MIT License](LICENSE).
