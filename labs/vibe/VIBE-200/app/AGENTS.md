# textkit - project conventions for Vibe

These conventions are loaded into context on every run from this repo. Follow
them when generating, editing, or reviewing code.

## Code shape
- Every helper is a pure function with type hints and a Google-style docstring.
- Guard empty input and return `""` rather than raising.
- Match the shape of `app/casing.py` when adding a new helper.

## Testing
- Every new helper ships with a pytest test in `tests/`.
- Run `python3 -m pytest -q` before proposing a diff, and keep the suite green.

## Scope
- Keep edits scoped: change only the lines the task requires.
- A documentation request must not change logic. If a "docs" diff also edits
  behavior, reject it and re-ask for docs only.
