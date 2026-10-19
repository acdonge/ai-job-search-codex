# Codex US setup

## 1. Open this adapted checkout

Clone [acdonge/ai-job-search-codex](https://github.com/acdonge/ai-job-search-codex),
then open its folder in Codex desktop or run `codex` from the repository root.
Clone this adaptation to get the US tracks; the original upstream repository has
its own workflow and does not contain these changes.
[Official Codex skills documentation](https://learn.chatgpt.com/docs/build-skills)
explains `.agents/skills` discovery and `$skill` invocation. If newly added skills
do not appear, reopen the project/chat. No Claude runtime/configuration is needed.

## 2. Select the track

Say “Help me get started with my applications” or invoke `$career-setup`. The first career interaction asks
industry / graduate / academia, then field/subfield. You can select explicitly:

```bash
python3 tools/career.py init --track industry
python3 tools/career.py init --track graduate
python3 tools/career.py init --track academia
```

These examples switch the active track; they do not reset any profile. Normally
run only the line for the path you want. An unattended `init` without a track exits
with a selection prompt rather than guessing. `status` displays the private profile.
Do not share its output if it contains personal data.

## 3. Provide evidence

Put permitted files under `workspace/<track>/documents/` (cv, diplomas, projects,
references, applications, postings) or explicitly point Codex at a file to import.
Use documents you have permission to process. The private profile copies are under
`workspace/<track>/profile/`; source templates remain unchanged. Ask Codex to update
only confirmed fields. Unknown values stay unknown. Private state is Git-ignored.

For graduate admissions specify MS type / PhD, field, entry term/year, interests,
course preparation and funding constraints. For academia specify faculty/postdoc/
research staff, discipline, start date, research/teaching evidence and constraints.
For industry specify roles, seniority, target geography/remote and requirements.

## 4. Search and prepare

Use `$career-search` → `$career-rank` → `$career-apply` → `$career-interview` →
`$career-outcome`. Plain-language requests work too. Pass an official URL or paste
full text when a portal is blocked. Codex records source, access status and freshness.
The registry is a starting set; add discipline-specific society and institution
sources as the user's field becomes known. Do not assume saved pages remain current.

No portal login, paid subscription or API key is required for the base workflow.
Certain optional sources/CLIs require accounts or keys; see `docs/US_SOURCES.md`.
Never insert a key in a tracked file. Optional Gmail/Notion needs a connected plugin;
without one, local files still work. There is no automatic emailing/submission.

## 5. Runtime dependencies

Python 3.10+ runs the helpers. Developer checks use:

```bash
python3 -m pip install -r requirements-dev.txt
```

The inherited optional portal CLIs use Bun. Install it through the official Bun
instructions if you choose to use them; the default US web search does not need it.
`python3 tools/install_portal_clis.py --dry-run` previews discovery and checks for
install-time scripts. Do not indiscriminately run portal adapters against restricted
sites. Fixture tests/typechecks are offline once development dependencies exist.

## 6. PDF documents

Existing `cv/main_example.tex` uses moderncv and LuaLaTeX; the cover template uses
XeLaTeX/fontspec and bundled fonts. Install TeX Live/MacTeX/MiKTeX as appropriate.
A minimal install needs moderncv, fontawesome5, geometry, fontspec, hyperref and their
TeX-distribution dependencies. Use the package manager to resolve missing packages.
Compile private copies, then run `tools/verify_pdf.py` (pypdf or `pdftotext`) and
`tools/verify_layout.py` on the resulting files. Inspect rendered pages visually.
If compilers are absent, retain drafts and clearly report PDF export is pending.

Academic CVs, SOPs and research/teaching statements follow the target's current
requirements; do not impose the stock corporate two-page CV limit on them.

## 7. Switch, resume and reset

A new chat asks whether to continue the saved track or select another. `init --track`
preserves all existing files. `$career-reset` first lists exact selected-track files
and asks before deletion. It never resets another track or the source repository.
Back up `workspace/` privately before deleting your checkout; Git does not contain it.
Do not run simultaneous profile-editing sessions against the same workspace.

## 8. Upstream and publication

This is derived from upstream commit `2e90272d8d456df56c16a286eab127d2951f783c`.
This edition has its own Git history starting from the adapted source snapshot.
Use `docs/MIGRATION.md` for the source mapping and compare upstream files separately.
Publish code only to your chosen repository; do not push to the original author's remote. A public repository must
never include personal data. `git check-ignore workspace/profile.json` should report
that path. Ignore rules do not protect already tracked files or forced additions.

Upstream `.claude` paths moved; do not blindly apply upstream profile/settings
changes. Review updates using the migration table in `docs/MIGRATION.md`. The
upstream-watch action is disabled in this adaptation; updates are a manual review.
