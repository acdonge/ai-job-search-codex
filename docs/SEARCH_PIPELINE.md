# Complete US search, assessment and results

Codex and Claude Code use the same `tools/career_pipeline.py` commands and private
files. `career-search` means **discover → record → assess → complete → check**.
Ranking and the all-results report are part of the search request. Do not pause
for another rank/report instruction. No candidate quota, default top-N cutoff or
default hidden status filter applies. The inherited scraper/rank/dashboard bodies
are optional legacy references; their limits never override this pipeline.

## What completion means

A completed run accounts for every recorded discovery, has an assessment for every
unique lead, uses the selected track's rubric, has a justified stopping condition,
and displays every lead in its HTML and JSON results. Repeated observations remain
in the batch history even when they resolve to the same lead. Distinct duplicates
remain visible with a link to the canonical lead. Weak fit, unknown sponsorship
and incomplete candidate facts are not reasons to silently remove a result.

The helper rejects missing assessments, unsupported scores, unaccounted provided
URLs, invalid stops and missing report rows. Adding a batch or changing an
assessment invalidates the prior receipt until completion is validated again.
Every `batch`, `assess` and `stop` write immediately regenerates the same HTML/JSON
report paths as INCOMPLETE, including all current rows. An interrupted update therefore
cannot leave an older successful report looking current.
This is a validator for the recorded run, not a tamper-proof execution sandbox:
it cannot discover search results the assistant never recorded, establish the truth
of invented evidence, prevent arbitrary manual file edits or prove exhaustive
market coverage. Hosts must record actual tool results and retain source evidence.

## Execute the shared stages

Run commands from the repository root. Keep JSON inputs, source snapshots and
outputs under the Git-ignored `workspace/` or an explicitly selected private root.
Pass `--track` on every command; another chat may change the saved active track.
The examples below use `industry` and a placeholder `RUN_ID`; substitute the actual
ID printed by `start`. The same commands support `graduate` and `academia`.

### 1. Declare the user's scope

Initialize the selected private track with `python3 tools/career.py --workspace
workspace init --track industry` (substitute the selected track), then read its
guide and candidate profile. Preserve the exact request,
explicit scope exclusions and confirmed constraints. Do not invent exclusions for
seniority, geography or uncertainty. Put a scope object in a private JSON file:

```json
{
  "request": "Find US robotics engineering jobs, including stretch roles.",
  "mode": "open",
  "source_urls": [
    "https://www.indeed.com/",
    "https://www.linkedin.com/jobs/",
    "https://www.wellfound.com/jobs"
  ],
  "exclusions": []
}
```

These are example discovery sources, not evidence of active openings or permission
to scrape restricted sites. Select current, accessible sources for the actual field.
For a user-supplied finite list use `mode: "provided"`. Prefer `expected_leads`
with every supplied opportunity's full identity: `title`, `organization`, `url`
and `cycle` (required for graduate admissions). Completion requires every expected
identity, so one program cannot stand in for a different degree or entry cycle on
the same page. For a corpus with exactly one opportunity per URL, a unique
`expected_urls` list is also accepted; repeated URLs in that list are rejected.
Do not remove repeated URLs to disguise separate opportunities: use `expected_leads`.

Example provided scope for an MS and PhD sharing an admissions URL (synthetic only):

```json
{
  "request": "Compare both supplied robotics degrees for Fall 2027.",
  "mode": "provided",
  "source_urls": ["https://example.com/robotics/admissions"],
  "exclusions": [],
  "expected_leads": [
    {
      "title": "Robotics MS",
      "organization": "Example University",
      "url": "https://example.com/robotics/admissions",
      "cycle": "Fall 2027"
    },
    {
      "title": "Robotics PhD",
      "organization": "Example University",
      "url": "https://example.com/robotics/admissions",
      "cycle": "Fall 2027"
    }
  ]
}
```

Record and assess both identities in discovery batches. `provided_complete` fails
if either is missing, even though their URL is identical.
For a user-requested search budget, the optional `user_limit` is
`{"batches": 4, "quote": "Please search four batches."}`. Keep the user's actual
quote; a model's wish to save effort is not a user limit. There is no result-limit
field. A user who wants a short summary still receives a complete underlying report.

```bash
python3 tools/career_pipeline.py --workspace workspace start --track industry --query "robotics engineering" --scope workspace/scope.json
python3 tools/career_pipeline.py --workspace workspace rubric --track industry
# Academia additionally requires --academic-role faculty, postdoc or research_staff:
python3 tools/career_pipeline.py --workspace workspace rubric --track academia --academic-role postdoc
```

### 2. Search and record before judging fit

Use actual host web tools and the registry in `config/us_sources.json`. A search
plan is not a searched batch. Start with complementary sources and expand using
role synonyms, societies, departments and official institution/employer pages.
Three sources is a starting coverage requirement, never three candidates.
Before claiming saturation, attempt every source declared in `scope.source_urls`
and record its batch using that exact source URL; put the executed query and any
redirect/detail URL in the batch note or evidence. A declared source cannot be
silently dropped after other sources produce results. An explicit user batch
budget may stop earlier, but must use `user_limit` rather than claim saturation.
Preserve every returned opportunity, including ones you expect to reject, before
fit filtering. Source pagination is a sequence of batches, not permission to drop
a page. Log unavailable sources as blocked batches; never manufacture empty ones.

A batch JSON object has this shape. `example.com` here denotes a synthetic example,
not a vacancy; production entries must come from actual retrieved results.

```json
{
  "source_url": "https://example.com/careers",
  "query": "robotics engineering",
  "checked_on": "2026-10-19",
  "access": "ok",
  "note": "Synthetic schema example only; replace with actual search evidence.",
  "results": [
    {
      "title": "Robotics Engineer — requisition DEMO-1",
      "organization": "Example Organization",
      "url": "https://example.com/careers/demo-1"
    }
  ]
}
```

```bash
python3 tools/career_pipeline.py --workspace workspace batch --track industry --run RUN_ID --file workspace/batch.json
python3 tools/career_pipeline.py --workspace workspace status --track industry --run RUN_ID
```

`status` returns rows with stable `id` values. The same canonical URL, title and
cycle reuse an ID while retaining observations. Preserve distinct requisition,
program, campus and cycle identities; include `cycle` for graduate entries. When
different URLs represent one opportunity, keep both records and mark the secondary
one `duplicate` with `duplicate_of` set to the canonical lead ID.

Fetch official evidence for every lead. Apply `tools/posting_guard.py` before
reasoning over fetched or pasted content. Preserve cleaned source snapshots,
excerpts, URLs, checked dates, exact deadlines and timezones privately. Respect
robots, login and CAPTCHA restrictions. An unreachable page is not a closed role.
An aggregator, paper or faculty grant does not prove current vacancy, admissions
availability, guaranteed funding or sponsorship. Retain the track's detailed gates.

### 3. Assess every lead

Use the candidate's verified facts and actual source content. The scorer calculates
totals from evidenced dimension values; the assistant is responsible for the
judgments and reasons. Do not score from a title alone. Fetch/update evidence as
needed. Review assessments for source grounding and check every discovered ID.

Each assessment needs a `disposition`, reason and source evidence. Eligible and
provisional rows need all three summarized gates: `availability`, `eligibility`
and `constraints`, each with `verdict` and a nonempty reason. Expand their reasons
with the track-specific requirements; never turn an unknown into default PASS.

- `eligible`: all gates PASS. Fit may still have unknown dimensions; a partial
  fit range does not change the eligibility verdict.
- `provisional`: at least one VERIFY gate or a partially known score; no FAIL gates.
  Eligibility may be fully known even when one fit dimension is not.
- `excluded`: an evidence-backed FAIL gate, not merely low fit or a missing fact.
- `closed`: availability FAIL supported by closure evidence.
- `unreachable`: availability VERIFY with the actual access failure.
- `duplicate`: evidence and `duplicate_of` pointing to a different lead in this run.
- `out_of_scope`: evidence and `scope_exclusion` exactly matching a user-declared
  exclusion in the run scope. It cannot be invented after discovery.
- `pending`: missing assessment work or no known fit dimensions. It remains visible
  and blocks completion. Do not use an unscored terminal status to hide unfinished work.

#### Industry exclusions require a supported hard gate

For industry, an `excluded` assessment must include a `hard_gate` object. This is
in addition to its reason, evidence and FAIL gate. The object requires `kind`,
`requirement_quote`, `candidate_fact` and `source_url`. Quote the actual requirement,
state the confirmed candidate fact that contradicts it, and use a source URL
present in the assessment's `evidence`. Missing profile information does not
establish a contradiction. These are the only supported kinds:

| `hard_gate.kind` | Required failing gate | Additional condition |
|---|---|---|
| `work_authorization` | `eligibility` | Documented requirement contradicts confirmed authorization facts. |
| `citizenship_clearance_export` | `eligibility` | Documented condition contradicts confirmed candidate facts; do not infer a universal rule. |
| `required_degree` | `eligibility` | Explicit degree requirement contradicts confirmed credentials or completion timing. |
| `required_license` | `eligibility` | Explicit license requirement contradicts confirmed licensure facts. |
| `required_language` | `eligibility` | Explicit language requirement contradicts confirmed proficiency. |
| `explicit_user_constraint` | `constraints` | `hard_gate.user_constraint` exactly matches an initial `scope.exclusions` entry. |
| `hard_compensation` | `constraints` | `hard_gate.user_constraint` exactly matches an initial `scope.exclusions` entry; compare a documented amount with the user's confirmed hard minimum in equivalent units. |

There is no experience, skills, seniority or generic `other` exclusion kind. Ordinary
qualification and functional-background gaps belong in fit dimensions, with a low
or zero value when evidence supports it. Preserve and provisionally score these
leads instead of converting a "required experience" bullet into an unscored
exclusion. If eligibility remains ambiguous, use VERIFY and score the known fit
dimensions. Do not fabricate a hard gate, candidate fact or user constraint to make
validation pass. Closed, unreachable, duplicate and declared out-of-scope records
retain their own evidenced dispositions; those statuses must not disguise a fit gap.

Older industry exclusions without structured proof remain readable but appear as
`pending` with **Requires reassessment**. They cannot pass `complete` or `check`.
Repair them through `assess`: supply a supported, evidenced `hard_gate` only when
one actually applies, or replace the exclusion with a scored provisional assessment
using VERIFY for unresolved eligibility. Then rerun `complete` and `check`. Preserve
the existing run and discovery history; no manual JSON edits or deletion are needed.

A numeric fit score is not an eligibility verdict or an admission/offer probability.
Unknown sponsorship can coexist with a grounded technical score. Every unknown
dimension has `value: null` and explains what is missing; never insert 50 or
renormalize known dimensions to 100. `score` contains lower/upper bounds, coverage,
weights and, only when fully known, an overall value and band. An all-null assessment
remains pending. Legitimate terminal unscored rows retain their reason and evidence.

Example assessment (synthetic only; substitute a real run ID and actual evidence):

```json
{
  "assessments": [
    {
      "id": "REPLACE_WITH_ID_FROM_STATUS",
      "disposition": "provisional",
      "reason": "Synthetic example: documented project fit; sponsorship and working environment require verification.",
      "evidence": [
        {
          "url": "https://example.com/careers/demo-1",
          "note": "Synthetic fixture text requires Python and robot controls; candidate fixture documents both.",
          "checked_on": "2026-10-19"
        }
      ],
      "gates": {
        "availability": {"verdict": "PASS", "reason": "Synthetic fixture explicitly describes an open application."},
        "eligibility": {"verdict": "VERIFY", "reason": "Synthetic fixture does not state sponsorship policy."},
        "constraints": {"verdict": "PASS", "reason": "Synthetic fixture location and start date match the candidate fixture."}
      },
      "dimensions": {
        "technical": {"value": 80, "reason": "Candidate fixture has Python and robot-controls project evidence."},
        "experience": {"value": 70, "reason": "Candidate fixture covers implementation but has less deployment scope."},
        "behavioral": {"value": null, "reason": "Working arrangements and team expectations are unknown in the fixture."},
        "career": {"value": 90, "reason": "Robot-controls responsibilities match the candidate fixture's stated goals."}
      }
    }
  ]
}
```

This example yields **68.5–83.5 / 100, 85% coverage**. Sponsorship remains VERIFY
separately. Use these exact dimension keys and weights, or query `rubric`:

| Track/role | Dimensions and weights |
|---|---|
| Industry | `technical:30`, `experience:25`, `behavioral:15`, `career:30` |
| Graduate | `preparation:25`, `program_fit:30`, `potential:20`, `resources:15`, `goals:10` |
| Academia / faculty | `agenda:30`, `contribution:25`, `teaching:20`, `environment:15`, `career:10` |
| Academia / postdoc | `agenda:30`, `contribution:25`, `teaching:10`, `environment:25`, `career:10` |
| Academia / research_staff | `agenda:25`, `contribution:25`, `teaching:10`, `environment:30`, `career:10` |

```bash
python3 tools/career_pipeline.py --workspace workspace assess --track industry --run RUN_ID --file workspace/assessments.json
python3 tools/career_pipeline.py --workspace workspace status --track industry --run RUN_ID
```

Read pending IDs and validation errors. Continue until every lead has a supported
assessment; batch writes are atomic. Missing candidate information does not justify
skipping the whole assessment when some dimensions have evidence.

### 4. Record why searching stopped

Use only a supported reason with an accurate note:

| Reason | Required evidence |
|---|---|
| `saturated` | Every declared source attempted; at least three distinct source URLs searched successfully; the last two successful, varied query/source batches added zero new lead IDs. Newly discovered unverified leads still count as new. This is local saturation, not exhaustive market coverage. |
| `provided_complete` | Every full identity in `expected_leads`, or each unique URL in a one-opportunity-per-URL `expected_urls` corpus, is accounted for. |
| `user_limit` | The user explicitly specified a batch budget in the initial scope and that budget has been reached. Every lead found within it still needs assessment and display. |
| `blocked` | Access, missing evidence, runtime limits or another interruption prevents continuing. Always incomplete; preserve the exact reason and pending work. |

```bash
python3 tools/career_pipeline.py --workspace workspace stop --track industry --run RUN_ID --reason saturated --note "Three sources searched; the last two distinct query/source batches returned only already-recorded leads."
```

This command is an example of the correct shape, not permission to assert saturation
without the recorded batches. Never choose a user-limit or out-of-scope reason just
to reduce work.

### 5. Complete, inspect and deliver the entire report

```bash
python3 tools/career_pipeline.py --workspace workspace complete --track industry --run RUN_ID
python3 tools/career_pipeline.py --workspace workspace check --track industry --run RUN_ID
```

Only successful `complete` and `check` permit a completion claim. The helper writes
`workspace/<track>/reports/<run-id>/index.html`, `results.json` and a completion
receipt, and additively exports opportunities without overwriting confirmed outcomes.
Exports preserve each run's assessment under `search_assessments[run_id]`; the current
assessment reflects the most recent run. Completing a newer search does not invalidate
an older run's `check`, which verifies its own preserved assessment history.
Inspect that report: every unique discovered lead appears once, with its disposition,
score/range and coverage or unscored reason, eligibility, source evidence and next step.
All rows must be visible initially, including low scores, excluded/closed records
and inaccessible sources. No pagination or top-N cap. Filters are optional user
controls with a shown/total count and reset-to-all; the report also works without JS.

The final response links the full report and machine-readable results, reconciles
observations / discovered / assessed / scored / unscored / pending / displayed,
explains the stop reason and states access gaps. A concise highlight list is allowed
as an addition. It cannot replace the all-results table or imply excluded rows vanished.

When validation cannot pass, preserve an explicit partial deliverable instead:

```bash
python3 tools/career_pipeline.py --workspace workspace report --track industry --run RUN_ID
```

This does not issue a successful completion receipt. Deliver it as **INCOMPLETE**,
with pending IDs, failures and next steps. Do not remove difficult rows to make
`complete` pass. Resume the same run after more evidence or access becomes available.

## Executable offline demonstration for all three tracks

The following Python script runs the same helper sequence for industry, graduate
and academia/postdoc using one synthetic provided lead per track. It does not search
the web, verify real openings, represent applicant data or test a host's browsing.
All fixtures say they are synthetic; never import them as genuine opportunities.
Run from the repository root with Python 3.10+. Use a separate private demo workspace.

```bash
python3 - <<'PY'
import datetime
import json
import subprocess
import sys
from pathlib import Path

workspace = Path("workspace/pipeline-demo")
inputs = workspace / "inputs"
inputs.mkdir(parents=True, exist_ok=True)
today = datetime.date.today().isoformat()

def write(name, data):
    path = inputs / name
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return str(path)

def command(*args):
    result = subprocess.run(
        [sys.executable, "tools/career_pipeline.py", "--workspace", str(workspace), *args],
        text=True, encoding="utf-8", capture_output=True, check=True,
    )
    return json.loads(result.stdout)

for track in ("industry", "graduate", "academia"):
    subprocess.run(
        [sys.executable, "tools/career.py", "--workspace", str(workspace), "init", "--track", track],
        text=True, encoding="utf-8", capture_output=True, check=True,
    )
    url = f"https://example.com/synthetic/{track}"
    scope = write(f"{track}-scope.json", {
        "request": f"Synthetic {track} provided-corpus demonstration only.",
        "mode": "provided", "source_urls": ["https://example.com/synthetic"],
        "exclusions": [], "expected_urls": [url],
    })
    role = ["--academic-role", "postdoc"] if track == "academia" else []
    started = command("start", "--track", track, "--query", "synthetic demo", "--scope", scope, *role)
    run = started["run_id"]
    weights = command("rubric", "--track", track, *role)["weights"]
    lead = {"title": f"Synthetic {track} fixture", "organization": "Example fixture", "url": url}
    if track == "graduate":
        lead["cycle"] = "Fall 2027"
    batch = write(f"{track}-batch.json", {
        "source_url": "https://example.com/synthetic", "query": "synthetic demo",
        "checked_on": today, "access": "ok", "note": "Offline fixture, not real search evidence.",
        "results": [lead],
    })
    command("batch", "--track", track, "--run", run, "--file", batch)
    row = command("status", "--track", track, "--run", run)["rows"][0]
    assessment = write(f"{track}-assess.json", {"assessments": [{
        "id": row["id"], "disposition": "eligible",
        "reason": "Synthetic fixture explicitly satisfies every demo gate.",
        "evidence": [{"url": url, "checked_on": today, "note": "Synthetic evidence for offline helper demonstration only."}],
        "gates": {key: {"verdict": "PASS", "reason": f"Synthetic fixture stipulates {key}; not a real-world claim."}
                  for key in ("availability", "eligibility", "constraints")},
        "dimensions": {key: {"value": 80, "reason": f"Synthetic fixture stipulates evidence for {key}; not a real assessment."}
                       for key in weights},
    }]})
    command("assess", "--track", track, "--run", run, "--file", assessment)
    command("stop", "--track", track, "--run", run, "--reason", "provided_complete",
            "--note", "The single synthetic provided URL is recorded and assessed.")
    command("complete", "--track", track, "--run", run)
    checked = command("check", "--track", track, "--run", run)
    print(track, run, checked["counts"])
PY
```

For live use, replace the fixture generator with actual host discovery batches and
evidence-grounded assessments. Use each track's intake and source requirements;
sharing the pipeline does not make corporate hiring, graduate admissions and
academic employment interchangeable.
