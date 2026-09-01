#!/usr/bin/env python3
"""Verify the .vibe/ quickstart is well-formed.

Offline, stdlib-only (tomllib is in the stdlib on 3.11+). It checks the same
things Vibe checks when it loads the project, so a green run here means the CLI
will discover all the pieces:

  - 2 custom agents in .vibe/agents/*.toml, each type "agent", each pointing at
    a prompt file that exists (system_prompt_id -> .vibe/prompts/<id>.md)
  - 2 skills in .vibe/skills/<name>/SKILL.md with valid name + description
  - 2 instruction files: ./AGENTS.md and ./src/AGENTS.md
  - .vibe/config.toml with default_agent set to one of the discovered agents

Run:  uv run python verify.py   (or: python3 verify.py)
"""
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VIBE = ROOT / ".vibe"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

failures: list[str] = []
notes: list[str] = []


def check(cond: bool, ok: str, bad: str) -> None:
    (notes.append(f"[PASS] {ok}") if cond else failures.append(f"[FAIL] {bad}"))


def parse_frontmatter(text: str) -> dict[str, str]:
    """Tiny YAML-frontmatter reader for the two scalar fields we assert."""
    m = re.match(r"^-{3,}\s*\n(.*?)\n-{3,}\s*\n", text, re.DOTALL)
    if not m:
        return {}
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t", "-")):
            k, _, v = line.partition(":")
            fields[k.strip()] = v.strip().strip("'\"")
    return fields


# --- agents ---------------------------------------------------------------
agent_files = sorted((VIBE / "agents").glob("*.toml")) if (VIBE / "agents").is_dir() else []
check(len(agent_files) == 2, f"found 2 agents: {[p.stem for p in agent_files]}",
      f"expected 2 agent TOMLs in .vibe/agents/, found {len(agent_files)}")
for p in agent_files:
    try:
        data = tomllib.loads(p.read_text())
    except tomllib.TOMLDecodeError as exc:
        failures.append(f"[FAIL] {p.name} is not valid TOML: {exc}")
        continue
    check(data.get("agent_type", "agent") == "agent",
          f"{p.stem}: agent_type=agent (selectable)",
          f"{p.stem}: agent_type must be 'agent' to be --agent-selectable")
    spid = data.get("system_prompt_id")
    if spid:
        prompt = VIBE / "prompts" / f"{spid}.md"
        check(prompt.is_file(),
              f"{p.stem}: system_prompt_id '{spid}' -> {prompt.relative_to(ROOT)} exists",
              f"{p.stem}: system_prompt_id '{spid}' but {prompt.relative_to(ROOT)} is missing")

# --- skills ---------------------------------------------------------------
skill_files = sorted((VIBE / "skills").glob("*/SKILL.md")) if (VIBE / "skills").is_dir() else []
check(len(skill_files) == 2, f"found 2 skills: {[p.parent.name for p in skill_files]}",
      f"expected 2 skills at .vibe/skills/<name>/SKILL.md, found {len(skill_files)}")
for p in skill_files:
    fm = parse_frontmatter(p.read_text())
    check(bool(fm.get("name")) and bool(NAME_RE.match(fm.get("name", ""))),
          f"{p.parent.name}: valid skill name '{fm.get('name')}'",
          f"{p.parent.name}: SKILL.md needs a lowercase-hyphen 'name' (got {fm.get('name')!r})")
    check(bool(fm.get("description")),
          f"{p.parent.name}: has a description",
          f"{p.parent.name}: SKILL.md needs a 'description'")

# --- instruction files ----------------------------------------------------
for rel in ("AGENTS.md", "src/AGENTS.md"):
    check((ROOT / rel).is_file(), f"instruction file {rel} present",
          f"missing instruction file {rel}")

# --- config wiring --------------------------------------------------------
cfg = VIBE / "config.toml"
if cfg.is_file():
    cfg_data = tomllib.loads(cfg.read_text())
    default_agent = cfg_data.get("default_agent")
    agent_names = {p.stem for p in agent_files}
    check(default_agent in agent_names,
          f".vibe/config.toml default_agent='{default_agent}' matches a discovered agent",
          f".vibe/config.toml default_agent='{default_agent}' is not one of {sorted(agent_names)}")
else:
    failures.append("[FAIL] .vibe/config.toml is missing")

# --- report ---------------------------------------------------------------
for line in notes:
    print(line)
if failures:
    print()
    for line in failures:
        print(line)
    print(f"\n{len(failures)} check(s) failed.")
    sys.exit(1)
print(f"\nAll checks passed. The .vibe/ quickstart is well-formed "
      f"({len(agent_files)} agents, {len(skill_files)} skills, 2 instruction files).")
