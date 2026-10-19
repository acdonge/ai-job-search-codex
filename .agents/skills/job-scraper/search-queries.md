# US search queries by selected track

Template only: personalize the copy at `workspace/<track>/profile/search-queries.md`.
Read `workflows/career.md`, the selected track guide and `config/us_sources.json`.
The registry supplies US sources and access limits; web discovery is the default.
Optional legacy CLIs run only when explicitly chosen. Do not run Danish adapters
or every installed CLI merely because its directory exists.

## Shared strategy

Use the confirmed field/subfield, synonyms, target geography and cycle. Start with
three complementary discovery sources plus official sites, then expand by discipline.
Use concise English terms for US postings; add other languages only when useful.
Candidate language proficiency comes from their profile, never from query language.
A missing proficiency is VERIFY, not an assumed failure. Explicit conflicts require
confirmed candidate facts. Record query, source, date, access failures and results.

## Industry

Group by function, not only title; use actual US state/city or remote constraints.

```text
"[YOUR_PRIMARY_JOB_TITLE_1]" "[YOUR_CITY]" careers
"[YOUR_PRIMARY_JOB_TITLE_2]" "[YOUR_KEY_SKILL]" United States
site:linkedin.com/jobs "[YOUR_PRIMARY_ROLE_TYPE]" United States
site:indeed.com "[YOUR_DOMAIN_EXPERTISE]" "[YOUR_REGION]"
site:wellfound.com "[YOUR_ADJACENT_ROLE_TYPE]"
site:usajobs.gov "[YOUR_KEY_SKILL]"
site:[OFFICIAL_EMPLOYER_CAREERS_HOST] "[YOUR_DOMAIN_KEYWORD_1]"
```

Prefer recent postings when dates exist, but retain older jobs confirmed still open.
Undated is unknown, not expired. Check work state restrictions for remote roles.
Resolve Greenhouse/Lever/Ashby board IDs from employer websites; their API docs are
adapter references, not job listings. Use a relevant state workforce or society
board from the registry for additional coverage.

## MS / PhD admissions

Use the intended **term and year**, degree and entry model; never a 14-day job filter.
Search official program, department and graduate school pages independently.

```text
site:edu "[FIELD]" "[MS_OR_PHD]" admissions "[ENTRY_YEAR]"
site:edu "[SUBFIELD]" graduate funding assistantship
site:edu "[RESEARCH_TOPIC]" faculty laboratory
site:[OFFICIAL_PROGRAM_HOST] deadline requirements "[ENTRY_TERM] [ENTRY_YEAR]"
```

Cross-check tuition, funding conditions, prerequisites, tests/waivers, faculty
availability, degree mode and separate funding deadlines. Publications/grants help
assess research fit; they do not establish an open funded seat.

## Academic employment

Choose faculty/postdoc/research staff explicitly, then discipline and start cycle.

```text
site:edu "[DISCIPLINE]" "assistant professor" "[START_YEAR]"
site:edu "[SUBFIELD]" postdoctoral position
site:higheredjobs.com "[DISCIPLINE]"
site:academicjobsonline.org "[DISCIPLINE]"
site:apply.interfolio.com "[SUBFIELD]"
site:jobs.sciencecareers.org "[RESEARCH_TOPIC]" United States
```

Add the discipline's society board and official institution/lab HR pages. Distinguish
priority review date, hard deadline and open-until-filled wording; verify the vacancy
still exists. Do not infer ongoing hiring from an old lab recruitment page.

## Output

Save full verified source snapshots and provenance privately. Separate verified,
provisional, excluded and unreachable opportunities. Show actual coverage and unknowns.
Never claim that query generation alone searched or verified any opportunity.
