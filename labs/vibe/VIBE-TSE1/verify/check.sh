#!/usr/bin/env bash
# Usage: bash verify/check.sh <starter|solution>
# Deterministic acceptance checks for the VIBE-TSE1 lab. It inspects the result
# state (does the demoed feature work, was the PR-style result produced, is the
# scoping decision correct) - not how you got there. The demo tasks can be run
# by driving the Vibe CLI or, if you have no key, by hand; the check is the same.
set -uo pipefail
DIR="${1:-solution}"; ROOT="$(cd "$(dirname "$0")/.." && pwd)"; T="$ROOT/$DIR"
pass=0; fail=0
ok(){ echo "  PASS: $1"; pass=$((pass+1)); }
no(){ echo "  FAIL: $1"; fail=$((fail+1)); }
echo "== Verifying $DIR =="

# 1) The demoed feature works: Vault.search behaves per FEATURE.md (Task 2, gate 1)
python3 - "$T" >/tmp/tse_feat.log 2>&1 << 'PY'
import sys, importlib.util, pathlib
root = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("vault", root / "app" / "vault.py")
m = importlib.util.module_from_spec(spec)
sys.modules["vault"] = m          # dataclasses needs the module registered
spec.loader.exec_module(m)
v = m.Vault()
for t in ["Buy milk", "buy bread", "Call Sam"]:
    v.add(t)
assert not hasattr(v, "search") or callable(getattr(v, "search")), "search is not callable"
assert hasattr(v, "search"), "Vault has no search() method yet"
assert {t.title for t in v.search("buy")} == {"Buy milk", "buy bread"}, "search('buy') should match both grocery tasks"
assert len(v.search("BUY")) == 2, "search must be case-insensitive"
assert v.search("   ") == [], "an empty/whitespace keyword must return no tasks"
print("OK")
PY
[ $? -eq 0 ] \
  && ok "Task 2 - Vault.search works (case-insensitive substring, empty-guard)" \
  || no "Task 2 - the search() feature is missing or wrong. Drive Vibe Code to add Vault.search per FEATURE.md, then re-check. Details: /tmp/tse_feat.log"

# 2) The feature ships with tests the agent wrote (Task 2, gate 2)
python3 - "$T" >/dev/null 2>&1 << 'PY'
import sys, pathlib, re
p = pathlib.Path(sys.argv[1]) / "tests" / "test_search.py"
if not p.exists(): sys.exit(2)
txt = p.read_text(encoding="utf-8")
sys.exit(0 if re.search(r"\.search\(", txt) else 3)
PY
rc=$?
case $rc in
  0) ok "Task 2 - tests/test_search.py exists and exercises search()" ;;
  2) no "Task 2 - tests/test_search.py is missing; a real change ships with its tests. Have Vibe Code write them." ;;
  3) no "Task 2 - tests/test_search.py exists but never calls .search(); it does not test the feature." ;;
  *) no "Task 2 - test check failed (rc=$rc)." ;;
esac

# 3) The headless PR-style result was produced and parses (Task 3, gate 3)
python3 - "$T" >/dev/null 2>&1 << 'PY'
import sys, pathlib, json
p = pathlib.Path(sys.argv[1]) / "pr.json"
if not p.exists(): sys.exit(2)
raw = p.read_text(encoding="utf-8").strip()
if not raw: sys.exit(3)
try:
    json.loads(raw)          # --output json emits one JSON document
    sys.exit(0)
except Exception:
    # tolerate newline-delimited JSON (--output streaming), still machine-parseable
    for line in raw.splitlines():
        line = line.strip()
        if line:
            json.loads(line)
    sys.exit(0)
PY
rc=$?
case $rc in
  0) ok "Task 3 - pr.json is present and parses as JSON (a CI-ready result)" ;;
  2) no "Task 3 - pr.json is missing; run the bounded headless command and redirect --output json to pr.json." ;;
  3) no "Task 3 - pr.json is empty; the headless run produced no output." ;;
  *) no "Task 3 - pr.json is not parseable JSON (rc=$rc); use --output json (or streaming)." ;;
esac

# 4) Qualification decision is correct (Task 4, gate 4)
python3 - "$T" >/tmp/tse_scope.log 2>&1 << 'PY'
import sys, pathlib, json
p = pathlib.Path(sys.argv[1]) / "scoping.json"
try:
    d = json.loads(p.read_text(encoding="utf-8"))
except Exception as e:
    print("scoping.json does not parse:", e); sys.exit(2)
errs = []
cands = d.get("candidates", {})
want = {
  "carrier_adapter_delivery": {
    "marks": {"strategically_valuable": True, "highly_urgent": True,
              "production_bound": True, "feasible_within_six_months": True},
    "verdict": "ready"},
  "internal_doc_generator": {
    "marks": {"strategically_valuable": False, "highly_urgent": False,
              "production_bound": False, "feasible_within_six_months": True},
    "verdict": "needs_scoping"},
}
for name, exp in want.items():
    c = cands.get(name, {})
    for mk, mv in exp["marks"].items():
        got = c.get("marks", {}).get(mk)
        if got is not mv:
            errs.append(f"{name}.marks.{mk} should be {mv}, got {got!r}")
    if c.get("verdict") != exp["verdict"]:
        errs.append(f"{name}.verdict should be '{exp['verdict']}', got {c.get('verdict')!r}")
    # consistency: ready iff all four marks true
    all_true = all(c.get("marks", {}).get(k) is True for k in exp["marks"])
    if (c.get("verdict") == "ready") != all_true:
        errs.append(f"{name}: verdict must be 'ready' only when all four marks are true")
if d.get("primary_surface") != "cli":
    errs.append("primary_surface should be 'cli' (they want adapter tests generated and run in CI)")
if d.get("engagement_type") != "core_process_automation":
    errs.append("engagement_type should be 'core_process_automation' (one team automating a core workflow)")
if d.get("recommended_next_step") != "iconic_use_case_workshop":
    errs.append("recommended_next_step should be 'iconic_use_case_workshop' (the Discover-phase next step)")
if errs:
    print("\n".join(errs)); sys.exit(1)
print("OK")
PY
[ $? -eq 0 ] \
  && ok "Task 4 - qualification is correct (marks, verdicts, surface, engagement, next step)" \
  || no "Task 4 - qualification decision is wrong; see the specifics in /tmp/tse_scope.log"

# 5) Objection handling is correct (Task 5, gate 5)
python3 - "$T" >/tmp/tse_obj.log 2>&1 << 'PY'
import sys, pathlib, json
d = json.loads((pathlib.Path(sys.argv[1]) / "scoping.json").read_text(encoding="utf-8"))
o = d.get("objection", {})
errs = []
if o.get("primary_pillar") != "enterprise_ready":
    errs.append("objection.primary_pillar should be 'enterprise_ready' (on-prem -> code, data, weights, keys stay with them)")
if o.get("offer_security_review") is not True:
    errs.append("objection.offer_security_review should be true (answer on-prem precisely, then offer a security review)")
if o.get("bridge_to_solutions_engineer") is not True:
    errs.append("objection.bridge_to_solutions_engineer should be true (the architect's deep config question is an SE bridge, not a bluff)")
if errs:
    print("\n".join(errs)); sys.exit(1)
print("OK")
PY
[ $? -eq 0 ] \
  && ok "Task 5 - objection handled (enterprise-ready pillar, security review, SE bridge)" \
  || no "Task 5 - objection handling is wrong; see the specifics in /tmp/tse_obj.log"

echo "== $DIR: $pass passed, $fail failed =="
exit $fail
