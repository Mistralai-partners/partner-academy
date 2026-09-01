"""Restart a conversation from an earlier entry (safe branching).

Grounded (mistralai==2.9.4):
  - client.beta.conversations.get_history(conversation_id=...) returns a
    ConversationHistory whose .entries are the ordered turns, each with an `id`.
  - client.beta.conversations.restart(conversation_id=..., inputs=...,
    from_entry_id=<entry.id>) returns a NEW ConversationResponse. Restart BRANCHES:
    it must yield a new conversation_id, leaving the original thread untouched.

The Analyze skill: pick the correct branch point (the Nth turn of a given role),
and verify isolation (the restart produced a genuinely new conversation, not a
mutation of the original).
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
    """Return the id of the `occurrence`-th (1-based) entry with the given role."""
    if occurrence < 1:
        raise ValueError("occurrence is 1-based")
    seen = 0
    for e in entries:
        if _role_of(e) == role:
            seen += 1
            if seen == occurrence:
                return _id_of(e)
    raise ValueError(f"no entry #{occurrence} with role={role!r}")


def is_isolated_branch(original_id: str, restarted_id: str) -> bool:
    """A restart is safe only if it created a NEW conversation."""
    return bool(restarted_id) and restarted_id != original_id
