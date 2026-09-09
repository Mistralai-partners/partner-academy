"""WFLOW-400 Task 4 (L2.2): choose the right activity flavor and defend it.

The SDK schedules activities three ways, and the L400 skill is picking the right one per step so
you neither burn orchestration overhead on trivial calls nor lose warm state on stateful ones:

- **regular** (default) — a durable, independently-retried task scheduled through the orchestrator.
  Use it for a real side effect (a DB write, an external API call).
- **local** — run in the SAME worker process, skipping the scheduling round-trip. Wrap a burst of
  tiny, fast, pure-CPU calls in `run_activities_locally()` (a sync context manager) so per-task
  overhead does not dominate.
- **sticky** — pin activities marked `sticky_to_worker=True` to ONE worker to reuse warm state (an
  open connection, a hot cache). Enter `run_sticky_worker_session()` (async context manager); every
  sticky activity inside runs on the same worker.

Dependency injection rides along: an activity defaults a parameter to `Depends(provider)` and the
platform resolves it at call time, so a shared client or config is injected, not hard-coded.

Executable boundary (honest): the three flavor APIs and `Depends` are real SDK constructs, checked
structurally (source + registration). The `choose_flavor` selection rule is pure logic and runs
live. Actually pinning to a worker needs a running worker session.

Grounded in: WFLOW-200 flavors.py (proven `run_activities_locally` / `run_sticky_worker_session` /
`sticky_to_worker=True` / `Depends`); building-workflows/activities/basics.md (activity flavors).
"""
from __future__ import annotations

from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows import Depends


class Settings(BaseModel):
    strict: bool = True


def provide_settings() -> Settings:
    """A provider Depends() resolves at call time. Real code would read config or a secret store."""
    return Settings()


@workflows.activity(name="validate-row")
async def validate_row(row: dict, settings: Settings = Depends(provide_settings)) -> dict:
    # `settings` is injected by Depends(provide_settings); the caller never passes it.
    ok = bool(row.get("id")) if settings.strict else True
    return {**row, "valid": ok}


@workflows.activity(name="normalize-field")
async def normalize_field(value: str) -> str:
    # Trivial, CPU-only: scheduling it through the orchestrator would cost more than the work.
    return value.strip().lower()


@workflows.activity(name="lookup-in-cache", sticky_to_worker=True)
async def lookup_in_cache(key: str) -> dict:
    # sticky_to_worker=True + a sticky session route every call to the SAME worker, reusing a warm
    # per-worker cache or loaded model instead of rebuilding it each call.
    return {"key": key, "hit": True}


@workflows.activity(name="persist-record")
async def persist_record(record: dict) -> int:
    return 1


def choose_flavor(step: dict) -> str:
    """Pick the flavor for a step and be able to defend it (offline, pure logic).

    - a real side effect (write/external call) -> regular (durable, independently retried)
    - a tiny pure-CPU transform -> local (skip the scheduling round-trip)
    - a call that reuses warm per-worker state -> sticky
    """
    if step.get("side_effect"):
        return "regular"
    if step.get("reuses_warm_state"):
        return "sticky"
    if step.get("pure_cpu") and step.get("tiny"):
        return "local"
    return "regular"  # when unsure, the durable default is the safe choice


class ImportRequest(BaseModel):
    rows: list[dict]


@workflows.workflow.define(name="import-flavors-workflow")
class ImportFlavorsWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, req: ImportRequest) -> dict:
        persisted = 0
        for row in req.rows:
            validated = await validate_row(row)  # regular: durable, with injected settings

            with workflows.run_activities_locally():  # local: a burst of trivial transforms
                name = await normalize_field(str(validated.get("name", "")))
                city = await normalize_field(str(validated.get("city", "")))

            async with workflows.run_sticky_worker_session():  # sticky: reuse the worker's cache
                enriched = await lookup_in_cache(name or validated["id"])

            persisted += await persist_record(
                {"id": validated["id"], "name": name, "city": city, "enriched": enriched["hit"]}
            )
        return {"persisted": persisted}
