# Feature request (the change you demo live)

**Repo:** `taskvault`, a tiny in-memory task store (`app/vault.py`).

**Requested feature:** add a `search(keyword)` method to the `Vault` class.

- Returns the tasks whose `title` contains `keyword`, matched
  **case-insensitively** (so `search("buy")` finds both `"Buy milk"` and
  `"buy bread"`).
- An empty or whitespace-only keyword returns **no** tasks.
- Match the shape of the existing code: type hints, a short docstring, and the
  same empty-input guard style used by `add`.
- Cover it with tests in `tests/test_search.py`.

You do **not** hand-write this. You drive Vibe Code to plan it, implement it,
and write the tests, while the customer watches the agent loop run. That is the
whole point of the demo: an autonomous coding agent, not a smarter autocomplete.
