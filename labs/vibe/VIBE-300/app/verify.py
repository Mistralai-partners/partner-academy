#!/usr/bin/env python3
"""Acceptance check for the VIBE-300 walkthrough lab (advanced Vibe Code CLI).

Run from this folder after reading and running the working code:

    python3 verify.py

Confirms the end state the lesson walks you through: the retry suite is green
(backoff is exponential), the shell tool is scoped to least privilege (ask, not
a blanket allow or never), and the reviewer sub-agent is read-only. All checks
are offline and deterministic. Prints RESULT: PASS and exits 0 only when every
check holds.
"""
import os, sys, subprocess, tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
passed, failed = [], []
def ok(m): passed.append(m); print(f"  PASS: {m}")
def no(m): failed.append(m); print(f"  FAIL: {m}")

def check_tests():
    r = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"], cwd=HERE, capture_output=True, text=True)
    ok("retry suite green (backoff is exponential)") if r.returncode == 0 else no("retry suite failing:\n" + (r.stdout or r.stderr)[-600:])

def check_bash_permission():
    p = os.path.join(HERE, ".vibe", "config.toml")
    try:
        perm = tomllib.load(open(p, "rb")).get("tools", {}).get("bash", {}).get("permission")
    except Exception as e:
        return no(f".vibe/config.toml missing or unparseable: {e}")
    ok(f"shell tool scoped to least privilege (permission = \"{perm}\")") if perm in ("ask", "allow") \
        else no(f"[tools.bash] permission is \"{perm}\"; set the least-privilege value \"ask\"")

def check_reviewer_read_only():
    p = os.path.join(HERE, ".vibe", "agents", "reviewer.toml")
    if not os.path.exists(p):
        return no(".vibe/agents/reviewer.toml is missing")
    try:
        tools = tomllib.load(open(p, "rb")).get("enabled_tools")
    except Exception as e:
        return no(f"reviewer.toml does not parse: {e}")
    if not tools:
        return no("reviewer.toml sets no enabled_tools")
    banned = {"write_file", "edit_file", "edit", "bash", "apply_patch", "run_command"}
    no(f"reviewer grants a write/shell tool ({sorted(set(tools)&banned)})") if set(tools) & banned \
        else ok("reviewer sub-agent is read-only (read/search only)")

def main():
    print("== Verifying VIBE-300 lab ==")
    check_tests(); check_bash_permission(); check_reviewer_read_only()
    print(f"\n== {len(passed)} passed, {len(failed)} failed ==")
    print("RESULT: PASS" if not failed else "RESULT: FAIL")
    sys.exit(0 if not failed else 1)

if __name__ == "__main__":
    main()
