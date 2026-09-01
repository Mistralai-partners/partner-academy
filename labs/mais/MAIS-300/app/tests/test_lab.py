"""Deterministic, offline acceptance tests for the MAIS-300 lab.

These exercise the pure logic the learner fixes. They use the REAL mistralai
SDK event/retry types but make NO network calls, so the check is reproducible and
free. The live_*.py scripts prove the same code paths against the real API.
"""
from types import SimpleNamespace

import pytest

from mais.streaming import fold_events
from mais.concurrency import build_retry_config, should_retry
from mais.rag import chunk_text, top_k, build_grounded_prompt
from mais.entries import pick_branch_entry, is_isolated_branch
from mais.embedding_cost import bytes_per_vector, storage_ratio

# Real SDK types (no network) ------------------------------------------------
from mistralai.client.models import (
    MessageOutputEvent,
    ResponseDoneEvent,
    ResponseErrorEvent,
    FunctionCallEvent,
)
from mistralai.client.models.conversationevents import ConversationEvents
from mistralai.client.models.conversationusageinfo import ConversationUsageInfo
from mistralai.client.utils import RetryConfig


def _wrap(etype, data):
    return ConversationEvents(event=etype, data=data)


# --- Task 1: streaming fold -------------------------------------------------
def test_stream_accumulates_all_deltas():
    events = [
        _wrap("message.output.delta", MessageOutputEvent(id="1", content="Hel")),
        _wrap("message.output.delta", MessageOutputEvent(id="2", content="lo ")),
        _wrap("message.output.delta", MessageOutputEvent(id="3", content="world")),
        _wrap("conversation.response.done", ResponseDoneEvent(usage=ConversationUsageInfo())),
    ]
    r = fold_events(events)
    assert r.text == "Hello world"      # BUG 1 in starter: only "world" survives
    assert r.terminated is True
    assert r.error is None


def test_stream_terminates_on_error():
    events = [
        _wrap("message.output.delta", MessageOutputEvent(id="1", content="partial")),
        _wrap("conversation.response.error", ResponseErrorEvent(message="upstream 503", code=503)),
        # A delta AFTER the error must never be reached (loop must have broken):
        _wrap("message.output.delta", MessageOutputEvent(id="x", content="LEAKED")),
    ]
    r = fold_events(events)
    assert r.terminated is True          # BUG 2 in starter: never terminates on error
    assert r.error == "upstream 503"
    assert "LEAKED" not in r.text


def test_stream_records_tool_calls():
    events = [
        _wrap("function.call.delta", FunctionCallEvent(id="f", name="web_search",
                                                       tool_call_id="tc", arguments="{}")),
        _wrap("message.output.delta", MessageOutputEvent(id="1", content="done")),
        _wrap("conversation.response.done", ResponseDoneEvent(usage=ConversationUsageInfo())),
    ]
    r = fold_events(events)
    assert "web_search" in r.tools_seen


# --- Task 2: retry policy ---------------------------------------------------
def test_should_retry_transient_only():
    assert should_retry(429) is True
    assert should_retry(503) is True
    assert should_retry(500) is True
    assert should_retry(400) is False    # BUG 2 in starter: retries 4xx
    assert should_retry(401) is False
    assert should_retry(404) is False


def test_retry_config_is_exponential():
    cfg = build_retry_config()
    assert isinstance(cfg, RetryConfig)
    assert cfg.backoff.exponent > 1.0    # BUG 1 in starter: exponent 1.0 (linear)
    assert cfg.backoff.initial_interval > 0
    assert cfg.backoff.max_interval >= cfg.backoff.initial_interval


# --- Task 3: RAG chunk + cosine --------------------------------------------
def test_chunk_overlap():
    # 10 chars, size 4, overlap 2 -> step 2 -> windows at 0,2,4,6,8
    chunks = chunk_text("ABCDEFGHIJ", size=4, overlap=2)
    assert chunks[0] == "ABCD"
    assert chunks[1] == "CDEF"          # BUG 1 in starter: no overlap -> "EFGH"
    assert chunks[2] == "EFGH"


def test_cosine_ranks_by_direction_not_magnitude():
    # Row 0 points the same DIRECTION as the query but small magnitude.
    # Row 1 is longer but points a different direction. Cosine must pick row 0;
    # a raw dot product (starter bug) picks row 1.
    query = [1.0, 0.0]
    matrix = [[0.1, 0.0], [3.0, 3.0]]
    assert top_k(query, matrix, 1) == [0]


def test_grounded_prompt_contains_context_and_query():
    p = build_grounded_prompt("What is X?", ["fact one", "fact two"])
    assert "fact one" in p and "fact two" in p
    assert "What is X?" in p


# --- Task 4: restart from entry --------------------------------------------
def _entry(i, role):
    return SimpleNamespace(id=i, role=role)


def test_pick_branch_entry_by_occurrence():
    entries = [
        _entry("e1", "user"),
        _entry("e2", "assistant"),
        _entry("e3", "user"),
        _entry("e4", "assistant"),
    ]
    assert pick_branch_entry(entries, role="user", occurrence=1) == "e1"  # starter -> "e3"
    assert pick_branch_entry(entries, role="user", occurrence=2) == "e3"


def test_isolation_check():
    assert is_isolated_branch("conv_A", "conv_B") is True    # starter inverted
    assert is_isolated_branch("conv_A", "conv_A") is False
    assert is_isolated_branch("conv_A", "") is False


# --- Task 5: embedding storage ---------------------------------------------
def test_bytes_per_vector():
    assert bytes_per_vector(1024, "float") == 4096    # starter -> 8192
    assert bytes_per_vector(1024, "int8") == 1024
    assert bytes_per_vector(1024, "binary") == 128    # starter -> 1024


def test_storage_ratio_binary_is_32x_smaller_than_float():
    assert storage_ratio(1024, "float", 1024, "binary") == pytest.approx(32.0)
