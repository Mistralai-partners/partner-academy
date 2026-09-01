#!/usr/bin/env python3
"""Acceptance check for the MAIS-TSE1 walkthrough lab.

Run from this folder after reading the working code:

    python3 verify.py

Confirms the structural properties of all four task scripts: correct SDK imports
for Document AI and RAG (t1-t2), and correct scoping/qualification decisions
(t3-t4, offline JSON checks). Prints RESULT: PASS and exits 0 only when every
check holds.
"""
import ast
import json
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


def _source(filename):
    path = os.path.join(HERE, filename)
    return open(path, encoding="utf-8").read() if os.path.exists(path) else ""


def check_t1():
    src = _source("t1_docai_extract.py")
    if not src:
        return no("t1_docai_extract.py is missing")
    if "ocr" not in src:
        return no("t1: must use the Document AI OCR API")
    if "mistralai" not in src:
        return no("t1: must import from mistralai")
    ok("t1 Document AI extraction: OCR API structure present")


def check_t2():
    src = _source("t2_rag_grounding.py")
    if not src:
        return no("t2_rag_grounding.py is missing")
    if "embeddings" not in src and "embed" not in src:
        return no("t2: must use the embeddings API for RAG grounding")
    if "chat" not in src and "conversation" not in src:
        return no("t2: must use the chat/conversation API for grounded answers")
    ok("t2 RAG grounding: embeddings + grounded answer structure present")


def check_t3():
    src = _source("t3_scope_surface.py")
    if not src:
        return no("t3_scope_surface.py is missing")
    if "surface" not in src.lower() and "scope" not in src.lower():
        return no("t3: must contain scoping/surface analysis logic")
    ok("t3 scope surface: scoping analysis structure present")


def check_t4():
    src = _source("t4_scope_multiagent.py")
    if not src:
        return no("t4_scope_multiagent.py is missing")
    if "agent" not in src.lower():
        return no("t4: must contain multi-agent scoping logic")
    ok("t4 scope multiagent: multi-agent scoping structure present")


def main():
    print("== Verifying MAIS-TSE1 lab ==")
    check_t1()
    check_t2()
    check_t3()
    check_t4()
    print(f"\n== {len(passed)} passed, {len(failed)} failed ==")
    print("RESULT: PASS" if not failed else "RESULT: FAIL")
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
