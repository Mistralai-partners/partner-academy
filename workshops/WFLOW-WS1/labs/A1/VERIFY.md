# A1: What "green" means

- This activity is complete when a live run of `verify.py` passes. Green means one
specific thing: an execution of the `confirm-order` workflow reaches the
`COMPLETED` status **and** returns the expected confirmation result.

- Both conditions must hold:

- **Status:** the execution reaches `COMPLETED` (its terminal success status).
- **Result:** the returned value equals the expected confirmation for the test
  input.

- The harness triggers with this input:

```json
{"order_id": "A-1001", "customer": "Acme Robotics"}
```

- and expects this result:

```
Order A-1001 confirmed for Acme Robotics.
```

## How to run it

### Offline pre-flight (no worker, no API call)

```bash
python verify.py --selftest
```

- This imports the workflow file and confirms the workflow name is discoverable. It
is safe to run before you edit anything and before any worker is started. It
passes on the untouched starter, because the only gap is the activity's return
value, which the pre-flight does not exercise. Use it to confirm the files are
wired.

### Live check (worker required)

- Export your API key: `export MISTRAL_API_KEY=...`
- Start the worker in one terminal: `make start-worker`
- Run the live check in a second terminal: `python verify.py`

- Exit code `0` means both conditions above hold. A non-zero exit means one of them
failed, and the harness prints an incident report explaining which.

## How to read a failure

- Failures print as an incident report with two lines: `INCIDENT` names the symptom,
and `TRACE IT` points at the most likely cause. The ones you are most likely to
see in A1:

- **"the trigger was rejected ... workflow unknown."** No worker has registered
  the name yet, or the registered name differs from what was triggered. Confirm
  `make start-worker` is running and that its startup log lists `confirm-order`.
- **"reached COMPLETED but returned <value>, expected <value>."** The wiring
  works, but the activity is computing the wrong confirmation string. Match it to
  the expected result above.
- **"did not reach COMPLETED within Ns" (last status: RUNNING).** Two common
  causes. First, the worker stopped processing tasks: confirm `make start-worker`
  is still up. Second, and this is the expected failure for the unfinished
  starter: `confirm_order` still returns None, and because the activity is typed
  `-> str`, the platform rejects the None result and retries the workflow task, so
  the execution never reaches COMPLETED and sits at RUNNING. Complete the `# TODO`
  in `confirm_order` so the activity returns the confirmation string, then re-run.
- **"could not import confirm_order.py."** A syntax or import error in the
  workflow file. Because the worker discovers workflows by importing files under
  `src/workflows/`, the same error would stop the worker from registering the
  workflow. Fix the error shown, then re-run.

## Verification notes

- The SDK surfaces used by `verify.py` are confirmed against the live Mistral AI
Studio Workflows docs:

- Trigger: `client.workflows.execute_workflow(workflow_identifier=..., input=...,
  execution_id=...)`. The harness supplies its own `execution_id` so it can poll
  the exact run it started.
- Fetch by id:
  `client.workflows.executions.get_workflow_execution(execution_id=...)`, then
  read `execution.status` and `execution.result`.
- Terminal statuses: `COMPLETED` on success; `FAILED`, `CANCELED`, and
  `TIMED_OUT` on failure.
- Client: `from mistralai.client import Mistral`; the harness passes
  `api_key=os.environ["MISTRAL_API_KEY"]` explicitly.

- The harness also unwraps a `{"result": <value>}` envelope if `execution.result`
is returned that way, matching the `Result: {'result': ...}` line shown in the
worker log.
