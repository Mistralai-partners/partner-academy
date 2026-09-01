# Full review checklist (support file for the security-checklist skill)

This is a bundled support file. The skill body points here; Vibe lists it under
the skill and the agent reads it on demand with read_file. Relative paths are
relative to this skill's directory.

## Correctness
- [ ] Inputs are validated at the boundary; impossible values are rejected.
- [ ] Numeric edge cases handled: zero, negative, and over-limit values.
- [ ] Return values are correct for every branch, including the error path.

## Robustness
- [ ] No bare `except:`; exceptions are specific and surfaced with context.
- [ ] External calls (I/O, network) have error handling and time bounds.

## Security
- [ ] No secrets in source (API keys, tokens, passwords). Use .env.
- [ ] No untrusted input used to build shell commands or file paths.

## Project conventions
- [ ] Public functions have docstrings and type hints (root AGENTS.md + src/AGENTS.md).
- [ ] Modules stay small and focused.
- [ ] Tests exist for new behavior and pass with `uv run pytest`.
