<!-- course-ref -->
**Course:** Mistral Vibe for Code - Tech Sales Essentials (VIBE-TSE1)

# VIBE-TSE1 Lab - Mistral Vibe for Code, Tech Sales Essentials

> **Before you start:** see the repository root `README.md` → **Running the labs** for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned SDK versions, the two-terminal worker setup for Workflows labs, and a troubleshooting table. It is the fastest way past a "the code does not work" moment.

Dual-modality lab for **Mistral Vibe for Code - Tech Sales Essentials
(VIBE-TSE1)**. For GSI, ISV, and hyperscaler pre-sales consultants. Two halves:
the **live demo** a technical seller performs on a customer's repo with the real
Vibe CLI, and the **scoping call** they turn into a qualified opportunity.

- `starter/` - begin here. The `taskvault` demo repo (missing the requested
  `search` feature), the discovery-call `scenario.md`, and an unfilled
  `scoping.json`.
- `solution/` - reference solution (feature + tests, a real headless `pr.json`,
  and a completed `scoping.json`).
- `verify/check.sh <starter|solution>` - deterministic acceptance checks
  (feature behavior, test presence, headless result, and the qualification and
  objection rubric).
- `tasks.md` - the five tasks (three demo tasks, two scoping tasks).
- `FACILITATOR.md` - instructor-led delivery layer (agenda, demo checkpoints, the
  scoping role-play, objection handling, pitfalls and unblocks).

## The two modalities

- **Self-paced.** Work `starter/` through `tasks.md`. Done when
  `bash verify/check.sh starter` reports **5 passed, 0 failed**.
- **Instructor-led / VILT.** Deliver from `FACILITATOR.md`: model the demo on the
  projector, then run the scoping call as a role-play with the room.

## Run it

```bash
# 1. Install / confirm the CLI and key (needed for the demo tasks 1-3)
vibe --version            # expect >= 2.24
vibe --setup              # sets MISTRAL_API_KEY

# 2. Work the tasks in starter/ (see tasks.md), then check
cd starter
bash ../verify/check.sh starter
```

**Done when `bash verify/check.sh starter` reports 5 passed, 0 failed.**

The scoping tasks (4 and 5) need no API key - they are graded from `scoping.json`.

Because this repo ships a `.vibe/` folder, Vibe loads its project config only
from a trusted directory. Accept the trust prompt in interactive mode, or pass
`--trust` for the non-interactive `-p` runs.

All Vibe commands and flags in this lab are from `vibe --help` (2.24.0) and the
pinned Vibe Code documentation. No invented flags, paths, or tool names.
