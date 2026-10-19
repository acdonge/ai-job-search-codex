# Codex runtime and three-track dispatch

Read this file before any career skill or inherited workflow. These adaptation
rules govern all migrated instructions, including direct invocation of upstream
skills. They override upstream country defaults, profile writes and tool names.

## Selection and private state

Follow AGENTS.md's first-chat selection gate. Pin the selected track in this chat and
pass it explicitly on source queries and record writes; another chat may change
the saved active_track. Do not reinterpret an existing task using a changed active_track. Run `tools/career.py init --track …`
only after selection; rerunning is non-destructive. Read `workspace/profile.json`:
`active_track` selects `industry`, `graduate` or `academia`; `profiles[track]` stores
field-specific intake values. Read `tracks/<track>.md` for intake, gates and outputs.
Only collect necessary data. Do not ask for SSNs, passport numbers or passwords.

`BASE = <repo>/workspace/<active_track>`. All commands execute from the repository
root; all private file paths are resolved explicitly as follows:

| Inherited reference | Actual private path |
|---|---|
| templates/candidate-profile.md | BASE/profile/candidate-profile.md |
| .agents/skills/job-application-assistant/01–09 reference files | Read BASE/profile/<same filename> after initialization; the tracked versions are templates only |
| search-queries.md | BASE/profile/search-queries.md |
| cv/, cover_letters/ | BASE/cv/, BASE/cover_letters/ |
| documents/ | BASE/documents/ (user may also explicitly authorize importing the root documents folder) |
| job_scraper/seen_jobs.json | BASE/job_scraper/seen_jobs.json |
| job_search_tracker.csv | BASE/job_search_tracker.csv (industry legacy tracker) |
| company_research/, upskill/, reports/, gmail_sync/ | corresponding BASE subfolder |

Use absolute or repo-root-relative expanded paths, not the literal `BASE` string.
Do not change cwd into a skill directory. Shared source tools/templates remain at
repo root. Private TeX cover classes/fonts are copied by init so relative imports work.
For the industry `rank_state.py` helper pass `--state BASE/job_scraper/seen_jobs.json`
on every subcommand and `--tracker BASE/job_search_tracker.csv` on `candidates`.
Graduate and academia do not call its fixed industry scoring calculation.
For legacy industry location/language fields map canonical `VERIFY` to `FLAG`;
keep `PASS`/`FAIL` as-is. Keep canonical gates and explanations in opportunities.json.
Apply hard eligibility failures before invoking the numeric scorer; do not let a
high score override them. Incomplete scores stay provisional outside rank_state.

The shared cross-track record is `BASE/opportunities.json`, written by
`python3 tools/career.py record --track <selected-track> --file <record.json>`. Minimum fields: `title`,
`organization`, `url`; graduate also requires `cycle` (e.g. Fall 2027).
Keep program/position ID, posting ID, campus and cycle distinct in titles when one
URL covers multiple opportunities. Record factual evidence, raw deadline string,
timezone, access status, gates, weighted score/evidence coverage and material paths
as additional fields. Unknown values stay null. No record is auto-submitted.
Statuses: discovered, verified, shortlisted, drafted, submitted, interview, offer,
admitted, waitlisted, rejected, withdrawn, accepted, enrolled, hired, declined,
expired, unreachable. `--user-confirmed` is required for actual outcomes; use it
only when the user supplied or approved the evidence, never for a model inference.
For industry, mirror the legacy CSV status to this summary using explicit semantic
mapping (`applied` → `submitted`, `offer_declined` → `declined`); keep detailed legacy
round statuses in `legacy_status`. Existing CSV/archive remain the industry record.

## Setup

Follow inherited `workflows/setup.md` document import/interview methodology with
the private mapping above. Its tracked-file warning does not apply to this private
layout. Do not write candidate data to source files or publish it. Ask field/subfield,
then the selected track's missing intake, not generic corporate questions for a PhD.
Update private profile copies and `profiles[track]`; preserve facts for other tracks.
Every claimed skill/achievement needs candidate evidence, never a copied template.
Behavioral assessment is optional; never infer personality or protected traits.

## Search

1. Read `config/us_sources.json` and `docs/US_SOURCES.md`; select the active track.
   Generate a starting plan with `tools/career.py search-plan --track <selected-track> --query '<field>'`
   (add `--cycle '<term year>'` for admissions). It emits queries, not search results.
2. Actually search using available web tools. ATS documentation entries explain adapters, not vacancy indexes. Resolve each
   employer’s actual board from its official careers page; do not search API docs
   as though they were job listings. Start with 3 complementary discovery
   sources and official sites; expand to society/field boards and institution lists.
   Continue until the requested coverage/budget is met or two varied batches yield
   no new verified matches. Report queries, sources tried, duplicates and failures.
3. Prefer primary employer careers/ATS, department/program admissions, lab or HR
   pages. Aggregators and research databases suggest leads; they do not prove
   active openings, current-cycle requirements, funding or faculty availability.
4. Fetch promising primary pages, run the inherited posting integrity gate, and
   retain URL, retrieved date, full source text and supporting excerpts. Closed is
   distinct from unreachable. Recheck before ranking/drafting. Report unverified
   leads separately. Do not bypass login, CAPTCHA, robots or access restrictions.
5. Deduplicate by institution/employer + posting/program ID + campus + cycle, using
   `tools/job_key.py` where suitable for industry. One campus/program can have
   separate degrees, delivery modes and deadlines; never merge these blindly.
6. Industry may reuse `job-scraper` Steps 2–5 and optional enabled CLI details after
   this US discovery step. Danish demos are not part of this US workflow. LinkedIn
   and other restricted boards are manual discovery by default. Do not auto-run
   every installed portal. Job recency is a preference, never an admissions cutoff.
7. Present verified matches with evidence and unknowns, then save records. Never
   claim exhaustive coverage. No network available: produce a query plan and say
   live opportunities have not been verified; allow pasted official content.

## Rank, apply, interview and outcome

- **Industry:** use migrated `workflows/rank.md`, `apply.md`, `interview.md`,
  `outcome.md` with the private mapping; `tracks/industry.md` controls US gates,
  compensation and truthful resume conventions. Keep upstream deterministic job
  scoring compatibility (technical 30, experience 25, behavioral 15, career 30)
  when using rank_state. Track guide must use the same weights.
- **Graduate:** follow `tracks/graduate.md` and `templates/graduate/`. Evaluate
  program/research/funding fit, verified current cycle and prerequisites. Draft only
  the requested program materials, not an employer cover letter by default.
- **Academia:** follow `tracks/academia.md` and `templates/academia/`. Select faculty,
  postdoc or research staff and tailor research/teaching/service evidence accordingly.
- All three retain the original factual-grounding audit, drafter → reviewer →
  revision loop, source archive, compile/layout/text extraction checks when producing
  PDFs, and honest outcome recording. Do not invent facts or AI-tool expertise.
- Use the selected track's interview and outcome sections. Save prep packs and
  material versions under BASE/documents/applications/<opportunity-id>/.
- Graduate/academia rankings and reports read opportunities.json; do not feed their
  lifecycle or weighting to the industry-only CSV/rank_state pipeline. Render an
  accessible HTML/Markdown table with track-specific fields and escaped content.

## Optional workflows and runtime translations

`$ARGUMENTS` means the user's supplied arguments, not a shell variable. Inherited
`/foo` labels identify a workflow; Codex native invocation is `$career-foo` (search
uses `$career-search`). Read the reference rather than pretending to call a slash tool.
Never set Claude-specific `subagent_type`, `allowed-tools`, or permission settings.
Load `agents/<role>.md` as a read-only task contract for an available Codex subagent.
Before dispatch, expand every profile/output path in its prompt to the selected
BASE and pass the track and rubric inline; a fresh-context reviewer must never
ground claims against source templates or another track’s files.
Tools/permissions are controlled by the user's Codex runtime, not these files.

Before raw page fetches, create a system temporary directory with Python tempfile
or `mktemp -d`, assign its returned path to task-specific `CAREER_SCRATCH`, and pass
that path explicitly. Codex has no guaranteed SCRATCHPAD variable. `fetch_page.py`
intentionally refuses repository-local outputs. Copy approved cleaned content into
private storage only after the integrity gate. Network tools must be available;
otherwise ask for pasted source text and label access limits.

Salary: upstream `salary_lookup.py` is an optional user-supplied dataset lookup,
not a US salary provider. Only run if such a dataset exists and its currency/period
are known. Default US evidence comes from official posted ranges and BLS/O*NET.
Never convert DKK assumptions into USD or equate stipend with salary.

Reset only the selected private track, present the exact files and ask before
any destructive deletion. For profile/all scope also clear only
`profiles[selected_track]` in workspace/profile.json, restore BASE/profile/candidate-profile.md
and BASE/cv/main_example.tex from source templates, and reset private personalized
reference copies. Preserve schema_version, active_track and every other track entry.
Never claim a profile reset erases documents or opportunity history outside its scope.
The inherited documents-reset shell block is the one cwd exception: execute it
inside the explicitly selected BASE after confirmation, never the repository root. Never reset other tracks, source templates or originals.
Gmail/Notion are optional and require appropriate available connectors and explicit
user intent; discover their actual tool names. Draft messages unless sending is
explicitly authorized. Sync only selected-track records.

For optional graduate/academia Gmail or Notion work, use BASE/opportunities.json
and the selected track's lifecycle rather than the corporate CSV. Match source
messages to exact institution/program/position and cycle; propose evidence-linked
updates before recording with `record --track <selected-track> --user-confirmed`.
Use a track/cycle field in destination rows and include only the explicitly requested
data. Never infer acceptance/enrollment or accepted offers from a congratulatory
message alone. If a connector cannot express the required fields, report the limit
and preserve the local record instead of coercing it into corporate statuses.
