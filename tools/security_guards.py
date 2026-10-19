#!/usr/bin/env python3
"""Repository checks for the Codex port; these checks are not a runtime sandbox.

Preserves upstream personal-data exclusions, dependency-manifest restrictions,
and the tracked-node_modules check. Rejects leftover Claude permission metadata,
which Codex does not enforce, instead of pretending it grants tool isolation.
Run from anywhere: python tools/security_guards.py. Standard library only.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []

# Legacy exclusions stay in place for imported workspaces. New Codex personal
# state lives in workspace/; historical agents could resolve paths at skill depth.
REQUIRED_IGNORE_RULES = [
    "salary_data.json",
    # Depth-independent: the job-scraper skill resolves `job_scraper/` relative
    # to its own directory, so the state file lands under .agents/skills/... and
    # a repo-rooted rule silently fails to match it.
    "**/job_scraper/seen_jobs.json",
    "**/job_scraper/notion_sync.json",
    "**/job_scraper/*.md",
    "*_BehavioralReport.pdf",
    "linkedin_Profile.pdf",
    "cv/main_*.*",
    "!cv/main_example.tex",
    # ATS text extractions (/apply step 5d) carry the CV's full text.
    "cv/*.txt",
    "cover_letters/cover_*.*",
    # /apply also recognizes the uppercase Cover_* naming variant.
    "cover_letters/Cover_*.*",
    "documents/cv/**",
    "documents/linkedin/**",
    "documents/diplomas/**",
    "documents/references/**",
    "documents/projects/**",
    "documents/applications/**",
    "documents/postings/**",
    # Belt-and-braces, not the primary guard: nothing writes here.
    # /interview's prep packs land under documents/applications/**, above.
    "documents/interview/**",
    "job_search_tracker.csv",
    "gmail_sync/",
    "reports/",
    "upskill/*.md",
    # Depth-independent twin of the rule above. The upskill *skill* resolves
    # `upskill/` relative to its own directory - the same observed behavior
    # the **/job_scraper rules exist for - so reports can land at
    # .agents/skills/upskill/upskill/*.md where the rooted rule cannot see
    # them. `**/upskill/*.md` would also ignore the skill's own SKILL.md
    # (the directory shares the name), so the report-file prefix is pinned.
    "**/upskill/report-*.md",
    # Not personal data but the same failure mode: /add-portal can generate a
    # skill for a portal that only returns usable content through a paid
    # fetching service, and that skill reads an API token from the environment.
    ".env",
    ".env.*",
    # Company research cache (/apply Step 3, /interview Step 2). Referenced
    # from commands, not a skill, so a plain rooted rule is correct here -
    # unlike the **/-prefixed job_scraper/upskill rules above.
    "company_research/*.json",
    # Each track holds personal profile/state/output under this private root.
    "workspace/",
]

ALLOWED_IGNORE_NEGATIONS = {
    "!cover_letters/OpenFonts/fonts/**",
    "!cv/main_example.tex",
    "!cover_letters/cover_example.tex",
    "!documents/**/.gitkeep",
}

FORBIDDEN_SCRIPTS = {"preinstall", "install", "postinstall", "prepare", "prepack"}
UNSUPPORTED_PERMISSION_KEYS = {"allowed-tools", "tools", "permissions", "hooks"}


def check_runtime_contract() -> None:
    """These are reference documents, not executable permission configurations."""
    legacy = ROOT / ".claude" / "settings.json"
    if legacy.exists():
        errors.append(".claude/settings.json: obsolete runtime configuration; Codex uses its own user-selected permissions")
    paths = list(ROOT.glob(".agents/skills/*/SKILL.md"))
    paths += list((ROOT / "workflows").glob("*.md"))
    paths += list((ROOT / "agents").glob("*.md"))
    for path in sorted(paths):
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8").lstrip("\ufeff")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{rel}: unreadable (must be UTF-8): {exc}")
            continue
        lines = text.splitlines()
        if not lines or lines[0] != "---":
            continue
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), len(lines))
        for line in lines[1:end]:
            # Keys may be quoted; only root-level metadata is interpreted.
            match = re.match(r"^[\"']?([A-Za-z0-9_-]+)[\"']?\s*:", line)
            if match and match.group(1) in UNSUPPORTED_PERMISSION_KEYS:
                errors.append(f"{rel}: unsupported permission key '{match.group(1)}'; reference frontmatter cannot restrict Codex tools")


def check_gitignore() -> None:
    path = ROOT / ".gitignore"
    try:
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    except OSError as exc:
        errors.append(f".gitignore: unreadable: {exc}")
        return
    rules = set(lines)
    for rule in REQUIRED_IGNORE_RULES:
        if rule not in rules:
            errors.append(
                f".gitignore: required personal-data rule missing: {rule!r}. "
                "These rules keep fork users from committing personal data. If the rule moved "
                "or was renamed intentionally, update REQUIRED_IGNORE_RULES in "
                "tools/security_guards.py in the same PR."
            )
    for line in lines:
        if line.startswith("!") and line not in ALLOWED_IGNORE_NEGATIONS:
            errors.append(
                f".gitignore: negation rule not in the reviewed allowlist: {line!r}. "
                "A negation re-includes a path an earlier rule excluded and can silently "
                "re-expose personal data (a required ignore rule stays present but stops "
                "taking effect). If this negation is intentional, add it to "
                "ALLOWED_IGNORE_NEGATIONS in tools/security_guards.py in the same PR."
            )


def check_package_manifests() -> None:
    manifests = [
        p for p in ROOT.glob(".agents/**/package.json") if "node_modules" not in p.parts
    ]
    if not manifests:
        errors.append(".agents: no package.json files found - glob roots are wrong or the tree moved")
    for manifest in manifests:
        relpath = manifest.relative_to(ROOT)
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{relpath}: unreadable or invalid JSON: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{relpath}: top-level JSON value must be an object")
            continue
        scripts = data.get("scripts", {})
        if not isinstance(scripts, dict):
            errors.append(f"{relpath}: scripts must be an object")
            continue
        bad = FORBIDDEN_SCRIPTS & set(scripts)
        if bad:
            errors.append(
                f"{relpath}: lifecycle script(s) {sorted(bad)} are forbidden - they execute "
                "arbitrary code during `bun install` on every fork user's machine."
            )
        if "trustedDependencies" in data:
            errors.append(
                f"{relpath}: trustedDependencies is forbidden - it re-enables dependency "
                "lifecycle scripts that bun blocks by default."
            )


def check_tracked_node_modules() -> None:
    """Fail on any tracked path with a ``node_modules`` component.

    ``.gitignore``'s old ``node_modules/`` rule matched directories only, so a
    symlink or plain file named ``node_modules`` (a contributor's local symlink
    to an absolute path, #623) was committed, broke ``bun install`` in CI with a
    dangling link, and checked out as a text file on Windows. The rule now has
    no trailing slash; this check catches what the rule cannot, such as a copy
    force-added or inherited from before the rule changed. Skipped quietly when
    the tree is not a git checkout (the guard also runs from a bare copy).
    """
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=False
        )
    except OSError:
        return
    if proc.returncode != 0:
        return
    for rel in proc.stdout.decode("utf-8", errors="replace").split("\x00"):
        if rel and "node_modules" in rel.split("/"):
            errors.append(
                f"tracked path inside node_modules: {rel!r}. Installed dependencies "
                "(or a symlink standing in for them) must never be committed: run "
                "`git rm --cached` on it; .gitignore's `node_modules` rule keeps it out."
            )


def main() -> int:
    errors.clear()
    check_runtime_contract()
    check_gitignore()
    check_package_manifests()
    check_tracked_node_modules()
    if errors:
        print(f"security_guards: {len(errors)} failure(s)")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("security_guards: OK (Codex metadata, private state exclusions, package manifests, no tracked node_modules)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
