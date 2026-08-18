"""Restart a conversation from an earlier entry (safe branching).

Grounded (mistralai==1.9.11):
  - client.beta.conversations.get_history(conversation_id=...) returns a
    ConversationHistory whose .entries are the ordered turns, each with an `id`.
  - client.beta.conversations.restart(conversation_id=..., inputs=...,
    from_entry_id=<entry.id>) returns a NEW ConversationResponse. Restart BRANCHES:
    it must yield a new conversation_id, leaving the original thread untouched.

TASK 4 (Analyze/debug): branching from the wrong entry, and the isolation check
is inverted. Fix both.
"""
from typing import Any, List


def _role_of(entry: Any):
    if isinstance(entry, dict):
        return entry.get("role")
    return getattr(entry, "role", None)


def _id_of(entry: Any):
    if isinstance(entry, dict):
        return entry["id"]
    return entry.id


def pick_branch_entry(entries: List[Any], role: str = "user", occurrence: int = 1) -> str:
    if occurrence < 1:
        raise ValueError("occurrence is 1-based")
    # BUG 1 (Task 4): symptom — you always branch from the final turn
    # instead of the requested one. This loop is handed a 1-based `occurrence`;
    # trace whether it is ever consulted.
    match = None
    for e in entries:
        if _role_of(e) == role:
            match = e
    if match is None:
        raise ValueError(f"no entry with role={role!r}")
    return _id_of(match)


def is_isolated_branch(original_id: str, restarted_id: str) -> bool:
    # BUG 2 (Task 4): symptom — the isolation guard passes when it should fail.
    # Write out what "isolated" means for the new vs original id, then compare it
    # to the condition below.
    return restarted_id == original_id
