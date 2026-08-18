# A2 - Verification

## What green means

- Green for A2 means the execution recovered on its own. Specifically: against the
injected downstream fault, the `resilient_confirm` execution reached the terminal
status `COMPLETED`, and it got there via retry (more than one attempt). More than
one attempt is the whole point. It proves your durability configuration carried
the execution, rather than a lucky clean run on the first try.

## How to run it

- The verifier lives at the activity root, next to the Makefile.

### Offline self-test

```
python verify.py --selftest
```

- No API key and no network. It confirms the workflow name is discoverable
(`WORKFLOW_NAME`) and the expected symbols are present. If the SDK is installed
it does this by importing the module; if the SDK is not installed yet it falls
back to a static source scan so this check still runs green offline, before
`uv add`. Run it first, before you start a worker, to prove the file is wired up.

### Live check

```
# terminal 1
make start-worker

# terminal 2
export MISTRAL_API_KEY=...
python verify.py
```

- The live check triggers a fresh execution against the re-armed fault, polls the
execution to a terminal status, and asserts recovery-via-retry. Each run uses a
new `request_id`, so the fault fires every time.

## How the attempt count is established

- The verifier proves recovery-via-retry from the fault injector's own attempt
counter, which the injector records on disk each time the activity re-enters.
That is deterministic ground truth for this lab and needs no unconfirmed SDK
field.

- In production you would instead read retry evidence from the execution history
or the console at console.mistral.ai. Reading a typed per-attempt retry count
programmatically from the execution object is marked `[VERIFY]` in the code:
counting `ACTIVITY_TASK_*` events from the full history is possible, but that
accessor is not confirmed here.

## Reading a hang versus a failure

- The two failure modes teach different lessons, so the verifier names which one
happened.

- Hang: the verifier reports that the execution never reached a terminal state
  within the poll window. This is what the starter does. With no
  `start_to_close_timeout` and no `heartbeat_timeout`, the wedged attempt is
  never given up on, so the whole execution stalls instead of failing over. The
  fix is to bound the attempt and to heartbeat the loop.

- Failure: the verifier reports a terminal status that is not `COMPLETED`
  (for example `FAILED`) after N attempts. This usually means the retry budget
  ran out before the fault cleared. Ask whether `retry_policy_max_attempts` is
  below the number of attempts the fault needs (its transient failures plus the
  one wedge).

- False green guard: if the execution reaches `COMPLETED` on the first attempt,
  the verifier fails on purpose. That means the fault did not fire, so the retry
  path was never exercised. Re-run; the fresh `request_id` re-arms the fault.

## Expected results

- Starter (no durability config): the live check does not pass. It reports a
  hang, or a failure if the platform rejects an unbounded activity outright.
  Note: the exact starter symptom (immediate rejection versus runtime hang)
  depends on SDK defaults and is marked `[VERIFY]` in the verifier.
- Solution: `--selftest` is green, and the live check is green with an attempt
  count greater than 1.
