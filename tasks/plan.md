# Codex US three-track migration

Directly adapt upstream commit `2e90272d8d456df56c16a286eab127d2951f783c`.
Preserve its MIT attribution, detailed application pipeline, Python
fetch/integrity/PDF/state tools, document templates, and regression tests.

## Contract

- Codex discovers `.agents/skills`; AGENTS.md is the entry point. Commands become
  skills backed by migrated workflow references. No Claude runtime dependency or
  fictional permission enforcement.
- First career interaction asks industry / graduate / academia (unless explicitly
  selected). Profiles and outputs are private and isolated by track.
- Source discovery covers the US; authoritative current postings/program pages
  verify eligibility, deadlines and funding. Unknown is never silently eligible.
- Industry keeps upstream detailed pipeline. Graduate and academia provide their
  own intake, fit criteria, documents and lifecycle through the same dispatcher.

## Ordered slices

1. Move canonical instructions, update references and Codex tool semantics.
2. Add deterministic track selection and isolated private workspace; test errors,
   repeat initialization and switching without data loss.
3. Integrate track-specific workflows, templates and verified US source registry.
4. Update documentation/guards/CI and run inherited + new tests; independent review.

Parallel owners: source registry; track guides/templates; native guards and CI.
Main owns migration, dispatcher, runtime helper, integration and release package.
User's request authorizes this implementation; no additional plan approval needed.

## Verification

Baseline: 768 Python tests, OK, 23 optional-dependency skips. Verify migration
contracts, three-track CLI behavior, private ignores, native skill lint, source
schema, surviving upstream tests, available Bun fixtures and LaTeX smoke checks.
Report missing runtimes and any live access limits explicitly. Never claim that
offline tests demonstrate successful login, submission or every live portal.
