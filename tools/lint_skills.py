#!/usr/bin/env python3
"""Validate Codex and Claude skills and their shared workflow references.

Run from anywhere: python tools/lint_skills.py. Requires PyYAML.
Skills are discovered in .agents/skills and .claude/skills; workflows/*.md are
shared reference procedures. This repository leaves permissions to each host.
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("lint_skills.py requires PyYAML: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []
UNSUPPORTED_PERMISSION_KEYS = {"allowed-tools", "tools", "permissions", "hooks"}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def active_markdown(text: str) -> str:
    """Exclude comments and code examples when checking the Claude import."""
    text = re.sub(r"<!--[\s\S]*?(?:-->|\Z)", "", text)
    lines = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence is not None:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            continue
        if marker:
            fence = marker[1]
            continue
        lines.append(line)
    # Markdown code spans may use multiple backticks and span lines.
    return re.sub(r"(?<!`)(`+)(?!`)[\s\S]*?(?<!`)\1(?!`)", "", "\n".join(lines))


def check_entrypoints() -> None:
    for name in ("AGENTS.md", "CLAUDE.md"):
        try:
            text = (ROOT / name).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{name}: missing or unreadable project entrypoint: {exc}")
            continue
        if not text.strip():
            errors.append(f"{name}: project entrypoint must not be empty")
        if name == "CLAUDE.md" and not re.search(r"(?<![\w@/])@AGENTS\.md(?![\w./-])", active_markdown(text)):
            errors.append("CLAUDE.md: missing active @AGENTS.md import")


def check_skill(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"{rel(path)}: missing YAML frontmatter (file must start with ---)")
        return
    end = text.find("\n---", 4)
    if end == -1:
        errors.append(f"{rel(path)}: unterminated YAML frontmatter")
        return
    try:
        data = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        errors.append(f"{rel(path)}: frontmatter is not valid YAML: {exc}")
        return
    if not isinstance(data, dict):
        errors.append(f"{rel(path)}: frontmatter did not parse to a mapping")
        return
    for key in ("name", "description"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"{rel(path)}: frontmatter missing required key '{key}' (non-empty string)")
    for key in sorted(UNSUPPORTED_PERMISSION_KEYS & data.keys()):
        errors.append(f"{rel(path)}: unsupported permission key '{key}'; this portable workflow leaves permissions to the user's runtime")
    # Native command skills point at one canonical, migrated procedure. Catch
    # a moved or mistyped procedure instead of silently invoking an empty skill.
    for target in re.findall(r"(?<![\w/])(workflows/[\w-]+\.md)", text[end + 4:]):
        if not (ROOT / target).is_file():
            errors.append(f"{rel(path)}: references a missing workflow: {target}")
    for target in re.findall(r"(?<![\w/])(\.agents/skills/[\w-]+/SKILL\.md)", text[end + 4:]):
        if not (ROOT / target).is_file():
            errors.append(f"{rel(path)}: references a missing skill: {target}")


def check_command(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").lstrip().splitlines()
    first = lines[0] if lines else ""
    # This shared dispatcher is read by command skills; it is deliberately
    # not advertised as a slash-command registration.
    if path.name in {"career.md", "codex.md"}:
        if not first.startswith("# "):
            errors.append(f"{rel(path)}: dispatcher reference must start with a Markdown title")
        return
    if not first.startswith("# /"):
        errors.append(f"{rel(path)}: workflow must start with a '# /<name>' title (found: {first[:50]!r})")


def main() -> int:
    errors.clear()
    check_entrypoints()
    codex_skills = sorted(ROOT.glob(".agents/skills/*/SKILL.md"))
    claude_skills = sorted(ROOT.glob(".claude/skills/*/SKILL.md"))
    skills = codex_skills + claude_skills
    commands = sorted((ROOT / "workflows").glob("*.md"))
    if not codex_skills:
        errors.append("no SKILL.md files found under .agents/skills/")
    if not claude_skills:
        errors.append("no SKILL.md files found under .claude/skills/")
    if not commands:
        errors.append("no workflow files found under workflows/")
    for skill in skills:
        check_skill(skill)
    for command in commands:
        check_command(command)
    if errors:
        print(f"lint_skills: {len(errors)} failure(s)")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"lint_skills: OK ({len(codex_skills)} Codex skills, {len(claude_skills)} Claude skills, {len(commands)} workflow references)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
