# Shared US career workflow

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
The mandatory search/scoring/report path is `tools/career_pipeline.py` for all three
tracks, described in `docs/SEARCH_PIPELINE.md`. Its run ledger and receipt govern
completion; direct `career.py record` writes are not a substitute. For optional
legacy industry `rank_state.py` use pass `--state BASE/job_scraper/seen_jobs.json`
on every subcommand and `--tracker BASE/job_search_tracker.csv` on `candidates`.
Graduate and academia do not call its fixed industry scoring calculation.
For legacy industry location/language fields map canonical `VERIFY` to `FLAG`;
keep `PASS`/`FAIL` as-is. Keep canonical gates and explanations in opportunities.json.
Apply hard eligibility failures before invoking the numeric scorer; do not let a
high score override them. Partial scores use the shared scorer's null dimensions,
range and evidence coverage, not invented values passed to rank_state.

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

Search means **discover → record all leads → assess every lead → complete and check
the all-results report** in both runtimes. Read `docs/SEARCH_PIPELINE.md` for exact
commands and schemas. Ranking and HTML reporting are included in this authorization,
not optional follow-ups. Never apply a candidate quota or the legacy top-N defaults.

1. Read `config/us_sources.json` and `docs/US_SOURCES.md`; select the active track.
   Generate a starting plan with `tools/career.py search-plan --track <selected-track> --query '<field>'`
   (add `--cycle '<term year>'` for admissions). It emits queries, not search results.
2. Start a private run with `tools/career_pipeline.py start`, preserving the user's
   exact request, explicit exclusions and any explicitly requested search budget.
   Actually search using available web tools. ATS documentation entries explain adapters, not vacancy indexes. Resolve each
   employer’s actual board from its official careers page; do not search API docs
   as though they were job listings. Start with 3 complementary discovery
   sources and official sites; expand to society/field boards and institution lists.
   Three is a starting number of sources, never a limit on candidates. Log every
   returned lead with `batch` before judging fit, including weak, provisional,
   duplicate and inaccessible leads. Each further page/batch must be ingested too.
   Continue under the validated stop rules in the pipeline guide: provided corpus
   accounted for, explicit user batch budget reached, or at least three sources
   followed by two varied successful batches adding no new IDs. No new verified
   matches is insufficient if unverified new leads are still being discovered.
   Record access/resource interruption as blocked and incomplete. Report queries,
   sources tried, duplicates and failures. Never manufacture empty batches.
3. Prefer primary employer careers/ATS, department/program admissions, lab or HR
   pages. Aggregators and research databases suggest leads; they do not prove
   active openings, current-cycle requirements, funding or faculty availability.
4. Assess every recorded lead. Fetch primary pages, run the inherited posting integrity gate, and
   retain URL, retrieved date, full source text and supporting excerpts. Closed is
   distinct from unreachable. Recheck before ranking/drafting. Report unverified
   leads visibly with evidence and next action. Do not bypass login, CAPTCHA,
   robots or access restrictions. Do not silently discard a low-fit lead or treat
   sponsorship uncertainty as a reason to omit an otherwise evidenced fit score.
5. Deduplicate by institution/employer + posting/program ID + campus + cycle, using
   `tools/job_key.py` where suitable for industry. One campus/program can have
   separate degrees, delivery modes and deadlines; never merge these blindly.
6. Industry may reuse applicable `job-scraper` fetch, parsing, source-history and
   optional enabled CLI details after this US discovery step. Its legacy candidate
   selection, quick-fit-only scoring and selective presentation do not apply. Danish demos are not part of this US workflow. LinkedIn
   and other restricted boards are manual discovery by default. Do not auto-run
   every installed portal. Job recency is a preference, never an admissions cutoff.
7. Use `assess` to persist every lead's gates, reasons and evidence. Score eligible
   and provisional leads using all track dimension keys; a known subset yields
   a range, never a reweighted total. Explain each legitimate unscored disposition.
   All-null or missing assessments remain pending and block completion.
   For industry, ordinary skills, function, experience and seniority gaps reduce
   fit; they do not permit an unscored exclusion. `excluded` requires the supported
   `hard_gate` contract in the pipeline guide, including a requirement quote,
   confirmed candidate contradiction and matching evidence URL. User-constraint
   and compensation exclusions must cite an exact initial scope exclusion. No
   generic hard-gate category exists. Ambiguous eligibility stays VERIFY and the
   known fit dimensions must still be scored.
8. Record the stop reason, run `complete`, then `check`. The helper exports additive
   opportunity records, all-results HTML/JSON and a receipt. Confirm every unique
   discovered lead is displayed by default, including excluded, closed, duplicate,
   unreachable and provisional rows. No status filter, pagination or top-N cap may
   hide rows on first load. The summary must reconcile observations, discovered,
   assessed, scored, unscored, pending and displayed counts and link the full report.
   When validation fails, resolve it or run `report` to save an INCOMPLETE artifact;
   never describe it as a completed search. A chat shortlist may supplement the
   complete table but must not replace it. Never claim exhaustive market coverage.
   No network available: produce a query plan and an explicitly incomplete run,
   say live opportunities have not been verified, and allow pasted official content.

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
- Search rankings and reports for every track read the selected pipeline run;
  `opportunities.json` remains the cross-run application lifecycle record. Do not
  feed graduate/academia lifecycle or weighting to the industry-only CSV/rank_state
  pipeline. The shared helper renders the complete escaped results table.
- `career-rank` resumes assessments in the selected search run and regenerates its
  validated report; `career-html-report` regenerates the same all-results report.
  Both use `docs/SEARCH_PIPELINE.md`. Legacy CSV dashboards remain optional for
  application history, not replacements for complete search results. Reranking or
  adding batches invalidates the old receipt until `complete` and `check` pass again.

## Optional workflows and runtime translations

`$ARGUMENTS` means the user's supplied arguments, not a shell variable. Use the
current host's tools and native invocation syntax:

| Capability | Codex | Claude Code |
|---|---|---|
| Project instructions | `AGENTS.md` | `CLAUDE.md` imports `AGENTS.md` |
| Skills | `.agents/skills/`; `$career-setup`, `$career-search`, etc. | `.claude/skills/`; `/career-setup`, `/career-search`, etc. |
| Shared skill content | Read the canonical `.agents/skills/<folder>/SKILL.md` | The Claude adapter reads that same canonical file; resolve sibling references from its canonical directory |
| Delegation | Available Codex subagent tool | Available Agent/Task tool with a supported general-purpose agent type |
| Web and connectors | Available web search/browser and connected tools | Available WebSearch/WebFetch/browser and MCP/connected tools |

Inherited `/setup`, `/apply`, etc. labels name reference procedures; use the
`career-*` skills above for native invocation. Read a canonical skill file as
instructions; do not invoke the other host's skill syntax or tool APIs.

`agents/<role>.md` files are read-only task contracts, not registered custom
subagents. Read the contract and pass it to an available agent; do not assume the
role's filename is a supported `subagent_type`. Before dispatch, expand every
profile/output path in its prompt to the selected BASE and pass the track and
rubric inline. A fresh-context reviewer must never ground claims against source
templates or another track's files. If delegation is unavailable, run a separate
review pass and identify it as self-review. Tools and permissions are controlled
by the active host and the user's settings, not these reference files. Do not
change runtime permission settings as part of career work.

Before raw page fetches, create a system temporary directory with Python tempfile
or `mktemp -d`, assign its returned path to task-specific `CAREER_SCRATCH`, and pass
that path explicitly. Do not assume a host-provided SCRATCHPAD variable. `fetch_page.py`
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
