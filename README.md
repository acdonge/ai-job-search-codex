<p align="center"><img src="assets/mascot/pip_flight_loop.gif" alt="Pip, the courier bird" width="160"></p>

# AI Job Search — Codex · United States

Adapted from [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search)
to work with Codex for US industry jobs, MS/PhD admissions, and academic jobs.

## Quick start

```bash
git clone https://github.com/acdonge/ai-job-search-codex.git
cd ai-job-search-codex
codex
```

Alternatively, open the repository folder as a project in Codex desktop.
Say **“Help me get started with my applications”** or invoke `$career-setup`.
At the first career interaction in each new chat, Codex asks which path to use,
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
tools. Without them, Codex can prepare search plans and work from supplied source
text while clearly reporting what has not been verified. No Anthropic account or
separate project-specific OpenAI API key is required.

## Workflow

| Stage | Codex skill | Purpose |
|---|---|---|
| Start or switch tracks | `$career-setup` | Select a track, import documents, fill information gaps |
| Search | `$career-search` | Discover US opportunities, verify official sources, deduplicate |
| Compare and prioritize | `$career-rank` | Check eligibility, apply track-specific criteria, expose uncertainty |
| Prepare materials | `$career-apply` | Tailor documents, verify facts, review, and record drafts |
| Interview | `$career-interview` | Prepare from the actual application materials and target requirements |
| Record outcomes | `$career-outcome` | Record confirmed submissions, interviews, offers, and decisions |

Additional skills: `$career-expand`, `$career-upskill`, `$career-html-report`,
`$career-add-template`, `$career-add-portal`, `$career-reset`,
`$career-gmail-sync`, and `$career-notion-sync`.
Gmail and Notion are optional and require available connected tools.
Legacy names such as `/setup`, `/scrape`, and `/apply` remain conversational aliases;
they are not registered custom Codex slash commands.

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

These commands produce source lists and query **plans**. Codex performs the actual
web research. The registry is not a claim that 54 automatic scrapers are implemented.
Original Danish portal adapters remain available for explicit optional use and are
excluded from the default US search workflow.

## Documentation and verification

- [Setup and usage](SETUP.md), [verification results and limits](docs/VERIFICATION.md)
- [Codex instructions](AGENTS.md), [runtime paths and workflow dispatch](workflows/codex.md)
- [Industry](tracks/industry.md), [MS/PhD](tracks/graduate.md), [Academia](tracks/academia.md)
- [Migration map](docs/MIGRATION.md), [security and privacy](SECURITY.md)

The inherited LaTeX toolchain is optional. When available, compile PDFs and inspect
them with the original `verify_pdf.py` and `verify_layout.py` helpers. Otherwise,
provide Markdown or TeX drafts and state that PDF export is pending. The target's
current length, format, and AI-use requirements take precedence over templates.

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -t .
python3 tools/lint_skills.py
python3 tools/security_guards.py
```

Licensed under the [MIT License](LICENSE).
