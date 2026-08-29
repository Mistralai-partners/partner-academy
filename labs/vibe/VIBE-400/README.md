<!-- course-ref -->
**Course:** Mistral Vibe for Code Expert (VIBE-400)

# VIBE-400 Lab - Extend and Operate Vibe Code (Expert)

> **Before you start:** see the repository root `README.md` -> **Running the labs**
> for prerequisites (uv, Python, `MISTRAL_API_KEY`, required models), the pinned
> versions, and a troubleshooting table.

Working reference code for **Mistral Vibe for Code Expert (VIBE-400)**, the
Create-tier build lab. You *read* production-grade hooks, least-privilege agent
profiles, a team permission posture, and a headless CI review gate. This is
**working code you read and run**, not a broken starter you repair.

Read the `.vibe/` setup before you run anything:

- `app/.vibe/hooks.toml` - pre_tool guard (strict+scoped) + post_tool audit +
  post_agent gate.
- `app/.vibe/hooks/guard.py` - denies destructive commands (rm -rf, git push).
- `app/.vibe/hooks/audit.py` - records every tool call to `audit.log`.
- `app/.vibe/hooks/gate.py` - records turn boundaries.
- `app/.vibe/agents/ci-reviewer.toml` - user-facing agent, read/search only.
- `app/.vibe/agents/researcher.toml` - delegation-only subagent, read/search only.
- `app/.vibe/config.toml` - bash gated (not blanket-allowed) + destructive denylist.
- `app/ci/review-gate.sh` - headless CI gate (transcript to exit code).

## Get the lab files

```bash
git clone https://github.com/Mistralai-partners/partner-academy.git
cd partner-academy/labs/vibe/VIBE-400/app
```

Set `MISTRAL_API_KEY` (or a `.env` in this folder) for the optional live `vibe`
runs. Already cloned the repo for another lab? Just `cd` into this folder instead.

## Read it, run it, check it

```bash
# 1. Read the hook scripts and TOML configs (above), then test the CI gate:
bash ci/review-gate.sh ci/samples/approved.json   # exit 0
bash ci/review-gate.sh ci/samples/rejected.json   # exit 1

# 2. Confirm the end state (offline, no API key needed):
python3 verify.py                        # RESULT: PASS
```

`verify.py` is offline and deterministic: it runs every hook against real
wire-protocol payloads, validates TOML configs, and asserts exit codes. A green
result never depends on a live model call.

## Notes

- `vibe` CLI >= 2.24, Python 3.11+ (for `tomllib`).
- `MISTRAL_API_KEY` is needed only for the optional live runs (`VIBE_LIVE=1`).
