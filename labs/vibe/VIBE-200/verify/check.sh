#!/usr/bin/env bash
# Usage: bash verify/check.sh <starter|solution>
# Deterministic acceptance checks for the VIBE-200 lab. Runs the same whether
# you fixed things by hand or by driving the Vibe CLI - it inspects the result
# state (tests, agent scope, project config), not how you got there.
set -uo pipefail
DIR="${1:-solution}"; ROOT="$(cd "$(dirname "$0")/.." && pwd)"; T="$ROOT/$DIR"
pass=0; fail=0
ok(){ echo "  PASS: $1"; pass=$((pass+1)); }
no(){ echo "  FAIL: $1"; fail=$((fail+1)); }
echo "== Verifying $DIR =="

# 1) slugify test green (Task 2) -----------------------------------------------
( cd "$T" && python3 -m pytest tests/test_slugify.py -q >/tmp/vibe200_slug.log 2>&1 ); pc=$?
[ $pc -eq 0 ] \
  && ok "Task 2 - slugify suite green (separators collapse, no edge hyphens)" \
  || no "Task 2 - slugify still failing: an input is producing doubled or edge hyphens. Hand app/slugify.py to Vibe and confirm by re-running the suite. Details: /tmp/vibe200_slug.log"

# 2) truncate test green (Task 3) ----------------------------------------------
( cd "$T" && python3 -m pytest tests/test_truncate.py -q >/tmp/vibe200_trunc.log 2>&1 ); tc=$?
[ $tc -eq 0 ] \
  && ok "Task 3 - truncate suite green (app/truncate.py exists and fits the tests)" \
  || no "Task 3 - truncate suite failing: tests/test_truncate.py expects app/truncate.py::truncate_words, which is missing or wrong. Generate it against @app/casing.py. Details: /tmp/vibe200_trunc.log"

# 3) reviewer sub-agent is read-only (Task 4) ----------------------------------
python3 - "$T/.vibe/agents/reviewer.toml" >/dev/null 2>&1 << 'PY'
import sys, tomllib
try:
    d = tomllib.load(open(sys.argv[1], "rb"))
except FileNotFoundError:
    print("NOFILE"); sys.exit(4)
except Exception:
    print("TOMLERR"); sys.exit(3)
tools = d.get("enabled_tools")
if not tools:
    print("NOTOOLS"); sys.exit(2)
banned = {"write_file", "search_replace", "edit_file", "bash", "apply_patch"}
sys.exit(1 if (set(tools) & banned) else 0)
PY
rc=$?
case $rc in
  0) ok "Task 4 - reviewer agent is read-only (read/search only, no write or shell)" ;;
  1) no "Task 4 - reviewer.toml still grants a write or shell tool; a reviewer should read and search only. Scope enabled_tools down and re-check." ;;
  2) no "Task 4 - reviewer.toml has no enabled_tools set; grant only the tools a reviewer needs." ;;
  3) no "Task 4 - reviewer.toml does not parse as TOML; fix the syntax." ;;
  4) no "Task 4 - .vibe/agents/reviewer.toml is missing." ;;
  *) no "Task 4 - reviewer agent not read-only (rc=$rc)." ;;
esac

# 4) project defaults: config.toml + AGENTS.md (Task 5) ------------------------
python3 - "$T/.vibe/config.toml" "$T/AGENTS.md" >/dev/null 2>&1 << 'PY'
import sys, tomllib, re, os
cfg_path, agents_path = sys.argv[1], sys.argv[2]
# config.toml: default_agent set to a real agent, bash permission = "ask"
try:
    cfg = tomllib.load(open(cfg_path, "rb"))
except Exception:
    print("CFGERR"); sys.exit(2)
da = cfg.get("default_agent")
if da not in {"default", "plan", "accept-edits", "auto-approve"}:
    print("NODEFAULT"); sys.exit(3)
if cfg.get("tools", {}).get("bash", {}).get("permission") != "ask":
    print("NOBASHPERM"); sys.exit(4)
# AGENTS.md: exists at repo root, non-trivial, states real conventions
if not os.path.exists(agents_path):
    print("NOAGENTS"); sys.exit(5)
text = open(agents_path, encoding="utf-8").read()
if len([l for l in text.splitlines() if l.strip()]) < 5:
    print("THINAGENTS"); sys.exit(6)
if not re.search(r"pytest|docstring|type hint|scope", text, re.I):
    print("VAGUEAGENTS"); sys.exit(7)
sys.exit(0)
PY
rc=$?
case $rc in
  0) ok "Task 5 - project defaults set (default_agent + safe bash permission + AGENTS.md conventions)" ;;
  2) no "Task 5 - .vibe/config.toml is missing or does not parse." ;;
  3) no "Task 5 - .vibe/config.toml has no valid default_agent; a fresh session should open read-only. Set default_agent." ;;
  4) no "Task 5 - the bash tool is not held to permission = \"ask\" in .vibe/config.toml; set the safe-by-default posture." ;;
  5) no "Task 5 - AGENTS.md is missing at the repo root; the team conventions have nowhere to live." ;;
  6) no "Task 5 - AGENTS.md is too thin to guide a run; write the real conventions." ;;
  7) no "Task 5 - AGENTS.md does not state testing or scoping conventions; make it concrete." ;;
  *) no "Task 5 - project defaults incomplete (rc=$rc)." ;;
esac

echo "== $DIR: $pass passed, $fail failed =="
exit $fail
