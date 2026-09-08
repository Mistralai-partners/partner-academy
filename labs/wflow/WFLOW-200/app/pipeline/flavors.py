"""WFLOW-200 Task 6 (SOLUTION): pick the right activity flavor + inject a dependency.

Not every activity should be scheduled the same way. The SDK gives three flavors, and the
everyday skill is choosing the right one so you neither burn orchestration overhead on trivial
calls nor lose warm state on stateful ones:

- **regular** (the default) — a durable, independently-retried task scheduled through the
  orchestrator. Use it for real side effects (a DB write, an external API call).
- **local** — run the activity in the SAME worker process, skipping the scheduling round-trip.
  Wrap a burst of tiny, fast, pure-CPU calls in `run_activities_locally()` (a sync context
  manager) so their per-task overhead does not dominate.
- **sticky** — pin activities marked `sticky_to_worker=True` to ONE worker so they reuse warm
  state (an open connection, a hot cache). Enter the async context manager
  `run_sticky_worker_session()`; every sticky activity inside runs on the same worker.

One more everyday piece rides along: **dependency injection**. An activity declares a parameter
defaulted to `Depends(provider)` and the platform resolves it at call time, so config or a shared
client is injected instead of hard-coded. And a note on **granularity**: the workflow COMPOSES
small activities (validate -> normalize -> enrich -> persist) rather than burying the whole job in
one mega-activity, so each step stays independently retryable and visible in history.

Grounded in: installed mistralai-workflows==3.10.0 introspection — `run_activities_locally()`
(core/execution/local_activity.py, sync ctx mgr), `run_sticky_worker_session()` +
`activity(sticky_to_worker=True)` (core/execution/sticky_session/, async ctx mgr), `Depends()`.
"""
from __future__ import annotations

from datetime import timedelta

from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows import Depends


# ---- Dependency injected into an activity via Depends() ------------------------------
class Settings(BaseModel):
    strict: bool = True


def provide_settings() -> Settings:
    """A provider Depends() resolves at call time. Real code would read a config/secret store."""
    return Settings()


# ---- regular flavor: a durable, independently-retried side effect --------------------
@workflows.activity(
    name="validate-row",
    start_to_close_timeout=timedelta(seconds=30),
    retry_policy_max_attempts=3,
)
async def validate_row(row: dict, settings: Settings = Depends(provide_settings)) -> dict:
    # `settings` is injected by Depends(provide_settings); the caller never passes it.
    ok = bool(row.get("id")) if settings.strict else True
    return {**row, "valid": ok}


# ---- local flavor: a tiny, fast, pure transform run in-process ----------------------
@workflows.activity(name="normalize-field")
async def normalize_field(value: str) -> str:
    # Trivial and CPU-only: scheduling it through the orchestrator would cost more than the work.
    return value.strip().lower()


# ---- sticky flavor: pinned to one worker to reuse warm state ------------------------
@workflows.activity(name="lookup-in-cache", sticky_to_worker=True)
async def lookup_in_cache(key: str) -> dict:
    # sticky_to_worker=True + a sticky session route every call to the SAME worker, so a warm
    # per-worker cache or loaded model is reused instead of rebuilt each call.
    return {"key": key, "hit": True}


# ---- regular flavor: the durable write at the end ----------------------------------
@workflows.activity(name="persist-record", start_to_close_timeout=timedelta(seconds=60))
async def persist_record(record: dict) -> int:
    return 1


class ImportRequest(BaseModel):
    rows: list[dict]


@workflows.workflow.define(name="import-workflow")
class ImportWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, req: ImportRequest) -> dict:
        persisted = 0
        for row in req.rows:
            # regular: durable validation with injected settings.
            validated = await validate_row(row)

            # local: a burst of trivial transforms with no per-task scheduling overhead.
            with workflows.run_activities_locally():
                name = await normalize_field(str(validated.get("name", "")))
                city = await normalize_field(str(validated.get("city", "")))

            # sticky: an enrichment call that reuses the same worker's warm cache.
            async with workflows.run_sticky_worker_session():
                enriched = await lookup_in_cache(name or validated["id"])

            # granularity: COMPOSE small steps here; do NOT bury them in one mega-activity.
            persisted += await persist_record(
                {"id": validated["id"], "name": name, "city": city, "enriched": enriched["hit"]}
            )
        return {"persisted": persisted}
