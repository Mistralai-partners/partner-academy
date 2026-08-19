<!-- course-ref -->
**Course:** Mistral Vibe for Code Advanced (VIBE-300)

# VIBE-300 Lab — Advanced Vibe Code CLI

> **Before you start:** see the repository root `README.md` → **Running the labs** for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned SDK versions, the two-terminal worker setup for Workflows labs, and a troubleshooting table. It is the fastest way past a "the code does not work" moment.

Hands-on lab for **Mistral Vibe for Code Advanced (VIBE-300)**. Replaces the in-course
click-through with real CLI practice: programmatic mode, tool-permission scoping, sub-agents,
config precedence, and bounded headless runs.

- `starter/` — begin here (a failing test, a permission bug, an incomplete read-only sub-agent).
- `solution/` — reference solution.
- `verify/check.sh <starter|solution>` — deterministic acceptance checks (pytest, TOML, tool scope).
- `tasks.md` — the six tasks.

Done when `bash verify/check.sh starter` reports 3 passed, 0 failed.
