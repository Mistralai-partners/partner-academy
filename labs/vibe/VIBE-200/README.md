<!-- course-ref -->
**Course:** Mistral Vibe for Code Intermediate (VIBE-200)

# VIBE-200 Lab - Mistral Vibe for Code Intermediate

> **Before you start:** see the repository root `README.md` → **Running the labs** for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned SDK versions, the two-terminal worker setup for Workflows labs, and a troubleshooting table. It is the fastest way past a "the code does not work" moment.

Hands-on lab for **Mistral Vibe for Code Intermediate (VIBE-200)**. Replaces the
in-course click-through with real CLI practice on the everyday development loop:
explore, fix, generate, review, and tune a small project with the Vibe CLI.

- `starter/` - begin here (a buggy helper, a missing helper, an over-broad
  review agent, and an unfinished `.vibe/` config).
- `solution/` - reference solution.
- `verify/check.sh <starter|solution>` - deterministic acceptance checks
  (pytest, agent scope, project config).
- `tasks.md` - the five tasks (four machine-checked gates plus one read-only
  exercise).
- `FACILITATOR.md` - instructor-led delivery layer (agenda, demo checkpoints,
  discussion prompts, pitfalls and unblocks).

**The project:** `textkit`, a tiny string-helpers package. `app/casing.py` is
the pattern file every new helper should imitate.

**Putting it together:** once you have done the config, custom-agent, `AGENTS.md`, and skill tasks here, see `samples/vibe-config-quickstart/` (repository root) for one small project that wires all four together, with a short narrated walkthrough.

## Run it

```bash
# 1. Install / confirm the CLI and key
vibe --version          # expect >= 2.24
export MISTRAL_API_KEY=...   # or `vibe --setup`

# 2. Work the tasks in starter/ (see tasks.md), then check
cd starter
bash ../verify/check.sh starter
```

**Done when `bash verify/check.sh starter` reports 4 passed, 0 failed.**

Because this repo ships a `.vibe/` folder, Vibe loads its project config only
from a trusted directory. Accept the trust prompt in interactive mode, or pass
`--trust` for non-interactive `-p` runs.

All Vibe commands and flags in this lab are from `vibe --help` (2.24.0) and the
pinned Vibe Code documentation. No invented flags, paths, or tool names.
