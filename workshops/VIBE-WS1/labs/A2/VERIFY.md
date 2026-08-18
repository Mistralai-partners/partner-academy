# A2 Verification

- You are done when both checks below hold. Green tests alone do not count, and a
clean diff alone does not count. Both must be true at the same time.

## Check 1: the acceptance test passes

- Run the target test by its node id:

```bash
python -m pytest tests/test_export.py::test_json_format
```

- Expected: `1 passed`. Then confirm nothing else broke:

```bash
python -m pytest
```

- Expected: `2 passed` (`test_csv_format` and `test_json_format`).

## Check 2: the change is scoped to the export module

- From your working directory, against the baseline commit you made in setup:

```bash
git diff --stat
```

- Expected: exactly two files, both in the export path:

```
 src/csv_report/cli.py    | 2 +-
 src/csv_report/export.py | ...
 2 files changed, ...
```

- This must match the file set in `solution/reference-diff.txt`. If `git diff --stat`
lists any other path, especially `tests/test_export.py`, Check 2 fails even if
Check 1 passed.

## Why this discipline matters

- The test is the contract. `test_json_format` encodes the exact expected JSON
  output. Making that assertion pass is an objective, reviewable definition of
  done, not a vibe check. This is why you pin it with `@tests/test_export.py` and
  treat it as frozen.
- The scoped diff is the safety rail. An agent can make a test pass in more than
  one way. Some of those ways are wrong: editing unrelated files, weakening the
  test, or adding untested surface area. A `git diff --stat` that touches only
  the export module proves the feature landed where it belongs and nothing else
  moved. Reviewers trust a small, scoped diff; they distrust a green checkmark on
  a sprawling one.
- Together, test-as-contract plus scoped-diff is how you keep an agent honest:
  the test says "this behavior now exists" and the diff says "and only this
  changed to get it."

## Common failure: the agent edits the test instead of the source

- The fastest way to turn `test_json_format` green is to change the test so it no
longer demands JSON. An agent under time pressure may propose exactly that:
editing `tests/test_export.py` (for example, relaxing the `expected` value or
deleting the assertion). This makes Check 1 pass and Check 2 fail, and it ships a
feature that does not actually work.

- How to catch it: watch the file path on every proposed edit. If the path is
`tests/test_export.py`, stop.

- How to unblock:

- Deny the edit.
- Restate the boundary in the session:
   ```
   The test is frozen. Do not modify tests/test_export.py. Implement the json
   format in the export module.
   ```
- Re-point the agent at the right file with an @-mention:
   ```
   Add the json branch to @src/csv_report/export.py and the choice to
   @src/csv_report/cli.py so test_json_format passes as written.
   ```

- If a test edit already landed, restore it before you continue:

```bash
git checkout -- tests/test_export.py
```

- Then rerun both checks.
