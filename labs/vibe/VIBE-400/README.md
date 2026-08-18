<!-- course-ref -->
**Course:** Mistral Vibe for Code Expert (VIBE-400)

# VIBE-400 Lab - Extend and Operate Vibe Code (Expert)

Hands-on lab for **Mistral Vibe for Code Expert (VIBE-400)**. This is the
Create-tier build lab: you *extend* the Vibe Code agent loop with hooks,
*design* least-privilege agent profiles and a team permission posture, and
*assemble* a headless CI review gate - operating Vibe Code as production
infrastructure, not a personal tool.

- `starter/` - begin here. Each artifact ships with the anti-pattern its task
  fixes (an unguarded loop, an over-scoped reviewer, a blanket-allow posture, a
  gate that never fails).
- `solution/` - reference solution. Every file validates against the real
  product schema and the hooks fire in a live run.
- `verify/check.sh <starter|solution>` - deterministic acceptance checks
  (8 checks, no network, no API key). Real hook scripts are executed against
  real wire-protocol payloads; the CI gate is run against captured transcripts.
- `tasks.md` - the five tasks (Create/Evaluate).
- `FACILITATOR.md` - instructor-led delivery (agenda, demos, discussion,
  pitfalls).

**Done when** `bash verify/check.sh starter` reports **8 passed, 0 failed**.

## Prerequisites

- `vibe` CLI ≥ 2.24 (`vibe --version`).
- Python 3.11+ (the verifier uses `tomllib`).
- `MISTRAL_API_KEY` only for the **optional** live runs
  (`ci/review-gate.sh --live`, and `VIBE_LIVE=1` in the verifier). All graded
  checks run offline.

## Layout

```
VIBE-400/
  starter/ | solution/
    .vibe/
      hooks.toml            # pre_tool guard (strict) + post_tool audit + post_agent gate
      hooks/{guard,audit,gate}.py
      agents/ci-reviewer.toml   # agent_type="agent"  (least-privilege reviewer)
      agents/researcher.toml    # agent_type="subagent" (delegation-only)
      config.toml               # team permission posture (bash gated + denylist)
    ci/
      review-gate.sh            # headless gate wrapper (offline + --live)
      parse_verdict.py          # transcript -> exit code (0/1/3)
      samples/{approved,rejected}.json
    app_sample.py               # a tiny file for a live reviewer/hook to read
  verify/check.sh
  tasks.md  README.md  FACILITATOR.md
```

## What "real" means here

- The hook scripts are executed by the verifier against the **actual Vibe hook
  wire protocol** (the JSON shape emitted by `vibe.core.hooks`), and they fire
  end-to-end in a live `vibe -p` run (see `VIBE_LIVE=1`).
- `hooks.toml`, both agent profiles, and `config.toml` validate against the
  installed product's own loaders (`HookConfig`, `AgentProfile.from_toml`,
  `VibeConfigSchema`).
- The CI gate runs and returns real exit codes the verifier asserts.
