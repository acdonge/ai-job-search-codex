#!/usr/bin/env python3
"""Validate Codex skills and their preserved workflow reference documents.

Run from anywhere: python tools/lint_skills.py. Requires PyYAML.
Skills are discovered in .agents/skills; workflows/*.md are reference procedures,
not runtime slash-command registrations. Runtime permissions belong to Codex.
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
        errors.append(f"{rel(path)}: unsupported permission key '{key}'; Codex runtime permissions are not set by skill frontmatter")
    # Native command skills point at one canonical, migrated procedure. Catch
    # a moved or mistyped procedure instead of silently invoking an empty skill.
    for target in re.findall(r"(?<![\w/])(workflows/[\w-]+\.md)", text[end + 4:]):
        if not (ROOT / target).is_file():
            errors.append(f"{rel(path)}: references a missing workflow: {target}")


def check_command(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").lstrip().splitlines()
    first = lines[0] if lines else ""
    # This shared dispatcher is read by command skills; it is deliberately
    # not advertised as a slash-command registration.
    if path.name == "codex.md":
        if not first.startswith("# "):
            errors.append(f"{rel(path)}: dispatcher reference must start with a Markdown title")
        return
    if not first.startswith("# /"):
        errors.append(f"{rel(path)}: workflow must start with a '# /<name>' title (found: {first[:50]!r})")


def main() -> int:
    errors.clear()
    skills = sorted(ROOT.glob(".agents/skills/*/SKILL.md"))
    commands = sorted((ROOT / "workflows").glob("*.md"))
    if not skills:
        errors.append("no SKILL.md files found under .agents/skills/")
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
    print(f"lint_skills: OK ({len(skills)} Codex skills, {len(commands)} workflow references)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
