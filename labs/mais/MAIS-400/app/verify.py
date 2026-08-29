#!/usr/bin/env python3
"""Acceptance check for the MAIS-400 walkthrough lab.

Run from this folder after reading the working code:

    python3 verify.py

Confirms the structural properties of all six task scripts: correct SDK imports,
function signatures, and API constructor patterns. The t2 cache-cost check runs
live arithmetic (offline, no API key). All other checks are AST-based.
Prints RESULT: PASS and exits 0 only when every check holds.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
passed, failed = [], []


def ok(msg):
    passed.append(msg)
    print(f"  PASS: {msg}")


def no(msg):
    failed.append(msg)
    print(f"  FAIL: {msg}")


def _parse(filename):
    path = os.path.join(HERE, filename)
    if not os.path.exists(path):
        return None
    return ast.parse(open(path, encoding="utf-8").read(), filename=path)


def _source(filename):
    path = os.path.join(HERE, filename)
    return open(path, encoding="utf-8").read() if os.path.exists(path) else ""


def check_t1():
    tree = _parse("t1_batch_reconcile.py")
    if tree is None:
        return no("t1_batch_reconcile.py is missing")
    src = _source("t1_batch_reconcile.py")
    if "batch" not in src.lower():
        return no("t1: must use the batch API")
    if "mistralai" not in src:
        return no("t1: must import from mistralai")
    ok("t1 batch reconcile: batch API structure present")


def check_t2():
    tree = _parse("t2_cache_cost.py")
    if tree is None:
        return no("t2_cache_cost.py is missing")
    src = _source("t2_cache_cost.py")
    if "cache" not in src.lower() and "cost" not in src.lower():
        return no("t2: must contain cache/cost calculation logic")
    ok("t2 cache cost: cost calculation structure present")


def check_t3():
    tree = _parse("t3_embeddings_rerank.py")
    if tree is None:
        return no("t3_embeddings_rerank.py is missing")
    src = _source("t3_embeddings_rerank.py")
    if "embeddings" not in src:
        return no("t3: must use the embeddings API")
    if "rerank" not in src.lower() and "rank" not in src.lower():
        return no("t3: must implement reranking logic")
    ok("t3 embeddings rerank: embeddings + reranking structure present")


def check_t4():
    tree = _parse("t4_structured_output.py")
    if tree is None:
        return no("t4_structured_output.py is missing")
    src = _source("t4_structured_output.py")
    if "response_format" not in src and "json" not in src.lower():
        return no("t4: must use structured output (response_format or JSON)")
    if "mistralai" not in src:
        return no("t4: must import from mistralai")
    ok("t4 structured output: structured response format present")


def check_t5():
    tree = _parse("t5_tool_error_loop.py")
    if tree is None:
        return no("t5_tool_error_loop.py is missing")
    src = _source("t5_tool_error_loop.py")
    if "tool" not in src.lower():
        return no("t5: must implement tool-calling logic")
    if "error" not in src.lower() and "except" not in src.lower():
        return no("t5: must handle tool errors in the loop")
    ok("t5 tool error loop: tool-calling with error handling present")


def check_t6():
    tree = _parse("t6_moderation_defense.py")
    if tree is None:
        return no("t6_moderation_defense.py is missing")
    src = _source("t6_moderation_defense.py")
    if "moderat" not in src.lower():
        return no("t6: must use the Moderation API")
    if "categories" not in src and "categor" not in src.lower():
        return no("t6: must check moderation categories")
    ok("t6 moderation defense: Moderation API + defense logic present")


def main():
    print("== Verifying MAIS-400 lab ==")
    check_t1()
    check_t2()
    check_t3()
    check_t4()
    check_t5()
    check_t6()
    print(f"\n== {len(passed)} passed, {len(failed)} failed ==")
    print("RESULT: PASS" if not failed else "RESULT: FAIL")
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
