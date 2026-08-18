#!/usr/bin/env bash
# Usage: bash verify/check.sh <starter|solution>
set -uo pipefail
DIR="${1:-solution}"; ROOT="$(cd "$(dirname "$0")/.." && pwd)"; T="$ROOT/$DIR"
pass=0; fail=0
ok(){ echo "  PASS: $1"; pass=$((pass+1)); }
no(){ echo "  FAIL: $1"; fail=$((fail+1)); }
echo "== Verifying $DIR =="
# 1) pytest (Task 2)
( cd "$T" && python3 -m pytest -q >/tmp/pt.log 2>&1 ); pc=$?
[ $pc -eq 0 ] && ok "pytest green (backoff is exponential)" || no "Task 2 — pytest still failing: retry backoff is not yet exponential. Details: /tmp/pt.log"
# 2) bash permission least-change (Task 4): must NOT be 'never'; must be present
perm=$(python3 - "$T/.vibe/config.toml" << 'PY'
import sys,tomllib
try:
    d=tomllib.load(open(sys.argv[1],'rb')); print(d.get("tools",{}).get("bash",{}).get("permission",""))
except Exception as e: print("ERR:"+str(e))
PY
)
[ "$perm" = "ask" ] || [ "$perm" = "allow" ] && ok "bash permission fixed ('$perm', not 'never')" || no "Task 4 — [tools.bash] permission is still '$perm'; trace the denial to this rule in .vibe/config.toml and set the least-privilege value ('ask')"
# 3) read-only reviewer sub-agent (Task 3): enabled_tools set, no write/edit/bash
python3 - "$T/.vibe/agents/reviewer.toml" << 'PY'
import sys,tomllib
try: d=tomllib.load(open(sys.argv[1],'rb'))
except Exception as e: print("TOMLERR:"+str(e)); sys.exit(3)
tools=d.get("enabled_tools")
if not tools: print("NOTOOLS"); sys.exit(2)
banned={"write_file","edit_file","bash","apply_patch","run_command"}
import sys as _s
print("HASBANNED" if (set(tools)&banned) else "OK"); _s.exit(1 if (set(tools)&banned) else 0)
PY
rc=$?
if [ $rc -eq 0 ]; then
  ok "reviewer sub-agent is read-only"
else
  case $rc in
    2) no "Task 3 — reviewer.toml has no 'enabled_tools' set: add the read/search tools the reviewer needs" ;;
    3) no "Task 3 — reviewer.toml does not parse as TOML: fix the syntax" ;;
    *) no "Task 3 — reviewer sub-agent not read-only: grant read/search only, no write_file/edit_file/bash (rc=$rc)" ;;
  esac
fi
echo "== $DIR: $pass passed, $fail failed =="
exit $fail
