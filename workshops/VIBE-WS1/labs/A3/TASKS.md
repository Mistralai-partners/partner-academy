# Lab A3: Debug a failing test to a green suite

- **Workshop:** Mistral Vibe Code practitioner workshop (VIBE-WS1)
- **Activity:** A3

- **Tool:** `vibe` CLI (verified against vibe 2.24.0)

## What you will do

- You will drive `vibe` to run a failing test suite, read the traceback, reason to
the **root cause**, and approve a **minimal fix in the source** (not the test).
You stay in the review seat the whole time: the agent proposes, you decide.

## Prerequisites

- `vibe` CLI installed and authenticated (`vibe --version` -> 2.24.0 or later).
- Python 3.10+ and `pytest` available (`python -m pytest --version`).
- A terminal in the directory where you copy the starter project.

## Done when these checks pass

- `python -m pytest tests/test_reorder.py::test_reorder_threshold` goes green.
- `python -m pytest` (the whole suite) passes.
- `git diff --name-only` shows the change in **source only**: nothing under
   `tests/` is modified.

- Full acceptance detail is in `VERIFY.md`.

---

## Setup (under 5 minutes)

- Copy the starter into a fresh working directory, put it under git so you can
prove later that only source changed, and confirm the red test.

```bash
cp -r starter my-a3 && cd my-a3
git init && git add -A && git commit -m "baseline"
python -m pytest
```

- You should see `1 failed, 3 passed`, with `test_reorder_threshold` failing on a
boundary assertion. That red test is the target.

---

## Task 1: Reproduce and read the failure with `vibe`

- **Objective:** Observe the real failure and the traceback before
  forming any theory.
- **Scenario:** `inventory-cli` shipped a regression. `test_reorder_threshold`
  started failing after a refactor and nobody knows why. First, see it fail
  through the agent so the agent has the evidence in context.
- **Steps:**
  - Launch the interactive session with the default agent (it asks before every
     tool call, which keeps you in control):

     ```bash
     vibe --agent default
     ```

- The starter folder is not a trusted folder, so `vibe` will warn and prompt
     you to trust it. Accept the trust prompt (or start with `vibe --trust`).
  - Ask the agent to run the suite and show you the failure, focusing its
     context on the relevant files:

     > Run `python -m pytest` and show me the full traceback for the failing
     > test. Look at @tests/test_reorder.py and @src/inventory_cli/reorder.py.

- Approve the `bash` and `read_file` tool calls when prompted.
- **Hint (evidence, not fix):** Read the assertion that failed and the exact
  argument values in the traceback. Which single input case is wrong, and how
  does it differ from the cases that pass? Do not change anything yet.
- **Acceptance:** You can state, in one sentence, which input case fails and what
  the test says the correct answer should be.

## Task 2: Hypothesize the root cause BEFORE proposing a fix

- **Objective:** Explain *why* the boundary case is wrong, in terms of
  the business rule, before any edit.
- **Scenario:** The failing test encodes a real requirement. A correct fix has
  to satisfy that requirement, so you need the root cause first.
- **Steps:**
  - Ask the agent to reason, not patch:

     > Do not edit anything yet. Compare the passing cases with the failing case
     > and tell me the root cause: what does `test_reorder_threshold` require at
     > the boundary, and why does the current code give the wrong answer there?
  - If the agent jumps straight to an edit, deny the `edit`/`write_file` tool
     call and repeat: "Root cause first, in words, then we decide on a fix."
- **Hint (evidence, not fix):** The passing tests use inputs that are clearly
  below or clearly above the threshold. The failing test uses an input exactly
  *at* the threshold. Ask what the reorder rule should do at that exact point.
- **Acceptance:** The agent has named the root cause: the threshold is the
  reorder trigger point, so the exact-boundary case must reorder, and the current
  comparison excludes it. No source has changed yet.

## Task 3: Review and approve a minimal source fix

- **Objective:** Judge whether the proposed change is minimal
  and lands in the source, then approve it.
- **Scenario:** With the root cause understood, the fix should be one small,
  obvious change to the logic: and nothing in the tests.
- **Steps:**
  - Ask for the smallest fix, in source:

     > Propose the smallest change to `@src/inventory_cli/reorder.py` that makes
     > the boundary case correct. Do not modify anything under `tests/`. Show me
     > the diff before applying.
  - Review the proposed `edit`. Confirm it touches only
     `src/inventory_cli/reorder.py` and that it changes the boundary behavior of
     `needs_reorder`. Approve the tool call only if both are true.
- **Hint (evidence, not fix):** A correct fix changes the decision only at the
  boundary and leaves the clearly-below and clearly-above cases exactly as they
  were. If the proposed diff touches a test file or weakens an assertion, deny
  it and restate: the test encodes the requirement.
- **Acceptance:** Exactly one source file changed; no test file changed.

## Task 4: Re-run the whole suite to green

- **Objective:** Confirm the fix resolves the target test without
  breaking anything else.
- **Scenario:** A boundary fix can have ripple effects. Prove the whole suite is
  green, not just the one test.
- **Steps:**
  - Ask the agent to re-run everything:

     > Run `python -m pytest` again and confirm the whole suite passes.
  - Then confirm the scope of your change yourself:

     ```bash
     git diff --name-only
     ```
- **Hint (evidence, not fix):** `git diff --name-only` must list only a file
  under `src/`. If you see anything under `tests/`, the fix went to the wrong
  place: revert and go back to Task 3.
- **Acceptance:** `python -m pytest` reports all tests passing and
  `git diff --name-only` shows source-only changes. See `VERIFY.md`.

---

## Stretch: Add a regression test that pins the boundary

- **Objective:** Add a test that would have caught this regression, and
  prove it actually catches it.
- **Steps:**
  - Ask the agent to add a focused regression test:

     > Add a regression test that pins the exact boundary case (stock equal to
     > threshold must reorder) to `tests/test_reorder.py`. Keep it minimal.
  - Prove it fails on the old code and passes on the fix. Temporarily set your
     source fix aside, run the new test, then restore the fix:

     ```bash
     git stash push -- src/inventory_cli/reorder.py   # set the fix aside
     python -m pytest tests/test_reorder.py            # new regression test should FAIL
     git stash pop                                      # restore the fix
     python -m pytest tests/test_reorder.py            # now it should PASS
     ```

- (If you already committed the fix, use `git checkout HEAD~1 --
     src/inventory_cli/reorder.py` to sample the pre-fix source instead, then
     `git checkout HEAD -- src/inventory_cli/reorder.py` to restore it.)
- **Acceptance:** The new regression test fails against the pre-fix source and
  passes against the fixed source.

---

## What you learned

- How to make an agent **reproduce a failure and read the traceback** before
  touching code.
- How to force **root-cause reasoning before a fix**, using the default agent so
  every tool call is yours to approve or deny.
- Why a failing test is a **specification**: the fix belongs in the source, and
  weakening or deleting the test is the wrong move.
- How to **verify scope** with `git diff --name-only` so a "green" suite is
  actually a correct one.

## Next

- Continue to **VIBECODE-300**, which builds on this review-driven workflow for
larger, multi-file changes.
