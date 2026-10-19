# Direct migration provenance

Base: MadsLorentzen/ai-job-search, commit
`2e90272d8d456df56c16a286eab127d2951f783c`. The original MIT license is retained.
This repository starts from a single snapshot of the US adaptation and does
not include upstream commit history. The source mapping below documents the port;
compare against the linked upstream repository when reviewing future changes.

| Upstream | Shared Codex / Claude Code edition |
|---|---|
| CLAUDE.md as mutable profile/instructions | Shared AGENTS.md + immutable CLAUDE.md import; templates/candidate-profile.md template; private profile copies |
| .claude/skills/* | Canonical .agents/skills/* plus committed Claude adapters referencing the same instructions |
| .claude/commands/*.md | workflows/*.md, exposed through career-* skills |
| .claude/agents/*.md | agents/*.md as read-only task contracts, real session tools chosen at runtime |
| .claude/settings.json | No project runtime settings; each host uses its user-selected permission policy |
| tracked personalized files | workspace/profile.json + workspace/<track>/ private state |
| Danish default source selection | 54-source US registry, verified primary pages and access labels |
| one corporate pipeline | industry / graduate / academia, shared verification with distinct materials/gates |
| forced Claude Code name in applications | only evidence-backed actual tools may be named |
| implied SCRATCHPAD | explicit system temporary directory via CAREER_SCRATCH |

Preserved: detailed document import, factual grounding, drafting/review loop,
posting_guard, fetch_page, robots parser, job_key, rank_state, salary dataset helper,
PDF/layout verification, original corporate templates, portal code and tests,
interview/outcome/archive/sync/report procedures. Source path tests follow renames.
Obsolete Claude permission fixture tests were replaced by native metadata, private
workspace and supply-chain guards. Onboarding privacy tests now protect private
copies instead of approving edits to tracked profiles.

Industry keeps rank_state's original 30/25/15/30 rubric. Graduate/academia use their
track guides and opportunities.json, never silently reuse corporate scoring.
Original corporate detail workflows run through workflows/career.md path mapping.

The upstream version checker detects original versus native layout and maps
original .claude methodology paths to local .agents paths. It reports Codex
AGENTS.md as not comparable to the original thin pointer. It only reports changes;
use the displayed original path and this table for manual review, never an
automatic profile/settings replacement. Commit-level upstream triage is not a
reliable list of missing changes after the history reset, because the repositories
have no shared Git ancestry; keep the upstream-watch workflow disabled and review
source/version differences manually. Historical CHANGELOG.md entries describe the original
project and intentionally retain its terminology. Optional Danish adapters are
retained for provenance and explicit use but excluded from US default search.

Official Codex format reference, checked 2026-10-19:
https://learn.chatgpt.com/docs/build-skills

Both hosts share the same US behavior. `CLAUDE.md` imports `AGENTS.md`; Claude
skills delegate to the canonical `.agents/skills` files through regular Markdown
adapters, so Windows clones do not require symlink support. Run
`python3 tools/sync_claude_skills.py --check` to check adapter consistency.
`workflows/codex.md` remains a compatibility pointer to `workflows/career.md`.
The files in `agents/` are task contracts for the host's available delegation tool,
not registered custom agent types. Connector availability and PDF dependencies
remain host-specific; report limits instead of assuming capabilities.
