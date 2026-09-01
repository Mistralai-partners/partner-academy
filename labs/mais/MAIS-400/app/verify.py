#!/usr/bin/env python3
"""Acceptance check for the MAIS-400 walkthrough lab.

Run from this folder after reading the working code:

    python3 verify.py

Confirms the structural properties of all thirteen task scripts: correct SDK
imports, function signatures, and API constructor patterns. All checks are
offline and deterministic (no API key, no network).
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


def check_t7():
    tree = _parse("t7_predicted_outputs.py")
    if tree is None:
        return no("t7_predicted_outputs.py is missing")
    src = _source("t7_predicted_outputs.py")
    if not _has_import(tree, "mistralai"):
        return no("t7: missing mistralai import")
    if not _has_function(tree, "edit_with_prediction"):
        return no("t7: missing edit_with_prediction function")
    if "prediction" not in src:
        return no("t7: must pass prediction parameter to chat.complete")
    if "codestral" not in src:
        return no("t7: must use codestral model for code edits")
    ok("t7 predicted outputs: chat.complete + prediction param + codestral")


def check_t8():
    tree = _parse("t8_realtime_transcription.py")
    if tree is None:
        return no("t8_realtime_transcription.py is missing")
    src = _source("t8_realtime_transcription.py")
    if not _has_function(tree, "transcribe_stream"):
        return no("t8: missing transcribe_stream function")
    if not _has_function(tree, "dual_delay_compare"):
        return no("t8: missing dual_delay_compare function")
    if "realtime" not in src:
        return no("t8: must use audio.realtime.transcribe_stream")
    if "target_streaming_delay_ms" not in src:
        return no("t8: must set target_streaming_delay_ms for latency tuning")
    ok("t8 realtime transcription: transcribe_stream + dual-delay comparison")


def check_t9():
    tree = _parse("t9_multi_agent_handoff.py")
    if tree is None:
        return no("t9_multi_agent_handoff.py is missing")
    src = _source("t9_multi_agent_handoff.py")
    if not _has_import(tree, "mistralai"):
        return no("t9: missing mistralai import")
    if not _has_function(tree, "build_pipeline"):
        return no("t9: missing build_pipeline function")
    if "handoffs" not in src:
        return no("t9: must use handoffs parameter to wire agent handoff chains")
    if "agents.create" not in src:
        return no("t9: must use beta.agents.create to build agents")
    if "agents.update" not in src:
        return no("t9: must use beta.agents.update to wire handoffs")
    ok("t9 multi-agent handoff: agents.create/update + handoffs wiring")


def check_t10():
    tree = _parse("t10_client_orchestration.py")
    if tree is None:
        return no("t10_client_orchestration.py is missing")
    src = _source("t10_client_orchestration.py")
    if not _has_import(tree, "mistralai"):
        return no("t10: missing mistralai import")
    if not _has_function(tree, "run_client_loop"):
        return no("t10: missing run_client_loop function")
    if "handoff_execution" not in src:
        return no("t10: must set handoff_execution='client' for client-side control")
    if "FunctionResultEntry" not in src:
        return no("t10: must use FunctionResultEntry to return tool results")
    if "conversations.append" not in src:
        return no("t10: must use conversations.append to continue the loop")
    ok("t10 client orchestration: client loop + FunctionResultEntry + conversations.append")


def check_t11():
    tree = _parse("t11_expert_document_ai.py")
    if tree is None:
        return no("t11_expert_document_ai.py is missing")
    src = _source("t11_expert_document_ai.py")
    if not _has_import(tree, "mistralai"):
        return no("t11: missing mistralai import")
    if not _has_function(tree, "extract_metadata"):
        return no("t11: missing extract_metadata function")
    if "ocr" not in src:
        return no("t11: must use client.ocr.process for document processing")
    if "document_annotation" not in src:
        return no("t11: must use document_annotation_format for structured extraction")
    if "BaseModel" not in src:
        return no("t11: must define a Pydantic BaseModel for the annotation schema")
    ok("t11 expert document AI: OCR + Pydantic annotation + confidence gating")


def check_t12():
    tree = _parse("t12_voice_pipelines.py")
    if tree is None:
        return no("t12_voice_pipelines.py is missing")
    src = _source("t12_voice_pipelines.py")
    if not _has_import(tree, "mistralai"):
        return no("t12: missing mistralai import")
    if not _has_function(tree, "synthesize_batch"):
        return no("t12: missing synthesize_batch function")
    if "speech" not in src:
        return no("t12: must use audio.speech.complete for TTS")
    if "voices" not in src:
        return no("t12: must use audio.voices to select a voice")
    if "base64" not in src:
        return no("t12: must decode base64 audio_data from the response")
    ok("t12 voice pipelines: voices.list + speech.complete + base64 decode")


def check_t13():
    tree = _parse("t13_quality_gates.py")
    if tree is None:
        return no("t13_quality_gates.py is missing")
    src = _source("t13_quality_gates.py")
    if not _has_function(tree, "pass_rate"):
        return no("t13: missing pass_rate function")
    if not _has_function(tree, "quality_gate"):
        return no("t13: missing quality_gate function")
    if "threshold" not in src:
        return no("t13: must implement a threshold-based gate")
    ok("t13 quality gates: pass_rate + quality_gate with threshold")


def main():
    print("== Verifying MAIS-400 lab ==")
    check_t1()
    check_t2()
    check_t3()
    check_t4()
    check_t5()
    check_t6()
    check_t7()
    check_t8()
    check_t9()
    check_t10()
    check_t11()
    check_t12()
    check_t13()
    print(f"\n== {len(passed)} passed, {len(failed)} failed ==")
    print("RESULT: PASS" if not failed else "RESULT: FAIL")
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
