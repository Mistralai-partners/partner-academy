#!/usr/bin/env bash
# Usage: bash verify/check.sh <starter|solution>
#
# Deterministic acceptance checks for VIBE-400. NO network and NO API key
# required: the hook checks execute the REAL hook scripts against real
# wire-protocol payloads, and the CI-gate check runs the REAL gate against
# captured transcripts. Structural checks parse the TOML you authored and
# assert the posture the task grades.
#
# A live end-to-end run (a real `vibe -p` firing the hooks) is available as an
# optional extra when VIBE_LIVE=1 and MISTRAL_API_KEY are set - see the tail of
# this script. It is NOT required to pass.
set -uo pipefail
DIR="${1:-solution}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
T="$ROOT/$DIR"
PY="$(command -v python3)"
pass=0; fail=0
ok(){ echo "  PASS: $1"; pass=$((pass+1)); }
no(){ echo "  FAIL: $1"; fail=$((fail+1)); }
echo "== Verifying $DIR =="

# ---------------------------------------------------------------------------
# Task 1a - hooks.toml shape (structural; mirrors vibe.core.hooks HookConfig)
# ---------------------------------------------------------------------------
"$PY" - "$T/.vibe/hooks.toml" >/dev/null 2>&1 <<'PY'
import sys, tomllib
try:
    data = tomllib.load(open(sys.argv[1], "rb"))
except Exception as e:
    print("TOMLERR:" + str(e)); sys.exit(3)
hooks = data.get("hooks", [])
by = {}
for h in hooks:
    t = h.get("type")
    by.setdefault(t, []).append(h)
    # schema constraint: match/strict are tool-hook only
    if t == "post_agent" and ("match" in h or "strict" in h):
        print("BADPOSTAGENT"); sys.exit(4)
    if not h.get("name") or not h.get("command"):
        print("MISSINGFIELD"); sys.exit(5)
pre = by.get("pre_tool", [])
strict_scoped = [h for h in pre if h.get("strict") is True and h.get("match")]
if not strict_scoped: print("NOSTRICTGUARD"); sys.exit(6)
if not by.get("post_tool"): print("NOPOSTTOOL"); sys.exit(7)
if not by.get("post_agent"): print("NOPOSTAGENT"); sys.exit(8)
print("OK")
PY
case $? in
  0) ok "hooks.toml declares a strict+scoped pre_tool guard, a post_tool audit, and a post_agent gate" ;;
  3) no "Task 1 - hooks.toml does not parse as TOML: fix the syntax" ;;
  4) no "Task 1 - a post_agent hook sets 'match' or 'strict'; both are valid on tool hooks only (pre_tool/post_tool). The loader rejects this at startup" ;;
  5) no "Task 1 - a hook is missing 'name' or 'command' (both required)" ;;
  6) no "Task 1 - no fail-closed guard: need a pre_tool hook with strict=true AND a match scope. Without strict, a hook crash becomes a soft warning and the tool still runs" ;;
  7) no "Task 1 - no post_tool hook: nothing records the tool calls that executed" ;;
  8) no "Task 1 - no post_agent hook: nothing records turn boundaries" ;;
  *) no "Task 1 - hooks.toml shape check failed" ;;
esac

# ---------------------------------------------------------------------------
# Task 1b - the pre_tool guard actually DENIES a destructive command (RAN)
# ---------------------------------------------------------------------------
GUARD_DENY=$(printf '%s' '{"session_id":"s","transcript_path":"/t","cwd":".","hook_event_name":"pre_tool","tool_name":"bash","tool_call_id":"c","tool_input":{"command":"rm -rf /"}}' | ( cd "$T" && "$PY" .vibe/hooks/guard.py 2>/dev/null ))
GUARD_ALLOW=$(printf '%s' '{"session_id":"s","transcript_path":"/t","cwd":".","hook_event_name":"pre_tool","tool_name":"bash","tool_call_id":"c","tool_input":{"command":"ls -la"}}' | ( cd "$T" && "$PY" .vibe/hooks/guard.py 2>/dev/null ))
if echo "$GUARD_DENY" | grep -q '"decision"[[:space:]]*:[[:space:]]*"deny"' && [ -z "$GUARD_ALLOW" ]; then
  ok "pre_tool guard denies 'rm -rf' (emits decision:deny) and passes through safe commands (empty stdout)"
else
  no "Task 1 - guard.py did not deny a destructive command. Feed it a pre_tool payload whose tool_input.command is 'rm -rf /' and it must print {\"decision\":\"deny\",...} on stdout; safe commands must print nothing"
fi

# ---------------------------------------------------------------------------
# Task 1c - the post_tool audit hook FIRES and writes a marker (RAN)
# ---------------------------------------------------------------------------
( cd "$T" && rm -f audit.log && printf '%s' '{"session_id":"abcd1234","transcript_path":"/t","cwd":".","hook_event_name":"post_tool","tool_name":"read_file","tool_call_id":"c","tool_input":{},"tool_status":"success","tool_output":null,"tool_output_text":"x","tool_error":null,"duration_ms":9.0}' | "$PY" .vibe/hooks/audit.py >/dev/null 2>&1 )
if [ -s "$T/audit.log" ] && grep -q "read_file" "$T/audit.log" 2>/dev/null; then
  ok "post_tool audit hook fired: audit.log records the executed tool call"
else
  no "Task 1 - audit.py did not write a marker. On a post_tool payload it must append a line naming the tool (e.g. 'read_file status=success ...') to audit.log in the project root"
fi

# ---------------------------------------------------------------------------
# Task 1d - the post_agent gate hook records a turn boundary (RAN)
# ---------------------------------------------------------------------------
( cd "$T" && printf '%s' '{"session_id":"deadbeef99","transcript_path":"/t","cwd":".","hook_event_name":"post_agent"}' | "$PY" .vibe/hooks/gate.py >/dev/null 2>&1 )
if grep -q "turn end" "$T/audit.log" 2>/dev/null; then
  ok "post_agent gate hook fired: a turn boundary was recorded in audit.log"
else
  no "Task 1 - gate.py did not record a turn boundary. On a post_agent payload it must append a 'turn end' line to audit.log"
fi
( cd "$T" && rm -f audit.log )

# ---------------------------------------------------------------------------
# Task 2 - custom agent profile ci-reviewer.toml is least-privilege (structural)
# ---------------------------------------------------------------------------
"$PY" - "$T/.vibe/agents/ci-reviewer.toml" >/dev/null 2>&1 <<'PY'
import sys, tomllib
BANNED={"write_file","edit_file","search_replace","bash","apply_patch","run_command"}
try: d=tomllib.load(open(sys.argv[1],"rb"))
except Exception as e: print("TOMLERR:"+str(e)); sys.exit(3)
if d.get("agent_type") != "agent": print("NOTAGENT"); sys.exit(4)
tools=d.get("enabled_tools")
if not tools: print("NOTOOLS"); sys.exit(5)
if set(tools) & BANNED: print("HASBANNED:"+",".join(sorted(set(tools)&BANNED))); sys.exit(6)
print("OK")
PY
case $? in
  0) ok "ci-reviewer.toml is a user-facing agent scoped to read/search only (least privilege for an untrusted PR)" ;;
  3) no "Task 2 - ci-reviewer.toml does not parse as TOML" ;;
  4) no "Task 2 - ci-reviewer.toml must set agent_type = \"agent\" (user-facing, selectable via --agent)" ;;
  5) no "Task 2 - ci-reviewer.toml has no enabled_tools; scope it explicitly" ;;
  6) no "Task 2 - ci-reviewer can still mutate the tree or run the shell. A reviewer of an untrusted PR should enable read/search tools only (e.g. read_file, grep)" ;;
  *) no "Task 2 - ci-reviewer.toml check failed" ;;
esac

# ---------------------------------------------------------------------------
# Task 3 - researcher.toml is a read-only delegation subagent (structural)
# ---------------------------------------------------------------------------
"$PY" - "$T/.vibe/agents/researcher.toml" >/dev/null 2>&1 <<'PY'
import sys, tomllib
BANNED={"write_file","edit_file","search_replace","bash","apply_patch","run_command"}
try: d=tomllib.load(open(sys.argv[1],"rb"))
except Exception as e: print("TOMLERR:"+str(e)); sys.exit(3)
if d.get("agent_type") != "subagent": print("NOTSUB"); sys.exit(4)
tools=d.get("enabled_tools")
if not tools: print("NOTOOLS"); sys.exit(5)
if set(tools) & BANNED: print("HASBANNED"); sys.exit(6)
print("OK")
PY
case $? in
  0) ok "researcher.toml is a delegation-only subagent (task-spawned) with read/search only" ;;
  3) no "Task 3 - researcher.toml does not parse as TOML" ;;
  4) no "Task 3 - researcher.toml must set agent_type = \"subagent\" so it is delegation-only (spawned via the task tool), not user-selectable" ;;
  5) no "Task 3 - researcher.toml has no enabled_tools" ;;
  6) no "Task 3 - the subagent can write/run shell; a delegated worker should be read-only" ;;
  *) no "Task 3 - researcher.toml check failed" ;;
esac

# ---------------------------------------------------------------------------
# Task 4 - permission posture in config.toml (structural)
# ---------------------------------------------------------------------------
"$PY" - "$T/.vibe/config.toml" >/dev/null 2>&1 <<'PY'
import sys, tomllib
try: d=tomllib.load(open(sys.argv[1],"rb"))
except Exception as e: print("TOMLERR:"+str(e)); sys.exit(3)
bash=d.get("tools",{}).get("bash",{})
perm=bash.get("permission")
if perm == "always": print("BLANKET"); sys.exit(4)
if perm not in ("ask","never"): print("NOPERM:"+str(perm)); sys.exit(5)
deny=bash.get("deny") or []
import re
pat=re.compile(r"rm\s+-rf|git\s+push|reset\s+--hard", re.I)
if not any(pat.search(str(x)) for x in deny): print("NODENY"); sys.exit(6)
print("OK")
PY
case $? in
  0) ok "config.toml gates bash (not blanket-allowed) and denylists destructive commands - a denylist match wins even under auto-approve" ;;
  3) no "Task 4 - config.toml does not parse as TOML" ;;
  4) no "Task 4 - [tools.bash].permission is still 'always' (blanket allow). Set it to 'ask' so the shell is gated" ;;
  5) no "Task 4 - [tools.bash].permission must be 'ask' or 'never'" ;;
  6) no "Task 4 - no destructive-command denylist. Add deny = [\"rm -rf *\", \"git push\", ...] so a sensitive pattern is blocked even under an always/auto-approve posture" ;;
  *) no "Task 4 - config.toml posture check failed" ;;
esac

# ---------------------------------------------------------------------------
# Task 5 - headless CI gate turns a transcript into an exit code (RAN)
# ---------------------------------------------------------------------------
bash "$T/ci/review-gate.sh" "$T/ci/samples/approved.json" >/dev/null 2>&1; a=$?
bash "$T/ci/review-gate.sh" "$T/ci/samples/rejected.json" >/dev/null 2>&1; r=$?
echo "not json" | bash "$T/ci/review-gate.sh" >/dev/null 2>&1; m=$?
if [ "$a" -eq 0 ] && [ "$r" -eq 1 ] && [ "$m" -eq 3 ]; then
  ok "CI gate: APPROVE->0, REQUEST_CHANGES->1, broken transcript->3 (a gate that can actually fail)"
else
  no "Task 5 - the gate must map verdicts to exit codes: approved.json must exit 0 (got $a), rejected.json must exit 1 (got $r), and a malformed transcript must exit 3 (got $m). A gate that exits 0 for everything cannot block a bad change"
fi

echo "== $DIR: $pass passed, $fail failed =="
# Optional: real end-to-end hook fire. Requires VIBE_LIVE=1 + MISTRAL_API_KEY.
if [ "${VIBE_LIVE:-0}" = "1" ] && [ -n "${MISTRAL_API_KEY:-}" ] && [ "$DIR" = "solution" ]; then
  echo "-- VIBE_LIVE: running a real bounded vibe -p to fire the hooks --"
  ( cd "$T" && rm -f audit.log && \
    vibe -p "Run the bash command: cat app_sample.py" --max-turns 2 --output json --auto-approve --trust >/tmp/vibe_live.json 2>/dev/null )
  if grep -q "status=" "$T/audit.log" 2>/dev/null; then
    echo "  LIVE PASS: hooks fired in a real run - audit.log:"; sed 's/^/    /' "$T/audit.log"
  else
    echo "  LIVE NOTE: no audit line captured (model may not have called a tool this run)"
  fi
  ( cd "$T" && rm -f audit.log )
fi
exit $fail
