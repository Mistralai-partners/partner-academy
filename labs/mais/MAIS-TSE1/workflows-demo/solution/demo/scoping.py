"""WFLOW-TSE1 scoping (SOLUTION): map a customer's needs to the right Workflows capability.

A prospect lists five concrete requirements. For each one, place the single Workflows capability
that answers it. This is the scoping conversation a technical seller runs: name the right primitive,
so the customer hears a credible, specific answer instead of "the platform can do that."

Valid capability keys (the Workflows capability vocabulary, grounded in the pinned docs):
- "activity"               anything that touches the outside world (HTTP, DB, file, LLM call)
- "query"                  read running state without modifying it (live progress)
- "signal"                 fire-and-forget message into a running workflow (human approval)
- "payload_offloading"     move data above the 2MB payload limit to the customer's own storage
- "sticky_worker_session"  reuse an in-memory resource (a loaded model) across activities
- "encryption"             encrypt payloads on the worker so the platform stores ciphertext only

Grounded in the pinned Workflows docs (SHA a3e0f0c...): building-workflows/workflows.md,
building-workflows/activities/basics.md, interacting-with-workflows/queries.md,
interacting-with-workflows/signals.md, building-workflows/payload_offloading.md,
building-workflows/activities/sticky_worker_sessions.md, building-workflows/encryption.md.
"""
from __future__ import annotations

# requirement key -> capability key
SCOPING: dict[str, str] = {
    # A step calls the customer's partner REST API over HTTP.
    "call_external_http_api": "activity",
    # Operations wants to read "percent complete" while a run is in flight.
    "watch_progress_live": "query",
    # A reviewer must approve high-value invoices mid-run.
    "human_approval_midrun": "signal",
    # Invoice bundles can exceed the 2MB payload limit and must stay in the customer's storage.
    "handle_files_over_2mb": "payload_offloading",
    # An expensive model must stay warm across several activities in a row.
    "reuse_loaded_model_across_steps": "sticky_worker_session",
    # Payloads must be unreadable to the platform; only the customer's workers may decrypt them.
    "platform_never_sees_cleartext": "encryption",
}
