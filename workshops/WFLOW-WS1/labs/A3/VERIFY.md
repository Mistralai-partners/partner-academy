# A3 - What green means

- A3 is complete when the workflow's state reflects each of the three
interactions, each driven by the right primitive.

## The three things green proves

- **State reflects a signal.** After `verify.py` sends an `add_notification`
   signal, a `get_status` query reports `notification_count >= 1`. The signal
   landed and the workflow woke to it.
- **The query returns state read-only.** `get_status` reports current state and
   changes nothing. It is non-async and side-effect-free.
- **The update returns a confirmation and mutates.** `set_priority` returns a
   dict that reports the new priority, and a follow-up query shows that priority
   in the case state.

- All three together is completion.

## How to run

**Selftest (offline, run this first):**

```
python verify.py --selftest
```

- No API key and no worker needed. It proves `triage_workflow.py` is real,
importable Python and that `add_notification`, `get_status`, and `set_priority`
are all discoverable. If the SDK is not installed yet, it falls back to a source
scan and tells you to run `uv add mistralai-workflows`.

**Live (drives a real execution):**

```
# terminal 1
make start-worker

# terminal 2
export MISTRAL_API_KEY=...   # if not already exported
python verify.py
```

- Live mode triggers the workflow, sends a signal, queries, applies an update,
and queries again. Green prints a one-line summary and exits 0.

## How to read a stale-state failure

- The signature failure for this activity is:

```
FAIL  query returned stale state after the signal: notification_count is still 0 ...
      Did the workflow wait_condition on the change, or is it busy-looping past it?
```

- Read this as an incident, not a typo. The signal was accepted, but the query
that follows it does not see the change. The root cause is in the entrypoint's
wait, not in the signal handler. A workflow that busy-loops never suspends on
the change, so the delivered notification is not observed durably. Fix it by
having the entrypoint `await workflows.workflow.wait_condition(...)` on the
notification count, and do not clear the notifications (advance a cursor
instead) so the query keeps reflecting the full case history.

- Other failures map to a specific task:

- **Update failed or returned nothing** points at the `set_priority` stub. An
  update must return a value; a signal cannot stand in for it.
- **State does not reflect the update** means the update returned a confirmation
  but did not durably mutate `self.priority`.
- **Signal rejected with 422** means the payload did not match the handler's
  declared params (`message: str`, `priority: int`). That validation is the
  payload contract doing its job.
