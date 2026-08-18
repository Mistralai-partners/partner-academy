# A4: What green means

- A4 is complete when BOTH conditions hold together:

- **Determinism check passes.** No nondeterminism error surfaces on replay. The
 workflow body reads like pure orchestration: it does not read wall-clock time,
 draw randomness, touch the network or filesystem, or iterate an unordered
 collection.
- **The schedule is valid and attached.** `build_schedule_definition` returns a
 well-formed `ScheduleDefinition` with a cron trigger (5-field, UTC) and the
 workflow input, and it is attached to the workflow with
 `@workflow.define(..., schedules=[SCHEDULE])`. The worker registers the schedule
 at startup.

- A run that passes determinism but has no attached schedule is not done. A run with
a schedule but a nondeterministic body is not done either. Both, together.

## How to run verify

### Offline selftest (start here)

```
uv run python verify.py --selftest
```

- Three checks run, each printing `[PASS]`, `[FAIL]`, or `[SKIP]` with an
incident-report message:

- **imports**: the only check that needs a live SDK. It imports the lab modules
 and confirms `WORKFLOW_NAME`. When `mistralai.workflows` is not installed (for
 example a bare pre-flight), it prints `[SKIP]` instead of failing, validates
 `WORKFLOW_NAME` from source, and lets the other two checks run. Install the SDK
 with `uv add mistralai-workflows` to turn the skip into a live import.
- **determinism (static scan)**: a source-text scan of the workflow entrypoint
 body flags replay-breaking constructs (`datetime.now(`, `time.time(`,
 `random.*`, `uuid.uuid4(`, `set(`, `open(`, `os.environ`). This is the check
 that would have caught the bug before it ever reached a schedule. The scan looks
 only inside the entrypoint body, so activities may legitimately use these calls.
- **schedule shape**: a source-text check that the `ScheduleDefinition` has a
 trigger and input, and that the workflow actually declares `schedules=`.

- The determinism and schedule checks read source only, so the selftest is
meaningful offline. The starter fails those two on purpose. The solution passes
them and runs green offline (the imports check skips without the SDK).

### Live run

```
# 1. Start (or restart) the worker so it registers the schedule
make start-worker

# 2. Trigger a run, or let the schedule fire
make execute workflow=reconciliation-workflow input='{"account_ids":["acct-001","acct-002","acct-003"]}'

# 3. Read the live guidance
uv run python verify.py
```

- Then open console.mistral.ai. Green = the run completes with no nondeterminism
error on replay and the workflow appears with its schedule registered.

- **[VERIFY] Live replay from a harness is not fully grounded.** The exact mechanism
to force a replay from a test (for example restarting the worker mid-execution) is
not named in the live docs, so the live mode of `verify.py` prints guidance rather
than asserting. Confirmed execution surface you can drive a run with:
`client.workflows.execute_workflow(...)`,
`client.workflows.executions.get_workflow_execution(...).status`, and the
`WORKFLOW_EXECUTION_COMPLETED` event from
`client.workflows.events.get_stream_events(...)`. Asserting a schedule's next-fire
time from the harness is also not grounded; the REST API is the documented path
for independent schedule management.

## How to read a replay divergence

- The console shows the nondeterminism error with a **step index**: replay diverged
at step N because a command in the workflow body produced a different value on the
second run. Map that step back to the line in the entrypoint. Ask of the suspect
line: would this produce the same value on a second run of the same body? Wall-
clock time will not. A `set` will not, because it has no defined iteration order.

## The intermittent set-iteration trap

- The wall-clock bug is loud: it changes on every call. The `set`-iteration bug is
quiet: iteration order can be the same on some runs and different on others, so
the workflow fails only sometimes. That is why you trace from the step index
rather than re-reading top to bottom, and why the fix must make the iteration
order deterministic (for example dedupe while preserving order, then sort), not
just relocate the time call. If you fix only the loud bug, replay still diverges
intermittently and the determinism check stays red.
