#!/usr/bin/env python3
"""Acceptance check for the MAIS-200 walkthrough lab.

Run from this folder after reading the working code:

    python3 verify.py

Confirms the structural properties of all five task scripts: the correct SDK
imports, function signatures, and API constructor patterns are in place. All
checks are offline and deterministic (no API key, no network). A live run of
each script against the real Mistral API is a separate, optional step.
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


def _has_import(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and name in node.module:
            return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if name in alias.name:
                    return True
    return False


def _has_function(tree, name):
    return any(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name
        for n in ast.walk(tree)
    )


def check_t1():
    tree = _parse("t1_reliable_agent.py")
    if tree is None:
        return no("t1_reliable_agent.py is missing")
    src = _source("t1_reliable_agent.py")
    if not _has_import(tree, "mistralai"):
        return no("t1: missing mistralai import")
    if not _has_function(tree, "build_agent"):
        return no("t1: missing build_agent function")
    if "beta.agents.create" not in src:
        return no("t1: must use client.beta.agents.create to build the agent")
    if "temperature" not in src:
        return no("t1: must set temperature in completion_args for deterministic output")
    if "max_tokens" not in src:
        return no("t1: must set max_tokens to bound output length")
    ok("t1 reliable agent: correct structure (agents.create + completion_args)")


def check_t2():
    tree = _parse("t2_tools_function_result.py")
    if tree is None:
        return no("t2_tools_function_result.py is missing")
    src = _source("t2_tools_function_result.py")
    if "FunctionResultEntry" not in src:
        return no("t2: must import and use FunctionResultEntry to return tool results")
    if "tool_call_id" not in src:
        return no("t2: must match tool_call_id from the function call to the result")
    if "conversations" not in src:
        return no("t2: must use the conversations API to drive the tool-calling loop")
    ok("t2 tools + function result: FunctionResultEntry with matching tool_call_id")


def check_t3():
    tree = _parse("t3_document_to_structured.py")
    if tree is None:
        return no("t3_document_to_structured.py is missing")
    src = _source("t3_document_to_structured.py")
    if "ocr" not in src:
        return no("t3: must use the OCR API (client.ocr.process)")
    if "document_annotation" not in src:
        return no("t3: must use document_annotation_format for structured extraction")
    if "pydantic" not in src.lower() and "BaseModel" not in src:
        return no("t3: must define a Pydantic model for the annotation schema")
    ok("t3 document to structured: OCR + Pydantic annotation schema")


def check_t4():
    tree = _parse("t4_rag_knowledge_base.py")
    if tree is None:
        return no("t4_rag_knowledge_base.py is missing")
    src = _source("t4_rag_knowledge_base.py")
    if "embeddings" not in src:
        return no("t4: must use the embeddings API (client.embeddings.create)")
    if "cosine" not in src.lower() and "dot" not in src.lower() and "similarity" not in src.lower():
        return no("t4: must compute similarity (cosine) for retrieval ranking")
    if "mistral-embed" not in src:
        return no("t4: must use the mistral-embed model for embeddings")
    ok("t4 RAG knowledge base: embeddings + cosine similarity retrieval")


def check_t5():
    tree = _parse("t5_guardrails_moderation.py")
    if tree is None:
        return no("t5_guardrails_moderation.py is missing")
    src = _source("t5_guardrails_moderation.py")
    if "moderat" not in src.lower():
        return no("t5: must use the Moderation API (client.classifiers.moderate)")
    if "categories" not in src:
        return no("t5: must check moderation result categories for flagged content")
    ok("t5 guardrails moderation: Moderation API + category check gate")


def main():
    print("== Verifying MAIS-200 lab ==")
    check_t1()
    check_t2()
    check_t3()
    check_t4()
    check_t5()
    print(f"\n== {len(passed)} passed, {len(failed)} failed ==")
    print("RESULT: PASS" if not failed else "RESULT: FAIL")
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
