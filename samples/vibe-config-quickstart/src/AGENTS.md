# src/ instructions

This is a second, nested instruction file. It applies to `src/` and its
descendants only, and it takes priority over the root `AGENTS.md` here because it
is closer to the files. Vibe injects it lazily: the first time a file under
`src/` is read, this file is added to the context.

## Rules for code in src/
- Every function must have a docstring AND type hints on all parameters and the
  return value. This is stricter than the root rule and it wins inside `src/`.
- Validate inputs at the boundary. Reject impossible values (for example a
  negative amount, or a refund larger than the order total) instead of returning
  a silently wrong result.
