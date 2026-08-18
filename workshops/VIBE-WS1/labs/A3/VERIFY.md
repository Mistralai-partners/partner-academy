# Lab A3: Verification

- Your work is correct only when **all three** objective checks below hold at the
same time. Run them from your working directory (the copy of `starter/` that you
put under git during setup).

## Objective acceptance checks

### Check 1: the named test goes green

```bash
python -m pytest tests/test_reorder.py::test_reorder_threshold
```

- Expected: `1 passed`. On the starter this test is red; after a correct fix it is
green.

### Check 2: the whole suite passes

```bash
python -m pytest
```

- Expected: `4 passed` (no failures, no errors). A boundary fix can ripple, so the
full suite: not just the one test: must be green.

### Check 3: the fix is in SOURCE ONLY

```bash
git diff --name-only
```

- Expected: exactly one path, under `src/` (specifically
`src/inventory_cli/reorder.py`). **Nothing under `tests/` may appear.** If a test
file shows up, the suite may be "green" for the wrong reason: see the common
failure below.

- A quick guard you can run:

```bash
git diff --name-only | grep -q '^tests/' && echo "FAIL: a test file changed" || echo "OK: source-only change"
```

- Expected: `OK: source-only change`.

## The "why" (incident report)

- **Symptom.** `test_reorder_threshold` failed with:

```
assert needs_reorder(5, 5) is True
E       assert False is True
E        +  where False = needs_reorder(5, 5)
```

- **Business rule.** The `threshold` is the reorder *trigger point*. An item must
be reordered once its stock **reaches** the threshold or drops below it. That
makes the boundary (stock exactly equal to the threshold) a reorder case.

- **Root cause.** During the refactor, the comparison in `needs_reorder` was
written as a strict "below" check rather than a "reached or below" check, so the
exact-boundary case fell on the wrong side and returned "no reorder needed." The
two other tests only exercised inputs clearly below or clearly above the
threshold, so they never touched the boundary and kept passing. That is what
masked the defect and made it look like a mystery.

- **Correct fix.** Make the threshold comparison inclusive of the boundary, in the
source (`src/inventory_cli/reorder.py`). `reorder_quantity` needs no change
because it delegates the decision to `needs_reorder`. Full write-up:
`solution/ROOT-CAUSE.md`; reference source: `solution/reorder.py`.

## Common failure: a green suite that is actually wrong

- The tempting shortcut is to make the suite green by attacking the **test**
instead of the **source**:

- weakening the assertion (for example, changing the expected value so the
  boundary no longer has to reorder),
- deleting or skipping `test_reorder_threshold`, or
- wrapping the call in a `try/except` so the failure is swallowed.

- All three make `python -m pytest` pass while leaving the real defect in place :
items at their reorder point would still never be flagged. **Check 3 exists to
catch exactly this:** any of these shortcuts changes a file under `tests/`, so
`git diff --name-only` fails.

### Unblock (when the agent tries the shortcut)

- If the agent proposes editing a test, weakening an assertion, or a `try/except`
wrapper:

- **Deny** the `edit` / `write_file` tool call.
- **Restate the contract:** "`test_reorder_threshold` encodes the requirement : 
   an item at its threshold must reorder. Do not change the test."
- **Ask for the root cause first:** "Tell me why the boundary case is wrong in
   the source, then propose the smallest source-only fix."

- This puts the agent back on the path to a real fix: one small change in
`src/inventory_cli/reorder.py` that satisfies the test as written.
