# A2: Edit under review to a passing test

## What you will do

- You will drive an interactive `vibe` session to add one feature to a small
reporting tool. A failing acceptance test is already written and acts as the
spec. You hand that test to the agent, ask it to implement only the new format,
review each edit as it is proposed (approve the in-scope ones, deny anything
out of scope), then run the test to green. This is the core loop of working with
an agent under review: the test defines "done", and you keep the change scoped.


- Format: hands-on, interactive `vibe` CLI.
- Time: about 20 minutes, plus a 5-minute setup.

## Prerequisites

- `vibe` CLI installed and authenticated. Confirm with `vibe --version`.
- Python 3.9+ and `pytest` available (`python -m pytest --version`).
- A terminal in a scratch directory you can write to.

## Done when these 3 checks pass

- `python -m pytest tests/test_export.py::test_json_format` passes.
- `python -m pytest` shows both `test_csv_format` and `test_json_format` green.
- `git diff --stat` (against your baseline commit) touches only the export
   module: `src/csv_report/export.py` and `src/csv_report/cli.py`. The test file
   and everything else are unchanged. This must match `solution/reference-diff.txt`.

- See `VERIFY.md` for the objective acceptance procedure.

---

## Setup (about 5 minutes)

- Copy the starter project into a working directory and baseline it in git so the
scope check works later.

```bash
cp -R starter my-a2 && cd my-a2
git init -q && git add -A && git commit -qm baseline
python -m pytest
```

- You should see `test_csv_format` pass and `test_json_format` fail with
`ValueError: unsupported format: json`. That red test is your contract.

---

## Task 1: Launch vibe and pin the contract

- Objective: Start a reviewed `vibe` session and give the agent the
  failing test as the specification.
- Scenario: You are in `my-a2/`. You want the agent to work under your review,
  proposing edits you approve one at a time, not auto-applying them.
- Steps:
  - Launch an interactive session with the default reviewed agent:
     ```bash
     vibe --agent default
     ```
- This folder is not a trusted folder yet, so `vibe` will warn and ask you to
     trust it. Accept the trust prompt (or relaunch with `vibe --trust --agent default`).
     The `default` agent asks for approval on every tool call, which is exactly
     what this lab is about. Do not use `--auto-approve` / `--yolo` here: an
     unreviewed edit session defeats the purpose of the review loop.
  - In the session, pin the test as the spec with an @-file mention and state
     the boundary explicitly:
     ```
     @tests/test_export.py is the contract and is frozen. Implement only what is
     needed to make test_json_format pass. Do not edit the test.
     ```
- Hint: If you are unsure the agent has the right target, ask it to read the
  test first (`read_file tests/test_export.py`) and tell you what output shape
  `test_json_format` expects before it writes anything. The expected shape is
  encoded in the test's `expected` value.
- Acceptance: The session is running under the `default` agent and the agent has
  acknowledged the test as the spec.

## Task 2: Implement --format json, reviewing each edit

- Objective: Approve the in-scope edits and deny anything outside the
  export path so the feature lands where it belongs.
- Scenario: The agent proposes a series of tool calls (read_file, then edit /
  write_file). Each one pauses for your approval.
- Steps:
  - Ask for the implementation:
     ```
     Add a "json" branch to export_rows in src/csv_report/export.py that returns
     json.dumps(rows, indent=2), and add "json" to the --format choices in
     src/csv_report/cli.py. Nothing else.
     ```
  - For each proposed edit, read the diff the agent shows before you approve:
     - Approve edits to `src/csv_report/export.py` and `src/csv_report/cli.py`.
     - Deny any edit to `tests/test_export.py`, `data.py`, or any other file.
       When you deny, say why: "The test is frozen. Implement the format in the
       export module instead."
- Hint: The starter marks the gap with a symptom-only comment in `export.py`
  (`# TODO: json export format is not implemented`). That comment points at where
  the branch is missing; it does not tell you the implementation. Compare the
  csv branch already there for the return-a-string pattern.
- Acceptance: Edits have been applied only to `export.py` and `cli.py`. No other
  file changed.

## Task 3: Run the test to green

- Objective: Confirm the contract is satisfied by running the test.
- Scenario: The edits are in. Now prove it against the frozen spec.
- Steps:
  - From inside the session (or a second terminal), run the target test:
     ```
     bash python -m pytest tests/test_export.py::test_json_format
     ```
  - Then run the full suite to confirm you did not break `test_csv_format`:
     ```
     bash python -m pytest
     ```
- Hint: If `test_json_format` still fails, read the assertion diff pytest prints.
  It shows expected vs actual JSON. Do not touch the test; adjust the export
  code until actual matches expected.
- Acceptance: `test_json_format` passes and the full suite is green.

## Task 4: Verify scope, then commit

- Objective: Prove the change is scoped, then record it.
- Scenario: Green tests are necessary but not sufficient. The change must also be
  scoped to the export module.
- Steps:
  - Check scope against your baseline:
     ```bash
     git diff --stat
     ```
- Confirm only `src/csv_report/export.py` and `src/csv_report/cli.py` appear.
  - Compare against the reference file set in `solution/reference-diff.txt`.
  - Commit once green and scoped:
     ```bash
     git add -A && git commit -m "Add --format json to export"
     ```
- Hint: If `git diff --stat` lists `tests/test_export.py` or any other file, an
  out-of-scope edit slipped through. See the "common failure" section in
  `VERIFY.md` for how to unblock.
- Acceptance: `git diff --stat` (pre-commit) matched the reference file set, and
  the change is committed.

---

## Stretch: a scope-discipline judgment call

- Ask the agent for a second format, then decide whether to accept it:

```
Also add --format yaml.
```

- There is no test for `yaml`, and the project has no YAML library on the standard
library path. This is the judgment: adding it means unrequested, untested,
possibly dependency-adding scope creep. The disciplined move is to deny it,
because the contract (`test_export.py`) does not ask for it. Note your reasoning.
If a real ticket later asks for YAML, the right move is a new failing test first,
then implement, same loop as this lab.

---

## What you learned

- A failing test is a precise, objective spec. Handing it to the agent with an
  @-file mention turns "make it work" into "make this exact assertion pass."
- Reviewing edits one at a time under the `default` agent keeps the change scoped:
  you approve the export path and deny the test file.
- Green tests plus a scoped `git diff` together are the definition of done. One
  without the other is not enough.

## Next

- Continue to VIBECODE-200 to go deeper on multi-file changes and using plan mode
before you let the agent edit.
