#!/usr/bin/env python3
"""Acceptance check for the VIBE-400 walkthrough lab (Extend and Operate).

Run from this folder after reading the working code:

    python3 verify.py

Confirms the end state the lesson walks you through: hooks.toml declares the
right hook types, the guard denies destructive commands, the audit hook records
tool calls, agent profiles are least-privilege, the permission posture gates
bash, and the CI gate maps verdicts to exit codes. All checks run offline and
deterministically. Prints RESULT: PASS and exits 0 only when every check holds.
"""
import json
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


def check_hooks_toml():
    path = os.path.join(HERE, ".vibe", "hooks.toml")
    if not os.path.exists(path):
        return no("hooks.toml is missing")
    try:
        data = tomllib.load(open(path, "rb"))
    except Exception as e:
        return no(f"hooks.toml does not parse: {e}")
    hooks = data.get("hooks", [])
    by_type = {}
    for h in hooks:
        by_type.setdefault(h.get("type"), []).append(h)
    strict_scoped = [h for h in by_type.get("pre_tool", [])
                     if h.get("strict") is True and h.get("match")]
    if not strict_scoped:
        return no("no fail-closed pre_tool guard (need strict=true + match)")
    if not by_type.get("post_tool"):
        return no("no post_tool hook (nothing records tool calls)")
    if not by_type.get("post_agent"):
        return no("no post_agent hook (nothing records turn boundaries)")
    ok("hooks.toml: strict+scoped guard, post_tool audit, post_agent gate")


def check_guard_denies():
    guard = os.path.join(HERE, ".vibe", "hooks", "guard.py")
    if not os.path.exists(guard):
        return no("guard.py is missing")
    payload = json.dumps({
        "session_id": "s", "transcript_path": "/t", "cwd": ".",
        "hook_event_name": "pre_tool", "tool_name": "bash",
        "tool_call_id": "c", "tool_input": {"command": "rm -rf /"},
    })
    r = subprocess.run(
        [sys.executable, guard],
        input=payload, capture_output=True, text=True, cwd=HERE,
    )
    if '"deny"' not in r.stdout:
        return no("guard.py did not deny 'rm -rf /'")
    safe = json.dumps({
        "session_id": "s", "transcript_path": "/t", "cwd": ".",
        "hook_event_name": "pre_tool", "tool_name": "bash",
        "tool_call_id": "c", "tool_input": {"command": "ls -la"},
    })
    r2 = subprocess.run(
        [sys.executable, guard],
        input=safe, capture_output=True, text=True, cwd=HERE,
    )
    if r2.stdout.strip():
        return no("guard.py should print nothing for safe commands")
    ok("guard denies destructive commands, passes safe ones")


def check_audit_hook():
    audit = os.path.join(HERE, ".vibe", "hooks", "audit.py")
    if not os.path.exists(audit):
        return no("audit.py is missing")
    log_path = os.path.join(HERE, "audit.log")
    try:
        os.remove(log_path)
    except FileNotFoundError:
        pass
    payload = json.dumps({
        "session_id": "test", "transcript_path": "/t", "cwd": ".",
        "hook_event_name": "post_tool", "tool_name": "read_file",
        "tool_call_id": "c", "tool_input": {}, "tool_status": "success",
        "tool_output": None, "tool_output_text": "x", "tool_error": None,
        "duration_ms": 9.0,
    })
    subprocess.run(
        [sys.executable, audit], input=payload,
        capture_output=True, text=True, cwd=HERE,
    )
    if os.path.exists(log_path) and "read_file" in open(log_path).read():
        ok("audit hook records tool calls to audit.log")
    else:
        no("audit.py did not write a tool record to audit.log")
    try:
        os.remove(log_path)
    except FileNotFoundError:
        pass


def check_ci_reviewer():
    path = os.path.join(HERE, ".vibe", "agents", "ci-reviewer.toml")
    if not os.path.exists(path):
        return no("ci-reviewer.toml is missing")
    try:
        d = tomllib.load(open(path, "rb"))
    except Exception as e:
        return no(f"ci-reviewer.toml does not parse: {e}")
    banned = {"write_file", "edit_file", "search_replace", "bash",
              "apply_patch", "run_command"}
    tools = d.get("enabled_tools", [])
    if set(tools) & banned:
        return no("ci-reviewer can still mutate (has write/shell tools)")
    ok("ci-reviewer is least-privilege (read/search only)")


def check_config_posture():
    path = os.path.join(HERE, ".vibe", "config.toml")
    if not os.path.exists(path):
        return no("config.toml is missing")
    try:
        d = tomllib.load(open(path, "rb"))
    except Exception as e:
        return no(f"config.toml does not parse: {e}")
    perm = d.get("tools", {}).get("bash", {}).get("permission")
    if perm == "always":
        return no("bash permission is blanket-allowed")
    deny = d.get("tools", {}).get("bash", {}).get("deny", [])
    pat = re.compile(r"rm\s+-rf|git\s+push|reset\s+--hard", re.I)
    if not any(pat.search(str(x)) for x in deny):
        return no("no destructive-command denylist on bash")
    ok("config gates bash + denylists destructive commands")


def check_ci_gate():
    gate = os.path.join(HERE, "ci", "review-gate.sh")
    if not os.path.exists(gate):
        return no("ci/review-gate.sh is missing")
    approved = os.path.join(HERE, "ci", "samples", "approved.json")
    rejected = os.path.join(HERE, "ci", "samples", "rejected.json")
    a = subprocess.run(["bash", gate, approved], capture_output=True, cwd=HERE)
    r = subprocess.run(["bash", gate, rejected], capture_output=True, cwd=HERE)
    if a.returncode == 0 and r.returncode == 1:
        ok("CI gate: APPROVE->0, REQUEST_CHANGES->1")
    else:
        no(f"CI gate exit codes wrong: approved={a.returncode}, rejected={r.returncode}")


def main():
    print("== Verifying VIBE-400 lab ==")
    check_hooks_toml()
    check_guard_denies()
    check_audit_hook()
    check_ci_reviewer()
    check_config_posture()
    check_ci_gate()
    print(f"\n== {len(passed)} passed, {len(failed)} failed ==")
    print("RESULT: PASS" if not failed else "RESULT: FAIL")
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
