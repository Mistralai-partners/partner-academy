<!-- course-ref -->
**Course:** Mistral Vibe for Code Advanced (VIBE-300)

# VIBE-300 Lab — Advanced Vibe Code CLI

Hands-on lab for **Mistral Vibe for Code Advanced (VIBE-300)**. Replaces the in-course
click-through with real CLI practice: programmatic mode, tool-permission scoping, sub-agents,
config precedence, and bounded headless runs.

- `starter/` — begin here (a failing test, a permission bug, an incomplete read-only sub-agent).
- `solution/` — reference solution.
- `verify/check.sh <starter|solution>` — deterministic acceptance checks (pytest, TOML, tool scope).
- `tasks.md` — the six tasks.

Done when `bash verify/check.sh starter` reports 3 passed, 0 failed.
