# Vibe Config Quickstart: project instructions

This is a small Python project managed with `uv`. Always use `uv run` to execute
Python and `uv run pytest` to run tests. Do not call `pip` or `python` directly.

This file is an instruction file (`AGENTS.md`). Vibe injects it automatically at
the start of every session for this directory and everything under it, so these
rules are always in effect without anyone loading them.

## Project conventions
- All public functions have a docstring and type hints.
- Tests live in `tests/` and use `pytest`. Run them before you call a change done.
- Keep modules small and focused.

## When to use the skills in this project
- When you review code, load the `security-checklist` skill and apply it.
- When you prepare a release, run the `/changelog` skill to draft the entry.

## Agents available (in `.vibe/agents/`)
- `reviewer`: read-only. Reviews code against these conventions and the checklist.
- `test-writer`: extends the test suite. Can edit files under `tests/`.

## What this project is
A deliberately tiny orders and refunds app used only as something for the agents
and skills to act on. Entry points: `src/orders.py` (the clean example) and
`src/refunds.py` (the review target, which breaks two conventions on purpose).
