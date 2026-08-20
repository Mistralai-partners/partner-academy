# A1 - Read before you write · VERIFY

- Self-checkable acceptance. No instructor required. Run these from your working
copy (`~/payments-service-a1`), the directory you committed as `baseline`.

## Pass condition

- Both checks must hold.

### Check 1 - The repo was not modified

```bash
git status
git diff
```

- `git diff` must be empty and `git status` must show no changes to tracked source
files. A new untracked `my-change-plan.md` is expected and is fine; it is your
plan, not an edit to the service. If any file under `src/` or `tests/` shows as
modified, this check fails.

### Check 2 - The plan names the required targets

```bash
python ~/partner-academy/workshops/VIBE-WS1/labs/A1/solution/verify/plan_check.py my-change-plan.md
```

- Must print `PASS`. The checker confirms your plan names the required target set:

- `api.py` and `handle_refund`
- `refunds.py` and `process_refund`
- `store.py`
- the idempotency concept (idempotency key)
- the test file to extend, `tests/test_refunds.py`

- An empty or off-target plan prints `FAIL` and lists exactly which required
symbols are missing.

## How to check against the reference

- Compare the targets in your `my-change-plan.md` against
`solution/change-plan.md`. Match on the file set and function names, not on
wording. If your plan reaches the same files and entry points, it is correct even
if the sentences differ.

## Why this is the right check

- An empty `git diff` proves you analyzed the service without changing it.
- A `PASS` from `plan_check.py` proves your plan landed on the correct surface: the handler, the domain function, the store, and the test.
- Together they show you can understand an unfamiliar system well enough to plan a safe change before you make it.

## Common failure and the unblock

- **Failure:** `git status` shows a source file changed, or `git diff` is not
empty. This means the agent proposed and applied an edit, or you switched out of
the `plan` agent into an editing session and something wrote to disk.

**Unblock:**

```bash
git checkout .
```

- This discards the unintended changes and returns to your `baseline`. Then
relaunch the read-only agent:

```bash
vibe --agent plan
```

- Confirm the session is read-only by asking it to list its allowed tools; you
should see read tools such as `read_file` and `grep`, and no `write_file` or
`edit`. For extra assurance, restrict the tool set explicitly:

```bash
vibe --agent plan --enabled-tools read_file --enabled-tools grep
```

- Then redo the plan and rerun both checks.
