"""WFLOW-TSE1 scoping (STARTER): map a customer's needs to the right Workflows capability.

A prospect lists five concrete requirements. For each one, place the single Workflows capability
that answers it. This is the scoping conversation a technical seller runs: name the right primitive,
so the customer hears a credible, specific answer instead of "the platform can do that."

Fill each value below with one capability key. Valid keys (the Workflows capability vocabulary):
- "activity"               anything that touches the outside world (HTTP, DB, file, LLM call)
- "query"                  read running state without modifying it (live progress)
- "signal"                 fire-and-forget message into a running workflow (human approval)
- "payload_offloading"     move data above the 2MB payload limit to the customer's own storage
- "sticky_worker_session"  reuse an in-memory resource (a loaded model) across activities
- "encryption"             encrypt payloads on the worker so the platform stores ciphertext only

Grounded in the pinned Workflows docs (SHA a3e0f0c...). See tasks.md T3.
"""
from __future__ import annotations

# TODO T3: replace each "" with the right capability key from the list above.
# requirement key -> capability key
SCOPING: dict[str, str] = {
    # A step calls the customer's partner REST API over HTTP.
    "call_external_http_api": "",
    # Operations wants to read "percent complete" while a run is in flight.
    "watch_progress_live": "",
    # A reviewer must approve high-value invoices mid-run.
    "human_approval_midrun": "",
    # Invoice bundles can exceed the 2MB payload limit and must stay in the customer's storage.
    "handle_files_over_2mb": "",
    # An expensive model must stay warm across several activities in a row.
    "reuse_loaded_model_across_steps": "",
    # Payloads must be unreadable to the platform; only the customer's workers may decrypt them.
    "platform_never_sees_cleartext": "",
}
