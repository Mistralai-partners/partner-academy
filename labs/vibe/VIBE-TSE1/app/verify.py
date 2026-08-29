#!/usr/bin/env python3
"""Acceptance check for the VIBE-TSE1 walkthrough lab.

Run from this folder after reading the working code:

    python3 verify.py

Confirms: Vault.search works correctly (case-insensitive, empty-guard), the
search test file exists and exercises search(), the headless PR result (pr.json)
is valid JSON, the qualification decision in scoping.json is correct, and the
objection handling is correct. All checks are offline and deterministic.
Prints RESULT: PASS and exits 0 only when every check holds.
"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
passed, failed = [], []


def ok(msg):
    passed.append(msg)
    print(f"  PASS: {msg}")


def no(msg):
    failed.append(msg)
    print(f"  FAIL: {msg}")


def check_vault_search():
    spec = importlib.util.spec_from_file_location(
        "vault", os.path.join(HERE, "app", "vault.py"))
    if spec is None:
        return no("app/vault.py is missing")
    m = importlib.util.module_from_spec(spec)
    sys.modules["vault"] = m
    try:
        spec.loader.exec_module(m)
    except Exception as e:
        return no(f"app/vault.py fails to import: {e}")
    v = m.Vault()
    for t in ["Buy milk", "buy bread", "Call Sam"]:
        v.add(t)
    if not hasattr(v, "search"):
        return no("Vault has no search() method")
    if {t.title for t in v.search("buy")} != {"Buy milk", "buy bread"}:
        return no("search('buy') should match both grocery tasks")
    if len(v.search("BUY")) != 2:
        return no("search must be case-insensitive")
    if v.search("   ") != []:
        return no("empty/whitespace keyword must return no tasks")
    ok("Vault.search works (case-insensitive, empty-guard)")


def check_search_tests():
    path = os.path.join(HERE, "tests", "test_search.py")
    if not os.path.exists(path):
        return no("tests/test_search.py is missing")
    txt = open(path, encoding="utf-8").read()
    if not re.search(r"\.search\(", txt):
        return no("test_search.py never calls .search()")
    ok("tests/test_search.py exists and exercises search()")


def check_pr_json():
    path = os.path.join(HERE, "pr.json")
    if not os.path.exists(path):
        return no("pr.json is missing")
    raw = open(path, encoding="utf-8").read().strip()
    if not raw:
        return no("pr.json is empty")
    try:
        json.loads(raw)
        ok("pr.json is valid JSON (CI-ready result)")
    except json.JSONDecodeError:
        for line in raw.splitlines():
            if line.strip():
                json.loads(line)
        ok("pr.json is valid NDJSON (CI-ready result)")


def check_scoping():
    path = os.path.join(HERE, "scoping.json")
    if not os.path.exists(path):
        return no("scoping.json is missing")
    try:
        d = json.loads(open(path, encoding="utf-8").read())
    except Exception as e:
        return no(f"scoping.json does not parse: {e}")
    errs = []
    cands = d.get("candidates", {})
    want = {
        "carrier_adapter_delivery": {"verdict": "ready"},
        "internal_doc_generator": {"verdict": "needs_scoping"},
    }
    for name, exp in want.items():
        c = cands.get(name, {})
        if c.get("verdict") != exp["verdict"]:
            errs.append(f"{name}.verdict should be '{exp['verdict']}', got {c.get('verdict')!r}")
    if d.get("primary_surface") != "cli":
        errs.append("primary_surface should be 'cli'")
    if errs:
        return no("; ".join(errs))
    ok("qualification decision is correct (verdicts, surface)")


def check_objection():
    path = os.path.join(HERE, "scoping.json")
    if not os.path.exists(path):
        return no("scoping.json missing (objection check)")
    d = json.loads(open(path, encoding="utf-8").read())
    o = d.get("objection", {})
    errs = []
    if o.get("primary_pillar") != "enterprise_ready":
        errs.append("objection.primary_pillar should be 'enterprise_ready'")
    if o.get("offer_security_review") is not True:
        errs.append("objection.offer_security_review should be true")
    if o.get("bridge_to_solutions_engineer") is not True:
        errs.append("objection.bridge_to_solutions_engineer should be true")
    if errs:
        return no("; ".join(errs))
    ok("objection handled (enterprise-ready, security review, SE bridge)")


def main():
    print("== Verifying VIBE-TSE1 lab ==")
    check_vault_search()
    check_search_tests()
    check_pr_json()
    check_scoping()
    check_objection()
    print(f"\n== {len(passed)} passed, {len(failed)} failed ==")
    print("RESULT: PASS" if not failed else "RESULT: FAIL")
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
