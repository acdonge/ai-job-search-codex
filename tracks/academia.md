# United States academic employment (`academia`)

Keep the upstream **setup → search → rank → apply → interview → outcome** sequence,
including guarded source fetching, evidence-based fit, independent draft review, PDF
inspection and application history. Use `workspace/profile.json` → `profiles.academia`;
switching `active_track` must not overwrite the industry or graduate profile. Converse
in English by default, honoring explicit user preferences, with English application materials
unless the institution requests otherwise.

Read `workflows/codex.md` for the runtime/path contract. Set `BASE=workspace/academia`:
private profile sources belong in `BASE/profile/`, dossiers in `BASE/documents/`.
Write `BASE/opportunities.json` through
`python tools/career.py record --file <private-record.json>`, with `title`, `organization`,
`url`, `status`, gates, evidence, deadlines, score coverage and material paths. A cycle
or search ID helps identify the search. Do not pass this track's rubric to the
industry-specific `tools/rank_state.py` schema.

## Setup: separate three academic markets

Ask which `academic_role` applies before collecting the relevant details:

| Role | Clarify |
|---|---|
| `faculty` | Tenure-track/tenured, teaching/clinical/practice faculty, visiting/adjunct; discipline, rank, institution type, teaching/research balance |
| `postdoc` | Research area/methods, doctoral completion date, training goals, mentor/lab needs, duration and start date |
| `research_staff` | Research scientist/engineer, staff scientist, lab manager or other staff role; contribution, scope, employment classification and career path |

Then collect `field`, `subfields`, `research_agenda`, `education`, `experience`,
`publication_record`, `grants`, `teaching`, `mentoring`, `service`, `methods`, `languages`,
`locations`, `start_date`, `compensation_minimum`, `work_authorization`,
`sponsorship_needed`, `deal_breakers` and `career_goals` as applicable. For grants record
PI/co-PI/other role, status, amount attribution and dates accurately. For publications
distinguish published/accepted/preprint/under review/in preparation and confirm author
order. A faculty opening may accept ABD candidates by a particular date; do not assume
either that all require a completed PhD now or that all accept ABD candidates.

Record verified contact/referee facts privately, including consent to contact. Ask only
for a practical work-rights summary; do not collect passport/SSN/visa-document numbers.
New confirmed candidate facts belong in the private profile before future drafting.

## Search: discipline and appointment type govern the sources

Use `academia` sources in `config/us_sources.json`: official university HR and department
pages, national-laboratory/research-institute careers, higher-education boards, academic
application systems, disciplinary society boards and postdoctoral sources. Faculty
directories and papers identify research connections; they do not prove a vacancy.
Include teaching-focused and research-focused institutions according to the user's goals.

Find the institution's official posting independently and reconcile aggregator differences.
Deduplicate by institution + requisition/search ID + rank/appointment, keeping separate
departmental searches separate. Record title, role subtype, rank, tenure status if stated,
department, location, appointment duration, start date, teaching expectations, required
materials, salary/stipend basis, benefits, sponsorship wording and canonical URL. “Open
rank” is not necessarily tenure-track; “research scientist” is not necessarily faculty.

Store the exact deadline language and distinguish **full-consideration/review-begins
date**, **hard close date**, **reference deadline**, and **open until filled**. A passed
review-begins date warrants a late-application flag, not an automatic closed status.
Capture timezone if given, verification date, source snapshot and current open-status
evidence. A date-only cutoff does not authorize inventing a time or timezone.

Use the inherited fetch escalation and `tools/posting_guard.py`. Unreachable/login-walled
sources remain unverified, never scored from their title. Lab grants, departmental news
and historic listings do not prove available funding, visa sponsorship or mentor capacity.
Report both searched sources and inaccessible coverage.

## Rank: evaluate mandatory conditions before fit

Gates are **PASS / FAIL / VERIFY** with requirement excerpts and candidate evidence.
FAIL requires a confirmed contradiction; a missing fact means VERIFY. Do not score a
failed opportunity. Provisional opportunities remain visible with the unresolved condition,
not labelled eligible. Separate research fit from formal permission to hold the role.

1. **Live opening and timing:** distinguish active search, review begun, hard deadline
   passed, vacancy filled and inaccessible source. Confirm start-date feasibility.
2. **Degree/rank/experience requirements:** degree completion by the stated date,
   discipline, professional licensure or postdoc eligibility window if explicitly required.
   A local program's years-since-PhD rule must not be generalized to every postdoc.
3. **Appointment/work authorization:** the exact employer and appointment type's stated
   requirements. Government fellowship eligibility can differ from staff employment;
   institutional international services guidance does not guarantee a specific appointment.
4. **Location, workload and appointment duration:** apply the user's confirmed hard
   constraints, including mandatory on-site work and fixed-term/adjunct restrictions.
5. **Compensation/funding:** compare documented salary or stipend period and known fees
   against any hard minimum. Pending grant support is conditional; “competitive salary”
   is unknown. Verify benefits and employment/fellowship classification separately.
6. **Materials and references:** degree evidence, required portfolio, statements, teaching
   evidence or recommendation delivery must be feasible. Do not contact referees without
   authorization or fabricate their endorsement.

Choose the appropriate column before scoring. Each column totals 100:

| Dimension | Faculty | Postdoc | Research staff |
|---|---:|---:|---:|
| Research / role agenda fit | 30 | 30 | 25 |
| Evidence of scholarly or technical contribution | 25 | 25 | 25 |
| Teaching / mentoring / collaboration | 20 | 10 | 10 |
| Environment, methods and resource fit | 15 | 25 | 30 |
| Career and practical fit | 10 | 10 | 10 |
| **Total** | **100** | **100** | **100** |

For teaching-focused faculty, the user may explicitly adopt a different rubric before
ranking (for example 20/20/35/15/10); record its name and weights in the profile and use
it consistently. Do not alter weights just to improve one institution's position.
Faculty independence is evidenced by contributions and a plausible agenda, not author
position alone. Postdoc scores emphasize training and mentor alignment; research staff
scores emphasize delivery, methods and team needs. Unknown mentoring quality or access
to equipment must remain unknown rather than inferred from institutional prestige.

Each known dimension scores 0–100. Overall is `sum(weight × score / 100)`. Unknown
dimensions use `null`; show known-weight coverage and interval from known contribution
to known contribution + unknown weights. Do not silently reweight the known subset.
The inherited 75/60/45/30 bands apply only to fully evidenced scores and describe search
priority, not offer odds. Present verified eligible, provisional, excluded and unreachable
rows separately, with each URL, verification date, gap and next action.

## Apply: a dossier appropriate to the appointment

Refresh the posting, prompt wording, source evidence and current requirements. Use the
actual appointment's instructions to select materials:

| Role | Typical starting set, only when requested/applicable |
|---|---|
| Faculty | Academic CV, cover letter, research statement, teaching statement, requested service/mentoring statement, publications, references |
| Postdoc | Academic CV, focused cover letter/contact draft, research interests or proposal, selected work, references |
| Research staff | CV or resume according to posting, tailored cover letter, technical/project evidence and references |

Start from `templates/academia/academic-cv.md`, `cover-letter.md`, `research-statement.md`,
`teaching-statement.md`, `research-proposal.md`, `contact-email.md` and
`application-checklist.md`. Do not insert an unsolicited statement based on outdated
assumptions about institutional requirements. Confidential letters remain the referees'
work; a factual briefing packet is appropriate, ghostwritten endorsements are not.

Retain the upstream drafter/reviewer loop. Audit dates, degrees, citation status, grant
roles, teaching responsibility, mentoring outcomes, resource claims and personal
contribution against verified profile evidence. Separate completed research from a future
proposal. Independently confirm faculty/department claims before including them; no
invented collaboration, funding commitment, available equipment or guaranteed lab space.
Check all prompts and institution-specific AI/authorship policies before finalizing.

Render and inspect every page with the declared template toolchain. Use the inherited
PDF/text/layout verification tools with the posting's limits; **an academic CV has no
repository-wide two-page cap**. Statements have the actual requested limits. Inspect
citations, figures, equations, page breaks, text extraction and contact information.
Adapt interpretation of stock layout warnings transparently for longer CVs; do not
claim a check passed when unavailable. Archive sources, drafts and the requirement
checklist in the private workspace. A complete local dossier is **drafted**, never
**submitted** unless a user confirmation or portal receipt establishes submission.

Local drafting can proceed when requested. Sending contact emails, inviting references,
submitting forms, accepting terms or paying fees require explicit instruction for that
action. Do not promise a successful appointment, funding or visa outcome.

## Interview and outcome

- **Faculty:** screening answers, job talk, teaching demonstration where requested,
  chalk talk/research plan where applicable, mentoring examples and department questions.
  Build a realistic resource/startup discussion from the proposed research, not invented
  institutional commitments.
- **Postdoc:** explain ownership and limits of past work, next research questions, methods,
  mentor expectations, project independence, publication practices, training and duration.
- **Research staff:** methods/problem-solving examples, collaboration and delivery,
  instrument/software responsibility, project planning and scope of appointment.

Track `discovered → verified → shortlisted → drafted → submitted → interview → offer`,
with `rejected`, `withdrawn`, `expired`, `declined`, `accepted` and `hired` only when supported. Store actual
interview stages (screen, campus visit, talk) as details, not fabricated events. Silence
and a passed review-begins date are not rejection. Record outcome date and evidence.
Compare written offers by salary/stipend period, benefits, appointment term, renewal
conditions, teaching/service load, startup/resources, research independence, start date
and any stated sponsorship conditions. Keep a PI's informal enthusiasm distinct from
an authorized written appointment. Acceptance or withdrawal needs user direction.
Record factual outcome transitions using `tools/career.py record --user-confirmed`
only after actual confirmation; include the supporting evidence in the record.

## Official references checked 2026-10-19

- [NIH postdoctoral program](https://www.training.nih.gov/research-training/pd/)
  demonstrates appointment-specific eligibility, funding terms and international support.
  Its requirements apply to that program, not all US postdoctoral positions.
- [Stanford faculty-career resources](https://careered.stanford.edu/resources)
  identifies distinct academic application materials and preparation resources.
- [Harvard postdoc application-material guidance](https://postdoc.fas.harvard.edu/preparing-your-materials)
  provides academic writing context; the actual vacancy determines the required documents.

These references support the workflow. Recheck the live vacancy and institutional policy
for every application rather than treating this date as current vacancy verification.
