#!/usr/bin/env python3
"""Acceptance check for the VIBE-200 walkthrough lab (textkit).

Run it from this folder after you have read the working code and run it:

    python3 verify.py

It confirms the end state the lesson walks you through, not how you got there:
the test suite is green, the reviewer agent is read-only, and the project
defaults (config.toml + AGENTS.md) are in place. All checks are offline and
deterministic, so a green result never depends on a live model call.
Prints RESULT: PASS and exits 0 only when every check holds.
"""
import os
import re
import subprocess
import sys
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
passed, failed = [], []


def ok(msg):
    passed.append(msg)
    print(f"  PASS: {msg}")


def no(msg):
    failed.append(msg)
    print(f"  FAIL: {msg}")


def check_tests():
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q"],
        cwd=HERE, capture_output=True, text=True,
    )
    if r.returncode == 0:
        ok("test suite green (slugify + truncate)")
    else:
        no("test suite failing:\n" + (r.stdout or r.stderr)[-800:])


def check_reviewer_read_only():
    path = os.path.join(HERE, ".vibe", "agents", "reviewer.toml")
    if not os.path.exists(path):
        return no(".vibe/agents/reviewer.toml is missing")
    try:
        d = tomllib.load(open(path, "rb"))
    except Exception as e:
        return no(f"reviewer.toml does not parse: {e}")
    tools = d.get("enabled_tools")
    if not tools:
        return no("reviewer.toml sets no enabled_tools")
    banned = {"write_file", "search_replace", "edit_file", "edit", "bash", "apply_patch"}
    if set(tools) & banned:
        return no(f"reviewer grants a write/shell tool ({sorted(set(tools) & banned)}); a reviewer reads and searches only")
    ok("reviewer agent is read-only (no write or shell tool)")


def check_project_defaults():
    cfg_path = os.path.join(HERE, ".vibe", "config.toml")
    agents_path = os.path.join(HERE, "AGENTS.md")
    try:
        cfg = tomllib.load(open(cfg_path, "rb"))
    except Exception:
        return no(".vibe/config.toml is missing or does not parse")
    if cfg.get("default_agent") not in {"default", "plan", "accept-edits", "auto-approve"}:
        return no(".vibe/config.toml has no valid default_agent (a fresh session should open read-only)")
    if cfg.get("tools", {}).get("bash", {}).get("permission") != "ask":
        return no('the bash tool is not held to permission = "ask" in .vibe/config.toml')
    if not os.path.exists(agents_path):
        return no("AGENTS.md is missing at the project root")
    text = open(agents_path, encoding="utf-8").read()
    if len([l for l in text.splitlines() if l.strip()]) < 5:
        return no("AGENTS.md is too thin to guide a run")
    if not re.search(r"pytest|docstring|type hint|scope", text, re.I):
        return no("AGENTS.md does not state testing or scoping conventions")
    ok("project defaults set (default_agent + safe bash permission + AGENTS.md conventions)")


def main():
    print("== Verifying textkit (VIBE-200) ==")
    check_tests()
    check_reviewer_read_only()
    check_project_defaults()
    print(f"\n== {len(passed)} passed, {len(failed)} failed ==")
    print("RESULT: PASS" if not failed else "RESULT: FAIL")
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
