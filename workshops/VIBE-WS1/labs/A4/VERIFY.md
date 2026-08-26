# A4 Verify: Acceptance checks and incident "why"

- Run the checks for the branch you built. All checks are objective. Do not accept "the
prompt said read-only" as evidence.

---

## Branch (a): custom read-only agent profile

- Assume your run wrote `review-agent.json` and you are in the repo working directory.

- **Exit code is 0.**

   ```sh
   echo $?
   ```

- Expected: `0`. A non-zero code means the run failed or was interrupted.

- **Output is a valid JSON array.** `--output json` dumps the full conversation as a
   JSON ARRAY (each element is a message). It is NOT an object with cost fields.

   ```sh
   python3 -c "import json,sys; d=json.load(sys.stdin); assert isinstance(d, list); print('ok, messages:', len(d))" < review-agent.json
   ```

- Expected: `ok, messages: N`.

- **No write_file/edit tool calls in the array.**

   ```sh
   grep -E '"(write_file|edit)"' review-agent.json && echo "FOUND WRITE CALLS (bad)" || echo "no write/edit calls (good)"
   ```

- Expected: `no write/edit calls (good)`. (You may also inspect the array in Python and
   walk each message's tool calls; grep is the quick version.)

- **The branch is unchanged.** This is the strongest proof.

   ```sh
   git diff --quiet && echo "clean tree (good)" || echo "TREE CHANGED (bad)"
   ```

- Expected: `clean tree (good)`.

> Note on cost: there is no single cost field to read from this JSON. The JSON
> array is a message log, not a summary object with a `cost_usd` field. The budget
> guardrail is enforced by `--max-price`; the true safety proof here is the empty diff
> plus the absence of write tool calls, not a parsed cost number.

---

## Branch (b): pre-tool hook guard

- Assume your run (an adversarial "edit the file" prompt) wrote `review-hook.json`.

- **Exit code is 0.** The run should complete cleanly even though a tool was denied.

   ```sh
   echo $?
   ```

- Expected: `0`.

- **The hook fired and denied the write.** The deny reason from `block_writes.py`
   appears in the message stream (returned to the model as a tool error).

   ```sh
   grep -F "read-only reviewer" review-hook.json && echo "hook denied the write (good)" || echo "no deny found (bad)"
   ```

- Expected: `hook denied the write (good)`.

- **The branch is unchanged.**

   ```sh
   git diff --quiet && echo "clean tree (good)" || echo "TREE CHANGED (bad)"
   ```

- Expected: `clean tree (good)`. `src/release_tools/version.py` still reads `1.4.0`.

---

## Offline checks (no API key needed)

- These validate the guard artifacts themselves and are safe to run anytime.

- **Hook script denies and exits 0:**

  ```sh
  echo '{"tool_name":"edit","tool_input":{"path":"x"}}' | python3 solution/block_writes.py; echo "exit: $?"
  ```

- Expected: `{"decision": "deny", "reason": "Blocked 'edit': ..."}` then `exit: 0`.

- **TOML files are well-formed:**

  ```sh
  python3 -c "import tomllib; tomllib.load(open('solution/reviewer.toml','rb')); tomllib.load(open('solution/hooks.toml','rb')); print('toml ok')"
  ```

- **Shell scripts parse:**

  ```sh
  sh -n starter/ci/review.sh && sh -n solution/review.sh && echo "shell ok"
  ```

---

## Why this matters (incident report framing)

- **The prompt is not a permission boundary.** If you only tell the model "you are
read-only" and leave `write_file`, `edit`, and `bash` enabled, the model can still call
them. In an unattended CI run there is no human to catch it, so a single confused turn
can rewrite the branch or run arbitrary shell.

- **Least privilege has to be posture, not politeness.** Move the restriction into a place
the model cannot talk its way past:

- an **agent profile** that allow-lists only read tools (`read_file`, `grep`), so write
  tools do not exist for the agent; or
- a **pre-tool hook** that denies `write_file`/`edit` before the tool ever runs.

- **Common failure and the unblock.** The risk Task 1 exposes is that the run *may* edit
files despite a "read-only" prompt, and when it does `git diff` shows the change (the model
may also refuse this time, but the tools stayed enabled, so you cannot count on it). The
unblock is not a stronger prompt. Move the restriction into the agent profile or a pre-tool
hook, re-run, and confirm the empty diff. If a hook does not fire, check that its `command`
uses an absolute path and that the folder is trusted (`--trust`).
